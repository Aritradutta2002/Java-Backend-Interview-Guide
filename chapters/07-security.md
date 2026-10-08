# Chapter 7: Security

---

## Q161 — Authentication vs Authorization

**The one-line answer:** Authentication proves who you are; authorization decides what you are allowed to do — they are distinct steps and distinct failure codes: 401 when identity is unknown, 403 when identity is known but access is denied.

### Definitions

- **Authentication:** "Who are you?" — Validates credentials (password, token, certificate) and establishes a principal (the verified identity).
- **Authorization:** "What can you do?" — Checks whether the authenticated principal has permission to perform the requested action on the requested resource.

### The 401 vs 403 distinction

| Code | Meaning | When to use |
|---|---|---|
| 401 Unauthorized | Not authenticated | No credentials sent, or credentials invalid/expired |
| 403 Forbidden | Authenticated but not authorized | Valid user, but lacks required role/permission |

Returning 404 instead of 403 for protected resources (to hide their existence from unauthorized users) is a valid security technique — but use it consistently.

### Principal, roles, and authorities

In Spring Security:
- **Principal:** The authenticated user (e.g., a `UserDetails` object or JWT claims).
- **`GrantedAuthority`:** A single permission or role (e.g., `ROLE_ADMIN`, `orders:write`).
- **Role:** A group of authorities, conventionally prefixed `ROLE_`. `hasRole("ADMIN")` checks `ROLE_ADMIN`.
- **Authority:** A fine-grained permission. `hasAuthority("orders:write")` checks the exact string.

### RBAC vs ABAC

- **RBAC (Role-Based Access Control):** User has roles; roles have permissions. Simple, common (`@PreAuthorize("hasRole('ADMIN')")`).
- **ABAC (Attribute-Based Access Control):** Access decisions based on attributes of user, resource, and environment. More expressive but complex (`only the order's owner can cancel it`).

```java
// RBAC
@PreAuthorize("hasRole('ADMIN')")
public void deleteUser(Long userId) { ... }

// ABAC-style — ownership check
@PreAuthorize("#userId == authentication.principal.id or hasRole('ADMIN')")
public UserProfile getProfile(Long userId) { ... }
```

---

## Q162 — Session vs JWT Trade-offs

**The one-line answer:** Server-side sessions are stateful — easy to revoke but require shared storage for horizontal scaling; JWTs are stateless — scale trivially but cannot be revoked without additional infrastructure.

### Server-side sessions

```
Client → sends session cookie (just an ID)
Server → looks up session data in store (Redis, DB)
Server → validates session, loads user details
```

**Pros:**
- Immediate revocation — delete the session record.
- Session data can be large without affecting network payloads.
- The server is in full control of session lifetime.

**Cons:**
- Requires shared session store for clustered deployments (Redis).
- Every request hits the session store (network hop).
- Sticky sessions (session affinity) work around this but reduce flexibility.

### JWT (JSON Web Token)

```
Header.Payload.Signature
eyJhbGci...   eyJzdWIi...   HMAC-SHA256(header+payload, secret)
```

The server validates the signature and trusts the claims — no DB lookup required.

**Pros:**
- Stateless — any server can validate any token.
- Works natively for cross-domain, mobile, and API clients.
- Carries claims (user ID, roles, expiry) in the token itself.

**Cons:**
- **Cannot be revoked** without a revocation list (which re-introduces statefulness).
- Token theft: if a token is stolen before expiry, the attacker has valid access.
- Short expiry + refresh tokens is the standard mitigation.

### JWT best practices

```
access_token: short-lived (15 minutes)
refresh_token: longer-lived (7 days), stored HttpOnly cookie, rotated on use
```

- Store JWTs in `HttpOnly` cookies (not `localStorage`) — immune to XSS.
- Validate `iss`, `aud`, `exp`, `nbf` claims on every request.
- Use asymmetric signing (RS256, ES256) for multi-service environments — services verify with public key, only auth service holds private key.
- Never put sensitive data in JWT payload — it's Base64-encoded, not encrypted (use JWE for encryption).

### Revocation strategies for JWTs

1. **Short expiry + refresh tokens** — access token valid 15min; breach window is minimal.
2. **Token blacklist** — store revoked JTIs in Redis with TTL matching token expiry.
3. **Token version field** — store a `tokenVersion` in the user record; reject tokens with an older version.

---

## Q163 — Password Hashing

**The one-line answer:** Never store plaintext or reversibly encrypted passwords — use an adaptive, salted, slow hashing algorithm like BCrypt or Argon2 so that brute-force and rainbow table attacks are computationally infeasible.

### Why regular hashes (MD5, SHA-256) are wrong for passwords

- Fast — a GPU can compute billions of SHA-256 hashes per second.
- No salt — identical passwords produce identical hashes (rainbow tables).
- Unchangeable work factor — can't adapt to faster hardware over time.

### BCrypt

```java
PasswordEncoder encoder = new BCryptPasswordEncoder(12); // cost factor 12
String hash = encoder.encode("myPassword123");    // $2a$12$...
boolean valid = encoder.matches("myPassword123", hash); // true
```

BCrypt automatically generates a random salt and embeds it in the hash string. The cost factor (10–12 recommended) controls iterations — doubling it doubles computation time. As hardware gets faster, increase the cost factor and rehash passwords on next login.

### Argon2 (preferred modern choice)

```java
PasswordEncoder encoder = new Argon2PasswordEncoder(
    16,    // salt length in bytes
    32,    // hash length in bytes
    1,     // parallelism
    65536, // memory in KB (64 MB)
    3      // iterations
);
```

Argon2 (winner of the Password Hashing Competition) resists GPU attacks better than BCrypt because it is memory-hard. Spring Security provides `Argon2PasswordEncoder`.

### Password migration

When upgrading from a weak hashing algorithm:
```java
// DelegatingPasswordEncoder — supports multiple algorithms, upgrades on login
PasswordEncoder encoder = PasswordEncoderFactories.createDelegatingPasswordEncoder();
// Prefixes: {bcrypt}..., {argon2}..., {noop}... (legacy)
// On successful login with old scheme, rehash and store with new scheme
```

### What NOT to do

- **MD5/SHA-1/SHA-256 alone:** Fast, no salt — vulnerable to rainbow tables and GPU brute force.
- **Encryption (AES):** Reversible — if the key is compromised, all passwords are exposed.
- **Unsalted hashing:** Identical passwords produce identical hashes — one breach exposes all users with that password.

---

## Q164 — OAuth2 and OpenID Connect Basics

**The one-line answer:** OAuth2 is an authorization delegation protocol (granting access to resources without sharing credentials); OpenID Connect is an identity layer on top of OAuth2 that enables authentication and provides a standardized user identity token (ID token).

### OAuth2 roles

- **Resource Owner:** The user who owns the data.
- **Client:** The application requesting access.
- **Authorization Server:** Issues tokens (e.g., Keycloak, Auth0, Google).
- **Resource Server:** The API protecting resources (your Spring Boot service).

### Authorization Code flow (most secure, recommended for web apps)

```
1. Client redirects user to Authorization Server
   GET /authorize?response_type=code&client_id=app&redirect_uri=...&scope=openid profile

2. User authenticates and consents at Authorization Server

3. Authorization Server redirects back with code
   GET /callback?code=abc123

4. Client exchanges code for tokens (server-to-server, no browser)
   POST /token  { code, client_id, client_secret, redirect_uri }
   → { access_token, refresh_token, id_token, expires_in }

5. Client uses access_token to call APIs
   Authorization: Bearer <access_token>
```

### PKCE (Proof Key for Code Exchange)

For public clients (SPAs, mobile apps) that can't keep a `client_secret`:
- Client generates a random `code_verifier` and its SHA-256 hash `code_challenge`.
- Sends `code_challenge` with the authorization request.
- Sends `code_verifier` with the token exchange — server verifies the hash.
- Prevents authorization code interception attacks.

### OpenID Connect additions

OAuth2 grants access to resources. OIDC adds:
- **ID token:** A JWT containing user identity claims (`sub`, `email`, `name`, `iat`, `exp`).
- **`/userinfo` endpoint:** Returns user claims.
- **Standard scopes:** `openid`, `profile`, `email`, `address`, `phone`.

### Spring Boot as Resource Server

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt.jwtAuthenticationConverter(jwtAuthConverter())))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/**").authenticated())
            .build();
    }
}
```

```properties
spring.security.oauth2.resourceserver.jwt.issuer-uri=https://auth.example.com
# Spring fetches JWKS (public keys) from issuer and validates JWT signatures
```

---

## Q165 — CSRF vs CORS

**The one-line answer:** CORS is a browser mechanism that controls which origins can read responses from cross-origin requests; CSRF is an attack where a malicious site causes a victim's authenticated browser to send unwanted requests to your API — they are often confused but address different threats.

### CORS (Cross-Origin Resource Sharing)

CORS prevents JavaScript on `evil.com` from reading the response of a request to `api.example.com`. Without CORS headers, the browser blocks the response even if the request was made.

CORS does NOT prevent the request from being sent — it prevents the response from being read by JavaScript. This is a critical distinction: a CSRF attack doesn't need to read the response, just cause the side effect.

### CSRF (Cross-Site Request Forgery)

```
1. User is logged in to bank.com (has session cookie)
2. User visits evil.com
3. evil.com contains: <img src="https://bank.com/transfer?to=attacker&amount=1000">
4. Browser sends the request with the user's session cookie
5. Bank processes the transfer — user never consented
```

### CSRF defenses

**1. SameSite cookies (modern, preferred):**
```
Set-Cookie: sessionId=abc; SameSite=Lax; Secure; HttpOnly
```
`SameSite=Lax` prevents the cookie from being sent on cross-origin form submissions and most cross-origin requests. Effectively eliminates CSRF without a token.

**2. CSRF tokens (traditional):**
```
Server → issues a CSRF token in the HTML form or as a cookie (not HttpOnly, so JS can read it)
Client → must include the token as a form field or custom header on state-changing requests
Server → validates the token before processing
```

The key: an attacker cannot read the CSRF token (same-origin policy), so they can't include it in the forged request.

**3. Stateless APIs with JWT in Authorization header:**
Browsers never automatically include Authorization headers on cross-origin requests — CSRF is not a concern for pure JWT APIs. Only cookie-based auth needs CSRF protection.

### Spring Security CSRF

```java
// Disable for stateless REST APIs using JWT
http.csrf(AbstractHttpConfigurer::disable)

// Enable for form-based apps
http.csrf(csrf -> csrf.csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse()))
```

---

## Q166 — Spring Security Filter Chain

**The one-line answer:** Spring Security's filter chain is an ordered list of `OncePerRequestFilter` implementations — each inspects, modifies, or short-circuits the request; understanding the chain lets you insert custom logic (JWT validation, rate limiting) at the right point.

### Default filter order (key filters)

```
1.  DisableEncodeUrlFilter
2.  WebAsyncManagerIntegrationFilter
3.  SecurityContextHolderFilter
4.  HeaderWriterFilter                    ← adds security headers (X-Frame-Options etc.)
5.  CorsFilter
6.  CsrfFilter
7.  LogoutFilter
8.  UsernamePasswordAuthenticationFilter  ← form login
9.  BearerTokenAuthenticationFilter       ← JWT extraction and validation
10. BasicAuthenticationFilter             ← HTTP Basic
11. RequestCacheAwareFilter
12. SecurityContextHolderAwareRequestFilter
13. AnonymousAuthenticationFilter         ← sets AnonymousAuthentication if no auth yet
14. SessionManagementFilter
15. ExceptionTranslationFilter            ← translates AuthenticationException / AccessDeniedException
16. AuthorizationFilter                   ← enforces access rules
```

### Adding a custom filter

```java
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res,
                                    FilterChain chain) throws ServletException, IOException {
        String header = req.getHeader(HttpHeaders.AUTHORIZATION);
        if (header != null && header.startsWith("Bearer ")) {
            String token = header.substring(7);
            try {
                Authentication auth = jwtService.authenticate(token);
                SecurityContextHolder.getContext().setAuthentication(auth);
            } catch (JwtException e) {
                res.sendError(HttpServletResponse.SC_UNAUTHORIZED, "Invalid token");
                return;
            }
        }
        chain.doFilter(req, res);
    }
}

// Register before the standard authentication filter
http.addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);
```

### ExceptionTranslationFilter

Translates Spring Security exceptions to HTTP responses:
- `AuthenticationException` → 401 (via `AuthenticationEntryPoint`)
- `AccessDeniedException` → 403 (via `AccessDeniedHandler`) or 401 for anonymous users

Always configure custom `AuthenticationEntryPoint` to return JSON instead of the default HTML login page for REST APIs.

---

## Q167 — Method Security

**The one-line answer:** Method-level security with `@PreAuthorize` applies authorization checks at the service layer — complementing URL-level security and enabling fine-grained access control based on method arguments and return values.

### Setup

```java
@Configuration
@EnableMethodSecurity(prePostEnabled = true)
public class MethodSecurityConfig { }
```

### @PreAuthorize

Evaluated before the method executes. If the expression returns false, `AccessDeniedException` is thrown.

```java
@Service
public class OrderService {

    @PreAuthorize("hasRole('USER')")
    public List<Order> listMyOrders(String customerId) { ... }

    @PreAuthorize("hasRole('ADMIN') or #customerId == authentication.principal.username")
    public Order getOrder(String orderId, String customerId) { ... }

    @PreAuthorize("hasAuthority('orders:delete') and hasRole('ADMIN')")
    public void deleteOrder(String orderId) { ... }
}
```

### @PostAuthorize

Evaluated after the method executes, with access to the return value (`returnObject`). Use to verify the returned object belongs to the requesting user:

```java
@PostAuthorize("returnObject.customerId == authentication.principal.username")
public Order getOrderById(Long id) {
    return repository.findById(id).orElseThrow();
}
```

### @PreFilter / @PostFilter

Filter collections before/after method execution:

```java
@PostFilter("filterObject.ownerId == authentication.principal.id")
public List<Document> listDocuments() {
    return repository.findAll(); // filtered by Spring Security in memory
}
```

Note: `@PostFilter` loads all records then filters in memory — inefficient for large result sets. Prefer filtering in the database query.

### URL security vs method security

Use both:
- **URL security** for coarse-grained, role-based access at the HTTP layer.
- **Method security** for fine-grained, data-level authorization at the business layer.

This provides defense in depth — even if URL security misconfiguration opens a path, method security still protects.

---

## Q168 — OWASP API Security Top 10

**The one-line answer:** The OWASP API Security Top 10 lists the most critical API vulnerabilities — every backend developer should be able to recognize and mitigate these in their own APIs.

### Top vulnerabilities

**1. Broken Object Level Authorization (BOLA / IDOR)**

The most common API vulnerability. A user accesses another user's resource by manipulating an ID.

```
GET /orders/42   ← logged in as user A, but order 42 belongs to user B → returns it anyway
```

Fix: Always check ownership: `order.getCustomerId().equals(currentUserId)`.

**2. Broken Authentication**

Weak passwords, missing rate limiting on login, token not expiring.

Fix: Use strong password hashing, rate-limit login attempts, short-lived JWTs.

**3. Broken Object Property Level Authorization (Mass Assignment)**

Updating fields the user shouldn't control:
```
PATCH /users/me  { "role": "ADMIN" }  ← user can promote themselves
```

Fix: Use explicit DTO fields — never bind request body directly to entity/domain objects.

**4. Unrestricted Resource Consumption**

No rate limiting, no pagination limits, no file size limits → DOS via large requests.

Fix: Rate limiting, max page sizes, request body size limits, timeouts.

**5. Broken Function Level Authorization**

Admin endpoints accessible to regular users because URL-level security is incomplete.

Fix: Default-deny (`anyRequest().denyAll()`), then explicitly permit endpoints.

**6. Unrestricted Access to Sensitive Business Flows**

Automated abuse of legitimate business functions (buying all items in flash sale, creating thousands of free accounts).

Fix: Rate limiting, CAPTCHA, anomaly detection.

**7. Server-Side Request Forgery (SSRF)**

User-controlled URL in a feature that makes server-side HTTP requests:
```
POST /webhook/test  { "url": "http://169.254.169.254/latest/meta-data/" }
← fetches AWS instance metadata
```

Fix: Allowlist URLs/IP ranges, block private IP ranges, use an egress proxy.

**8. Security Misconfiguration**

Verbose error messages, debug endpoints exposed, default credentials, CORS `*`.

Fix: Security headers, no stack traces in responses, disable actuator in production, environment-specific config.

**9. Improper Inventory Management**

Outdated API versions, shadow APIs (undocumented/forgotten endpoints) with fewer security controls.

Fix: Version management, sunset old APIs, maintain an API registry.

**10. Unsafe Consumption of APIs**

Trusting data from third-party APIs without validation:
```
String name = externalApiResponse.get("name"); // inject this into SQL query
```

Fix: Treat all external data as untrusted; validate and sanitize before use.

---

## Q169 — Secrets Management

**The one-line answer:** Secrets (DB passwords, API keys, JWT signing keys) must never appear in source code, config files committed to version control, or application logs — use environment variables for simple deployments and a secrets manager (Vault, AWS Secrets Manager) for production.

### What counts as a secret

- Database credentials
- API keys for third-party services (Stripe, Twilio, SendGrid)
- JWT signing keys / OAuth2 client secrets
- Encryption keys
- SMTP credentials
- Cloud service credentials

### Anti-patterns

```yaml
# NEVER DO THIS — committed to Git
spring:
  datasource:
    password: mySecretPassword123  # plaintext in application.yml
  
stripe:
  api-key: sk_live_abc123  # live API key in source code
```

### Environment variable approach (minimum)

```bash
# Injected at runtime, not in source code
export SPRING_DATASOURCE_PASSWORD=secret
export STRIPE_API_KEY=sk_live_abc123
```

In Kubernetes via Secrets:
```yaml
env:
  - name: SPRING_DATASOURCE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-secret
        key: password
```

### HashiCorp Vault integration

```properties
spring.config.import=vault://secret/myapp
spring.cloud.vault.host=vault.example.com
spring.cloud.vault.token=${VAULT_TOKEN}
```

Vault provides: dynamic credentials (auto-rotating DB passwords), lease-based access, audit log of who accessed what secret.

### Preventing accidental exposure

```java
// Log masking — never log secrets
log.debug("Connecting to DB at {} with user {}", url, username); // password NOT logged

// @ToString exclusion (Lombok)
@ToString.Exclude private String apiKey;

// application.properties — Spring Boot sanitizes these in /actuator/env
spring.datasource.password=...  // shown as "****** " in actuator
```

### Secret rotation

Dynamic secrets (Vault, AWS Secrets Manager rotation) generate new credentials periodically without application restart. Configure Spring datasource refresh or use a vault-agent sidecar that writes secrets to files and notifies the app.

---

## Q170 — TLS and HTTPS

**The one-line answer:** TLS (Transport Layer Security) encrypts data in transit and authenticates the server's identity via certificates — every external-facing service must use HTTPS; internal service-to-service traffic should also use TLS (mTLS) in zero-trust networks.

### TLS handshake (simplified TLS 1.3)

```
1. Client Hello: supported cipher suites, client random
2. Server Hello: chosen cipher suite, server random, server certificate
3. Client verifies certificate (chain to trusted CA)
4. Key exchange: ephemeral Diffie-Hellman
5. Both sides derive session keys
6. Encrypted application data
```

### Certificate chain

```
Root CA (self-signed, in browser/OS trust store)
  └─ Intermediate CA (cross-signed by Root CA)
      └─ Your server certificate (signed by Intermediate CA)
```

The server presents its cert + intermediate cert. Client validates the chain up to a trusted root.

### Spring Boot HTTPS configuration

```properties
server.ssl.key-store=classpath:keystore.p12
server.ssl.key-store-password=${SSL_KEYSTORE_PASSWORD}
server.ssl.key-store-type=PKCS12
server.ssl.key-alias=myapp
server.port=8443
```

In production, terminate TLS at the load balancer or ingress, not the application — simpler certificate management, better performance.

### HSTS (HTTP Strict Transport Security)

```java
http.headers(h -> h.httpStrictTransportSecurity(
    hsts -> hsts.includeSubDomains(true).maxAgeInSeconds(31536000)));
```

Tells browsers: "Never connect to this domain over HTTP — always use HTTPS." Prevents SSL-stripping attacks.

### mTLS (Mutual TLS)

Both client and server present certificates — used for service-to-service authentication in zero-trust architectures. Each service has a client certificate; the server validates it before allowing access.

### Certificate management

- Use Let's Encrypt for free, auto-renewing certs.
- Monitor certificate expiry — expired certs cause hard downtime.
- Use cert-manager in Kubernetes for automatic provisioning and renewal.

---

## Q171 — Security Logging and Auditing

**The one-line answer:** Security-relevant events must be logged (authentication successes/failures, authorization decisions, admin actions, data access) with enough context to support forensics — but logs must never contain secrets, passwords, or PII that isn't masked.

### What to log

```java
// Authentication events
log.info("[SECURITY] LOGIN_SUCCESS user={} ip={}", username, clientIp);
log.warn("[SECURITY] LOGIN_FAILURE user={} ip={} reason={}", username, clientIp, reason);

// Authorization events
log.warn("[SECURITY] ACCESS_DENIED user={} resource={} action={}", userId, resource, action);

// Admin and sensitive operations
log.info("[AUDIT] user={} action=DELETE_USER targetUser={} ip={}", adminId, targetId, ip);
log.info("[AUDIT] user={} action=EXPORT_DATA count={} ip={}", userId, recordCount, ip);

// Suspicious patterns
log.warn("[SECURITY] RATE_LIMIT_EXCEEDED user={} endpoint={}", userId, endpoint);
log.warn("[SECURITY] INVALID_TOKEN ip={} reason={}", ip, reason);
```

### What NOT to log

```java
// NEVER log these
log.info("User {} logged in with password {}", username, password);  // plaintext password
log.debug("Payment request: {}", fullCardNumber);                     // PAN (card number)
log.info("JWT token: {}", token);                                     // valid credential
log.info("Request body: {}", requestBody);                            // may contain secrets
```

### Masking sensitive fields

```java
public static String mask(String value) {
    if (value == null || value.length() <= 4) return "****";
    return value.substring(0, 2) + "****" + value.substring(value.length() - 2);
}
log.info("Card ending in {}", mask(cardNumber)); // "4111111111111111" → "41****11"
```

### Audit trail requirements

- **Tamper-evident:** Logs should be written to a append-only store (Elasticsearch, SIEM) that the application cannot modify.
- **Timestamped:** Use UTC timestamps with millisecond precision.
- **Correlated:** Every log line should include request ID and user ID (via MDC).
- **Retention:** Regulatory frameworks (PCI-DSS, SOC2, GDPR) require minimum 1-year retention.

### Spring Security audit events

```java
@EventListener
public void onAuthSuccess(AuthenticationSuccessEvent event) {
    log.info("[SECURITY] LOGIN_SUCCESS principal={}", event.getAuthentication().getName());
}

@EventListener
public void onAuthFailure(AbstractAuthenticationFailureEvent event) {
    log.warn("[SECURITY] LOGIN_FAILURE principal={} reason={}",
        event.getAuthentication().getName(),
        event.getException().getClass().getSimpleName());
}
```

---

## Q172 — Input Validation and Path Traversal

**The one-line answer:** All user input is untrusted and must be validated at the boundary — validate type, length, format, and range; sanitize or reject before use in file paths, commands, or rendered output; path traversal attacks use `../` sequences to escape intended directories.

### Validation layers

```
HTTP Layer: Content-Type, body size limits, JSON structure
Controller: @Valid, @RequestParam constraints (type conversion)
Service: Business rule validation (order must have items, amount > 0)
Database: Constraints (NOT NULL, CHECK, UNIQUE, FK)
```

### Path traversal attack

```
GET /files/download?name=../../etc/passwd
→ reads /var/www/uploads/../../etc/passwd = /etc/passwd
```

```java
// VULNERABLE
public byte[] download(@RequestParam String filename) {
    Path file = Paths.get("/uploads/" + filename); // ../../etc/passwd traversal!
    return Files.readAllBytes(file);
}

// SAFE
public byte[] download(@RequestParam String filename) {
    // Normalize and check the resolved path is within the allowed directory
    Path uploadDir = Paths.get("/uploads").toAbsolutePath().normalize();
    Path resolvedFile = uploadDir.resolve(filename).normalize();

    if (!resolvedFile.startsWith(uploadDir)) {
        throw new SecurityException("Path traversal attempt detected");
    }
    if (!Files.isRegularFile(resolvedFile)) {
        throw new ResourceNotFoundException("File not found");
    }
    return Files.readAllBytes(resolvedFile);
}
```

### XSS prevention

For APIs that return JSON, XSS is rarely a direct concern (JSON isn't rendered as HTML). But if you render HTML server-side or include user data in HTML responses:

```java
// Escape output in templates — Thymeleaf does this automatically with th:text
// Never use th:utext with user content
// Spring's HtmlUtils
String safe = HtmlUtils.htmlEscape(userInput);
```

### Deserialization vulnerabilities

Java deserialization of untrusted data can execute arbitrary code via gadget chains. Never deserialize untrusted streams with Java's native `ObjectInputStream`. Use `ObjectInputFilter` to restrict allowed classes:

```java
ObjectInputStream ois = new ObjectInputStream(inputStream);
ois.setObjectInputFilter(ObjectInputFilter.Config.createFilter("com.example.*;!*"));
```

Prefer JSON (Jackson) or Protobuf for all external data exchange.

### Input allowlist vs denylist

**Allowlist (preferred):** Define exactly what is valid and reject everything else.
```java
private static final Pattern SAFE_FILENAME = Pattern.compile("^[a-zA-Z0-9_\\-\\.]{1,100}$");
if (!SAFE_FILENAME.matcher(filename).matches()) throw new ValidationException("Invalid filename");
```

**Denylist (fragile):** Block known bad patterns — attackers find bypass via encoding, double-encoding, Unicode normalization. Only use as a secondary defense.

### Security headers

```java
http.headers(h -> h
    .frameOptions(HeadersConfigurer.FrameOptionsConfig::deny)       // X-Frame-Options: DENY
    .contentTypeOptions(withDefaults())                              // X-Content-Type-Options: nosniff
    .xssProtection(withDefaults())                                   // X-XSS-Protection: 1; mode=block
    .referrerPolicy(r -> r.policy(NO_REFERRER))
    .contentSecurityPolicy(csp -> csp.policyDirectives(
        "default-src 'self'; script-src 'self'; object-src 'none'"))
);
```
