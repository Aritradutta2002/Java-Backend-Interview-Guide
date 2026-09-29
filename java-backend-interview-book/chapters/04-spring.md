# Chapter 4. Spring Framework and Spring Boot

All answers assume Spring Boot 3.x on Spring Framework 6 with Java 17, which means the `jakarta.*` namespace, `SecurityFilterChain`-style configuration and Hibernate 6. Where behaviour is a default that can be changed, the text says so.

## Q076. What does dependency injection solve, and why prefer constructor injection?

**Priority:** Must Know  
**Why interviewers ask it:** It is the foundation of every Spring answer that follows, and constructor injection is a design decision, not a style preference.

**Interview-ready answer:** Dependency injection inverts control of object creation: a class declares what it needs and the container supplies it, so the class depends on abstractions rather than on constructing concrete collaborators. I prefer constructor injection because it makes dependencies explicit and mandatory, allows the fields to be `final` so the object is immutable and safely published, and lets me instantiate the class in a plain unit test with `new` and hand-written fakes — no Spring context required. It also surfaces design problems: a constructor with nine parameters is telling me the class does too much. Field injection hides dependencies, prevents `final` fields, and cannot be used without reflection in tests.

**In-depth explanation:** Spring resolves constructor parameters by type, falling back to `@Qualifier` or the parameter name when several candidates exist. Since Spring 4.3 a single constructor needs no `@Autowired` annotation at all. Setter injection remains useful for genuinely optional dependencies, and `ObjectProvider<T>` handles optional or multiple candidates cleanly. A practical benefit of constructor injection is that circular dependencies fail fast at startup rather than producing a half-initialised bean; since Boot 2.6 circular references are rejected by default, and re-enabling them with `spring.main.allow-circular-references` is a workaround, not a fix. The deeper point is that DI exists to decouple policy from wiring — the same service class should run in production with a Kafka publisher and in a test with an in-memory one, without conditional code inside the class.

**Practical backend example:** A service whose dependencies are visible and testable:

```java
@Service
public class CheckoutService {
    private final OrderRepository orders;          // final: set once, safely published
    private final PaymentGateway payments;

    public CheckoutService(OrderRepository orders, PaymentGateway payments) { // no @Autowired needed
        this.orders = orders;
        this.payments = payments;
    }
}

// unit test: no Spring context at all
var service = new CheckoutService(new InMemoryOrderRepository(), new StubPaymentGateway());
```

**Common follow-ups:**
- What about circular dependencies? They are rejected by default in Boot 2.6+; extract the shared behaviour into a third bean or use an event instead of forcing `@Lazy`.
- When is setter injection acceptable? For genuinely optional collaborators, or when a framework requires a no-argument constructor.
- How do you inject one of several implementations? `@Qualifier` by bean name, `@Primary` for a default, or inject `List<T>`/`Map<String, T>` to get them all.

**Mistakes to avoid:** Using `@Autowired` on fields because it is shorter; calling `new` on a dependency inside a service and losing substitutability; using `@Lazy` to hide a circular design problem.

**Production perspective:** Explicit constructor dependencies make refactoring and dependency auditing far easier; you can see from the signature what a class touches. It also keeps startup failures loud and early, which is much better than discovering a missing bean on the first production request.

**Related concepts covered:** Inversion of control, bean qualification, immutability, testability, circular dependency handling.

## Q077. How are component scanning and bean registration different?

**Priority:** Must Know  
**Why interviewers ask it:** Knowing both routes explains how third-party classes join the context and why a bean sometimes "isn't found".

**Interview-ready answer:** Component scanning discovers your own classes annotated with `@Component` and its stereotypes — `@Service`, `@Repository`, `@Controller`, `@RestController` — within the packages Spring scans, which by default is the package of the `@SpringBootApplication` class and everything below it. Explicit registration with `@Bean` methods inside a `@Configuration` class is how I register classes I do not own, such as an `ObjectMapper`, a `RestClient` or a third-party client, and how I control construction when it needs parameters or conditional logic. Both produce singletons in the same container; scanning is convention, `@Bean` is explicit configuration.

**In-depth explanation:** The stereotypes are semantically meaningful: `@Repository` adds persistence exception translation, `@RestController` implies `@ResponseBody`, and `@Configuration` classes are proxied by default so that calling one `@Bean` method from another returns the shared singleton instead of a new instance. Setting `proxyBeanMethods = false` on `@Configuration` avoids that proxy for a small startup gain, but then inter-method calls create new objects — a subtle trap. Package placement matters: a `@Service` in a sibling package of the main class is never scanned, which is the usual cause of "required a bean of type X that could not be found". `@Import`, `@ComponentScan(basePackages = ...)` and auto-configuration classes listed in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` are the remaining registration routes.

**Practical backend example:** Registering a third-party client explicitly while scanning your own services:

```java
@Configuration
public class HttpClientConfig {
    @Bean
    RestClient pricingRestClient(RestClient.Builder builder,
                                 @Value("${pricing.base-url}") String baseUrl) {
        return builder.baseUrl(baseUrl)
                      .requestFactory(new SimpleClientHttpRequestFactory())
                      .build();                       // a class you do not own -> @Bean
    }
}

@Service                                              // your own class -> component scanning
public class PricingClient { /* ... */ }
```

**Common follow-ups:**
- How do you register a class from a library? With a `@Bean` method, since you cannot annotate its source.
- Why was my `@Service` not found? It is outside the scanned package tree, or its auto-configuration condition excluded it.
- What does `proxyBeanMethods = false` change? Inter-`@Bean`-method calls no longer return the container singleton; they execute the method again.

**Mistakes to avoid:** Putting components outside the main application package; using `@Component` on a class that also needs constructor arguments only known at runtime; scanning very broad packages, which slows startup and can register unwanted beans.

**Production perspective:** Over-broad component scanning lengthens startup and can pull in test or sample classes. Keep the application package tree deliberate, and prefer explicit `@Bean` definitions for anything with configuration-dependent construction.

**Related concepts covered:** Stereotype annotations, @Configuration proxying, auto-configuration imports, bean not found diagnosis, startup cost.

## Q078. What happens during bean creation and lifecycle?

**Priority:** Important  
**Why interviewers ask it:** Lifecycle knowledge explains initialisation failures, proxy behaviour and why `@PostConstruct` sometimes sees incomplete state.

**Interview-ready answer:** For each singleton, Spring instantiates the bean (constructor injection happens here), populates remaining dependencies, calls `*Aware` callbacks, runs `BeanPostProcessor` before-initialisation hooks, then `@PostConstruct`, then `InitializingBean.afterPropertiesSet`, then any custom init method, then post-initialisation hooks — which is where AOP proxies such as `@Transactional` are created. Once all singletons are ready the context publishes `ContextRefreshedEvent` and Boot fires `ApplicationRunner`/`CommandLineRunner`. On shutdown it runs `@PreDestroy` and `DisposableBean.destroy` in reverse dependency order. The key consequence is that inside a constructor or `@PostConstruct` the bean is not yet proxied, so self-calls there bypass transactional and async behaviour.

**In-depth explanation:** `BeanPostProcessor` is the extension point behind most Spring "magic": `AutowiredAnnotationBeanPostProcessor` performs injection, `AbstractAutoProxyCreator` wraps beans in proxies, and `ConfigurationPropertiesBindingPostProcessor` binds configuration. Because proxies are applied after initialisation, work that must run through the proxy belongs in an `ApplicationRunner` or an `ApplicationListener<ApplicationReadyEvent>` rather than in `@PostConstruct`. Prototype beans are not fully managed: Spring creates and configures them but does not call destruction callbacks, so resources must be released explicitly. `SmartLifecycle` gives ordered start and stop phases, which is how message listener containers are started after the web layer is ready and stopped first during shutdown.

**Practical backend example:** Choosing the right hook for warm-up work:

```java
@Component
public class CacheWarmer {
    private final PricingService pricing;            // proxied bean
    public CacheWarmer(PricingService pricing) { this.pricing = pricing; }

    @PostConstruct
    void validateConfig() { /* cheap, local checks only - no proxied self-calls, no DB work */ }

    @EventListener(ApplicationReadyEvent.class)      // context fully initialised and proxied
    void warmUp() { pricing.preloadPopularSkus(); }
}
```

**Common follow-ups:**
- When does `@PostConstruct` run? After dependency injection but before AOP proxies are in place around that bean.
- Why is my `@Transactional` ignored during startup? The proxy is not applied to self-invocations inside initialisation; use `ApplicationReadyEvent`.
- Are prototype beans destroyed by Spring? No; destruction callbacks are not invoked for prototypes.

**Mistakes to avoid:** Doing network or database work in `@PostConstruct` and delaying startup; relying on bean initialisation order instead of dependencies; putting `@Transactional` on an init method.

**Production perspective:** Work performed at startup extends deployment time and can fail a rollout. Prefer readiness-gated warm-up, keep initialisation fast, and let health checks report when the application is ready rather than blocking the context.

**Related concepts covered:** BeanPostProcessor, AOP proxy timing, ApplicationReadyEvent, SmartLifecycle, prototype limitations.

## Q079. What are bean scopes and singleton thread-safety implications?

**Priority:** Must Know  
**Why interviewers ask it:** Shared mutable state in a singleton bean is one of the most common concurrency bugs in Spring applications.

**Interview-ready answer:** The default scope is singleton: one instance per application context, shared by every request thread. That is fine as long as the bean is stateless or only holds immutable or thread-safe state; a mutable instance field on a controller or service is shared across concurrent requests and will corrupt data. Prototype creates a new instance per lookup, and the web scopes — request, session, application — bind an instance to that lifetime. Injecting a shorter-lived scope into a singleton needs a proxy or an `ObjectProvider`, otherwise the first instance is captured forever. My default is stateless singletons with all request state passed as method parameters.

**In-depth explanation:** "Singleton" in Spring means one per container, not the Gang of Four singleton pattern, and it is not automatically thread-safe — the container makes no synchronisation promises. Request-scoped beans are implemented with a scoped proxy that resolves the current request from a `ThreadLocal`, which means they do not work on a different thread, such as inside `@Async` or a `CompletableFuture` continuation, without explicit context propagation. Prototype beans injected into singletons are resolved once at injection time; `@Lookup` methods, `ObjectProvider<T>.getObject()` or `@Scope(proxyMode = TARGET_CLASS)` obtain a fresh instance per call. Fields that are safe include immutable configuration values, thread-safe collaborators (repositories, `RestClient`, `ObjectMapper`) and concurrent data structures.

**Practical backend example:** An unsafe field and its stateless replacement:

```java
@RestController
public class ReportController {
    // BROKEN: shared across all concurrent requests
    // private List<Row> rows = new ArrayList<>();

    private final ReportService reportService;        // stateless collaborator - safe
    public ReportController(ReportService reportService) { this.reportService = reportService; }

    @GetMapping("/reports/{id}")
    public ReportDto get(@PathVariable UUID id) {
        List<Row> rows = reportService.rows(id);      // request state stays on the stack
        return ReportDto.from(rows);
    }
}
```

**Common follow-ups:**
- Is a singleton bean thread-safe? Only if it holds no mutable state; Spring adds no synchronisation.
- How do you inject a prototype into a singleton? `ObjectProvider`, `@Lookup`, or a scoped proxy — plain injection captures one instance.
- Do request-scoped beans work in `@Async` methods? Not by default; the request context is thread-bound and must be propagated explicitly.

**Mistakes to avoid:** Caching per-user data in a service field; using a non-thread-safe `SimpleDateFormat` as a bean field (use `DateTimeFormatter`, which is immutable); assuming prototype scope solves a concurrency problem in a singleton caller.

**Production perspective:** Shared-state bugs appear only under concurrency, so they pass functional tests and surface as cross-user data leakage in production — a correctness and privacy problem. Code review should treat any mutable field in a singleton as suspicious.

**Related concepts covered:** Scoped proxies, ThreadLocal request context, stateless design, thread-safe collaborators, async context propagation.

## Q080. How does Spring Boot auto-configuration decide what to create?

**Priority:** Must Know  
**Why interviewers ask it:** Auto-configuration feels like magic until you can explain conditions and inspect the report.

**Interview-ready answer:** `@SpringBootApplication` includes `@EnableAutoConfiguration`, which loads auto-configuration classes listed in each starter's `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`. Each class is guarded by conditions: `@ConditionalOnClass` (the library is on the classpath), `@ConditionalOnMissingBean` (you have not defined your own), `@ConditionalOnProperty`, `@ConditionalOnWebApplication` and others. So adding `spring-boot-starter-data-jpa` plus a driver gives you a `DataSource`, an `EntityManagerFactory` and a transaction manager — unless you define your own, in which case `@ConditionalOnMissingBean` backs off. To see exactly what happened I run with `--debug` or open `/actuator/conditions`, which lists positive and negative matches with reasons.

**In-depth explanation:** Ordering matters: auto-configurations run after user configuration so that `@ConditionalOnMissingBean` sees your beans, and `@AutoConfigureBefore`/`@AutoConfigureAfter` sequence them relative to each other. Properties are bound through `@ConfigurationProperties` classes such as `DataSourceProperties` and `ServerProperties`, which is why `application.yml` keys map so predictably. You can exclude a configuration with `@SpringBootApplication(exclude = ...)` or `spring.autoconfigure.exclude`. Note that `@ConditionalOnMissingBean` evaluates on bean type by default, so defining a bean of a different type will not disable the default. Boot 2.7 moved the registration file from `spring.factories` to the `AutoConfiguration.imports` file, and Boot 3 completed that move — relevant when reading older tutorials or writing your own starter.

**Practical backend example:** Overriding one auto-configured bean while keeping the rest:

```java
@Configuration
public class JacksonConfig {
    @Bean                                             // replaces the auto-configured ObjectMapper
    ObjectMapper objectMapper() {                     // because of @ConditionalOnMissingBean
        return JsonMapper.builder()
                .addModule(new JavaTimeModule())
                .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
                .serializationInclusion(JsonInclude.Include.NON_NULL)
                .build();
    }
}
```

```bash
java -jar app.jar --debug          # prints the condition evaluation report
curl localhost:8080/actuator/conditions | jq '.contexts.application.positiveMatches | keys'
```

**Common follow-ups:**
- How do you inspect what was auto-configured? `--debug` at startup or the `/actuator/conditions` endpoint.
- How do you override a default bean? Define your own of the same type; most auto-configurations back off via `@ConditionalOnMissingBean`.
- How do you disable one entirely? `spring.autoconfigure.exclude` or the `exclude` attribute of `@SpringBootApplication`.

**Mistakes to avoid:** Assuming auto-configuration is reflection-based guesswork rather than conditional configuration; excluding a whole starter when one property would do; defining a bean of a subtly different type and wondering why the default is still active.

**Production perspective:** Startup behaviour differences between environments usually come from classpath or property differences that flip conditions. The condition report is the fastest way to prove which branch was taken in a given deployment.

**Related concepts covered:** Conditional annotations, starters, property binding, actuator conditions endpoint, custom starters.

## Q081. How should profiles and external configuration be managed?

**Priority:** Must Know  
**Why interviewers ask it:** Configuration mistakes cause outages and credential leaks, and precedence rules are frequently misunderstood.

**Interview-ready answer:** I keep one `application.yml` with safe defaults, profile-specific files such as `application-prod.yml` for structural differences, and put anything environment-specific or secret into environment variables or a secret manager. Spring Boot resolves properties in a defined order where later sources win: command-line arguments beat environment variables, which beat profile-specific files, which beat the base file. Relaxed binding means `SPRING_DATASOURCE_URL` maps to `spring.datasource.url`, which is exactly how containers supply configuration. Profiles should express environment topology, not business logic; scattering `@Profile` across services makes behaviour hard to reason about and untestable.

**In-depth explanation:** The full precedence list includes devtools settings, test properties, command-line arguments, `SPRING_APPLICATION_JSON`, servlet parameters, JNDI, OS environment variables, Java system properties, profile-specific files outside and inside the jar, then the base files. Boot 3 supports config trees (`spring.config.import=configtree:/etc/secrets/`) for Kubernetes secrets mounted as files, and `spring.config.import` for sources such as Vault or Config Server. Secrets must never be committed, and they should not be passed as command-line arguments because they appear in the process list. `@ConfigurationProperties` with `@Validated` turns configuration errors into startup failures, which is exactly what you want — failing at boot is better than failing on the first request. Keep profile use minimal and prefer property values to conditional beans wherever possible.

**Practical backend example:** Typed, validated configuration with environment overrides:

```yaml
# application.yml
payments:
  base-url: https://sandbox.payments.local
  timeout: 2s
  api-key: ${PAYMENTS_API_KEY}     # supplied by the environment, never committed
```

```java
@Validated
@ConfigurationProperties(prefix = "payments")
public record PaymentsProperties(@NotBlank String baseUrl,
                                 @NotNull Duration timeout,
                                 @NotBlank String apiKey) {}
```

**Common follow-ups:**
- What wins in property precedence? Command-line arguments over environment variables over profile files over the base file; the reference documentation lists the exact order.
- How do you supply secrets in Kubernetes? Environment variables from a Secret, or mounted files read with a config tree import; never baked into the image.
- Should business rules live behind profiles? No; use feature flags or configuration values so behaviour is testable without switching profiles.

**Mistakes to avoid:** Committing credentials to `application-prod.yml`; using `@Value` everywhere instead of typed properties; relying on the default profile in production; duplicating whole configuration files per environment.

**Production perspective:** Validated configuration at startup converts a class of runtime incidents into deployment failures caught by the rollout. Also log the active profiles at startup — but never log property values that may contain secrets.

**Related concepts covered:** Property precedence, relaxed binding, @ConfigurationProperties validation, secret management, config trees.

## Q082. What is the Spring MVC request lifecycle?

**Priority:** Must Know  
**Why interviewers ask it:** Knowing the order of filters, handler mapping, argument resolution and exception handling makes debugging web behaviour systematic.

**Interview-ready answer:** The servlet container passes the request through the filter chain — including Spring Security's filter — to the `DispatcherServlet`. It asks the `HandlerMapping` which controller method matches, then the `HandlerAdapter` invokes it. Before invocation, `HandlerInterceptor.preHandle` runs, then argument resolvers bind path variables, query parameters and the body, with `@Valid` triggering Bean Validation at that point. The method returns an object, a return-value handler serialises it through an `HttpMessageConverter` (Jackson for JSON), and `postHandle`/`afterCompletion` run. If anything throws, the `HandlerExceptionResolver` chain handles it, which is where `@ControllerAdvice` and `@ExceptionHandler` participate. Errors thrown in filters are outside MVC and land on the servlet error page instead.

**In-depth explanation:** That last distinction matters in practice: a `@ControllerAdvice` cannot handle an exception thrown by a filter, because the dispatcher never ran; security authentication failures are therefore handled by Spring Security's own entry point and access-denied handler, not by your advice. Content negotiation selects the converter based on the `Accept` header and the return type. `ResponseEntity` gives explicit control over status and headers. Spring 6 adds `ProblemDetail` (RFC 7807) as a first-class error representation, and `ResponseEntityExceptionHandler` already maps common Spring exceptions to it. Async handling differs: returning `Callable`, `DeferredResult` or `CompletableFuture` releases the container thread while processing continues, with interceptors following the `AsyncHandlerInterceptor` contract.

**Practical backend example:** Validation plus a consistent error shape:

```java
@RestController
@RequestMapping("/api/orders")
public class OrderController {
    @PostMapping
    public ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest request) {
        Order order = orderService.place(request.toCommand());
        return ResponseEntity.created(URI.create("/api/orders/" + order.id()))
                             .body(OrderResponse.from(order));
    }
}

@RestControllerAdvice
class ApiExceptionHandler {
    @ExceptionHandler(MethodArgumentNotValidException.class)
    ProblemDetail onInvalid(MethodArgumentNotValidException ex) {
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        problem.setTitle("Validation failed");
        problem.setProperty("errors", ex.getBindingResult().getFieldErrors().stream()
                .collect(Collectors.toMap(FieldError::getField, FieldError::getDefaultMessage, (a, b) -> a)));
        return problem;                                   // problem-details body (RFC 9457)
    }
}
```

**Common follow-ups:**
- Where does validation run? During argument resolution, before the controller body executes; failures raise `MethodArgumentNotValidException`.
- Can `@ControllerAdvice` handle filter exceptions? No; those occur before the dispatcher, so security and servlet-level handlers deal with them.
- What is the difference between an interceptor and a filter here? Filters wrap the whole servlet request; interceptors run inside the dispatcher and know which handler was selected.

**Mistakes to avoid:** Expecting `@ExceptionHandler` to catch authentication failures; returning entities directly and triggering lazy loading during serialisation; ignoring content negotiation and hard-coding `produces` incorrectly.

**Production perspective:** A single consistent error contract across all endpoints — ideally `ProblemDetail` — makes client handling and log triage far simpler. Always include a correlation identifier in error responses so a user report maps to a log entry.

**Related concepts covered:** DispatcherServlet flow, argument resolvers, HttpMessageConverter, ProblemDetail, async request handling, filter versus interceptor.

## Q083. How do @RequestParam, @PathVariable and @RequestBody differ?

**Priority:** Important  
**Why interviewers ask it:** Correct binding choices reflect an understanding of HTTP semantics, not just Spring annotations.

**Interview-ready answer:** `@PathVariable` binds a segment of the URI template and identifies a resource — `/orders/{id}`. `@RequestParam` binds query string parameters or form fields, which suit filtering, sorting and pagination — `/orders?status=PAID&page=2`. `@RequestBody` deserialises the request body, normally JSON via Jackson, and is used for create and update payloads. Required-ness differs: path variables are inherently required, request parameters can have `required = false` and a `defaultValue`, and a missing body produces a 400. Header and cookie values have their own annotations. The rule of thumb is identity in the path, filters in the query, and state in the body.

**In-depth explanation:** Type conversion happens through Spring's `ConversionService`, so `UUID`, `LocalDate` and enums bind automatically; a malformed value produces `MethodArgumentTypeMismatchException`, which maps to 400 rather than 500 if you handle it. Validation applies differently: `@Valid @RequestBody` triggers `MethodArgumentNotValidException`, while constraints directly on `@RequestParam` require `@Validated` on the class and raise `ConstraintViolationException` — two different exception types that both deserve mapping in your advice. Jackson deserialisation of records works in Boot 3 without extra annotations in most cases. Sensitive data should never travel in query parameters because URLs are logged by proxies and stored in browser history; use the body or a header instead.

**Practical backend example:** One endpoint using each binding correctly:

```java
@GetMapping("/api/customers/{customerId}/orders")
public Page<OrderSummary> list(
        @PathVariable UUID customerId,                                   // identity
        @RequestParam(defaultValue = "PAID") OrderStatus status,          // filter, with default
        @RequestParam(required = false) @Past LocalDate since,            // optional filter
        @PageableDefault(size = 20, sort = "createdAt") Pageable pageable) {
    return orderQueryService.search(customerId, status, since, pageable);
}

@PutMapping("/api/orders/{id}")
public OrderResponse update(@PathVariable UUID id, @Valid @RequestBody UpdateOrderRequest body) {
    return OrderResponse.from(orderService.update(id, body.toCommand()));
}
```

**Common follow-ups:**
- How are invalid bodies reported? Jackson failures surface as `HttpMessageNotReadableException` (400); constraint failures as `MethodArgumentNotValidException`.
- Can GET have a body? HTTP does not forbid it, but it is not interoperable — use query parameters, or POST for complex searches.
- Why not put a token in a query parameter? URLs are logged and cached; credentials belong in headers.

**Mistakes to avoid:** Using `@RequestParam` for resource identity; accepting entities as request bodies; forgetting `@Validated` when validating parameters; putting personally identifiable data in the URL.

**Production perspective:** Query parameters end up in access logs and traces; body content usually does not. That difference matters for both privacy compliance and log volume, and it should drive the API design rather than convenience.

**Related concepts covered:** HTTP semantics, type conversion, validation exception types, pagination parameters, logging and privacy.

## Q084. How would you validate requests and return consistent errors?

**Priority:** Must Know  
**Why interviewers ask it:** Error contracts are part of an API's public surface, and inconsistent ones are a real source of client bugs.

**Interview-ready answer:** I validate DTO shape declaratively with Jakarta Bean Validation — `@NotBlank`, `@Positive`, `@Email`, `@Size` — triggered by `@Valid` on the request body, and I use `@Valid` on nested objects and collection elements so the whole graph is checked. Business rules that need database state or cross-field logic stay in the service layer and throw domain exceptions. Both paths converge in a `@RestControllerAdvice` that produces one consistent error body, ideally `ProblemDetail` with a stable `type`, a human-readable `title`, a field-level error list and a correlation ID. Validation returns 400, domain conflicts 409, missing resources 404, and anything unexpected 500 without leaking a stack trace.

**In-depth explanation:** Group validation with constraint groups handles create-versus-update differences without duplicating DTOs, and custom constraints (`@Constraint` with a `ConstraintValidator`) keep complex rules declarative. Note the exception taxonomy: `MethodArgumentNotValidException` for bodies, `ConstraintViolationException` for parameter-level constraints, `HttpMessageNotReadableException` for malformed JSON, and `MethodArgumentTypeMismatchException` for bad path or query types. Extending `ResponseEntityExceptionHandler` gives sensible defaults for the Spring-raised set. Accumulate all field errors rather than failing on the first one, since clients want to show every problem at once. Never echo the raw input value of a sensitive field in the error message, and keep messages stable enough that clients can rely on codes rather than prose.

**Practical backend example:** Layered validation with a single error contract:

```java
public record CreateOrderRequest(
        @NotNull UUID customerId,
        @NotEmpty @Valid List<LineRequest> lines,          // nested validation
        @Size(max = 280) String note) {
    public record LineRequest(@NotBlank String sku, @Positive int quantity) {}
}

@Service
public class OrderService {
    @Transactional
    public Order place(PlaceOrderCommand command) {
        if (!inventory.hasStock(command.lines())) {
            throw new InsufficientStockException(command.lines());   // business rule -> 409
        }
        return orderRepository.save(Order.from(command));
    }
}

@RestControllerAdvice
class ApiErrors extends ResponseEntityExceptionHandler {
    @ExceptionHandler(InsufficientStockException.class)
    ProblemDetail onStock(InsufficientStockException ex) {
        ProblemDetail p = ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, ex.getMessage());
        p.setType(URI.create("https://api.example.com/problems/insufficient-stock"));
        p.setProperty("correlationId", MDC.get("correlationId"));
        return p;
    }
}
```

**Common follow-ups:**
- How do you validate nested objects? Annotate the field with `@Valid`; without it the nested constraints are skipped.
- Can `@Valid` replace service-layer validation? No; it checks shape and format, not invariants that depend on stored state.
- Which status code for a business conflict? 409 for state conflicts, 422 when the payload is syntactically valid but semantically unacceptable, 400 for malformed input.

**Mistakes to avoid:** Returning 500 for validation failures; exposing stack traces or SQL text to clients; validating only in the controller and trusting the service; inconsistent error shapes between endpoints.

**Production perspective:** A stable error contract reduces support load and makes client retries safe. Include a correlation ID in every error body so a user-reported failure can be found in logs and traces instantly.

**Related concepts covered:** Bean Validation, constraint groups, ProblemDetail, status code selection, domain exceptions, correlation IDs.

## Q085. How does @Transactional work through proxies?

**Priority:** Must Know  
**Why interviewers ask it:** Proxy semantics explain the single most common "why is my transaction not working?" bug in Spring applications.

**Interview-ready answer:** `@Transactional` is implemented with AOP: Spring creates a proxy around the bean, and the proxy opens a transaction before the method and commits or rolls back after it. Because the interception happens on the way in through the proxy, an internal call from one method of the bean to another — self-invocation — goes directly to the target object and is never intercepted, so the annotation is silently ignored. The same applies to private, static or final methods, since the proxy cannot intercept them. The fixes are to move the transactional method to another bean, inject a self-reference, or use `TransactionTemplate` for explicit control. Spring Boot uses CGLIB class proxies by default, so an interface is not required.

**In-depth explanation:** The transaction itself is bound to the thread through `TransactionSynchronizationManager`, which is also how the `EntityManager` and JDBC `Connection` are shared within a boundary. That thread binding is why transactions do not propagate into `@Async` methods or new threads. Rollback rules are another frequent surprise: by default Spring rolls back on unchecked exceptions and `Error`, but commits on checked exceptions unless you declare `rollbackFor`. Ordering with other aspects matters too — `@Transactional` and `@Async` on the same method create two proxies, and the effective behaviour depends on order, which is a good reason not to combine them. Since the proxy wraps the bean, any `@PostConstruct` work executes before the transactional proxy exists.

**Practical backend example:** The self-invocation trap and two correct alternatives:

```java
@Service
public class ImportService {
    private final RowRepository rows;
    private final TransactionTemplate tx;            // explicit, no proxy involved

    public void importAll(List<Row> batch) {
        for (Row row : batch) {
            saveRow(row);                            // BROKEN: self-call bypasses the proxy
        }
        for (Row row : batch) {
            tx.executeWithoutResult(status -> rows.save(row));  // WORKS: explicit boundary
        }
    }

    @Transactional
    public void saveRow(Row row) { rows.save(row); } // only transactional when called from outside
}
```

**Common follow-ups:**
- Why does self-invocation bypass the transaction? The call never leaves the target object, so the proxy has no chance to intercept it.
- Do private methods work? No; CGLIB proxies cannot advise private, static or final methods.
- How do you verify a boundary exists? `TransactionSynchronizationManager.isActualTransactionActive()` in a test, or enable transaction debug logging.
- Are checked exceptions rolled back? Not by default; declare `@Transactional(rollbackFor = Exception.class)` if you need that.

**Mistakes to avoid:** Annotating a private method; wrapping an entire request in one long transaction; calling a transactional method from the same class; assuming a transaction spans threads.

**Production perspective:** A missing transaction boundary appears as partially applied writes — an order saved without its lines, or an event published without the row it describes. These bugs survive testing because they only manifest when a later step fails.

**Related concepts covered:** AOP proxies, transaction synchronisation, rollback rules, TransactionTemplate, async and transaction interaction.

## Q086. What do propagation modes REQUIRED and REQUIRES_NEW actually do?

**Priority:** Must Know  
**Why interviewers ask it:** Propagation determines what survives a failure, and REQUIRES_NEW has operational consequences people miss.

**Interview-ready answer:** `REQUIRED`, the default, joins an existing transaction if one is active and starts a new one otherwise; everything commits or rolls back together. `REQUIRES_NEW` suspends the current transaction and starts a genuinely independent one with its own database connection, so it can commit even if the outer transaction later rolls back — useful for audit records or failure logging that must survive. The catch is that it borrows a second connection from the pool while the first is held, so nesting it under load can exhaust the pool and deadlock. `NESTED` uses savepoints within one transaction, allowing partial rollback, and is supported only by some JDBC drivers and platforms. `MANDATORY`, `SUPPORTS`, `NOT_SUPPORTED` and `NEVER` express the remaining combinations.

**In-depth explanation:** An important consequence of joining in `REQUIRED` mode is that an inner failure marks the whole transaction rollback-only, so even if the caller catches the exception the commit fails with `UnexpectedRollbackException` — this confuses teams who expect a caught exception to be recoverable. `REQUIRES_NEW` avoids that but introduces a visibility subtlety: the inner transaction cannot see uncommitted changes from the outer one, so passing entity IDs created but not yet flushed will fail. The pool interaction is the practical risk: with a pool of 10 connections, ten concurrent requests each holding an outer transaction and opening an inner one will deadlock waiting for connections. Keep the inner transaction short, and size the pool with nesting in mind.

**Practical backend example:** Audit that must persist even when the business transaction fails:

```java
@Service
public class PaymentService {
    @Transactional                                            // REQUIRED (default)
    public void charge(Order order) {
        auditService.record(order.id(), "CHARGE_ATTEMPTED");  // committed independently
        gateway.capture(order.total());                       // may throw -> outer rolls back
        order.markPaid();
    }
}

@Service
public class AuditService {
    @Transactional(propagation = Propagation.REQUIRES_NEW)    // own connection, own commit
    public void record(UUID orderId, String event) {
        auditRepository.save(new AuditRow(orderId, event, Instant.now()));
    }
}
```

**Common follow-ups:**
- Does `REQUIRES_NEW` share the same transaction? No; it suspends the outer one and uses a separate connection and commit.
- What is `UnexpectedRollbackException`? The outer transaction was marked rollback-only by an inner failure, so the commit could not proceed.
- When would you use `NESTED`? For partial rollback via savepoints within a single transaction, where the platform supports it.
- Can the inner transaction see the outer one's uncommitted rows? No, which can cause foreign key failures if you pass unflushed IDs.

**Mistakes to avoid:** Using `REQUIRES_NEW` casually inside loops; assuming catching an exception inside a joined transaction makes it recoverable; ignoring connection pool sizing when nesting transactions.

**Production perspective:** Connection pool exhaustion caused by nested transactions is a classic incident: requests hang, HikariCP logs timeouts, and CPU is idle. If audit or outbox writes must survive failures, consider the transactional outbox pattern instead of nested transactions.

**Related concepts covered:** Transaction propagation, savepoints, connection pool sizing, rollback-only marking, outbox pattern.

## Q087. What determines transaction rollback and isolation in Spring?

**Priority:** Must Know  
**Why interviewers ask it:** Default rollback behaviour surprises people, and isolation choices affect both correctness and throughput.

**Interview-ready answer:** By default Spring rolls back on `RuntimeException` and `Error` and commits on checked exceptions; you change that with `rollbackFor` and `noRollbackFor`. Once any participant marks the transaction rollback-only, the commit cannot succeed. Isolation is delegated to the database: `@Transactional(isolation = ...)` sets the level for that transaction, and PostgreSQL's default is READ COMMITTED, which prevents dirty reads but allows non-repeatable reads and phantoms. Raising the level to REPEATABLE READ or SERIALIZABLE increases consistency but also the chance of serialisation failures that the application must retry. I usually keep READ COMMITTED and enforce correctness with explicit locking, unique constraints or optimistic versioning where it matters.

**In-depth explanation:** The checked-exception default comes from EJB conventions; it is a frequent bug source in code that throws checked domain exceptions expecting a rollback. Note also that catching an exception inside the transactional method prevents the proxy from ever seeing it, so no rollback occurs at all unless you call `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()`. Isolation levels are enforced by the database engine, and their exact semantics vary between products: PostgreSQL implements REPEATABLE READ using snapshot isolation, which also prevents phantom reads, whereas the SQL standard permits them — a good example of distinguishing standard from implementation. SERIALIZABLE in PostgreSQL uses serialisable snapshot isolation and can abort transactions with SQLSTATE 40001, so retry logic is mandatory when you choose it. Isolation only applies within the database; it says nothing about external API calls.

**Practical backend example:** Explicit rollback rules and a retryable serialisable operation:

```java
@Transactional(rollbackFor = InsufficientFundsException.class)   // checked exception must roll back
public void withdraw(UUID accountId, Money amount) throws InsufficientFundsException {
    Account account = accountRepository.findById(accountId).orElseThrow();
    if (!account.canWithdraw(amount)) throw new InsufficientFundsException(accountId);
    account.debit(amount);
}

@Retryable(retryFor = CannotAcquireLockException.class, maxAttempts = 3,
           backoff = @Backoff(delay = 50, multiplier = 2.0))
@Transactional(isolation = Isolation.SERIALIZABLE)
public void reconcile(UUID ledgerId) { /* may abort with SQLSTATE 40001 and be retried */ }
```

**Common follow-ups:**
- Do checked exceptions roll back by default? No; only unchecked exceptions and errors do.
- What happens if you catch the exception inside the method? No rollback occurs unless you mark the transaction rollback-only explicitly.
- Does PostgreSQL REPEATABLE READ allow phantom reads? Its snapshot isolation prevents them, which is stronger than the SQL standard requires.
- Is SERIALIZABLE safe to use? It is correct but can abort transactions under contention, so it requires retry handling.

**Mistakes to avoid:** Assuming every exception rolls back; swallowing exceptions inside transactional methods; raising isolation globally to fix one race; expecting isolation to protect an external HTTP call.

**Production perspective:** Higher isolation shifts failures from silent data anomalies to visible serialisation errors — better, provided the application retries idempotently. Always log and meter retry counts so contention is visible before it becomes a latency problem.

**Related concepts covered:** Rollback rules, rollback-only marking, isolation levels, PostgreSQL snapshot isolation, retry strategies.

## Q088. Why can a read-only transaction still write?

**Priority:** Important  
**Why interviewers ask it:** It is a precise test of the difference between an optimisation hint and an enforced guarantee.

**Interview-ready answer:** `@Transactional(readOnly = true)` is primarily a hint. For Hibernate it sets the flush mode to manual, so the persistence context does not dirty-check or flush changes automatically, and it can avoid taking snapshots of loaded entities, which saves memory on large reads. Spring also passes the read-only flag to the JDBC connection, and whether that is enforced depends on the driver and database: PostgreSQL does honour a read-only transaction and rejects writes with an error, while some databases ignore it. So with JPA alone, an explicit `flush()` or a native query could still write; it is best treated as an optimisation and a statement of intent, not a security control.

**In-depth explanation:** The performance benefit is real for query-heavy endpoints: skipping dirty checking on thousands of loaded entities reduces CPU and memory. The semantic benefit is documentation — readers know the method is not supposed to modify state. Some setups also route read-only transactions to a read replica through a routing `DataSource`, which is where the annotation acquires real operational meaning, and where a stray write would fail outright. Note also that `readOnly` on a method that lazily initialises collections still works, since loading is not writing. If you truly need to guarantee no writes, rely on database permissions for the connection user rather than on the annotation.

**Practical backend example:** Read-only query services and replica routing:

```java
@Service
@Transactional(readOnly = true)                 // class-level default for queries
public class OrderQueryService {
    public Page<OrderSummary> search(OrderFilter filter, Pageable pageable) {
        return orderRepository.search(filter, pageable);   // no dirty checking, no flush
    }

    @Transactional                               // explicit override where writes are intended
    public void archive(UUID id) { orderRepository.archive(id); }
}
```

**Common follow-ups:**
- Does `readOnly` enforce immutability? Not by itself; it is a hint to Hibernate and the driver. PostgreSQL does reject writes in a read-only transaction, but do not rely on it as a security boundary.
- What is the actual benefit? Skipped dirty checking and flushes, lower memory for large result sets, clear intent, and the ability to route to replicas.
- Can lazy loading still work? Yes; reading associations is not a write.

**Mistakes to avoid:** Treating `readOnly` as authorisation; expecting it to speed up every query; mixing writes into a class-level read-only service without overriding it.

**Production perspective:** Combining read-only transactions with replica routing is a common scaling step, but it introduces replication lag: a read immediately after a write may not see the new row. Route flows that need read-your-writes consistency to the primary.

**Related concepts covered:** Hibernate flush modes, dirty checking cost, read replicas and replication lag, JDBC connection flags, intent documentation.

## Q089. How do Spring filters and interceptors differ?

**Priority:** Important  
**Why interviewers ask it:** Placing cross-cutting logic at the wrong layer causes security gaps and duplicated work.

**Interview-ready answer:** A `Filter` is a servlet-level component that wraps the entire request, including static resources and error dispatches, and runs before Spring MVC decides which handler applies. It can modify the request and response streams, which is why authentication, correlation IDs, compression and CORS live there. A `HandlerInterceptor` runs inside the `DispatcherServlet` and knows which handler method was selected, so it suits handler-aware concerns such as per-endpoint auditing, rate limits keyed by route, or adding model attributes. Spring Security is entirely filter-based, so authentication decisions happen before any interceptor or controller code runs.

**In-depth explanation:** Ordering is explicit: filters run in registration order (`@Order` or `FilterRegistrationBean`), and `OncePerRequestFilter` ensures a filter is not executed twice on forwards or async dispatches. Interceptors have three hooks — `preHandle`, `postHandle` and `afterCompletion` — and `postHandle` is not called when an exception is thrown, so cleanup belongs in `afterCompletion`. Exceptions thrown in filters bypass `@ControllerAdvice`, which is why security error responses need their own `AuthenticationEntryPoint` and `AccessDeniedHandler`. For simple cross-cutting behaviour on service methods, AOP aspects are a third option, and for reactive applications `WebFilter` replaces the servlet filter. Choosing the outermost layer that has enough information is a good default rule.

**Practical backend example:** A filter for correlation and an interceptor for per-endpoint metrics:

```java
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class CorrelationFilter extends OncePerRequestFilter { /* sets MDC, clears in finally */ }

@Component
public class AuditInterceptor implements HandlerInterceptor {
    @Override public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object handler) {
        if (handler instanceof HandlerMethod hm) {              // knows the target method
            MDC.put("endpoint", hm.getBeanType().getSimpleName() + "#" + hm.getMethod().getName());
        }
        return true;
    }
    @Override public void afterCompletion(HttpServletRequest req, HttpServletResponse res,
                                          Object handler, Exception ex) { MDC.remove("endpoint"); }
}
```

**Common follow-ups:**
- Where should authentication live? In the filter chain, before handler resolution — this is what Spring Security does.
- Why was `postHandle` not called? An exception was thrown; use `afterCompletion` for cleanup that must always run.
- What guarantees a filter runs once? Extending `OncePerRequestFilter`, which guards against forwards and async re-dispatch.

**Mistakes to avoid:** Implementing authorisation in an interceptor that security filters already bypassed; forgetting to clear thread-bound state; assuming `@ControllerAdvice` covers filter exceptions; reading the request body in a filter without wrapping it, which leaves nothing for the controller.

**Production perspective:** Correlation IDs set in the outermost filter make every downstream log and trace joinable. Keep filters cheap — they run for every request including health checks — and exclude actuator paths from expensive logic.

**Related concepts covered:** Servlet filter chain, OncePerRequestFilter, HandlerInterceptor hooks, Spring Security placement, request body wrapping, MDC hygiene.

## Q090. How do you avoid circular dependency and oversized services?

**Priority:** Important  
**Why interviewers ask it:** A circular dependency is usually a symptom of a design problem, and the interviewer wants the diagnosis, not the workaround.

**Interview-ready answer:** A circular dependency means two beans each need the other during construction; since Boot 2.6 that fails at startup by default. The workarounds — `@Lazy`, setter injection, or enabling circular references — hide the real issue, which is that responsibilities are tangled. My first move is to look for the shared concept: usually a third collaborator should own the common logic, or one direction should become an event rather than a direct call. The same instinct applies to oversized services: when a class has a dozen dependencies it is doing several jobs, and splitting it along use cases makes both testing and reasoning simpler.

**In-depth explanation:** Three refactoring patterns cover most cases. First, extract a shared component that both beans depend on, turning a cycle into a tree. Second, invert one direction with an interface owned by the consumer, so the dependency points the way the domain does. Third, decouple with an application event when the second action is a reaction rather than a requirement — although in-process events are synchronous by default and are not durable. For large services, splitting by use case — `PlaceOrderService`, `CancelOrderService` — keeps each class small and gives transaction boundaries a natural home. Package-by-feature rather than package-by-layer reduces the temptation to create a giant shared service in the first place.

**Practical backend example:** Breaking a cycle by extracting the shared rule:

```java
// before: OrderService -> PricingService -> OrderService  (cycle, context fails to start)

@Component                                            // extracted shared logic, no back-reference
public class DiscountPolicy {
    public Money apply(Money base, CustomerTier tier) { /* pure calculation */ }
}

@Service
public class PricingService {
    private final DiscountPolicy discountPolicy;      // depends downward only
    public PricingService(DiscountPolicy discountPolicy) { this.discountPolicy = discountPolicy; }
}

@Service
public class OrderService {
    private final PricingService pricing;             // one direction only
    public OrderService(PricingService pricing) { this.pricing = pricing; }
}
```

**Common follow-ups:**
- Does `@Lazy` solve the design problem? No; it defers resolution so startup succeeds, but the tangled responsibilities remain.
- Is an application event a good fix? Sometimes — it decouples the direction, but in-process events are synchronous and lost on crash unless you use the outbox pattern.
- How many dependencies are too many? There is no fixed number; when the class name no longer describes one job, split it.

**Mistakes to avoid:** Enabling `spring.main.allow-circular-references` as a permanent fix; creating a "CommonService" dumping ground; splitting by technical layer instead of by feature.

**Production perspective:** Large tangled services concentrate risk: every change touches the same file, merge conflicts increase, and transaction boundaries blur. Smaller use-case services make it clear what runs inside a transaction and what does not.

**Related concepts covered:** Dependency direction, extract-collaborator refactoring, application events, package-by-feature, transaction boundary clarity.

## Q091. When would you use @ConfigurationProperties instead of @Value?

**Priority:** Important  
**Why interviewers ask it:** Typed configuration is a small decision with a large effect on startup safety and maintainability.

**Interview-ready answer:** `@Value` injects a single property and is fine for one-off values, but it is stringly typed, scattered across classes, validated only when it is used, and awkward for lists or nested structures. `@ConfigurationProperties` binds a whole prefix to a typed object — records work well in Boot 3 — supports relaxed binding, `Duration` and `DataSize` conversion, nested objects, lists and maps, and can be validated with `@Validated` so a bad or missing value fails at startup rather than at the first request. I use `@ConfigurationProperties` for anything with more than one related key, and keep `@Value` for trivial single values.

**In-depth explanation:** Binding happens through `Binder`, which applies relaxed rules: `payments.api-key`, `payments.apiKey`, `PAYMENTS_APIKEY` and `PAYMENTS_API_KEY` all reach the same property. Constructor binding (used automatically for records and classes annotated with `@ConfigurationProperties` that have a single parameterised constructor) makes the object immutable. Registering the class requires either `@EnableConfigurationProperties` or `@ConfigurationPropertiesScan`. Validation uses Bean Validation annotations on the properties type; failures produce a clear startup error naming the property. A related benefit is discoverability: with the `spring-boot-configuration-processor` dependency, your properties appear in IDE auto-completion, and the actuator `configprops` endpoint documents effective values (with sanitisation for secrets).

**Practical backend example:** Grouped, validated, immutable configuration:

```java
@Validated
@ConfigurationProperties(prefix = "orders.retry")
public record RetryProperties(
        @Min(1) @Max(10) int maxAttempts,
        @NotNull Duration initialBackoff,
        @DefaultValue("2.0") double multiplier) {}
```

```yaml
orders:
  retry:
    max-attempts: 3
    initial-backoff: 250ms     # bound to Duration automatically
```

**Common follow-ups:**
- How do you handle a missing setting? Make it `@NotNull` so startup fails loudly, or give it a `@DefaultValue`.
- Does it support lists and maps? Yes, including nested objects, with indexed YAML syntax.
- How do you see effective values at runtime? The `/actuator/configprops` endpoint, which sanitises keys that look like secrets.

**Mistakes to avoid:** Sprinkling `@Value` across many classes; using `String` for durations and parsing manually; forgetting `@EnableConfigurationProperties` or `@ConfigurationPropertiesScan`; logging the whole properties object when it contains credentials.

**Production perspective:** Configuration errors caught at startup are caught by the deployment pipeline; configuration errors caught at first use become incidents. Typed, validated properties are a cheap way to shift that failure left.

**Related concepts covered:** Relaxed binding, constructor binding with records, startup validation, actuator configprops, configuration metadata.

## Q092. How do application events work, and what do they not guarantee?

**Priority:** Important  
**Why interviewers ask it:** In-process events are often mistaken for messaging, which leads to lost work after a crash.

**Interview-ready answer:** Publishing with `ApplicationEventPublisher` calls matching `@EventListener` methods synchronously on the same thread by default, inside the same transaction if one is active. That makes them useful for decoupling modules within one application, but they guarantee nothing about durability: if the process crashes after the listener starts, the work is gone, and there is no retry, no ordering across publishers and no delivery to other instances. `@TransactionalEventListener` improves correctness by deferring the listener until after commit, which prevents acting on data that later rolls back. If the side effect must survive a crash or reach another service, the event belongs in a broker with a transactional outbox, not in the application context.

**In-depth explanation:** By default `@TransactionalEventListener` runs in the `AFTER_COMMIT` phase; other phases are `BEFORE_COMMIT`, `AFTER_ROLLBACK` and `AFTER_COMPLETION`. An important subtlety is that a listener running after commit is outside the original transaction, so persisting something there needs `REQUIRES_NEW` or a new transaction — writes without one will silently do nothing in some setups. Adding `@Async` to a listener moves it to another thread, which loses transaction and request context and makes exception handling your responsibility. Exceptions in a synchronous listener propagate to the publisher and will roll back the caller's transaction, which is sometimes desirable and often surprising. Events are also invisible to tracing unless you propagate context, so cross-module debugging suffers if you overuse them.

**Practical backend example:** Sending a confirmation only after the order really committed:

```java
@Service
public class OrderService {
    private final ApplicationEventPublisher events;
    @Transactional
    public Order place(PlaceOrderCommand cmd) {
        Order order = orderRepository.save(Order.from(cmd));
        events.publishEvent(new OrderPlacedEvent(order.id()));   // published inside the transaction
        return order;
    }
}

@Component
public class ConfirmationListener {
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onPlaced(OrderPlacedEvent event) {
        mailer.sendConfirmation(event.orderId());   // never runs if the transaction rolled back
    }
}
```

**Common follow-ups:**
- Can listeners run before commit? Yes, with `TransactionPhase.BEFORE_COMMIT`, but then the work can still be rolled back.
- Are events delivered to other instances? No; they are in-process only.
- What happens if a listener throws? A synchronous listener propagates the exception to the publisher and can roll back the transaction; an async listener does not.

**Mistakes to avoid:** Treating events as reliable messaging; writing to the database in an `AFTER_COMMIT` listener without a new transaction; chaining many events until the flow is untraceable; adding `@Async` without an error handler.

**Production perspective:** Events are excellent for modular monoliths and terrible as an integration guarantee. If a business outcome depends on the side effect — a payment, an email, a downstream update — persist the intent in the same transaction and publish from an outbox relay.

**Related concepts covered:** Transaction phases, async listeners, outbox pattern, modular monolith design, tracing context.

## Q093. What are the risks of @Async in a web application?

**Priority:** Important  
**Why interviewers ask it:** `@Async` looks like free concurrency and quietly breaks context, error handling and capacity assumptions.

**Interview-ready answer:** `@Async` is proxy-based like `@Transactional`, so self-invocation does not work and the method must be public and called from another bean. The method runs on a `TaskExecutor`; if you do not define one, Boot 3 provides a `SimpleAsyncTaskExecutor`-based default that is not a bounded pool in the traditional sense, so I always configure an explicit bounded executor. Thread-bound context does not follow the call: security context, MDC, request-scoped beans and the current transaction are all absent unless propagated. Exceptions from `void` async methods disappear unless you register an `AsyncUncaughtExceptionHandler`. And fire-and-forget work is lost on shutdown or crash, so anything that must happen needs persistence first.

**In-depth explanation:** The correct mental model is that `@Async` hands work to a different thread with a different context, and everything thread-bound must be rebuilt. `DelegatingSecurityContextAsyncTaskExecutor` propagates the security context, and a `TaskDecorator` can copy MDC entries for logging continuity. Transactions do not propagate: a `@Transactional` method calling an `@Async` method will commit independently of it, and the async method needs its own boundary. Capacity is the other half — an unbounded queue behind `@Async` turns a traffic spike into heap growth, so a bounded `ThreadPoolTaskExecutor` with a sensible rejection policy is essential. Spring Boot 3.2+ can back `@Async` with virtual threads, which removes the pool-sizing question for I/O-bound work but not the context and durability issues.

**Practical backend example:** Bounded executor with context propagation:

```java
@Bean("notificationExecutor")
public ThreadPoolTaskExecutor notificationExecutor() {
    ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
    executor.setCorePoolSize(4);
    executor.setMaxPoolSize(8);
    executor.setQueueCapacity(200);                       // bounded
    executor.setThreadNamePrefix("notify-");
    executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
    executor.setTaskDecorator(new MdcTaskDecorator());    // keeps correlation IDs in logs
    executor.setWaitForTasksToCompleteOnShutdown(true);
    executor.setAwaitTerminationSeconds(20);              // drain on shutdown
    executor.initialize();
    return executor;
}

@Async("notificationExecutor")
public void sendReceipt(UUID orderId) { /* own transaction if it touches the database */ }
```

**Common follow-ups:**
- Are transactions propagated to `@Async` methods? No; the new thread has no transaction, so annotate the async method if it needs one.
- Why is my `@Async` method running synchronously? Self-invocation, a missing `@EnableAsync`, or a non-public method.
- Where do exceptions go? For `void` methods, to the `AsyncUncaughtExceptionHandler`; for future-returning methods, into the future.

**Mistakes to avoid:** Using the default executor in production; assuming the security context follows; fire-and-forget for work the user was told succeeded; unbounded queues.

**Production perspective:** Async work must still be observable: export queue depth, active threads and rejection counts, and propagate trace context so an async failure can be linked to the originating request.

**Related concepts covered:** Proxy semantics, TaskExecutor configuration, context propagation, graceful shutdown, durability of background work.

## Q094. How should scheduled tasks be designed for multiple replicas?

**Priority:** Important  
**Why interviewers ask it:** Almost every service is deployed with more than one instance, and naive `@Scheduled` jobs then run several times.

**Interview-ready answer:** `@Scheduled` runs in every instance, so with three replicas a nightly job runs three times. If the job is not idempotent that means duplicate emails, duplicate charges or conflicting updates. The options are to make the work idempotent and let duplicates be harmless, to use a distributed lock such as ShedLock backed by the database or Redis, to elect a leader, or to move the schedule outside the application into a Kubernetes CronJob or a scheduler service. I also remember that Spring's default `TaskScheduler` is single-threaded, so one long job delays the others, and that `fixedDelay` measures from the end of the previous run while `fixedRate` measures from the start and can overlap.

**In-depth explanation:** Idempotency is the strongest design: claim work with an atomic `UPDATE ... WHERE status = 'PENDING'` so exactly one instance takes each row, rather than relying on who runs the schedule. Distributed locks must handle the crash case with a lock TTL, otherwise an instance dying mid-job blocks the schedule; ShedLock's `lockAtMostFor` exists for this. Time zones matter for cron expressions — `@Scheduled(cron = "0 0 3 * * *", zone = "UTC")` avoids daylight-saving surprises. Long-running jobs also need to interact correctly with shutdown: mark them as interruptible and let the graceful shutdown drain them, or they will be killed mid-write. Finally, jobs need observability: a last-success timestamp metric and an alert on staleness catch a silently dead schedule far faster than log inspection.

**Practical backend example:** Database-claimed work plus a distributed lock:

```java
@Scheduled(cron = "0 */5 * * * *", zone = "UTC")
@SchedulerLock(name = "settlementJob", lockAtMostFor = "10m", lockAtLeastFor = "1m") // ShedLock
public void settleBatch() {
    settlementService.settleClaimedBatch();
}
```

```sql
-- atomic claim: only one instance can take each row, even without a lock library
UPDATE settlement
SET status = 'PROCESSING', claimed_by = :instanceId, claimed_at = now()
WHERE id IN (SELECT id FROM settlement WHERE status = 'PENDING'
             ORDER BY created_at LIMIT 100 FOR UPDATE SKIP LOCKED)
RETURNING id;
```

**Common follow-ups:**
- Can two pods run the same job? Yes, by default; use a distributed lock, leader election, or an external scheduler.
- What is the difference between `fixedRate` and `fixedDelay`? `fixedRate` starts runs on a fixed interval and can overlap; `fixedDelay` waits a fixed gap after the previous run finishes.
- Why did my scheduled task stop? An uncaught exception in a `scheduleAtFixedRate`-style task cancels future runs; catch inside the task.
- Is the default scheduler multi-threaded? No; configure a `ThreadPoolTaskScheduler` when jobs can overlap.

**Mistakes to avoid:** Assuming a single instance; using `SELECT ... FOR UPDATE` without `SKIP LOCKED` and serialising all workers; cron expressions in local time; jobs with no metrics.

**Production perspective:** `FOR UPDATE SKIP LOCKED` is a robust, dependency-free way to distribute work across replicas in PostgreSQL. Whatever mechanism you choose, expose a "last successful run" gauge and alert on it — silent schedule failure is common and expensive.

**Related concepts covered:** Distributed locking, idempotent jobs, SKIP LOCKED work queues, cron time zones, scheduler thread pools, job observability.

## Q095. How does Spring Security's filter chain fit into a request?

**Priority:** Must Know  
**Why interviewers ask it:** Understanding where authentication happens explains error handling, testing and most configuration mistakes.

**Interview-ready answer:** Spring Security installs a single servlet filter that delegates to an ordered chain of security filters. Each request passes through filters that extract credentials — a session cookie, a bearer token, HTTP Basic — authenticate them, and populate the `SecurityContextHolder`. Later filters perform authorisation based on the configured rules, and only then does the request reach the `DispatcherServlet` and your controller. Because all of this happens before MVC, authentication failures are handled by the `AuthenticationEntryPoint` and authorisation failures by the `AccessDeniedHandler`, not by `@ControllerAdvice`. In Spring Security 6 configuration is a `SecurityFilterChain` bean using the lambda DSL; `WebSecurityConfigurerAdapter` no longer exists.

**In-depth explanation:** Notable filters in order include `SecurityContextHolderFilter` (restores an existing context), `CsrfFilter`, authentication filters such as `UsernamePasswordAuthenticationFilter` or `BearerTokenAuthenticationFilter`, `ExceptionTranslationFilter` (converts security exceptions into responses or redirects), and `AuthorizationFilter` (applies `authorizeHttpRequests` rules) last. Method security with `@PreAuthorize` is a separate AOP mechanism applied at the service layer and requires `@EnableMethodSecurity`. The `SecurityContext` is stored in a `ThreadLocal`, so it does not propagate to async threads without a delegating executor. For stateless APIs you disable session creation and CSRF protection is generally unnecessary for token-authenticated endpoints, but that decision must be deliberate rather than copied from a tutorial.

**Practical backend example:** A stateless resource server configuration:

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity                                   // enables @PreAuthorize
public class SecurityConfig {
    @Bean
    SecurityFilterChain api(HttpSecurity http) throws Exception {
        return http
            .securityMatcher("/api/**")
            .csrf(csrf -> csrf.disable())                              // stateless bearer-token API
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(HttpMethod.GET, "/api/public/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .oauth2ResourceServer(oauth -> oauth.jwt(Customizer.withDefaults()))
            .build();
    }
}
```

**Common follow-ups:**
- Where is the `SecurityContext` populated? In an authentication filter, before the dispatcher servlet runs.
- Why doesn't my `@ControllerAdvice` catch a 401? Because the failure happened in the filter chain, before MVC; configure an `AuthenticationEntryPoint`.
- How do you secure service methods as well? `@EnableMethodSecurity` plus `@PreAuthorize`, which applies AOP at the service layer.

**Mistakes to avoid:** Disabling CSRF without understanding whether cookies authenticate the request; relying only on URL rules while ignoring object-level ownership checks; assuming the security context is available in async threads.

**Production perspective:** Order and matchers are easy to get subtly wrong, so integration tests that assert 401, 403 and 200 for representative endpoints are worth more than reading the configuration. Log authentication failures with enough context to detect credential-stuffing patterns, but never log tokens.

**Related concepts covered:** Filter chain order, SecurityContextHolder, method security, stateless sessions, entry points and access-denied handling.

## Q096. How do you test a Spring MVC controller slice?

**Priority:** Important  
**Why interviewers ask it:** Test slicing shows whether you can get fast feedback without booting the whole application for every test.

**Interview-ready answer:** `@WebMvcTest` starts only the web layer — controllers, JSON converters, validation, exception handlers and, if configured, the security filter chain — and leaves out repositories and services, which I supply with `@MockitoBean` (Boot 3.4+; `@MockBean` in earlier versions). I drive requests with `MockMvc`, which dispatches through the real `DispatcherServlet` without a network socket, and assert status, headers and JSON. That exercises routing, binding, validation and serialisation, which unit-testing the controller class directly would skip entirely. For full-stack coverage I use `@SpringBootTest` with a random port and a Testcontainers database, but sparingly because it is much slower.

**In-depth explanation:** Slices work by limiting component scanning to relevant annotations, so a `@Service` will not be loaded and must be mocked. Security is included in `@WebMvcTest` when Spring Security is on the classpath, which means unauthenticated requests return 401 unless you annotate with `@WithMockUser` or configure test security — surprising if you expected 200. `MockMvc` does not run the servlet container, so container-specific behaviour such as compression or real HTTP semantics is not covered; `@SpringBootTest(webEnvironment = RANDOM_PORT)` with `TestRestClient`/`TestRestTemplate` does. JSON assertions with JSONPath keep tests focused on the contract rather than on object equality. Remember to test the failure paths — validation errors, not-found handling and authorisation — because those are the parts clients hit when something goes wrong.

**Practical backend example:** A focused controller test including a validation failure:

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired MockMvc mvc;
    @MockitoBean OrderService orderService;                 // collaborator is mocked

    @Test
    @WithMockUser(roles = "USER")
    void returns201AndLocationOnCreate() throws Exception {
        given(orderService.place(any())).willReturn(Order.sample());
        mvc.perform(post("/api/orders").contentType(MediaType.APPLICATION_JSON)
                        .content("""
                            {"customerId":"3f1e...","lines":[{"sku":"ABC-000001","quantity":2}]}"""))
           .andExpect(status().isCreated())
           .andExpect(header().exists("Location"))
           .andExpect(jsonPath("$.status").value("NEW"));
    }

    @Test
    @WithMockUser
    void returns400WhenQuantityIsNotPositive() throws Exception {
        mvc.perform(post("/api/orders").contentType(MediaType.APPLICATION_JSON)
                        .content("""
                            {"customerId":"3f1e...","lines":[{"sku":"ABC-000001","quantity":0}]}"""))
           .andExpect(status().isBadRequest())
           .andExpect(jsonPath("$.errors").exists());
    }
}
```

**Common follow-ups:**
- Which beans are loaded by `@WebMvcTest`? Web-layer components only — controllers, advice, converters, filters and security; services and repositories are excluded.
- Why do my tests get 401? Spring Security is active in the slice; add `@WithMockUser` or configure test security explicitly.
- When do you use `@SpringBootTest` instead? For end-to-end behaviour across layers, real HTTP, or database integration with Testcontainers.

**Mistakes to avoid:** Calling controller methods directly and claiming to have tested the endpoint; mocking `MockMvc`; loading the full context for every test and slowing the build; asserting only the happy path.

**Production perspective:** Fast slice tests keep pull-request feedback short, which materially improves how often people run the suite. Keep a small number of full end-to-end tests for the critical flows and rely on slices for breadth.

**Related concepts covered:** Test slices, MockMvc, mocking collaborators, security in tests, JSONPath assertions, test pyramid.

## Q097. What happens on application startup and how do you debug failure?

**Priority:** Important  
**Why interviewers ask it:** Startup failures block deployments, and a structured diagnosis beats trial and error.

**Interview-ready answer:** `SpringApplication.run` creates the environment (loading properties and profiles), creates the application context, applies auto-configuration, instantiates and wires singletons, performs `@ConfigurationProperties` binding and validation, starts the web server, and finally publishes `ApplicationReadyEvent` and runs any runners. Failures cluster into a few families: a missing or ambiguous bean, a property binding or validation error, a port already in use, a failing external connection such as the database, and a classpath or version conflict. Boot's failure analysers usually print a clear description and action; if not, I run with `--debug` for the condition report, check `mvn dependency:tree` for conflicts, and read the first exception in the chain rather than the last.

**In-depth explanation:** Reading the stack trace from the bottom up is usually the fastest route, because the root cause — for example `NoSuchMethodError` from a version clash — sits deepest. Bean definition overriding is disabled by default in Boot, so two beans with the same name fail rather than silently replacing each other. Slow startup is a related concern: eager database connections, large component scans and heavy `@PostConstruct` work all add seconds; `spring.jmx.enabled=false`, lazy initialisation for development, and deferring warm-up to `ApplicationReadyEvent` help. In Kubernetes, startup problems interact with probes: use a startup probe or a generous `initialDelaySeconds` so a slow boot is not mistaken for a crash loop.

**Practical backend example:** A systematic triage sequence:

```bash
java -jar app.jar --debug 2>&1 | head -80        # condition evaluation report
mvn dependency:tree -Dincludes=com.fasterxml.jackson.core   # version conflicts
curl localhost:8080/actuator/health | jq          # which component is down
curl localhost:8080/actuator/beans  | jq 'keys'   # what actually got registered
```

```text
Typical messages and their meaning
  Parameter 0 of constructor ... required a bean of type X   -> not scanned, or condition excluded it
  Failed to bind properties under 'payments'                 -> type mismatch or missing value
  Web server failed to start. Port 8080 was already in use   -> port conflict
  NoSuchMethodError / NoClassDefFoundError                   -> dependency version clash
```

**Common follow-ups:**
- Where do you find condition reports? `--debug` output at startup or `/actuator/conditions` at runtime.
- What causes a bean definition conflict? Two definitions with the same name; overriding is disabled by default in Boot.
- How do you speed up startup? Trim component scanning, avoid eager remote calls, and move warm-up to `ApplicationReadyEvent`.

**Mistakes to avoid:** Reading only the last line of the stack trace; enabling bean overriding to silence a conflict; adding dependencies to fix a `NoClassDefFoundError` without resolving the version clash; heavy work in `@PostConstruct`.

**Production perspective:** Startup time affects rollout speed and autoscaling responsiveness. Track it as a metric, and ensure health and readiness endpoints distinguish "still starting" from "broken", so orchestrators wait instead of restarting.

**Related concepts covered:** Context refresh phases, failure analysers, condition reports, dependency conflicts, startup probes, actuator endpoints.

## Q098. How do you troubleshoot a bean not found or ambiguous bean?

**Priority:** Important  
**Why interviewers ask it:** It is an everyday Spring problem with a small set of causes, and a methodical answer shows practical experience.

**Interview-ready answer:** "No qualifying bean of type X" has three usual causes: the class is not in a scanned package, it lacks a stereotype annotation or `@Bean` method, or a conditional annotation excluded it — for example a missing property or an absent class. "Expected single matching bean but found 2" means several candidates exist, which I resolve with `@Primary` for a sensible default or `@Qualifier` at the injection point. Injecting `List<T>` or `Map<String, T>` is often better when all implementations are genuinely needed, such as a set of validators. I confirm the actual state with `/actuator/beans` and the condition report rather than guessing.

**In-depth explanation:** Conditional exclusion is the most confusing case, because nothing is wrong with your code: a bean guarded by `@ConditionalOnProperty` silently disappears when the property is absent in one environment. The condition report shows that as a negative match with the reason. Qualifiers can be by name, by a custom qualifier annotation, or by the parameter name, since Spring falls back to matching the bean name against the parameter name — which is why renaming a parameter can break wiring in unexpected ways. `ObjectProvider<T>` handles optional dependencies without failing startup, and `@Autowired(required = false)` is the older equivalent. For collections, ordering with `@Order` or `Ordered` is defined and useful when the sequence matters, such as a chain of validators.

**Practical backend example:** Multiple implementations selected cleanly:

```java
public interface PaymentGateway { boolean supports(PaymentMethod method); Receipt capture(Order o); }

@Component class CardGateway implements PaymentGateway { /* ... */ }
@Component class WalletGateway implements PaymentGateway { /* ... */ }

@Service
public class PaymentRouter {
    private final List<PaymentGateway> gateways;          // inject all implementations
    public PaymentRouter(List<PaymentGateway> gateways) { this.gateways = gateways; }

    public Receipt pay(Order order, PaymentMethod method) {
        return gateways.stream().filter(g -> g.supports(method)).findFirst()
                .orElseThrow(() -> new UnsupportedPaymentMethodException(method))
                .capture(order);
    }
}
```

**Common follow-ups:**
- When should you use `@Primary`? When one implementation is the sensible default and the others are rare overrides.
- How do you make a dependency optional? `ObjectProvider<T>`, `Optional<T>` injection, or `@Autowired(required = false)`.
- Why did the bean disappear in one environment? A `@ConditionalOnProperty` or `@Profile` guard; check the condition report.

**Mistakes to avoid:** Adding `@Primary` to several beans; using field injection so the failure appears later; marking everything `@Component` including value objects; ignoring the actionable text Boot prints under "Action".

**Production perspective:** Environment-specific wiring bugs are best caught by a smoke test that starts the context with the production profile in CI. A context-loads test is cheap and catches an entire class of deployment failures.

**Related concepts covered:** Qualifiers and primary beans, conditional beans, collection injection, ObjectProvider, actuator beans endpoint.

## Q099. How do you configure database connections and pool limits?

**Priority:** Must Know  
**Why interviewers ask it:** The connection pool is usually the real capacity limit of a Spring service, and its defaults are frequently wrong.

**Interview-ready answer:** Spring Boot uses HikariCP by default. The settings that matter are `maximum-pool-size` (total connections this instance may hold), `connection-timeout` (how long a thread waits for a connection before failing, default 30 seconds), `max-lifetime` (recycle connections before the database or a proxy drops them), `idle-timeout` and `leak-detection-threshold`. Sizing is a whole-system decision: replicas times pool size must stay below the database's `max_connections`, leaving headroom for migrations and admin sessions. Bigger is not better — a pool larger than the database can serve just moves queueing into the database. When the pool is exhausted, requests block until the timeout and then fail with a Hikari timeout exception, which in traces looks like a slow endpoint with idle CPU.

**In-depth explanation:** Connection hold time is what determines the required pool size: a transaction that also makes an HTTP call holds its connection for the duration of that call, which is why external calls should never sit inside a transaction. `leak-detection-threshold` logs a stack trace when a connection is held longer than the configured time, which is the fastest way to find the offending code path. For PostgreSQL, connections are relatively expensive, so a connection pooler such as PgBouncer is common at scale; note that transaction-level pooling in PgBouncer is incompatible with session-level features such as prepared statement caching unless configured carefully. Long idle transactions are especially harmful in PostgreSQL because they hold back vacuum and cause table bloat; monitor `idle in transaction` sessions.

**Practical backend example:** A deliberate pool configuration with diagnostics:

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 10          # 10 x replicas must stay under max_connections
      minimum-idle: 10               # avoid latency spikes from pool growth
      connection-timeout: 3000       # fail fast rather than queue for 30s
      max-lifetime: 1500000          # 25 min, below the database/proxy idle cut-off
      leak-detection-threshold: 20000
      pool-name: orders-pool
  jpa:
    properties:
      hibernate.jdbc.batch_size: 50
```

```sql
-- what to check during an incident
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;
SELECT pid, now() - xact_start AS age, query FROM pg_stat_activity
WHERE state = 'idle in transaction' ORDER BY age DESC LIMIT 10;
```

**Common follow-ups:**
- What happens when all connections are borrowed? New requests wait up to `connection-timeout` and then fail; latency rises while CPU stays low.
- Should the pool be large? Only as large as the database can serve concurrently; oversizing shifts contention into the database.
- How do you find a connection leak? Enable `leak-detection-threshold` and read the logged stack traces.

**Mistakes to avoid:** Leaving the default 30-second connection timeout on a user-facing API; calling external services inside a transaction; ignoring `max_connections` when scaling replicas; sizing the pool by guesswork rather than from hold time and throughput.

**Production perspective:** Export Hikari metrics — active, idle, pending threads and timeout count. Pending threads above zero is the earliest signal of saturation and usually precedes user-visible errors by minutes.

**Related concepts covered:** HikariCP settings, connection hold time, PgBouncer, idle-in-transaction bloat, pool metrics, capacity planning.

## Q100. What causes slow Spring endpoints besides slow Java code?

**Priority:** Must Know  
**Why interviewers ask it:** Most latency in a backend service is not in the Java logic, and knowing where to look first is the skill being tested.

**Interview-ready answer:** In my experience the usual suspects, in order, are database work (too many queries, especially N+1, missing indexes, or large result sets), waiting on the connection pool, downstream HTTP calls without proper timeouts, serialisation of oversized payloads, GC pauses from memory pressure, and excessive logging. I start with a distributed trace for a slow request, which attributes time to spans, then look at the SQL count and duration for that endpoint, then the pool and GC metrics. Only after that do I profile Java code. Fixing the wrong layer is expensive: adding instances to a database-bound service makes the database slower, not the endpoint faster.

**In-depth explanation:** A trace usually narrows the problem in seconds: a single 900 ms span on a downstream call is a different problem from 300 spans of 3 ms each, which is N+1. Hibernate statistics or a query-count assertion in tests catch N+1 before production. Serialisation cost grows with payload size and is often invisible — returning an entity graph with lazy collections can trigger extra queries during JSON writing. Response compression, pagination and DTO projections address that. Thread pool saturation shows as queueing delay rather than processing time, which is why it is easy to miss without pool metrics. Finally, logging at debug level in production, or logging whole request bodies, can consume more CPU than the business logic.

**Practical backend example:** Measuring before optimising:

```java
@Bean
ObservationRegistryCustomizer<ObservationRegistry> observationConfig() {
    return registry -> registry.observationConfig()
            .observationHandler(new DefaultTracingObservationHandler(tracer));  // spans per request
}
```

```properties
# development-time visibility into SQL volume (never enable verbose SQL logging in production)
spring.jpa.properties.hibernate.generate_statistics=true
logging.level.org.hibernate.stat=DEBUG
management.endpoints.web.exposure.include=health,metrics,prometheus
```

**Common follow-ups:**
- How do traces narrow it down? Each span shows where wall-clock time went — database, downstream call, or application code.
- What is the fastest check for N+1? Query count per request from Hibernate statistics, or a test that asserts the number of statements.
- Why is CPU low while latency is high? The service is waiting — on the database, a downstream service, or a pool.

**Mistakes to avoid:** Profiling Java code before checking I/O; enabling `show-sql` in production; scaling out a database-bound service; drawing conclusions from average latency instead of percentiles.

**Production perspective:** Alert on p95/p99 latency per endpoint rather than averages, and record SQL query counts per request in a development or staging profile. Most serious regressions announce themselves as a change in query count or payload size.

**Related concepts covered:** Distributed tracing, N+1 detection, pool saturation, payload size, GC pauses, latency percentiles.

## Q101. How do you handle validation of business rules versus DTO shape?

**Priority:** Important  
**Why interviewers ask it:** Confusing input validation with domain invariants leads to rules that can be bypassed.

**Interview-ready answer:** DTO validation checks the shape of the request — required fields, formats, ranges, sizes — and belongs at the controller boundary with Bean Validation, returning 400. Business rules depend on state the request cannot see: does this customer have credit, is the SKU in stock, is the order in a cancellable status. Those belong in the domain or service layer, execute inside the transaction that will act on them, and typically return 409 or 422. The distinction matters because the same service can be called from a message consumer or a scheduled job where no controller validation ran — so the invariant must be enforced where the state change happens, not only at the edge.

**In-depth explanation:** The strongest form is to make invalid states unrepresentable: value objects that validate in their constructor, an `Order` that only exposes legal transitions, and database constraints as the last line of defence. Note that even a service-layer check is advisory under concurrency — two requests can both see stock available. Genuine enforcement requires a database constraint, a conditional update (`UPDATE ... WHERE quantity >= :n`) or a lock. Keep error signalling consistent: domain exceptions that the advice layer maps to status codes, rather than returning booleans that callers forget to check. Also avoid duplicating rules in the DTO and the domain; the DTO checks format, the domain checks meaning.

**Practical backend example:** Three layers of defence for the same rule:

```java
public record ReserveStockRequest(@NotBlank String sku, @Positive int quantity) {}   // shape

@Transactional
public void reserve(String sku, int quantity) {
    int updated = inventoryRepository.reserveIfAvailable(sku, quantity);             // meaning
    if (updated == 0) throw new InsufficientStockException(sku, quantity);           // -> 409
}
```

```sql
-- conditional update: the database enforces the invariant atomically
UPDATE inventory SET reserved = reserved + :qty
WHERE sku = :sku AND available - reserved >= :qty;
-- plus a constraint as the final guarantee
ALTER TABLE inventory ADD CONSTRAINT reserved_not_negative CHECK (reserved >= 0);
```

**Common follow-ups:**
- Can `@Valid` replace service validation? No; it cannot see database state, and non-HTTP entry points skip it entirely.
- Which status code for a broken business rule? 409 for a state conflict, 422 for semantically invalid content; be consistent across the API.
- Where do cross-field checks go? Simple ones can be custom class-level constraints; anything needing stored state belongs in the service.

**Mistakes to avoid:** Trusting controller validation as the only guard; duplicating the same rule in three layers with different messages; returning 500 for rule violations; checking availability without an atomic update.

**Production perspective:** Rules enforced only in application code fail under concurrency and during data migrations. A database constraint is the cheapest guarantee you will ever write, and it protects against bugs in code paths you have not thought about.

**Related concepts covered:** Bean Validation, domain invariants, conditional updates, database constraints, HTTP status semantics.

## Q102. What is the difference between @Controller and @RestController?

**Priority:** Important  
**Why interviewers ask it:** It is a quick check of precision about response handling and content negotiation.

**Interview-ready answer:** `@Controller` is the general MVC stereotype: a handler method's return value is interpreted as a view name unless the method or class is annotated with `@ResponseBody`. `@RestController` is simply `@Controller` plus `@ResponseBody` at the class level, so every return value is serialised into the response body — JSON by default with Jackson on the classpath. `ResponseEntity` adds explicit control over the status code, headers and body, which is what I use whenever a method returns anything other than a plain 200, such as 201 with a `Location` header or 204 with no content.

**In-depth explanation:** The mechanism is the return-value handler: with `@ResponseBody`, the `HttpMessageConverter` chain selects a converter based on the return type and the client's `Accept` header, producing 406 if nothing matches. Without it, a `ViewResolver` maps the returned string to a template. Mixing both is legitimate in applications that serve server-rendered pages and JSON APIs; use separate controllers to keep it clear. `ResponseEntity<Void>` covers 204 responses, and `ResponseEntity.created(uri)` is the standard way to answer a successful POST. Spring also honours `@ResponseStatus` on exceptions and on handler methods, which is a lighter alternative when the status is always the same.

**Practical backend example:** Explicit status and headers where they matter:

```java
@RestController
@RequestMapping("/api/invoices")
public class InvoiceController {

    @PostMapping                                        // 201 + Location for creation
    public ResponseEntity<InvoiceResponse> create(@Valid @RequestBody CreateInvoice body) {
        Invoice invoice = invoiceService.create(body.toCommand());
        return ResponseEntity.created(URI.create("/api/invoices/" + invoice.id()))
                             .body(InvoiceResponse.from(invoice));
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)              // 204, no body
    public void delete(@PathVariable UUID id) { invoiceService.delete(id); }

    @GetMapping(value = "/{id}/pdf", produces = MediaType.APPLICATION_PDF_VALUE)
    public ResponseEntity<Resource> pdf(@PathVariable UUID id) {
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"invoice.pdf\"")
                .body(invoiceService.renderPdf(id));
    }
}
```

**Common follow-ups:**
- What does `ResponseEntity` add? Full control of status, headers and body, including conditional responses and cache headers.
- Can one application mix both stereotypes? Yes; keep view controllers and API controllers separate for clarity.
- What produces a 406? Content negotiation failed — no converter can satisfy the `Accept` header.

**Mistakes to avoid:** Returning 200 for every outcome; forgetting the `Location` header on creation; annotating a `@Controller` method with `@ResponseBody` inconsistently across a class; hard-coding `produces` values that conflict with the actual payload.

**Production perspective:** Correct status codes are part of the API contract and drive client retry behaviour, caching and monitoring dashboards. A service that returns 200 with an error body defeats every generic alerting rule built on HTTP status.

**Related concepts covered:** HttpMessageConverter, content negotiation, ResponseEntity, @ResponseStatus, REST status semantics.

## Q103. How do you implement graceful shutdown for a Boot service?

**Priority:** Important  
**Why interviewers ask it:** Rolling deployments happen constantly, and ungraceful shutdown silently drops in-flight work.

**Interview-ready answer:** I enable `server.shutdown=graceful` and set `spring.lifecycle.timeout-per-shutdown-phase`, so on SIGTERM the web server stops accepting new connections and waits for in-flight requests to finish before the context closes. In Kubernetes I pair that with a readiness probe that fails immediately on shutdown, so the pod is removed from the load balancer before the server stops accepting, and with a `terminationGracePeriodSeconds` longer than the shutdown timeout. Background components need the same care: executors must be configured to wait for tasks, message consumers must stop polling and finish or re-deliver the current message, and scheduled jobs should be interruptible. Work that must not be lost has to be persisted, not held in memory.

**In-depth explanation:** The ordering problem is subtle: SIGTERM and endpoint removal happen concurrently, so a pod can receive new requests for a short period after it starts shutting down. Spring Boot's availability state support (`AvailabilityChangeEvent`, `/actuator/health/readiness`) plus a small `preStop` sleep gives the load balancer time to notice. Kafka consumers should be allowed to finish processing the current records and commit offsets; an abrupt stop means those records are re-delivered, which is only safe if the consumer is idempotent. Executors configured with `setWaitForTasksToCompleteOnShutdown(true)` and an `awaitTerminationSeconds` participate in the same lifecycle. If the process exceeds the grace period the orchestrator sends SIGKILL, so the sum of your timeouts must be smaller than the grace period.

**Practical backend example:** Coordinated shutdown configuration:

```yaml
server:
  shutdown: graceful
spring:
  lifecycle:
    timeout-per-shutdown-phase: 25s
management:
  endpoint:
    health:
      probes:
        enabled: true          # /actuator/health/liveness and /readiness
```

```yaml
# Kubernetes side
terminationGracePeriodSeconds: 40          # > 25s shutdown phase + preStop
lifecycle:
  preStop:
    exec: { command: ["sh", "-c", "sleep 5"] }   # let endpoints propagate first
readinessProbe:
  httpGet: { path: /actuator/health/readiness, port: 8080 }
```

**Common follow-ups:**
- What about async consumers? Stop polling first, finish or abandon the in-flight message deliberately, and rely on idempotent processing for re-delivery.
- Why a `preStop` sleep? Endpoint removal is eventually consistent; the delay avoids receiving requests after the server stops accepting.
- What happens if shutdown exceeds the grace period? SIGKILL terminates the process immediately, losing in-flight work.

**Mistakes to avoid:** Relying on in-memory queues to drain; a grace period shorter than the shutdown timeout; ignoring background executors; assuming requests stop arriving the moment SIGTERM is received.

**Production perspective:** Graceful shutdown is what makes deployments invisible to users. Measure it: a spike in 502s or connection resets during rollouts is the signal that the shutdown sequence is misconfigured.

**Related concepts covered:** SIGTERM handling, readiness probes, executor draining, consumer rebalancing, idempotency, deployment safety.

## Q104. How would you structure a small Spring feature end to end?

**Priority:** Must Know  
**Why interviewers ask it:** It shows whether you can assemble the pieces into something maintainable rather than reciting annotations.

**Interview-ready answer:** I keep four layers with clear responsibilities. The controller handles HTTP: binding, validation of shape, status codes, and mapping to a command object — no business logic. The service owns the use case and the transaction boundary, orchestrating domain objects and repositories. The domain holds invariants and state transitions. The repository handles persistence. DTOs are separate from entities in both directions so the API contract and the schema can evolve independently. Cross-cutting concerns — error mapping, correlation IDs, security — live in advice and filters. For a feature like "cancel an order", that gives one endpoint, one service method with `@Transactional`, a domain method enforcing the state machine, and a repository call, plus tests at each level.

**In-depth explanation:** The transaction boundary belongs in the service, not the controller, because the controller is about transport and the repository is too granular. External calls should sit outside the transaction or be handled with an outbox, so a slow gateway never holds a database connection. Package by feature (`orders/`, `payments/`) rather than by layer keeps related code together and makes boundaries visible. Mapping can be manual for a handful of fields — explicit, debuggable and refactor-safe — or generated with MapStruct when the volume justifies it; reflection-based deep mappers tend to hide bugs. Idempotency deserves thought at design time for any state-changing endpoint that a client may retry.

**Practical backend example:** The full slice for one use case:

```java
// web/OrderController.java
@PostMapping("/api/orders/{id}/cancellation")
public ResponseEntity<OrderResponse> cancel(@PathVariable UUID id,
                                            @RequestHeader("Idempotency-Key") String key,
                                            @Valid @RequestBody CancelOrderRequest body) {
    Order order = orderService.cancel(new CancelOrderCommand(id, body.reason(), key));
    return ResponseEntity.ok(OrderResponse.from(order));
}

// application/OrderService.java
@Service
public class OrderService {
    @Transactional                                     // one boundary per use case
    public Order cancel(CancelOrderCommand command) {
        Order order = orders.findById(command.orderId())
                            .orElseThrow(() -> new OrderNotFoundException(command.orderId()));
        order.cancel(command.reason());                // domain enforces the state machine
        events.publishEvent(new OrderCancelledEvent(order.id()));  // after-commit listener
        return order;                                  // dirty checking flushes the update
    }
}

// domain/Order.java
public void cancel(String reason) {
    if (status != OrderStatus.PAID && status != OrderStatus.NEW) {
        throw new IllegalOrderStateException(id, status);          // invariant lives here
    }
    this.status = OrderStatus.CANCELLED;
    this.cancellationReason = reason;
}
```

**Common follow-ups:**
- Where is the transaction boundary? In the service method that represents the use case.
- Why not return entities from controllers? They leak schema details, can trigger lazy loading during serialisation, and couple the API to the database.
- Where does idempotency live? Usually a stored key with a unique constraint checked at the start of the use case.

**Mistakes to avoid:** Business logic in controllers; `@Transactional` on repository calls only; anaemic domain objects with all logic in a service and no invariants anywhere; entities as API payloads.

**Production perspective:** Clear layering pays off during incidents: you know where to add a log line, where the transaction starts, and which layer to test. It also makes it obvious when an external call has crept inside a transaction.

**Related concepts covered:** Layered architecture, transaction boundaries, DTO mapping, domain invariants, idempotency, package-by-feature.

## Q105. What should you check before upgrading a Boot 2 app to Boot 3?

**Priority:** Important  
**Why interviewers ask it:** Boot 3 is a real migration, and knowing its breaking changes shows current, practical stack knowledge.

**Interview-ready answer:** The three big items are Java 17 as the minimum, the move from `javax.*` to `jakarta.*` for servlet, persistence, validation and annotations, and third-party libraries that must be upgraded to Jakarta-compatible versions. Beyond that: Spring Security 6 removes `WebSecurityConfigurerAdapter` in favour of `SecurityFilterChain` beans and changes several defaults; Hibernate 6 changes some ID generation and type mapping behaviour; the trailing-slash URL matching default changed; actuator endpoint details and property names moved in places. My process is to upgrade to the latest Boot 2.7 first, remove deprecation warnings, run the Spring Boot migrator and OpenRewrite recipes, then move to Boot 3 with a thorough integration test suite and a staged rollout.

**In-depth explanation:** The `jakarta` namespace change is mechanical but wide: every `javax.persistence`, `javax.validation` and `javax.servlet` import changes, and any library that still ships `javax` classes must be replaced. Hibernate 6 is the subtlest part of the migration — sequence-based ID allocation defaults, `@Enumerated` handling and some SQL generation differ, so persistence tests with a real PostgreSQL through Testcontainers are worth far more than unit tests here. Security 6 requires rewriting configuration classes and `antMatchers` becomes `requestMatchers`. The trailing-slash matching change means `/orders/` no longer maps to `/orders` by default and can break existing clients. Observability also changed: Spring Boot 3 uses Micrometer Observation and Micrometer Tracing instead of Spring Cloud Sleuth.

**Practical backend example:** Typical mechanical changes:

```java
// Boot 2                                        // Boot 3
import javax.persistence.Entity;                 import jakarta.persistence.Entity;
import javax.validation.Valid;                   import jakarta.validation.Valid;
import javax.servlet.Filter;                     import jakarta.servlet.Filter;

// Security: adapter class                       // Security 6: a bean
// extends WebSecurityConfigurerAdapter          @Bean SecurityFilterChain chain(HttpSecurity http)
// http.authorizeRequests().antMatchers(...)     http.authorizeHttpRequests(a -> a.requestMatchers(...))
```

```bash
mvn -B org.openrewrite.maven:rewrite-maven-plugin:run \
  -Drewrite.activeRecipes=org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_0
```

**Common follow-ups:**
- Why do `javax` imports break? Jakarta EE renamed the namespace; Spring 6 targets `jakarta.*` exclusively.
- What usually breaks silently? Hibernate 6 mapping and ID generation differences, and trailing-slash URL matching.
- How do you de-risk the upgrade? Upgrade to the latest 2.7 first, rely on integration tests against a real database, and roll out behind a canary.

**Mistakes to avoid:** Upgrading Boot and business features in the same release; skipping the 2.7 stepping stone; trusting unit tests with mocks to catch persistence behaviour changes; forgetting third-party libraries that still target `javax`.

**Production perspective:** Plan the upgrade as its own deployment with a rollback path, and compare key metrics — latency percentiles, error rates, query counts — before and after. Framework upgrades most often show up as subtle persistence or serialisation differences rather than outright failures.

**Related concepts covered:** Jakarta namespace migration, Spring Security 6 configuration, Hibernate 6 changes, OpenRewrite automation, canary deployment, integration testing with Testcontainers.
