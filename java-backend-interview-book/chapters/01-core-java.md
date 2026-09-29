# Chapter 1. Core Java, OOP, exceptions, and language fundamentals

Assume Java 17 unless a question explicitly mentions Java 21. Examples omit imports when the types are unambiguous, and use a small order-service domain so the ideas stay connected to backend work rather than to textbook shapes.

## Q001. How would you apply encapsulation, abstraction, inheritance and polymorphism in an order service?

**Priority:** Must Know  
**Why interviewers ask it:** They want design decisions applied to a real service, not four memorised definitions.

**Interview-ready answer:** Encapsulation means the `Order` owns its invariants: no caller sets `status` directly, they call `markPaid` or `cancel`, and the object rejects an illegal transition. Abstraction means checkout depends on a `PaymentGateway` interface describing what I need — capture, refund — not on a provider SDK. Polymorphism is what makes that useful: a Stripe implementation in production and a stub in tests satisfy the same contract, and the service does not change. Inheritance I use sparingly, only when there is a genuine is-a relationship with substitutable behaviour; sharing code is not a reason to extend a class, because composition is easier to change and to test. The practical goal is that business rules live in one place and replaceable integrations sit behind small interfaces.

**In-depth explanation:** Encapsulation is about valid state, not about the `private` keyword — a class with a private field and a public setter for every field is not encapsulated. The useful test is whether an object can ever be observed in a state your business rules forbid. Inheritance carries the Liskov obligation: a subtype must be usable wherever the supertype is, so an override that strengthens preconditions or weakens postconditions is a bug even when it compiles. Polymorphism resolves at runtime through the reference's dynamic type, which is what allows dependency inversion: high-level policy depends on an interface, and the low-level detail implements it. In a Spring application this shows up as constructor-injected interfaces, and the payoff is that swapping a provider or writing a fast test touches one line of wiring.

**Practical backend example:** Invariants inside the object, integration behind an interface:

```java
public class Order {
    private OrderStatus status = OrderStatus.NEW;
    private String receiptId;

    public void markPaid(String receiptId) {
        if (status != OrderStatus.NEW) {                 // the object protects its own rules
            throw new IllegalStateException("cannot pay an order in status " + status);
        }
        this.receiptId = Objects.requireNonNull(receiptId);
        this.status = OrderStatus.PAID;
    }
}

public interface PaymentGateway { Receipt capture(Money amount); }   // abstraction I own

// polymorphism: the service is identical in production and in tests
public class CheckoutService {
    private final PaymentGateway payments;
    public CheckoutService(PaymentGateway payments) { this.payments = payments; }
}
```

**Common follow-ups:**
- Where is inheritance appropriate? Where the subtype genuinely satisfies the supertype's contract — a stable taxonomy or a framework extension point — not for code reuse.
- Is a private field enough encapsulation? No; public setters can still drive the object into an invalid state. Expose intent-revealing methods instead.
- How does this relate to dependency inversion? The service depends on an interface it defines; the provider adapter implements it, so the dependency points inward.

**Mistakes to avoid:** Reciting definitions with no example; calling every interface an abstraction while all logic sits in the controller; inheriting from a base service for two helper methods; anaemic entities that are just field bags with a service mutating them.

**Production perspective:** Narrow interfaces around external providers are what make a migration or an outage workaround tractable — you write one adapter instead of editing twenty call sites. The cost is indirection, so do not create an interface per class by reflex; introduce one when there is a real second implementation, including a test double that meaningfully simplifies testing.

**Related concepts covered:** Domain invariants, Liskov substitution, dependency inversion, test doubles, anaemic domain model.

## Q002. When would you choose an interface, abstract class or concrete class?

**Priority:** Must Know  
**Why interviewers ask it:** It shows how you shape extension points, and whether you add them speculatively.

**Interview-ready answer:** I use an interface for a capability that unrelated types can provide — `PaymentGateway`, `TaxCalculator` — because a class can implement many interfaces and that keeps the contract narrow. I use an abstract class when several closely related implementations genuinely share state or a template algorithm, and I want to fix the skeleton while subclasses fill in steps. I use a concrete class when there is no extension point, which is most of the time. Since Java 8 interfaces can have default and static methods, so "interfaces cannot have behaviour" is outdated, but they still cannot hold per-instance state. The rule I apply is not to invent an abstraction for a second implementation that does not exist yet; a concrete class is easy to extract an interface from later.

**In-depth explanation:** Default methods exist mainly for API evolution — adding a method to a published interface without breaking implementers — and a class inheriting conflicting defaults from two interfaces must override to disambiguate. Abstract classes buy you constructors, protected state and final template methods, at the price of single inheritance and tighter coupling: subclasses become sensitive to the base class's internals. Sealed interfaces (Java 17) add a third option when you want a closed set of implementations with exhaustive handling. A practical heuristic: if the shared thing is a contract, use an interface; if it is a partially implemented algorithm with shared state, an abstract class is honest; if it is neither, keep it concrete and let the need for abstraction emerge from a second real caller.

**Practical backend example:** A capability contract, a template, and a value type that needs neither:

```java
public interface TaxCalculator {                      // capability: unrelated implementations
    Money calculate(Order order);
    default boolean supports(Country country) { return true; }   // evolvable default
}

public abstract class AbstractImportJob {             // template: shared skeleton + state
    protected final Clock clock;
    protected AbstractImportJob(Clock clock) { this.clock = clock; }
    public final ImportReport run() {                 // final: the skeleton is not overridable
        var started = Instant.now(clock);
        var rows = fetch();                           // subclass supplies the steps
        return new ImportReport(rows.size(), started, Instant.now(clock));
    }
    protected abstract List<Row> fetch();
}

public record TaxRate(String region, BigDecimal percentage) {}   // concrete: no extension point
```

**Common follow-ups:**
- Can an interface hold state? Only `public static final` constants; instance state requires a class.
- Can an abstract class implement an interface? Yes, and it may leave some methods abstract for subclasses.
- Why might you prefer a sealed interface? When you want a fixed set of implementations and exhaustive `switch` handling without a `default` branch.

**Mistakes to avoid:** Claiming interfaces cannot have method bodies; creating an interface with exactly one implementation for testability when a hand-written fake or a real object would do; deep abstract class hierarchies where a subclass must read the parent's source to work.

**Production perspective:** A published interface is a maintenance commitment — every implementer breaks when you add an abstract method. If a library-style interface must evolve, a default method with a sensible fallback avoids a breaking change; in internal code, changing all implementations is usually cheaper than accumulating defaults.

**Related concepts covered:** Default and static methods, template method pattern, sealed types, API evolution, speculative generality.

## Q003. Why prefer composition over inheritance in service design?

**Priority:** Must Know  
**Why interviewers ask it:** It probes whether you can keep change local as a codebase grows.

**Interview-ready answer:** Composition delegates to injected collaborators, so each behaviour can be replaced or tested on its own; inheritance binds a subclass to a base class's implementation, including details that are not part of any documented contract. The classic failure is a base service whose method calls another overridable method: a harmless-looking change to the base silently changes every subclass. With composition the dependencies are explicit in the constructor, which also makes an oversized class obvious — five collaborators is a design smell you can see. I still use inheritance where the subtype relationship is genuine and substitutable, or where a framework requires it. But "I need these two helper methods" is a reason to inject a collaborator, not to extend a class.

**In-depth explanation:** The fragile base class problem is the core argument: subclasses depend on the base's internal call sequence, so behaviour-preserving refactors in the base can break them, and the compiler will not warn you. Composition also composes — you can wrap a collaborator in a decorator to add retries, caching or metrics without touching either class, which inheritance cannot do at runtime. The counterweight is that composition can be over-applied: extracting every conditional into a strategy interface produces indirection with no benefit. A reasonable progression is to write concrete code first, then extract a collaborator when you have an independent policy, an external integration, or a genuine second implementation. Where you do inherit, making the class or the methods `final` unless designed for extension prevents accidental overriding.

**Practical backend example:** Injected policies, and a decorator that inheritance could not give you:

```java
// composition: each policy replaceable and independently testable
public class CheckoutService {
    private final FraudChecker fraud;
    private final PaymentGateway payments;
    public CheckoutService(FraudChecker fraud, PaymentGateway payments) { ... }
}

// decoration: add behaviour around an existing implementation without subclassing it
public class MeteredPaymentGateway implements PaymentGateway {
    private final PaymentGateway delegate;
    private final Timer timer;
    public Receipt capture(Money amount) {
        return timer.record(() -> delegate.capture(amount));
    }
}
```

**Common follow-ups:**
- When is inheritance still right? Stable taxonomies, framework contracts, and sealed hierarchies where substitutability is real and checked.
- Does composition remove coupling? No; it converts implicit coupling to the base class into explicit coupling to a contract you control.
- How do you protect a class you do own from bad subclassing? Make it `final`, or make overridable methods explicitly documented and everything else final.

**Mistakes to avoid:** A `BaseService` that every service extends for logging; overriding a method to disable inherited behaviour (a substitutability violation); extracting a strategy interface for a single `if` statement.

**Production perspective:** Inheritance chains make incidents harder: you read three classes to learn what one endpoint actually does. Explicit constructor dependencies show the blast radius of a change at a glance, and they make it obvious when a class has quietly grown into a god object.

**Related concepts covered:** Fragile base class, decorator pattern, dependency injection, final classes, strategy extraction.

## Q004. What is the equals and hashCode contract, and how can it break a HashSet?

**Priority:** Must Know  
**Why interviewers ask it:** Violating it produces silent data loss in collections and caches, and it is the most common Java correctness trap.

**Interview-ready answer:** The contract is: equal objects must have equal hash codes; `equals` must be reflexive, symmetric, transitive, consistent, and false for null. Hash-based collections rely on it — `HashMap` locates the bucket by hash, then compares with `equals` inside the bucket. If two objects are equal but hash differently, they land in different buckets and a `HashSet` happily stores both duplicates. The subtler failure is mutating a field used in `hashCode` after insertion: the entry stays in the old bucket, so `contains` returns false and the entry is unreachable but still consuming memory. That is why I build keys from immutable fields, and prefer records or IDE-generated implementations over hand-written ones.

**In-depth explanation:** Unequal objects may share a hash code — that is a collision, handled by the bucket's chain or tree — so `hashCode` is about distribution, not uniqueness. Symmetry breaks easily when a subclass adds a field to `equals`: `sub.equals(base)` is false while `base.equals(sub)` is true, which is why `getClass()` comparison and `instanceof` comparison behave differently, and why composition is safer than inheritance for value types. For JPA entities the usual advice is to base `equals` on a business key rather than the generated ID, because the ID is null before persist, so an entity added to a `Set` before flushing changes its hash afterwards. Java 16 records generate both methods from their components, which makes them the least error-prone option for keys and DTOs.

**Practical backend example:** A correct key, and the mutation trap:

```java
// record: equals/hashCode generated from immutable components
public record OrderKey(long tenantId, String externalReference) {
    public OrderKey {
        Objects.requireNonNull(externalReference);
    }
}

// the trap: a mutable field participating in hashCode
class MutableKey {
    String value;                                  // mutated after insertion
    @Override public int hashCode() { return Objects.hash(value); }
    @Override public boolean equals(Object o) {
        return o instanceof MutableKey k && Objects.equals(value, k.value);
    }
}

Set<MutableKey> set = new HashSet<>();
MutableKey key = new MutableKey(); key.value = "a";
set.add(key);
key.value = "b";                                   // hash changes; entry stays in the old bucket
set.contains(key);                                 // false - the entry is lost but still in memory
```

**Common follow-ups:**
- Must unequal objects have different hash codes? No; collisions are legal and expected. Equal objects must agree.
- What happens with a constant `hashCode`? Everything collides into one bucket: correct but degenerate, O(n) lookups until the bin treeifies.
- How should JPA entities implement it? Prefer a stable business key; using a generated ID breaks for unsaved entities whose ID is still null.

**Mistakes to avoid:** Overriding `equals` without `hashCode`; including mutable or lazily loaded fields; using `==` for `String` or `Integer` comparison inside `equals`; forgetting the null and type checks.

**Production perspective:** These bugs surface as caches that never hit, deduplication that lets duplicates through, or a `Set` whose size keeps growing — all of which look like data problems, not code problems. Records for keys and a test that inserts, mutates and re-looks-up are cheap protection.

**Related concepts covered:** Hash bucket distribution, records, symmetry and inheritance, JPA entity identity, cache correctness.

## Q005. How is Comparable different from Comparator, and what must ordering agree with?

**Priority:** Important  
**Why interviewers ask it:** Sorting contracts are easy to violate, and a violation can throw at runtime under load.

**Interview-ready answer:** `Comparable` defines a type's single natural ordering, implemented by the class itself in `compareTo`. `Comparator` is an external, reusable ordering you pass to a sort or a `TreeMap`, and you can have as many as you need — by total, by date, by status then date. The contract matters: the comparison must be consistent — if `a > b` and `b > c` then `a > c` — antisymmetric, and it must not depend on mutable state that changes during the sort. Java's sort detects a broken comparator and throws `IllegalArgumentException: Comparison method violates its general contract!`, often only on larger inputs. I also make sure `compareTo` is consistent with `equals` for anything used in a sorted set or map, because those use comparison, not `equals`, to decide membership.

**In-depth explanation:** `TreeSet` and `TreeMap` consider two elements duplicates when the comparison returns zero, so an ordering inconsistent with `equals` silently drops entries — the classic case is `BigDecimal`, where `1.0` and `1.00` are unequal by `equals` but compare equal. The runtime exception comes from TimSort, which relies on a consistent total order to merge runs; small arrays use insertion sort and may not detect the violation, which is why these bugs appear in production rather than in tests. Subtraction-based comparators (`a.value - b.value`) overflow for large or negative values and are a frequent source of inconsistency; `Integer.compare` is both safe and clearer. Modern comparator construction — `Comparator.comparing(...).thenComparing(...).reversed()` — is composable and avoids most hand-written mistakes, and `nullsFirst`/`nullsLast` handles nullable fields explicitly.

**Practical backend example:** Composed comparators and the overflow trap:

```java
// natural ordering: one per type, on the type itself
public record Money(long minorUnits, String currency) implements Comparable<Money> {
    public int compareTo(Money other) {
        if (!currency.equals(other.currency)) throw new IllegalArgumentException("currency mismatch");
        return Long.compare(minorUnits, other.minorUnits);         // never subtraction
    }
}

// external orderings: as many as the use cases need
Comparator<Order> byStatusThenNewest =
        Comparator.comparing(Order::status)
                  .thenComparing(Order::createdAt, Comparator.reverseOrder())
                  .thenComparing(Order::id);                        // stable tiebreaker

orders.sort(Comparator.comparing(Order::customerName,
        Comparator.nullsLast(String.CASE_INSENSITIVE_ORDER)));      // explicit null policy
```

**Common follow-ups:**
- What causes "Comparison method violates its general contract"? An inconsistent or non-transitive comparator, often from subtraction overflow or comparing on mutable state.
- Why can a `TreeSet` lose elements? It treats a zero comparison as equality, so an ordering inconsistent with `equals` merges distinct objects.
- Is `Collections.sort` stable? Yes for objects — equal elements keep their relative order — which is why a tiebreaker only matters for determinism across different inputs.

**Mistakes to avoid:** `a.getX() - b.getX()` on ints that can overflow; comparators that read a field mutated by another thread during the sort; implementing `Comparable` inconsistently with `equals` and then using a `TreeMap`.

**Production perspective:** Sorting bugs scale with data: a comparator that works on ten rows throws on ten thousand. If you sort user-controlled data, add a deterministic final tiebreaker such as the ID so that pagination does not shuffle rows between pages.

**Related concepts covered:** TimSort contract, TreeMap semantics, comparator composition, null handling, deterministic pagination.

## Q006. Why are Strings immutable, and how do StringBuilder and the pool affect code?

**Priority:** Must Know  
**Why interviewers ask it:** String behaviour touches memory, security and correctness in everyday code.

**Interview-ready answer:** `String` is immutable so it can be shared safely: it is thread-safe without synchronisation, its hash code can be cached — which is why it is a good map key — and a value cannot change after a security or validation check. The compiler interns string literals in a pool so identical literals share one object, which is exactly why comparing with `==` is unreliable: a literal and a runtime-built string are different objects with equal contents, so you compare with `equals`. Immutability means every concatenation creates a new object, so building a string in a loop with `+` allocates garbage proportional to the loop; `StringBuilder` mutates one buffer instead. A single concatenation expression is fine — the compiler handles it — it is the loop that matters.

**In-depth explanation:** Since Java 9, `String` stores bytes with an encoding flag (compact strings), so Latin-1 text uses one byte per character; this is an implementation detail, not a guarantee, but it matters for heap sizing. `String.intern()` explicitly adds to the pool, which is occasionally useful for massive duplicate data but can hurt: the pool is a hash table, and interning many distinct strings costs time and native memory. `StringBuilder` is unsynchronised and fast; `StringBuffer` is its synchronised ancestor and almost never needed. Text blocks (Java 15) make multi-line SQL and JSON readable without concatenation. One security note: because strings are immutable and pooled, a password held in a `String` stays in memory until garbage collected, which is why sensitive values are conventionally held in `char[]` or cleared buffers.

**Practical backend example:** Where the allocation actually happens:

```java
// fine: the compiler compiles a single expression into efficient concatenation
String message = "order " + orderId + " confirmed";

// costly: a new String (and builder) per iteration
String csv = "";
for (OrderLine line : lines) csv += line.sku() + ";";        // O(n^2) copying

// correct: one buffer, resized geometrically
StringBuilder sb = new StringBuilder(lines.size() * 16);
for (OrderLine line : lines) sb.append(line.sku()).append(';');
String result = sb.toString();

// comparison: never ==
String fromRequest = new String("PAID".getBytes(StandardCharsets.UTF_8));
boolean wrong = fromRequest == "PAID";            // false: different objects
boolean right = "PAID".equals(fromRequest);       // true, and null-safe on the literal
```

**Common follow-ups:**
- Why does `==` sometimes work for strings? Both sides may be the same pooled literal; that is an implementation coincidence, not a rule.
- Is `String.intern()` a good idea? Rarely; it helps only with massive duplication and otherwise adds pool pressure and latency.
- `StringBuilder` or `StringBuffer`? `StringBuilder` unless you genuinely share the builder across threads, which is itself a design smell.

**Mistakes to avoid:** Concatenating in a loop; using `==` for value comparison; building SQL by concatenation (an injection risk as well as slow); holding secrets in long-lived `String` fields.

**Production perspective:** String duplication is a common source of heap pressure in services that parse many similar payloads; a heap dump usually shows it immediately as thousands of identical values. Fixing it with a small canonicalisation map or an enum is often a bigger win than tuning the garbage collector.

**Related concepts covered:** String pool and interning, compact strings, StringBuilder sizing, text blocks, heap analysis, secret handling.

## Q007. What is pass-by-value in Java, including object references?

**Priority:** Must Know  
**Why interviewers ask it:** It is a precision question: the right answer requires distinguishing a reference from the object it points to.

**Interview-ready answer:** Java is strictly pass-by-value. For a primitive, the value is copied. For an object, the reference is copied — so the method gets its own copy of a pointer to the same object. That means a method can mutate the object and the caller sees the change, but reassigning the parameter inside the method has no effect on the caller's variable. The practical consequence is that passing a mutable collection or entity to a method hands out the ability to modify it, which is why I return unmodifiable views or defensive copies at boundaries, and prefer immutable types for anything shared. People sometimes call this "pass-by-reference" for objects, but it is not: a true pass-by-reference language would let the method reassign the caller's variable.

**In-depth explanation:** The distinction matters for API design more than for trivia. If a service method accepts a `List` and stores it in a field, the caller can still mutate that list afterwards and silently change the service's state — a classic aliasing bug that also shows up with arrays returned from getters. The same applies to JPA entities handed to another layer: whoever holds the reference can change a managed entity, and dirty checking will write those changes at flush. Defensive copying on input and unmodifiable wrappers on output remove the ambiguity; `List.copyOf` both copies and rejects nulls. Note also that `final` on a parameter or field prevents reassignment of the reference, not mutation of the object — `final List` can still have elements added.

**Practical backend example:** Reassignment versus mutation, and the boundary fix:

```java
void demonstrate(Order order, int count) {
    order.markPaid("rcp_1");        // visible to the caller: same object
    order = new Order();            // NOT visible: only this local copy is rebound
    count = 99;                     // NOT visible: primitive copy
}

// aliasing bug: the caller can still mutate the stored list
class Basket {
    private final List<OrderLine> lines;
    Basket(List<OrderLine> lines) { this.lines = List.copyOf(lines); }   // defensive copy
    List<OrderLine> lines() { return Collections.unmodifiableList(lines); }  // no write access out
}
```

**Common follow-ups:**
- Can a method change which object the caller's variable refers to? No; only the object's internal state can be changed.
- What does `final` on a parameter guarantee? Only that the parameter is not reassigned inside the method; the object remains mutable.
- Why copy collections at the boundary? Because a stored reference lets the caller mutate your internal state later, which is a bug that appears far from its cause.

**Mistakes to avoid:** Saying Java passes objects by reference; returning the internal collection or array from a getter; assuming an immutable wrapper makes the underlying elements immutable; treating `final` as immutability.

**Production perspective:** Aliasing bugs are hard to reproduce because the mutation happens somewhere else entirely. Immutable value types and copy-on-input boundaries eliminate a whole class of "who changed this?" incidents, at the cost of some allocation that is almost always irrelevant.

**Related concepts covered:** Aliasing, defensive copying, unmodifiable views, `final` semantics, JPA entity exposure.

## Q008. How do checked and unchecked exceptions influence API design?

**Priority:** Must Know  
**Why interviewers ask it:** The choice shapes every caller's code, and most candidates have only a stylistic opinion.

**Interview-ready answer:** A checked exception is part of the method signature: callers must catch it or declare it, so it says "this failure is expected and you should decide what to do". An unchecked exception says "this is a programming error or an unrecoverable condition". My rule is to use unchecked exceptions for almost everything in application code — a business rule violation, a missing resource — because there is usually one place, a global handler, that turns them into responses, and checked exceptions force intermediate layers to handle or propagate failures they cannot act on. I use checked exceptions where the caller genuinely has a recovery path and I want the compiler to enforce the decision. What matters more than the category is that the exception carries meaning: a typed `OrderNotFoundException` with the ID, not a bare `RuntimeException` with a string.

**In-depth explanation:** The real costs of checked exceptions are the pressure to write `catch (Exception e) {}` to make code compile, and the fact that they leak through abstractions — a `SQLException` in a service signature exposes persistence to the web layer. Spring's design is instructive: it wraps JDBC's checked `SQLException` in the unchecked `DataAccessException` hierarchy precisely so that callers are not forced to handle what they cannot fix, while still allowing specific subtypes such as `DuplicateKeyException` to be caught where a recovery exists. When translating, always keep the cause (`throw new OrderProcessingException(msg, e)`) or the stack trace of the original failure is lost, which makes production debugging much harder. Also design for the handler: exceptions that carry structured data — the resource type, the ID, a stable error code — let you produce consistent API errors without parsing messages.

**Practical backend example:** Typed unchecked exceptions and translation that preserves the cause:

```java
public class OrderNotFoundException extends RuntimeException {      // unchecked: no recovery here
    private final UUID orderId;
    public OrderNotFoundException(UUID orderId) {
        super("order not found: " + orderId);
        this.orderId = orderId;                                      // structured, not just text
    }
    public UUID orderId() { return orderId; }
}

// translate at the boundary, keep the cause
try {
    return paymentClient.capture(request);
} catch (IOException e) {                                            // checked, provider-specific
    throw new PaymentUnavailableException("payment provider unreachable", e);   // cause preserved
}
```

**Common follow-ups:**
- Why does Spring translate `SQLException`? So callers are not forced to handle low-level failures, while typed subclasses still allow targeted recovery.
- When is a checked exception the right call? When the caller has a realistic, specific recovery action and you want the compiler to insist on it.
- What must never be lost when wrapping? The cause. Without it you lose the original stack trace and usually the actual reason.

**Mistakes to avoid:** Swallowing exceptions with an empty catch; `throws Exception` on service methods; catching `Throwable`; using exceptions for normal control flow; losing the cause when rethrowing.

**Production perspective:** Exception types are an operational interface: they drive alerting, retry decisions and error dashboards. A hierarchy that distinguishes "client sent something invalid" from "a dependency is down" lets you alert on the second without being paged for the first.

**Related concepts covered:** Exception translation, cause chaining, `DataAccessException`, error codes, alerting on failure classes.

## Q009. How would you design exception handling for a Spring service?

**Priority:** Must Know  
**Why interviewers ask it:** Consistent error responses are a visible sign of API maturity, and the layering is easy to get wrong.

**Interview-ready answer:** I throw meaningful domain exceptions where the problem is detected, and translate them to HTTP in exactly one place — a `@RestControllerAdvice` with `@ExceptionHandler` methods. Controllers do not contain try/catch for business failures, and services do not know about status codes. The advice maps each exception type to a status and builds a consistent body; in Spring 6 I use `ProblemDetail`, the standard problem-details format (RFC 7807, updated by RFC 9457), with a stable machine-readable code, a human-readable message, and a correlation ID so support can find the request in the logs. Validation failures produce per-field errors. Unexpected exceptions get a 500 with a generic message — logged in full server-side, with no stack trace or internal detail in the response.

**In-depth explanation:** Order of specificity matters: Spring picks the most specific handler, so a broad `Exception` handler is a safety net, not the main path. Log levels should differ by class of failure — client errors at debug or info, dependency failures at warn, unexpected errors at error with the stack trace — otherwise your error dashboard is dominated by users typing bad input. Some failures never reach `@ExceptionHandler`: anything thrown in a filter or during security processing is handled by the filter chain, so authentication and authorization errors need their own entry points to produce the same body shape. Keep the error contract documented and stable; clients branch on it, so changing a code is a breaking change.

**Practical backend example:** One translation point, one body shape:

```java
@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(OrderNotFoundException.class)
    ProblemDetail handleNotFound(OrderNotFoundException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        problem.setProperty("code", "ORDER_NOT_FOUND");            // stable, machine-readable
        problem.setProperty("correlationId", MDC.get("correlationId"));
        return problem;                                             // 404
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, "Validation failed");
        problem.setProperty("errors", ex.getBindingResult().getFieldErrors().stream()
                .map(f -> Map.of("field", f.getField(), "message", f.getDefaultMessage())).toList());
        return problem;                                             // 400 with per-field detail
    }

    @ExceptionHandler(Exception.class)
    ProblemDetail handleUnexpected(Exception ex) {
        log.error("unhandled exception correlationId={}", MDC.get("correlationId"), ex);  // full detail in logs
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.INTERNAL_SERVER_ERROR, "Unexpected error");   // generic to the client
        problem.setProperty("correlationId", MDC.get("correlationId"));
        return problem;
    }
}
```

**Common follow-ups:**
- Why not catch in the controller? It scatters mapping logic and produces inconsistent bodies; one advice keeps the contract in one place.
- What about exceptions thrown in filters? They bypass `@ExceptionHandler`; security and filter errors need their own entry points to match the format.
- Should the client see the stack trace? Never. Log it with a correlation ID and return that ID instead.

**Mistakes to avoid:** Returning 200 with an error field; leaking exception messages containing SQL or internal hostnames; logging the same exception at every layer; using 500 for validation failures.

**Production perspective:** A stable error contract with codes and correlation IDs is what makes support tractable: a customer quotes an ID, you find the exact request. Without it, every investigation starts with a timestamp and a guess.

**Related concepts covered:** ProblemDetail (RFC 7807, updated by RFC 9457), `@RestControllerAdvice`, validation errors, correlation IDs, log-level discipline, information disclosure.

## Q010. How does try-with-resources work and what happens with suppressed exceptions?

**Priority:** Important  
**Why interviewers ask it:** Resource leaks are a real production failure mode, and the suppression detail shows depth.

**Interview-ready answer:** Try-with-resources declares resources that implement `AutoCloseable` in the parentheses, and the compiler generates the `close()` calls in a finally block, in reverse order of declaration, whether the body completes normally or throws. It removes the classic bug where an exception in the body hides the close, or an exception in close replaces the real failure. That last case is what suppression handles: if the body throws and `close()` also throws, the body's exception propagates and the close exception is attached to it, retrievable via `getSuppressed()`. Before this construct, the close exception would overwrite the original one and you would debug the wrong problem. In backend code it matters for streams, JDBC objects and any client with a connection.

**In-depth explanation:** Since Java 9 you can name an existing effectively-final variable in the resource list, which avoids a redundant local. Multiple resources are closed in reverse order, which is what you want for a `ResultSet` inside a `Statement` inside a `Connection`. It is worth knowing which objects actually need closing: in a Spring application, `JdbcTemplate` and JPA manage connections for you, so manual closing is limited to things like `Files.lines`, `Stream` over I/O, HTTP response bodies, and files you open directly. A frequently missed case is a `Stream` returned from a repository method — Spring Data's `Stream` results hold a database cursor and must be closed, so they belong in a try-with-resources. Note that the suppressed exception is easy to lose in logs if you log only `getMessage()`; logging the throwable prints suppressed entries too.

**Practical backend example:** Closing in reverse order, and reading the suppressed cause:

```java
// resources closed in reverse order: rs, then ps, then connection
try (Connection connection = dataSource.getConnection();
     PreparedStatement ps = connection.prepareStatement("SELECT id FROM \"order\" WHERE status = ?")) {
    ps.setString(1, "PAID");
    try (ResultSet rs = ps.executeQuery()) {
        while (rs.next()) { ... }
    }
}

// Spring Data streaming results hold a cursor: close them
try (Stream<Order> orders = orderRepository.streamAllByStatus(OrderStatus.PAID)) {
    orders.forEach(this::export);
}

// suppression: the body's exception wins, close's exception is attached
try (var resource = new FailingResource()) {
    throw new IllegalStateException("primary failure");
} catch (Exception e) {
    log.error("failed: {} suppressed={}", e.getMessage(), Arrays.toString(e.getSuppressed()), e);
}
```

**Common follow-ups:**
- What if both the body and `close()` throw? The body's exception propagates; the close exception is added to its suppressed list.
- Can you use an existing variable? Yes, since Java 9, provided it is final or effectively final.
- Does Spring still need this? For managed resources no, but streaming repository results, file I/O and raw JDBC all still require it.

**Mistakes to avoid:** Closing inside the `try` body instead of using the construct; ignoring a streaming repository result's cursor; catching and logging only the message so suppressed exceptions vanish; assuming `finally` alone is equivalent.

**Production perspective:** Leaked connections and cursors manifest as pool exhaustion under load — requests queue and time out while the database looks idle. Because the leak accumulates, the failure typically appears hours after deployment, which makes the cause easy to misattribute.

**Related concepts covered:** AutoCloseable, suppressed exceptions, reverse close order, streaming result sets, connection pool exhaustion.

## Q011. What do final, finally and finalize mean in modern Java?

**Priority:** Important  
**Why interviewers ask it:** Three similar names with unrelated meanings, one of which is deprecated — it is a quick precision check.

**Interview-ready answer:** `final` is a modifier: a final variable cannot be reassigned, a final method cannot be overridden, a final class cannot be extended. It does not make an object immutable — a `final List` can still have elements added — but final fields do have a memory-model guarantee: correctly constructed objects publish their final fields safely to other threads. `finally` is the block that runs after try/catch regardless of outcome, used for cleanup, though try-with-resources is better for closeable resources. `finalize` was a method the garbage collector could call before reclaiming an object; it was unpredictable, harmful to performance, and is deprecated for removal — `Cleaner` or explicit `close()` is the modern approach. In practice I use `final` constantly, `finally` occasionally, and `finalize` never.

**In-depth explanation:** The final-field guarantee is genuinely useful: if an object's fields are final and the reference does not escape during construction, other threads observing the reference see fully initialised values without synchronisation, which is the basis of safe immutable value objects. `finally` has a sharp edge: a `return` or a thrown exception inside `finally` discards whatever the `try` block was returning or throwing, silently swallowing failures — most static analysers flag it. On `finalize`, the reasons for deprecation are worth knowing: finalisers run on an unspecified thread at an unspecified time, can resurrect objects, and delay reclamation by at least one GC cycle. `Cleaner` registers a cleanup action tied to reachability without those hazards, but even it is a backstop; deterministic `close()` in try-with-resources is the correct design.

**Practical backend example:** The useful one, the sharp edge, and the modern replacement:

```java
public final class Money {                 // final class: no subclass can break invariants
    private final long minorUnits;         // final fields: safely published to other threads
    private final String currency;
    public Money(long minorUnits, String currency) {
        this.minorUnits = minorUnits;
        this.currency = Objects.requireNonNull(currency);
    }
}

int broken() {
    try { return 1; }
    finally { return 2; }                  // returns 2 and discards the try result - never do this
}

// instead of finalize: deterministic close, with Cleaner only as a safety net
public class NativeBuffer implements AutoCloseable {
    private static final Cleaner CLEANER = Cleaner.create();
    private final Cleaner.Cleanable cleanable;
    public void close() { cleanable.clean(); }
}
```

**Common follow-ups:**
- Does `final` make an object immutable? No; it prevents reassignment of the variable, not mutation of the object.
- Can `finally` swallow an exception? Yes, if it returns or throws — a well-known source of hidden failures.
- What replaced `finalize`? Deterministic `close()` with try-with-resources, and `Cleaner` when a safety net is genuinely needed.

**Mistakes to avoid:** Claiming `final` gives immutability; returning from `finally`; relying on finalisers to release resources; assuming `System.gc()` makes any of this deterministic.

**Production perspective:** Marking value classes and their fields final is free defensive design: it documents intent, enables safe sharing across threads, and lets the JIT make stronger assumptions. Relying on finalisers, by contrast, has caused real outages by holding native resources far longer than expected.

**Related concepts covered:** Final field semantics, safe publication, try-with-resources, Cleaner, control-flow hazards.

## Q012. How do you make a class truly immutable?

**Priority:** Must Know  
**Why interviewers ask it:** Immutability is the cheapest concurrency and correctness tool, and "truly" hides the interesting details.

**Interview-ready answer:** Make the class final so behaviour cannot be overridden, make every field private and final, set them all in the constructor, and provide no method that changes state. The part people miss is deep immutability: if a field is a mutable object — a list, a date, an array — you must copy it on the way in and never hand out the internal reference on the way out, otherwise callers can mutate your "immutable" object from outside. Validate invariants in the constructor so an instance can never exist in an invalid state. Records give you most of this for free, but not deep immutability: a record component holding a `List` is still mutable unless you copy it in the compact constructor.

**In-depth explanation:** The payoff is that immutable objects are inherently thread-safe and can be shared, cached and used as map keys without defensive thinking. Final fields also carry the memory-model guarantee that other threads see fully constructed values, provided the object does not leak `this` during construction — for example by registering a listener in the constructor. `List.copyOf` is the concise way to copy and freeze in one step, and it rejects nulls; `Collections.unmodifiableList` wraps without copying, so the underlying list can still change beneath you. For "modification", provide `with`-style methods that return a new instance. The cost is allocation, which is usually irrelevant, but for very hot paths or very large structures a mutable builder used during construction and frozen afterwards is the standard compromise.

**Practical backend example:** Deep immutability with a record, including the copy step:

```java
public record Order(UUID id, Money total, List<OrderLine> lines, Instant createdAt) {
    public Order {                                      // compact constructor
        Objects.requireNonNull(id);
        lines = List.copyOf(lines);                     // defensive copy: caller's list is detached
        if (lines.isEmpty()) throw new IllegalArgumentException("an order needs at least one line");
    }
    public Order withLineAdded(OrderLine line) {        // "modify" by producing a new instance
        var updated = new ArrayList<>(lines);
        updated.add(line);
        return new Order(id, total.plus(line.amount()), updated, createdAt);
    }
}

List<OrderLine> caller = new ArrayList<>(List.of(line));
Order order = new Order(id, total, caller, now);
caller.add(otherLine);                                  // no effect: the record copied the list
```

**Common follow-ups:**
- Do records guarantee immutability? They give shallow immutability; mutable components must be copied in the compact constructor.
- Why copy on the way out too? Returning the internal collection lets a caller mutate your state; return an unmodifiable view or a copy.
- What is the memory-model benefit? Final fields are safely published, so other threads see fully initialised values without extra synchronisation.

**Mistakes to avoid:** Storing a caller's list directly; exposing an array from a getter; a setter "just for the framework"; leaking `this` from a constructor; treating `Collections.unmodifiableList` over a field you keep mutating as immutable.

**Production perspective:** Immutable domain values remove an entire class of concurrency bugs and make reasoning about caches straightforward — if the value cannot change, a cached copy cannot go stale by mutation. Where allocation genuinely matters, measure before trading that away.

**Related concepts covered:** Deep versus shallow immutability, defensive copying, safe publication, records, builder pattern, with-style updates.

## Q013. When are records suitable for backend DTOs, and when are they not?

**Priority:** Important  
**Why interviewers ask it:** Records are common in modern Java code, and knowing their limits is more useful than knowing the syntax.

**Interview-ready answer:** Records are an excellent fit for data carriers: request and response DTOs, value objects, query projections, event payloads. They give you a canonical constructor, accessors, `equals`, `hashCode` and `toString` from the component list, and the compact constructor is a natural place to validate. They are a poor fit for JPA entities, which need a no-argument constructor, non-final fields for proxying and dirty checking, and an identity that is not value-based. They are also awkward when you need partial construction, many optional fields or framework-mandated setters. Jackson supports records natively in recent versions, and Bean Validation annotations work on components, so for API DTOs they are usually the better default.

**In-depth explanation:** A record's `equals` is value-based over all components, which is right for DTOs and wrong for entities: two `Order` entities with the same field values are not the same order, and an entity's identity must survive field changes. The compact constructor runs before fields are assigned, so it is the place to normalise (trim, lowercase) and to copy mutable components. Records cannot extend a class, though they can implement interfaces, and they combine well with sealed interfaces for closed result hierarchies. For JSON, Jackson 2.12+ handles records including constructor binding, and adding `@JsonProperty` on components lets you keep wire names stable while renaming Java fields. Where a DTO has fifteen optional fields, a builder is friendlier than a fifteen-argument canonical constructor — that is a signal about the DTO's design as much as about records.

**Practical backend example:** Record DTO with validation and normalisation, versus an entity that should not be one:

```java
// good: API request DTO - validated, normalised, immutable
public record CreateOrderRequest(
        @NotBlank String customerReference,
        @NotEmpty List<@Valid OrderLineRequest> lines,
        @NotNull @Positive Long totalMinorUnits) {
    public CreateOrderRequest {
        customerReference = customerReference == null ? null : customerReference.trim();
        lines = lines == null ? List.of() : List.copyOf(lines);
    }
}

// good: projection from a query
public record CustomerRevenue(UUID customerId, String name, long netMinorUnits) {}

// not a record: JPA needs a no-arg constructor, mutable fields and identity-based equality
@Entity
public class Order {
    @Id @GeneratedValue private UUID id;
    private OrderStatus status;
    protected Order() { }                    // required by JPA
}
```

**Common follow-ups:**
- Why not use records for entities? JPA requires a no-argument constructor and mutable state for proxies and dirty checking, and entity identity is not value-based.
- Can records be validated? Yes; Bean Validation annotations on components work, and the compact constructor can enforce invariants directly.
- Can a record implement an interface? Yes, and sealed interface plus records is a clean way to model a closed set of results.

**Mistakes to avoid:** Mapping a record directly to a database table; assuming a record with a `List` component is deeply immutable; using records for objects with rich behaviour and lifecycle; exposing entity records over the API and coupling the wire format to the schema.

**Production perspective:** Records make the entity/DTO boundary easy to keep, which is what prevents schema changes leaking into your API and mass-assignment bugs leaking into your schema. That boundary costs a mapping layer and pays for itself the first time a column is renamed.

**Related concepts covered:** DTO versus entity, compact constructors, Jackson binding, Bean Validation, sealed hierarchies, projections.

## Q014. How should Optional be used at service boundaries?

**Priority:** Must Know  
**Why interviewers ask it:** `Optional` is widely misused, and the misuse patterns are easy to spot in an answer.

**Interview-ready answer:** `Optional` is designed as a return type for a method whose result may legitimately be absent — a lookup that finds nothing. I use it there, and I let the caller decide: `orElseThrow` for a mandatory resource, `map` to transform, `orElse` for a default. I avoid it as a field type or as a method parameter — it is not serialisable, it adds an allocation and a wrapper for no benefit, and an optional parameter is better expressed as an overload. I never call `get()` without checking, because that is just a `NoSuchElementException` waiting to happen. And absence is not the same as an error: a missing optional record is `Optional.empty()`, whereas a corrupt one should throw.

**In-depth explanation:** Spring Data repositories return `Optional` from `findById` precisely so the missing case is explicit at the type level, and `orElseThrow(() -> new OrderNotFoundException(id))` turns it into a domain exception that the error handler maps to 404. Chaining reads well — `repository.findById(id).map(Mapper::toDto).orElseThrow(...)` — but nested optionals or `Optional<List>` are smells: an empty list already expresses "nothing found". Serialisation is a practical constraint: Jackson can be configured to handle `Optional` fields, but the resulting JSON contract is confusing, so DTOs should use nullable fields or omit them. In streams, `flatMap(Optional::stream)` (Java 9+) is the idiomatic way to drop empties. As a rule of thumb: `Optional` at the boundary of a lookup, plain types everywhere else.

**Practical backend example:** Idiomatic use, and the patterns to avoid:

```java
// repository returns Optional; the caller chooses the policy
public OrderDto get(UUID id) {
    return orderRepository.findById(id)
            .map(OrderDto::from)
            .orElseThrow(() -> new OrderNotFoundException(id));      // mandatory -> 404
}

public ShippingPreference preferenceFor(UUID customerId) {
    return preferences.findByCustomerId(customerId)
            .orElse(ShippingPreference.DEFAULT);                     // optional -> default
}

// collecting present values from a stream
List<Order> found = ids.stream()
        .map(orderRepository::findById)
        .flatMap(Optional::stream)                                   // Java 9+
        .toList();

// avoid: Optional fields, Optional parameters, and unchecked get()
// record Dto(Optional<String> note) {}          // not serialisation-friendly
// void save(Optional<Order> order) {}           // use an overload instead
// Order o = repository.findById(id).get();      // throws NoSuchElementException
```

**Common follow-ups:**
- Should an `Optional` field appear in a DTO? No; use a nullable field or omit it. `Optional` is not designed for serialisation or for state.
- What about `Optional<List<T>>`? Redundant — an empty list already means "none".
- `orElse` or `orElseGet`? `orElseGet` when the default is expensive, because `orElse` evaluates its argument eagerly even when a value is present.

**Mistakes to avoid:** `get()` without `isPresent`; `Optional` parameters; `isPresent`/`get` pairs where `map`/`orElseThrow` reads better; using `Optional` to signal errors rather than absence.

**Production perspective:** The value is that "not found" becomes a compile-time consideration rather than a null that fails three frames away. Combined with a typed not-found exception and a single error handler, it is what makes 404 versus 500 correct across an API without per-endpoint effort.

**Related concepts covered:** Null-safety, Spring Data lookups, stream flatMap, serialisation constraints, eager versus lazy defaults.

## Q015. What is the difference between overloading and overriding?

**Priority:** Important  
**Why interviewers ask it:** It separates compile-time from runtime dispatch, which explains several surprising bugs.

**Interview-ready answer:** Overloading is multiple methods with the same name and different parameter lists in the same class; the compiler picks one from the static types of the arguments, so it is resolved at compile time. Overriding is a subclass replacing a superclass method with the same signature; the JVM picks the implementation from the object's runtime type, which is dynamic dispatch and the basis of polymorphism. The practical consequence is that overloading with a `null` literal or with an `Object` versus a specific type can bind to a method you did not expect, and that overload choice does not change just because the runtime type is a subclass. Overriding has rules: the signature must match, the return type may be covariant, access cannot be narrowed, and a checked exception cannot be broadened. I use `@Override` so the compiler catches a typo that would otherwise create an accidental overload.

**In-depth explanation:** Overload resolution follows a specificity order — exact match, widening, boxing, varargs — which is why `remove(int)` and `remove(Object)` on `List` behave so differently: `list.remove(1)` removes the element at index 1, while `list.remove(Integer.valueOf(1))` removes the value. A `null` argument binds to the most specific applicable type and is ambiguous when two unrelated types apply, which is a compile error. Overriding is also where the private/static distinction bites: private and static methods are not overridden, they are hidden, so calling a static method through a reference uses the reference's static type. For substitutability, an override must honour the original contract, and if you need to reuse the parent's behaviour, `super.method()` makes that explicit rather than implicit.

**Practical backend example:** The classic overload surprise and a correct override:

```java
List<Integer> ids = new ArrayList<>(List.of(10, 20, 30));
ids.remove(1);                       // overload on int: removes INDEX 1 -> [10, 30]
ids.remove(Integer.valueOf(10));     // overload on Object: removes the VALUE 10

class NotificationService {
    void send(Object payload) { ... }
    void send(String message) { ... }
}
Object payload = "hello";
service.send(payload);               // binds to send(Object): chosen from the STATIC type

class EmailGateway implements NotificationGateway {
    @Override                        // compiler verifies this really overrides something
    public DeliveryResult send(Notification notification) { ... }   // covariant return allowed
}
```

**Common follow-ups:**
- Can a static method be overridden? No; it is hidden. Dispatch uses the reference's static type.
- Can an override change the return type? Yes, to a covariant (more specific) type, but not to an unrelated one.
- Why is `@Override` recommended? It turns a misspelled or mismatched signature into a compile error instead of a silent new method.

**Mistakes to avoid:** Overloading with types that differ only by boxing or by `Object`; relying on runtime type to pick an overload; narrowing access or broadening checked exceptions in an override; omitting `@Override`.

**Production perspective:** Overload ambiguity causes bugs that are invisible in review because the call site looks obviously correct — the `List.remove` case has caused real data bugs. Distinct method names (`removeAt`, `removeValue`) are often better than clever overloading in application code.

**Related concepts covered:** Static versus dynamic dispatch, overload resolution rules, covariant returns, method hiding, `@Override` safety.

## Q016. How do access modifiers and packages shape a module's API?

**Priority:** Important  
**Why interviewers ask it:** Visibility is an architectural tool, and most developers use only `public` and `private`.

**Interview-ready answer:** The four levels are private (class only), package-private (the default, same package), protected (package plus subclasses), and public (everywhere). Used deliberately they define a module's surface: I put a feature's classes in one package, keep helpers and implementation classes package-private, and expose only the few types other features need. That makes the public surface small enough to reason about and refactor. Package structure matters as much as the keywords — layer-by-layer packages (`controller`, `service`, `repository`) force almost everything to be public because collaborators live in different packages, whereas feature packages (`orders`, `payments`) let internals stay package-private. The Java module system can enforce this at the JAR level with exported packages, but most Spring applications rely on package discipline plus a build-time check.

**In-depth explanation:** `protected` is often misunderstood: it allows access from a subclass, but through a reference of the subclass type, not to arbitrary instances of the parent from another package. Spring adds practical constraints: proxied methods must be visible to the proxy, so `@Transactional` on a private method does nothing at all with the default proxying, and CGLIB subclass proxies cannot override `final` or private methods. That is a framework constraint, not a language rule, and it is a reason to keep proxied methods public or at least package-private rather than making everything public reflexively. For enforcing boundaries over time, ArchUnit tests ("no class in `orders.internal` may be accessed from `payments`") turn conventions into failing builds, which is the only mechanism that survives team growth.

**Practical backend example:** Feature packaging with a narrow public surface:

```text
com.example.orders
├── OrderService.java          (public - the feature's API)
├── OrderController.java       (public - web entry point)
├── Order.java                 (public - domain type used by the API)
└── internal
    ├── OrderTotalsCalculator.java   (package-private - implementation detail)
    └── OrderRepository.java         (package-private - nobody outside orders needs it)
```

```java
class OrderTotalsCalculator {           // package-private: invisible outside com.example.orders.internal
    Money calculate(List<OrderLine> lines) { ... }
}

// ArchUnit: make the boundary a build failure, not a convention
@ArchTest
static final ArchRule internals_are_not_used_elsewhere = noClasses()
        .that().resideOutsideOfPackage("com.example.orders..")
        .should().accessClassesThat().resideInAPackage("com.example.orders.internal..");
```

**Common follow-ups:**
- What is the default modifier for a top-level class? Package-private; only members can be private.
- Is `protected` effectively public? No; it grants subclass access through the subclass's own type, plus package access.
- Why can visibility break Spring proxies? Proxies wrap or subclass the bean, so private and final methods are not intercepted — `@Transactional` on a private method silently does nothing.

**Mistakes to avoid:** Making everything public because the test is in another package; treating `protected` as a documentation hint; layer-only packaging that defeats package-private entirely; relying on comments to mark "internal" classes.

**Production perspective:** A small public surface is what makes refactoring safe: you can change an internal class without auditing the whole codebase. Teams that enforce boundaries with automated rules keep that property; teams that rely on conventions lose it within a year.

**Related concepts covered:** Package-private design, feature packaging, Spring proxy visibility rules, ArchUnit enforcement, JPMS exports.

## Q017. What happens during class loading and static initialization?

**Priority:** Important  
**Why interviewers ask it:** Startup failures and mysterious `NoClassDefFoundError`s come from this area.

**Interview-ready answer:** A class goes through loading (finding and reading the bytecode), linking (verification, preparation of static fields with default values, and resolution), and initialisation (running static field initialisers and static blocks in textual order, after the superclass is initialised). Initialisation is lazy and happens on first active use — creating an instance, calling a static method, reading a non-constant static field. Compile-time constants are inlined by the compiler, so reading one does not trigger initialisation at all. The operational detail that matters: if a static initialiser throws, you get `ExceptionInInitializerError`, the class is marked erroneous, and every later use throws `NoClassDefFoundError` — which is confusing because the second error names a class that clearly exists. So I keep static initialisation trivial and put anything that can fail into managed startup code.

**In-depth explanation:** Class identity is the pair (class loader, binary name), so the same class loaded by two loaders produces two distinct types and a `ClassCastException` that looks impossible — a real issue in application servers and plugin systems, less so in a plain Spring Boot fat jar. Static state is per class loader, which also means "singletons" are not global in a container with several loaders. In a Spring application, prefer a `@Bean` or `@PostConstruct` over a static block for anything that reads configuration or performs I/O: the container controls ordering, failures are reported with context, and the work is testable. Static initialisers that call network services are a known cause of hangs at startup with no useful log line, because they run before most logging is configured.

**Practical backend example:** The failure mode and the managed alternative:

```java
class Rules {
    // dangerous: I/O in a static initialiser
    static final List<Rule> RULES = fetchRemoteRules();     // throws -> ExceptionInInitializerError
    static final int MAX_RETRIES = 3;                       // compile-time constant: inlined by callers
}

// later, somewhere unrelated:
Rules.RULES.size();   // NoClassDefFoundError: Could not initialize class Rules  (the real cause is gone)
```

```java
// managed: ordering, failure reporting and testability handled by the container
@Configuration
class RuleConfiguration {
    @Bean
    RuleSet ruleSet(RuleClient client) {          // failure surfaces as a clear startup error
        return client.fetchRules();
    }
}
```

**Common follow-ups:**
- Do static fields belong to instances? No; they belong to the class as loaded by a particular class loader.
- What happens after a static initialiser fails? The class is unusable for that loader; subsequent access throws `NoClassDefFoundError`.
- Why can two "identical" classes be incompatible? Class identity includes the loader, so different loaders yield different types.

**Mistakes to avoid:** Network or file I/O in static blocks; assuming `static final` always means compile-time constant; relying on static mutable state for caching in a container; catching `ExceptionInInitializerError` instead of fixing the cause.

**Production perspective:** Startup failures need a visible cause and a deployment policy — a container that crash-loops with `NoClassDefFoundError` tells you nothing about the original exception unless it was logged when it first happened. Moving initialisation into beans makes the first failure the one you see.

**Related concepts covered:** Loading, linking and initialisation, lazy initialisation, constant inlining, class loaders and identity, Spring startup lifecycle.

## Q018. How do primitives, wrappers and autoboxing create bugs?

**Priority:** Must Know  
**Why interviewers ask it:** Boxing bugs are subtle, common, and produce wrong results rather than exceptions.

**Interview-ready answer:** Primitives hold values and cannot be null; wrappers are objects, so they can be null and have identity. Autoboxing converts between them automatically, and that convenience creates three traps. First, unboxing a null throws `NullPointerException` at a line that looks like arithmetic — typical when a nullable database column maps to `Long` and you assign it to a `long`. Second, `==` on wrappers compares references: it appears to work for small values because the JVM caches `Integer` between -128 and 127, then fails for 128 and above, so you must use `equals`. Third, boxing in a loop allocates objects and is measurably slower than primitives. My rules are: primitives for arithmetic and internal state, wrappers only where null is meaningful, `equals` for wrapper comparison, and explicit null handling when mapping nullable columns.

**In-depth explanation:** The `Integer` cache is specified for -128..127 (its upper bound is adjustable with `-XX:AutoBoxCacheMax`), and `Boolean`, `Byte`, `Short`, `Character` and `Long` have similar caching for small values — which is exactly why the bug is intermittent: tests use small IDs, production uses large ones. Ternary expressions have a nasty variant: mixing a primitive and a wrapper in the two branches forces unboxing of the wrapper, so `flag ? 1 : nullableInteger` can throw even when the chosen branch is the primitive. In collections everything is boxed, so `Map<String, Integer>` counters allocate per increment; `merge` or `computeIfAbsent` with `AtomicInteger`, or a primitive-specialised structure, avoids that where it matters. `Optional.orElse(null)` assigned to a primitive is another quiet unboxing hazard.

**Practical backend example:** All three traps in code you might actually write:

```java
Integer a = 127, b = 127;
Integer c = 128, d = 128;
System.out.println(a == b);          // true  - cached instances
System.out.println(c == d);          // false - different objects (use equals)
System.out.println(c.equals(d));     // true

// nullable column -> primitive: NPE at the assignment, not at the query
Long discountId = resultSet.getObject("discount_id", Long.class);   // may be null
long id = discountId;                                               // NullPointerException

// ternary unboxing: throws even though the int branch is selected
Integer nullable = null;
int value = true ? 1 : nullable;     // compiler unboxes both branches -> NPE risk

// safe mapping
long safeId = discountId != null ? discountId : 0L;
```

**Common follow-ups:**
- Why does `==` sometimes work on `Integer`? The small-value cache returns the same object; outside that range you get distinct objects.
- Where does the `NullPointerException` come from in arithmetic? Implicit unboxing of a null wrapper.
- When are wrappers the right choice? When absence is meaningful — a nullable column, an unset filter — otherwise prefer primitives.

**Mistakes to avoid:** `==` on wrappers; declaring counters as `Integer`; mixing primitives and wrappers in ternaries; mapping nullable columns to primitives; boxing inside hot loops.

**Production perspective:** These bugs pass tests with small fixtures and fail with production-sized identifiers, which makes them a classic "works in staging" incident. A static analysis rule for wrapper `==` comparisons catches most of them automatically.

**Related concepts covered:** Integer cache, unboxing NPEs, ternary type promotion, collection boxing costs, nullable column mapping.

## Q019. How would you handle dates, times and time zones in an API?

**Priority:** Must Know  
**Why interviewers ask it:** Time handling is where real systems quietly produce wrong data, and the correct approach is a set of concrete decisions.

**Interview-ready answer:** I store and transmit instants in UTC, using `Instant` in Java and `timestamptz` in PostgreSQL, and format them as ISO-8601 with an offset — `2026-03-14T09:15:30Z`. Conversion to a local zone happens at the edge, for display, using the user's zone rather than the server's default. I choose the type by meaning: `Instant` for a moment that happened, `LocalDate` for a calendar date such as a birthday or an invoice date, `LocalDateTime` only with a separate zone for future scheduled events, and `ZonedDateTime` when the zone is part of the data. I never use the legacy `Date` and `Calendar`, and I never rely on the JVM default zone — I inject a `Clock`, which also makes time testable.

**In-depth explanation:** Future events are the case that catches people: a meeting scheduled for "09:00 Europe/Berlin next March" must be stored as local time plus zone, because if a government changes the daylight-saving rules the stored UTC instant would now be the wrong local time. Recurring schedules have the same property. Daylight-saving transitions also make some local times nonexistent or ambiguous, and `ZonedDateTime` resolves them with defined rules rather than throwing — worth knowing when you compute "the same time tomorrow". Storage matters too: PostgreSQL `timestamptz` stores a UTC instant and converts on input and output, while `timestamp` stores wall-clock text with no zone, which is almost never what you want for events. Finally, durations and periods differ: `Duration` is exact time, `Period` is calendar-aware, and adding one month is not adding thirty days.

**Practical backend example:** Types, storage, and an injected clock:

```java
@Entity
public class Order {
    private Instant createdAt;            // timestamptz in PostgreSQL: a moment in time
    private LocalDate invoiceDate;        // a calendar date: no zone, no time
}

@Entity
public class ScheduledMeeting {
    private LocalDateTime localStart;     // future event: store local time...
    private String zoneId;                // ...plus the zone, so DST rule changes stay correct
    public Instant startInstant() {
        return localStart.atZone(ZoneId.of(zoneId)).toInstant();
    }
}

@Service
public class OrderService {
    private final Clock clock;            // injected: never Instant.now() directly
    public Order create(CreateOrderRequest request) {
        return new Order(UUID.randomUUID(), Instant.now(clock));
    }
}
```

```json
{ "createdAt": "2026-03-14T09:15:30Z", "invoiceDate": "2026-03-14" }
```

**Common follow-ups:**
- Why store future events as local time plus zone? Because time-zone rules change; the intended local time is the invariant, not the derived UTC instant.
- `timestamp` or `timestamptz` in PostgreSQL? `timestamptz` for instants; `timestamp` has no zone and silently reinterprets values.
- Why inject a `Clock`? It removes the hidden dependency on the system clock and makes boundary conditions testable.

**Mistakes to avoid:** Using `Date`/`SimpleDateFormat` (also not thread-safe); relying on the server's default zone; storing local times for events; assuming every day has 24 hours; formatting with a locale-dependent pattern in an API.

**Production perspective:** Time bugs cluster around midnight, month ends, daylight-saving transitions and year boundaries — exactly when reports are produced and people notice. Pin the JVM and container time zone to UTC, log timestamps with offsets, and test the transition dates explicitly.

**Related concepts covered:** java.time type selection, UTC storage, PostgreSQL timestamptz, DST transitions, Clock injection, ISO-8601 formatting.

## Q020. How should BigDecimal be used for money?

**Priority:** Must Know  
**Why interviewers ask it:** Money errors are visible to customers and auditors, and the correct approach has specific rules.

**Interview-ready answer:** Never use `double` or `float` for money: binary floating point cannot represent 0.1 exactly, so sums drift. Use `BigDecimal` constructed from a `String` or from integer minor units — `new BigDecimal(0.1)` captures the binary error, `new BigDecimal("0.1")` does not. `BigDecimal` is immutable, so every operation returns a new value, and division requires an explicit scale and `RoundingMode` or it throws `ArithmeticException` on a non-terminating result. Comparison must use `compareTo`, because `equals` also compares scale, so `1.0` and `1.00` are not equal. The alternative many systems use is to store integer minor units — cents — in a `long` and only format for display; that removes rounding ambiguity entirely and is attractive for high-volume ledgers. Either way, currency travels with the amount, and rounding is decided by the business, not left to a default.

**In-depth explanation:** Rounding policy deserves explicit thought: `RoundingMode.HALF_UP` matches common commercial expectations, while `HALF_EVEN` (banker's rounding) reduces cumulative bias across many operations and is required in some domains. The order of operations matters for taxes and discounts — rounding each line then summing gives a different total from summing then rounding — so the rule must be written down and tested. In PostgreSQL, `numeric(19,4)` maps to `BigDecimal` without loss, while `double precision` reintroduces the problem at the storage layer. In JSON, serialising a `BigDecimal` as a number can lose precision in JavaScript clients, so many APIs send a string, or send integer minor units plus a currency code. Finally, a `Money` value object carrying amount and currency prevents the two classic bugs: adding different currencies, and passing a raw number where a currency-aware value belongs.

**Practical backend example:** Construction, division, comparison and a value object:

```java
BigDecimal wrong = new BigDecimal(0.1);           // 0.1000000000000000055511151231257827...
BigDecimal right = new BigDecimal("0.1");         // exactly 0.1
BigDecimal fromCents = BigDecimal.valueOf(1999, 2);  // 19.99 without string parsing

BigDecimal share = total.divide(new BigDecimal("3"), 2, RoundingMode.HALF_UP);  // scale required

new BigDecimal("1.0").equals(new BigDecimal("1.00"));      // false - scale differs
new BigDecimal("1.0").compareTo(new BigDecimal("1.00"));   // 0 - use this

public record Money(long minorUnits, Currency currency) {      // integer minor units
    public Money plus(Money other) {
        if (!currency.equals(other.currency)) throw new IllegalArgumentException("currency mismatch");
        return new Money(Math.addExact(minorUnits, other.minorUnits), currency);   // overflow-safe
    }
    public BigDecimal toAmount() {
        return BigDecimal.valueOf(minorUnits, currency.getDefaultFractionDigits());
    }
}
```

```sql
-- storage: exact, never double precision
ALTER TABLE "order" ADD COLUMN total numeric(19,4) NOT NULL;
```

**Common follow-ups:**
- Why is `new BigDecimal(0.1)` wrong? The `double` argument already carries binary error, which `BigDecimal` faithfully preserves.
- Why does `equals` surprise people? It compares scale as well as value; `compareTo` compares numeric value only.
- Minor units or `BigDecimal`? Minor units avoid rounding ambiguity and are convenient for ledgers; `BigDecimal` is better when you need fractional-cent intermediate results such as tax rates.

**Mistakes to avoid:** `double` for money anywhere in the path, including JSON and the database; dividing without a scale and rounding mode; `equals` for amount comparison; mixing currencies silently; rounding in a different order from the specification.

**Production perspective:** Money discrepancies get escalated, not triaged — a one-cent difference in a daily report triggers an investigation. Write the rounding and ordering rules down, test them with known totals, and keep amounts exact end to end, including the JSON representation.

**Related concepts covered:** Floating-point representation, rounding modes, scale versus value, numeric storage types, Money value objects, JSON precision.

## Q021. When should you use enums rather than strings or booleans?

**Priority:** Important  
**Why interviewers ask it:** Enums are a cheap way to make invalid states unrepresentable, and their persistence trade-offs are practical knowledge.

**Interview-ready answer:** I use an enum whenever a value comes from a small, known, closed set — order status, payment method, channel. The benefits are compile-time checking, exhaustive `switch` handling, no typos, and a natural place to attach behaviour or metadata to each constant. Strings for the same purpose invite typos and inconsistent casing, and require validation everywhere. Multiple booleans are worse: three flags imply eight states when only three are legal, and nothing prevents an impossible combination. The one place to be careful is persistence and the wire format: I store enums as strings (`@Enumerated(EnumType.STRING)`), never as ordinals, because ordinals break the moment someone reorders or inserts a constant.

**In-depth explanation:** Enums can carry state and behaviour — a `PaymentMethod` can know whether it supports refunds — which keeps per-constant logic next to the constant instead of in a scattered `switch`. In Java 17, an exhaustive `switch` over an enum in expression form does not need a `default` branch, so adding a constant produces a compile error at every place that must handle it: that is a feature, and adding a `default` throws it away. Across service boundaries, enums need a tolerant-reader policy: a consumer built before a new constant existed must not crash on it, so deserialisation should map unknown values to a defined fallback rather than failing. For database storage, a string column with a check constraint is the common pairing; `@Enumerated(EnumType.ORDINAL)` is the default in JPA when you forget the annotation, which is precisely the dangerous choice.

**Practical backend example:** Behaviour on the constant, safe persistence, tolerant deserialisation:

```java
public enum PaymentMethod {
    CARD(true), BANK_TRANSFER(true), STORE_CREDIT(false);

    private final boolean refundable;
    PaymentMethod(boolean refundable) { this.refundable = refundable; }
    public boolean isRefundable() { return refundable; }        // behaviour lives with the constant
}

@Entity
public class Payment {
    @Enumerated(EnumType.STRING)                                 // never ORDINAL
    @Column(nullable = false, length = 32)
    private PaymentMethod method;
}

// exhaustive switch: adding a constant becomes a compile error here
String label = switch (order.status()) {
    case NEW -> "Awaiting payment";
    case PAID -> "Paid";
    case CANCELLED -> "Cancelled";
};      // no default: the compiler enforces completeness

// tolerant reading at the boundary
@JsonCreator
static PaymentMethod fromWire(String value) {
    return Arrays.stream(values()).filter(m -> m.name().equalsIgnoreCase(value))
                 .findFirst().orElse(UNKNOWN);
}
```

**Common follow-ups:**
- Why store the name rather than the ordinal? Ordinals depend on declaration order, so reordering or inserting a constant silently corrupts existing rows.
- What happens when a producer adds a constant? Consumers must tolerate unknown values — map to a fallback instead of throwing.
- When is an enum the wrong choice? When the set is open or configurable at runtime, such as user-defined categories; use a reference table instead.

**Mistakes to avoid:** Ordinal persistence; parsing enums with `valueOf` on untrusted input without catching `IllegalArgumentException`; adding a `default` branch that hides missing cases; several booleans representing one state machine.

**Production perspective:** Enum changes are schema and contract changes. Adding a constant is usually safe if consumers are tolerant; removing or renaming one requires a migration on both sides, so treat the constant name as a published value.

**Related concepts covered:** Closed sets, exhaustive switch, enum persistence, tolerant readers, state modelling, check constraints.

## Q022. What does a sealed hierarchy buy you in Java 17?

**Priority:** Bonus  
**Why interviewers ask it:** It is a modern language feature whose value shows up in domain modelling, not syntax.

**Interview-ready answer:** A sealed interface or class declares exactly which types may implement or extend it, using `permits`, and every permitted subtype must be `final`, `sealed` or explicitly `non-sealed`. The payoff is a closed set the compiler knows about: a `switch` over a sealed type can be checked for exhaustiveness, so adding a new subtype makes every incomplete `switch` fail to compile instead of falling into a `default` branch at runtime. That makes it a good fit for modelling results and domain events — a `PaymentResult` that is either `Approved`, `Declined` or `Pending`, each a record with its own data. Compared with an enum, sealed types carry per-case data; compared with an open interface, you keep control over the set.

**In-depth explanation:** Sealed types plus records plus pattern matching form a coherent trio for algebraic-style modelling: the sealed interface names the choices, the records carry each choice's payload, and pattern matching in `switch` destructures them. In Java 17 pattern matching for `switch` is a preview feature; it became standard in Java 21, so a book targeting both should be explicit about which version a snippet requires. Permitted subtypes must be in the same module, or the same package for the unnamed module, which is also a packaging decision. The alternative — an interface with a `type` field and casts — loses both exhaustiveness and clarity. Where the set genuinely needs to be open for plugins, sealing is the wrong tool.

**Practical backend example:** A closed result type with per-case data (exhaustive `switch` shown in Java 21 form):

```java
public sealed interface PaymentResult permits Approved, Declined, Pending {}

public record Approved(String receiptId, Money captured)     implements PaymentResult {}
public record Declined(String reasonCode, boolean retryable) implements PaymentResult {}
public record Pending(String providerReference, Duration retryAfter) implements PaymentResult {}

// Java 21: exhaustive, no default branch needed; adding a case breaks compilation here
String describe(PaymentResult result) {
    return switch (result) {
        case Approved a -> "captured " + a.captured();
        case Declined d -> "declined: " + d.reasonCode();
        case Pending p  -> "pending, retry after " + p.retryAfter();
    };
}
```

**Common follow-ups:**
- Why not an enum? Enums cannot carry different data per constant; sealed records can.
- What must permitted subtypes declare? Each must be `final`, `sealed` or `non-sealed`, and live in the same module or package.
- Is pattern matching for `switch` available in 17? As a preview; it is standard from Java 21, so check the target version before relying on it.

**Mistakes to avoid:** Sealing a type that genuinely needs external implementations; adding a `default` branch and losing exhaustiveness checking; assuming Java 17 supports the full Java 21 pattern-matching syntax.

**Production perspective:** The practical benefit is that adding a new case — a new payment outcome — produces compile errors at exactly the places that must handle it, instead of a runtime surprise in one forgotten branch. That is valuable in code that evolves across teams.

**Related concepts covered:** Algebraic data modelling, exhaustive switch, records, pattern matching, Java version differences.

## Q023. How do switch expressions and pattern matching differ across Java 17 and 21?

**Priority:** Important  
**Why interviewers ask it:** Version precision matters when a team is migrating, and vague answers signal second-hand knowledge.

**Interview-ready answer:** Switch expressions with arrow labels and `yield` are standard from Java 14, so they are fully available in 17: they return a value, do not fall through, and must be exhaustive for enums and sealed types. Pattern matching for `instanceof` is also standard in 16, so `if (o instanceof Order order)` binds the variable directly. What changed in Java 21 is that pattern matching for `switch` became standard — matching on type patterns with guards (`case Order o when o.total().isPositive()`) — along with record patterns for destructuring. The two had different timelines: pattern matching for `switch` first previewed in 17, record patterns only from 19, and both were finalised in 21. In a Java 17 codebase I therefore use switch expressions and `instanceof` patterns freely, but type patterns in `switch` still require preview flags; on 21 I can use the full set.

**In-depth explanation:** Beyond syntax, the semantics are worth knowing: arrow labels eliminate accidental fall-through, and a switch expression over an enum or sealed type that covers all cases needs no `default`, which is what makes new cases a compile error. When the selector can be null, classic `switch` throws `NullPointerException`; Java 21 allows an explicit `case null` so the handling is visible rather than accidental. Record patterns in 21 destructure nested data in one line, which reads far better than a chain of accessors. The migration angle matters in interviews: knowing that a preview feature requires `--enable-preview` and produces class files tied to that exact JDK version explains why teams avoid previews in production.

**Practical backend example:** What compiles where:

```java
// Java 17 (standard): switch expression + instanceof pattern
int retryDelaySeconds = switch (status) {
    case NEW, PENDING -> 5;
    case PAID -> 0;
    case CANCELLED -> {
        audit.record(status);
        yield -1;                                    // yield returns a value from a block
    }
};

if (event instanceof PaymentEvent payment && payment.amount().isPositive()) {
    ledger.record(payment);                          // binding variable, standard since 16
}

// Java 21 (standard): type patterns in switch, guards, record patterns, case null
String describe(Object event) {
    return switch (event) {
        case null -> "no event";
        case PaymentEvent(var id, Money amount) when amount.isPositive() -> "payment " + id;
        case PaymentEvent p -> "non-positive payment " + p.id();
        case RefundEvent r  -> "refund " + r.id();
        default -> "unknown";
    };
}
```

**Common follow-ups:**
- Which parts are not standard in 17? Pattern matching for `switch` is preview there; record patterns do not exist at all until their 19 preview. Switch expressions and `instanceof` patterns are standard in 17.
- What happens with a null selector? Classic `switch` throws; Java 21 lets you write `case null` explicitly.
- Why avoid preview features in production? They require `--enable-preview`, can change between releases, and tie class files to one JDK version.

**Mistakes to avoid:** Claiming Java 17 has full pattern matching for `switch`; adding `default` to an exhaustive sealed switch; assuming arrow labels fall through; using preview features in a production build.

**Production perspective:** These features reduce boilerplate in mapping and dispatch code, which is where bugs hide. During a migration from 17 to 21, they are also a good early win: switching a visitor-style chain to a pattern `switch` usually removes code and adds exhaustiveness checking.

**Related concepts covered:** Switch expressions, instanceof patterns, record patterns, guarded patterns, preview feature policy, JDK migration.

## Q024. What do annotations do, and when is reflection appropriate?

**Priority:** Important  
**Why interviewers ask it:** Spring is built on both, and understanding the mechanics separates users of the framework from people who can debug it.

**Interview-ready answer:** Annotations are metadata attached to code elements. They do nothing by themselves — something has to read them: the compiler, an annotation processor at build time, or a framework at runtime through reflection, which requires `RetentionPolicy.RUNTIME`. Spring reads annotations at startup to build bean definitions, wire dependencies and create proxies, so the cost is mostly paid once rather than per request. Reflection is appropriate for framework-level work — mapping, serialisation, dependency injection, test tooling — where you genuinely cannot know the types at compile time. In application code it is rarely the right answer: it bypasses compile-time checking, breaks refactoring and IDE navigation, is slower, and can fail at runtime in ways the compiler would have caught. If I find myself reflecting in business logic, I look for a design that uses an interface or a map of handlers instead.

**In-depth explanation:** Retention policies matter: `SOURCE` annotations vanish after compilation (`@Override`), `CLASS` is retained in the class file but not loaded, and `RUNTIME` is visible to reflection. Meta-annotations compose — Spring's `@RestController` is itself annotated with `@Controller` and `@ResponseBody`, which is why the framework searches annotation hierarchies rather than exact types. Reflection has real costs beyond speed: it defeats dead-code analysis, complicates native compilation with GraalVM (which needs explicit reflection configuration or build-time hints), and can throw `InaccessibleObjectException` under the module system when accessing non-exported internals. `MethodHandle` and `VarHandle` are faster alternatives for repeated access, and annotation processors move work to compile time entirely — which is how Lombok, MapStruct and Micronaut avoid runtime reflection.

**Practical backend example:** A custom runtime annotation and the reflection that reads it:

```java
@Retention(RetentionPolicy.RUNTIME)          // required for runtime reflection
@Target(ElementType.METHOD)
public @interface AuditLogged {
    String action();
}

@Service
public class OrderService {
    @AuditLogged(action = "ORDER_CANCELLED")
    public void cancel(UUID orderId) { ... }
}

// a Spring AOP aspect reads the metadata - framework-level use of reflection
@Aspect @Component
public class AuditAspect {
    @Around("@annotation(audited)")
    public Object record(ProceedingJoinPoint joinPoint, AuditLogged audited) throws Throwable {
        Object result = joinPoint.proceed();
        auditLog.write(audited.action(), SecurityContextHolder.getContext().getAuthentication());
        return result;
    }
}
```

**Common follow-ups:**
- Why must retention be RUNTIME? Otherwise the annotation is discarded and reflection cannot see it.
- Why is reflection discouraged in business code? It removes compile-time safety and refactoring support, and it is slower than a direct call.
- What is the GraalVM implication? Reflective access needs explicit configuration or hints, or the native image fails at runtime.

**Mistakes to avoid:** Assuming an annotation has behaviour on its own; using reflection to reach private fields in application code; forgetting `@Retention`; relying on reflection in code destined for a native image without registering it.

**Production perspective:** Reflection-heavy startup is a measurable part of a Spring Boot application's boot time, which matters for autoscaling and serverless deployments. Compile-time approaches — annotation processors, explicit configuration — trade a little flexibility for faster, more predictable startup.

**Related concepts covered:** Retention policies, meta-annotations, Spring AOP, MethodHandles, annotation processors, GraalVM native images.

## Q025. How would you design a value object for an email address?

**Priority:** Important  
**Why interviewers ask it:** It is a small design exercise that exposes validation, normalisation, immutability and boundary thinking all at once.

**Interview-ready answer:** I make it an immutable record with a single `String` component, validated and normalised in the compact constructor so an instance cannot exist in an invalid state — trim, lowercase the domain part, reject blanks and anything failing a pragmatic format check. Then the type replaces `String` in signatures: `sendWelcome(Email email)` cannot be called with a phone number, which is the real value. I keep validation pragmatic rather than attempting a fully RFC-compliant regex, because the only definitive validation is sending a message and confirming receipt. For persistence I map it with an attribute converter or store the string and reconstruct, and for equality I decide explicitly whether comparison is case-insensitive — normalising on construction makes that decision once.

**In-depth explanation:** Normalisation deserves care: the domain is case-insensitive, but the local part is technically case-sensitive per the standard, even though most providers treat it as insensitive. Lowercasing everything is a common product decision, and it must be applied consistently, including in the database's unique index, or duplicates slip in. `toLowerCase(Locale.ROOT)` avoids the Turkish dotless-i problem that `toLowerCase()` with a default locale can introduce. Validation belongs in the constructor so every path — API, import job, message consumer — gets the same rule; a Bean Validation `@Email` annotation on a DTO field is a good outer layer but does not protect the domain. The wider pattern is primitive obsession: replacing bare strings and longs with small types eliminates a class of argument-order bugs that the compiler otherwise cannot see.

**Practical backend example:** The value object and its persistence:

```java
public record Email(String value) {
    private static final Pattern PATTERN =
            Pattern.compile("^[^@\\s]+@[^@\\s.]+(\\.[^@\\s.]+)+$");   // pragmatic, not RFC-complete

    public Email {
        Objects.requireNonNull(value, "email is required");
        value = value.trim().toLowerCase(Locale.ROOT);                 // normalise once, here
        if (value.length() > 254 || !PATTERN.matcher(value).matches()) {
            throw new IllegalArgumentException("invalid email address");
        }
    }
    public String domain() { return value.substring(value.indexOf('@') + 1); }
}

@Converter(autoApply = true)
public class EmailConverter implements AttributeConverter<Email, String> {
    public String convertToDatabaseColumn(Email email) { return email == null ? null : email.value(); }
    public Email convertToEntityAttribute(String column) { return column == null ? null : new Email(column); }
}
```

```sql
CREATE UNIQUE INDEX uq_customer_email ON customer (email);   -- values are already normalised
```

**Common follow-ups:**
- Why not a full RFC 5322 regex? It is enormous, still cannot prove deliverability, and rejects valid addresses; verification by sending a message is the real check.
- Should comparison be case-insensitive? Normalise on construction and make the database index agree; then equality is simply value equality.
- Where does validation belong? In the constructor, so every entry path is covered; DTO-level `@Email` is an additional outer layer.

**Mistakes to avoid:** Passing raw strings through every layer; validating in the controller only; `toLowerCase()` without a locale; storing unnormalised values behind a unique index; making the value object mutable.

**Production perspective:** Normalised value objects prevent the duplicate-account class of support tickets, where `User@Example.com` and `user@example.com` become two customers. They also make audit and export code simpler, because there is one canonical representation.

**Related concepts covered:** Primitive obsession, compact constructor validation, locale-safe normalisation, JPA attribute converters, unique constraints.

## Q026. What are the risks of mutable keys and shallow copies?

**Priority:** Important  
**Why interviewers ask it:** Both produce data corruption that no exception announces.

**Interview-ready answer:** A mutable key is dangerous because hash-based and sorted collections place an entry according to the key's value at insertion time. Mutate a field that participates in `hashCode` or `compareTo`, and the entry stays where it was: `contains` returns false, `get` returns null, and the entry is unreachable but still retained — a silent leak and a silent data loss at once. A shallow copy is the related problem: copying an object but sharing its inner mutable objects means the "copy" and the original change together, which surfaces as one customer's change appearing in another's data. The fixes are the same in spirit: immutable keys, deep copies where nesting is mutable, and unmodifiable views at boundaries so callers cannot reach in.

**In-depth explanation:** Java's own APIs illustrate the shallow-copy trap: `clone()` on an array copies references, not elements; `new ArrayList<>(other)` copies the list structure but shares the element objects; `Collections.unmodifiableList` prevents adding and removing but not mutating the elements themselves. So "defensive copy" only helps if the elements are immutable or are themselves copied. For keys, the practical rule is that anything used as a `Map` key or `Set` element should be immutable — a record over immutable components is ideal. A subtle related case is a JPA entity used as a key before it is persisted: its ID is null at insertion and set at flush, which changes the hash if `hashCode` uses the ID. Where a key must derive from mutable state, remove the entry before mutating and re-insert afterwards, which makes the cost explicit.

**Practical backend example:** The shared-nested-object bug and the deep copy:

```java
// shallow copy: the two "independent" baskets share the same lines
class Basket {
    private final List<OrderLine> lines;
    Basket(Basket other) { this.lines = new ArrayList<>(other.lines); }   // new list, same elements
}
Basket copy = new Basket(original);
copy.lines().get(0).setQuantity(99);      // also changes original's first line if OrderLine is mutable

// safer: immutable elements, so sharing them is harmless
public record OrderLine(String sku, int quantity, Money amount) {}
Basket copy2 = new Basket(List.copyOf(original.lines()));

// mutable key: remove, mutate, re-insert if you truly must
map.remove(key);
key.setRegion("EU");
map.put(key, value);
```

**Common follow-ups:**
- Why is the entry unreachable after mutation? The lookup hashes the new value and probes a different bucket from the one holding the entry.
- Does `unmodifiableList` make the contents immutable? No; it only blocks structural changes to the list. Element mutation still works.
- How do you copy safely? Make the elements immutable, or copy them individually — a deep copy — rather than copying only the container.

**Mistakes to avoid:** Entities as `HashMap` keys before persist; `clone()` on arrays of mutable objects assuming isolation; returning an internal list wrapped as unmodifiable while still mutating the elements; mutating a key "just this once".

**Production perspective:** These bugs are found by users, not by monitoring: a cache that never hits, a report that shows another tenant's value, a set that grows without bound. Preferring immutable value types for keys and payloads removes the whole category rather than patching instances of it.

**Related concepts covered:** Hash bucket placement, deep versus shallow copies, unmodifiable views, entity identity, memory retention.

## Q027. How do you avoid null-related bugs without hiding invalid states?

**Priority:** Must Know  
**Why interviewers ask it:** Null handling shows whether you design for correctness or just add defensive checks.

**Interview-ready answer:** The goal is not to remove every null check but to reduce the places where null is possible. I validate at the boundary — `Objects.requireNonNull` in constructors, Bean Validation on request DTOs — so invalid input never reaches the domain. I prefer empty collections over null, `Optional` as a return type for genuine lookups, and value objects that cannot be constructed in an invalid state. What I avoid is silently substituting defaults: replacing a missing required field with an empty string or zero turns a clear failure into wrong data that someone discovers a month later. So the rule is fail fast and loudly for invalid states, and represent legitimate absence explicitly with `Optional` or an empty collection. Nullability annotations plus static analysis catch the remainder at build time.

**In-depth explanation:** There is a real distinction between "this value is missing and that is fine" and "this value should exist and does not". The first is modelling; the second is a bug or invalid input, and it deserves an exception at the earliest point, with the field name in the message. `Objects.requireNonNull` in constructors is the cheapest enforcement, and it fails at construction rather than at first use, which is much easier to debug. `@NonNull`/`@Nullable` annotations (JSpecify, or the framework's own) let tools such as Error Prone or IntelliJ inspections flag violations without runtime cost; Kotlin interop respects them too. For collections, returning `List.of()` rather than null removes an entire class of caller-side checks. In deeply nested data, `Optional` chaining or a null-safe accessor is preferable to a pyramid of `if (x != null)`.

**Practical backend example:** Boundary validation, explicit absence, and no silent defaults:

```java
public record CreateOrderRequest(
        @NotBlank String customerReference,                 // rejected at the boundary with 400
        @NotEmpty List<@Valid OrderLineRequest> lines) {}

public class Order {
    private final UUID id;
    private final Money total;
    public Order(UUID id, Money total) {
        this.id = Objects.requireNonNull(id, "id");          // fails at construction, not later
        this.total = Objects.requireNonNull(total, "total");
    }
}

public List<Discount> discountsFor(UUID customerId) {
    return discountRepository.findByCustomerId(customerId);  // returns List.of(), never null
}

public Optional<ShippingAddress> defaultAddress(UUID customerId) {   // legitimate absence
    return addressRepository.findDefault(customerId);
}

// avoid: hiding a missing required value
// String reference = request.customerReference() != null ? request.customerReference() : "";
```

**Common follow-ups:**
- Should a method ever return null for a collection? No; return an empty collection so callers need no check.
- Is `Optional` a replacement for validation? No; it expresses absence in a return type. Invalid input should be rejected with an error.
- What do nullability annotations buy you? Build-time detection through static analysis and better IDE and Kotlin interop, with no runtime cost.

**Mistakes to avoid:** `if (x != null)` scattered through business logic instead of at the boundary; substituting defaults for missing required values; returning null collections; catching `NullPointerException` as flow control; `Optional` fields in entities.

**Production perspective:** A `NullPointerException` deep in a service usually means a check was missing several layers earlier, and the stack trace points at the symptom. Boundary validation with the field name in the message turns those incidents into a 400 response with a clear reason, which is both cheaper to support and safer.

**Related concepts covered:** Boundary validation, Optional semantics, empty collections, nullability annotations, fail-fast construction, static analysis.

## Q028. What is the difference between fail-fast validation and accumulating errors?

**Priority:** Important  
**Why interviewers ask it:** It is a user-experience and API-design decision, not only a coding style.

**Interview-ready answer:** Fail-fast stops at the first problem and throws immediately; accumulation collects every problem and reports them together. For an API request, accumulation is almost always right: a client submitting a form wants all invalid fields in one response, not a round trip per mistake. Bean Validation does this natively — `@Valid` gathers every constraint violation and the handler maps them to a list of field errors. For internal invariants, fail-fast is right: a constructor should throw on the first impossible argument, because there is no user to inform and continuing would mean operating on a broken object. So my rule is accumulate at the boundary where a human or client will act on the results, and fail fast inside the domain where the only correct action is to stop.

**In-depth explanation:** There is a middle case worth naming: cross-field and business-rule validation that cannot be expressed as field constraints — "delivery date must be after the order date", "this SKU is not available in this country". Those often need the same accumulated treatment, which means a validation service that returns a list of violations rather than throwing on the first. Order also matters: cheap syntactic checks first, then expensive ones such as database lookups, so an obviously malformed request does not cost a query. Do not accumulate across a security boundary — an authorization failure should stop processing immediately rather than being reported alongside field errors, since continuing may leak information about resources the caller cannot see. For batch processing the same distinction applies at a different scale: a per-item result list is usually more useful than aborting the whole batch, provided partial success is well defined.

**Practical backend example:** Accumulating at the boundary, failing fast inside:

```java
// boundary: Bean Validation accumulates, the handler returns every field error at once
@PostMapping("/api/orders")
ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest request) { ... }

// business rules that constraints cannot express: accumulate too
public List<Violation> validate(CreateOrderRequest request) {
    List<Violation> violations = new ArrayList<>();
    if (request.deliveryDate().isBefore(LocalDate.now(clock))) {
        violations.add(new Violation("deliveryDate", "must not be in the past"));
    }
    if (!catalogue.availableIn(request.sku(), request.country())) {
        violations.add(new Violation("sku", "not available in " + request.country()));
    }
    return violations;                                  // caller decides: 422 with all of them
}

// domain: fail fast, because there is no one to negotiate with
public Order(UUID id, Money total, List<OrderLine> lines) {
    Objects.requireNonNull(id);
    if (lines.isEmpty()) throw new IllegalArgumentException("an order needs at least one line");
}
```

**Common follow-ups:**
- Which status code for a failed business rule? 400 for a malformed request; 422 is a common choice for a syntactically valid request that violates a rule — pick one and document it.
- Should validation hit the database? Only after the cheap checks pass, and be aware that a check-then-act validation is still racy; a unique constraint is the real guarantee.
- Do you accumulate authorization failures? No; stop immediately, and avoid revealing what exists.

**Mistakes to avoid:** Returning only the first field error to a form client; running expensive validation before basic checks; treating validation as a substitute for database constraints; mixing authorization results into validation output.

**Production perspective:** Accumulated, field-level errors with stable codes cut support volume, because the client can render the problem next to the input. They also make client-side retries unnecessary, which reduces load during peak submission periods.

**Related concepts covered:** Bean Validation, cross-field rules, 400 versus 422, check-then-act races, batch partial success, information disclosure.

## Q029. How would you refactor a long conditional into a maintainable strategy?

**Priority:** Important  
**Why interviewers ask it:** It tests pragmatic refactoring judgement — including knowing when not to.

**Interview-ready answer:** First I check what the conditional really is. If it is a chain selecting behaviour by a type or key — shipping cost per carrier, fee per payment method — I replace it with a map from key to strategy, so adding a case means adding a class and a registration rather than editing a method everyone touches. In Spring, injecting `Map<String, PricingStrategy>` gives you the registry for free from the bean names. If the branches are just data — different rates per region — a table or configuration is better than classes. And if it is a short, cohesive conditional, I leave it alone: replacing three lines with three classes and a factory makes the code harder to follow, not easier. Before refactoring I make sure there are tests covering each branch, then refactor, then verify behaviour is unchanged.

**In-depth explanation:** The signal that a conditional should become polymorphic is repetition: the same `switch` on the same key appearing in several methods, which means each new case requires edits in multiple places. The map-of-strategies approach makes the open-closed principle concrete, and with sealed types plus an exhaustive switch you get a compile-time guarantee that every case is handled — sometimes better than a registry, because a missing strategy in a map is a runtime failure. Keep the default path explicit: an unknown key should throw a clear exception rather than silently doing nothing. Also weigh the testing cost: strategies are individually testable, but the wiring needs a test too, so the total number of tests goes up while each gets simpler.

**Practical backend example:** From chain to registry, with Spring wiring:

```java
// before: every new method repeats the same switch
public Money shippingCost(Order order) {
    if (order.carrier() == Carrier.DHL) return dhlRate(order);
    else if (order.carrier() == Carrier.UPS) return upsRate(order);
    else if (order.carrier() == Carrier.LOCAL) return localRate(order);
    throw new IllegalStateException("unknown carrier");
}

// after: one small class per behaviour, registered by key
public interface ShippingRate {
    Carrier carrier();
    Money calculate(Order order);
}

@Service
public class ShippingCostService {
    private final Map<Carrier, ShippingRate> strategies;

    public ShippingCostService(List<ShippingRate> rates) {          // Spring injects all implementations
        this.strategies = rates.stream()
                .collect(Collectors.toMap(ShippingRate::carrier, Function.identity()));
    }

    public Money cost(Order order) {
        ShippingRate rate = strategies.get(order.carrier());
        if (rate == null) throw new UnsupportedCarrierException(order.carrier());   // explicit default
        return rate.calculate(order);
    }
}
```

**Common follow-ups:**
- When should you not refactor? When the conditional is short, appears once, and is unlikely to grow — indirection has a real readability cost.
- Strategy map or sealed types with exhaustive switch? Sealed types give compile-time completeness; a map is better when implementations are plugged in dynamically.
- How do you refactor safely? Characterisation tests for each branch first, then refactor, then confirm the tests still pass unchanged.

**Mistakes to avoid:** Creating a strategy per branch for data differences that belong in configuration; a silent no-op default; scattering strategy registration so no one can find the implementations; refactoring without tests.

**Production perspective:** The measurable benefit is that a new case is an additive change — a new class and a new test — instead of an edit to a method several teams depend on. That is what reduces merge conflicts and regression risk as a codebase grows.

**Related concepts covered:** Strategy pattern, open-closed principle, Spring collection injection, sealed types, characterisation tests, configuration versus code.

## Q030. What makes a Java API backward-compatible for callers?

**Priority:** Important  
**Why interviewers ask it:** Shared libraries and modules break teams when compatibility is treated casually.

**Interview-ready answer:** There are two kinds of compatibility, and they differ. Source compatibility means existing code still compiles; binary compatibility means existing compiled code still links and runs without recompiling. Adding a method to a class is usually fine; adding an abstract method to an interface breaks every implementer, which is why default methods exist. Changing a method's parameter or return type, renaming anything public, narrowing visibility, or adding a checked exception are all breaking. Some changes are source-compatible but not binary-compatible — widening a return type or changing a constant's value, which is inlined at compile time. My approach is to keep the public surface small, add rather than change, deprecate with a replacement and a removal timeline, and use semantic versioning so callers can see the risk in the version number.

**In-depth explanation:** Several specific cases are worth knowing. Adding an overload can silently change which method a recompiled caller binds to, since overload resolution happens at compile time. Changing a `public static final` primitive or `String` constant does not affect already-compiled callers at all, because the old value was inlined — a genuinely surprising source of inconsistency. Reordering enum constants breaks anything persisting ordinals. Serialization adds another dimension: changing fields without managing `serialVersionUID` breaks deserialisation of old data, which matters for caches and message payloads. For services rather than libraries, the same thinking applies to the wire contract: adding an optional field is safe, removing or renaming one is not, and consumers should be tolerant readers. Tooling helps — japicmp or revapi can fail the build on an incompatible change, which is more reliable than review.

**Practical backend example:** Compatible evolution of a published interface:

```java
// breaking: every implementer stops compiling
public interface PaymentGateway {
    Receipt capture(Money amount);
    Refund refund(String receiptId);          // newly added abstract method - breaks implementers
}

// compatible: a default implementation keeps existing implementers working
public interface PaymentGateway {
    Receipt capture(Money amount);
    default Refund refund(String receiptId) {
        throw new UnsupportedOperationException("refunds are not supported by this gateway");
    }
}

// compatible: add an overload rather than changing the signature
public Receipt capture(Money amount) { return capture(amount, IdempotencyKey.random()); }
public Receipt capture(Money amount, IdempotencyKey key) { ... }

// deprecate with a migration path and a timeline
@Deprecated(since = "2.4", forRemoval = true)     // removal announced for 3.0
public Receipt charge(Money amount) { return capture(amount); }
```

**Common follow-ups:**
- Is adding a method to an interface safe? Only with a default implementation; otherwise every implementer breaks.
- What is source-compatible but not binary-compatible? Changing an inlined constant, or widening a return type — old compiled callers can fail to link or keep the old value.
- How do you signal a breaking change? Semantic versioning plus `@Deprecated(forRemoval = true)` with a documented replacement and removal release.

**Mistakes to avoid:** Renaming public methods "for clarity" in a shared library; changing constant values assuming callers see the new one; removing a deprecated method without a release note; letting internal classes become public by accident.

**Production perspective:** In a multi-team codebase, an incompatible library release turns into blocked deployments across services. Automated compatibility checks in CI plus a short deprecation window is the combination that keeps the cost predictable; the same discipline applied to API and event schemas prevents the equivalent problem at runtime.

**Related concepts covered:** Source versus binary compatibility, default methods, deprecation policy, semantic versioning, constant inlining, schema evolution.
