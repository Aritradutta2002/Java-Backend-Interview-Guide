# Chapter 1: Core Java, OOP, Exceptions, and Language Fundamentals

Assume Java 17 unless a question explicitly mentions Java 21. All code examples follow modern production backend conventions.

---

## Q001 — OOP in Realistic Backend Code

**The one-line answer:** In backend services, OOP is about protecting business invariants through encapsulation, isolating volatile integrations behind abstractions, using polymorphism to eliminate branchy conditionals, and favoring composition over inheritance for maintainable workflows.

### The four pillars in production backend design

1. **Encapsulation:** Protect valid state transitions inside domain entities rather than treating them as bags of getters/setters (anemic domain model).
   ```java
   public class Order {
       private OrderStatus status = OrderStatus.PENDING;
       private Money total;

       public void pay(Receipt receipt) {
           if (this.status != OrderStatus.PENDING) {
               throw new IllegalStateException("Cannot pay for order in status: " + status);
           }
           Objects.requireNonNull(receipt, "Receipt required");
           this.status = OrderStatus.PAID;
       }
   }
   ```
2. **Abstraction:** Expose intentions via narrow interfaces while hiding external protocol, network, or provider details.
   ```java
   public interface PaymentGateway {
       Receipt charge(CustomerId customerId, Money amount);
   }
   ```
3. **Polymorphism:** Swap implementations at runtime via Spring dependency injection or factory strategies without modifying business logic:
   ```java
   @Service
   public class CheckoutService {
       private final PaymentGateway paymentGateway; // injected: Stripe, PayPal, or Mock in tests
       public CheckoutService(PaymentGateway paymentGateway) {
           this.paymentGateway = paymentGateway;
       }
   }
   ```
4. **Inheritance:** Restrict inheritance to true polymorphic substitution (Liskov Substitution Principle). Do not use inheritance solely to inherit helper methods across unrelated services.

### Anemic domain models vs rich domain models

In an anemic model, entities are passive data structures (`getAmount()`, `setAmount()`) and controllers or services contain all business rules. In a rich domain model, entities enforce their own invariants, preventing illegal business states anywhere in the system.

### Common follow-ups

- **What is the open-closed principle in practice?** Classes should be open for extension but closed for modification. Introducing a new payment method means adding a new `PaymentGateway` implementation, not editing 50-line `if-else` blocks inside `CheckoutService`.
- **How does interface segregation apply to backend services?** Keep interfaces small and client-specific. Instead of a monolithic `OrderService` interface with 30 methods, split into query and command boundaries (`OrderReader`, `OrderWriter`).

### Mistakes to avoid

- Treating encapsulation as merely making fields `private` while providing public setters for all of them.
- Creating an interface for every single service class even when only one implementation will ever exist without unit-testing need.

### Production perspective

Keeping domain logic inside entities and external calls behind interfaces allows safe mocking in unit tests, prevents flaky database integration tests, and lets you migrate third-party vendors without touching core business rules.

---

## Q002 — Interface vs Abstract Class in Java 17/21

**The one-line answer:** Use an interface to define a polymorphic contract across unrelated classes or multiple capabilities; use an abstract class when closely related implementations share mutable state, constructors, or a reusable template algorithm.

### Key differences

| Feature | Interface | Abstract Class |
|---|---|---|
| Multiple inheritance | Yes (implements multiple interfaces) | No (extends only one class) |
| Instance state | No instance fields (only static final constants) | Can declare instance fields |
| Constructors | None | Yes (called by subclasses via `super`) |
| Methods | Abstract, `default`, `static`, `private` | Abstract, concrete, `final`, `static` |
| Access modifiers | Methods `public` (or `private` helpers) | Any access modifier (`protected`, `package-private`, etc.) |
| Evolution | Can add `default` methods without breaking implementers | Adding abstract methods breaks all subclasses |

### When to choose which

- **Choose Interface:** For role-based capabilities (`Auditable`, `Exportable`, `PaymentGateway`), decoupling architecture layers, and enabling test mocking.
- **Choose Abstract Class:** For template method patterns where subclasses share common setup, lifecycle, or protected state:
  ```java
  public abstract class AbstractAuditService {
      protected final AuditLogRepository repo;
      protected AbstractAuditService(AuditLogRepository repo) { this.repo = repo; }

      public final void execute(AuditRequest req) { // Template method
          validate(req);
          doExecute(req);
          repo.log(req.userId(), req.action());
      }
      protected abstract void doExecute(AuditRequest req);
  }
  ```

### Sealed interfaces in Java 17/21

Modern Java lets you restrict implementers:
```java
public sealed interface PaymentMethod permits CreditCard, BankTransfer, Crypto {}
```

### Common follow-ups

- **Can an interface have concrete methods?** Yes: `default` methods (for backwards compatibility/mixins), `static` utility methods, and `private` helper methods (Java 9+).
- **Can an abstract class implement an interface without implementing its methods?** Yes, leaving the method implementation to concrete subclasses.

### Mistakes to avoid

- Forgetting that interface fields are implicitly `public static final`.
- Relying on interface `default` methods to hold state — interfaces cannot hold per-instance state.

### Production perspective

In public API libraries and hexagonal architectures, domain ports are always interfaces. Abstract classes serve internally as skeletal implementations to reduce boilerplate.

---

## Q003 — Composition vs Inheritance

**The one-line answer:** Favor composition over inheritance because composition decouples behavior through explicit collaborators that can be swapped or mocked, while inheritance creates tight coupling to base-class internals and breaks encapsulation.

### Why inheritance easily breaks (The Fragile Base Class problem)

Inheriting a class binds you to its internal implementation details. If a base class changes an internal helper method or calls an overridable method inside its constructor, subclasses can subtly fail.

```java
// INHERITANCE TRAP: Extending a collection or base service
public class MonitoredList<T> extends ArrayList<T> {
    private int addCount = 0;
    @Override public boolean add(T e) { addCount++; return super.add(e); }
    @Override public boolean addAll(Collection<? extends T> c) {
        addCount += c.size();
        return super.addAll(c); // super.addAll calls add() internally -> DOUBLE COUNT!
    }
}
```

### The composition alternative

Wrap the dependency as an injected collaborator (Delegation / Decorator pattern):
```java
public class MonitoredService {
    private final OrderRepository repository; // Collaborator
    private final MeterRegistry meterRegistry; // Collaborator

    public MonitoredService(OrderRepository repository, MeterRegistry meterRegistry) {
        this.repository = repository;
        this.meterRegistry = meterRegistry;
    }

    public Order saveOrder(Order order) {
        meterRegistry.counter("orders.created").increment();
        return repository.save(order);
    }
}
```

### When inheritance IS justified

1. Strict "is-a" hierarchy adhering to Liskov Substitution Principle (every subclass can substitute the base class without breaking callers).
2. Framework base classes designed explicitly for extension (e.g. Spring's `ResponseEntityExceptionHandler`).

### Common follow-ups

- **How does composition help in testing?** Injected collaborators can be replaced with mocks or fakes in unit tests. With inheritance, you cannot isolate the base class from the subclass during tests.
- **Does composition carry a performance penalty?** Negligible object reference indirection, which HotSpot JIT compiler frequently inlines at runtime.

### Mistakes to avoid

- Extending a class just to reuse one utility method (use a helper or injected delegate instead).
- Deep inheritance hierarchies (>2 levels) in business logic services.

### Production perspective

Enterprise systems evolve constantly. Services built with composition easily accommodate decorator concerns (metrics, caching, retries, distributed tracing) via Spring AOP or proxy wrappers without modifying core classes.

---

## Q004 — Method Overloading vs Overriding

**The one-line answer:** Overloading is compile-time (static) polymorphism where methods share a name but differ in parameter signatures; overriding is runtime (dynamic) polymorphism where a subclass provides a specific implementation of a superclass method with identical signature.

### Comparison

| Aspect | Overloading | Overriding |
|---|---|---|
| Binding time | Compile time (early binding) | Runtime (dynamic dispatch / virtual method table) |
| Method name | Identical | Identical |
| Parameters | Must differ in type, count, or order | Must be identical |
| Return type | Can be anything | Must be identical or covariant (subtype) |
| Access modifier | Can be anything | Cannot be more restrictive |
| Checked exceptions | Can declare any exception | Cannot declare broader or new checked exceptions |
| `@Override` annotation | Invalid | Strongly recommended |

### Covariant return types & bridge methods

A subclass method can return a subtype of the superclass method's return type:
```java
public class BaseService {
    public Number calculate() { return 1; }
}
public class SubService extends BaseService {
    @Override
    public Integer calculate() { return 1; } // Covariant return
}
```
The compiler generates a synthetic **bridge method** in bytecode to maintain binary compatibility: `public Number calculate() { return this.calculate(); }`.

### Static methods cannot be overridden

Static methods are resolved at compile time based on the reference type, not runtime object instance. Declaring the same static method in a subclass is **method hiding**, not overriding.

### Common follow-ups

- **The accidental overload bug with equals:** Declaring `public boolean equals(MyClass other)` instead of `public boolean equals(Object other)` creates an overload. `HashSet` and `HashMap` will not invoke it, causing silent equality failures!
- **Widening vs Autoboxing resolution:** When resolving overloaded methods, the compiler prefers widening over boxing, and boxing over varargs.

### Mistakes to avoid

- Overloading methods with confusingly similar parameter types (e.g. `List<String>` vs `List<Integer>` — which fails anyway due to type erasure!).
- Omitting `@Override`, which risks silent overload bugs if method signatures drift.

### Production perspective

Avoid complex overload sets with ambiguous boxing/varargs. In public APIs, prefer distinct method names (e.g. `findByName` and `findById`) over overloaded `find`.

---

## Q005 — equals and hashCode Contract

**The one-line answer:** If two objects are equal according to `equals(Object)`, they MUST produce the exact same `hashCode()`; if this contract is violated, hash-based collections like `HashMap` and `HashSet` fail to find, deduplicate, or remove entries.

### The contractual rules

1. **Reflexive:** `x.equals(x)` is `true`.
2. **Symmetric:** `x.equals(y)` returns `true` if and only if `y.equals(x)` returns `true`.
3. **Transitive:** If `x.equals(y)` and `y.equals(z)`, then `x.equals(z)`.
4. **Consistent:** Repeated invocations return the same result unless state is mutated.
5. **Non-nullity:** `x.equals(null)` is always `false`.
6. **Hash code consistency:** Equal objects must have equal hash codes. Unequal objects may share hash codes (collision), but distinct hash codes improve hash table performance.

### What happens when the contract is broken

```java
public class BrokenUser {
    private String id;
    public BrokenUser(String id) { this.id = id; }
    @Override public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof BrokenUser u)) return false;
        return Objects.equals(id, u.id);
    }
    // MISSING hashCode()! Uses System.identityHashCode
}

Set<BrokenUser> set = new HashSet<>();
set.add(new BrokenUser("123"));
boolean exists = set.contains(new BrokenUser("123")); // FALSE!
```
The second object lands in a different hash bucket because its default identity hash code differs, so `equals` is never even evaluated.

### The mutable key catastrophe

Never mutate fields used in `hashCode()` after an object is placed in a `HashMap` or `HashSet`. Mutation changes the computed bucket index. The map searches the new bucket, while the object remains stuck in the old bucket — creating an unretrievable memory leak!

### Proper implementation (Java 17 record or Objects.hash)

```java
public record OrderKey(long tenantId, UUID orderId) {} // Automatically fulfills contract!
```

### Common follow-ups

- **How do you handle JPA Entity equality?** Database IDs are null before saving and populated on persist. Comparing by ID breaks when unsaved entities are added to a Set. Best practice: use a unique business key (e.g., UUID or natural key) for `equals`/`hashCode`, or compare identity (`this == o`) if no natural key exists.
- **TreeSet behavior:** `TreeSet` uses `compareTo()` or `Comparator`, NOT `equals()`. If `compareTo` returns 0, `TreeSet` considers them duplicates even if `equals` returns false.

### Mistakes to avoid

- Using `==` inside `equals` for object references (e.g. Strings).
- Including mutable collections or lazy JPA associations inside `hashCode()`.

### Production perspective

Cache keys, deduplication sets, and distributed session attributes depend on reliable hashing. Prefer immutable records or UUID-based keys.

---

## Q006 — compareTo and Comparator

**The one-line answer:** `Comparable<T>` defines the natural, intrinsic ordering of a class via `compareTo(T)`, while `Comparator<T>` defines custom, pluggable, external sorting strategies via `compare(T, T)`.

### Comparing the two

| Aspect | `Comparable<T>` | `Comparator<T>` |
|---|---|---|
| Package | `java.lang` | `java.util` |
| Method | `int compareTo(T o)` | `int compare(T o1, T o2)` |
| Location | Implemented inside the target class | External class, lambda, or static factory |
| Number of orders | Exactly one (natural order) | Unlimited custom orders |
| Usage | `Collections.sort(list)` | `list.sort(comparator)` |

### Consistency with equals

The natural order should be **consistent with equals**:
`(x.compareTo(y) == 0) == x.equals(y)`
If this is violated, sorted collections like `TreeSet` and `TreeMap` behave erratically because they determine element uniqueness solely by `compareTo == 0`, ignoring `equals()`.
Example: `BigDecimal("2.0")` and `BigDecimal("2.00")` return `false` for `equals()`, but `0` for `compareTo()`. Adding both to a `HashSet` stores 2 elements; adding both to a `TreeSet` stores only 1 element!

### Modern Comparator construction

```java
Comparator<Order> orderComparator = Comparator
    .comparing(Order::getCreatedAt)
    .thenComparing(Order::getPriority, Comparator.reverseOrder())
    .thenComparing(Order::getId, Comparator.nullsLast(Comparator.naturalOrder()));
```

### Common follow-ups

- **Integer subtraction overflow trap:** Never write `return o1.id - o2.id;`. If `o1.id` is large positive and `o2.id` is large negative, integer overflow yields a reversed sign. Always write `Integer.compare(o1.id, o2.id)` or `Long.compare(o1.id, o2.id)`.
- **Null handling:** Always wrap with `Comparator.nullsFirst()` or `Comparator.nullsLast()` when sorting fields that could be null.

### Mistakes to avoid

- Writing non-transitive comparators (e.g. random or non-consistent returns), which causes `IllegalArgumentException: Comparison method violates its general contract!` during `TimSort`.

### Production perspective

Multi-attribute sorting with null-safety and secondary tie-breakers (like order creation timestamp + order ID) is critical for deterministic pagination and API response consistency.

---

## Q007 — String Immutability and String Pool

**The one-line answer:** Strings in Java are immutable for security, thread safety, hash code caching, and memory optimization via the String Constant Pool; once created, a String's internal character buffer cannot be altered.

### Four core reasons for String immutability

1. **Security:** Strings carry sensitive parameters: database URLs, usernames, passwords, file paths, and network sockets. If strings were mutable, another thread could mutate a validated file path between validation and execution (TOCTOU attack).
2. **String Constant Pool:** String literals are cached in heap memory. Multiple variables pointing to `"admin"` reference the same object, saving massive heap space. Immutability guarantees that modifying one reference cannot alter others.
3. **Thread Safety:** Immutable objects are inherently thread-safe without synchronization. They can be freely shared across concurrent requests.
4. **Cached HashCode:** `String.hashCode()` is computed once lazily and cached in a private field. This makes Strings blazingly fast as keys in `HashMap` and `ConcurrentHashMap`.

### String memory internals (Compact Strings in Java 9+)

Before Java 9, `String` stored characters as `char[]` (2 bytes per char). Since most strings are Latin-1 (ASCII), Java 9 introduced Compact Strings:
```java
public final class String {
    private final byte[] value; // 1 byte per char for Latin-1, 2 bytes for UTF-16
    private final byte coder;   // 0 for LATIN1, 1 for UTF16
    private int hash;           // cached hash code
}
```
This cuts heap usage for strings by up to 50% in enterprise applications!

### String pool vs heap allocation

```java
String s1 = "hello";             // Interned in String Constant Pool
String s2 = "hello";             // Points to exact same pooled instance
String s3 = new String("hello");  // Explicit heap allocation outside pool

System.out.println(s1 == s2);      // true (same memory address)
System.out.println(s1 == s3);      // false (different heap objects)
System.out.println(s1.equals(s3)); // true (identical contents)
System.out.println(s1 == s3.intern()); // true (intern() resolves to pool)
```

### Common follow-ups

- **Why use `char[]` instead of `String` for passwords?** A String remains in the String pool or heap until garbage collection, leaving cleartext in memory dumps. A `char[]` can be explicitly overwritten with zeros (`Arrays.fill(pwd, '0')`) immediately after authentication.
- **Where does the String Pool live?** Since Java 7, it lives in the main Java Heap (not PermGen), making it subject to standard GC.

### Mistakes to avoid

- Calling `String.intern()` excessively on unbounded user input. The internal JVM intern table has fixed bucket sizing; flooding it causes GC overhead and memory leaks.
- Comparing strings using `==` instead of `equals()`.

### Production perspective

String allocations dominate heap memory in web services (often 30–40% of heap). Enabling G1 GC String Deduplication (`-XX:+UseStringDeduplication`) automatically merges duplicate `byte[]` backing arrays across long-lived strings in the background.

---

## Q008 — StringBuilder and String Concatenation Pitfalls

**The one-line answer:** Never concatenate strings using `+` inside a loop; use `StringBuilder` with an appropriately pre-sized capacity to prevent $O(N^2)$ memory copying and GC allocation storms.

### The loop concatenation trap

```java
// HORRIBLE: Allocates new StringBuilder and copies buffer on EVERY iteration
String result = "";
for (String item : items) { // N iterations
    result += item; 
}
```
In bytecode, `result += item` compiles to:
`result = new StringBuilder().append(result).append(item).toString();`
On each iteration, an entire new `StringBuilder` and array are allocated, copying all previous characters. For $N$ items, this takes $O(N^2)$ time and allocates huge volumes of short-lived garbage on the heap.

### The correct approach

```java
StringBuilder sb = new StringBuilder(estimatedSize);
for (String item : items) {
    sb.append(item);
}
String result = sb.toString();
```
Or using modern Java streams / `String.join`:
```java
String result = String.join(",", items);
// Or: items.stream().collect(Collectors.joining(","));
```

### StringBuilder vs StringBuffer

| Feature | `StringBuilder` (Java 5+) | `StringBuffer` (Java 1.0) |
|---|---|---|
| Thread safety | Not thread-safe | Thread-safe (methods `synchronized`) |
| Performance | Fast, zero synchronization overhead | Slower due to lock contention |
| Usage | Default choice for string construction | Obsolete in 99% of backend code |

### Java 9+ invokedynamic optimization (JEP 280)

Outside loops, single-line concatenation like:
`String msg = "Order " + orderId + " for customer " + customerName;`
is no longer compiled to chained `StringBuilder.append()`. Instead, javac generates an `invokedynamic` call to `StringConcatFactory.makeConcatWithConstants()`, which calculates the exact final size and builds the string with zero redundant array copies.

### Common follow-ups

- **What is StringBuilder's default capacity?** 16 characters. When capacity is exceeded, it grows by `(currentCapacity * 2) + 2`. Pre-sizing capacity eliminates array resizings and copies.

### Mistakes to avoid

- Using `StringBuffer` out of habit when building strings within a single thread or method scope.
- Pre-sizing capacity too small or forgetting to pre-size when building multi-megabyte payloads (e.g. CSV exports).

### Production perspective

Large string concatenation in reporting or CSV export endpoints can trigger high JVM YoungGen GC pause times. Always use `BufferedWriter`, streaming Jackson serializers, or pre-sized `StringBuilder` instances.

---

## Q009 — Checked vs Unchecked Exceptions and API Design

**The one-line answer:** Use checked exceptions for recoverable business conditions that callers are expected to handle; use unchecked exceptions (`RuntimeException`) for programming bugs, unrecoverable errors, and clean API design across application layers.

### Exception hierarchy

```
java.lang.Throwable
 ├── java.lang.Error (Fatal JVM errors: OutOfMemoryError, StackOverflowError — NEVER catch)
 └── java.lang.Exception
      ├── java.lang.RuntimeException (UNCHECKED: NullPointerException, IllegalArgumentException)
      └── Other Exceptions (CHECKED: IOException, SQLException)
```

### The modern backend consensus

In modern Java and Spring Boot backend development:
1. **Checked exceptions create boilerplate noise:** Forcing callers to catch exceptions they cannot fix (like `SQLException`) leads to empty catch blocks or rethrowing `RuntimeException` wrappers.
2. **Checked exceptions break functional programming:** `Function`, `Predicate`, and Stream APIs cannot throw checked exceptions without ugly wrapper utilities.
3. **Exception translation at layer boundaries:** Catch low-level checked exceptions at the persistence or external integration boundary and translate them to domain-specific unchecked exceptions:

```java
public Order findOrder(OrderId id) {
    try {
        return jdbcTemplate.queryForObject(sql, mapper, id.value());
    } catch (EmptyResultDataAccessException ex) {
        throw new OrderNotFoundException("Order not found: " + id, ex); // Root cause preserved!
    } catch (DataAccessException ex) {
        throw new OrderStorageException("Database failure loading order: " + id, ex);
    }
}
```

### Spring `@Transactional` rollback default

By default, Spring transactions rollback ONLY on unchecked exceptions (`RuntimeException` and `Error`). If a method throws a checked exception (`Exception`), Spring commits the transaction unless configured via `@Transactional(rollbackFor = Exception.class)`!

### Common follow-ups

- **How do you preserve the stack trace?** Always pass the original exception as the `cause` parameter to the custom exception constructor: `new MyException("Message", cause)`.
- **When should a checked exception still be used?** When failure is a normal, expected business alternative that the immediate caller must handle (e.g. `InsufficientFundsException` on account transfer).

### Mistakes to avoid

- Swallowing exceptions: `catch (Exception e) {}` with no logging or rethrow.
- Catching `Throwable` or `Error`.
- Throwing generic `RuntimeException` instead of specific domain exceptions.

### Production perspective

Standardize on an unchecked domain exception hierarchy mapped to HTTP status codes via Spring's `@RestControllerAdvice`. This keeps service code clean, expressive, and decoupled from transport protocols.

---

## Q010 — try-with-resources and AutoCloseable

**The one-line answer:** `try-with-resources` automatically closes any resource implementing `AutoCloseable` in reverse declaration order upon block exit, while preserving the primary business exception and attaching close failures as suppressed exceptions.

### How it works

```java
try (InputStream in = new FileInputStream(source);
     OutputStream out = new FileOutputStream(dest)) {
    in.transferTo(out);
} // Both in and out guaranteed closed, even if transferTo throws!
```

### Suppressed exceptions: why try-finally was broken

In old `try-finally` code:
```java
InputStream in = null;
try {
    in = new FileInputStream("file.txt");
    process(in); // Exception 1: CorruptDataException
} finally {
    if (in != null) in.close(); // Exception 2: SocketTimeoutException
}
```
If `close()` threw an exception, **Exception 1 was swallowed and permanently lost**!
With `try-with-resources`:
- Exception 1 (from `try` body) is the **primary exception** thrown to the caller.
- Exception 2 (from `close()`) is caught and attached to Exception 1 via `primary.addSuppressed(closeException)`.
- Callers can inspect secondary failures using `e.getSuppressed()`.

### `AutoCloseable` vs `Closeable`

- `java.lang.AutoCloseable` (Java 7): `void close() throws Exception;`. Intended for any resource.
- `java.io.Closeable` (Java 5): `void close() throws IOException;`. Narrows exception to `IOException`, and is required to be idempotent.

### Common follow-ups

- **Resource declaration order:** Resources are closed in **reverse order** of creation (out closes before in). This correctly handles dependencies where a wrapper stream wraps an underlying channel.
- **Java 9 enhancement:** Variables that are effectively final can be referenced directly in try-with-resources without redeclaration:
  ```java
  var reader = getReader();
  try (reader) { ... }
  ```

### Mistakes to avoid

- Manually closing a connection or transaction managed by Spring inside a try-with-resources block — let Spring control the pooled connection lifecycle.
- Throwing checked exceptions from a custom resource's `close()` method when an unchecked exception or silent no-op is more appropriate.

### Production perspective

Resource leaks (unclosed database statements, HTTP response bodies, file channels) cause socket/file-descriptor exhaustion that crashes production servers. Always manage I/O streams and raw JDBC statements with `try-with-resources`.

---

## Q011 — Immutability and Defensive Copying

**The one-line answer:** True immutability requires making the class final, all fields private and final, providing no mutators, and performing defensive copies on mutable inputs in constructors and mutable outputs in getters to prevent state aliasing.

### The 5 rules of true immutability

1. Make class `final` (or use private constructors with static factories) to prevent subclassing.
2. Make all fields `private` and `final`.
3. Do not provide any mutator methods (no setters).
4. Perform defensive copying of all mutable arguments passed into the constructor.
5. Perform defensive copying (or return unmodifiable views) of all mutable fields in getters.

```java
public final class UserProfile {
    private final String username;
    private final List<String> roles;
    private final Date memberSince;

    public UserProfile(String username, List<String> roles, Date memberSince) {
        this.username = Objects.requireNonNull(username);
        // Defensive copy on write: prevents caller from mutating list after passing it
        this.roles = List.copyOf(roles); 
        this.memberSince = new Date(memberSince.getTime()); // Date is mutable!
    }

    public List<String> getRoles() {
        return roles; // Already unmodifiable via List.copyOf
    }

    public Date getMemberSince() {
        return new Date(memberSince.getTime()); // Defensive copy on read
    }
}
```

### `Collections.unmodifiableList` vs `List.copyOf`

- `Collections.unmodifiableList(list)`: Creates an unmodifiable **view** backed by the original list. If the caller mutates the original list, the view reflects those changes!
- `List.copyOf(list)`: Performs a true defensive snapshot copy. Further mutations to the input list have zero effect on the copy.

### Safe publication and the Java Memory Model

Under the JMM, an object whose fields are all `final` is guaranteed to be **safely published** to all threads without synchronization once the constructor finishes. Other threads will never see default uninitialized values.

### Common follow-ups

- **Is a Java `record` deeply immutable?** No. A record is only shallowly immutable. If a record component is a mutable `ArrayList`, its contents can still be mutated.

### Mistakes to avoid

- Assuming `final` deeply freezes an object. A `final List<Item>` prevents reference reassignment, but `list.add()` remains completely mutable.
- Using legacy mutable classes like `java.util.Date` instead of immutable `java.time.Instant`.

### Production perspective

Immutable objects eliminate concurrency race conditions, make cache entries safe to share, and simplify reasoning in multi-threaded Spring services.

---

## Q012 — Records in Java 17/21

**The one-line answer:** Records are transparent, immutable data carriers that automatically generate private final fields, a canonical constructor, accessors, `equals()`, `hashCode()`, and `toString()` with minimal boilerplate.

### Modern record syntax and compact constructors

```java
public record CreateUserRequest(
    String username,
    String email,
    List<String> roles
) {
    // Compact constructor for validation and defensive copies
    public CreateUserRequest {
        Objects.requireNonNull(username, "username required");
        Objects.requireNonNull(email, "email required");
        if (!email.contains("@")) {
            throw new IllegalArgumentException("Invalid email: " + email);
        }
        roles = roles == null ? List.of() : List.copyOf(roles); // defensive copy
    }
}
```

### Record capabilities and limitations

- **Capabilities:** Can implement interfaces, declare static fields and methods, define custom instance methods, and override accessors.
- **Limitations:** Cannot extend other classes (implicitly extends `java.lang.Record`), cannot be extended (implicitly `final`), cannot declare instance fields outside the record header.

### Why records are NOT suitable as JPA entities

| Reason | Detail |
|---|---|
| Mutability | JPA requires mutable entities for dirty checking and lifecycle tracking. |
| No-arg constructor | Hibernate proxies require a public/protected no-argument constructor. |
| Proxy subclassing | Hibernate uses CGLIB/ByteBuddy to subclass entities for lazy loading; records are `final`. |
| Identity semantics | Records evaluate equality across all fields; JPA entities require identity based on primary key. |

### Where records excel

- API DTOs (Request / Response bodies in Spring `@RestController`).
- Value objects and composite Map keys.
- CQRS read projections and Spring Data JPA interface/record query projections.
- Messaging payloads (Kafka / RabbitMQ event DTOs).

### Common follow-ups

- **Accessor naming:** Records generate `name()`, NOT `getName()`. Jackson 2.12+ supports record accessors out of the box.
- **Record serialization:** Records bypass Java's unsafe reflective serialization hacks and deserialize strictly via the canonical constructor, making them immune to classic deserialization gadget vulnerabilities.

### Mistakes to avoid

- Putting mutable collections inside records without a compact constructor defensive copy.
- Attempting to map records directly to Hibernate entities with bidirectional associations.

### Production perspective

Use records for 100% of data crossing API and service boundaries. They reduce DTO boilerplate by 80% without requiring Lombok.

---

## Q013 — Optional Done Right

**The one-line answer:** Use `Optional<T>` strictly as a method return type to explicitly signal that a value may be absent; never use it for fields, method parameters, or collection wrappers.

### Proper Optional usage

```java
// GOOD: Idiomatic search returning Optional
public Optional<Customer> findCustomer(CustomerId id) {
    return customerRepository.findById(id.value());
}

// Consuming Optional cleanly:
String name = findCustomer(id)
    .filter(Customer::isActive)
    .map(Customer::getName)
    .orElseGet(() -> fetchDefaultName()); // orElseGet evaluates lazily!
```

### `orElse()` vs `orElseGet()`

```java
// DANGEROUS: orElse() evaluates the argument eagerly on EVERY call
Customer c = findCustomer(id).orElse(createDefaultInDatabase()); 
// createDefaultInDatabase() executes even if findCustomer returned a customer!

// SAFE: orElseGet() takes a Supplier and evaluates ONLY when empty
Customer c = findCustomer(id).orElseGet(() -> createDefaultInDatabase());
```

### Top anti-patterns to avoid

1. **Never call `optional.get()` without checking:** Calling `.get()` without `isPresent()` throws `NoSuchElementException`, which is no better than a `NullPointerException`.
2. **Never use `Optional` as a method parameter:** Forces callers to write `service.update(Optional.of(data))`. Use method overloading or nullable arguments instead.
3. **Never use `Optional` as an entity field:** `Optional` does not implement `Serializable`, adds memory overhead, and confuses ORMs.
4. **Never wrap collections in `Optional`:** Return an empty list (`Collections.emptyList()`), never `Optional<List<T>>` or `null`.
5. **Never return `null` from a method returning `Optional`:** Always return `Optional.empty()`.

### Common follow-ups

- **Primitive Optionals:** Use `OptionalInt`, `OptionalLong`, `OptionalDouble` to avoid boxing overhead.
- **Stream integration:** In Java 9+, use `optional.stream()` to cleanly flatten optional streams:
  `orders.stream().map(this::findCoupon).flatMap(Optional::stream).toList();`

### Mistakes to avoid

- Writing `if (opt.isPresent()) { return opt.get(); } else { ... }` — this defeats the purpose of Optional; use `opt.map().orElse(...)` or pattern matching.

### Production perspective

At service boundaries and repositories, `Optional` forces the caller to explicitly consider the missing-data branch, eliminating a massive source of production NPEs.

---

## Q014 — Pass-by-Value and Object References

**The one-line answer:** Java is strictly pass-by-value in all situations; for primitive types, the actual value is copied, while for objects, the value of the object reference (the pointer to the heap object) is copied.

### The classic swap method proof

```java
public static void swap(Order a, Order b) {
    Order temp = a;
    a = b;
    b = temp;
}

Order o1 = new Order(1);
Order o2 = new Order(2);
swap(o1, o2);
System.out.println(o1.getId()); // Still 1! Swapping references inside swap() had zero effect.
```
Inside `swap()`, the local variables `a` and `b` are copies of the references. Reassigning `a` or `b` changes where the local variable points, but leaves the caller's `o1` and `o2` pointing to their original objects.

### Mutating object state vs reassigning references

```java
public static void modifyOrder(Order order) {
    order.setStatus("CONFIRMED"); // Mutates object on heap! Visible to caller.
    order = new Order(99);        // Reassigns local copy of reference! Invisible to caller.
}
```
Both caller and callee hold separate reference copies that point to the same object on the heap. Mutating that object changes shared state.

### Common follow-ups

- **Does Java have pointers?** Java has references, which are memory pointers managed safely by the JVM without pointer arithmetic.
- **How to prevent callers from mutating passed objects?** Pass immutable objects, records, or defensive copies.

### Mistakes to avoid

- Telling an interviewer that Java passes primitives by value and objects by reference — this is factually incorrect and a red flag.
- Returning direct references to internal mutable arrays or collections.

### Production perspective

Accidental mutation of passed-in request objects across asynchronous boundaries or service layers causes hard-to-trace bugs. Always treat method parameters as read-only.

---

## Q015 — var and Local Type Inference

**The one-line answer:** `var` (Java 10+) introduces compile-time type inference for local variables with initializers, eliminating redundant type boilerplate while preserving static type safety.

### Where `var` is allowed vs forbidden

```java
// ALLOWED:
var list = new ArrayList<String>();         // Inferred as ArrayList<String>
var stream = list.stream().filter(...);     // Inferred as Stream<String>
for (var item : list) { ... }               // In enhanced for loop
try (var in = new FileInputStream(...)) {}  // In try-with-resources
(@NotNull var x) -> x.process();            // In lambda parameters with annotations (Java 11)

// FORBIDDEN (Compile error):
private var field = 10;                     // Cannot be used for fields
public var process(var input) { ... }       // Cannot be used for method params or return types
var x;                                      // Missing initializer
var y = null;                               // Cannot infer type from null
var arr = { 1, 2, 3 };                      // Array initializer requires explicit type
```

### Readability best practices

- **Use `var` when the type is obvious:**
  `var user = new UserRegistrationDTO();` or `var orders = orderService.findAll();`
- **Avoid `var` when the type is obscured:**
  `var result = processData(); // Bad: caller cannot see what result is!`
- **Avoid `var` with diamond operator:**
  `var list = new ArrayList<>(); // Inferred as ArrayList<Object>, losing type safety!`

### Common follow-ups

- **Does `var` affect runtime performance?** Zero impact. `var` is resolved strictly at compile time; the generated bytecode contains the exact concrete type.
- **Can you reassign a `var` variable?** Yes, but only with values compatible with the inferred type: `var x = "hello"; x = "world"; // OK; x = 123; // Compile error!`.

### Mistakes to avoid

- Thinking `var` makes Java dynamically typed like Python or JavaScript.
- Sacrificing code clarity in pull requests by using `var` on complex nested method call returns.

### Production perspective

`var` shines when working with long generic types, such as `Map<Department, List<Map.Entry<Employee, BigDecimal>>>`, keeping code clean and readable.

---

## Q016 — Sealed Classes and Interfaces

**The one-line answer:** Sealed classes and interfaces (Java 17+) restrict which classes or interfaces may extend or implement them, enabling safe, closed domain hierarchies and compiler-enforced exhaustive pattern matching.

### Syntax and rules

```java
public sealed interface PaymentResult 
    permits PaymentResult.Success, PaymentResult.Failed, PaymentResult.Pending {

    record Success(String transactionId, Money amount) implements PaymentResult {}
    record Failed(String reason, ErrorCode errorCode) implements PaymentResult {}
    record Pending(Instant retryAfter) implements PaymentResult {}
}
```

### Requirements for permitted subclasses

1. Must be declared in the `permits` clause (unless defined in the same file).
2. Must belong to the same package or named module.
3. Must explicitly declare one of three modifiers:
   - `final`: No further extension permitted.
   - `sealed`: Subclass is also sealed with its own permits.
   - `non-sealed`: Subclass is open for unrestricted extension.

### Why sealed types transform domain modeling

Prior to Java 17, Java could not model **Algebraic Data Types (Sum types)**. A class was either entirely open to subclassing or completely closed (`final`). Sealed types let domain architects define a closed set of possibilities:

```java
public String handle(PaymentResult result) {
    return switch (result) {
        case PaymentResult.Success s -> "Paid: " + s.transactionId();
        case PaymentResult.Failed f -> "Failed: " + f.reason();
        case PaymentResult.Pending p -> "Pending until: " + p.retryAfter();
        // NO DEFAULT BRANCH NEEDED! Compiler verifies exhaustiveness!
    };
}
```
If someone adds a new `Cancelled` permit, the code will fail to compile everywhere the switch is used until the new branch is handled.

### Common follow-ups

- **Sealed vs Final:** `final` allows zero subclasses; `sealed` allows a strictly controlled list of subclasses.
- **Sealed vs Enums:** Enums represent fixed single-instance constants. Sealed hierarchies represent fixed *types* where each variant can have distinct fields, constructors, and instance state.

### Mistakes to avoid

- Adding a redundant `default:` case in switch expressions over sealed types — this suppresses compiler warnings when a new permitted subtype is introduced.

### Production perspective

Sealed types combined with records provide type-safe, bug-free domain modeling for business results, workflow states, and event hierarchies in financial and enterprise systems.

---

## Q017 — Pattern Matching for instanceof and switch

**The one-line answer:** Pattern matching reduces casting ceremony by binding type-tested variables directly; in Java 21, pattern matching switch provides guarded expressions and compiler-enforced exhaustiveness across complex types.

### Pattern matching for `instanceof` (Java 16+)

```java
// OLD WAY:
if (obj instanceof Order) {
    Order o = (Order) obj; // Redundant cast
    o.process();
}

// MODERN PATTERN MATCHING:
if (obj instanceof Order o && o.isActive()) { // o is in scope right here!
    o.process();
}
```

### Pattern matching for `switch` in Java 21 (JEP 441)

Java 21 delivers production pattern matching switch with **guards (`when`)** and **explicit null handling**:

```java
public String formatNotification(Notification n) {
    return switch (n) {
        case EmailNotification e when e.isUrgent() -> "URGENT EMAIL to: " + e.recipient();
        case EmailNotification e -> "Standard email to: " + e.recipient();
        case SmsNotification s -> "SMS to: " + s.phoneNumber();
        case PushNotification p -> "Push notification";
        case null -> throw new IllegalArgumentException("Notification cannot be null");
    };
}
```

### Record patterns (Java 21 destructuring)

Java 21 lets you destructure records directly inside the pattern:
```java
if (obj instanceof Order(UUID id, Money(BigDecimal amount, Currency curr))) {
    System.out.println("Order " + id + ": " + amount + " " + curr);
}
```

### Common follow-ups

- **Ordering of cases:** More specific pattern cases must precede broader pattern cases, or the compiler reports an unreachable code error.
- **Handling null:** In classic switch, `switch (null)` threw `NullPointerException`. In Java 21, you can declare `case null -> ...` or combine `case null, default -> ...`.

### Mistakes to avoid

- Forgetting that pattern variables obey scope rules: `if (!(obj instanceof Order o)) return; o.process();` is valid because `o` is definitely assigned if the method didn't return!

### Production perspective

Pattern matching turns convoluted visitor patterns and nested `if-else` casts into concise, declarative, compiler-checked business decision tables.

---

## Q018 — Advanced Enums

**The one-line answer:** Enums in Java are full-fledged classes extending `java.lang.Enum` that can hold state, constructors, and abstract methods with constant-specific implementations (the Enum Strategy Pattern).

### Constant-specific behavior (Strategy Pattern)

Instead of huge switch statements inside services, enums can encapsulate behavioral variations directly:

```java
public enum DiscountStrategy {
    REGULAR {
        @Override public BigDecimal calculate(BigDecimal amount) {
            return amount;
        }
    },
    VIP {
        @Override public BigDecimal calculate(BigDecimal amount) {
            return amount.multiply(BigDecimal.valueOf(0.85)); // 15% off
        }
    },
    EMPLOYEE {
        @Override public BigDecimal calculate(BigDecimal amount) {
            return amount.multiply(BigDecimal.valueOf(0.70)); // 30% off
        }
    };

    public abstract BigDecimal calculate(BigDecimal amount);
}
```

### Specialized collections: `EnumMap` and `EnumSet`

- `EnumMap`: An extremely fast, compact map where keys are enums. Internally backed by a plain array indexed by ordinal. Zero hash collisions, lower memory than `HashMap`.
- `EnumSet`: A high-performance set of enums backed by a single `long` bitmask (up to 64 enums) or bit vector. Bitwise speed for `contains`, `add`, and set operations.

### JPA persistence gotcha: Ordinal vs String

```java
// DISASTER: Stores 0, 1, 2 in database
@Enumerated(EnumType.ORDINAL) 
private OrderStatus status; // Reordering or inserting a new constant corrupts all DB data!

// SAFE: Stores "PENDING", "SHIPPED"
@Enumerated(EnumType.STRING)
private OrderStatus status;
```
For production resilience, prefer a custom JPA `AttributeConverter` storing an explicit immutable code.

### Common follow-ups

- **Singleton via Enum:** Joshua Bloch highlights a single-element enum (`public enum AppConfig { INSTANCE; ... }`) as the safest implementation of a Singleton because the JVM guarantees thread-safety, serialization safety, and protection against reflection instantiation attacks.

### Mistakes to avoid

- Modifying mutable state inside an enum constant. Enum constants are static singletons; internal mutable state creates severe multi-threaded race conditions.

### Production perspective

Enums excel at modeling state machines, rate limits, role permissions, and pricing tiers. Always pair them with `EnumMap` when grouping or caching by enum key.

---

## Q019 — Annotations and Reflection Basics

**The one-line answer:** Annotations provide metadata about code elements, while Reflection allows inspecting, instantiating, and invoking classes, methods, and fields dynamically at runtime.

### Annotation retention policies

```java
@Retention(RetentionPolicy.RUNTIME) // Critical for Spring/JPA!
@Target(ElementType.METHOD)
public @interface Audited {
    String action() default "GENERAL";
}
```

| Retention Policy | Retained In | Available via Reflection? | Examples |
|---|---|---|---|
| `SOURCE` | Discarded during compilation | No | `@Override`, `@SuppressWarnings`, Lombok |
| `CLASS` | Stored in `.class` file, discarded by JVM | No | Bytecode weaving tools (AspectJ) |
| `RUNTIME` | Stored in JVM memory / Metaspace | Yes | Spring's `@Service`, `@Transactional`, JPA `@Entity` |

### How Spring uses Reflection and Proxies

When Spring Boot boots up:
1. It scans classpath `.class` files and uses reflection to detect `@Component`, `@Service`, etc.
2. It reflects on constructors to perform Dependency Injection.
3. For transactional or secured beans, Spring uses **CGLIB** (subclassing) or **JDK Dynamic Proxies** (interfaces) to wrap the target bean and intercept method calls.

### The dark side of Reflection

1. **Performance cost:** Bypasses JIT optimizations, inlining, and access checks.
2. **Breaks encapsulation:** Accessing private fields via `field.setAccessible(true)` bypasses invariants.
3. **Java Module System (Java 9+):** Strongly encapsulates internal packages; reflective access requires explicit `opens <package> to <module>` directives in `module-info.java`.

### Common follow-ups

- **How do modern frameworks avoid reflection?** Micronaut and Quarkus perform compile-time annotation processing (Ahead-Of-Time compilation), eliminating runtime reflection to achieve instantaneous startup.

### Mistakes to avoid

- Using reflection in hot-path business logic (e.g. per-request JSON mapping loops).
- Hardcoding string method names in `Class.getMethod("badMethod")` which breaks silently upon refactoring.

### Production perspective

Frameworks cache reflected `Method` and `Field` handles on startup to minimize runtime overhead. Write application logic with typed interfaces rather than custom reflection.

---

## Q020 — Serialization and serialVersionUID

**The one-line answer:** Java native serialization converts object graphs to byte streams via `Serializable`, using `serialVersionUID` to verify version compatibility; however, native serialization is deprecated in modern architecture due to severe remote-code-execution security risks.

### What `serialVersionUID` does

`serialVersionUID` is a version identifier for a `Serializable` class:
```java
public class UserSession implements Serializable {
    private static final long serialVersionUID = 1L;
    private String userId;
    private transient String password; // NOT serialized!
}
```
If you do not declare `serialVersionUID`, the JVM calculates one at runtime by hashing class methods, fields, and interfaces. If you add even a single comment-less method or field, the computed ID changes, and deserializing older saved objects throws `InvalidClassException`.

### Why Java native serialization is a production hazard

1. **Remote Code Execution (RCE) / Gadget Chains:** Deserializing untrusted data allows attackers to construct object graphs that execute arbitrary code upon deserialization (e.g., Apache Commons Collections vulnerability).
2. **Bypasses constructors:** Native deserialization creates objects without calling any constructor, bypassing validation and invariant enforcement.

### Modern alternatives

Always use schema-based, transport-independent serialization in backend services:
- **REST APIs:** JSON via Jackson or Gson.
- **Inter-service RPC:** Protocol Buffers (gRPC) or Apache Avro.
- **Caching (Redis):** JSON or binary Protobuf serializers, never Java native `JdkSerializationRedisSerializer`.

### Common follow-ups

- **The `transient` keyword:** Marks fields that must be skipped during serialization (passwords, cached counters, database connections).
- **How records serialize:** Records serialize based solely on their state components and deserialize strictly via the canonical constructor, avoiding security vulnerabilities.

### Mistakes to avoid

- Leaving `JdkSerializationRedisSerializer` as the default serializer in Spring Data Redis.
- Relying on native serialization for persistent caching across application version deployments.

### Production perspective

Modern production environments ban Java native deserialization from network inputs. Use static code analysis tools (SpotBugs/Checkmarx) to flag native deserialization endpoints.

---

## Q021 — Date and Time API

**The one-line answer:** Use `java.time` (JSR-310) immutable types: `Instant` for UTC machine timestamps and database storage, `LocalDate`/`LocalTime` for wall-clock concepts without timezone, and `ZonedDateTime`/`OffsetDateTime` for timezone-aware business operations.

### Type decision matrix

| Type | Represents | Best Use Case | Database Mapping |
|---|---|---|---|
| `Instant` | Point on UTC timeline (epoch nanoseconds) | Audit logs, `createdAt`, `updatedAt` | `TIMESTAMP WITH TIME ZONE` |
| `LocalDate` | Civil date (year, month, day) | Birthdays, official holidays | `DATE` |
| `LocalDateTime` | Civil date + time without timezone | Store opening hours, alarm clock | `TIMESTAMP` (without time zone) |
| `OffsetDateTime` | Date + time with fixed UTC offset (`+02:00`) | REST API ISO-8601 payloads | `TIMESTAMPTZ` |
| `ZonedDateTime` | Date + time with full timezone rules & DST | Flight arrivals, recurring events | Store Instant + ZoneId separately |

### Why legacy `Date` and `SimpleDateFormat` were broken

1. `java.util.Date` is mutable; calling `date.setTime()` breaks encapsulation.
2. `SimpleDateFormat` is **NOT thread-safe**. Sharing an instance across threads corrupts date strings and throws sporadic exceptions.
3. Month was 0-indexed (January = 0), causing endless off-by-one errors.

### Production best practices

```java
// ALWAYS use UTC on the backend
Instant now = Instant.now();

// Inject Clock for testable time!
@Service
public class OrderService {
    private final Clock clock; // Inject Clock.systemUTC() in prod, Clock.fixed() in tests
    public OrderService(Clock clock) { this.clock = clock; }

    public Order createOrder() {
        return new Order(Instant.now(clock));
    }
}
```

### Common follow-ups

- **Duration vs Period:** `Duration` measures machine time in seconds/nanoseconds (`Duration.ofMinutes(15)`); `Period` measures conceptual date-based time in years, months, and days (`Period.ofMonths(3)`).
- **Daylight Saving Time (DST):** When adding a day to `ZonedDateTime`, Java adjusts for 23-hour or 25-hour days caused by DST transitions.

### Mistakes to avoid

- Storing local server time in database columns instead of UTC.
- Using `LocalDateTime` for financial transaction timestamps (loss of UTC offset context).

### Production perspective

Standardize on ISO-8601 strings (`2026-10-08T08:30:00Z`) at API boundaries and `Instant` in domain entities. Inject a `Clock` bean in Spring Boot to make time-dependent unit tests deterministic.

---

## Q022 — Autoboxing and Wrapper Pitfalls

**The one-line answer:** Autoboxing automatically converts between primitives and wrappers, but introduces subtle bugs including the Integer Cache equality trap, silent `NullPointerException` on unboxing, and severe memory and GC overhead in hot loops.

### The Integer Cache equality trap

Java caches `Integer` objects between `-128` and `127` (inclusive) via `Integer.valueOf()`:

```java
Integer a = 100;
Integer b = 100;
System.out.println(a == b); // TRUE (same cached object reference)

Integer x = 200;
Integer y = 200;
System.out.println(x == y); // FALSE! (distinct heap instances outside cache)
System.out.println(x.equals(y)); // TRUE (compares values)
```
**Rule:** ALWAYS compare wrapper objects using `.equals()`, never `==`.

### Unboxing NullPointerException

If an unboxed wrapper is null, the JVM throws an immediate NPE:
```java
Integer count = null;
int total = count + 1; // Throws NullPointerException! JVM executes count.intValue()
```

### Memory and GC performance bloat

- A primitive `int` takes **4 bytes**.
- An `Integer` object takes **24 bytes** on a 64-bit JVM (16-byte object header + 4-byte int + 4-byte padding) plus an 8-byte reference pointer.
- Inside a collection of 1,000,000 numbers, `List<Integer>` consumes ~32MB versus ~4MB for a primitive array.
- In tight computation loops, repeated autoboxing causes massive YoungGen allocation and GC churn:
  ```java
  // TERRIBLE: Autoboxes on every iteration, creating 10M Integer objects!
  Long sum = 0L;
  for (long i = 0; i < 10_000_000; i++) { sum += i; }

  // PROPER: Pure primitive execution
  long sum = 0L;
  for (long i = 0; i < 10_000_000; i++) { sum += i; }
  ```

### Common follow-ups

- **Do other wrappers have caches?** `Byte`, `Short`, `Long` cache `-128` to `127`. `Character` caches `0` to `127`. `Boolean.TRUE` and `Boolean.FALSE` are cached. `Float` and `Double` have **NO** cache.
- **Primitive streams:** Use `IntStream`, `LongStream`, `DoubleStream` to avoid boxing overhead during stream processing.

### Mistakes to avoid

- Using wrappers for entity IDs or balances without null checks before math operations.
- Using boxed collections for high-throughput numeric crunching.

### Production perspective

In high-throughput microservices, avoiding unnecessary boxing in loops and using primitive streams or specialized collections directly reduces CPU cycles and GC pause frequencies.

---

## Q023 — final, finally, finalize

**The one-line answer:** `final` is an immutability/restriction modifier on variables, methods, and classes; `finally` is a cleanup block that executes after try/catch; `finalize()` is a legacy, broken GC hook deprecated for removal that must never be used.

### Breakdown of each keyword

#### 1. `final`
- **Variable:** Cannot be reassigned. (If referencing an object, internal state can still mutate).
- **Method:** Cannot be overridden by subclasses (allows JIT inlining).
- **Class:** Cannot be extended (e.g. `String`, `Integer`, records).
- **JMM guarantee:** Final fields initialized in constructors are safely published across threads without race conditions.

#### 2. `finally`
Executes guaranteed cleanup after a `try` block, regardless of exceptions or return statements:
```java
try {
    return compute();
} finally {
    cleanUp(); // Executes BEFORE return completes!
}
```
**When does `finally` NOT execute?**
1. `System.exit(0)` is called.
2. The JVM crashes (SIGKILL, OutOfMemoryError in thread creation).
3. The host machine loses power or kernel dies.
4. An infinite loop occurs inside the `try` block.

*Anti-pattern:* Never write `return` inside a `finally` block — it swallows and silences any exception thrown in the `try` block!

#### 3. `finalize()`
Historically invoked by garbage collector before reclaiming an object.
- **Why it was deprecated:** Timing was completely unpredictable, degraded GC throughput, caused deadlocks, and allowed objects to "resurrect" themselves.
- **Replacement:** Use `try-with-resources` with `AutoCloseable`, or `java.lang.ref.Cleaner` for low-level native resource disposal.

### Common follow-ups

- **Can you alter a `final` field via reflection?** Be precise here. `Field.set()` on a `final` field normally throws `IllegalAccessException`, and calling `setAccessible(true)` on a `final` instance field of a plain class can still succeed on Java 17. What genuinely blocks it is a `static final` field, a record component, or a hidden class. Treat `final` as immutable by contract, and never rely on reflection to break it.

### Mistakes to avoid

- Trusting `finalize()` to close database connections or files.
- Overusing `try-finally` when `try-with-resources` is cleaner and safer.

### Production perspective

Resource leaks must be managed deterministically at the application layer via `AutoCloseable` and connection pools, never delegated to GC finalizers.

---

## Q024 — Core Functional Interfaces

**The one-line answer:** Java 8+ provides four foundational functional interfaces in `java.util.function`: `Predicate<T>` (boolean test), `Function<T, R>` (mapping/transformation), `Supplier<T>` (lazy factory), and `Consumer<T>` (side-effect consumer).

### The core four

| Interface | Method Signature | Purpose | Typical Stream Usage |
|---|---|---|---|
| `Predicate<T>` | `boolean test(T t)` | Condition check / filtering | `stream.filter(predicate)` |
| `Function<T, R>` | `R apply(T t)` | Transformation / mapping | `stream.map(function)` |
| `Consumer<T>` | `void accept(T t)` | Terminal side-effect | `stream.forEach(consumer)` |
| `Supplier<T>` | `T get()` | Factory / lazy evaluation | `optional.orElseGet(supplier)` |

### Two-argument and operator specializations

- **Bi-variants:** `BiPredicate<T, U>`, `BiFunction<T, U, R>`, `BiConsumer<T, U>`.
- **Operators:** `UnaryOperator<T>` (specialized `Function<T, T>`), `BinaryOperator<T>` (specialized `BiFunction<T, T, T>` used in `reduce()`).
- **Primitive specializations:** `IntPredicate`, `ToLongFunction<T>`, `DoubleConsumer` avoid autoboxing.

### Composing functional interfaces

Functional interfaces have built-in default methods for chaining pipelines:
```java
// Predicate composition
Predicate<Order> isPaid = Order::isPaid;
Predicate<Order> isShipped = Order::isShipped;
Predicate<Order> requiresAttention = isPaid.and(isShipped.negate());

// Function chaining (andThen vs compose)
Function<Integer, Integer> times2 = x -> x * 2;
Function<Integer, Integer> plus3 = x -> x + 3;

times2.andThen(plus3).apply(5); // (5 * 2) + 3 = 13
times2.compose(plus3).apply(5); // (5 + 3) * 2 = 16
```

### Common follow-ups

- **What makes an interface functional?** Having exactly one abstract method (Single Abstract Method - SAM). The `@FunctionalInterface` annotation is optional but recommended as it causes compiler verification.
- **Can a functional interface have default methods?** Yes, any number of `default` and `static` methods, as well as public methods matching `java.lang.Object` (like `equals`).

### Mistakes to avoid

- Writing heavy business logic with side effects inside `Function` or `Predicate`.
- Nesting functional compositions so deeply that debugging stack traces becomes impossible.

### Production perspective

Functional composition provides clean, reusable rule engines (validation pipelines, discount strategies, eligibility filters) that are trivial to test in isolation.

---

## Q025 — Lambdas and Effectively Final

**The one-line answer:** Lambdas are anonymous implementations of functional interfaces that can capture enclosing local variables only if those variables are "effectively final" (never reassigned after initialization).

### Why the "effectively final" rule exists

Local variables live on the thread's **stack frame**. When a lambda is created, it may be executed asynchronously on another thread (e.g. `CompletableFuture`) long after the enclosing method has returned and its stack frame has been destroyed!
To make this work, the JVM **copies** the local variable into the lambda's heap object:
- If Java allowed the local variable to be modified, the stack variable and the lambda's copied variable would get out of sync.
- True mutable closures across threads would require complex shared-variable heap promotion and synchronization locks.
Hence, Java enforces that local variables must be assigned exactly once:

```java
int port = 8080; // effectively final
Runnable r = () -> System.out.println("Listening on " + port); // OK!

int count = 0;
// orders.forEach(o -> count++); // COMPILE ERROR: count is mutated!
```

### Capturing instance fields vs local variables

Instance fields are stored on the **heap**, not the stack. Lambdas can freely read and mutate instance fields because the lambda captures `this` (the stable object reference on the heap):
```java
public class Worker {
    private int processed = 0;
    public void run() {
        orders.forEach(o -> this.processed++); // Allowed, but NOT thread-safe in parallel streams!
    }
}
```

### Four types of Method References

| Type | Syntax | Lambda Equivalent |
|---|---|---|
| Static method | `Math::max` | `(a, b) -> Math.max(a, b)` |
| Bound instance | `order::calculateTotal` | `() -> order.calculateTotal()` |
| Unbound instance | `String::toLowerCase` | `(str) -> str.toLowerCase()` |
| Constructor | `ArrayList::new` | `() -> new ArrayList<>()` |

### Common follow-ups

- **How are lambdas compiled?** Unlike anonymous inner classes (which generate `MyClass$1.class` files on disk), lambdas compile to an `invokedynamic` instruction calling `LambdaMetafactory`, generating lightweight call-site instances dynamically.
- **Lexical scoping difference:** An anonymous class introduces its own scope (`this` refers to the anonymous class); a lambda shares the lexical scope of the enclosing class (`this` refers to the enclosing instance).

### Mistakes to avoid

- Using single-element arrays (`int[] count = {0};`) or `AtomicInteger` to bypass effectively-final rules inside parallel streams — this introduces race conditions or cache-line bouncing.

### Production perspective

Prefer stream aggregation operations (`count()`, `reduce()`, `collect()`) over mutating captured variables. It is cleaner, thread-safe, and parallel-ready.

---

## Q026 — NullPointerException Avoidance Strategies

**The one-line answer:** Prevent NullPointerExceptions by establishing a zero-null policy: return empty collections or Optional instead of null, validate parameters at boundaries with `Objects.requireNonNull()`, and leverage Java 14+ helpful NPE diagnostics.

### 5 production strategies for zero-NPE services

1. **Never return null for collections or arrays:**
   ```java
   public List<Order> getOrders() {
       return orders == null ? Collections.emptyList() : orders;
   }
   ```
2. **Use `Optional` strictly for return types where absence is expected:**
   ```java
   public Optional<User> findByEmail(String email) { ... }
   ```
3. **Fail-fast validation at public service and domain boundaries:**
   ```java
   public Order(CustomerId customerId, Money total) {
       this.customerId = Objects.requireNonNull(customerId, "customerId cannot be null");
       this.total = Objects.requireNonNull(total, "total cannot be null");
   }
   ```
4. **Yoda-style or safe equals on literals:**
   ```java
   if ("COMPLETED".equals(order.getStatus())) { ... } // Safe even if getStatus() is null!
   // Vs: if (order.getStatus().equals("COMPLETED")) // NPE if getStatus() is null
   ```
5. **Static analysis annotations:** Use `@NonNull` / `@Nullable` (from `jakarta.annotation` or SpotBugs) enforced via build tools like NullAway or ErrorProne.

### Helpful NullPointerExceptions in modern Java (Java 14+)

In Java 14+, the JVM pinpoints the exact expression that was null:
```
Cannot invoke "com.example.Address.getZipCode()" because the return value of "com.example.User.getAddress()" is null
```
This saves hours of production troubleshooting compared to legacy single-line NPE messages.

### Common follow-ups

- **Null Object Pattern:** Replacing null with a no-op implementation of an interface (e.g. `EmptyDiscount` or `AnonymousUser`) to eliminate null checks.

### Mistakes to avoid

- Checking for null everywhere inside internal private methods (clutters code). Enforce non-nullity at the edge/constructor, so internal code can assume valid state.

### Production perspective

Eliminating null references at the domain boundary with records and value objects prevents corrupt data from silently poisoning caches and databases.

---

## Q027 — Unicode and UTF-8 Basics for Backend Strings

**The one-line answer:** Java `char` is a 16-bit UTF-16 code unit, which cannot store 4-byte supplementary characters (such as emojis) in a single char; backend systems must handle code points correctly and ensure UTF-8 encoding across databases and HTTP payloads.

### The Unicode trap: `length()` vs visible characters

In Java, `String.length()` counts **16-bit code units**, NOT characters:
```java
String rocket = "🚀"; // Unicode code point U+1F680 (requires 2 UTF-16 surrogate chars)
System.out.println(rocket.length()); // PRINTS 2, NOT 1!

// True character (code point) count:
int realLength = rocket.codePointCount(0, rocket.length()); // PRINTS 1!
```
Iterating with `for (int i = 0; i < s.length(); i++) s.charAt(i)` corrupts emojis by splitting surrogate pairs. Always use `string.codePoints()` when inspecting characters.

### UTF-8 in backend production

- **UTF-8 is variable-length:** ASCII characters take 1 byte; accented Latin takes 2 bytes; Chinese/Japanese/Korean takes 3 bytes; emojis take 4 bytes.
- **MySQL `utf8` vs `utf8mb4` disaster:** In MySQL, `utf8` historically only allocated 3 bytes per character. Inserting an emoji into a `utf8` column crashes with `Incorrect string value`. Modern schemas must always use `utf8mb4`.
- **String byte length vs character length:** Validating `string.length() <= 255` does not guarantee it fits into a 255-byte column or payload! Four-byte emojis can cause byte overflow.

### Explicit character set encoding

Never rely on platform default encoding:
```java
// BAD: Uses OS default charset (windows-1252 or whatever the server has)
byte[] bytes = str.getBytes(); 

// GOOD: Always specify StandardCharsets.UTF_8
byte[] bytes = str.getBytes(StandardCharsets.UTF_8);
String decoded = new String(bytes, StandardCharsets.UTF_8);
```

### Common follow-ups

- **HTTP Charset:** Always ensure HTTP headers specify `Content-Type: application/json; charset=utf-8`.

### Mistakes to avoid

- Using `getBytes("UTF-8")` which throws checked `UnsupportedEncodingException`; use `StandardCharsets.UTF_8` which is type-safe and never throws.

### Production perspective

Internationalized text, customer names with accents, and emojis in user feedback break legacy systems. Always configure UTF-8 in database connection strings, Docker containers (`LANG=C.UTF-8`), and serialization libraries.

---

## Q028 — Cloning and Copy Constructors

**The one-line answer:** Java's `Cloneable` interface and `Object.clone()` are deeply flawed and should be avoided; use copy constructors, static factory methods, or defensive copies for creating duplicates of objects.

### Why `Cloneable` is broken (Joshua Bloch's assessment)

1. `Cloneable` is a marker interface that has no methods, yet `clone()` is declared `protected` on `java.lang.Object`.
2. It allocates memory reflectively without calling any constructor, bypassing validation and initialization rules.
3. Default `super.clone()` performs a **shallow copy** — references to nested mutable objects are shared between the clone and the original.
4. It forces handling checked `CloneNotSupportedException`.

### The idiomatic alternatives

#### 1. Copy Constructor
```java
public class Order {
    private final String id;
    private final List<OrderItem> items;

    // Copy constructor
    public Order(Order other) {
        this.id = other.id;
        // Deep copy of mutable list items
        this.items = other.items.stream().map(OrderItem::new).toList();
    }
}
```

#### 2. Static Copy Factory
```java
public static Order copyOf(Order other) {
    return new Order(other);
}
```

### Shallow copy vs Deep copy

- **Shallow copy:** Duplicates the parent object, but internal collection references still point to the same memory addresses. Mutating a child element alters both objects!
- **Deep copy:** Recursively duplicates all nested objects throughout the object graph.

### Common follow-ups

- **How to perform deep copies of complex object graphs?** For complex trees, using a copy constructor chain is fastest. Alternatively, serialize and deserialize via Jackson or Protobuf, though this carries performance overhead.
- **Records eliminate the need for cloning:** Records are shallowly immutable. New variations can be constructed cleanly using copy expressions or builder patterns.

### Mistakes to avoid

- Implementing `Cloneable` in new classes.
- Assuming `new ArrayList<>(originalList)` creates a deep copy — it creates a new list containing references to the exact same elements!

### Production perspective

In domain-driven design, entities have identity and should rarely be cloned. For value objects and DTOs, use immutable records or explicit copy constructors to avoid hidden state aliasing.

---

## Q029 — Class Loading Basics

**The one-line answer:** Class loading loads bytecode into Metaspace through a three-phase process (Loading, Linking, Initialization) governed by the hierarchical Delegation Model; understanding class loading is essential for diagnosing `ClassNotFoundException` versus `NoClassDefFoundError`.

### The three phases of class loading

1. **Loading:** Reads binary `.class` byte streams from disk or network and creates a `Class<?>` object in JVM Metaspace.
2. **Linking:**
   - *Verification:* Verifies bytecode adheres to JVM specifications and type safety rules.
   - *Preparation:* Allocates memory for `static` fields and initializes them to default values (`0`, `null`).
   - *Resolution:* Resolves symbolic references into direct memory pointers.
3. **Initialization:** Executes class static initializers (`static { ... }`) and assigns explicit values to static fields.

### The ClassLoader Hierarchy & Delegation Model

```
Bootstrap ClassLoader (C++ / native JDK core modules: java.base)
       ▲
Platform / Extension ClassLoader (JDK extensions, security providers)
       ▲
Application / System ClassLoader (Application classpath / JARs)
       ▲
Custom ClassLoaders (Spring Boot nested JARs, Tomcat webapp isolation)
```
**Parent Delegation Principle:** When a ClassLoader needs to load a class, it delegates the request to its parent first. Only if the parent hierarchy fails to find the class does the child attempt to load it from its own classpath.

### `ClassNotFoundException` vs `NoClassDefFoundError`

| Exception / Error | Category | When it happens | Root Cause |
|---|---|---|---|
| `ClassNotFoundException` | Checked Exception | Dynamic runtime lookup via reflection (`Class.forName()` or `loadClass()`) | The class name does not exist on the classpath at runtime. |
| `NoClassDefFoundError` | Fatal `Error` | Compile-time class resolution during code execution | The class was present at compile time, but missing from classpath at runtime, OR static initialization of that class previously crashed with an unhandled exception (`ExceptionInInitializerError`)! |

### Common follow-ups

- **How does Spring Boot package executable JARs?** Spring Boot uses its custom `LaunchedURLClassLoader` to load nested JAR dependencies packaged inside `BOOT-INF/lib/` without requiring exploded folders.

### Mistakes to avoid

- Catching `Exception` and expecting it to catch `NoClassDefFoundError` — it is an `Error`, not an `Exception`!
- Putting heavy, failure-prone logic inside static initialization blocks.

### Production perspective

`NoClassDefFoundError` in production almost always points to incompatible third-party dependency versions on the classpath (dependency conflicts / diamond dependencies in Maven/Gradle) or a failed static initializer during startup.

---

## Q030 — Java 17 vs Java 21 for Backend Developers

**The one-line answer:** While Java 17 introduced sealed types, records, and pattern matching for instanceof, Java 21 represents a monumental leap for backend scalability with Virtual Threads (Project Loom), pattern matching switch, sequenced collections, and Generational ZGC.

### Major feature comparison

| Feature Area | Java 17 (LTS) | Java 21 (LTS) | Backend Impact |
|---|---|---|---|
| **Concurrency** | Platform threads (1 OS thread per Java thread) | **Virtual Threads** (JEP 444) | High-throughput blocking I/O without reactive complexity |
| **Pattern Matching** | `instanceof` pattern matching | **Pattern Matching for switch** & Record patterns | Declarative, compiler-enforced business rule processing |
| **Collections** | Standard collections | **Sequenced Collections** (JEP 431) | Unified `getFirst()`, `getLast()`, `reversed()` across List, Deque, Set |
| **Garbage Collection** | G1 GC default, ZGC non-generational | **Generational ZGC** (JEP 439) | Sub-millisecond pause times with high throughput and lower CPU overhead |
| **String formatting** | Text blocks, `String.format` | String templates (preview — see caveat below) | Safer SQL and JSON string building |

> **String templates caveat:** JEP 430 previewed string templates (`STR."..."`) in Java 21 and 22, but they were **withdrawn in Java 23 and are still not final**. They have not shipped in any LTS. Say "previewed, not yet final" rather than "preview in 21" — and note that most production code still uses `String.format`, text blocks, or Jackson's `JsonMapper` for this.

### Virtual Threads in production (The game changer)

Virtual threads decouple Java thread count from OS thread limits. Millions of virtual threads can run concurrently:
```java
// Spring Boot 3.2+ application.properties:
// spring.threads.virtual.enabled=true
```
When a virtual thread executes blocking I/O (database query, REST client call), the JVM unmounts it from the carrier OS thread. The OS thread immediately processes another virtual thread.

### The Virtual Thread Pinning Caveat

A virtual thread cannot unmount if blocked inside a `synchronized` block or method (pinning). In Java 21, replace hot `synchronized` blocks with `ReentrantLock` to avoid starving carrier threads!

### Sequenced Collections (JEP 431)

```java
LinkedHashSet<String> set = new LinkedHashSet<>();
set.addFirst("alpha");
set.addLast("omega");
String first = set.getFirst();
String last = set.getLast();
SequencedSet<String> reversed = set.reversed(); // Ordered reverse view!
```

### Common follow-ups

- **Should CPU-bound applications use Virtual Threads?** No. Virtual threads provide zero advantage for CPU-bound tasks (cryptography, video transcoding); they excel exclusively for blocking I/O (microservice calls, database queries).
- **LTS Migration Path:** Upgrading from Java 17 to Java 21 is binary compatible and requires minimal effort in Spring Boot 3.x, providing immediate throughput gains.

### Mistakes to avoid

- Pooling virtual threads with an `ExecutorService` pool. Virtual threads are short-lived and should never be pooled; spawn a new virtual thread per task!
- Leaving `ThreadLocal` holding huge memory buffers when running millions of virtual threads.

### Production perspective

Java 21 delivers the throughput advantages of reactive architectures (like WebFlux) using standard, readable imperative code, drastically simplifying backend development and production debugging.
