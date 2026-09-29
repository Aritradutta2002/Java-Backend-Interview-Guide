# Chapter 1. Core Java, OOP, exceptions, and language fundamentals

Assume Java 17 unless a question explicitly mentions Java 21. Examples omit imports when the types are unambiguous.

## Q001. How would you apply encapsulation, abstraction, inheritance and polymorphism in an order service?

**Priority:** Must Know  
**Why interviewers ask it:** They want design decisions, not four memorized definitions.

**Interview-ready answer:** I encapsulate order invariants inside an `Order` rather than letting controllers change fields directly. I expose an abstraction such as `PaymentGateway` so checkout depends on a contract, not a provider. Polymorphism lets Stripe and a test gateway implement that contract. Inheritance can model a genuine is-a relationship, but I avoid extending a base service merely to reuse code: composition is easier to change and test. The goal is to keep business rules in one place while leaving replaceable integrations behind small interfaces.

**In-depth explanation:** Encapsulation protects valid state, not just private fields: an order should reject shipping before payment. Abstraction reveals needed behavior while hiding implementation. Inheritance creates subtype substitutability obligations; an overridden method that changes expected behavior violates them. Polymorphism selects behavior through the contract at runtime. A service can inject a gateway and use a domain object without requiring either to inherit framework base classes.

**Practical backend example:** `Receipt receipt = paymentGateway.capture(order.total()); order.markPaid(receipt.id());` The domain method checks state; the gateway can be swapped without editing the order's rules. In production, coordinate the external call and database update with an idempotent workflow rather than holding a database transaction open across the call.

**Common follow-ups:**
- Where is inheritance appropriate? For a stable subtype hierarchy whose members genuinely satisfy the same contract.
- Is a private field sufficient encapsulation? No; public setters can still permit invalid transitions.

**Mistakes to avoid:** Calling every interface an abstraction while leaving all business logic in controllers; using inheritance solely for code reuse.

**Production perspective:** Small boundaries make provider migrations and targeted tests less risky, but extra interfaces for every trivial class add noise.

**Related concepts covered:** Domain invariants, dependency inversion, substitutability, test doubles.

## Q002. When would you choose an interface, abstract class or concrete class?

**Priority:** Must Know  
**Why interviewers ask it:** They are checking how you shape an extension point.

**Interview-ready answer:** I use an interface for a capability that unrelated implementations can provide, such as `PaymentGateway`. An abstract class makes sense when closely related implementations share meaningful state or a template algorithm. A concrete class is simplest when I do not need an extension point. Java interfaces can provide default behavior but cannot hold per-instance state. I do not introduce abstractions only because a class might someday have another implementation.

**In-depth explanation:** A class can implement multiple interfaces but extend one class. Interface default methods support compatible API evolution, although adding a conflicting default may require an override. An abstract class can define constructors, protected state and implemented methods; that shared state also couples subclasses. Prefer a narrow contract at a module boundary and keep implementation details concrete.

**Practical backend example:** `interface TaxCalculator { Money calculate(Order order); }` can have region-specific implementations; a single immutable `TaxRate` value object need not have its own interface.

**Common follow-ups:**
- Can an interface have fields? Only implicitly `public static final` constants, not instance fields.
- Can an abstract class implement an interface? Yes, and leave methods for subclasses.

**Mistakes to avoid:** Saying interfaces cannot have methods with bodies; treating speculative interfaces as automatic testability.

**Production perspective:** Public interfaces are contracts to maintain. Keep them cohesive and avoid exposing provider-specific details.

**Related concepts covered:** Default methods, multiple implementation, API evolution, coupling.

## Q003. Why prefer composition over inheritance in service design?

**Priority:** Must Know  
**Why interviewers ask it:** They want to see whether you can keep change localized.

**Interview-ready answer:** Composition delegates work to injected collaborators and lets me replace one behavior independently. Inheritance ties a subclass to base-class behavior and can make overrides depend on undocumented assumptions. For example, an order service should use a `FraudChecker` and a `PaymentGateway`, not inherit a broad `BaseCheckoutService` just to get two helper methods. I still use inheritance when the subtype relationship is real and substitutable.

**In-depth explanation:** An inherited method can call another overridable method, so changing the base class may change subclasses unexpectedly. Composition gives explicit dependencies and makes isolated tests straightforward. It is not a rule to split every line into an injected strategy: start with concrete code and extract boundaries when there are independent policies or external integrations.

**Practical backend example:** `CheckoutService(FraudChecker fraud, PaymentGateway payments)` makes the fraud policy and payment provider independently replaceable.

**Common follow-ups:**
- When is inheritance reasonable? Stable taxonomies or framework contracts with well-defined substitutability.
- Does composition eliminate coupling? No; it moves coupling to an explicit contract.

**Mistakes to avoid:** Equating code reuse with an is-a relationship; creating a strategy for a one-line constant.

**Production perspective:** Explicit collaborators are easier to monitor and replace during a provider migration.

**Related concepts covered:** Strategy pattern, dependency injection, Liskov substitution, testing.

## Q004. What is the equals and hashCode contract, and how can it break a HashSet?

**Priority:** Must Know  
**Why interviewers ask it:** Equality bugs are hard to spot and affect collections directly.

**Interview-ready answer:** `equals` should be reflexive, symmetric, transitive, consistent and false for null. If two objects compare equal, they must have the same `hashCode`; unequal objects may collide. A `HashSet` locates a bucket using the hash and then checks equality. If I mutate a field used by both methods after insertion, lookup and removal may fail. I prefer immutable keys and define equality based on stable domain identity or value semantics.

**In-depth explanation:** Equal hash codes do not imply equal objects. `Objects.equals` and `Objects.hash` help implement value equality, but hashing many mutable fields is dangerous. ORM entities with generated IDs need special care: two unsaved objects both have null IDs, and an ID appears after persistence. There is no single universal entity equality recipe; consider lifecycle and proxy behavior before choosing one.

**Practical backend example:** `record OrderKey(long tenantId, String externalId) {}` gives stable value equality for a deduplication set.

**Common follow-ups:**
- Must unequal objects have different hashes? No, collisions are allowed.
- What happens if only equals is overridden? Hash-based collections can retain logically duplicate keys.

**Mistakes to avoid:** Comparing string fields with `==`; using a mutable balance as a key component.

**Production perspective:** A bad equality strategy can silently corrupt cache and deduplication behavior.

**Related concepts covered:** HashMap, records, immutability, JPA identity.

## Q005. How is Comparable different from Comparator, and what must ordering agree with?

**Priority:** Important  
**Why interviewers ask it:** Sorting and sorted-set semantics expose contract mistakes.

**Interview-ready answer:** `Comparable` defines a type's natural order; a `Comparator` defines an external or alternate order. A comparator must be transitive and return zero consistently for values it treats as equivalent. `TreeSet` and `TreeMap` use the comparison result to identify keys, so if comparison returns zero for unequal values, one can disappear. For sets that should follow `equals`, I make ordering consistent with equality or choose a hash-based set.

**In-depth explanation:** Sorting can have many legitimate orders, such as date, price or priority; those usually belong in named comparators. `Comparator.comparing(...).thenComparing(...)` makes tie-breakers explicit. The Java sorting APIs require a consistent comparison contract; a comparator that changes with mutable state can produce incorrect behavior.

**Practical backend example:** `Comparator<Order> byCreated = Comparator.comparing(Order::createdAt).thenComparing(Order::id);` The ID breaks timestamp ties for stable pagination.

**Common follow-ups:**
- Does `compareTo() == 0` always imply `equals()`? Not required generally, but sorted collections behave as if it does for uniqueness.
- Why not subtract integers to compare? Subtraction can overflow; use `Integer.compare`.

**Mistakes to avoid:** Sorting only by a nonunique timestamp when stable order matters.

**Production perspective:** Deterministic ordering is necessary for reproducible results and reliable pagination.

**Related concepts covered:** TreeSet, stable sort, pagination, equality.

## Q006. Why are Strings immutable, and how do StringBuilder and the pool affect code?

**Priority:** Must Know  
**Why interviewers ask it:** Strings combine correctness, memory and performance trade-offs.

**Interview-ready answer:** A `String`'s contents cannot be changed, so it is safe to share and use as a map key. `StringBuilder` is a mutable buffer useful when appending repeatedly inside a loop; it is not thread-safe. The string pool can reuse literals and interned values, but I compare contents with `equals`, not `==`, because reference identity is not a content guarantee. Ordinary `+` concatenation is often fine for a small expression; I profile before changing it.

**In-depth explanation:** Immutability allows stable hashes and simplifies concurrency. The compiler may optimize concatenation; the real concern is repeatedly creating intermediate values in an accumulation loop. `StringBuilder` grows its internal storage and trades synchronization for speed; `StringBuffer` is synchronized but usually unnecessary with local variables. Pooling is an implementation/memory technique, not a substitute for equality.

**Practical backend example:** `StringBuilder csv = new StringBuilder(); for (String id : ids) csv.append(id).append('\n');` Use parameterized SQL rather than assembling a SQL `IN` clause from this string.

**Common follow-ups:**
- Is `StringBuilder` safe to share across requests? Not without coordination; keep it local.
- Why might `"a" == new String("a")` be false? They can be different objects with equal contents.

**Mistakes to avoid:** Using `==` for user input; treating immutability as encryption or secrecy.

**Production perspective:** Avoid building unbounded strings from large payloads; stream output when appropriate.

**Related concepts covered:** Equality, allocations, pooling, safe sharing.

## Q007. What is pass-by-value in Java, including object references?

**Priority:** Must Know  
**Why interviewers ask it:** This distinction clarifies mutation and method effects.

**Interview-ready answer:** Java always passes a copy of a value. For a primitive, that value is the number or boolean. For an object variable, it is a copy of the reference to the same object. A method can mutate that shared object if it is mutable, but assigning its parameter to a new object does not replace the caller's variable. I avoid hidden mutation and return a new value when I intend to replace data.

**In-depth explanation:** The distinction is between changing an object and reassigning a local reference. Neither means the JVM copies the object when a method is called. An immutable object's method cannot modify the instance, so APIs often return the result: `date.plusDays(1)` returns a new `LocalDate`. Aliasing is the larger design issue when multiple components retain a reference to mutable state.

**Practical backend example:** `void add(List<String> ids) { ids.add("A"); ids = new ArrayList<>(); }` The caller sees `"A"` in its list but not the new list.

**Common follow-ups:**
- Can a method change a caller's primitive variable? Not by assigning its parameter.
- Does `final` on a reference freeze its object? No; it prevents reassignment of that variable.

**Mistakes to avoid:** Saying objects are passed by reference; assuming a copied list reference is a defensive copy.

**Production perspective:** Shared mutable DTOs can create cross-request bugs; copy at ownership boundaries.

**Related concepts covered:** Aliasing, defensive copying, final, immutable values.

## Q008. How do checked and unchecked exceptions influence API design?

**Priority:** Must Know  
**Why interviewers ask it:** Good error contracts depend on recoverability.

**Interview-ready answer:** Checked exceptions must be caught or declared and can make a recoverable condition visible to callers. Unchecked exceptions are not enforced by the compiler and often represent programming errors or failures handled at a higher boundary. Neither category automatically means an error is safe to ignore. I choose an exception based on what the caller can do, preserve the cause when translating infrastructure failures, and map expected domain failures to an appropriate API response.

**In-depth explanation:** `IOException` is checked; `IllegalArgumentException` is unchecked. A service might translate a repository-specific exception into a domain-level conflict while retaining the cause for diagnostics. Avoid making every caller catch an exception if it has no meaningful local recovery. Also avoid swallowing unexpected exceptions and returning success-shaped defaults.

**Practical backend example:** `throw new OrderConflictException("Order already paid", cause);` A controller advice can map it to 409 without exposing database details.

**Common follow-ups:**
- Does Spring roll back on checked exceptions by default? No; default rollback applies to unchecked exceptions and `Error`.
- Should you catch `Exception` everywhere? No; catch where you can recover, translate or add useful context.

**Mistakes to avoid:** Losing the original cause; exposing raw stack traces to API clients.

**Production perspective:** Error taxonomy should support useful metrics and actionable logs without leaking sensitive data.

**Related concepts covered:** Spring transactions, exception translation, API errors.

## Q009. How would you design exception handling for a Spring service?

**Priority:** Must Know  
**Why interviewers ask it:** They want a consistent contract across domain and HTTP layers.

**Interview-ready answer:** A service should throw meaningful domain exceptions such as `OrderNotFound` or `OrderConflict`, rather than HTTP exceptions everywhere. At the web boundary, `@RestControllerAdvice` maps them to stable status codes and a consistent error body. Validation failures become 400 responses with safe field details; unexpected failures become 500 with a correlation ID, not a stack trace. I log unexpected failures once at the boundary and keep causes for internal diagnostics.

**In-depth explanation:** A missing resource is different from an invalid command or an optimistic-lock conflict. Translation prevents persistence details from becoming public API contracts. Spring Boot 3's `ProblemDetail` is a useful RFC 7807-style response type, but the exact schema should be documented and tested. Exception advice cannot recover after a response has already been committed.

**Practical backend example:** `@ExceptionHandler(OrderNotFound.class) ResponseEntity<ProblemDetail> missing(OrderNotFound ex) { var p = ProblemDetail.forStatus(404); p.setTitle("Order not found"); return ResponseEntity.status(404).body(p); }`

**Common follow-ups:**
- Where should errors be logged? At a boundary with request context, avoiding repeated stack traces at each layer.
- Is every validation error a 500? No, invalid client input usually needs a 4xx response.

**Mistakes to avoid:** Returning internal exception messages directly; using 200 for failed operations.

**Production perspective:** Stable machine-readable errors help clients retry or correct requests appropriately.

**Related concepts covered:** ProblemDetail, validation, observability, HTTP status codes.

## Q010. How does try-with-resources work and what happens with suppressed exceptions?

**Priority:** Important  
**Why interviewers ask it:** Resource cleanup matters even when work fails.

**Interview-ready answer:** Try-with-resources closes `AutoCloseable` resources when the block exits, including on exceptions. Resources are closed in reverse declaration order. If the body throws and closing also throws, the body exception remains primary and the closing exception is attached as suppressed. I use it for streams, files and manually managed JDBC resources; when Spring owns a connection or transaction, I let the framework manage that lifecycle.

**In-depth explanation:** The construct makes cleanup structurally hard to forget. If only closing fails, that exception propagates. Suppressed exceptions are available through `getSuppressed()` and can explain secondary failures. Ownership matters: closing a connection borrowed and managed by a framework at the wrong point can break a transaction.

**Practical backend example:** `try (InputStream in = storage.open(key)) { return in.readAllBytes(); }` For large files, stream in chunks rather than allocating the entire object.

**Common follow-ups:**
- In what order are resources closed? Reverse declaration order.
- What does `AutoCloseable.close()` allow? It may throw `Exception`; specific resource types can narrow it.

**Mistakes to avoid:** Masking failures in a `finally` block; forgetting the size of `readAllBytes()`.

**Production perspective:** Leaked file descriptors or connections can exhaust a service long before heap memory runs out.

**Related concepts covered:** JDBC lifecycle, exception suppression, resource exhaustion.

## Q011. What do final, finally and finalize mean in modern Java?

**Priority:** Important  
**Why interviewers ask it:** Similar names hide very different semantics.

**Interview-ready answer:** `final` restricts reassignment, overriding or inheritance depending on where it appears; it does not deeply freeze an object. `finally` is a block normally used for cleanup after try/catch, though try-with-resources is preferable for closeable resources. `finalize()` is legacy finalization, deprecated for removal and unsuitable for reliable cleanup. I use explicit lifecycle management rather than depending on the GC to release external resources.

**In-depth explanation:** A `final List` reference can still point to a mutable list. A `finally` block normally runs on return or throw, but should not be sold as an absolute guarantee under process termination or VM failure. Finalization timing was unspecified and introduced performance and safety problems. `Cleaner` can be a safety net for some native resources, not a substitute for closing them deliberately.

**Practical backend example:** `private final PaymentGateway gateway;` means the field cannot be reassigned after construction, but the gateway implementation may itself be mutable.

**Common follow-ups:**
- Is a final field always thread-safe? No; it can reference a non-thread-safe object.
- Should you override finalize? No, use explicit cleanup such as `AutoCloseable`.

**Mistakes to avoid:** Claiming `finally` runs literally always; using finalization to release DB connections.

**Production perspective:** Predictable cleanup avoids exhausting sockets and other native resources.

**Related concepts covered:** Immutability, resource ownership, GC.

## Q012. How do you make a class truly immutable?

**Priority:** Must Know  
**Why interviewers ask it:** Immutable objects simplify reasoning and concurrency.

**Interview-ready answer:** I prevent mutation after construction, validate invariants in the constructor, keep fields private and final where possible, and copy mutable inputs and outputs. `List.copyOf` protects a collection structure, but not mutable elements inside it. A record is only shallowly immutable for the same reason. I avoid exposing a mutable `Date` or array directly and use immutable value types such as `Instant` when possible.

**In-depth explanation:** The goal is that no caller can observe state changing through any alias. Merely omitting setters is not enough if the constructor stores the caller's mutable list or a getter returns an internal array. If subclasses can introduce mutable behavior, make the class final or strictly control inheritance. Immutable instances are easier to share safely and make reliable keys.

**Practical backend example:** `final class Batch { private final List<String> ids; Batch(List<String> ids) { this.ids = List.copyOf(ids); } List<String> ids() { return ids; } }` This assumes `String` elements are immutable.

**Common follow-ups:**
- Is `Collections.unmodifiableList(input)` a defensive copy? No, later changes to `input` remain visible.
- Does `final` recursively freeze fields? No.

**Mistakes to avoid:** Returning internal arrays; claiming records deeply copy components.

**Production perspective:** Immutability reduces synchronization needs but copying very large graphs has a memory cost.

**Related concepts covered:** Records, safe publication, value objects, defensive copies.

## Q013. When are records suitable for backend DTOs, and when are they not?

**Priority:** Important  
**Why interviewers ask it:** Records are useful, but not a universal entity replacement.

**Interview-ready answer:** A record is a concise carrier for a fixed set of values and is well suited to an immutable request/response DTO or query projection. It supplies accessors, a constructor, value-based `equals`, `hashCode` and `toString`. It does not deeply freeze mutable components, so I copy collections in a compact constructor. A typical mutable JPA entity should remain a regular class because entity lifecycle, proxies and no-arg-constructor requirements do not fit record semantics.

**In-depth explanation:** Records are final and extend `java.lang.Record`, so they cannot extend an entity base class. Validation can live in the canonical or compact constructor, though API validation is often also handled at the boundary. Beware that generated `toString` can expose sensitive fields in logs. Records represent data shapes, not a promise that every field's referent is immutable.

**Practical backend example:** `record CreateOrderRequest(List<String> productIds) { CreateOrderRequest { productIds = List.copyOf(productIds); } }`

**Common follow-ups:**
- Can a record implement an interface? Yes.
- Can you update a record field? No; create a new record instance instead.

**Mistakes to avoid:** Using a record as a managed JPA entity; logging a record containing a password.

**Production perspective:** DTO records reduce boilerplate, but review serialization compatibility before changing component names.

**Related concepts covered:** DTOs, JPA entities, shallow immutability, API contracts.

## Q014. How should Optional be used at service boundaries?

**Priority:** Must Know  
**Why interviewers ask it:** It tests whether absence is modeled intentionally.

**Interview-ready answer:** `Optional<T>` is useful as a return type when a value may legitimately be absent, such as `findById`. The caller should choose a response: `orElseThrow`, a fallback, or a 404. I do not use `get()` without checking, and I generally avoid `Optional` fields, method parameters or collection elements when an ordinary type or empty collection is clearer. I also avoid returning null from a method declared to return `Optional`.

**In-depth explanation:** `orElse` evaluates its argument eagerly; `orElseGet` evaluates the supplier only if empty. `map` transforms a present value, while `flatMap` avoids nested optionals for functions already returning `Optional`. Absence is not always an error: a lookup can return empty, while a command requiring the entity should translate absence into a domain exception.

**Practical backend example:** `Order order = repository.findById(id).orElseThrow(() -> new OrderNotFound(id));`

**Common follow-ups:**
- Should a list lookup return `Optional<List<T>>`? Usually return an empty list for no results.
- What is the difference between `orElse` and `orElseGet`? The former evaluates the fallback eagerly.

**Mistakes to avoid:** `optional.get()` after assuming presence; using Optional to suppress validation of required inputs.

**Production perspective:** Clear absence contracts prevent surprising 500s and inconsistent API responses.

**Related concepts covered:** Null handling, repository lookups, exception boundaries.

## Q015. What is the difference between overloading and overriding?

**Priority:** Important  
**Why interviewers ask it:** Method dispatch affects real behavior in hierarchies.

**Interview-ready answer:** Overloading defines methods with the same name but different parameter lists; the compiler selects among them using the declared argument types. Overriding supplies a subtype implementation of an inherited instance method; runtime dispatch uses the actual object's type. Return type alone cannot overload a method. Static methods are hidden, not overridden, and private methods are not overridden.

**In-depth explanation:** For overriding, the parameter signature remains the same, return types can be covariant, visibility cannot be narrowed and checked exceptions cannot be broadened. An overloaded method chosen at compile time does not change simply because a variable points to a subtype at runtime. The `@Override` annotation catches accidental signature mistakes.

**Practical backend example:** `Gateway g = new StripeGateway(); g.charge(order);` invokes the overridden `charge` implementation. An overload `charge(PremiumOrder)` is selected only if the compile-time argument type matches.

**Common follow-ups:**
- Can constructors be overridden? No; they are not inherited.
- Can a static method be overridden? No; same-signature subclass methods hide it.

**Mistakes to avoid:** Confusing overload selection with dynamic dispatch; omitting `@Override` on intended overrides.

**Production perspective:** Ambiguous overloads with null arguments make APIs harder to use and maintain.

**Related concepts covered:** Polymorphism, compile-time types, method signatures.

## Q016. How do access modifiers and packages shape a module's API?

**Priority:** Important  
**Why interviewers ask it:** Visibility is an architectural tool.

**Interview-ready answer:** I expose only the types and methods other modules need. `private` is class-local, package-private is available in the same package, `protected` is available in the package and to subclasses subject to access rules, and `public` is broadly accessible. I use package-private helpers where appropriate rather than making every service utility public. A public method becomes a contract that is harder to change later.

**In-depth explanation:** Packages can group implementation details around a feature. Java's module system can further constrain exports, but many Spring applications use packages without named JPMS modules. Framework proxying and reflection sometimes impose visibility constraints, so verify framework behavior instead of broadly making everything public. `protected` cross-package access is through subclass context, not arbitrary access to any parent instance.

**Practical backend example:** Keep an `OrderTotalsCalculator` package-private inside `orders` if only order services use it; expose a narrow application service to controllers.

**Common follow-ups:**
- What is the default modifier for a top-level class? Package-private.
- Is protected equivalent to public for subclasses everywhere? No; cross-package access has restrictions.

**Mistakes to avoid:** Making internals public just for tests; using packages solely as `controller/service/repository` buckets when feature boundaries help.

**Production perspective:** Smaller public surfaces reduce accidental coupling during refactoring.

**Related concepts covered:** Encapsulation, modules, Spring proxies, feature packaging.

## Q017. What happens during class loading and static initialization?

**Priority:** Important  
**Why interviewers ask it:** Startup failures can be caused by initialization side effects.

**Interview-ready answer:** A class is loaded, linked and initialized when the JVM needs it according to language rules. Static fields and static initialization blocks run during initialization in textual order after default zero initialization, with superclass initialization first. I keep static initialization simple and deterministic; external calls or configuration reads there can cause hard-to-debug startup failures. A failed initializer can surface as `ExceptionInInitializerError` and leave the class unusable for that loader.

**In-depth explanation:** Loading locates bytecode, linking verifies and prepares it, and initialization executes static initializers. Merely mentioning a type in source does not necessarily initialize it. Constants that are compile-time constants may be inlined by callers. Different classloaders can load distinct classes with the same binary name, which matters in containers and plugin systems.

**Practical backend example:** Prefer an injected `@Bean` configuration that loads a remote ruleset at a controlled startup phase over `static final Rules RULES = fetchRemoteRules();`.

**Common follow-ups:**
- Do static fields belong to each object? No, they belong to a class as defined by its classloader.
- What happens after static initialization fails? Subsequent uses can fail with `NoClassDefFoundError`.

**Mistakes to avoid:** Assuming every static final field is a compile-time constant; doing network I/O in static blocks.

**Production perspective:** Startup failures need a visible cause and a retry/deployment policy, not hidden static side effects.

**Related concepts covered:** Classloaders, Boot startup, initialization order.

## Q018. How do primitives, wrappers and autoboxing create bugs?

**Priority:** Must Know  
**Why interviewers ask it:** Small conversions can cause null errors and misleading comparisons.

**Interview-ready answer:** Primitives hold values and cannot be null; wrappers such as `Integer` are objects and can represent absence. Autoboxing converts between them, but unboxing a null wrapper throws `NullPointerException`. I compare wrapper values with `equals` or numeric comparison, not `==`, which compares object identity. In hot paths or large arrays, boxing can add allocation and memory overhead, though I measure before optimizing.

**In-depth explanation:** Some wrapper instances may be cached, which makes `==` appear to work for certain values but is not a general value-comparison strategy. Numeric promotion can also surprise: `int` arithmetic may overflow before assignment to `long`. Use `long` operands or exact arithmetic methods when overflow matters. Nullability should be intentional at API boundaries.

**Practical backend example:** `Integer count = request.count(); int safe = count == null ? 0 : count;` Better still, validate whether an absent count is allowed rather than silently defaulting.

**Common follow-ups:**
- What does `Integer x = null; int y = x;` do? Throws `NullPointerException` on unboxing.
- Is `Integer.valueOf(1000) == Integer.valueOf(1000)` reliable? No; use value equality.

**Mistakes to avoid:** Relying on wrapper cache behavior; using null to mean both missing and zero.

**Production perspective:** Unexpected unboxing errors often surface only on unusual input; validate and test null cases.

**Related concepts covered:** Nullability, equality, overflow, performance.

## Q019. How would you handle dates, times and time zones in an API?

**Priority:** Must Know  
**Why interviewers ask it:** Time-zone mistakes affect billing, scheduling and reporting.

**Interview-ready answer:** I use `Instant` for an unambiguous event timestamp, `LocalDate` for a date without a time zone, and `ZonedDateTime` or `ZoneId` when local civil time matters. I specify the API format, generally ISO 8601 with an offset for timestamps, and store a clear time representation. I do not assume that a day is always 24 hours across daylight-saving transitions. I inject `Clock` so time-dependent rules can be tested.

**In-depth explanation:** A `LocalDateTime` alone cannot identify a unique instant without a zone; some local times are skipped or occur twice at DST changes. PostgreSQL `timestamptz` represents an instant and displays according to the session time zone; it does not retain the original zone name. For a recurring 9 a.m. business event, persist the intended `ZoneId` separately.

**Practical backend example:** `Instant now = clock.instant(); LocalDate businessDay = now.atZone(ZoneId.of("Europe/London")).toLocalDate();`

**Common follow-ups:**
- Is UTC enough for future local schedules? No; retain the intended time zone for rules affected by DST.
- Why inject Clock? It makes boundary-time tests deterministic.

**Mistakes to avoid:** Parsing a timestamp without specifying its zone; storing display-local time as if it were UTC.

**Production perspective:** Document time semantics across services and database connections, especially around DST and month-end.

**Related concepts covered:** ISO 8601, PostgreSQL timestamptz, testing, DST.

## Q020. How should BigDecimal be used for money?

**Priority:** Must Know  
**Why interviewers ask it:** Binary floating point and scale mistakes cause billing defects.

**Interview-ready answer:** I avoid `double` for decimal money calculations. I construct `BigDecimal` from a decimal string or `valueOf`, define currency and rounding rules explicitly, and round at the business-required boundary. `BigDecimal.equals` considers scale, so `2.0` and `2.00` are not equal by that method, while `compareTo` reports the same numeric value. I also consider a minor-unit integer representation when the currency and operation allow it.

**In-depth explanation:** `new BigDecimal(0.1)` captures the binary floating-point approximation; `new BigDecimal("0.1")` does not. Division can require a scale and `RoundingMode`, otherwise a non-terminating decimal throws. Money is more than an amount: currency, precision and tax/rounding policy are part of its meaning. Normalize deliberately rather than assuming scale is cosmetic in persistence or equality.

**Practical backend example:** `BigDecimal tax = subtotal.multiply(rate).setScale(2, RoundingMode.HALF_UP);` The rounding mode is an example policy, not universally correct for all jurisdictions.

**Common follow-ups:**
- Why can `equals` differ from `compareTo`? Equality includes scale; numeric comparison does not.
- Is `BigDecimal` automatically currency-safe? No; it does not encode currency or business rounding policy.

**Mistakes to avoid:** Constructing from a double literal; rounding each intermediate step without a defined rule.

**Production perspective:** Agree rounding policy with finance requirements and test edge cases at exact boundaries.

**Related concepts covered:** Precision, scale, currency, database numeric types.

## Q021. When should you use enums rather than strings or booleans?

**Priority:** Important  
**Why interviewers ask it:** Domain states need readable, controlled modeling.

**Interview-ready answer:** I use an enum for a finite, known set of states such as `PENDING`, `PAID` and `CANCELLED`, especially when a boolean would hide multiple possibilities. Enums provide type-safe constants and can hold state-specific behavior. I avoid assuming the enum name is a forever-stable external representation: database values and API strings may need explicit mappings. If new states can arrive from another system, I decide how unknown values are handled.

**In-depth explanation:** A boolean `isProcessed` cannot distinguish payment pending from failed. Enums make invalid states harder to express, but adding a constant can break exhaustive switches or strict deserializers in clients. JPA's `EnumType.STRING` is usually safer than ordinal mapping when declaration order changes, yet renaming a constant still needs a migration strategy.

**Practical backend example:** `enum OrderStatus { PENDING, PAID, CANCELLED }` and reject a `PAID -> PENDING` transition in a domain method rather than allowing arbitrary setters.

**Common follow-ups:**
- Why avoid ordinal persistence? Reordering constants changes stored meaning.
- Can an enum have methods? Yes, including per-constant behavior where justified.

**Mistakes to avoid:** Using one boolean for a multi-state workflow; exposing `name()` as an unreviewed public contract.

**Production perspective:** Treat newly introduced states as compatibility changes across consumers.

**Related concepts covered:** State machines, persistence mapping, API evolution.

## Q022. What does a sealed hierarchy buy you in Java 17?

**Priority:** Bonus  
**Why interviewers ask it:** It reveals whether you can model a closed set of outcomes clearly.

**Interview-ready answer:** A sealed class or interface restricts which types can extend or implement it using `permits` rules. That helps model outcomes such as `Success` and `Rejected` without allowing arbitrary implementations. Each permitted direct subtype must be final, sealed or non-sealed. I use it when the variants have different data and behavior; for a simple fixed list of constant names, an enum may be simpler.

**In-depth explanation:** Sealed classes are a standard feature in Java 17. They let code and reviewers reason about the complete family, though exhaustive pattern-switch support differs by Java version: do not assume Java 21 finalized switch patterns are available unchanged in Java 17. The hierarchy is closed at its immediate permitted boundary, but a non-sealed subtype reopens extension.

**Practical backend example:** `sealed interface PaymentResult permits Approved, Declined {}` with `record Approved(String receipt) implements PaymentResult {}` and `record Declined(String reason) implements PaymentResult {}`.

**Common follow-ups:**
- Can permitted implementations live anywhere? Placement rules depend on named modules or, without them, the same package.
- Why not always use enum? Variants may need different typed payloads.

**Mistakes to avoid:** Claiming sealed implies immutable; forgetting non-sealed permits further subtyping.

**Production perspective:** Typed outcomes can reduce exception-driven normal control flow, but avoid exposing internal result types as unstable API contracts.

**Related concepts covered:** Records, algebraic data modeling, Java versions.

## Q023. How do switch expressions and pattern matching differ across Java 17 and 21?

**Priority:** Important  
**Why interviewers ask it:** Code examples should compile on the stated baseline.

**Interview-ready answer:** Switch expressions using `->` and `yield` are standard before Java 17 and useful when every branch produces a value. Pattern matching for `instanceof` is standard in Java 17, so I can write `if (value instanceof Order order)`. Pattern matching for `switch` and record patterns became standard in Java 21. If a service supports Java 17 without preview features, I do not paste Java 21 switch-pattern code into it.

**In-depth explanation:** A switch expression must be exhaustive; an enum switch can fail compilation after a new constant is added if not handled. Arrow branches avoid accidental fall-through. `instanceof` pattern variables are scoped where the match is known to succeed. A Java 17 project may have some switch pattern support only as a preview feature, which needs explicit compiler/runtime flags and should not be assumed in ordinary production examples.

**Practical backend example:** `String label = switch (status) { case PENDING -> "waiting"; case PAID -> "complete"; case CANCELLED -> "closed"; };` works on Java 17.

**Common follow-ups:**
- What does `yield` do? It provides a value from a block branch of a switch expression.
- Can a switch expression omit cases? Only if it is still exhaustive, for example with a default.

**Mistakes to avoid:** Confusing Java 17 preview features with standard language support.

**Production perspective:** Pin the build JDK and language level; a local Java 21 compiler can hide compatibility errors.

**Related concepts covered:** Exhaustiveness, enums, sealed types, build configuration.

## Q024. What do annotations do, and when is reflection appropriate?

**Priority:** Important  
**Why interviewers ask it:** Spring annotations are metadata, not magic by themselves.

**Interview-ready answer:** An annotation describes metadata; a compiler, annotation processor or runtime framework must interpret it. Spring scans and processes annotations such as `@Service` and `@Transactional` to register beans or create proxies. Reflection can inspect types or invoke members at runtime, which enables frameworks but adds complexity and may have access or performance constraints. I prefer ordinary typed code for application logic and use framework annotations at clear boundaries.

**In-depth explanation:** Annotation retention controls whether metadata is available in source, class files or at runtime. `@Transactional` does not start a transaction when a method is called without an appropriate Spring-managed proxy. Compile-time processing can generate code without runtime reflection. Framework behavior depends on how metadata is discovered, inherited and proxied, so tests should verify important boundaries.

**Practical backend example:** `@Service class OrderService { @Transactional void place(Order order) { ... } }` only gains transaction behavior when invoked through the managed proxy under normal proxy-based configuration.

**Common follow-ups:**
- Does declaring an annotation execute code? No, a processor must act on it.
- Why can self-invocation bypass `@Transactional`? The internal call does not pass through the proxy.

**Mistakes to avoid:** Assuming every private annotated method is intercepted; using reflection where a simple interface suffices.

**Production perspective:** Proxies and reflection can obscure call paths; inspect configuration and logs when behavior differs from annotations.

**Related concepts covered:** AOP proxies, retention, Spring DI, annotation processors.

## Q025. How would you design a value object for an email address?

**Priority:** Important  
**Why interviewers ask it:** It combines validation, equality and domain boundaries.

**Interview-ready answer:** I would make an immutable `EmailAddress` that validates basic format and stores a documented normalized representation. Value equality should depend on that representation, not object identity. I would avoid claiming a simple regex proves deliverability, and I would decide whether case normalization is acceptable for the product and provider assumptions. Validation at the request boundary gives a friendly error; the value object preserves the invariant for internal callers too.

**In-depth explanation:** RFC email syntax and real deliverability are more complex than a single regex. Domain normalization is a policy choice: lowercasing a domain is generally reasonable, while changing local-part case can be context-dependent. If email is used for uniqueness, a database unique constraint on the chosen normalized key closes concurrent-registration races. Sensitive values should not be casually logged.

**Practical backend example:** `record EmailAddress(String value) { EmailAddress { value = value.trim(); if (!value.contains("@")) throw new IllegalArgumentException("Invalid email"); } }` This is illustrative basic validation, not a complete email parser.

**Common follow-ups:**
- Can request validation replace a domain invariant? No; other callers can bypass the HTTP layer.
- Is a pre-insert availability check enough for uniqueness? No, enforce a database constraint.

**Mistakes to avoid:** Claiming a simplistic regex accepts all valid emails; equating normalization with verification.

**Production perspective:** Define canonicalization and uniqueness policy before importing users from multiple identity providers.

**Related concepts covered:** Records, database constraints, validation, privacy.

## Q026. What are the risks of mutable keys and shallow copies?

**Priority:** Important  
**Why interviewers ask it:** Aliasing bugs often masquerade as collection bugs.

**Interview-ready answer:** A hash key must keep stable equality and hash values while stored; mutating a key field can make an entry unreachable through normal lookup. A shallow copy creates a new outer collection but shares its elements, so modifying a mutable element still changes what both owners observe. I choose immutable key/value types or explicitly copy mutable nested data at ownership boundaries.

**In-depth explanation:** `List.copyOf` creates an unmodifiable collection snapshot of references, not deep copies of each element. `Collections.unmodifiableList` is only a view over the original list. For arrays, `clone()` creates a shallow array copy. Deep copying arbitrary object graphs can be costly and error-prone; often the better design is to use immutable domain values.

**Practical backend example:** `Map<OrderKey, Order> cache` is safe only if `OrderKey` equality stays stable. A record with a mutable `byte[]` component still needs a defensive copy and custom array-aware equality if used as a value key.

**Common follow-ups:**
- Does final make a list immutable? No.
- Does `List.copyOf` protect mutable elements? No.

**Mistakes to avoid:** Changing a key after insertion; calling an unmodifiable view a snapshot.

**Production perspective:** Mutable cache keys can cause growing, apparently inexplicable duplicate entries.

**Related concepts covered:** HashMap, records, defensive copies, cache correctness.

## Q027. How do you avoid null-related bugs without hiding invalid states?

**Priority:** Must Know  
**Why interviewers ask it:** Null handling is about contracts, not just syntax.

**Interview-ready answer:** I define which inputs are required, validate them at the boundary, and fail clearly if they are missing. For legitimate absence, I use `Optional` on a lookup return or an empty collection for zero results. Inside domain code I favor constructors that establish valid state. I do not sprinkle null defaults everywhere if null means an invalid request, because that can silently create wrong orders.

**In-depth explanation:** Java's type system does not enforce non-null references by default. `Objects.requireNonNull` can guard a required constructor field, while Bean Validation produces user-facing request errors. Defaults are appropriate only if they are part of the domain contract. Null-safe syntax or Optional cannot replace deciding what absence means.

**Practical backend example:** `CreateOrderRequest` can require `customerId`; a service lookup returns `Optional<Customer>` and turns empty into `CustomerNotFound` before changing state.

**Common follow-ups:**
- Should missing line items become an empty order? Only if the product permits empty orders.
- Should an empty query result be null? Usually an empty collection is clearer.

**Mistakes to avoid:** Catching `NullPointerException` as normal validation; replacing every missing required field with a default.

**Production perspective:** Explicit contracts produce actionable 4xx responses instead of sporadic downstream 500s.

**Related concepts covered:** Optional, Bean Validation, constructors, API errors.

## Q028. What is the difference between fail-fast validation and accumulating errors?

**Priority:** Important  
**Why interviewers ask it:** Different layers need different feedback strategies.

**Interview-ready answer:** For a user-submitted DTO, collecting independent field errors lets the client fix several issues in one pass. For a domain invariant or unsafe operation, failing fast prevents invalid state from proceeding. I separate shape validation, such as a missing product ID, from business rules, such as insufficient inventory, which require current data. The API should consistently map both to meaningful, safe responses.

**In-depth explanation:** Bean Validation can collect multiple constraint violations; nested objects need cascaded validation with `@Valid`. Cross-field rules can use custom validation or service/domain logic. A service may need a transaction to check a rule against current database state; a pre-check alone cannot close concurrency races without locking or constraints. Accumulating every possible error is not appropriate if later checks depend on earlier valid data.

**Practical backend example:** Validate `@NotEmpty List<@NotNull Long> productIds` on the request, then check inventory and reject the checkout before charging payment.

**Common follow-ups:**
- Can Bean Validation guarantee stock availability? No; stock changes concurrently and needs transactional control.
- Is fail-fast always better? No; independent form-field errors are often better accumulated.

**Mistakes to avoid:** Treating DTO validation as a substitute for database constraints or domain rules.

**Production perspective:** Clear errors reduce client retries; expensive validation should still respect request-size limits.

**Related concepts covered:** Bean Validation, transactions, race conditions, API contracts.

## Q029. How would you refactor a long conditional into a maintainable strategy?

**Priority:** Important  
**Why interviewers ask it:** It tests whether you can simplify change without overengineering.

**Interview-ready answer:** I first check whether the conditional is actually hard to maintain. For a small, closed enum, a switch expression can be clearest. If many payment providers have different integrations and change independently, I define a narrow `PaymentProcessor` contract, implement one per provider, and select one through an explicit registry. I keep common validation outside the strategy and make missing or duplicate provider mappings fail clearly.

**In-depth explanation:** The strategy pattern replaces repeated branching with polymorphic behavior, but moving one switch into a registry without reducing complexity is not a win. Spring can inject a list of processors and build a map by provider code. Validate uniqueness at startup rather than silently choosing the last implementation. Keep the selected strategy stateless or thread-safe because Spring services are usually singletons.

**Practical backend example:** `PaymentProcessor processor = processors.get(command.provider()); if (processor == null) throw new UnsupportedProvider(command.provider()); processor.charge(command);`

**Common follow-ups:**
- When keep a switch? When cases are few, stable and easy to scan.
- How do you test selection? Test missing/duplicate registration and each strategy's behavior.

**Mistakes to avoid:** Creating dozens of classes for a two-case condition; hiding an unsafe default branch.

**Production perspective:** Provider isolation makes rollout and failure metrics clearer, but plugin registries need startup validation.

**Related concepts covered:** Polymorphism, DI, enums, extensibility.

## Q030. What makes a Java API backward-compatible for callers?

**Priority:** Important  
**Why interviewers ask it:** Backend changes must not unexpectedly break consumers.

**Interview-ready answer:** Compatibility includes source, binary and behavioral expectations, not just whether a method name still exists. Removing a public method or changing its signature can break callers; changing its meaning can break them even if code compiles. Serialized JSON, enum strings and error codes are also contracts across services. I prefer additive changes, deprecate and measure old usage, test representative clients, and version or coordinate when a breaking change is unavoidable.

**In-depth explanation:** Adding an abstract method to an interface can break implementers; a default method may help but can conflict with other defaults. Adding enum values can break exhaustive switches or strict clients. A new required JSON field is not additive for old senders. Behavioral changes such as returning null where an empty list was promised are compatibility issues even without signature changes.

**Practical backend example:** Add optional `deliveryInstructions` to `CreateOrderRequest` while preserving the old request shape; do not suddenly require it without a migration plan.

**Common follow-ups:**
- Is a new response field always safe? Often, but strict deserializers or signed payloads may reject it.
- Is deprecation enough? No; measure use and plan removal or migration.

**Mistakes to avoid:** Equating successful compilation with safe rollout; persisting enum ordinal values.

**Production perspective:** Contract tests and staged deployments reduce mixed-version failures.

**Related concepts covered:** API versioning, serialization, interface evolution, rollout.