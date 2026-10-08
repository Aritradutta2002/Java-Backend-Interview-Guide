# Chapter 6: HTTP, REST APIs, and Microservices

---

## Q136 — HTTP Methods and Semantics

**The one-line answer:** HTTP methods carry semantic contracts — safe (no side effects), idempotent (same result on repeated calls), or neither — and choosing the right method signals intent to clients, proxies, and caches.

### Method properties

| Method | Safe | Idempotent | Has request body | Typical use |
|---|---|---|---|---|
| GET | ✅ | ✅ | No (allowed but unusual) | Retrieve resource |
| HEAD | ✅ | ✅ | No | Retrieve headers only |
| OPTIONS | ✅ | ✅ | No | CORS preflight, capability discovery |
| PUT | ❌ | ✅ | Yes | Replace entire resource |
| DELETE | ❌ | ✅ | Optional | Remove resource |
| POST | ❌ | ❌ | Yes | Create, process, non-idempotent action |
| PATCH | ❌ | ❌ (can be) | Yes | Partial update |

**Safe** means the request must not change server state. Proxies and caches assume safe requests can be retried freely. **Idempotent** means repeating the request produces the same server state as executing it once. Clients can safely retry idempotent requests after a timeout without fear of duplicates.

### Critical distinctions

- `GET` must have no side effects — never use GET for state changes (no `GET /orders/123/cancel`).
- `DELETE` is idempotent — `DELETE /orders/123` twice should return 204 the first time, 404 the second — the state (order does not exist) is the same.
- `POST` is neither safe nor idempotent — `POST /orders` twice creates two orders.
- Idempotency keys make POST effectively idempotent for safe retries (see Q139).

### Headers that matter

```
Content-Type: application/json          # what you're sending
Accept: application/json                # what you expect back
Authorization: Bearer <token>           # credentials
If-None-Match: "abc123"                 # conditional GET (ETag)
X-Request-ID: uuid                      # correlation
X-Idempotency-Key: uuid                 # idempotent POST
```

---

## Q137 — HTTP Status Codes

**The one-line answer:** Status codes communicate the outcome of a request to clients and intermediaries — use them precisely so clients can react correctly without parsing the response body.

### Ranges

- **2xx — Success**
- **3xx — Redirection**
- **4xx — Client error** (the request is wrong — don't retry as-is)
- **5xx — Server error** (the server failed — may be safe to retry)

### Codes to know precisely

| Code | Name | When to use |
|---|---|---|
| 200 | OK | Successful GET, PUT, PATCH, or POST when result is returned |
| 201 | Created | Resource successfully created; include `Location` header |
| 202 | Accepted | Request accepted for async processing; not yet done |
| 204 | No Content | Successful DELETE or PUT with no response body |
| 301 | Moved Permanently | Resource has new permanent URL; cacheable |
| 302 | Found | Temporary redirect |
| 304 | Not Modified | ETag matched; client should use cached version |
| 400 | Bad Request | Malformed request, validation failure |
| 401 | Unauthorized | Not authenticated (misleadingly named) |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 405 | Method Not Allowed | Wrong HTTP method for this endpoint |
| 409 | Conflict | State conflict (duplicate, version mismatch, business rule) |
| 410 | Gone | Resource permanently deleted (stronger than 404) |
| 415 | Unsupported Media Type | Request Content-Type not accepted |
| 422 | Unprocessable Entity | Request is well-formed but semantically invalid |
| 429 | Too Many Requests | Rate limit exceeded; include `Retry-After` |
| 500 | Internal Server Error | Unexpected server failure |
| 502 | Bad Gateway | Upstream service returned invalid response |
| 503 | Service Unavailable | Service overloaded or down; include `Retry-After` |
| 504 | Gateway Timeout | Upstream service timed out |

### 200 vs 201 vs 202

- Return **201** (not 200) when a resource is created — include a `Location: /orders/123` header.
- Return **202** for long-running async operations — include a polling URL in the response body or `Location` header.
- Return **200** for synchronous successful operations that return a body.

---

## Q138 — REST Resource Design

**The one-line answer:** REST resources are nouns, not verbs — URLs identify things, and HTTP methods express actions on them; a well-designed URL structure is intuitive, stable, and maps cleanly to your domain.

### Resource naming rules

```
# GOOD — nouns, lowercase, hyphens for readability
GET    /orders                        # list orders
POST   /orders                        # create order
GET    /orders/{id}                   # get specific order
PUT    /orders/{id}                   # replace order
PATCH  /orders/{id}                   # partial update order
DELETE /orders/{id}                   # delete order

GET    /orders/{id}/items             # sub-resource collection
GET    /orders/{id}/items/{itemId}    # specific sub-resource

# BAD — verbs in URL
POST /createOrder
GET  /getOrderById?id=123
POST /orders/cancel
```

### Actions that don't fit CRUD

Some operations are actions, not resources. Two approaches:

```
# Option 1 — controller resource (sub-resource that is an action)
POST /orders/{id}/cancellations       # create a cancellation
POST /orders/{id}/refunds             # create a refund

# Option 2 — RPC-style (acceptable when truly an action with no resource)
POST /orders/{id}/cancel
POST /payments/{id}/capture
```

The controller pattern is more RESTful; the RPC style is pragmatic and widely used.

### Relationships between resources

```
GET /customers/{id}/orders            # orders belonging to a customer
POST /orders/{id}/items               # add item to order

# Avoid deep nesting beyond 2 levels — hard to read and use
GET /customers/{cid}/orders/{oid}/items/{iid}/reviews  # too deep
# Better: GET /order-items/{itemId}/reviews
```

---

## Q139 — Idempotency and Retry-Safe Endpoints

**The one-line answer:** Idempotency keys let non-idempotent POST operations be safely retried — the server stores the key-to-result mapping and returns the same result for duplicate requests, preventing double-execution of critical operations like payments.

### The problem

A client sends `POST /payments` and the network times out before receiving the response. The payment may or may not have been processed. Retrying without idempotency could charge the customer twice.

### Idempotency key pattern

```
Client generates a UUID:  X-Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000

First request:
  POST /payments
  X-Idempotency-Key: 550e8400...
  → Server processes payment, stores (key → result), returns 200

Retry (network failure, same key):
  POST /payments
  X-Idempotency-Key: 550e8400...
  → Server finds stored result, returns 200 with same response (no double charge)
```

### Server implementation

```java
@PostMapping("/payments")
public ResponseEntity<PaymentResult> capture(
        @RequestHeader("X-Idempotency-Key") String idempotencyKey,
        @RequestBody PaymentRequest request) {

    // Check if already processed
    return idempotencyStore.get(idempotencyKey)
        .map(ResponseEntity::ok)
        .orElseGet(() -> {
            PaymentResult result = paymentService.process(request);
            idempotencyStore.save(idempotencyKey, result, Duration.ofDays(1));
            return ResponseEntity.ok(result);
        });
}
```

Storage: Redis with TTL is ideal for idempotency keys. A unique index on the key in the DB also works.

### PUT and DELETE are already idempotent

`PUT /orders/123` with the same body always produces the same state. `DELETE /orders/123` always results in the order not existing (404 on second call is still idempotent — state is the same).

---

## Q140 — PUT vs PATCH vs POST

**The one-line answer:** POST creates a new resource; PUT replaces an entire resource; PATCH applies a partial update — choosing correctly reflects the semantics of the operation and sets correct client expectations for retry safety.

### PUT — full replacement

```
PUT /orders/123
Content-Type: application/json
{
  "customerId": "C1",
  "status": "CONFIRMED",
  "total": 99.99
}
```

The server replaces the entire resource. Fields not included are set to defaults or removed. **Idempotent** — sending the same PUT multiple times has the same result.

### PATCH — partial update

```
PATCH /orders/123
Content-Type: application/json-patch+json
[
  { "op": "replace", "path": "/status", "value": "CONFIRMED" }
]
```

Or merge patch (RFC 7396):
```
PATCH /orders/123
Content-Type: application/merge-patch+json
{ "status": "CONFIRMED" }
```

Only specified fields are changed. Other fields remain unchanged. PATCH is generally considered non-idempotent (though can be designed to be).

### POST — create or process

```
POST /orders           → creates a new order, returns 201 with Location
POST /orders/123/cancel → action (cancel is not a resource state in strict REST)
```

### Common confusion: PUT for upsert

```
PUT /orders/external-id-from-partner
```

PUT can create a resource if it doesn't exist (upsert). The client specifies the full resource URL. This is valid REST.

### Interview pitfalls

- Saying "PATCH is idempotent" — it can be, but isn't by definition (e.g., `PATCH /counter { "op": "increment" }` is not idempotent).
- Using PUT for partial updates — PUT semantics require a full representation.
- Using POST for idempotent operations without an idempotency key.

---

## Q141 — Content Negotiation and Media Types

**The one-line answer:** Content negotiation lets the client declare what format it can consume (`Accept`) and what format it's sending (`Content-Type`), and the server selects the best matching representation.

### Headers

```
# Client tells server what it accepts
Accept: application/json, application/xml;q=0.9, */*;q=0.8

# Client declares what it's sending
Content-Type: application/json

# Server declares what it's returning
Content-Type: application/json; charset=UTF-8
```

`q` values (quality factors) indicate preference: `q=1.0` is highest, `q=0.0` means unacceptable.

### Spring MVC content negotiation

```java
@GetMapping(value = "/orders/{id}", produces = {
    MediaType.APPLICATION_JSON_VALUE,
    MediaType.APPLICATION_XML_VALUE
})
public OrderResponse getOrder(@PathVariable Long id) { ... }
```

If the client sends `Accept: application/xml` and Jackson XML is on the classpath, Spring returns XML.

### Custom media types for versioning

```
Accept: application/vnd.example.orders.v2+json
```

This is the most RESTful versioning approach but the hardest to implement. See Q142 for versioning strategies.

### Common errors

- **406 Not Acceptable:** Server can't produce any format the client `Accept`s.
- **415 Unsupported Media Type:** Server can't consume the `Content-Type` the client sent.

---

## Q142 — API Versioning Strategies

**The one-line answer:** API versioning manages breaking changes — URI versioning is the simplest and most visible; header/media-type versioning is purist REST but harder to test; sunset headers signal deprecation.

### URI versioning

```
GET /v1/orders
GET /v2/orders
```

**Pros:** Simple, visible, easy to test in browser, cache-friendly.  
**Cons:** Couples the version to the URL semantics (URIs should identify resources, not contract versions).

### Header versioning

```
GET /orders
API-Version: 2
```

**Pros:** Keeps URLs clean, truly RESTful.  
**Cons:** Invisible in browser, harder to test without tooling.

### Media type versioning

```
Accept: application/vnd.example.orders.v2+json
```

**Pros:** Most RESTful, version is tied to representation format.  
**Cons:** Complex to implement and test; verbose for clients.

### Query parameter versioning

```
GET /orders?version=2
```

**Cons:** Query params are typically for filtering/sorting, not versioning. Breaks semantic clarity. Not recommended for REST APIs.

### Deprecation and sunset

```
HTTP/1.1 200 OK
Sunset: Sat, 01 Jan 2026 00:00:00 GMT
Deprecation: true
Link: <https://api.example.com/v2/orders>; rel="successor-version"
```

RFC 8594 defines `Sunset` header. Give consumers at least 6–12 months notice.

### Breaking vs non-breaking changes

**Non-breaking (backward-compatible):**
- Adding new optional fields to responses
- Adding new optional request parameters with defaults
- Adding new endpoints

**Breaking changes (require version bump):**
- Removing or renaming fields
- Changing field types
- Changing status codes or error formats
- Removing endpoints

---

## Q143 — Pagination, Filtering, and Sorting

**The one-line answer:** List endpoints need pagination (size/page or cursor), filtering (query parameters mapped to WHERE clauses), and sorting (field + direction) — all must be validated and sanitized to prevent injection and denial of service.

### Pagination

```
# Offset-based
GET /orders?page=0&size=20&sort=createdAt,desc

# Cursor-based
GET /orders?limit=20&after=eyJpZCI6MTIzfQ==   # base64 cursor
```

Response includes pagination metadata:
```json
{
  "content": [...],
  "page": { "number": 0, "size": 20, "totalElements": 1500, "totalPages": 75 },
  "links": {
    "next": "/orders?page=1&size=20",
    "prev": null
  }
}
```

### Filtering

```
GET /orders?status=PENDING&customerId=C123&createdAfter=2024-01-01&minTotal=100
```

Map to Spring Data Specifications or JPQL predicates. Validate each parameter:
- Enum values must be from allowed set.
- Dates must be parseable.
- Numeric ranges must have reasonable bounds.
- String fields must have max length.

### Sorting — injection prevention

```java
private static final Set<String> ALLOWED_SORT_FIELDS = Set.of("createdAt", "total", "status");

public Pageable buildPageable(int page, int size, String sortBy, String direction) {
    if (!ALLOWED_SORT_FIELDS.contains(sortBy)) {
        sortBy = "createdAt"; // default
    }
    Sort.Direction dir = "asc".equalsIgnoreCase(direction) ? Sort.Direction.ASC : Sort.Direction.DESC;
    return PageRequest.of(page, Math.min(size, 100), Sort.by(dir, sortBy));
}
```

**Never** pass a user-supplied sort column directly to SQL — it bypasses parameterization and enables SQL injection.

### Defaults and limits

Always set defaults and maximum page size:
```
size=20 (default), max=100
page=0 (default)
sort=createdAt,desc (default)
```

---

## Q144 — Error Response Design

**The one-line answer:** A consistent, machine-readable error format with a correlation ID lets clients handle errors programmatically and lets your team diagnose issues without calling the client — RFC 7807 ProblemDetail is the modern standard.

### ProblemDetail (RFC 7807)

```json
{
  "type": "https://api.example.com/errors/validation-failed",
  "title": "Validation Failed",
  "status": 400,
  "detail": "One or more fields failed validation",
  "instance": "/orders",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "errors": [
    { "field": "customerId", "message": "must not be blank" },
    { "field": "items[0].quantity", "message": "must be greater than 0" }
  ]
}
```

- `type` — URI to documentation about this error type (stable, bookmarkable).
- `title` — Human-readable summary (stable — don't change between calls).
- `detail` — Human-readable explanation of this specific occurrence.
- `instance` — URI of the request that caused the error.
- Additional fields are allowed as extensions.

### What NOT to include in error responses

- Stack traces (security risk — reveals internal structure).
- Internal exception messages for 5xx errors (may contain SQL, paths, configs).
- Sensitive data (user IDs from internal systems, account numbers).

```java
// 5xx — generic message, log details internally
ProblemDetail pd = ProblemDetail.forStatus(500);
pd.setTitle("Internal Server Error");
pd.setProperty("correlationId", correlationId);
// detail is intentionally vague for security
log.error("[{}] Unexpected error", correlationId, ex); // full detail in logs
```

### Correlation IDs

Every request should get a correlation ID (from `X-Request-ID` header or generated). Include it in:
- The error response body.
- The `X-Request-ID` response header.
- Every log line (via MDC).
- Any upstream requests made while handling this request.

---

## Q145 — HTTP Caching

**The one-line answer:** HTTP caching uses `ETag` (content hash) and `Cache-Control` headers to let clients and proxies avoid redundant requests — conditional requests with `If-None-Match` return 304 Not Modified when content hasn't changed.

### Cache-Control directives

```
Cache-Control: no-store           # never cache — sensitive data
Cache-Control: no-cache           # cache but must revalidate with server before use
Cache-Control: private, max-age=300  # browser can cache, proxies cannot; 5min TTL
Cache-Control: public, max-age=3600  # anyone can cache; 1hr TTL
Cache-Control: must-revalidate    # must revalidate after expiry
```

### ETag — content-based cache validation

```java
@GetMapping("/orders/{id}")
public ResponseEntity<OrderResponse> getOrder(@PathVariable Long id,
                                              @RequestHeader(value = "If-None-Match", required = false) String ifNoneMatch) {
    Order order = service.findById(id);
    String etag = "\"" + order.getVersion() + "\""; // or hash of content

    if (etag.equals(ifNoneMatch)) {
        return ResponseEntity.status(HttpStatus.NOT_MODIFIED).build();
    }

    return ResponseEntity.ok()
        .eTag(etag)
        .cacheControl(CacheControl.maxAge(5, TimeUnit.MINUTES).cachePrivate())
        .body(mapToResponse(order));
}
```

Flow:
1. First request: server returns `ETag: "v42"`.
2. Client caches response with ETag.
3. Next request: client sends `If-None-Match: "v42"`.
4. If unchanged: server returns `304 Not Modified` (no body) — saves bandwidth.
5. If changed: server returns `200 OK` with new content and new ETag.

### Last-Modified alternative

```
Last-Modified: Tue, 15 Jan 2024 09:00:00 GMT
# Client sends: If-Modified-Since: Tue, 15 Jan 2024 09:00:00 GMT
```

ETag is preferred over Last-Modified when sub-second change detection matters.

---

## Q146 — CORS

**The one-line answer:** CORS (Cross-Origin Resource Sharing) is a browser security mechanism that blocks cross-origin fetch requests by default; the server must explicitly allow origins via response headers, and preflight OPTIONS requests must be handled before the actual request.

### What CORS controls

The browser sends the `Origin` header with cross-origin requests. The server's response headers determine if the browser allows the JavaScript to read the response.

```
Client (https://app.example.com) → Server (https://api.example.com)
```

### Simple requests (no preflight)

GET/POST/HEAD with standard headers — browser sends `Origin`, checks `Access-Control-Allow-Origin` in response.

### Preflighted requests (OPTIONS first)

PUT, DELETE, PATCH, or requests with custom headers trigger a preflight:

```
OPTIONS /orders/123
Origin: https://app.example.com
Access-Control-Request-Method: DELETE
Access-Control-Request-Headers: Authorization, X-Request-ID

HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH
Access-Control-Allow-Headers: Authorization, Content-Type, X-Request-ID
Access-Control-Max-Age: 3600    ← cache preflight result for 1 hour
```

### Spring CORS configuration

```java
// Method-level
@CrossOrigin(origins = "https://app.example.com", maxAge = 3600)
@GetMapping("/orders")
public List<OrderResponse> list() { ... }

// Global configuration
@Configuration
public class CorsConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("https://app.example.com", "https://admin.example.com")
            .allowedMethods("GET", "POST", "PUT", "DELETE", "PATCH")
            .allowedHeaders("*")
            .allowCredentials(true)
            .maxAge(3600);
    }
}
```

**Never use `allowedOrigins("*")` with `allowCredentials(true)` — it's a security violation.**

---

## Q147 — Cookies, Sessions, and SameSite

**The one-line answer:** Cookies store state on the client; session cookies authenticate users; `HttpOnly` prevents JavaScript access; `Secure` requires HTTPS; `SameSite=Strict/Lax` prevents CSRF by controlling when cookies are sent cross-site.

### Cookie security attributes

```
Set-Cookie: sessionId=abc123; 
            HttpOnly;           # not accessible via document.cookie — prevents XSS token theft
            Secure;             # only sent over HTTPS
            SameSite=Lax;       # sent on top-level navigation, not on cross-site fetch
            Path=/;
            Max-Age=3600;       # expires in 1 hour
```

### SameSite values

| Value | Cross-site top-level nav | Cross-site sub-requests |
|---|---|---|
| `Strict` | ❌ | ❌ — most secure, may break OAuth redirects |
| `Lax` | ✅ (GET only) | ❌ — good default |
| `None` | ✅ | ✅ — must combine with `Secure`; used for embedded widgets |

### Session vs JWT (see Q162 for full comparison)

For server-side sessions, the server stores session data and the cookie contains only a session ID. For JWT in cookies: the JWT is stored in an `HttpOnly` cookie (safer than `localStorage`), making it immune to XSS but still requiring CSRF protection.

### CSRF in context of SameSite

`SameSite=Lax` or `Strict` on session cookies effectively prevents CSRF attacks — the browser won't send the cookie on cross-origin form submissions. Explicit CSRF tokens are still recommended for `SameSite=None` APIs.

---

## Q148 — OpenAPI and Documentation

**The one-line answer:** OpenAPI (Swagger) documents your API as a machine-readable contract — SpringDoc generates it automatically from your controllers; good documentation includes examples, error schemas, and authentication requirements.

### SpringDoc setup

```xml
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.x.x</version>
</dependency>
```

```properties
springdoc.api-docs.path=/api-docs
springdoc.swagger-ui.path=/swagger-ui.html
springdoc.swagger-ui.enabled=false  # disable in production
```

### Annotating your API

```java
@Operation(summary = "Create an order", description = "Creates a new order for the authenticated customer")
@ApiResponses({
    @ApiResponse(responseCode = "201", description = "Order created",
        content = @Content(schema = @Schema(implementation = OrderResponse.class))),
    @ApiResponse(responseCode = "400", description = "Validation failed",
        content = @Content(schema = @Schema(implementation = ProblemDetail.class))),
    @ApiResponse(responseCode = "409", description = "Duplicate order")
})
@PostMapping("/orders")
public ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest request) { ... }

@Schema(description = "Request to create a new order")
public record CreateOrderRequest(
    @Schema(description = "Customer ID", example = "C123", requiredMode = REQUIRED)
    @NotBlank String customerId,

    @Schema(description = "Ordered items", minItems = 1)
    @NotEmpty List<@Valid OrderItemRequest> items
) {}
```

### Contract-first vs code-first

**Code-first** (generate spec from code): faster to start, may produce inconsistent naming. **Contract-first** (write spec, generate stubs): stronger contract discipline, enables parallel client/server development.

---

## Q149 — Async APIs: 202, Webhooks, and Polling

**The one-line answer:** Long-running operations should return 202 Accepted immediately with a status URL; the client polls for completion or receives a webhook callback — this prevents client timeouts and enables horizontal scaling.

### 202 Accepted pattern

```
POST /reports/generate
Body: { "type": "monthly", "month": "2024-01" }

→ 202 Accepted
Location: /reports/jobs/job-456
Retry-After: 30

GET /reports/jobs/job-456
→ 200 OK
{
  "jobId": "job-456",
  "status": "PROCESSING",   // or COMPLETED, FAILED
  "progress": 45,
  "estimatedCompletionAt": "2024-01-15T10:05:00Z"
}

GET /reports/jobs/job-456   (after completion)
→ 200 OK
{
  "status": "COMPLETED",
  "result": { "downloadUrl": "/reports/files/report-jan-2024.pdf" }
}
```

### Webhook pattern

Client registers a callback URL:
```
POST /webhooks
{ "url": "https://client.example.com/hooks/orders", "events": ["order.completed", "order.failed"] }
```

Server sends events:
```
POST https://client.example.com/hooks/orders
X-Signature: sha256=abc123
{
  "event": "order.completed",
  "orderId": "ORD-123",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

**Webhook reliability:**
- Retry with exponential backoff on delivery failure.
- Deliver to a dead-letter URL after N retries.
- Include a signature (`HMAC-SHA256` of payload + secret) for authenticity.
- Ensure idempotency — client may receive duplicates on retry.

---

## Q150 — Timeouts, Retries, Backoff, and Jitter

**The one-line answer:** Every outbound HTTP call must have a timeout; failed calls should retry with exponential backoff; jitter randomizes retry timing to prevent all clients retrying simultaneously and overwhelming the upstream.

### Timeout types

```java
// RestClient / RestTemplate configuration
RestClient client = RestClient.builder()
    .requestFactory(new HttpComponentsClientHttpRequestFactory(
        HttpClientBuilder.create()
            .setConnectionRequestTimeout(Timeout.ofMilliseconds(500))  // time to get conn from pool
            .setConnectTimeout(Timeout.ofMilliseconds(1000))            // TCP connect
            .setResponseTimeout(Timeout.ofMilliseconds(5000))           // time to read full response
            .build()
    ))
    .build();
```

Always set all three: connection request timeout, connect timeout, and read timeout. Missing any one can cause a thread to block indefinitely.

### Retry with exponential backoff

```
Attempt 1: wait 0s
Attempt 2: wait 1s
Attempt 3: wait 2s
Attempt 4: wait 4s
Attempt 5: fail / give up
```

### Jitter — the essential addition

Without jitter, all clients that started at the same time will retry at the same time (the "thundering herd"):

```java
// Full jitter: random within [0, base_delay * 2^attempt]
long baseDelay = 1000L;
int maxAttempts = 5;

for (int attempt = 1; attempt <= maxAttempts; attempt++) {
    try { return callService(); }
    catch (ServiceException e) {
        if (attempt == maxAttempts) throw e;
        long cap = baseDelay * (1L << attempt);
        long delay = ThreadLocalRandom.current().nextLong(0, Math.min(cap, 30_000L));
        Thread.sleep(delay);
    }
}
```

### Retry with Resilience4j

```java
@Retry(name = "paymentService", fallbackMethod = "paymentFallback")
public PaymentResult processPayment(PaymentRequest req) { ... }

public PaymentResult paymentFallback(PaymentRequest req, Exception ex) {
    return PaymentResult.queued(req.getOrderId()); // fallback behavior
}
```

```properties
resilience4j.retry.instances.paymentService.max-attempts=3
resilience4j.retry.instances.paymentService.wait-duration=1s
resilience4j.retry.instances.paymentService.exponential-backoff-multiplier=2
resilience4j.retry.instances.paymentService.retry-exceptions=java.io.IOException
```

**Only retry idempotent operations.** Retrying a non-idempotent call can cause duplicates.

---

## Q151 — Circuit Breaker and Bulkhead

**The one-line answer:** A circuit breaker stops calling a failing downstream service to fail fast and allow recovery; a bulkhead isolates failures in one service from consuming all resources and affecting other services.

### Circuit breaker states

```
CLOSED → (failure threshold exceeded) → OPEN → (wait duration) → HALF_OPEN → (probe succeeds) → CLOSED
                                                                             → (probe fails)    → OPEN
```

- **CLOSED:** Normal operation. Requests pass through. Failures are counted.
- **OPEN:** Short-circuit — requests fail immediately without calling the downstream. Saves resources and prevents cascade.
- **HALF_OPEN:** Allow a small number of test requests through. If they succeed, close; if they fail, reopen.

### Resilience4j circuit breaker

```java
@CircuitBreaker(name = "inventory", fallbackMethod = "defaultStock")
public StockLevel checkStock(String productId) {
    return inventoryService.getStock(productId);
}

public StockLevel defaultStock(String productId, Exception ex) {
    return StockLevel.unknown(); // graceful degradation
}
```

```properties
resilience4j.circuitbreaker.instances.inventory.failure-rate-threshold=50
resilience4j.circuitbreaker.instances.inventory.sliding-window-size=10
resilience4j.circuitbreaker.instances.inventory.wait-duration-in-open-state=10s
resilience4j.circuitbreaker.instances.inventory.permitted-number-of-calls-in-half-open-state=3
```

### Bulkhead

Limits concurrent calls to a downstream service, so one slow dependency can't consume all threads:

```properties
resilience4j.bulkhead.instances.inventory.max-concurrent-calls=20
resilience4j.bulkhead.instances.inventory.max-wait-duration=100ms
```

### Why both matter

Circuit breaker prevents calls to a down service. Bulkhead limits damage when a service is degraded-but-not-down (slow). Use both together: bulkhead to constrain resource use, circuit breaker to stop calling a failing service.

---

## Q152 — Partial Failures, Saga, and Outbox

**The one-line answer:** In microservices, a multi-step business process spanning services can partially fail — the Saga pattern orchestrates compensating transactions to roll back completed steps; the Outbox pattern ensures events are reliably published only after the local transaction commits.

### The distributed transaction problem

```
OrderService.placeOrder():
  1. Save order to DB ✅
  2. Call InventoryService.reserve() ✅
  3. Call PaymentService.charge() ❌ (network failure)
  → Order saved, inventory reserved, payment failed — inconsistent state
```

There's no distributed ACID without 2PC (slow, fragile).

### Saga pattern

**Choreography saga** (event-driven):
```
OrderService → publishes OrderCreated event
  InventoryService → listens, reserves stock → publishes StockReserved
  PaymentService → listens, charges card → publishes PaymentCharged → Order confirmed
  (if any step fails: publish failure event → upstream services run compensating transactions)
```

**Orchestration saga** (central coordinator):
```
SagaOrchestrator:
  1. → OrderService: create order → success
  2. → InventoryService: reserve → success
  3. → PaymentService: charge → failure
  4. → InventoryService: release reservation (compensate)
  5. → OrderService: cancel order (compensate)
```

### Outbox pattern — guaranteed event publishing

```
┌─────────────────────────────────────┐
│ @Transactional placeOrder()         │
│   INSERT INTO orders ...            │
│   INSERT INTO outbox_events ...     │  ← same DB transaction
│   COMMIT                            │
└─────────────────────────────────────┘
         ↓ (separate process)
┌─────────────────────────────────────┐
│ OutboxPoller: poll outbox_events    │
│   publish to Kafka/RabbitMQ         │
│   mark event as published           │
└─────────────────────────────────────┘
```

Guarantees: if the DB commit succeeds, the event will eventually be published. If the DB commit fails, no event is published. Eliminates the "event published but DB rolled back" race condition.

---

## Q153 — Microservices vs Monolith

**The one-line answer:** Start with a well-structured monolith; migrate to microservices only when team size, deployment independence, or scalability requirements genuinely justify the operational complexity they add.

### When monolith is right

- Team size < 10 engineers — microservices overhead exceeds benefit.
- Domain not well understood yet — boundaries will shift.
- Simple deployment requirements — single artifact is easier.
- Low traffic — vertical scaling is sufficient.

### When microservices make sense

- **Independent deployment:** Different teams deploy different services on different schedules.
- **Independent scaling:** Inventory service needs 20 instances; reporting service needs 2.
- **Technology heterogeneity:** Python ML service + Java order service + Go payment service.
- **Fault isolation:** Recommendation service failure shouldn't bring down checkout.
- **Large teams:** Conway's Law — system architecture mirrors organization structure.

### Microservice costs

- Network latency between services.
- Distributed tracing and debugging complexity.
- Data consistency (no cross-service ACID transactions).
- Service discovery, load balancing, health checks.
- Multiple CI/CD pipelines.
- Testing service interactions.

### Modular monolith — the middle ground

A monolith with strict module boundaries (enforced by package-private visibility or JPMS modules) that could be extracted to services later. Shares a deployment unit but maintains logical separation. Ideal for most teams.

---

## Q154 — REST vs gRPC vs Messaging

**The one-line answer:** REST is the universal default for synchronous APIs; gRPC is better for high-throughput internal service-to-service calls with strong contracts; messaging (Kafka, RabbitMQ) enables asynchronous, decoupled, event-driven communication.

### Comparison

| | REST/HTTP | gRPC | Messaging |
|---|---|---|---|
| Communication | Synchronous | Synchronous (+ streaming) | Asynchronous |
| Protocol | HTTP/1.1 or HTTP/2 | HTTP/2 | AMQP, Kafka protocol |
| Contract | OpenAPI (optional) | Protobuf (required) | Schema registry (optional) |
| Performance | Good | Excellent (binary, multiplexed) | Excellent (decoupled) |
| Browser support | ✅ | ❌ (needs grpc-web) | ❌ |
| Schema evolution | Loose | Strict (field numbers) | Depends (Avro, JSON) |
| Coupling | Loose | Tight (shared .proto) | Loosest |
| Error handling | HTTP status codes | gRPC status codes | DLQ, retries |

### When to choose gRPC

- Internal microservice-to-microservice calls with high throughput.
- Polyglot environments (generate clients in any language from .proto).
- Bidirectional streaming (real-time updates, server push).

### When to choose messaging

- Decoupled event publishing (order placed → inventory, email, analytics all listen).
- Work queues (background job processing).
- Fan-out (one event → multiple consumers).
- Temporal decoupling (consumer can be down and process events when it comes back).

---

## Q155 — API Gateway and BFF

**The one-line answer:** An API gateway is a single entry point that handles routing, auth, rate limiting, and cross-cutting concerns for all services; a Backend For Frontend (BFF) is a specialized gateway tailored to the needs of a specific client type.

### API Gateway responsibilities

```
Client → API Gateway → Service A
                    → Service B
                    → Service C
```

- **Routing:** Route requests to the correct downstream service.
- **Authentication:** Verify JWT/API key before forwarding.
- **Rate limiting:** Per-client or per-route throttling.
- **SSL termination:** HTTPS at the gateway; HTTP internally.
- **Request aggregation:** Combine multiple service calls into one client response.
- **Load balancing:** Distribute requests across service instances.
- **Circuit breaking:** Stop forwarding to unhealthy services.

Spring Cloud Gateway example:
```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: order-service
          uri: lb://order-service      # lb:// = load balanced via service registry
          predicates:
            - Path=/api/orders/**
          filters:
            - StripPrefix=1
            - name: CircuitBreaker
              args: { name: orderService, fallbackUri: forward:/fallback }
```

### BFF (Backend For Frontend)

Different clients have different needs:
- Mobile app: minimal payload, optimized for bandwidth.
- Web SPA: richer data, multiple aggregated calls.
- Partner API: different auth, rate limits, and data shape.

```
Mobile App → Mobile BFF  → Services
Web App    → Web BFF     → Services
Partners   → Partner API → Services (with stricter rate limits)
```

Each BFF is owned by the frontend team, giving them control over their API shape without coupling to the backend team's internal service design.

---

## Q156 — End-to-End Feature Design

**The one-line answer:** Feature design starts with requirements, produces an API contract, a database schema, validation rules, and error handling — walking through this completely in an interview demonstrates full-stack backend ownership.

### Example: "Add a coupon code to an order"

**Requirements:**
- Customer can apply one coupon per order.
- Coupon has a code, discount type (PERCENT or FIXED), value, and optional expiry.
- Coupon must be valid (not expired, not already used by this customer for single-use coupons).

**API:**
```
POST /orders/{orderId}/coupon
{ "couponCode": "SAVE10" }

→ 200 OK: { "discountAmount": 10.00, "newTotal": 90.00 }
→ 400: coupon code blank
→ 404: order not found / coupon not found
→ 409: coupon already applied / coupon expired / already used
```

**Database:**
```sql
coupons(id, code UNIQUE, discount_type, discount_value, expires_at, max_uses, current_uses)
order_coupons(order_id FK, coupon_id FK, applied_at, discount_amount)
```

**Service logic:**
```java
@Transactional
public void applyCoupon(Long orderId, String code) {
    Order order = orderRepo.findByIdForUpdate(orderId).orElseThrow();
    Coupon coupon = couponRepo.findByCode(code).orElseThrow();

    validate(order, coupon);               // check expiry, usage limits, already applied
    BigDecimal discount = coupon.calculate(order.getTotal());
    order.applyDiscount(discount);
    coupon.incrementUsage();               // optimistic lock on coupon
    orderCouponRepo.save(new OrderCoupon(order, coupon, discount));
}
```

**Edge cases:** race condition on coupon usage count → use optimistic locking or `UPDATE ... WHERE current_uses < max_uses`.

---

## Q157 — Small System Design: URL Shortener or Rate Limiter

**The one-line answer:** In a scoped system design exercise, demonstrate requirements clarification, data model, API design, scalability considerations, and trade-offs — not just an implementation.

### URL Shortener design

**Requirements:** Shorten URLs, redirect, ~100M URLs, 1B redirects/day.

**API:**
```
POST /shorten   { "url": "https://long.example.com/..." }
→ 201: { "shortCode": "abc123", "shortUrl": "https://short.io/abc123" }

GET /abc123 → 301 or 302 redirect to original URL
```

**Data model:**
```sql
urls(short_code VARCHAR(8) PK, original_url TEXT, created_at, expires_at, user_id)
```

**Short code generation:**
- Base62 encoding of auto-incremented ID (simple, no collisions).
- Or: random 7-8 chars with collision check and retry.

**Scalability:**
- Redis cache for hot short codes (most clicks are on recently created links).
- Read replicas for redirect lookups.
- CDN for redirect responses with `Cache-Control: max-age=3600`.
- 302 (temporary) allows changing the destination; 301 (permanent) is cached by browsers.

**Interview tip:** Ask clarifying questions first — analytics needed? Custom short codes? Expiry?

### Token Bucket Rate Limiter design

**Concept:** Each client has a bucket with `capacity` tokens. Tokens refill at `rate` per second. Each request consumes one token. Bucket empty → reject request.

**Redis implementation:**
```lua
-- Lua script for atomic check-and-decrement
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or capacity
local last_refill = tonumber(bucket[2]) or now

local elapsed = now - last_refill
local new_tokens = math.min(capacity, tokens + elapsed * refill_rate)

if new_tokens >= 1 then
    redis.call('HMSET', key, 'tokens', new_tokens - 1, 'last_refill', now)
    return 1  -- allowed
else
    return 0  -- rejected
end
```

---

## Q158 — Rate Limiting

**The one-line answer:** Rate limiting protects your API from abuse and overload — implement it at the gateway level with Redis-backed token bucket or sliding window counters, return 429 with `Retry-After`, and differentiate limits by client tier.

### Algorithms

**Token bucket:** Allows bursts up to bucket capacity. Good for APIs that allow bursting.

**Leaky bucket:** Smooth output rate regardless of input bursts. Good for downstream protection.

**Fixed window:** Count requests in fixed time windows (e.g., 100 req/min). Simple but has boundary burst problem (200 requests in 2 seconds straddling a minute boundary).

**Sliding window:** More accurate; uses a log of request timestamps or Redis sorted set:

```java
// Redis sliding window — count requests in last 60 seconds
public boolean isAllowed(String clientId) {
    long now = System.currentTimeMillis();
    long windowStart = now - 60_000;

    redisTemplate.opsForZSet().removeRangeByScore(clientId, 0, windowStart);
    Long count = redisTemplate.opsForZSet().zCard(clientId);

    if (count < RATE_LIMIT) {
        redisTemplate.opsForZSet().add(clientId, String.valueOf(now), now);
        redisTemplate.expire(clientId, Duration.ofMinutes(2));
        return true;
    }
    return false;
}
```

### Response headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 23
X-RateLimit-Reset: 1705312860   # Unix timestamp when limit resets
Retry-After: 37                 # seconds until next request allowed (on 429)
```

### Granularity

- Per IP — basic protection.
- Per API key / user — fair use per customer.
- Per endpoint — expensive operations get stricter limits.
- Per tier — paid customers get higher limits.

---

## Q159 — Webhooks and Callback Security

**The one-line answer:** Webhook consumers must verify request authenticity with HMAC signatures, implement idempotency for duplicate delivery, and return 2xx quickly to avoid retry storms.

### Signing webhook payloads

**Producer (you):**
```java
String payload = objectMapper.writeValueAsString(event);
String signature = "sha256=" + hmacSha256(payload, webhookSecret);
httpClient.post(endpoint)
    .header("X-Signature", signature)
    .body(payload)
    .send();
```

**Consumer (recipient):**
```java
@PostMapping("/webhook")
public ResponseEntity<Void> receiveWebhook(
        @RequestHeader("X-Signature") String signature,
        @RequestBody String rawBody) {

    String expected = "sha256=" + hmacSha256(rawBody, secret);
    if (!MessageDigest.isEqual(expected.getBytes(), signature.getBytes())) {
        return ResponseEntity.status(401).build(); // reject invalid signature
    }

    String eventId = extractEventId(rawBody);
    if (!idempotencyStore.setIfAbsent(eventId, Duration.ofDays(1))) {
        return ResponseEntity.ok().build(); // duplicate — acknowledge but ignore
    }

    eventProcessor.processAsync(rawBody); // process asynchronously, return fast
    return ResponseEntity.ok().build();   // must return 2xx quickly
}
```

### Delivery guarantees

- Retry with exponential backoff on non-2xx responses.
- Dead-letter after N failures — notify the consumer.
- Include event timestamps for replay detection.
- Provide a replay API so consumers can request missed events.

---

## Q160 — API Compatibility and Contract Testing

**The one-line answer:** Consumer-driven contract testing (Pact) verifies that a provider's API matches what consumers actually use — catching breaking changes before deployment, not in production.

### Breaking vs non-breaking changes (recap)

**Non-breaking:** adding optional response fields, adding new optional request fields with defaults, adding endpoints.

**Breaking:** removing fields, renaming fields, changing field types, changing required/optional semantics, removing endpoints, changing status codes.

### Semantic versioning for APIs

- `MAJOR` version bump for breaking changes.
- `MINOR` for backward-compatible additions.
- Maintain at least one major version backward.

### Consumer-driven contract testing with Pact

```
Consumer team writes: "I expect GET /orders/{id} to return { id, status, total }"
Provider team verifies: "My implementation satisfies the consumer's contract"
```

Pact generates a contract (JSON) from consumer tests and the provider runs a verification test against it. If the provider breaks the contract, the build fails before deployment.

```java
// Consumer test (Pact)
@Pact(provider = "order-service", consumer = "checkout-ui")
public RequestResponsePact getOrderPact(PactDslWithProvider builder) {
    return builder
        .given("order 123 exists")
        .uponReceiving("get order by id")
            .path("/orders/123").method("GET")
        .willRespondWith()
            .status(200)
            .body(new PactDslJsonBody()
                .numberType("id")
                .stringType("status")
                .decimalType("total"))
        .toPact();
}
```

### OpenAPI linting

Use tools like `openapi-diff` or `Optic` in CI to detect breaking changes between API versions:
```bash
openapi-diff old-spec.yaml new-spec.yaml --fail-on-incompatible
```
