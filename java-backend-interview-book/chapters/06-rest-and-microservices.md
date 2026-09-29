# Chapter 6. HTTP, REST APIs, and microservices

Examples use Spring Boot 3 with `RestClient`/`WebClient` and Resilience4j where a resilience library is needed. HTTP semantics are quoted from the RFC definitions of the methods and status codes; anything that is convention rather than specification is labelled as such.

## Q136. How do GET, POST, PUT, PATCH and DELETE differ?

**Priority:** Must Know  
**Why interviewers ask it:** Method semantics drive caching, retries and proxy behaviour, so getting them wrong has real operational consequences.

**Interview-ready answer:** `GET` is safe and idempotent: it must not change state, and caches and crawlers may repeat it freely. `POST` is neither safe nor idempotent; it is the general "process this" method and is the right choice for creating a resource whose identifier the server assigns. `PUT` replaces a resource at a known URI and is idempotent — sending it twice leaves the same state. `PATCH` applies a partial modification and is not idempotent in general, although a well-designed patch usually is. `DELETE` is idempotent in effect: the first call removes the resource and later calls find nothing to remove, which typically returns 404 or 204. Idempotency is the property that determines whether a client may safely retry after a timeout.

**In-depth explanation:** Safety and idempotency are contracts you must actually honour: a `GET` with side effects breaks caches and prefetchers, and an idempotent `PUT` that appends rather than replaces will corrupt data on retry. `PATCH` has two common formats — JSON Merge Patch (RFC 7386), where null means "remove", and JSON Patch (RFC 6902), an operation list — and picking one explicitly avoids ambiguity about partial updates. For `POST` creation, return 201 with a `Location` header; for asynchronous processing, return 202 with a status URL. Note that idempotency in HTTP is about the resulting state, not the response body: two `DELETE` calls may return different statuses while leaving the same state. Requests that are not naturally idempotent can be made retry-safe with an idempotency key, which is the standard approach for payments.

**Practical backend example:** Method choice mapped to real endpoints:

```java
@GetMapping("/api/orders/{id}")            // safe, cacheable, no side effects
public OrderResponse get(@PathVariable UUID id) { ... }

@PostMapping("/api/orders")                // server assigns the ID -> 201 + Location
public ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrder body) { ... }

@PutMapping("/api/orders/{id}/shipping-address")   // full replacement, idempotent
public ShippingAddress replaceAddress(@PathVariable UUID id, @Valid @RequestBody ShippingAddress a) { ... }

@PatchMapping(value = "/api/orders/{id}", consumes = "application/merge-patch+json")
public OrderResponse patch(@PathVariable UUID id, @RequestBody JsonMergePatch patch) { ... }

@DeleteMapping("/api/orders/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)      // 204; repeated calls leave the same state
public void delete(@PathVariable UUID id) { ... }
```

**Common follow-ups:**
- Is `DELETE` always repeat-safe? The resulting state is the same, though the status code may differ between the first and later calls.
- Can `POST` be made idempotent? Not by the method, but yes by an idempotency key stored with a unique constraint.
- When is `PUT` better than `PATCH`? When the client sends the full representation and you want replace semantics with natural idempotency.

**Mistakes to avoid:** Using `GET` for state changes because it is easy to call from a browser; `POST /getOrders`-style RPC over HTTP without a reason; `PUT` that merges instead of replacing; assuming `PATCH` is automatically idempotent.

**Production perspective:** Proxies, CDNs, service meshes and client libraries make retry decisions based on method semantics. If your `POST` is not idempotent and a gateway retries it after a timeout, you get duplicate orders — which is why idempotency keys exist.

**Related concepts covered:** Safety and idempotency, JSON Patch formats, 201 versus 202, idempotency keys, retry behaviour of intermediaries.

## Q137. Which HTTP status codes should an API use for common outcomes?

**Priority:** Must Know  
**Why interviewers ask it:** Status codes are the machine-readable part of your contract and drive client retries, alerts and dashboards.

**Interview-ready answer:** 200 for a successful read or update with a body, 201 with a `Location` header for creation, 202 when work is accepted for asynchronous processing, 204 for success with no body. On the client side: 400 for malformed input, 401 when authentication is missing or invalid, 403 when the caller is authenticated but not allowed, 404 for a missing resource, 409 for a state conflict such as a duplicate or a version mismatch, 422 when the payload is well-formed but semantically invalid, 429 for rate limiting with a `Retry-After` header. On the server side: 500 for unexpected errors, 502/504 for upstream failures and timeouts, and 503 when the service is deliberately unavailable or overloaded. The distinction that matters most is 4xx meaning "do not retry unchanged" versus 5xx and 429 meaning "retrying may help".

**In-depth explanation:** 401 versus 403 is precise: 401 means the request lacks valid credentials — and the response should include `WWW-Authenticate` — while 403 means the identity is known and still not permitted. 404 versus 403 also has a security dimension: returning 404 for resources the caller may not see avoids leaking their existence, which is often preferable for multi-tenant APIs. 409 versus 422 is conventional rather than strictly specified; the important thing is to be consistent across your API and document it. Never return 200 with an error body: it defeats generic monitoring, client error handling and gateway retry policies. Include `Retry-After` on 429 and 503 so clients back off intelligently rather than hammering.

**Practical backend example:** Mapping domain outcomes to codes in one place:

```java
@RestControllerAdvice
class StatusMapping {
    @ExceptionHandler(OrderNotFoundException.class)
    ProblemDetail notFound(OrderNotFoundException e) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, e.getMessage());        // 404
    }
    @ExceptionHandler(DuplicateOrderException.class)
    ProblemDetail conflict(DuplicateOrderException e) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, e.getMessage());         // 409
    }
    @ExceptionHandler(RateLimitExceededException.class)
    ResponseEntity<ProblemDetail> throttled(RateLimitExceededException e) {
        return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                .header(HttpHeaders.RETRY_AFTER, String.valueOf(e.retryAfterSeconds()))       // 429
                .body(ProblemDetail.forStatus(HttpStatus.TOO_MANY_REQUESTS));
    }
}
```

**Common follow-ups:**
- When do you return 409 versus 422? 409 for a conflict with current state (duplicate, stale version); 422 for a syntactically valid payload that violates semantic rules. Be consistent and document the choice.
- 401 or 403 for an expired token? 401, because the credentials are no longer valid; include `WWW-Authenticate`.
- Should a missing resource the user cannot access return 404? Often yes, to avoid confirming that it exists.

**Mistakes to avoid:** 200 with `{"error": ...}`; 500 for validation failures; 403 for unauthenticated requests; omitting `Retry-After` on throttling responses; inventing non-standard codes.

**Production perspective:** Dashboards and alerts are usually built on status classes. If validation errors are reported as 500, every client bug pages your on-call engineer; if real failures are reported as 200, nothing pages anyone.

**Related concepts covered:** Retry semantics, Retry-After, information disclosure, ProblemDetail, monitoring by status class.

## Q138. How would you design a resource-oriented order API?

**Priority:** Must Know  
**Why interviewers ask it:** It shows whether you can translate a business process into a clean, evolvable HTTP interface.

**Interview-ready answer:** I model nouns as resources with stable URIs and use methods for the verbs: `/orders` for the collection, `/orders/{id}` for the item, `/orders/{id}/lines` for sub-resources. State transitions that are not simple updates become sub-resources rather than verbs in the path — `POST /orders/{id}/cancellation` instead of `POST /cancelOrder`. Representations are DTOs, not entities, with explicit field names, ISO-8601 timestamps in UTC and monetary amounts as integer minor units with a currency code. I design for pagination and filtering from the start, return 201 with a `Location` on creation, and keep the contract additive so it can evolve. Where a process genuinely does not map onto a resource, a well-named action endpoint is better than a contorted abstraction.

**In-depth explanation:** Consistency matters more than REST purism: plural collection names, the same pagination parameters everywhere, the same error shape and the same date format across every endpoint. Nesting should stop at one or two levels — `/customers/{id}/orders` is useful for scoping, but deep nesting makes URIs brittle when relationships change. Expose the identifiers clients need and avoid leaking internal sequence IDs when they can be enumerated; UUIDs or opaque IDs reduce that risk. Think about concurrency in the design: an `ETag` plus `If-Match` gives optimistic concurrency at the HTTP level. Also decide early whether partial responses (sparse fieldsets) or embedded sub-resources are supported, because adding them later changes response shapes.

**Practical backend example:** A coherent resource layout:

```text
GET    /api/orders?status=PAID&customerId=...&page=...&size=...   list with filters
POST   /api/orders                                               create -> 201 + Location
GET    /api/orders/{orderId}                                     read one
PATCH  /api/orders/{orderId}                                     partial update
POST   /api/orders/{orderId}/cancellation                        state transition as a sub-resource
GET    /api/orders/{orderId}/lines                               sub-collection
PUT    /api/orders/{orderId}/shipping-address                    replace a component
```

```json
{
  "id": "1f0b2a5e-9c2d-4f7a-8f0e-8a1b2c3d4e5f",
  "status": "PAID",
  "createdAt": "2026-03-14T09:21:00Z",
  "total": { "amountMinor": 129900, "currency": "EUR" },
  "lines": [ { "sku": "ABC-000001", "quantity": 2 } ]
}
```

**Common follow-ups:**
- Should verbs appear in URLs? Prefer resources and sub-resources; a clearly named action endpoint is acceptable when no resource fits.
- How do you represent money? Integer minor units plus a currency code, never a floating-point number.
- How deep should nesting go? One or two levels; beyond that, use top-level resources with filters.

**Mistakes to avoid:** RPC-style endpoints such as `/api/doOrderStuff`; exposing database column names; inconsistent date formats; returning different error shapes per endpoint; sequential integer IDs that let clients enumerate other customers' data.

**Production perspective:** An API is a long-lived contract; clients you do not control will depend on details you considered incidental. Write the OpenAPI specification alongside the implementation and treat breaking changes as a release process, not a code change.

**Related concepts covered:** Resource modelling, sub-resources for transitions, representation design, OpenAPI, opaque identifiers, ETags.

## Q139. How should validation and error responses be structured?

**Priority:** Must Know  
**Why interviewers ask it:** Error design is where APIs most often become inconsistent, and clients suffer for years afterwards.

**Interview-ready answer:** One error shape for the whole API. In Spring Boot 3 I use `ProblemDetail` (RFC 7807), which gives `type`, `title`, `status`, `detail` and `instance`, and I add a machine-readable error code, a list of field errors for validation failures, and a correlation ID for support. Clients should branch on the status code and the stable error code, never on prose. Messages must be safe: no stack traces, no SQL, no internal hostnames, and no echoing of sensitive input values. Validation failures return 400 with every field error listed at once, so a form can display them all rather than one per round trip.

**In-depth explanation:** A stable `code` field matters because `title` and `detail` are human text that may be reworded or localised. Locale handling belongs in the client where possible; if the server localises, it should still keep the code stable. Distinguish client-visible detail from internal detail: log the exception with full context and the correlation ID, then return a short safe message with that same ID. For bulk operations, decide and document whether the response is all-or-nothing or a per-item result list — 207-style multi-status semantics need explicit design. Finally, version the error contract alongside the API: adding a field is safe, changing the meaning of `code` values is not.

**Practical backend example:** A consistent, safe error payload:

```java
@ExceptionHandler(MethodArgumentNotValidException.class)
ProblemDetail onValidation(MethodArgumentNotValidException ex) {
    ProblemDetail p = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
    p.setType(URI.create("https://api.example.com/problems/validation-failed"));
    p.setTitle("Validation failed");
    p.setProperty("code", "VALIDATION_FAILED");                 // stable, machine-readable
    p.setProperty("errors", ex.getBindingResult().getFieldErrors().stream()
            .map(fe -> Map.of("field", fe.getField(), "message", fe.getDefaultMessage()))
            .toList());
    p.setProperty("correlationId", MDC.get("correlationId"));
    return p;
}

@ExceptionHandler(Exception.class)
ProblemDetail onUnexpected(Exception ex) {
    String id = MDC.get("correlationId");
    log.error("unhandled error correlationId={}", id, ex);      // full detail stays in the logs
    ProblemDetail p = ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR,
            "Unexpected error. Quote the correlation id when contacting support.");
    p.setProperty("correlationId", id);
    return p;                                                    // nothing internal leaks
}
```

**Common follow-ups:**
- How do you avoid leaking internals? Log the detail server-side and return a generic message plus a correlation ID.
- Should errors be localised? Keep a stable machine-readable code; localise only human-facing text, ideally in the client.
- One error or all errors for validation? Return all field errors in one response.

**Mistakes to avoid:** Different error shapes per controller; returning exception class names; embedding SQL or stack traces; using HTTP 200 with an error object; unstable error codes.

**Production perspective:** A correlation ID that appears in the response, the logs and the trace turns a vague user complaint into a two-minute investigation. Make it mandatory in every error path, including the security filter chain.

**Related concepts covered:** RFC 7807 ProblemDetail, error codes, correlation IDs, information disclosure, bulk operation semantics.

## Q140. How would you implement pagination, filtering and stable sorting?

**Priority:** Must Know  
**Why interviewers ask it:** List endpoints are where APIs meet database performance, and unstable paging is a classic bug.

**Interview-ready answer:** I expose a bounded page size with a server-side maximum, a documented default sort, and a tie-breaker on a unique column so ordering is deterministic. For shallow pages, offset-based paging is acceptable and simple; for deep or high-volume access I use cursor-based paging, where the cursor encodes the last seen sort key. Filters map to indexed columns and are validated against an allowlist so clients cannot sort or filter by arbitrary fields — that is both a performance and an injection concern. The response includes the items and paging metadata: next cursor or page number, page size, and a total only if it can be produced cheaply.

**In-depth explanation:** Unstable sorting is the subtle failure: sorting only by `created_at` when several rows share a timestamp lets rows move between pages, so users see duplicates or miss items. Adding the primary key as a final sort key fixes it. Total counts are expensive on large filtered sets; many APIs return `hasMore` instead, or an approximate count. Allowlisting sort fields prevents a client from sorting by an unindexed column and triggering a full table sort. Cursors should be opaque — base64 of the keyset values — so the implementation can change. Also cap `size`: without a maximum, one client can request a million rows and exhaust memory on both sides.

**Practical backend example:** A cursor-paged endpoint with validated inputs:

```java
private static final Set<String> SORTABLE = Set.of("createdAt", "totalCents");

@GetMapping("/api/orders")
public CursorPage<OrderSummary> list(
        @RequestParam(required = false) OrderStatus status,
        @RequestParam(defaultValue = "createdAt") String sort,
        @RequestParam(required = false) String cursor,
        @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {   // hard cap
    if (!SORTABLE.contains(sort)) throw new InvalidSortException(sort);    // allowlist
    Cursor decoded = Cursor.decode(cursor);                                // opaque to clients
    List<OrderSummary> rows = orderQueryService.page(status, sort, decoded, size + 1);
    boolean hasMore = rows.size() > size;                                  // avoids a COUNT query
    return CursorPage.of(rows.subList(0, Math.min(size, rows.size())), hasMore);
}
```

**Common follow-ups:**
- What happens if rows are inserted between pages? With offsets, items shift and can duplicate or disappear; cursors are stable.
- How do you return a total without a slow count? Return `hasMore`, or use an approximate count from statistics when an estimate suffices.
- Why allowlist sort fields? To keep queries on indexed columns and to avoid dynamic SQL built from user input.

**Mistakes to avoid:** Unbounded `size`; sorting by a non-unique column only; `COUNT(*)` on every request; exposing raw offsets in cursors; allowing arbitrary filter expressions from clients.

**Production perspective:** List endpoints are usually the highest-traffic part of an API and the easiest to regress. Load test them with production-like data volumes, and monitor page-size distribution — a client requesting size 100 every time may need a bulk export instead.

**Related concepts covered:** Keyset pagination, deterministic ordering, allowlists, count query cost, opaque cursors, rate limiting interaction.

## Q141. How does idempotency make payment creation retry-safe?

**Priority:** Must Know  
**Why interviewers ask it:** Network timeouts are inevitable, and duplicate payments are the textbook consequence of ignoring them.

**Interview-ready answer:** The client generates a unique idempotency key per logical operation and sends it as a header. The server stores that key with a unique constraint in the same transaction that creates the payment. If the same key arrives again, the insert conflicts and the server returns the original result instead of creating a second payment. The key must be tied to the request content so a different payload with the same key is rejected rather than silently returning the wrong result, and keys need a retention period long enough to cover client retry windows. This turns a non-idempotent `POST` into a retry-safe operation without changing HTTP semantics.

**In-depth explanation:** The critical detail is atomicity: recording the key and performing the effect must be in one transaction, otherwise a crash between them reopens the duplicate window. Concurrent retries need handling too — two simultaneous requests with the same key should not both proceed; the unique constraint resolves that by failing one, which then waits for or returns the stored result. Storing a hash of the request body lets you return 409 or 422 when the same key is reused with different content, which catches client bugs. Decide the response for a replay: returning the original 201 response body is the friendliest and is what major payment APIs do. Finally, downstream calls need their own idempotency: pass the key to the payment provider so their system also deduplicates.

**Practical backend example:** Key storage, replay and conflicting reuse:

```sql
CREATE TABLE idempotency_record (
    key            text PRIMARY KEY,
    request_hash   text        NOT NULL,
    response_body  jsonb       NOT NULL,
    status_code    int         NOT NULL,
    created_at     timestamptz NOT NULL DEFAULT now()
);
```

```java
@PostMapping("/api/payments")
public ResponseEntity<PaymentResponse> create(@RequestHeader("Idempotency-Key") String key,
                                              @Valid @RequestBody CreatePayment body) {
    String hash = Hashing.sha256(body);
    Optional<IdempotencyRecord> existing = idempotencyRepository.find(key);
    if (existing.isPresent()) {
        if (!existing.get().requestHash().equals(hash)) {
            throw new IdempotencyKeyReusedException(key);          // 409: same key, different payload
        }
        return existing.get().toResponse();                        // replay the original result
    }
    return paymentService.createAtomically(key, hash, body);       // insert key + payment in one tx
}
```

**Common follow-ups:**
- What if the same key arrives with a different body? Reject it (409); silently returning the old result would hide a client bug.
- How long should keys be kept? Long enough to cover client retries and reconciliation — commonly 24 hours to a few days — then purge.
- Who generates the key? The client, once per logical operation, and it must reuse the same key for retries of that operation.

**Mistakes to avoid:** Generating the key on the server; storing the key after performing the effect; no unique constraint; treating a duplicate as an error rather than returning the original outcome; unbounded key tables.

**Production perspective:** Idempotency keys are what make automatic retries — by clients, gateways and service meshes — safe. Combine them with an outbox for downstream effects, and reconcile with the provider daily to catch the cases where you never learned the outcome.

**Related concepts covered:** Unique constraints, exactly-once effects, retry safety, request hashing, key retention, downstream idempotency.

## Q142. What are ETag and Cache-Control used for?

**Priority:** Important  
**Why interviewers ask it:** HTTP caching is free performance that most backend developers under-use, and ETags also provide concurrency control.

**Interview-ready answer:** `Cache-Control` tells clients and intermediaries whether and how long a response may be reused — `max-age`, `no-store` for sensitive data, `private` for per-user responses, `must-revalidate` for freshness. `ETag` is a validator: the server returns a version token for a representation, and the client sends it back with `If-None-Match`; if nothing changed the server responds 304 with no body, saving bandwidth. The same mechanism works for writes: `If-Match` with the current ETag gives optimistic concurrency, so a `PUT` fails with 412 if someone else modified the resource in the meantime. `Last-Modified` with `If-Modified-Since` is the coarser, timestamp-based alternative.

**In-depth explanation:** Strong ETags mean byte-identical representations; weak ETags (`W/"..."`) mean semantically equivalent, which is usually what you want when the payload includes a rendering timestamp. Generating an ETag from an entity version column is cheap and stable; hashing the serialised body is simpler but costs the serialisation work you were trying to avoid. Caching rules are easy to get wrong for authenticated responses: mark them `private` and `no-store` when they contain personal data, and use `Vary: Accept, Authorization` so a shared cache does not serve one user's data to another. Note that 304 responses still require the request to reach the server unless a cache is allowed to serve without revalidation — ETags save bandwidth and rendering, not round trips.

**Practical backend example:** Conditional read plus optimistic write:

```java
@GetMapping("/api/products/{id}")
public ResponseEntity<ProductResponse> get(@PathVariable UUID id,
                                           @RequestHeader(value = "If-None-Match", required = false) String inm) {
    Product product = productService.get(id);
    String etag = "\"v" + product.getVersion() + "\"";          // from the @Version column
    if (etag.equals(inm)) {
        return ResponseEntity.status(HttpStatus.NOT_MODIFIED).eTag(etag).build();   // 304, no body
    }
    return ResponseEntity.ok()
            .eTag(etag)
            .cacheControl(CacheControl.maxAge(Duration.ofMinutes(5)).cachePublic())
            .body(ProductResponse.from(product));
}

@PutMapping("/api/products/{id}")
public ResponseEntity<ProductResponse> update(@PathVariable UUID id,
                                              @RequestHeader("If-Match") String ifMatch,
                                              @Valid @RequestBody UpdateProduct body) {
    long expectedVersion = parseVersion(ifMatch);
    return productService.update(id, expectedVersion, body)     // throws -> 412 Precondition Failed
            .map(p -> ResponseEntity.ok(ProductResponse.from(p)))
            .orElseThrow(() -> new PreconditionFailedException(id));
}
```

**Common follow-ups:**
- What does 304 mean? Not Modified — the cached representation is still valid, and no body is sent.
- How do ETags help with concurrency? `If-Match` lets the server reject an update based on a stale version with 412.
- What should you never cache? Anything personal or authorised for a specific user in a shared cache; use `private`/`no-store` and `Vary`.

**Mistakes to avoid:** Caching authenticated responses publicly; generating ETags by hashing a payload that includes a timestamp; forgetting `Vary`; using `no-cache` when you mean `no-store`.

**Production perspective:** For read-heavy APIs behind a CDN, correct cache headers reduce origin load dramatically. Measure cache hit ratio and 304 rates; a caching layer that never hits is just latency.

**Related concepts covered:** Conditional requests, optimistic concurrency over HTTP, Vary headers, CDN behaviour, weak versus strong validators.

## Q143. How do timeouts, retries and backoff interact?

**Priority:** Must Know  
**Why interviewers ask it:** Naive retries turn a small downstream slowdown into a self-inflicted outage.

**Interview-ready answer:** Every outbound call needs a connect timeout and a read timeout, both shorter than the caller's own deadline, otherwise threads pile up waiting. Retries should only apply to safe or idempotent operations and to failures that could plausibly succeed on a second attempt — connection errors, 503, 429, and timeouts on idempotent requests. They must use exponential backoff with jitter to avoid synchronised retry storms, and a retry budget or attempt cap so the total work is bounded. Crucially, retries multiply load exactly when the downstream is struggling, so they belong behind a circuit breaker. I also propagate a deadline so that an inner retry never exceeds the time the caller is still willing to wait.

**In-depth explanation:** The mathematics matter: three attempts per call across three service hops is up to 27 requests for one user action. A retry budget — for example, retries may be at most 10% of requests — prevents amplification. Jitter is not optional; without it, all clients that failed at the same moment retry at the same moment. Timeouts should be derived from observed latency percentiles rather than guessed round numbers, and they should be tighter than the upstream deadline minus the time already spent. Non-idempotent operations can still be retried if they carry an idempotency key. Finally, distinguish fast failures from slow ones: a connection refused can be retried almost immediately, while a timeout suggests overload and deserves a longer wait.

**Practical backend example:** Bounded retries with jitter and a deadline:

```java
@Bean
RestClient paymentsClient(RestClient.Builder builder) {
    var factory = new SimpleClientHttpRequestFactory();
    factory.setConnectTimeout(Duration.ofMillis(500));     // always set both
    factory.setReadTimeout(Duration.ofMillis(1500));
    return builder.baseUrl(paymentsBaseUrl).requestFactory(factory).build();
}

@Bean
RetryRegistry retryRegistry() {
    return RetryRegistry.of(RetryConfig.custom()
            .maxAttempts(3)
            .intervalFunction(IntervalFunction.ofExponentialRandomBackoff(
                    Duration.ofMillis(100), 2.0, 0.5))      // exponential + jitter
            .retryExceptions(IOException.class, TimeoutException.class)
            .retryOnResult(r -> r instanceof ResponseEntity<?> re
                    && (re.getStatusCode().value() == 503 || re.getStatusCode().value() == 429))
            .failAfterMaxAttempts(true)
            .build());
}
```

**Common follow-ups:**
- Which requests are safe to retry? Idempotent ones, or non-idempotent ones carrying an idempotency key.
- Why jitter? To de-synchronise clients that all failed at the same instant and would otherwise retry together.
- How do you stop retry amplification? A retry budget, a circuit breaker, and deadlines propagated across hops.

**Mistakes to avoid:** Retrying 4xx errors; infinite retries; the same timeout at every layer so nothing fails fast; retrying inside a database transaction; no jitter.

**Production perspective:** Instrument attempts, retry counts and timeout counts separately from errors. A retry spike is an early warning, and a retry rate that exceeds your budget during an incident is usually making the incident worse.

**Related concepts covered:** Deadlines, exponential backoff with jitter, retry budgets, circuit breakers, idempotency, timeout tuning from percentiles.

## Q144. When should you add a circuit breaker or bulkhead?

**Priority:** Important  
**Why interviewers ask it:** Resilience patterns are frequently name-dropped; the interviewer wants to know when each is warranted and what it costs.

**Interview-ready answer:** A circuit breaker protects a caller from a failing dependency: after a failure-rate threshold it opens and fails fast for a cool-down period, then allows trial calls in a half-open state before closing again. That preserves the caller's threads and gives the downstream room to recover. A bulkhead limits how much concurrency any one dependency can consume — a semaphore or a dedicated thread pool — so a slow dependency cannot starve the whole service. I add them for remote dependencies that are slow or unreliable and where a fallback or degraded response exists. They are not substitutes for timeouts: without a timeout, calls never fail, so the breaker never trips.

**In-depth explanation:** Configuration is where these go wrong. Thresholds based on too few calls flap; a minimum call count and a sliding window make the decision stable. The fallback must be genuinely acceptable — a cached value, an empty list, a "temporarily unavailable" field — because a fallback that fabricates data is worse than an error. Opening a breaker on a non-idempotent write is risky if the request may have succeeded; treat the outcome as unknown and reconcile. Bulkheads are often the simpler and more effective tool: a semaphore of 10 permits per dependency prevents resource monopolisation with far less configuration. Combine them with health-based routing at the infrastructure layer where available.

**Practical backend example:** Breaker plus bulkhead with a meaningful fallback:

```java
@Bean
CircuitBreakerConfig recommendationsBreaker() {
    return CircuitBreakerConfig.custom()
            .slidingWindowType(SlidingWindowType.COUNT_BASED)
            .slidingWindowSize(50)
            .minimumNumberOfCalls(20)             // avoid flapping on tiny samples
            .failureRateThreshold(50)
            .waitDurationInOpenState(Duration.ofSeconds(10))
            .permittedNumberOfCallsInHalfOpenState(5)
            .build();
}

@CircuitBreaker(name = "recommendations", fallbackMethod = "popularFallback")
@Bulkhead(name = "recommendations", type = Bulkhead.Type.SEMAPHORE)   // cap concurrency
public List<Product> recommend(UUID userId) { return recommendationClient.fetch(userId); }

private List<Product> popularFallback(UUID userId, Throwable t) {
    return popularProductsCache.get();     // degraded but honest: still useful content
}
```

**Common follow-ups:**
- Can a breaker replace a timeout? No; without timeouts, calls hang and failures are never counted.
- What is a good fallback? Cached or default data, or an explicit partial response — never fabricated business data.
- When is a bulkhead enough on its own? When the dependency is optional and you mainly need to protect shared capacity.

**Mistakes to avoid:** Breakers on every internal call regardless of need; thresholds that trip on three requests; fallbacks that silently return wrong data; forgetting that an open breaker on a write leaves an unknown outcome.

**Production perspective:** Export breaker state transitions as events and alert on prolonged open states — that is a dependency outage, not a blip. Test the fallback path deliberately, because untested fallbacks are usually broken when finally needed.

**Related concepts covered:** Failure isolation, semaphore bulkheads, fallback design, half-open probing, health-based routing.

## Q145. How do synchronous calls compare with asynchronous messaging?

**Priority:** Must Know  
**Why interviewers ask it:** Choosing the interaction style is an architecture decision with consequences for coupling, latency and consistency.

**Interview-ready answer:** A synchronous call gives an immediate answer and simple reasoning: the caller knows the outcome. The price is temporal coupling — if the callee is down or slow, the caller is affected — and cascading failures across a call chain. Asynchronous messaging decouples availability: the producer writes to a broker and continues, and the consumer processes when it can, which absorbs spikes and survives short outages. The price is eventual consistency, duplicate delivery to handle, out-of-order messages, and harder end-to-end debugging. My rule: use synchronous calls when the caller needs the result to continue — a price quote, an authorisation check — and messaging for side effects and notifications that can complete later.

**In-depth explanation:** Read operations that block a user response are naturally synchronous. Writes that trigger downstream work — send an email, update a search index, notify a partner — are naturally asynchronous, and doing them synchronously couples your checkout availability to an email provider. A hybrid pattern is common: accept the request synchronously, return 202 with a status URL, and complete the work asynchronously. Whatever the style, the client experience must be designed: what does the user see while the work is pending, and how do they learn the outcome? Messaging also shifts operational burden to the broker: partitions, consumer lag, dead-letter queues and replay all become things you must monitor.

**Practical backend example:** Synchronous where the answer is needed, asynchronous for the rest:

```java
@Transactional
public OrderResponse place(PlaceOrderCommand cmd) {
    AuthorizationResult auth = paymentClient.authorize(cmd.payment());   // synchronous: needed now
    if (!auth.approved()) throw new PaymentDeclinedException(auth.reason());

    Order order = orderRepository.save(Order.from(cmd, auth));
    outbox.append(new OrderPlaced(order.id()));    // asynchronous: email, invoicing, analytics
    return OrderResponse.from(order);              // fast response, side effects follow
}
```

**Common follow-ups:**
- How do clients see the result of async work? Polling a status endpoint, a webhook, or a push notification; design it explicitly.
- Does messaging remove failure? No; it moves it to consumer lag, retries and dead letters, which need monitoring.
- What about request/reply over a broker? Possible, but it reintroduces temporal coupling with added complexity — usually prefer HTTP.

**Mistakes to avoid:** Making checkout depend synchronously on non-essential services; using messaging for something the user is waiting for without status feedback; assuming messaging guarantees ordering or exactly-once delivery.

**Production perspective:** Every synchronous dependency multiplies your availability: three dependencies at 99.9% give roughly 99.7% combined. Removing non-essential synchronous calls is often the cheapest reliability improvement available.

**Related concepts covered:** Temporal coupling, availability multiplication, 202 Accepted flows, eventual consistency, consumer lag monitoring.

## Q146. How would you version an API without breaking clients?

**Priority:** Important  
**Why interviewers ask it:** Versioning strategy shows whether you think about clients you cannot deploy.

**Interview-ready answer:** The cheapest version is the one you never need: design for additive change, so adding an optional field or a new endpoint does not break anyone, and require clients to ignore unknown fields. When a genuinely breaking change is unavoidable — removing a field, changing a type, changing semantics — I introduce a new version, most commonly as a URI prefix such as `/api/v2/orders` because it is explicit, easy to route and easy to log. Header or media-type versioning is more purist but harder to debug and cache. I then run both versions in parallel, publish a deprecation timeline with `Deprecation` and `Sunset` headers, measure usage per version, and remove the old one only when traffic has stopped.

**In-depth explanation:** Breaking versus non-breaking is worth being precise about. Non-breaking: adding an optional request field, adding a response field, adding an endpoint, adding an enum value only if clients tolerate unknown values. Breaking: removing or renaming fields, changing types or formats, tightening validation, changing default behaviour, adding a required request field, and — often overlooked — changing error codes or status semantics. Enum extension is the classic trap: clients that switch exhaustively on a value will fail when a new one appears, so document the tolerance requirement from day one. Internal service-to-service APIs can evolve faster with consumer-driven contract tests, while public APIs need long support windows. Whatever you choose, version the contract, not the internal code.

**Practical backend example:** Running two versions side by side with deprecation signalling:

```java
@RestController
@RequestMapping("/api/v1/orders")
public class OrderControllerV1 {
    @GetMapping("/{id}")
    public ResponseEntity<OrderResponseV1> get(@PathVariable UUID id) {
        return ResponseEntity.ok()
                .header("Deprecation", "true")
                .header("Sunset", "Wed, 30 Sep 2026 23:59:59 GMT")     // machine-readable timeline
                .header("Link", "</api/v2/orders>; rel=\"successor-version\"")
                .body(OrderResponseV1.from(orderService.get(id)));
    }
}

@RestController
@RequestMapping("/api/v2/orders")            // v2: money as an object, status renamed
public class OrderControllerV2 { /* ... */ }
```

**Common follow-ups:**
- Is adding a field always safe? Adding an optional field is safe if clients ignore unknown fields; adding a required request field is breaking.
- URI or header versioning? URI is explicit and simple to operate; media-type versioning is cleaner in theory but harder to debug and cache.
- How do you know when to remove v1? Per-version usage metrics plus an announced sunset date.

**Mistakes to avoid:** Versioning every internal refactor; maintaining five versions indefinitely; changing semantics within a version; breaking clients by tightening validation without notice.

**Production perspective:** Track requests per version per client so deprecation is data-driven and you can contact the specific consumers still using v1. Contract tests against both versions prevent accidental regressions while they coexist.

**Related concepts covered:** Backward compatibility rules, deprecation headers, consumer-driven contract testing, enum evolution, client identification.

## Q147. How do correlation IDs and trace context travel across services?

**Priority:** Important  
**Why interviewers ask it:** Distributed debugging is impossible without propagated context, and this is a practical, testable skill.

**Interview-ready answer:** The entry point — gateway or first service — generates a trace ID if none is present and puts it in a standard header, today usually W3C `traceparent`, often alongside an application correlation ID. Every service reads it, adds it to the logging context (MDC), includes it in log lines and error responses, and forwards it on outbound calls, including message headers for asynchronous hops. In Spring Boot 3 this is handled by Micrometer Tracing with an exporter such as OpenTelemetry, which instruments the web layer, `RestClient`/`WebClient` and messaging automatically. The discipline required is to propagate context across thread boundaries — async executors and message consumers — and to clear it afterwards so pooled threads do not leak it.

**In-depth explanation:** A trace is a tree of spans; each span has a trace ID, a span ID and a parent. `traceparent` carries those, and `baggage` can carry a small amount of user-defined context — with caution, since baggage crosses trust boundaries and must never contain personal data. Sampling is the other practical concern: tracing every request is expensive at high volume, so head-based sampling with a percentage plus always-sample-on-error is typical. For logs to be joinable with traces, the trace ID must be in the log line, ideally in a structured JSON field. Asynchronous hops need explicit propagation: put the trace context in Kafka headers and restore it in the consumer, otherwise the trace ends at the producer.

**Practical backend example:** Structured logs carrying trace identifiers:

```yaml
management:
  tracing:
    sampling:
      probability: 0.1            # sample 10% of traces; errors are typically always sampled
logging:
  pattern:
    level: "%5p [${spring.application.name},%X{traceId:-},%X{spanId:-}]"
```

```java
@Component
public class OrderEventProducer {
    private final KafkaTemplate<String, String> kafka;
    private final Propagator propagator;

    public void publish(OrderPlaced event) {
        ProducerRecord<String, String> record =
                new ProducerRecord<>("orders", event.orderId().toString(), json.write(event));
        propagator.inject(tracer.currentTraceContext().context(), record.headers(),
                (headers, key, value) -> headers.add(key, value.getBytes(UTF_8)));  // async hop
        kafka.send(record);
    }
}
```

**Common follow-ups:**
- Why not log personal data alongside the trace? Logs are widely accessible and retained; identifiers should be opaque, and personal data needs minimisation and redaction.
- What happens on an async hop? Context must be injected into message headers and extracted by the consumer, or the trace breaks.
- How much should you sample? Enough to diagnose typical behaviour — often 1–10% — with errors and slow requests always captured.

**Mistakes to avoid:** Inventing a custom header when a standard exists; logging the trace ID in some services but not others; forgetting to clear MDC in pooled threads; putting sensitive data in baggage.

**Production perspective:** The single highest-value observability investment for a multi-service system is a trace ID that appears in every log line and every error response. It converts "some requests are slow" into "this span in this service is slow".

**Related concepts covered:** W3C trace context, MDC, sampling strategies, message header propagation, structured logging, data minimisation.

## Q148. What failure modes occur with a chain of service calls?

**Priority:** Important  
**Why interviewers ask it:** Reasoning about partial failure is the core skill of distributed backend work.

**Interview-ready answer:** The main modes are cascading failure, where a slow dependency consumes the caller's threads and spreads upward; partial failure, where some steps of a multi-step operation succeeded and others did not, leaving inconsistent state; timeout ambiguity, where you do not know whether the remote side applied the change; retry amplification, where every layer retries and multiplies load; and availability multiplication, where a chain of 99.9% services produces a much lower combined figure. The mitigations are deadlines propagated across hops, bulkheads and breakers, idempotency so retries are safe, compensating actions or reconciliation for partial failures, and removing unnecessary synchronous dependencies from critical paths.

**In-depth explanation:** Deadline propagation deserves emphasis: if the user-facing request has a 2-second budget and 1.2 seconds are already spent, the next hop should be given at most the remainder, not a fixed 3-second timeout. Without that, inner services keep working on requests nobody is waiting for. Partial failure needs a decision per workflow: compensate (undo the earlier steps), retry forward (keep trying until it succeeds, which requires idempotency), or reconcile later. Sagas formalise the compensating approach for long-running workflows. Graceful degradation is often better than failure: return the page without recommendations rather than a 500. Finally, test these paths — fault injection or chaos experiments reveal that most fallbacks have never actually run.

**Practical backend example:** Deadline-aware fan-out with degradation:

```java
public Dashboard load(UUID userId, Duration budget) {
    Instant deadline = Instant.now().plus(budget);
    Duration remaining = () -> Duration.between(Instant.now(), deadline);

    Profile profile = call(() -> profileClient.fetch(userId), remaining.get().dividedBy(2),
                           () -> Profile.unknown(userId));            // essential, has a fallback
    List<Offer> offers = remaining.get().isNegative()
            ? List.of()                                               // budget exhausted: skip
            : call(() -> offerClient.fetch(userId), remaining.get(), List::of);
    return new Dashboard(profile, offers);
}
```

**Common follow-ups:**
- What is a deadline? The absolute time by which the whole operation must finish; each hop gets the remaining budget, not a fixed timeout.
- How do you handle a partially applied workflow? Compensate, retry forward with idempotency, or reconcile asynchronously — decide per workflow and document it.
- Why does a chain reduce availability? Serial dependencies multiply: three 99.9% services yield about 99.7%.

**Mistakes to avoid:** Fixed timeouts at every hop; assuming a failed call did nothing; unbounded retries; treating every dependency as essential; untested fallbacks.

**Production perspective:** Draw the dependency graph for your critical path and mark each dependency as essential or optional. Most teams discover that several "essential" calls can degrade gracefully, which is the cheapest reliability win available.

**Related concepts covered:** Deadline propagation, sagas and compensation, graceful degradation, availability math, chaos testing.

## Q149. What is eventual consistency and when is it acceptable?

**Priority:** Important  
**Why interviewers ask it:** It tests whether you can reason about consistency as a product decision, not just a technical one.

**Interview-ready answer:** Eventual consistency means that after a change, different parts of the system converge to the same state after some delay rather than instantly. It is the normal outcome when data is replicated or propagated by events: the order database commits, and the search index or the analytics store updates moments later. It is acceptable when the business tolerates a short window of staleness — search results, recommendations, dashboards, notification delivery. It is not acceptable where a stale read causes a wrong decision, such as an account balance used for authorisation or stock at the point of sale. The key design work is making the window visible and bounded, and giving users read-your-writes behaviour where they would otherwise be confused.

**In-depth explanation:** Read-your-writes is the most common usability requirement: after a user edits something, they must see their own change. Techniques include reading from the primary for a short period after a write, passing a version token the read path waits for, or optimistically rendering the local change. Monitoring must include the lag itself — replication lag, consumer lag, index freshness — with alerts, because "eventually" without a bound is not a guarantee. UI design matters too: showing "processing" rather than an incorrect value manages expectations. Also, eventual consistency interacts with idempotency and ordering: if events can arrive out of order, apply them with version checks so an older update cannot overwrite a newer one.

**Practical backend example:** Version-guarded projection updates plus a freshness metric:

```java
@KafkaListener(topics = "orders")
public void onOrderChanged(OrderChanged event) {
    // ignore stale events: never let an older version overwrite a newer projection
    int updated = projectionRepository.updateIfNewer(event.orderId(), event.version(), event.payload());
    if (updated == 0) {
        log.debug("ignored stale event order={} version={}", event.orderId(), event.version());
    }
    freshnessGauge.set(Duration.between(event.occurredAt(), Instant.now()).toMillis());
}
```

```sql
UPDATE order_projection SET payload = :payload, version = :version, updated_at = now()
WHERE order_id = :orderId AND version < :version;    -- monotonic, out-of-order safe
```

**Common follow-ups:**
- How do users see pending state? Show an explicit "processing" state, or read from the primary so they see their own writes.
- How do you bound the delay? Monitor replication and consumer lag with alerts, and define an SLO for freshness.
- What if events arrive out of order? Apply version or timestamp guards so older data cannot overwrite newer data.

**Mistakes to avoid:** Using eventually consistent data for authorisation or money; no lag monitoring; assuming ordering is guaranteed; showing stale data as if it were current.

**Production perspective:** Freshness is a service level objective like latency. Define it, measure it, and alert on it; otherwise a stalled consumer silently serves month-old data and nobody notices until a customer complains.

**Related concepts covered:** Read-your-writes, replication and consumer lag, out-of-order handling, projection design, freshness SLOs.

## Q150. How would you design an order placement workflow end to end?

**Priority:** Must Know  
**Why interviewers ask it:** It is an appropriately scoped design question that reveals how you combine API, transaction, payment and event concerns.

**Interview-ready answer:** The client sends `POST /orders` with an idempotency key. The service validates the request, reserves stock with an atomic conditional update, creates the order in `PENDING_PAYMENT`, and commits — all in one short local transaction with no external calls. Payment authorisation happens outside the transaction; on success a second short transaction marks the order `PAID` and writes an outbox event. Downstream effects — confirmation email, invoicing, analytics, fulfilment — consume that event asynchronously and idempotently. Failure paths are explicit: declined payment releases the reservation, an ambiguous payment timeout leaves the order in a pending state that a reconciliation job resolves against the provider. The API returns 201 with the order and its current status.

**In-depth explanation:** The critical decisions are where the transaction boundaries sit and where idempotency is enforced. Stock reservation must be atomic (`UPDATE ... WHERE available >= :qty`) or you oversell under concurrency. The payment call must not sit inside a database transaction. The outbox makes "order is paid" and "event published" atomic without distributed transactions. Reservations need a timeout so abandoned orders release stock, which is usually a scheduled sweep. For the user experience, decide whether to respond after authorisation (slower, definitive) or to accept and return 202 with a status endpoint (faster, requires client polling or push). Every consumer of the event must be idempotent because delivery is at-least-once.

**Practical backend example:** The skeleton of the flow:

```java
public OrderResponse place(PlaceOrderCommand cmd, String idempotencyKey) {
    Optional<OrderResponse> replay = idempotency.find(idempotencyKey);
    if (replay.isPresent()) return replay.get();                       // retry-safe

    Order order = tx.execute(s -> {                                    // transaction 1: short, local
        inventory.reserveOrThrow(cmd.lines());                         // atomic conditional update
        Order created = orderRepository.save(Order.pending(cmd));
        idempotency.record(idempotencyKey, created.id());
        return created;
    });

    AuthorizationResult auth = paymentClient.authorize(                 // outside any transaction
            cmd.payment(), order.id(), idempotencyKey);                 // key forwarded downstream

    return tx.execute(s -> {                                            // transaction 2: short
        if (auth.approved()) {
            order.markPaid(auth.reference());
            outbox.append(new OrderPaid(order.id()));                   // atomic with the state change
        } else {
            order.markPaymentFailed(auth.reason());
            inventory.release(cmd.lines());
        }
        return OrderResponse.from(orderRepository.save(order));
    });
}
```

**Common follow-ups:**
- Where is idempotency enforced? At the API boundary with a stored key, and again downstream by passing the key to the payment provider.
- What if the payment call times out? The outcome is unknown: leave the order pending and reconcile against the provider rather than retrying blindly.
- How do reservations get released? A scheduled sweep expires reservations older than the hold window.

**Mistakes to avoid:** Holding a transaction across the payment call; checking stock with a read before writing; publishing events before commit; assuming a timeout means failure.

**Production perspective:** Instrument each state transition and alert on orders stuck in intermediate states — that metric catches nearly every failure mode in this workflow, including ones you did not anticipate.

**Related concepts covered:** Transaction boundaries, outbox pattern, idempotency keys, stock reservation, reconciliation, state machine monitoring.

## Q151. How do API gateways differ from service-to-service concerns?

**Priority:** Important  
**Why interviewers ask it:** It probes whether you can place cross-cutting responsibilities at the right layer.

**Interview-ready answer:** A gateway sits at the edge and handles concerns common to all external traffic: TLS termination, routing, authentication of end users, coarse rate limiting, request size limits, CORS and sometimes response caching. Service-to-service concerns are different: mutual authentication between services, per-dependency timeouts, retries, circuit breakers and fine-grained authorisation based on the resource being accessed. The mistake I avoid is putting business logic in the gateway, because it becomes a shared bottleneck that every team must change and nobody owns. Each service still validates its own input and enforces its own authorisation — the gateway is a filter, not a guarantee.

**In-depth explanation:** Defence in depth is the underlying principle: a service must not assume it is only reachable through the gateway, because internal callers, misconfigurations and lateral movement all bypass it. Service meshes move some of this into a sidecar — mTLS, retries, timeouts, traffic shifting — which centralises policy without embedding it in application code, at the cost of operational complexity. Backend-for-frontend is a useful pattern when different clients need different aggregations: a thin per-client layer keeps the core services clean. Gateways also become a single point of failure and a latency contributor, so they need the same capacity planning and observability as any service.

**Practical backend example:** Responsibility split:

```text
Gateway / edge
  - TLS termination, HTTP/2
  - JWT validation (signature, issuer, audience, expiry)
  - global rate limits per API key, body size limits
  - CORS policy, routing to services, request ID injection

Service
  - re-validates the token's claims it depends on
  - authorises the specific resource (does this user own this order?)
  - validates payloads, enforces business rules
  - per-dependency timeouts, retries, bulkheads for its own outbound calls
```

**Common follow-ups:**
- Should business logic live at the gateway? No; it becomes a shared bottleneck and duplicates domain rules outside their owning service.
- Does the gateway remove the need for service-side authorisation? No; resource-level checks must happen where the data lives.
- What does a service mesh add? Uniform mTLS, retries and traffic policy at the infrastructure layer, with extra operational complexity.

**Mistakes to avoid:** Trusting gateway-injected headers without validation; implementing per-tenant business rules in gateway configuration; forgetting the gateway's own capacity limits; skipping internal authentication because "it is internal".

**Production perspective:** Gateways concentrate risk: a bad route or rate-limit change can affect every API at once. Treat gateway configuration as code with reviews, staged rollout and quick rollback.

**Related concepts covered:** Defence in depth, service mesh, backend-for-frontend, edge rate limiting, configuration as code.

## Q152. How do you prevent duplicate requests from creating duplicate resources?

**Priority:** Must Know  
**Why interviewers ask it:** Duplicate creation is one of the most common production data problems, and the fix must be at the right layer.

**Interview-ready answer:** The durable answer is a uniqueness guarantee in the database: a unique constraint on whatever identifies the logical operation — an idempotency key, a client-supplied reference, or a natural business key such as (customer, order number). Then either attempt the insert and translate a conflict into the original result, or use an upsert (`INSERT ... ON CONFLICT`). Application-level checks like "does it already exist?" before inserting are races under concurrency and will eventually produce duplicates. A client-generated ID helps, because it lets the client retry with the same identifier, but only if the server enforces uniqueness on it.

**In-depth explanation:** There are two distinct duplicate sources: the same request retried (network timeout, client bug, gateway retry) and two genuinely concurrent requests representing the same intent. A unique constraint handles both. Choosing the key matters: an idempotency key is per-attempt-group and expires; a natural business key is permanent and also prevents duplicates created months apart, which may or may not be desirable. For resources created from events, the event ID is the natural deduplication key. Where a resource legitimately allows duplicates (two identical orders placed deliberately), the client must supply distinct keys, which is why the key should express client intent rather than payload content alone.

**Practical backend example:** Client-supplied reference with a database guarantee:

```sql
ALTER TABLE "order" ADD CONSTRAINT uk_order_client_reference
    UNIQUE (customer_id, client_reference);
```

```java
@PostMapping("/api/orders")
public ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrder body) {
    try {
        Order order = orderService.create(body);                     // insert relies on the constraint
        return ResponseEntity.created(location(order)).body(OrderResponse.from(order));
    } catch (DataIntegrityViolationException e) {
        Order existing = orderRepository
                .findByCustomerIdAndClientReference(body.customerId(), body.clientReference())
                .orElseThrow(() -> e);
        return ResponseEntity.ok(OrderResponse.from(existing));      // return the original, not an error
    }
}
```

**Common follow-ups:**
- Is a client-generated ID enough? Only if the server enforces uniqueness on it; otherwise two inserts still succeed.
- What if the duplicate arrives concurrently? The unique index serialises them; one insert fails and reads the winner's row.
- Should a duplicate be an error? Usually not for a retry — return the original resource; for a genuinely different payload with the same key, return 409.

**Mistakes to avoid:** `existsBy` before `save`; relying on the application to be the only writer; unique constraints only in code comments; returning 500 on constraint violations.

**Production perspective:** Cleaning up duplicates after the fact is expensive and often user-visible (duplicate charges, duplicate shipments). A unique index costs almost nothing and prevents the entire class of problem.

**Related concepts covered:** Unique constraints, upserts, idempotency keys, natural keys, conflict translation, concurrent inserts.

## Q153. What should happen when a downstream service times out after committing?

**Priority:** Must Know  
**Why interviewers ask it:** Timeout ambiguity is the defining problem of distributed systems, and the answer reveals real experience.

**Interview-ready answer:** A timeout tells you nothing about the remote outcome — the request may have succeeded, failed, or still be in progress. So the operation must be treated as unknown, not failed. If the call is idempotent or carries an idempotency key, a bounded retry is safe and will either reapply harmlessly or return the original result. If it is not idempotent, retrying risks a duplicate side effect; instead I record the attempt in a pending state and resolve it by querying the provider's status endpoint or reconciling later. What I never do is silently assume failure and roll back local state, because that creates a mismatch the customer eventually discovers.

**In-depth explanation:** The design implication is that every non-idempotent remote call should have a way to ask "did this happen?" — a status endpoint keyed by your reference, or a reconciliation feed. Store your own reference before the call, so the record exists even if the response never arrives. A pending state plus a scheduled resolver is the standard pattern: check the provider, then either complete or fail the local record. Time limits matter: define how long a record may stay pending before it escalates to a human. The same logic applies to your own API: give clients an idempotency mechanism and a status endpoint so they can resolve their own ambiguous timeouts.

**Practical backend example:** Pending state plus a resolver:

```java
@Transactional
public void startCapture(UUID paymentId) {
    payments.markPending(paymentId);          // recorded BEFORE the call, so it always exists
}

public void capture(UUID paymentId) {
    startCapture(paymentId);
    try {
        CaptureResult result = gateway.capture(paymentId, idempotencyKeyFor(paymentId));
        payments.complete(paymentId, result);
    } catch (TimeoutException e) {
        log.warn("capture outcome unknown payment={}", paymentId, e);   // do NOT assume failure
    }
}

@Scheduled(fixedDelay = 60_000)
public void resolvePending() {
    for (Payment p : payments.findPendingOlderThan(Duration.ofMinutes(2))) {
        gateway.lookup(p.reference()).ifPresent(status -> payments.settle(p.id(), status));
    }
}
```

**Common follow-ups:**
- Should you immediately retry? Only if the operation is idempotent or key-protected; otherwise query the status first.
- How do you know what happened? A provider status endpoint keyed by your reference, or a reconciliation file or feed.
- How long can a record stay pending? Define a limit, alert when exceeded, and have a manual resolution path.

**Mistakes to avoid:** Treating a timeout as a failure; rolling back local state without confirmation; retrying a non-idempotent capture; leaving pending records unmonitored.

**Production perspective:** Pending-state counts and ages are among the most valuable business-level metrics you can expose. A rising count of unresolved operations is an early indicator of an integration problem long before customers call.

**Related concepts covered:** Timeout ambiguity, idempotency keys, status lookup endpoints, reconciliation jobs, pending-state monitoring.

## Q154. How do you make a webhook consumer safe?

**Priority:** Important  
**Why interviewers ask it:** Webhooks are a common integration point with security, ordering and reliability pitfalls all at once.

**Interview-ready answer:** Four things. Verify authenticity: check the HMAC signature over the raw body with the shared secret, using a constant-time comparison, and reject stale timestamps to prevent replay. Deduplicate: store the provider's event ID with a unique constraint, because webhooks are delivered at least once. Respond quickly: acknowledge with 2xx and process asynchronously, since most providers retry on slow responses and may disable endpoints that time out. Handle ordering: events can arrive out of order, so apply them with version or timestamp guards rather than assuming sequence. I also make the endpoint's failure behaviour deliberate — return 5xx only when I genuinely want a retry.

**In-depth explanation:** Signature verification must use the exact raw bytes received; parsing and re-serialising JSON changes the payload and breaks the HMAC, which is why you need access to the raw body. Constant-time comparison avoids timing side channels. Timestamp tolerance (commonly five minutes) limits replay windows. For deduplication, a unique index on the event ID is both the check and the guarantee. Asynchronous processing means writing the event to a table or queue and returning 200 immediately; the worker then handles retries, dead-lettering and alerting. Because retries are inevitable, the handler must be idempotent at the effect level, not just the ingestion level. Finally, webhook endpoints are public: apply rate limits and body size limits, and never trust fields in the payload over your own records.

**Practical backend example:** Verify, deduplicate, enqueue:

```java
@PostMapping(value = "/webhooks/payments", consumes = MediaType.APPLICATION_JSON_VALUE)
public ResponseEntity<Void> receive(@RequestHeader("X-Signature") String signature,
                                    @RequestHeader("X-Timestamp") long timestamp,
                                    @RequestBody byte[] rawBody) {          // raw bytes, not a DTO
    if (Math.abs(Instant.now().getEpochSecond() - timestamp) > 300) {
        return ResponseEntity.badRequest().build();                          // replay window
    }
    byte[] expected = hmacSha256(secret, (timestamp + ".").getBytes(UTF_8), rawBody);
    if (!MessageDigest.isEqual(expected, Base64.getDecoder().decode(signature))) {
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();       // constant-time compare
    }
    WebhookEvent event = json.read(rawBody, WebhookEvent.class);
    inbox.insertIgnoreDuplicate(event.id(), rawBody);                        // unique index on event id
    return ResponseEntity.ok().build();                                      // fast ack, async processing
}
```

**Common follow-ups:**
- What if events arrive out of order? Apply them with a version or timestamp guard so an older event cannot overwrite newer state.
- Why acknowledge before processing? Providers retry slow endpoints and may disable them; processing asynchronously keeps acknowledgement fast and reliable.
- How do you handle a poison event? Dead-letter it after bounded retries and alert, rather than blocking the whole inbox.

**Mistakes to avoid:** Verifying the signature against re-serialised JSON; using `equals` for signature comparison; doing heavy work synchronously in the handler; trusting payload amounts without verifying against your own records.

**Production perspective:** Monitor inbox lag, duplicate rate and signature failures. A spike in signature failures usually means a secret rotation went wrong, and it is much easier to see on a graph than in logs.

**Related concepts covered:** HMAC verification, replay protection, inbox pattern, at-least-once delivery, dead-letter handling, async acknowledgement.

## Q155. How would you rate-limit an API?

**Priority:** Important  
**Why interviewers ask it:** Rate limiting protects availability and shows understanding of distributed counters.

**Interview-ready answer:** I choose an algorithm first: fixed windows are simple but allow bursts at boundaries; sliding windows smooth that; token bucket is the usual choice because it allows a controlled burst while enforcing an average rate. Then the scope: per API key, per user, per IP, or per endpoint, often several tiers together. In a multi-instance deployment the counter must be shared, so Redis with atomic operations or a Lua script is the standard implementation, or the limit is enforced at the gateway. Responses must be informative: 429 with `Retry-After` and rate-limit headers so well-behaved clients can adapt. I also make sure the limiter fails open or closed deliberately if Redis is unavailable.

**In-depth explanation:** Atomicity is the correctness crux — check-then-increment across a network is a race, so use `INCR` with `EXPIRE` set atomically, or a Lua script implementing the token bucket in one round trip. Per-IP limits are coarse behind NAT and proxies, so authenticated identity is a better key where available; `X-Forwarded-For` must be trusted only from known proxies. Consider what happens to legitimate bursts: a hard limit can break batch clients that could be served fine, which is why token bucket with a burst capacity is popular. Distinguish rate limiting from quota (long-term usage) and from concurrency limiting (in-flight requests) — they solve different problems, and a concurrency limit is often the better protection for expensive endpoints.

**Practical backend example:** Redis token bucket with informative headers:

```java
// Lua keeps check-and-consume atomic in one round trip
private static final String TOKEN_BUCKET = """
    local tokens = tonumber(redis.call('HGET', KEYS[1], 'tokens') or ARGV[1])
    local last   = tonumber(redis.call('HGET', KEYS[1], 'ts') or ARGV[4])
    local refill = math.min(tonumber(ARGV[1]), tokens + (ARGV[4] - last) * ARGV[2])
    if refill < 1 then return {0, refill} end
    redis.call('HSET', KEYS[1], 'tokens', refill - 1, 'ts', ARGV[4])
    redis.call('EXPIRE', KEYS[1], ARGV[3])
    return {1, refill - 1}
    """;

if (!allowed) {
    return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
            .header("Retry-After", "1")
            .header("RateLimit-Limit", "100")
            .header("RateLimit-Remaining", "0")
            .build();
}
```

**Common follow-ups:**
- What response headers help clients? `Retry-After` plus limit/remaining/reset headers so clients can self-throttle.
- Why not count in application memory? Each replica would allow the full limit; the counter must be shared.
- What if Redis is down? Decide explicitly: fail open (accept traffic, risk overload) or fail closed (reject, risk an outage). Most APIs fail open with a local fallback limit.

**Mistakes to avoid:** Non-atomic check-then-increment; per-IP limits as the only tier; no `Retry-After`; limiting cheap and expensive endpoints identically; trusting `X-Forwarded-For` from anywhere.

**Production perspective:** Rate limits are a customer-facing contract: document them, expose usage headers, and alert when a major client starts hitting limits, because that usually signals a client bug or a legitimate need for a higher tier.

**Related concepts covered:** Token bucket, Redis atomic scripts, distributed counters, concurrency limiting versus rate limiting, fail-open decisions.

## Q156. How do content negotiation and media types affect an API?

**Priority:** Bonus  
**Why interviewers ask it:** It checks protocol precision that becomes important for file endpoints, versioning and integrations.

**Interview-ready answer:** The client states what it can accept with the `Accept` header, and describes what it is sending with `Content-Type`. The server picks a representation it can produce; if it cannot satisfy `Accept` it returns 406, and if it cannot parse the request body's media type it returns 415. In Spring, `produces` and `consumes` on a mapping participate in that negotiation. Beyond JSON, this matters for CSV or PDF exports, for versioned media types such as `application/vnd.example.order.v2+json`, and for `application/merge-patch+json` on PATCH endpoints. Charset should be UTF-8 everywhere, stated explicitly where the type allows it.

**In-depth explanation:** Negotiation also drives caching: a shared cache must vary on `Accept` (and often `Accept-Encoding`) or it will serve the wrong representation, which is what the `Vary` header is for. Media-type versioning keeps URIs stable and is elegant, but it is harder to test in a browser, harder to route at a gateway and harder to read in logs — a trade-off worth stating. For file downloads, `Content-Disposition` controls whether the browser displays or downloads the file and provides the filename; it must be sanitised because header injection through filenames is a real vulnerability. Compression is negotiated with `Accept-Encoding`, and enabling gzip on JSON responses is usually a large, cheap bandwidth win.

**Practical backend example:** Two representations of one resource:

```java
@GetMapping(value = "/api/reports/{id}", produces = MediaType.APPLICATION_JSON_VALUE)
public ReportDto json(@PathVariable UUID id) { return reportService.get(id); }

@GetMapping(value = "/api/reports/{id}", produces = "text/csv")     // same URI, different Accept
public ResponseEntity<StreamingResponseBody> csv(@PathVariable UUID id) {
    return ResponseEntity.ok()
            .contentType(MediaType.parseMediaType("text/csv; charset=UTF-8"))
            .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"report.csv\"")
            .header(HttpHeaders.VARY, HttpHeaders.ACCEPT)            // caches must distinguish
            .body(out -> reportService.streamCsv(id, out));          // streamed, not buffered
}
```

**Common follow-ups:**
- What does 415 mean? Unsupported Media Type — the server cannot process the request body's `Content-Type`.
- What does 406 mean? Not Acceptable — the server cannot produce any representation matching `Accept`.
- Why set `Vary`? So shared caches store and serve the correct representation per `Accept` value.

**Mistakes to avoid:** Ignoring `Accept` and always returning JSON with a 200; unsanitised filenames in `Content-Disposition`; buffering large exports in memory; omitting charset on text types.

**Production perspective:** Export endpoints are a common source of memory incidents. Stream them, cap the result size or make them asynchronous with a download link, and keep them off the same connection pool as interactive traffic.

**Related concepts covered:** Accept and Content-Type, 406 versus 415, Vary and caching, media-type versioning, streaming responses, content disposition.

## Q157. What is the difference between liveness and readiness?

**Priority:** Important  
**Why interviewers ask it:** Confusing the two causes restart loops and outages during dependency blips.

**Interview-ready answer:** Liveness answers "is this process broken beyond recovery?" — if it fails, the orchestrator restarts the container. Readiness answers "should this instance receive traffic right now?" — if it fails, the instance is removed from the load balancer but keeps running. The critical rule is that a failing external dependency should usually not fail liveness, because restarting the pod will not fix the database and a restart loop makes things worse. It may legitimately fail readiness if the instance genuinely cannot serve requests. Spring Boot exposes both through `/actuator/health/liveness` and `/actuator/health/readiness`, and a startup probe covers slow initialisation.

**In-depth explanation:** Health indicators aggregate component checks; by default many are included in the overall health group, so it is important to configure which components belong to which probe. A readiness check that queries the database on every probe adds load and can amplify an incident — a cheap cached check is usually better. During shutdown, readiness should fail immediately so traffic drains before the server stops accepting connections. Startup probes exist because a slow-booting application would otherwise be killed by an aggressive liveness probe. Also consider partial readiness: if one of several features is degraded, it may be better to serve the rest than to remove the instance entirely.

**Practical backend example:** Probe groups configured deliberately:

```yaml
management:
  endpoint:
    health:
      probes:
        enabled: true
      group:
        liveness:
          include: livenessState          # process health only - no external dependencies
        readiness:
          include: readinessState,db      # may include critical dependencies
      show-details: never                 # do not leak internals publicly
```

```yaml
livenessProbe:   { httpGet: { path: /actuator/health/liveness,  port: 8080 }, periodSeconds: 10 }
readinessProbe:  { httpGet: { path: /actuator/health/readiness, port: 8080 }, periodSeconds: 5 }
startupProbe:    { httpGet: { path: /actuator/health/liveness,  port: 8080 }, failureThreshold: 30 }
```

**Common follow-ups:**
- Should a failed database fail liveness? Generally no; restarting will not fix the database, and a restart loop removes capacity. Readiness may fail instead.
- What is a startup probe for? To give a slow-starting application time to boot without an aggressive liveness probe killing it.
- Why fail readiness during shutdown? So the load balancer stops sending traffic before the server stops accepting connections.

**Mistakes to avoid:** Pointing both probes at the same deep health check; probing expensive dependencies every second; exposing detailed health information publicly; ignoring the startup case.

**Production perspective:** A dependency outage combined with a dependency-checking liveness probe turns a partial failure into a full one as every pod restarts simultaneously. Keep liveness cheap and local.

**Related concepts covered:** Kubernetes probes, health groups, graceful shutdown, cascading failure, actuator configuration.

## Q158. How do you handle file upload and download safely?

**Priority:** Important  
**Why interviewers ask it:** File endpoints combine memory, security and storage concerns that trip up many services.

**Interview-ready answer:** For uploads I enforce a maximum size at both the framework and the proxy, stream to storage rather than buffering in memory, validate the content type by inspecting the bytes rather than trusting the client, and generate my own storage key instead of using the client's filename. For downloads I stream from storage with the correct `Content-Type` and a sanitised `Content-Disposition`, and I authorise every request rather than relying on an unguessable URL. Large files are better handled with pre-signed URLs to object storage so the bytes never pass through the application at all. Uploaded content should be stored outside the web root and scanned when the risk profile requires it.

**In-depth explanation:** Path traversal is the classic vulnerability: a filename like `../../etc/passwd` must never influence a storage path, which is why a generated UUID key with the original name kept only as metadata is the safe design. Content-type sniffing matters because a file named `.jpg` can contain anything; libraries that inspect magic bytes are more trustworthy than the declared type. Serving user-uploaded content from your primary domain risks stored XSS, so a separate domain or `Content-Disposition: attachment` plus `X-Content-Type-Options: nosniff` is recommended. On the resource side, multipart parsing can buffer to disk or memory depending on configuration, so set thresholds explicitly. Pre-signed URLs shift bandwidth and memory to the object store and are the standard approach above a few megabytes.

**Practical backend example:** Bounded, streamed upload with a generated key:

```yaml
spring:
  servlet:
    multipart:
      max-file-size: 10MB
      max-request-size: 12MB
      file-size-threshold: 1MB      # buffer to disk beyond this
```

```java
@PostMapping(value = "/api/documents", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
public DocumentResponse upload(@RequestPart("file") MultipartFile file) throws IOException {
    if (file.getSize() > MAX_BYTES) throw new PayloadTooLargeException();
    String detected = tika.detect(file.getInputStream());            // inspect bytes, not the name
    if (!ALLOWED_TYPES.contains(detected)) throw new UnsupportedFileTypeException(detected);

    String key = "documents/" + UUID.randomUUID();                   // never use the client filename
    try (InputStream in = file.getInputStream()) {
        objectStorage.put(key, in, file.getSize(), detected);        // streamed, not loaded into heap
    }
    return documentService.record(key, sanitize(file.getOriginalFilename()), detected);
}
```

**Common follow-ups:**
- How do you avoid path traversal? Never build paths from client input; generate the storage key yourself.
- Can `Content-Type` be trusted? No; detect from the file's bytes and validate against an allowlist.
- How do you serve very large files? Pre-signed URLs to object storage, so the application does not proxy the bytes.

**Mistakes to avoid:** Reading the whole file into a byte array; trusting the declared content type or filename; serving uploads from the main domain without `nosniff` and attachment disposition; no size limits at the proxy.

**Production perspective:** File endpoints are a common cause of heap exhaustion and of security findings. Limit sizes, stream everything, and keep upload traffic isolated so a large transfer cannot starve interactive requests.

**Related concepts covered:** Multipart configuration, streaming I/O, content sniffing, path traversal, pre-signed URLs, stored XSS.

## Q159. How would you design a small notification service?

**Priority:** Important  
**Why interviewers ask it:** It is a scoped design exercise touching queues, retries, templating, idempotency and provider failure.

**Interview-ready answer:** The service consumes notification requests from a queue, renders a template per channel, sends through a provider, and records the outcome. Key design points: deduplicate with a notification key so the same event cannot send twice; retry with backoff for transient provider failures and dead-letter after a bounded number of attempts; respect user preferences and quiet hours; and store a delivery record with status so support can answer "was this sent?". Templates live in a versioned store with locale support. I also isolate providers behind an interface so a failing email provider can be swapped or failed over, and rate-limit per provider to respect their quotas.

**In-depth explanation:** Idempotency is the crux: at-least-once delivery from the queue means the consumer will occasionally see the same message twice, so the send must be keyed — typically `(eventId, channel, recipient)` with a unique constraint checked before sending, and the provider's own idempotency key passed through where supported. Ordering is usually not required for notifications, which simplifies scaling. Provider failures need classification: 4xx from the provider (bad address) is permanent and should not be retried, while 5xx and timeouts are transient. Bounce and complaint webhooks should feed back into suppression lists, otherwise reputation suffers. Finally, notifications carry personal data, so payload retention and logging need care.

**Practical backend example:** Consumer with dedupe, classification and dead-lettering:

```java
@KafkaListener(topics = "notifications", concurrency = "4")
public void handle(NotificationRequested msg, Acknowledgment ack) {
    String key = msg.eventId() + ":" + msg.channel() + ":" + msg.recipientHash();
    if (deliveryRepository.insertIfAbsent(key) == 0) { ack.acknowledge(); return; }  // duplicate

    RenderedMessage rendered = templateService.render(msg.templateId(), msg.locale(), msg.params());
    try {
        ProviderResult result = providers.forChannel(msg.channel()).send(rendered, key);
        deliveryRepository.markSent(key, result.providerMessageId());
    } catch (PermanentProviderException e) {          // invalid address: never retry
        deliveryRepository.markFailed(key, e.getMessage());
    } catch (TransientProviderException e) {          // retry with backoff, then dead-letter
        throw e;                                      // handled by the error handler / DLT
    }
    ack.acknowledge();
}
```

**Common follow-ups:**
- How do you avoid duplicate emails? A unique delivery key per event, channel and recipient, inserted before sending.
- What goes to a dead-letter topic? Messages that failed after the retry budget, with enough context to replay them later.
- How do you handle bounces? Consume provider webhooks and maintain a suppression list to stop sending to bad addresses.

**Mistakes to avoid:** Retrying permanent failures; no deduplication; templates hard-coded in application code; logging full message bodies containing personal data; unlimited retries against a failing provider.

**Production perspective:** Track sent, failed, retried and suppressed counts per channel and template. Notification bugs are highly visible to customers, and a delivery record per attempt is what makes support requests answerable.

**Related concepts covered:** At-least-once consumers, deduplication keys, error classification, dead-letter topics, suppression lists, template versioning.

## Q160. When should you split a service, and when keep a modular monolith?

**Priority:** Important  
**Why interviewers ask it:** It tests architectural judgement and resistance to following trends without reasons.

**Interview-ready answer:** I split when there is a concrete forcing reason: independent scaling needs, different availability or compliance requirements, genuinely separate ownership by different teams, or an isolation requirement for risky workloads. I keep a modular monolith when the main goal is clean boundaries, because modules give you those without network calls, distributed transactions, versioned contracts and multi-service debugging. A network boundary costs real money: partial failure, latency, serialisation, deployment coordination, distributed tracing and operational overhead. The usual sensible path is a well-modularised monolith with clear internal APIs, extracting a service when a specific pressure justifies it.

**In-depth explanation:** Splitting on the wrong seam creates a distributed monolith: services that must be deployed together and cannot function independently, which is worse than either alternative. Good seams follow business capabilities with their own data, minimal synchronous chatter, and stable interfaces. Data ownership is the hardest part: two services sharing a database are not independent, and splitting the schema requires deciding how they exchange data — events, APIs, or replicated read models. Conway's law is real: service boundaries that do not match team boundaries create constant coordination. Before extracting, it is worth enforcing module boundaries in the monolith (package rules, ArchUnit tests, Spring Modulith) to prove the seam works when calls are still in-process.

**Practical backend example:** Enforcing a boundary before extracting it:

```java
// ArchUnit test: the order module may not reach into billing internals
@ArchTest
static final ArchRule modules_respect_boundaries = classes()
        .that().resideInAPackage("..order..")
        .should().onlyDependOnClassesThat()
        .resideInAnyPackage("..order..", "..billing.api..", "java..", "org.springframework..");
```

```text
Signals that justify extraction
  - one component needs 10x the instances of the rest
  - a compliance requirement demands isolated data and access control
  - an independent team owns the capability and is blocked by shared deploys
  - a risky or resource-hungry workload threatens the rest of the application
```

**Common follow-ups:**
- What is the cost of a network boundary? Partial failure, latency, serialisation, contract versioning, distributed debugging, and more infrastructure.
- Can a monolith scale? Often yes — horizontally behind a load balancer; the usual bottleneck is the database, which splitting does not automatically fix.
- How do you prepare for a future split? Enforce module boundaries in code, keep data ownership clean, and avoid shared mutable tables across modules.

**Mistakes to avoid:** Splitting by technical layer; services sharing one database; extracting before the boundary is understood; treating microservices as a goal rather than a trade-off.

**Production perspective:** Each additional service adds deployment, monitoring, on-call and dependency management overhead. Count the total operational cost, not just the code, and make sure the organisation is ready to run what it builds.

**Related concepts covered:** Modular monolith, distributed monolith anti-pattern, data ownership, Conway's law, ArchUnit boundary tests, extraction criteria.
