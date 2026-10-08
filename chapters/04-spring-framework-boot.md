# Chapter 4: Spring Framework and Spring Boot

---

## Q076 — Dependency Injection and Constructor Injection

**The one-line answer:** Dependency injection inverts control by having the container supply collaborators rather than having a class create them; constructor injection is the recommended style because it makes dependencies explicit, enforces immutability, and makes the class independently testable.

### Why constructor injection

```java
// Constructor injection — preferred
@Service
public class OrderService {
    private final OrderRepository repository;
    private final PaymentGateway gateway;

    public OrderService(OrderRepository repository, PaymentGateway gateway) {
        this.repository = Objects.requireNonNull(repository);
        this.gateway    = Objects.requireNonNull(gateway);
    }
}
```

- Dependencies are **explicit** in the constructor signature.
- Fields are `final` — the bean is immutable after construction.
- Can be instantiated in unit tests with `new OrderService(mockRepo, mockGateway)` — no Spring context needed.
- Circular dependencies fail **at startup**, not at first call.
- `@Autowired` is optional on single-constructor classes (Spring 4.3+).

### Field injection — why to avoid

```java
// Field injection — avoid
@Service
public class OrderService {
    @Autowired private OrderRepository repository; // mutable, hidden dependency
}
```

- Requires Spring to instantiate — harder to unit test.
- Hides dependencies; callers can't see what the class needs.
- Cannot be `final`; risk of null if Spring hasn't injected yet.

### Setter injection — limited use

Use setter injection only for **optional** dependencies or when a circular dependency genuinely can't be resolved by design. Mark the setter with `@Autowired(required = false)`.

### Circular dependency detection

Constructor injection detects circular dependencies at application startup (`BeanCurrentlyInCreationException`). This forces you to fix the design. Field/setter injection defers the problem and can hide it until runtime.

---

## Q077 — Bean Scopes

**The one-line answer:** Bean scope controls how many instances Spring creates — singleton (one per container) is the default and correct for stateless services; prototype (one per request), request, and session scopes exist for stateful beans and require careful proxy configuration.

### Scopes

| Scope | Instances | Typical use |
|---|---|---|
| `singleton` | 1 per ApplicationContext | Services, repositories, all stateless beans |
| `prototype` | New instance per `getBean()` / inject | Stateful objects that must not be shared |
| `request` | 1 per HTTP request | Request-scoped state (user context) |
| `session` | 1 per HTTP session | Shopping cart, user preferences |
| `application` | 1 per ServletContext | Rare; shared across contexts |

### The singleton mutable-field bug

```java
@Service // singleton
public class ReportService {
    private List<String> results = new ArrayList<>(); // SHARED across all requests

    public List<String> generate(Query q) {
        results.clear();         // one thread clears while another is reading
        results.add(process(q));
        return results;
    }
}
```

Never store request-specific state in a singleton bean's fields.

### Injecting a shorter-scoped bean into a singleton

A `request`-scoped bean cannot be directly injected into a `singleton` because the singleton is created once, but request beans are different per request.

Fix: use a **scoped proxy**:

```java
@Component
@Scope(value = "request", proxyMode = ScopedProxyMode.TARGET_CLASS)
public class RequestContext { ... }

@Service
public class OrderService {
    private final RequestContext ctx; // proxy injected; delegates to real per-request bean
    public OrderService(RequestContext ctx) { this.ctx = ctx; }
}
```

---

## Q078 — Bean Lifecycle

**The one-line answer:** Spring beans go through instantiation → dependency injection → post-construct initialization → in-use → pre-destroy teardown; hooks at each phase allow safe startup and cleanup.

### Lifecycle phases

```
1. Instantiate (constructor called)
2. Inject dependencies (@Autowired, constructor)
3. BeanPostProcessor.postProcessBeforeInitialization
4. @PostConstruct / InitializingBean.afterPropertiesSet
5. BeanPostProcessor.postProcessAfterInitialization
6. Bean in use
7. @PreDestroy / DisposableBean.destroy (on context close)
```

### @PostConstruct and @PreDestroy

```java
@Service
public class CacheWarmingService {
    private final Cache cache;

    public CacheWarmingService(Cache cache) { this.cache = cache; }

    @PostConstruct
    void warmUp() {
        // Dependencies already injected — safe to use them
        cache.load(defaultKeys());
    }

    @PreDestroy
    void shutdown() {
        cache.flush();
    }
}
```

**Never** put slow or failure-prone work in a constructor. With constructor injection every collaborator really is already assigned by the time the constructor runs, so the dependency-ordering argument does not apply — the reason to prefer `@PostConstruct` is **startup behaviour**. `@PostConstruct` runs after the bean is fully wired and after `BeanPostProcessor.postProcessBeforeInitialization`, so it can safely use injected dependencies and be ordered against other beans' init via `SmartLifecycle` phases or `@DependsOn`. Reserve the constructor for pure validation and field assignment; do I/O, cache warming, and remote calls in `@PostConstruct`.

### SmartLifecycle

For ordered startup (e.g., start metrics collection before starting the HTTP server), implement `SmartLifecycle`:

```java
@Component
public class MetricsCollector implements SmartLifecycle {
    @Override public void start() { ... }
    @Override public void stop()  { ... }
    @Override public boolean isRunning() { return running; }
    @Override public int getPhase() { return 0; } // lower = starts first
}
```

---

## Q079 — @Component vs @Bean

**The one-line answer:** `@Component` (and its stereotypes) triggers classpath scanning to auto-detect and register a bean from your own class; `@Bean` on a method in a `@Configuration` class registers a bean from code — typically a third-party class or one needing complex construction logic.

### @Component family

```java
@Component   // generic component
@Service     // service layer (no functional difference — semantic marker)
@Repository  // data access layer (also enables exception translation)
@Controller  // web layer
@RestController // @Controller + @ResponseBody
```

Spring scans packages under `@SpringBootApplication` (which includes `@ComponentScan`).

### @Bean for third-party or complex beans

```java
@Configuration
public class InfrastructureConfig {

    @Bean
    public ObjectMapper objectMapper() {
        return JsonMapper.builder()
            .addModule(new JavaTimeModule())
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
            .build();
    }

    @Bean
    @ConditionalOnMissingBean
    public Clock clock() {
        return Clock.systemUTC();
    }
}
```

You cannot put `@Component` on `ObjectMapper` because you don't own its source. `@Bean` gives full control over instantiation.

### @Configuration class proxying

`@Configuration` classes are CGLIB-proxied by default — calling `@Bean` methods from within the same class returns the same singleton instance (not a new object each call). `@Configuration(proxyBeanMethods = false)` disables proxying for faster startup when you don't call `@Bean` methods directly.

---

## Q080 — Spring Boot Auto-Configuration

**The one-line answer:** Auto-configuration uses conditional annotations to register beans only when specific classes, properties, or other beans are or aren't present — enabling Spring Boot starters to wire common infrastructure without XML or explicit configuration.

### How it works

1. A starter JAR (e.g., `spring-boot-starter-data-jpa`) brings in the dependency and a `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` file listing auto-configuration classes.
2. At startup, Spring Boot loads these classes and evaluates their `@Conditional` annotations.
3. Beans are registered only when conditions pass.

### Key conditional annotations

```java
@ConditionalOnClass(DataSource.class)        // only if DataSource is on classpath
@ConditionalOnMissingBean(DataSource.class)  // only if no DataSource bean exists yet
@ConditionalOnProperty(name = "feature.enabled", havingValue = "true")
@ConditionalOnWebApplication
@ConditionalOnExpression("${env} == 'prod'")
```

### Overriding auto-configuration

Define your own `@Bean` of the same type — `@ConditionalOnMissingBean` prevents the auto-config bean from also being registered:

```java
@Bean
public DataSource dataSource() {
    // Your custom DataSource — auto-config's DataSource bean is skipped
    return HikariDataSource(...);
}
```

### Disabling specific auto-configuration

```java
@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class})
```

Or in `application.properties`:
```properties
spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration
```

### Debugging auto-configuration

```
--debug flag or logging.level.org.springframework.boot.autoconfigure=DEBUG
```

Produces a "Conditions Evaluation Report" showing which auto-configurations matched and which were excluded and why.

---

## Q081 — Spring Boot Startup Flow

**The one-line answer:** Spring Boot startup creates the `ApplicationContext`, runs auto-configuration, refreshes the context (instantiates and wires all beans), then starts the embedded server — failures at any phase produce distinct error messages.

### Startup sequence

```
SpringApplication.run()
  │
  ├─ Load application.properties / YAML
  ├─ Create ApplicationContext (type depends on classpath: servlet, reactive, none)
  ├─ Run ApplicationContextInitializers
  ├─ Load @Configuration classes, @ComponentScan, auto-configurations
  ├─ context.refresh()
  │    ├─ Register bean definitions
  │    ├─ Instantiate singletons (constructor injection, @PostConstruct)
  │    └─ Start embedded server (Tomcat, Netty...)
  ├─ ApplicationReadyEvent fired
  └─ CommandLineRunner / ApplicationRunner callbacks
```

### Common startup failures

| Error | Cause |
|---|---|
| `BeanCreationException` | Constructor threw, dependency missing, `@PostConstruct` failed |
| `BeanCurrentlyInCreationException` | Circular dependency (constructor injection) |
| `UnsatisfiedDependencyException` | No bean of required type found |
| `BindException` | `@ConfigurationProperties` binding failed (wrong type, missing required value) |
| `PortInUseException` | Server port already occupied |

### ApplicationReadyEvent vs ApplicationStartedEvent

- `ApplicationStartedEvent` — context refreshed, runners not yet called.
- `ApplicationReadyEvent` — runners completed; application is ready to serve.

Use `ApplicationReadyEvent` to log "service is up" metrics or send readiness signals.

---

## Q082 — @ConfigurationProperties and Validation

**The one-line answer:** `@ConfigurationProperties` binds a prefix of the environment to a typed Java class, providing type safety, IDE completion, and integrated validation — prefer it over scattered `@Value` annotations for groups of related properties.

### Usage

```java
@ConfigurationProperties(prefix = "app.payment")
@Validated
public class PaymentProperties {
    @NotBlank
    private String apiKey;
    
    @Min(1) @Max(60)
    private int timeoutSeconds = 30;
    
    private String baseUrl = "https://api.payment.com";
    
    // getters and setters (or use @ConstructorBinding for immutable)
}
```

```properties
app.payment.api-key=pk_live_xxx
app.payment.timeout-seconds=10
```

Register with `@EnableConfigurationProperties(PaymentProperties.class)` or place on a `@Configuration` class, or add `@ConfigurationPropertiesScan`.

### Immutable binding (Spring Boot 2.2+)

```java
@ConfigurationProperties(prefix = "app.payment")
public record PaymentProperties(
    @NotBlank String apiKey,
    @Min(1) int timeoutSeconds
) {}
```

### Property precedence (high to low)

The complete, canonical order — this is the one list to memorise:

1. Command-line arguments (`--server.port=9090`)
2. `SPRING_APPLICATION_JSON` environment variable
3. OS environment variables (`SERVER_PORT`)
4. JVM system properties (`-Dserver.port=9090`)
5. `application-{profile}.properties` (filesystem takes priority over classpath)
6. `application.properties` (filesystem over classpath)
7. `@PropertySource` annotations
8. Default values declared in code

Two rules that follow from this and are worth stating unprompted:

- **Profile files override the base file, but do not replace it.** `application-prod.properties` only overrides the keys it actually declares; everything else still comes from `application.properties`.
- **Environment variables beat packaged files**, which is why `SPRING_DATASOURCE_PASSWORD` works as a secrets-injection point without rebuilding the image. See Q093 for activating profiles and Q169 for secrets management.

### @Value vs @ConfigurationProperties

| | `@Value` | `@ConfigurationProperties` |
|---|---|---|
| Type safety | Limited | Full |
| Validation | Manual | `@Validated` + JSR-303 |
| Grouping | One value at a time | Entire namespace |
| Relaxed binding | Partial | Full (`camelCase`, `kebab-case`, `SNAKE_CASE`) |
| IDE metadata | None (manual) | Auto-generated with `spring-boot-configuration-processor` |

---

## Q083 — Spring MVC Request Flow

**The one-line answer:** Every HTTP request flows through `DispatcherServlet` → `HandlerMapping` → `HandlerAdapter` → your controller method → `MessageConverter` → response, with filters, interceptors, and exception handlers wrapping the pipeline at defined points.

### Full flow

```
Client HTTP Request
  │
  ▼
Filter Chain (javax.servlet.Filter / OncePerRequestFilter)
  │  e.g., security filter, CORS filter, MDC filter
  ▼
DispatcherServlet.doDispatch()
  │
  ├─ HandlerMapping.getHandler()      → finds your @RequestMapping method
  ├─ HandlerInterceptor.preHandle()   → runs before handler
  ├─ HandlerAdapter.handle()          → invokes controller method
  │    ├─ ArgumentResolvers           → bind @PathVariable, @RequestBody, etc.
  │    ├─ Your @Controller method
  │    └─ ReturnValueHandlers         → convert return value
  ├─ HandlerInterceptor.postHandle()  → runs after handler (before response write)
  ├─ MessageConverter                 → serialize to JSON/XML
  └─ HandlerInterceptor.afterCompletion() → runs after response sent
  │
  ▼ (on exception anywhere above)
HandlerExceptionResolver / @ExceptionHandler / @ControllerAdvice
```

### Filter vs Interceptor

| | Filter | Interceptor |
|---|---|---|
| Spec | Servlet API | Spring MVC |
| Scope | All requests (even non-MVC) | Only requests handled by DispatcherServlet |
| Spring context access | Possible but awkward | Full access to Spring beans |
| Response body | Can wrap / replace | Cannot modify after handler wrote response |
| Order | Via `@Order` or `FilterRegistrationBean` | Via `WebMvcConfigurer.addInterceptors` |

Filters are better for security, CORS, and request/response transformation. Interceptors are better for logging, auth checks using Spring beans, and adding response headers.

---

## Q084 — @RestController and Message Converters

**The one-line answer:** `@RestController` combines `@Controller` and `@ResponseBody`, telling Spring to serialize the return value to the HTTP response body using the best-match `HttpMessageConverter` based on content negotiation.

### Content negotiation

Spring selects a converter based on:
1. The `Accept` header from the client (what it can receive).
2. The `Content-Type` the method can produce (`@RequestMapping(produces = ...)`).

Jackson's `MappingJackson2HttpMessageConverter` handles `application/json` by default.

### Customizing Jackson

```java
@Bean
public Jackson2ObjectMapperBuilderCustomizer customizer() {
    return builder -> builder
        .featuresToDisable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
        .modules(new JavaTimeModule())
        .serializationInclusion(JsonInclude.Include.NON_NULL);
}
```

### Common issues

- `HttpMessageNotReadableException` — request body cannot be deserialized (wrong JSON structure, type mismatch). Returns 400.
- `HttpMessageNotWritableException` — response object cannot be serialized (circular reference, missing Jackson annotation). Returns 500.
- `415 Unsupported Media Type` — client sent `Content-Type` the endpoint doesn't consume.
- `406 Not Acceptable` — client's `Accept` header doesn't match what the endpoint produces.

---

## Q085 — Request Binding and Validation

**The one-line answer:** Spring MVC binds HTTP input to controller method parameters via argument resolvers; `@Valid` / `@Validated` triggers Bean Validation on `@RequestBody` DTOs and returns `400 Bad Request` automatically when validation fails.

### Binding annotations

```java
@RestController
@RequestMapping("/orders")
public class OrderController {

    @GetMapping("/{id}")
    public OrderResponse getById(
        @PathVariable("id") String id,
        @RequestParam(defaultValue = "false") boolean includeItems
    ) { ... }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public OrderResponse create(@Valid @RequestBody CreateOrderRequest request) { ... }

    @GetMapping
    public Page<OrderResponse> list(@Valid OrderFilter filter) { ... } // @ModelAttribute style
}
```

### Validation DTO

```java
public record CreateOrderRequest(
    @NotBlank(message = "Customer ID is required")
    String customerId,

    @NotEmpty(message = "At least one item required")
    @Size(max = 50)
    List<@Valid OrderItemRequest> items,

    @FutureOrPresent
    LocalDate deliveryDate
) {}
```

When `@Valid` validation fails, Spring throws `MethodArgumentNotValidException` (for `@RequestBody`) or `ConstraintViolationException` (for path/query params). Handle in `@ControllerAdvice`:

```java
@ExceptionHandler(MethodArgumentNotValidException.class)
public ResponseEntity<ProblemDetail> handleValidation(MethodArgumentNotValidException ex) {
    ProblemDetail pd = ProblemDetail.forStatus(400);
    pd.setTitle("Validation failed");
    pd.setProperty("errors", ex.getBindingResult().getFieldErrors().stream()
        .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
        .toList());
    return ResponseEntity.badRequest().body(pd);
}
```

---

## Q086 — Exception Handling with @ControllerAdvice

**The one-line answer:** `@RestControllerAdvice` provides a centralized place to map domain exceptions to HTTP responses with consistent error bodies — keeping error handling out of individual controllers.

### Full example

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(OrderNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ProblemDetail handleNotFound(OrderNotFoundException ex, WebRequest req) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        pd.setTitle("Order not found");
        pd.setProperty("orderId", ex.getOrderId());
        return pd;
    }

    @ExceptionHandler(OptimisticLockingFailureException.class)
    @ResponseStatus(HttpStatus.CONFLICT)
    public ProblemDetail handleConflict(OptimisticLockingFailureException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT,
            "Resource was modified concurrently. Please retry.");
    }

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ProblemDetail handleUnexpected(Exception ex, WebRequest req) {
        String correlationId = getCorrelationId(req);
        log.error("Unexpected error [correlationId={}]", correlationId, ex);
        ProblemDetail pd = ProblemDetail.forStatus(500);
        pd.setProperty("correlationId", correlationId);
        return pd; // never expose ex.getMessage() for unexpected errors
    }
}
```

### ProblemDetail (RFC 7807, Spring Boot 3+)

```json
{
  "type": "https://example.com/errors/order-not-found",
  "title": "Order not found",
  "status": 404,
  "detail": "Order ORD-123 does not exist",
  "orderId": "ORD-123"
}
```

Enable with `spring.mvc.problemdetails.enabled=true` in Spring Boot 3.

### Logging strategy

Log **unexpected** errors (5xx) with full stack trace at the exception handler. Log **expected** domain exceptions (4xx) at DEBUG or INFO without stack trace — they're client errors, not bugs. Never log the same error at multiple layers.

---

## Q087 — Filters, Interceptors, and AOP

**The one-line answer:** Filters handle raw HTTP at the servlet level; interceptors handle Spring MVC-dispatched requests; AOP handles method-level cross-cutting concerns — each operates at a different abstraction level and suits different use cases.

### Choosing the right extension point

| Use case | Best choice |
|---|---|
| JWT extraction, CORS, rate limiting | Filter |
| Logging request/response with Spring context | Interceptor |
| Caching method results | AOP (`@Cacheable`) |
| Transaction management | AOP (`@Transactional`) |
| Authorization (method level) | AOP (`@PreAuthorize`) |
| Metric timing for service methods | AOP (custom aspect or Micrometer) |
| Response body transformation | Filter (wraps `HttpServletResponseWrapper`) |

### Filter example

```java
@Component
@Order(1)
public class CorrelationIdFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res,
                                    FilterChain chain) throws ServletException, IOException {
        String id = Optional.ofNullable(req.getHeader("X-Request-ID"))
                            .orElse(UUID.randomUUID().toString());
        MDC.put("requestId", id);
        res.setHeader("X-Request-ID", id);
        try { chain.doFilter(req, res); }
        finally { MDC.clear(); }
    }
}
```

### Interceptor example

```java
@Component
public class AuditInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object handler) {
        // return false to abort the request
        return true;
    }
    @Override
    public void afterCompletion(HttpServletRequest req, HttpServletResponse res,
                                Object handler, Exception ex) {
        auditService.log(req.getRequestURI(), res.getStatus());
    }
}
```

---

## Q088 — AOP and Proxies

**The one-line answer:** Spring AOP uses JDK dynamic proxies (for interface-based beans) or CGLIB proxies (for class-based beans) to intercept method calls and weave in cross-cutting concerns — this proxy mechanism explains why self-invocation doesn't trigger advice.

### Key AOP terms

- **Aspect:** A class containing advice (the cross-cutting code).
- **Pointcut:** An expression matching join points where advice applies.
- **Advice:** The code to run (before, after, around, after-returning, after-throwing).
- **Join point:** A method execution (Spring AOP only supports method execution join points).
- **Weaving:** How the proxy is applied (runtime in Spring AOP).

### Example — timing aspect

```java
@Aspect
@Component
public class TimingAspect {
    @Around("@annotation(Timed)")
    public Object time(ProceedingJoinPoint pjp) throws Throwable {
        long start = System.nanoTime();
        try {
            return pjp.proceed();
        } finally {
            long elapsed = System.nanoTime() - start;
            metrics.record(pjp.getSignature().getName(), elapsed);
        }
    }
}
```

### The self-invocation pitfall

```java
@Service
public class OrderService {
    public void placeOrder(Order order) {
        validateAndSave(order);        // direct call — bypasses proxy
    }

    @Transactional                     // has NO effect when called from placeOrder above
    public void validateAndSave(Order order) { ... }
}
```

`placeOrder` is called on the proxy, but the proxy delegates to `this`. The inner call `validateAndSave` happens on the real object, not the proxy — so `@Transactional` is never intercepted. Fix: inject `self` reference, restructure into separate beans, or use `AopContext.currentProxy()` (fragile).

### JDK vs CGLIB proxies

- **JDK proxy:** Target must implement at least one interface. Creates a `$Proxy` class.
- **CGLIB proxy:** Subclasses the target class. Can proxy any non-final class/method.
- Spring Boot defaults to CGLIB (`spring.aop.proxy-target-class=true`). Final classes/methods cannot be proxied.

---

## Q089 — @Transactional Mechanics

**The one-line answer:** `@Transactional` is implemented via AOP proxy — when the proxy intercepts a call, it begins a transaction before the method and commits (or rolls back) after it; this means only external calls through the proxy are transactional, and only `RuntimeException` and `Error` trigger rollback by default.

### What happens step by step

```
Caller → Proxy.placeOrder()
  1. Proxy checks @Transactional metadata
  2. TransactionInterceptor: begin transaction (or join existing)
  3. Delegates to real OrderService.placeOrder()
  4. On normal return: commit
  5. On RuntimeException/Error: rollback
  6. On checked exception: COMMIT by default (see rollbackFor)
```

### Rollback rules

```java
// Only rolls back on RuntimeException/Error (default)
@Transactional
public void save(Order order) { ... }

// Also rolls back on checked exceptions
@Transactional(rollbackFor = Exception.class)
public void save(Order order) throws IOException { ... }

// Does NOT roll back on a specific exception
@Transactional(noRollbackFor = StaleObjectStateException.class)
public void update(Order order) { ... }
```

**Gotcha:** A checked exception thrown from a `@Transactional` method does NOT trigger rollback by default — the transaction commits. This is a common data-integrity bug.

### readOnly = true

```java
@Transactional(readOnly = true)
public Order findById(String id) { ... }
```

Hints to Hibernate to skip dirty checking and flush; some databases/drivers optimize read-only transactions. Use on all query-only methods.

### Self-invocation

```java
@Service
public class OrderService {
    public void process() {
        this.save(); // WRONG — not transactional — calls real object, not proxy
    }

    @Transactional
    public void save() { ... }
}
```

Fix: extract `save()` into a separate `@Service` bean.

---

## Q090 — Transaction Propagation and Isolation

**The one-line answer:** Propagation controls what happens when a transactional method is called from within an existing transaction; isolation controls what uncommitted changes from other transactions this transaction can see.

### Propagation levels

| Propagation | Behavior |
|---|---|
| `REQUIRED` (default) | Join existing transaction; create new if none |
| `REQUIRES_NEW` | Always create a new transaction; suspend existing one |
| `NESTED` | Create a savepoint within existing transaction; partial rollback possible |
| `SUPPORTS` | Join existing if present; run non-transactionally if not |
| `NOT_SUPPORTED` | Always run non-transactionally; suspend existing |
| `MANDATORY` | Must join existing; throw if no active transaction |
| `NEVER` | Must not run in a transaction; throw if active |

### REQUIRES_NEW use case — audit logging

```java
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void auditLog(String action) {
    // runs in its own transaction — commits even if outer transaction rolls back
    auditRepo.save(new AuditEntry(action));
}
```

### Isolation levels

| Level | Dirty Read | Non-Repeatable Read | Phantom Read |
|---|---|---|---|
| `READ_UNCOMMITTED` | ✅ possible | ✅ possible | ✅ possible |
| `READ_COMMITTED` (PostgreSQL default) | ❌ prevented | ✅ possible | ✅ possible |
| `REPEATABLE_READ` | ❌ | ❌ | ✅ possible |
| `SERIALIZABLE` | ❌ | ❌ | ❌ |

```java
@Transactional(isolation = Isolation.SERIALIZABLE)
public void transferFunds(Account from, Account to, BigDecimal amount) { ... }
```

Higher isolation = less concurrency, more locking/conflict. Use the minimum isolation that satisfies correctness requirements. PostgreSQL uses MVCC — `READ_COMMITTED` avoids most read anomalies without heavy locking.

---

## Q091 — Spring Data JPA Query Methods

**The one-line answer:** Spring Data JPA auto-implements repository methods from their names, `@Query` annotations, or native SQL — choose the approach based on complexity and need for type safety.

### Method name derivation

```java
public interface OrderRepository extends JpaRepository<Order, Long> {
    List<Order> findByCustomerIdAndStatus(String customerId, OrderStatus status);
    Optional<Order> findByExternalId(String externalId);
    long countByStatus(OrderStatus status);
    boolean existsByExternalIdAndCustomerId(String externalId, String customerId);
    List<Order> findTop5ByCustomerIdOrderByCreatedAtDesc(String customerId);
}
```

### @Query JPQL

```java
@Query("SELECT o FROM Order o JOIN FETCH o.items WHERE o.customerId = :customerId")
List<Order> findWithItemsByCustomer(@Param("customerId") String customerId);
```

### @Query native SQL

```java
@Query(value = "SELECT * FROM orders WHERE status = ?1 AND created_at > NOW() - INTERVAL '7 days'",
       nativeQuery = true)
List<Order> findRecentByStatus(String status);
```

### Projections — returning less than the full entity

```java
public interface OrderSummary {
    Long getId();
    String getCustomerId();
    BigDecimal getTotal();
}

List<OrderSummary> findByStatus(OrderStatus status, Pageable pageable);
```

This avoids fetching all entity fields and associations when only a subset is needed.

---

## Q092 — Pagination with Page and Slice

**The one-line answer:** `Page<T>` runs an extra `COUNT` query for total elements; `Slice<T>` fetches `pageSize + 1` to detect "has next" without a count — prefer `Slice` for large datasets where total count is expensive.

### Page — includes total count

```java
// Repository
Page<Order> findByStatus(OrderStatus status, Pageable pageable);

// Usage
Pageable pageable = PageRequest.of(0, 20, Sort.by("createdAt").descending());
Page<Order> page = repo.findByStatus(ACTIVE, pageable);

page.getContent();       // current page items
page.getTotalElements(); // total matching records (from COUNT query)
page.getTotalPages();
page.hasNext();
```

### Slice — no count query

```java
Slice<Order> findByCustomerId(String customerId, Pageable pageable);

Slice<Order> slice = repo.findByCustomerId(id, PageRequest.of(0, 20));
slice.hasNext(); // true if more pages exist (fetches pageSize+1 to determine)
```

### Deep pagination performance

`OFFSET 10000 LIMIT 20` forces the database to scan and discard 10,000 rows. For large offsets, use keyset (cursor) pagination:

```java
// Keyset pagination — use the last seen ID to filter, not offset
@Query("SELECT o FROM Order o WHERE o.id > :lastId ORDER BY o.id ASC")
List<Order> findAfter(@Param("lastId") long lastId, Pageable pageable);
```

---

## Q093 — Profiles and Configuration Precedence

**The one-line answer:** Spring profiles activate different bean sets and configuration files per environment; property sources follow a defined precedence order where command-line args and environment variables override file-based properties.

### Activating profiles

```bash
# Command line
java -jar app.jar --spring.profiles.active=prod

# Environment variable
SPRING_PROFILES_ACTIVE=prod

# In tests
@ActiveProfiles("test")
```

### Profile-specific beans

```java
@Profile("!prod")  // active in all profiles except prod
@Bean
public DataSource h2DataSource() { ... }

@Profile("prod")
@Bean
public DataSource hikariDataSource() { ... }
```

### Property file loading order

```
application.properties           → base properties
application-{profile}.properties → profile overrides
```

### Property precedence (single canonical list)

The full order is given in Q082 and is identical here — CLI args, `SPRING_APPLICATION_JSON`, OS env vars, JVM system properties, `application-{profile}.properties`, `application.properties`, `@PropertySource`, defaults. There is only one list to remember.

What this question adds is *activation*: a profile changes **which beans exist** and **which file is layered on top**, and `spring.profiles.active` itself follows the same precedence — so `SPRING_PROFILES_ACTIVE=prod` in the environment beats `spring.profiles.active=dev` in `application.properties`. Also note `spring.profiles.active` can take a comma-separated list (`prod,metrics`), and later profiles in the list win for conflicting properties.

### Spring Cloud Config / Vault

For production secrets, use Spring Cloud Config Server or HashiCorp Vault:
```properties
spring.config.import=vault://secret/myapp
```
Vault properties take highest file-based priority and support dynamic rotation.

---

## Q094 — Logging and MDC

**The one-line answer:** Use SLF4J + Logback (Spring Boot default) with structured logging and MDC correlation IDs so every log line from a request can be traced end-to-end across services.

### Logging levels and discipline

```java
log.debug("Processing order {}", orderId);   // development detail — disabled in prod
log.info("Order placed: id={}", orderId);    // significant business events
log.warn("Retry attempt {} for order {}", attempt, orderId); // recoverable issue
log.error("Failed to process order {}", orderId, exception); // always pass exception as last arg
```

Never log with string concatenation in hot paths — format strings are evaluated lazily.

### MDC for correlation

```java
// In a filter (once per request)
MDC.put("requestId", correlationId);
MDC.put("userId", authenticatedUserId);
// ... handle request ...
MDC.clear(); // always in finally

// Logback pattern — includes MDC fields automatically
<pattern>%d{ISO8601} [%X{requestId}] [%X{userId}] %-5level %logger{36} - %msg%n</pattern>
```

### Structured logging with JSON (production)

```xml
<!-- logback-spring.xml -->
<appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
    <encoder class="net.logstash.logback.encoder.LogstashEncoder"/>
</appender>
```

JSON logs enable log aggregation systems (ELK, Loki) to query by field rather than text pattern.

### Log noise reduction

Do not log at every layer for the same event. Log once where you have the most context. Suppress noisy health check and actuator endpoint logs:

```properties
logging.level.org.springframework.web.servlet.DispatcherServlet=WARN
```

---

## Q095 — Spring Boot Actuator

**The one-line answer:** Actuator exposes production-ready endpoints for health checks, metrics, environment info, and thread dumps; always restrict sensitive endpoints behind authentication and never expose them on the public port.

### Key endpoints

| Endpoint | Purpose |
|---|---|
| `/actuator/health` | Liveness/readiness (Kubernetes probes) |
| `/actuator/metrics` | Micrometer metrics |
| `/actuator/info` | Build info, git commit |
| `/actuator/env` | Property values (sanitized) |
| `/actuator/loggers` | Dynamic log level changes at runtime |
| `/actuator/threaddump` | JVM thread dump |
| `/actuator/heapdump` | JVM heap dump (heavyweight!) |
| `/actuator/prometheus` | Prometheus scrape endpoint |

### Security configuration

```properties
management.server.port=8081                  # separate port for actuator
management.endpoints.web.exposure.include=health,info,metrics,prometheus
management.endpoint.health.show-details=when-authorized
management.endpoint.health.probes.enabled=true
```

### Custom health indicator

```java
@Component
public class PaymentGatewayHealthIndicator implements HealthIndicator {
    @Override
    public Health health() {
        try {
            gateway.ping();
            return Health.up().withDetail("provider", "stripe").build();
        } catch (Exception ex) {
            return Health.down().withDetail("reason", ex.getMessage()).build();
        }
    }
}
```

Kubernetes liveness probe: `/actuator/health/liveness`  
Kubernetes readiness probe: `/actuator/health/readiness`

---

## Q096 — Common Spring Startup Failures

**The one-line answer:** Most Spring startup failures are caused by missing beans, circular dependencies, invalid configuration binding, or classpath issues — read the root cause in the exception chain, not just the outer wrapper.

### Diagnosis checklist

**`UnsatisfiedDependencyException: No qualifying bean of type X`**
- The required type is not a Spring bean.
- The implementing class lacks `@Component`/`@Service`.
- The package is not under `@ComponentScan`.
- A `@Profile` condition isn't met.
- A `@ConditionalOn...` condition blocked the bean.

**`BeanCurrentlyInCreationException`** (circular dependency)
- Bean A's constructor requires B; B's constructor requires A.
- Fix: redesign (extract common service, use events), or use setter injection (last resort).

**`BindException` / `BindValidationException`**
- `@ConfigurationProperties` type mismatch or `@NotNull` property missing.
- Check that `app.my-prop` matches the field name and type exactly.

**`IllegalStateException: ApplicationContext has not been refreshed yet`**
- Accessing the context before `refresh()` completes.

**`Failed to configure a DataSource`**
- Spring Data JPA on classpath but no `spring.datasource.url` configured.
- Fix: set properties or exclude `DataSourceAutoConfiguration`.

### Reading the stack trace

Spring wraps exceptions in layers. Always scan for `Caused by:` chains to find the root cause — the outermost exception is usually just `BeanCreationException`.

---

## Q097 — Circular Dependencies

**The one-line answer:** Circular dependencies indicate a design smell — two beans that each need the other usually means a responsibility should be extracted into a third bean, or event-driven decoupling should replace direct injection.

### Detection

Constructor injection fails at startup with `BeanCurrentlyInCreationException`. This is intentional — it forces you to fix the design rather than masking it.

### Fix strategies

**1. Extract a shared dependency:**
```
OrderService → UserService (circular)
↓ fix: extract UserValidator
OrderService → UserValidator ← UserService
```

**2. Use events to break the cycle:**
```java
// Instead of UserService calling OrderService directly
applicationEventPublisher.publishEvent(new UserActivatedEvent(userId));

// OrderService listens
@EventListener
public void onUserActivated(UserActivatedEvent event) { ... }
```

**3. Inject via ApplicationContext lazily (last resort):**
```java
@Lazy
@Autowired
private OrderService orderService; // only resolved on first call, not at startup
```

**4. Interface segregation:** If A depends on a subset of B's behavior, extract that subset into an interface that C implements, where C doesn't depend on A.

---

## Q098 — Spring Boot Performance Tuning

**The one-line answer:** Spring Boot performance tuning targets connection pool sizing, web server thread pools, avoiding blocking calls on reactive/virtual thread workers, and startup time — always measure before tuning.

### HikariCP connection pool (JDBC)

```properties
spring.datasource.hikari.maximum-pool-size=20
spring.datasource.hikari.minimum-idle=5
spring.datasource.hikari.connection-timeout=3000    # ms — fail fast if pool exhausted
spring.datasource.hikari.idle-timeout=600000
spring.datasource.hikari.max-lifetime=1800000
```

Pool size ≈ `(core count × 2) + effective_spindle_count`. Overly large pools add overhead. Under-sized pools cause request queuing. Monitor `hikaricp.connections.pending` and `hikaricp.connections.timeout`.

### Tomcat thread pool

```properties
server.tomcat.threads.max=200          # max worker threads
server.tomcat.threads.min-spare=10
server.tomcat.accept-count=100         # queue depth when all threads busy
server.tomcat.connection-timeout=20000
```

With virtual threads: `spring.threads.virtual.enabled=true` replaces Tomcat thread pool with virtual thread-per-request model.

### Startup optimization

```properties
spring.jpa.open-in-view=false             # disables OSIV (see Q129)
spring.jpa.defer-datasource-initialization=true
spring.main.lazy-initialization=true      # defer bean creation to first use (dev only)
```

### Avoiding blocking calls

Never call `Thread.sleep()`, synchronous HTTP client, or JDBC inside a reactive pipeline or on a virtual thread's carrier without proper isolation. Use dedicated executor for blocking work.

---

## Q099 — @Scheduled Jobs

**The one-line answer:** `@Scheduled` runs methods on a single-threaded scheduler by default — overlapping executions are impossible but also means one slow job blocks all others; use `fixedDelay` for sequential chains and `fixedRate`/`cron` with caution about overlap.

### Configuration

```java
@EnableScheduling
@SpringBootApplication
public class App { }

@Component
public class ReportJob {
    @Scheduled(cron = "0 0 2 * * *")                    // 2 AM daily
    public void generateDailyReport() { ... }

    @Scheduled(fixedDelay = 5000)                        // 5s after last completion
    public void pollExternalQueue() { ... }

    @Scheduled(fixedRate = 60000, initialDelay = 10000) // every 60s, start after 10s
    public void heartbeat() { ... }
}
```

### Single-threaded scheduler problem

All `@Scheduled` methods share **one thread** by default. If `generateDailyReport` takes 30 minutes, `pollExternalQueue` won't run during that time.

Fix: configure a multi-threaded task scheduler:

```java
@Bean
public TaskScheduler taskScheduler() {
    ThreadPoolTaskScheduler scheduler = new ThreadPoolTaskScheduler();
    scheduler.setPoolSize(5);
    scheduler.setThreadNamePrefix("scheduler-");
    return scheduler;
}
```

### Preventing overlap

If a `fixedRate` job takes longer than its interval, executions pile up. Use `fixedDelay` (starts next run after previous finishes) or guard with a flag:

```java
private final AtomicBoolean running = new AtomicBoolean(false);

@Scheduled(fixedRate = 30000)
public void safeJob() {
    if (!running.compareAndSet(false, true)) return; // skip if already running
    try { doWork(); } finally { running.set(false); }
}
```

### Distributed locking for clustered services

In a multi-instance deployment, `@Scheduled` runs on every instance. Use `ShedLock` or a Redis lock to ensure only one instance executes at a time.

---

## Q100 — @Async

**The one-line answer:** `@Async` executes a method in a Spring-managed thread pool; it requires `@EnableAsync`, returns a `Future` or `CompletableFuture` for result/exception access, and suffers the same self-invocation limitation as `@Transactional`.

### Setup

```java
@EnableAsync
@SpringBootApplication
public class App { }

@Bean("notificationExecutor")
public Executor notificationExecutor() {
    ThreadPoolTaskExecutor exec = new ThreadPoolTaskExecutor();
    exec.setCorePoolSize(4);
    exec.setMaxPoolSize(10);
    exec.setQueueCapacity(500);
    exec.setThreadNamePrefix("notify-");
    exec.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
    exec.initialize();
    return exec;
}
```

### Usage

```java
@Service
public class NotificationService {
    @Async("notificationExecutor")
    public CompletableFuture<Void> sendEmail(String to, String subject) {
        emailClient.send(to, subject);
        return CompletableFuture.completedFuture(null);
    }
}
```

### Exception handling

Exceptions from `@Async` void methods are silently swallowed unless you configure an `AsyncUncaughtExceptionHandler`:

```java
@Configuration
public class AsyncConfig implements AsyncConfigurer {
    @Override
    public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        return (ex, method, params) ->
            log.error("Async exception in {}: {}", method.getName(), ex.getMessage(), ex);
    }
}
```

For `CompletableFuture`-returning methods, exceptions are captured in the future and must be handled by the caller.

### Self-invocation — same limitation as @Transactional

```java
// WRONG — @Async has no effect
public void process() { this.sendEmail(...); }

@Async
public CompletableFuture<Void> sendEmail(...) { ... }
```

---

## Q101 — Spring Security Filter Chain Basics

**The one-line answer:** Spring Security adds a chain of servlet filters that intercept every request; the security filter chain validates credentials, populates `SecurityContextHolder`, and enforces access rules before the request reaches controllers.

### Default filter order (simplified)

```
DisableEncodeUrlFilter
SecurityContextHolderFilter
UsernamePasswordAuthenticationFilter
BearerTokenAuthenticationFilter (if JWT)
ExceptionTranslationFilter
AuthorizationFilter
```

### Security configuration (Spring Security 6+)

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(AbstractHttpConfigurer::disable)     // stateless REST APIs
            .sessionManagement(s -> s.sessionCreationPolicy(STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health/**").permitAll()
                .requestMatchers("/api/public/**").permitAll()
                .requestMatchers(HttpMethod.GET, "/api/orders/**").hasRole("USER")
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
            .build();
    }
}
```

### SecurityContextHolder

Stores the `Authentication` object for the current request thread. After filter chain validation, your controllers can access it:

```java
Authentication auth = SecurityContextHolder.getContext().getAuthentication();
String userId = ((JwtAuthenticationToken) auth).getToken().getSubject();
```

### Adding a custom filter

```java
http.addFilterBefore(new RateLimitFilter(), AuthorizationFilter.class);
```

---

## Q102 — Docker, Layered JARs, and Graceful Shutdown

**The one-line answer:** Spring Boot builds layered JARs so unchanged dependency layers are cached in Docker, reducing image rebuild time; graceful shutdown ensures in-flight requests complete before the JVM exits on SIGTERM.

### Layered JAR structure

```
layers:
  ├── dependencies        (rarely changes — cached across builds)
  ├── spring-boot-loader  (rarely changes)
  ├── snapshot-dependencies (changes on SNAPSHOT updates)
  └── application         (your code — changes every build)
```

### Dockerfile (multi-stage with layers)

```dockerfile
FROM eclipse-temurin:21-jre AS builder
WORKDIR /app
COPY target/*.jar app.jar
RUN java -Djarmode=layertools -jar app.jar extract

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=builder /app/dependencies/ ./
COPY --from=builder /app/spring-boot-loader/ ./
COPY --from=builder /app/snapshot-dependencies/ ./
COPY --from=builder /app/application/ ./
ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
```

### Graceful shutdown

```properties
server.shutdown=graceful
spring.lifecycle.timeout-per-shutdown-phase=30s
```

On SIGTERM: Spring stops accepting new requests, waits up to 30s for in-flight requests to complete, then calls `@PreDestroy` and closes the context.

Kubernetes must be configured with `terminationGracePeriodSeconds > timeout-per-shutdown-phase + application warmup` to avoid `OOMKilled` or premature kill.

---

## Q103 — Micrometer and Tracing

**The one-line answer:** Micrometer is Spring Boot's metrics facade that exports to Prometheus/Datadog/CloudWatch; Micrometer Tracing (with Brave or OpenTelemetry) propagates trace/span IDs across service calls for distributed tracing.

### Core metric types

```java
@Component
public class OrderMetrics {
    private final Counter ordersPlaced;
    private final Timer orderProcessingTime;
    private final Gauge activeOrders;

    public OrderMetrics(MeterRegistry registry) {
        ordersPlaced = Counter.builder("orders.placed")
            .tag("region", "eu-west")
            .description("Total orders placed")
            .register(registry);

        orderProcessingTime = Timer.builder("orders.processing.time")
            .publishPercentiles(0.5, 0.95, 0.99)
            .register(registry);

        activeOrders = Gauge.builder("orders.active", activeOrderCount, AtomicInteger::get)
            .register(registry);
    }
}
```

### Cardinality warning

High-cardinality tags (user IDs, order IDs) on metrics create millions of time series and crash Prometheus. Only use low-cardinality tags (status, region, endpoint group).

### Tracing

```properties
management.tracing.sampling.probability=0.1   # sample 10% of requests
management.zipkin.tracing.endpoint=http://zipkin:9411/api/v2/spans
```

Trace ID propagates automatically through `RestTemplate`, `WebClient`, Kafka headers, and thread pools when using Micrometer Tracing with context propagation.

---

## Q104 — File Upload and Streaming Responses

**The one-line answer:** Use `MultipartFile` for small file uploads with size limits enforced by Spring; stream large responses with `StreamingResponseBody` or `ResponseBodyEmitter` to avoid loading entire files into heap.

### File upload

```java
@PostMapping("/documents")
public ResponseEntity<String> upload(@RequestParam("file") MultipartFile file) {
    if (file.isEmpty()) return ResponseEntity.badRequest().body("Empty file");
    if (file.getSize() > MAX_SIZE) return ResponseEntity.status(413).build();

    String path = storageService.store(file.getOriginalFilename(), file.getInputStream());
    return ResponseEntity.created(URI.create("/documents/" + path)).build();
}
```

```properties
spring.servlet.multipart.max-file-size=10MB
spring.servlet.multipart.max-request-size=10MB
```

### Streaming large responses

```java
@GetMapping(value = "/reports/{id}/csv", produces = "text/csv")
public ResponseEntity<StreamingResponseBody> downloadCsv(@PathVariable String id) {
    StreamingResponseBody body = outputStream -> {
        try (var writer = new OutputStreamWriter(outputStream)) {
            reportService.streamCsv(id, writer); // writes incrementally
        }
    };
    return ResponseEntity.ok()
        .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"report.csv\"")
        .body(body);
}
```

This writes the response incrementally without loading the entire file into memory.

---

## Q105 — Designing a Spring Boot Service Structure

**The one-line answer:** Organize by feature/domain rather than by technical layer — it keeps related code together, reduces cross-package dependencies, and scales to a modular monolith naturally.

### Technical layering (common but limiting)

```
src/main/java/com/example/
  controller/   ← all controllers
  service/      ← all services
  repository/   ← all repositories
  model/        ← all entities
```

Works for small apps but causes circular-reasoning when features grow: "where does this belong?"

### Domain/feature packaging (preferred)

```
src/main/java/com/example/
  orders/
    OrderController.java
    OrderService.java
    OrderRepository.java
    Order.java
    OrderStatus.java
    CreateOrderRequest.java
    OrderResponse.java
    events/
      OrderPlacedEvent.java
  customers/
    CustomerController.java
    CustomerService.java
    ...
  shared/
    validation/
    events/
    config/
```

Advantages:
- Each feature is self-contained — easy to extract to a microservice later.
- Package-private visibility hides internals.
- High cohesion, low coupling between packages.

### Layering rules

```
Controller → ApplicationService → DomainService / Domain Model
                               → Repository (interface)
Repository (interface) ← Repository (implementation, JPA)
```

- Domain model has no Spring dependencies.
- Application service orchestrates use cases, owns transactions.
- Controller handles HTTP concerns only — no business logic.
- Never call the repository directly from a controller.
