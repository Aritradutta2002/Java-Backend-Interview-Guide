# Chapter 7. Security

Examples use Spring Security 6 (Spring Boot 3) and the `SecurityFilterChain` style of configuration. Security advice here is the standard, widely accepted guidance for backend APIs; specific regulatory obligations depend on your jurisdiction and industry and are out of scope.

## Q161. How do authentication and authorization differ?

**Priority:** Must Know  
**Why interviewers ask it:** It is the foundation for everything else, and conflating the two is how broken access control happens.

**Interview-ready answer:** Authentication establishes who the caller is — validating a password, a token signature, a client certificate. Authorization decides what that identity may do: which endpoints it can call and which specific records it can see or change. They fail differently: missing or invalid credentials give 401, an authenticated but not permitted caller gives 403. The most common real-world mistake is doing only coarse authorization — "this endpoint requires ROLE_USER" — without checking ownership, so any logged-in user can read another user's order by changing an ID. Both layers are necessary, and the resource-level check must happen on the server for every request.

**In-depth explanation:** Least privilege applies at every level: tokens should carry the narrowest scopes needed, database users should not be superusers, and service accounts should not share credentials. Authorization models range from role-based (roles grant permissions), to attribute-based (decisions from attributes such as tenant, ownership, time), to relationship-based for complex sharing scenarios. A practical middle ground for most backends is roles for coarse capability plus an explicit ownership or tenant predicate in the query itself, so a missing check cannot return another tenant's data. Authorization decisions should also be auditable: log who did what to which resource, because that record is what makes an incident investigable.

**Practical backend example:** Both layers applied together:

```java
@PreAuthorize("hasRole('USER')")                       // coarse: authenticated with a role
@GetMapping("/api/orders/{id}")
public OrderResponse get(@PathVariable UUID id, @AuthenticationPrincipal Jwt jwt) {
    UUID customerId = UUID.fromString(jwt.getSubject());
    return orderRepository.findByIdAndCustomerId(id, customerId)   // fine-grained: ownership in the query
            .map(OrderResponse::from)
            .orElseThrow(() -> new OrderNotFoundException(id));    // 404, not 403: no existence leak
}
```

**Common follow-ups:**
- Why check ownership on every request? Because the client controls the identifier; without it, any authenticated user can read any record.
- 401 or 403? 401 when credentials are missing or invalid, 403 when the authenticated caller is not permitted.
- Where should authorization live? At the edge for coarse rules and in the service or query for resource-level decisions.

**Mistakes to avoid:** Relying on the UI hiding a button; checking roles but not ownership; trusting an identifier from the request body; scattering authorization logic so no one can audit it.

**Production perspective:** Broken access control is consistently among the most common serious web vulnerabilities. Add tests that call each endpoint as a different tenant and assert 403 or 404 — they are cheap and catch regressions that code review misses.

**Related concepts covered:** Least privilege, RBAC and ABAC, tenant isolation, IDOR, audit logging, status code semantics.

## Q162. When choose server sessions versus JWT bearer tokens?

**Priority:** Must Know  
**Why interviewers ask it:** It is the clearest test of whether a candidate repeats "JWT is stateless and therefore better" or reasons about trade-offs.

**Interview-ready answer:** Server-side sessions keep state on the server and give the client an opaque cookie. Revocation is immediate — delete the session — and the cookie carries no data, but you need shared session storage such as Redis when running multiple instances. JWTs are self-contained and verified by signature, so any service can validate them without a lookup, which suits distributed systems and third-party APIs. The cost is revocation: a signed token is valid until it expires, so you need short lifetimes plus refresh tokens, or a denylist that reintroduces the state you were avoiding. For a browser application with one backend, sessions are often simpler and safer; for multi-service or third-party access, tokens usually win.

**In-depth explanation:** A JWT is signed, not encrypted, by default — anyone holding it can read its claims, so it must never contain secrets. Storage in the browser matters: an httpOnly, Secure, SameSite cookie is not readable by JavaScript, whereas `localStorage` is exposed to any XSS. Cookie-based auth then needs CSRF protection, which bearer headers avoid. Token lifetime is the key control: short access tokens (minutes) with refresh tokens held securely limit the damage of a leak, and refresh token rotation with reuse detection catches theft. Sessions also have practical advantages — you can list and revoke active sessions per user, and you can change permissions instantly, whereas a JWT carries the permissions it was minted with until expiry.

**Practical backend example:** Choosing per context:

```java
// Browser app, single backend: session cookie, CSRF protection on
http.sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED))
    .csrf(Customizer.withDefaults());

// Service-to-service or SPA with a token: stateless resource server
http.sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
    .csrf(csrf -> csrf.disable())                 // no ambient credentials to abuse
    .oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()));
```

```properties
# short-lived access tokens limit the revocation gap
security.jwt.access-token-ttl=10m
security.jwt.refresh-token-ttl=14d
```

**Common follow-ups:**
- Is a JWT encrypted by default? No; it is signed and base64url-encoded, so the claims are readable. Use JWE if confidentiality is required.
- How do you revoke a JWT? Short expiry plus refresh rotation, or a denylist keyed by token ID — which makes it stateful again.
- Where should a browser store a token? An httpOnly Secure cookie is safer than `localStorage`, which is readable by any injected script.

**Mistakes to avoid:** Claiming JWT is always better; long-lived access tokens; putting personal data or secrets in claims; storing tokens in `localStorage` without accepting the XSS risk; forgetting that permissions inside a token go stale.

**Production perspective:** Whichever you choose, you need a way to force logout — after a password change, a compromise, or a permissions change. Design that path deliberately rather than discovering during an incident that tokens cannot be revoked.

**Related concepts covered:** Session storage, refresh token rotation, cookie flags, CSRF interaction, revocation strategies, claim staleness.

## Q163. How should passwords be stored and verified?

**Priority:** Must Know  
**Why interviewers ask it:** Credential handling is non-negotiable knowledge, and the wrong answer is a serious red flag.

**Interview-ready answer:** Never store passwords in reversible form. Use an adaptive, deliberately slow hash designed for passwords — Argon2id, bcrypt or scrypt — with a per-password random salt, which those algorithms generate and embed in the output. Verification re-hashes the candidate with the stored parameters and compares in constant time, which the encoder handles. General-purpose hashes such as SHA-256 are unsuitable because they are fast, so an attacker with the database can try billions of candidates per second on a GPU. The work factor should be tuned so hashing takes a noticeable fraction of a second on your hardware, and increased over time as hardware improves.

**In-depth explanation:** In Spring Security, `DelegatingPasswordEncoder` prefixes stored hashes with the algorithm id (for example `{bcrypt}`), which allows transparent migration: verify with the old algorithm and re-hash on successful login with the new one. Around the hash, other controls matter: rate limiting and lockout on repeated failures, a generic error message so you do not reveal which accounts exist, and multi-factor authentication for sensitive systems. Password reset must use a single-use, short-lived, high-entropy token stored hashed, not a password sent by email. Also check candidate passwords against known-breached lists rather than enforcing baroque composition rules, which mostly produce predictable substitutions.

**Practical backend example:** Encoder configuration and safe verification:

```java
@Bean
PasswordEncoder passwordEncoder() {
    // delegating encoder: new hashes use the default, old ones still verify
    return PasswordEncoderFactories.createDelegatingPasswordEncoder();
}

public void login(String email, String rawPassword) {
    User user = users.findByEmail(email).orElse(User.DUMMY);     // avoid timing-based enumeration
    if (!passwordEncoder.matches(rawPassword, user.passwordHash())) {
        loginAttempts.recordFailure(email);                       // rate limit / lockout
        throw new BadCredentialsException("Invalid email or password");  // generic message
    }
    if (passwordEncoder.upgradeEncoding(user.passwordHash())) {
        users.updateHash(user.id(), passwordEncoder.encode(rawPassword)); // transparent upgrade
    }
}
```

**Common follow-ups:**
- Why not SHA-256 alone? It is fast by design, so offline brute force is cheap; password hashes must be deliberately slow and memory-hard.
- Where does the salt go? Modern encoders generate a random salt per password and embed it in the stored string.
- How do you handle password reset? A single-use, short-lived, random token stored hashed; never email the password.

**Mistakes to avoid:** Custom hashing schemes; a single application-wide salt; encryption instead of hashing; revealing whether an email exists; unlimited login attempts.

**Production perspective:** Plan for a breach: with adaptive hashing and unique salts, stolen hashes are expensive to crack, which buys time to force resets. Keep the work factor configurable so it can be raised without a code change.

**Related concepts covered:** Adaptive hashing, salts, encoder migration, account enumeration, rate limiting, reset token design.

## Q164. What are OAuth2 and OpenID Connect at a practical level?

**Priority:** Important  
**Why interviewers ask it:** Most services integrate with an identity provider, and the OAuth2/OIDC distinction is widely misunderstood.

**Interview-ready answer:** OAuth2 is a delegated authorization framework: it lets an application obtain a token to access resources on behalf of a user or of itself, without handling the user's credentials. It does not, by itself, tell you who the user is. OpenID Connect is a thin layer on top that adds authentication: an ID token, a standard `userinfo` endpoint and standard claims. The grants that matter today are authorization code with PKCE for user-facing applications, including SPAs and mobile apps, and client credentials for service-to-service calls. The implicit and resource-owner-password grants are discouraged. In Spring Boot, the API is usually an OAuth2 resource server validating access tokens, while the login flow is handled by the identity provider.

**In-depth explanation:** Three token types appear: the access token, presented to APIs and typically short-lived; the refresh token, used to obtain new access tokens and kept secret; and the ID token, which is for the client to learn about the user and must not be used as an API credential. PKCE protects the authorization code exchange for clients that cannot keep a secret. Scopes express what the token is allowed to do, and are not the same thing as application roles — scopes are delegated permissions, roles are properties of the user. Redirect URI validation is security-critical: allowing wildcards enables token theft. Understanding these distinctions is more valuable in an interview than memorising the protocol's message flow.

**Practical backend example:** A resource server validating tokens and mapping scopes:

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://id.example.com/realms/app     # discovery + JWKS
          # 'audiences' (Boot 2.7+) rejects tokens minted for other APIs;
          # see Q169 for the programmatic AudienceValidator equivalent
          audiences: orders-api
```

```java
http.authorizeHttpRequests(auth -> auth
        .requestMatchers(HttpMethod.GET, "/api/orders/**").hasAuthority("SCOPE_orders.read")
        .requestMatchers(HttpMethod.POST, "/api/orders/**").hasAuthority("SCOPE_orders.write")
        .anyRequest().authenticated())
    .oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()));
```

**Common follow-ups:**
- Is OAuth2 itself authentication? No; it is authorization delegation. OIDC adds authentication on top with an ID token.
- Which grant for a single-page app? Authorization code with PKCE; implicit is deprecated.
- Can an ID token be used to call an API? No; APIs must accept access tokens, and the audience check enforces that.

**Mistakes to avoid:** Using the ID token as an API credential; skipping audience validation; wildcard redirect URIs; treating scopes as roles; implementing your own OAuth server without a strong reason.

**Production perspective:** Cache the provider's JWKS and handle key rotation gracefully, because a failed key fetch means every request fails authentication. Also monitor token validation failures — a spike usually signals a clock skew or rotation issue rather than an attack.

**Related concepts covered:** Authorization code with PKCE, client credentials, token types, scopes versus roles, JWKS rotation, audience validation.

## Q165. How do CORS and CSRF differ?

**Priority:** Must Know  
**Why interviewers ask it:** These are routinely confused, and confusion leads to disabling the wrong protection.

**Interview-ready answer:** CORS is a browser mechanism that relaxes the same-origin policy: it lets a server declare which other origins may read its responses from browser JavaScript. It is not a server-side protection — a non-browser client such as curl or a backend service ignores CORS entirely. CSRF is an attack where a malicious site causes the victim's browser to send a state-changing request to your site using credentials the browser attaches automatically, typically cookies. CSRF protection therefore matters whenever authentication is ambient: cookies or HTTP Basic. An API authenticated with a bearer token in a header is not automatically vulnerable, because the browser will not attach that header for a cross-site request. So the rule is: configure CORS for legitimate browser clients, and enable CSRF protection when you use cookie-based sessions.

**In-depth explanation:** CORS has two request classes: simple requests, which the browser sends directly and then blocks the response if the origin is not allowed, and preflighted requests (custom headers, JSON content type, non-simple methods), where the browser first sends an `OPTIONS` request. Note the implication: for simple requests the server has already executed the action even if the browser hides the response, which is precisely why CORS is not a substitute for authorization. `Access-Control-Allow-Origin: *` cannot be combined with credentials, so cookie-based APIs must echo specific allowed origins. For CSRF, the standard defences are a synchroniser token, `SameSite=Lax` or `Strict` cookies (which modern browsers largely default to Lax), and checking `Origin`. Disabling CSRF protection is only acceptable when no ambient credential can be used.

**Practical backend example:** Correct configuration for each case:

```java
@Bean
CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration config = new CorsConfiguration();
    config.setAllowedOrigins(List.of("https://app.example.com"));  // never "*" with credentials
    config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
    config.setAllowedHeaders(List.of("Authorization", "Content-Type", "Idempotency-Key"));
    config.setAllowCredentials(true);
    config.setMaxAge(Duration.ofMinutes(30));                       // cache preflights
    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/api/**", config);
    return source;
}

// cookie-session app: keep CSRF protection on
http.csrf(csrf -> csrf.csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse()));
// stateless bearer-token API: no ambient credentials, CSRF protection is not applicable
```

**Common follow-ups:**
- Does CORS protect an API from curl? No; it is enforced by browsers only. Server-side authorization is the protection.
- When can you disable CSRF protection? When authentication cannot be sent ambiently — a pure bearer-token API with no cookie sessions.
- What does `SameSite` do? It tells the browser not to attach the cookie on cross-site requests, mitigating CSRF at the cookie level.

**Mistakes to avoid:** `allowedOrigins("*")` with credentials; disabling CSRF protection on a cookie-authenticated application; believing CORS prevents attacks; reflecting the `Origin` header back without validation.

**Production perspective:** CORS misconfiguration is a frequent finding in security reviews, especially origin reflection, which effectively allows every site. Keep the allowlist in configuration, review it, and test it with an automated check per environment.

**Related concepts covered:** Same-origin policy, preflight requests, SameSite cookies, synchroniser tokens, ambient authority, origin validation.

## Q166. How do you prevent SQL injection and unsafe deserialization?

**Priority:** Must Know  
**Why interviewers ask it:** Both are injection-class vulnerabilities with catastrophic impact and well-known, simple defences.

**Interview-ready answer:** For SQL, never build statements by concatenating user input: use parameterised queries — JDBC prepared statements, JPA named parameters, or a query builder — so the value is never parsed as SQL. Parts of a query that cannot be parameterised, such as a column name in `ORDER BY`, must come from a strict allowlist. For deserialization, do not deserialise untrusted data into arbitrary types: avoid Java native serialization entirely for external input, and never enable Jackson polymorphic type handling with a permissive base type, because that lets an attacker choose which classes are instantiated. Deserialise into explicit DTOs, validate them, and reject unknown fields where appropriate.

**In-depth explanation:** ORMs reduce SQL injection risk but do not eliminate it: a native query built with string concatenation is just as vulnerable, and so is a dynamically constructed JPQL fragment. Least privilege limits the blast radius — the application's database user should not be able to drop tables or read other schemas. For deserialization, the danger is gadget chains: existing classes on the classpath whose construction triggers side effects. Jackson's default typing (`enableDefaultTyping`) has produced many CVEs, which is why polymorphic deserialization should use a closed allowlist of subtypes. The same class of problem exists for XML (XXE — disable external entities), YAML (unsafe constructors) and for any library that turns data into objects. Dependency scanning matters too, since these vulnerabilities often arrive through transitive dependencies.

**Practical backend example:** Parameterisation, allowlisting and safe JSON handling:

```java
// SAFE: parameters are bound, never parsed as SQL
@Query(value = "SELECT * FROM \"order\" WHERE customer_id = :customerId AND status = :status",
       nativeQuery = true)
List<Order> find(UUID customerId, String status);

// UNSAFE: never do this
// entityManager.createNativeQuery("SELECT * FROM \"order\" WHERE status = '" + status + "'");

// dynamic ORDER BY cannot be parameterised -> allowlist
private static final Map<String, String> SORT = Map.of(
        "createdAt", "created_at", "total", "total_cents");
String column = SORT.getOrDefault(requestedSort, "created_at");   // never interpolate raw input
```

```java
ObjectMapper mapper = JsonMapper.builder()
        .disable(MapperFeature.ALLOW_FINAL_FIELDS_AS_MUTATORS)
        .enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)   // explicit contract
        .build();                                                     // no default typing enabled
```

**Common follow-ups:**
- Is escaping sufficient for SQL? No; escaping is error-prone and context-dependent. Parameterisation is the reliable defence.
- What about dynamic sorting or table names? Use an allowlist mapping client values to known identifiers.
- Why is Java native serialization risky? Deserialising untrusted bytes can instantiate arbitrary classes and trigger gadget chains; avoid it for external data.

**Mistakes to avoid:** String concatenation "just this once"; trusting an ORM to prevent injection in native queries; enabling Jackson default typing; parsing XML without disabling external entities; running the application as a database superuser.

**Production perspective:** Add static analysis and dependency scanning to CI so both classes of issue are caught automatically. Also log and alert on database errors that look like injection attempts — they often indicate active probing.

**Related concepts covered:** Prepared statements, allowlists, gadget chains, XXE, least-privilege database users, dependency scanning.

## Q167. How would you secure a Spring Boot API endpoint?

**Priority:** Must Know  
**Why interviewers ask it:** It connects security theory to the concrete configuration you would actually write.

**Interview-ready answer:** I start from deny by default: `anyRequest().authenticated()`, then explicitly permit the few public endpoints. Authentication is a bearer token validated as an OAuth2 resource server, or a session for browser flows. Authorization is layered: URL rules for coarse capability, method security with `@PreAuthorize` for service-level rules, and an ownership predicate in the query for resource-level access. I disable CSRF protection only for genuinely stateless token APIs, enable HTTPS with HSTS at the edge, and add the standard security headers. Actuator endpoints are restricted, error responses avoid leaking internals, and I write tests asserting 401, 403 and 200 for representative requests.

**In-depth explanation:** Order matters in `authorizeHttpRequests`: the first matching rule wins, so a broad `permitAll` placed early can accidentally expose everything after it. `securityMatcher` lets you define separate chains for the API and for a browser-facing application with different policies. Method security requires `@EnableMethodSecurity`, and `@PreAuthorize` can reference method arguments and the authenticated principal, which makes ownership checks expressive. Remember that CORS is configured separately from authorization and that preflight `OPTIONS` requests must be permitted. Finally, security configuration is code that deserves review and tests; a one-line change can silently open an endpoint, and nothing in the application will fail at startup.

**Practical backend example:** A layered configuration with tests:

```java
@Bean
SecurityFilterChain api(HttpSecurity http) throws Exception {
    return http
        .securityMatcher("/api/**")
        .csrf(csrf -> csrf.disable())                                  // stateless bearer tokens only
        .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
        .cors(Customizer.withDefaults())
        .headers(h -> h.httpStrictTransportSecurity(hsts -> hsts.maxAgeInSeconds(31536000))
                       .contentTypeOptions(Customizer.withDefaults())
                       .frameOptions(HeadersConfigurer.FrameOptionsConfig::deny))
        .authorizeHttpRequests(auth -> auth
            .requestMatchers(HttpMethod.OPTIONS, "/**").permitAll()    // CORS preflight
            .requestMatchers("/api/public/**").permitAll()
            .requestMatchers("/api/admin/**").hasRole("ADMIN")
            .anyRequest().authenticated())                             // deny by default
        .oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()))
        .build();
}

@PreAuthorize("hasRole('SUPPORT') or #customerId == authentication.name")   // method-level rule
public CustomerDto get(String customerId) { ... }
```

**Common follow-ups:**
- What about method-level security? `@EnableMethodSecurity` plus `@PreAuthorize`/`@PostAuthorize` for rules that need arguments or the principal.
- How do you test it? Slice tests asserting 401 for anonymous, 403 for the wrong role, and 200 for the right one.
- Why permit `OPTIONS`? Browsers send unauthenticated preflight requests; blocking them breaks legitimate CORS clients.

**Mistakes to avoid:** A broad `permitAll` early in the chain; disabling CSRF protection on cookie-authenticated applications; exposing actuator publicly; relying on URL rules alone for data access; never testing the negative cases.

**Production perspective:** Add an automated check that lists every endpoint and its required authority, and review it on each release. Endpoints added without security rules are the most common way an internal API becomes public.

**Related concepts covered:** Deny-by-default, filter chain matching, method security, security headers, CORS preflight, actuator exposure.

## Q168. How do you design resource-level authorization?

**Priority:** Must Know  
**Why interviewers ask it:** Insecure direct object reference is one of the most frequently exploited real-world flaws.

**Interview-ready answer:** Every read or write of a specific record must verify that the authenticated principal is allowed to touch that record, not just that they are logged in. The most robust technique is to make the ownership or tenant condition part of the query itself — `findByIdAndCustomerId` rather than `findById` followed by a check — because then a missing check cannot return data. For shared resources I model permissions explicitly (owner, collaborator, viewer) and evaluate them centrally rather than scattering `if` statements. Responding 404 instead of 403 for records the caller may not see avoids confirming that they exist. And identifiers should be unguessable, though unguessability is defence in depth, never the control itself.

**In-depth explanation:** Multi-tenancy deserves special discipline: a tenant column on every table plus a mandatory predicate, or PostgreSQL row-level security, so a forgotten filter fails closed rather than leaking. Hibernate filters or a repository base class that always applies the tenant condition reduce the chance of an oversight. Bulk endpoints are a common gap — a request containing 100 IDs must check every one, not just the first. So are nested resources: `/orders/{orderId}/lines/{lineId}` must verify that the line belongs to the order and the order to the caller. Write paths deserve extra care because mass assignment can let a client change the owner field itself. Finally, authorization decisions belong in tests: a parameterised test that replays each endpoint as a second tenant is one of the highest-value test suites you can have.

**Practical backend example:** Ownership in the query plus centralised policy:

```java
// 1) ownership is part of the query - a forgotten check cannot leak data
Optional<Order> findByIdAndCustomerId(UUID id, UUID customerId);

// 2) shared resources: a central policy component, evaluated by method security
@Component("documentPolicy")
public class DocumentPolicy {
    public boolean canRead(UUID documentId, Authentication auth) {
        return permissions.hasAny(documentId, auth.getName(), Set.of(OWNER, COLLABORATOR, VIEWER));
    }
}

@PreAuthorize("@documentPolicy.canRead(#documentId, authentication)")
@GetMapping("/api/documents/{documentId}")
public DocumentDto get(@PathVariable UUID documentId) { ... }
```

```sql
-- 3) defence in depth for multi-tenancy
ALTER TABLE "order" ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "order"
    USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

**Common follow-ups:**
- Why is a hidden UI not enough? The API is directly callable; the client is not a security boundary.
- Should you return 403 or 404? 404 avoids confirming the resource exists, which is usually preferable for other tenants' data.
- How do you handle bulk operations? Authorize every identifier in the request, and fail the whole operation or report per-item results explicitly.

**Mistakes to avoid:** `findById` followed by a forgettable check; trusting a tenant ID from the request body; sequential integer IDs as the only obstacle; skipping checks on nested and bulk endpoints.

**Production perspective:** Access-control regressions are silent — nothing errors, data simply leaks. Automated cross-tenant tests and periodic access reviews are the practical defences, along with logging denied attempts so probing is visible.

**Related concepts covered:** IDOR, multi-tenancy, row-level security, permission models, mass assignment, negative testing.

## Q169. What should an access token contain and how is it validated?

**Priority:** Important  
**Why interviewers ask it:** Token validation is easy to implement partially, and a partial implementation is an authentication bypass.

**Interview-ready answer:** A JWT access token carries registered claims — issuer, subject, audience, expiry, not-before, issued-at, and a token id — plus scopes or roles and any minimal application claims. Validation must check all of it: the signature against the issuer's published keys, that the algorithm is the expected asymmetric one rather than whatever the token says, the issuer, the audience (so a token for another API is rejected), and the time claims with a small clock-skew allowance. Keys are fetched from the JWKS endpoint and selected by the `kid` header, with caching and graceful handling of rotation. Tokens should be short-lived, and anything sensitive must stay out of the claims because they are readable.

**In-depth explanation:** The historical `alg: none` attack and key-confusion attacks (signing with the public key as an HMAC secret) are why the verifier must fix the expected algorithm rather than trusting the header. Clock skew is a real operational issue: allowing 30–60 seconds avoids spurious failures between machines. Rotation works through `kid`: the provider publishes both old and new keys during an overlap period, and your JWKS cache must refresh when it sees an unknown `kid` — with rate limiting so an attacker cannot force constant fetches. Opaque tokens are the alternative: they carry no data and are validated by introspection against the authorization server, which gives instant revocation at the cost of a network call per request. Spring Security implements all of this when you configure `issuer-uri`, but you should be able to explain what it is doing.

**Practical backend example:** Explicit validators, including audience:

```java
@Bean
JwtDecoder jwtDecoder(@Value("${security.issuer-uri}") String issuer) {
    NimbusJwtDecoder decoder = JwtDecoders.fromIssuerLocation(issuer);   // discovery + JWKS caching
    decoder.setJwtValidator(new DelegatingOAuth2TokenValidator<>(
            JwtValidators.createDefaultWithIssuer(issuer),               // iss, exp, nbf
            new JwtClaimValidator<List<String>>("aud",
                    aud -> aud != null && aud.contains("orders-api")),   // audience
            new JwtTimestampValidator(Duration.ofSeconds(30))));         // clock skew
    return decoder;
}
```

**Common follow-ups:**
- How does key rotation work? The provider publishes multiple keys; the token's `kid` selects one, and clients refresh the JWKS cache when they see an unknown key id.
- Why validate the audience? Otherwise a token issued for a different API of the same issuer would be accepted here.
- Opaque tokens or JWTs? Opaque tokens give instant revocation through introspection; JWTs avoid a network call per request. Choose based on revocation needs and latency budget.

**Mistakes to avoid:** Trusting the `alg` header; skipping audience or issuer checks; no clock-skew tolerance; caching JWKS forever; putting personal data in claims; accepting expired tokens because "the gateway checked already".

**Production perspective:** Alert on authentication failure spikes and on JWKS fetch errors. A provider key rotation combined with an unrefreshable cache is a classic total-outage scenario that is easy to prevent and hard to diagnose under pressure.

**Related concepts covered:** JWT claims, JWKS and kid rotation, algorithm confusion, clock skew, token introspection, audience scoping.

## Q170. How do you manage secrets across environments?

**Priority:** Important  
**Why interviewers ask it:** Leaked credentials are among the most common causes of real breaches, and prevention is mostly process plus tooling.

**Interview-ready answer:** Secrets never live in source control or container images. They are supplied at runtime — environment variables from a secret manager, mounted files, or a direct integration such as Vault or a cloud secret service — and referenced from configuration with placeholders. Each environment has its own secrets, and production secrets are not accessible from developer machines. Rotation must be possible without a code change and ideally without downtime, which means the application reads the secret at startup or refresh rather than baking it in, and supports an overlap period for credential change. Secret scanning runs in CI so an accidental commit is caught immediately, and any leaked secret is rotated, not just deleted from history.

**In-depth explanation:** Kubernetes Secrets are base64-encoded, not encrypted, unless encryption at rest is enabled, and they are visible to anyone who can read the namespace — so RBAC matters as much as the storage. Mounted files are often better than environment variables because environment variables leak into child processes, crash dumps and some logging frameworks. Short-lived dynamic credentials — for example a database credential issued per pod with a TTL — are stronger than long-lived static ones. For local development, use separate non-production credentials and a `.env` file that is gitignored, never a copy of production values. Also secure the audit trail: who read which secret and when is valuable during an incident.

**Practical backend example:** Configuration referencing runtime-provided secrets:

```yaml
spring:
  datasource:
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}          # injected from the secret store, never committed
  config:
    import: "configtree:/etc/secrets/"   # Kubernetes secret mounted as files
```

```yaml
# Kubernetes: mount as files, restrict with RBAC, enable encryption at rest
volumes:
  - name: app-secrets
    secret: { secretName: orders-api-secrets, defaultMode: 0400 }
```

```bash
# CI: block commits containing credentials
gitleaks detect --no-git --redact --exit-code 1
```

**Common follow-ups:**
- Should secrets be in images? No; images are shared, cached and often pushed to registries with broad read access.
- How do you rotate without downtime? Support two valid credentials during an overlap window, or restart with the new value behind a rolling deploy.
- What if a secret leaks? Rotate immediately and audit usage; removing the commit does not invalidate the credential.

**Mistakes to avoid:** Committing `application-prod.yml` with real values; passing secrets as command-line arguments (visible in the process list); sharing one credential across environments; treating base64 as encryption.

**Production perspective:** Make rotation routine rather than an emergency procedure — a credential that has never been rotated cannot be rotated quickly under pressure. Test the rotation path in a lower environment on a schedule.

**Related concepts covered:** Secret managers, config trees, dynamic credentials, secret scanning, Kubernetes RBAC, rotation procedures.

## Q171. How do you handle sensitive data in logs and responses?

**Priority:** Important  
**Why interviewers ask it:** Logs are widely readable and long-lived, so they are a common and overlooked source of data exposure.

**Interview-ready answer:** The principle is minimisation: log what is needed to operate the system and nothing more. Never log credentials, tokens, full card numbers, or entire request and response bodies containing personal data. Use identifiers instead of values — a customer ID rather than an email — and mask where a value must be partially visible. In responses, return only the fields the client needs, and keep internal details such as stack traces, SQL and hostnames out entirely. For debugging, rely on correlation IDs plus targeted, time-boxed verbose logging in a controlled environment rather than logging everything permanently. Redaction should be enforced structurally, for example a serialiser that masks annotated fields, because relying on every developer to remember is not a control.

**In-depth explanation:** Structured logging makes redaction practical: with key-value fields you can apply an allowlist, whereas free-text messages are hard to filter reliably. Log retention matters as much as content: if personal data ends up in logs, it inherits the retention and access policy of your logging system, which is usually broader than the database's. Third-party log aggregation and error trackers extend that reach further. Exceptions are a frequent leak path — an exception message containing a query with parameter values, or a validation error echoing the rejected value. Also consider derived exposure: a log line that records "user X requested document Y" may itself be sensitive in some domains.

**Practical backend example:** Structural redaction rather than developer discipline:

```java
public record PaymentRequest(
        @JsonSerialize(using = MaskedSerializer.class) String cardNumber,   // "**** **** **** 4242"
        @JsonIgnore String cvv,                                             // never serialised at all
        long amountMinor, String currency) {}

// logging: identifiers and outcomes, never payloads
log.info("payment processed paymentId={} customerId={} amountMinor={} currency={} outcome={}",
        payment.id(), payment.customerId(), payment.amountMinor(), payment.currency(), outcome);
// avoid: log.debug("payment request {}", request);   // would serialise the whole object
```

```xml
<!-- Logback: last-resort pattern-based masking for known token formats -->
<replace regex="(Bearer\s+)[A-Za-z0-9._-]+" replacement="$1[REDACTED]"/>
```

**Common follow-ups:**
- How do you debug without logging tokens? Log a hash or the last four characters, plus a correlation ID that ties the request together.
- What about request bodies? Log them only in non-production with synthetic data, or log a redacted subset of fields.
- Who can read your logs? Usually many more people than can read the database — treat that as part of the threat model.

**Mistakes to avoid:** `log.debug` of whole DTOs in production; exception messages containing parameter values; stack traces in API responses; assuming log retention is short when it is not.

**Production perspective:** Add a CI check or code review rule for logging statements that pass whole objects, and periodically grep logs for patterns such as `Bearer ` or card-shaped digits. Finding a leak yourself is much cheaper than having it reported.

**Related concepts covered:** Data minimisation, structured logging, redaction strategies, correlation IDs, log retention and access, exception hygiene.

## Q172. What security checks belong in a public file-upload endpoint?

**Priority:** Important  
**Why interviewers ask it:** Upload endpoints combine several attack surfaces and are a realistic test of defensive thinking.

**Interview-ready answer:** Authenticate and authorize the upload, then enforce a size limit at the proxy and in the application so a huge file cannot exhaust memory or disk. Determine the type from the file's bytes, not the declared `Content-Type` or the extension, and accept only an allowlist. Generate the storage key yourself so the client's filename can never influence a path — that removes traversal entirely. Store outside the web root, ideally in object storage, and serve downloads through an authorized endpoint or a short-lived pre-signed URL with `Content-Disposition: attachment` and `X-Content-Type-Options: nosniff`. Where the risk warrants it, scan for malware and re-encode images to strip embedded payloads, and rate-limit uploads per user.

**In-depth explanation:** Serving user content from your main domain is the subtle risk: an uploaded HTML or SVG file can execute in the origin's context and steal sessions, which is why a separate domain or forced download is recommended. Archive files introduce decompression bombs, so limit the expanded size and entry count if you extract them. Metadata in images can contain location data you may not want to retain, and re-encoding removes both metadata and many embedded exploits. Quotas matter operationally: without per-user limits, storage cost becomes an availability problem. Finally, log uploads with the user, size and detected type — that record is what makes an abuse investigation possible.

**Practical backend example:** Layered checks in one handler:

```java
@PostMapping(value = "/api/attachments", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
@PreAuthorize("hasRole('USER')")
public AttachmentDto upload(@RequestPart MultipartFile file, @AuthenticationPrincipal Jwt jwt) throws IOException {
    if (file.getSize() > 10L * 1024 * 1024) throw new PayloadTooLargeException();          // size
    quotaService.assertWithinQuota(jwt.getSubject(), file.getSize());                       // abuse
    String detected = contentTypeDetector.detect(file.getInputStream());                    // magic bytes
    if (!Set.of("image/png", "image/jpeg", "application/pdf").contains(detected)) {
        throw new UnsupportedFileTypeException(detected);                                   // allowlist
    }
    byte[] safe = detected.startsWith("image/")
            ? imageService.reencode(file.getBytes(), detected)    // strips metadata and payloads
            : file.getBytes();
    String key = "attachments/" + jwt.getSubject() + "/" + UUID.randomUUID();               // generated key
    objectStorage.put(key, safe, detected);
    return attachmentService.record(key, sanitizeName(file.getOriginalFilename()), detected, safe.length);
}
```

**Common follow-ups:**
- Can `Content-Type` be trusted? No; it is client-supplied. Detect from the content and validate against an allowlist.
- How do you prevent path traversal? Generate the storage key server-side; never concatenate client-supplied names into paths.
- Why serve uploads from a different domain? So that a malicious HTML or SVG file cannot execute in your application's origin.

**Mistakes to avoid:** Trusting the extension; storing files under the web root; no per-user quota; extracting archives without limits; serving user content inline on the main domain.

**Production perspective:** Uploads are also a cost and capacity concern, not only a security one. Set quotas, monitor storage growth, and keep upload traffic on a path that cannot starve interactive requests.

**Related concepts covered:** Content sniffing, allowlists, generated storage keys, pre-signed URLs, decompression bombs, image re-encoding, quotas.
