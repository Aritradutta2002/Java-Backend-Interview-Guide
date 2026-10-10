> **GENERATED FILE - DO NOT EDIT DIRECTLY.**
>
> Source of truth is `chapters/*.md` and `extras/*.md`.
>
> Rebuild with `node scripts/build.mjs` (add `--strict-template` to enforce the answer template).

# Top 200 Java Backend Developer Interview Questions and Answers - 3-5 Years Experience

## Contents

- [Chapter 1](#chapter-1)
- [Chapter 2](#chapter-2)
- [Chapter 3](#chapter-3)
- [Chapter 4](#chapter-4)
- [Chapter 5](#chapter-5)
- [Chapter 6](#chapter-6)
- [Chapter 7](#chapter-7)
- [Chapter 8](#chapter-8)
- [Chapter 9](#chapter-9)
- [Chapter 10](#chapter-10)
- [Highest-Priority Questions to Revise First](#top-40)
- [How to Use This Book & 7-Day Study Plan](#study-plan)
- [Practical Mini-Exercises](#mini-exercises)
- [Glossary](#glossary)

<a id="chapter-1"></a>

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


<a id="chapter-2"></a>

# Chapter 2: Collections, Generics, Streams, and Functional Java

## Q031 — Choosing the Right Collection

**The one-line answer:** Pick the collection that enforces the contract your code needs — ordering, uniqueness, access pattern, and thread-safety — rather than defaulting to ArrayList everywhere.

### Decision framework

| Need | Reach for |
|---|---|
| Ordered list, random access | `ArrayList` |
| Ordered list, frequent head/tail mutation | `ArrayDeque` (not LinkedList) |
| Unique elements, no order needed | `HashSet` |
| Unique elements, insertion order | `LinkedHashSet` |
| Unique elements, sorted | `TreeSet` |
| Key→value, no order needed | `HashMap` |
| Key→value, insertion order | `LinkedHashMap` |
| Key→value, sorted keys | `TreeMap` |
| Key→value, enum keys | `EnumMap` |
| FIFO queue | `ArrayDeque` |
| Priority ordering | `PriorityQueue` |
| Thread-safe map | `ConcurrentHashMap` |
| Thread-safe list (read-heavy) | `CopyOnWriteArrayList` |

The default should be to declare the interface, not the implementation: `List<String> names = new ArrayList<>()`. That keeps the door open to swap `LinkedList` or an immutable list later without touching callers, and it is the difference between code that reads as intent and code that reads as implementation detail.

```java
// Pinned to an implementation — every caller now knows it is an ArrayList
ArrayList<String> names = new ArrayList<>();

// Declared as a contract — callers only know it is an ordered, indexable list
List<String> names = new ArrayList<>();
```

### What interviewers probe

- **Memory:** `LinkedList` has ~48 bytes per node overhead vs ~4 bytes per slot in `ArrayList`. Rarely worth it.
- **Thread safety:** `Vector`/`Hashtable` are synchronized but obsolete. Never recommend them. Use `ConcurrentHashMap` or `Collections.synchronizedXxx` only when truly needed.
- **Null policy:** `HashMap` allows one null key and null values. `TreeMap` allows null values but null keys throw `NullPointerException` (compareTo is called). `ConcurrentHashMap` allows neither.

### Common follow-ups

- **Why is `Vector` obsolete rather than just "old"?** It synchronizes every single operation, including reads, so it serializes concurrent access that does not need serializing. `ConcurrentHashMap` locks per bucket and reads lock-free, so it is both thread-safe and fast — there is no scenario where `Vector` is the better answer.
- **Why is `CopyOnWriteArrayList` read-heavy-only?** Every `add`/`set` copies the entire backing array. A read-heavy, write-rare list (listeners, feature-flag caches, route tables) is ideal; a list written on every request is a performance disaster.
- **What replaces `Hashtable` when I need sorted keys?** `ConcurrentSkipListMap` — sorted, thread-safe, O(log n), with no counterpart in the legacy collections.

### Mistakes to avoid

- Declaring the concrete type (`ArrayList<Order> orders = new ArrayList<>()`) instead of `List<Order>`.
- Reaching for `Collections.synchronizedList` because you saw "thread-safe" in the question; iteration still needs external synchronization, which almost always surprises people.
- Picking a collection for its asymptotics without checking the constant factor and memory layout — the reason `ArrayList` beats `LinkedList` is cache locality, not Big-O (see Q032).

### Production perspective

Choosing the right collection is a one-line decision with a long tail: the wrong choice shows up not as a crash but as a p99 latency curve that degrades as data grows, or as a `StackOverflowError`/`OutOfMemoryError` that only reproduces at production data volumes. In code review, this is the first thing I check — a `LinkedList` in a hot path or a `Vector` in new code is a reliable signal that nobody profiled the service.

---

## Q032 — ArrayList vs LinkedList

**The one-line answer:** Use `ArrayList` almost always. `LinkedList` is rarely better in practice because cache locality losses outweigh its O(1) insertion advantage.

### Complexity comparison

| Operation | ArrayList | LinkedList |
|---|---|---|
| `get(i)` | O(1) | O(n) |
| `add(end)` | O(1) amortized | O(1) |
| `add(middle)` | O(n) shift | O(n) traversal + O(1) link |
| `remove(middle)` | O(n) shift | O(n) traversal + O(1) unlink |
| Memory per element | ~4 bytes (reference) | ~48 bytes (Node object) |

### The myth about LinkedList insertions

The "O(1) insert" of `LinkedList` only holds once you already have the iterator positioned at the node. Getting to that position costs O(n). Most code does `list.add(index, element)` which is O(n) for both structures — but `LinkedList` is slower because pointer chasing defeats CPU cache prefetch.

Benchmark results consistently show `ArrayList` wins even for frequent middle insertions once the list is larger than a few hundred elements.

### When LinkedList is genuinely better

- You implement a **Deque** (double-ended queue) and need O(1) `addFirst`/`removeFirst` — but `ArrayDeque` is even faster for this.
- You hold an **iterator** and call `iterator.remove()` in a tight loop.

In practice, `ArrayDeque` replaces `LinkedList` for almost every real use case. Reach for `Queue`/`Deque` when the semantics of your code are "process in order" or "process by priority" — the interface makes the intent self-documenting, and `ArrayDeque` is faster than `LinkedList` for both stack and queue use cases.

### Common follow-ups

- **What about `CopyOnWriteArrayList` for a read-heavy list?** It has O(n) writes but O(1) lock-free reads and snapshot iterators. Perfect for listener registries and reference data; wrong for anything written per request.
- **Is `HashMap`'s O(1) really guaranteed?** O(1) *average* assuming a good `hashCode`. A deliberately bad `hashCode` degrades a bucket chain to O(n) — and even Java 8's treeification only helps once the chain exceeds 8 entries *and* the table has ≥ 64 buckets, so a small map with a terrible hash still walks a list.
- **When should a field be `List` vs `Set` vs array?** `Set` when uniqueness is a business rule you want the type system to enforce; `List` when order and duplicates are meaningful; array only at performance boundaries (and never leak it as a return type).

### Mistakes to avoid

- Sizing the initial capacity wrongly: `new ArrayList<>()` for a known 10,000-element result forces ~14 array resizes and copies. `new ArrayList<>(10_000)` does it once.
- Treating an `Iterable` returned from a service as safe to iterate twice; most streams and some lazy views are single-use.
- Assuming `Collections.unmodifiableList` makes something immutable — it does not, it is only a view. See Q038.

### Production perspective

`ArrayList` with a pre-sized capacity is the single cheapest performance win in backend Java. In export and report endpoints that build large lists, sizing the list up front removes repeated `Arrays.copyOf` churn and measurably reduces young-gen GC pressure.

---

## Q033 — HashMap Internals

**The one-line answer:** HashMap stores entries in an array of buckets, uses hash codes to assign buckets, chains collisions as a linked list, and converts long chains to red-black trees (Java 8+) to bound worst-case lookup to O(log n).

### Step by step: what happens on `put(key, value)`

1. `key.hashCode()` is called. HashMap applies a secondary hash: `(h = key.hashCode()) ^ (h >>> 16)` to spread high bits into low bits.
2. The bucket index is computed as `hash & (capacity - 1)` (bitwise AND, not modulo, because capacity is always a power of 2).
3. If the bucket is empty, the entry is placed directly.
4. If the bucket has existing entries, each key is checked with `==` then `equals`. On match, the value is replaced. On no match, the entry is appended.
5. **Treeification:** if a bucket's chain length exceeds `TREEIFY_THRESHOLD` (8) *and* the table size is ≥ `MIN_TREEIFY_CAPACITY` (64), the chain is converted to a red-black tree.
6. After insertion, if `size > capacity * loadFactor` (default 0.75), the table is **resized** to double capacity and all entries are rehashed.

### Why the default load factor is 0.75

It's a practical trade-off: 0.75 keeps average chain length below 1.5 while not wasting too much memory. A lower factor (e.g., 0.5) reduces collisions but wastes space. A higher factor (e.g., 0.9) packs more entries but increases collisions.

### Mutable key danger

If you mutate a key after it's been inserted, its `hashCode` changes, and you can no longer find the entry — it's still in the map but in the wrong bucket. Always use immutable keys (`String`, `Integer`, `UUID`).

### Interview gotchas

- `HashMap` is **not thread-safe**. Concurrent puts during resize can corrupt the internal structure (infinite loop in Java 6; data loss in Java 8+).
- The **worst case** before Java 8 was O(n) per lookup on hash collision attack. Treeification reduces it to O(log n).
- `HashMap` allows one `null` key (stored in bucket 0) and multiple `null` values.

### The Java 8 resize improvement

Before Java 8, resizing rehashed every entry by re-running the full hash and re-deriving the bucket, which was expensive and, combined with a race, could produce an infinite loop in Java 6. In Java 8+, each entry keeps its final hash, and during resize entries split into two lists: those whose `(hash & oldCapacity) == 0` stay at the same index, and those where it is `1` move to `index + oldCapacity`. This makes resize roughly twice as fast and removes the classic cyclic corruption.

### Common follow-ups

- **Why is capacity always a power of two?** Because the bucket index is computed with `hash & (capacity - 1)`, a bitwise AND that is only a correct modulo substitute when the capacity is a power of two. If it were not, high bits would be ignored and collisions would cluster badly.
- **What is `TREEIFY_THRESHOLD = 8` and `UNTREEIFY_THRESHOLD = 6`?** A bucket converts to a red-black tree at 8 entries and converts back at 6, provided the table is at least 64 buckets. The hysteresis avoids thrashing when entries hover at the boundary.
- **When does a bucket NOT treeify?** When the table is smaller than `MIN_TREEIFY_CAPACITY` (64). The map resizes first — the assumption is that a small table should grow rather than pay for tree node overhead.
- **How do I make a map thread-safe?** `ConcurrentHashMap` (see Q063). Do not wrap `HashMap` in `Collections.synchronizedMap` and assume iteration is safe — compound operations still need external locking.
- **Is the iteration order stable?** No. `HashMap` order depends on capacity and hash distribution and changes when the map resizes. Never write code or tests that depend on it. If you need determinism, use `LinkedHashMap` or `TreeMap` (Q034).

### Mistakes to avoid

- Using a mutable object as a key, or as an element of a `HashSet`. Mutating it after insertion orphans the entry — it is still in the map but unreachable, which is a memory leak rather than a bug you will see quickly.
- Writing a `hashCode()` that returns a constant to "avoid collisions" — that is the worst possible outcome, it turns every bucket into one long chain.
- Assuming `HashMap` scales across threads because a single-threaded microbenchmark looked fine.

### Production perspective

`HashMap` sizing is a real cost in hot paths. A per-request `new HashMap<>()` for a response that ends up holding 500 entries triggers several resizes; pre-sizing with the expected capacity is free. Equally, a `HashMap<SomeEnum, V>` where an `EnumMap` would do is paying hash computation and pointer chasing for something an array lookup gives you directly.

---

## Q034 — LinkedHashMap, TreeMap, EnumMap

**The one-line answer:** `LinkedHashMap` buys insertion-order (or access-order) iteration by threading a doubly-linked list through the entries, `TreeMap` buys sorted keys and range queries with a red-black tree, and `EnumMap` buys O(1) and minimum memory by indexing a plain array with the enum ordinal — pick based on which property your code actually reads, not on how they perform on the happy path.

### LinkedHashMap

Extends `HashMap`, maintains a **doubly-linked list** through all entries in insertion order (default) or access order.

- Access order mode (`new LinkedHashMap<>(16, 0.75f, true)`) moves each accessed entry to the tail — enabling a simple LRU cache.
- Override `removeEldestEntry` to evict automatically:

```java
new LinkedHashMap<>(capacity, 0.75f, true) {
    protected boolean removeEldestEntry(Map.Entry<K,V> eldest) {
        return size() > capacity;
    }
};
```

- Iteration is O(n) but predictable. Slightly more memory than `HashMap` per entry due to the prev/next pointers.

Because `LinkedHashMap` extends `HashMap` and *overrides* nothing about the lookup algorithm, all the hashing behaviour from Q033 still applies — including the mutable-key hazard.

### TreeMap

Backed by a **red-black tree**. Keys are sorted by natural order or a supplied `Comparator`.

- All core operations (`get`, `put`, `remove`) are O(log n).
- Unique methods: `floorKey`, `ceilingKey`, `headMap`, `tailMap`, `subMap` — invaluable for range queries.
- `null` keys are forbidden (comparator would need to handle null).

```java
TreeMap<Instant, Double> readings = new TreeMap<>();
readings.floorEntry(now);              // latest reading at or before now
readings.subMap(from, true, to, true); // [from, to] inclusive — O(log n) to locate
readings.descendingMap();              // reverse-order view, no copy
```

Note that `headMap`/`tailMap`/`subMap` return **views**, so mutating the view mutates the backing tree — the same trap as `Collections.unmodifiable*`.

### EnumMap

Keys must be enum constants. Internally backed by a plain **array** indexed by enum ordinal.

- O(1) for all operations, lower memory than `HashMap`.
- Iteration is in enum declaration order.
- Never use `HashMap<MyEnum, V>` when you can use `EnumMap<MyEnum, V>`.

```java
// No hashing, no boxing of the key, no collisions — just an array index
Map<OrderStatus, BigDecimal> totals = new EnumMap<>(OrderStatus.class);
```

### Common follow-ups

- **How is an LRU cache implemented with `LinkedHashMap`?** Construct it in access-order mode and override `removeEldestEntry` to return `size() > capacity`. `get()` promotes the entry to the tail, so the eldest entry at the head is the least recently used. Note it is **not** thread-safe — wrap it or use `ConcurrentHashMap` plus explicit ordering for a concurrent cache.
- **Why does `LinkedHashMap` use two pointers per entry?** One for the hash bucket's chain, one for the linked list. That is how it keeps both O(1) lookup and stable ordering.
- **`TreeMap` vs `ConcurrentSkipListMap`?** `TreeMap` is single-threaded. `ConcurrentSkipListMap` is the concurrent, sorted map — O(log n) with lock-free reads. Reach for it, not a synchronized `TreeMap`.
- **Can `EnumMap` be compared to `Object[]`?** Effectively yes, with bounds checking and enum-key safety. That is why it is the fastest map in the JDK.

### Mistakes to avoid

- Expecting `HashMap` iteration order to match `LinkedHashMap` order and writing a test that asserts a specific `HashMap` order — that test will fail the moment the map resizes.
- Using `TreeMap` with a `Comparator` whose ordering is inconsistent with `equals` (see Q006): the map will silently drop entries it considers duplicates.
- Using `EnumMap` for a map whose keys are not enums, then discovering at compile time — this is a good error, treat it as a signal that your key type is wrong.

### Production perspective

`EnumMap` is the default choice whenever a backend service groups data by a status enum — order-state rollups, per-region counters, metrics by outcome. It has zero hash cost, deterministic declaration-order iteration, and a tiny footprint, which matters when you hold thousands of small maps in a cache.

---

## Q035 — HashSet, LinkedHashSet, TreeSet

**The one-line answer:** The three set implementations are thin wrappers over their `Map` counterparts sharing a dummy value, so choosing between them is really choosing between unordered, insertion-ordered, and sorted iteration — and the correctness of all three rests entirely on `equals`/`hashCode` being right.

All three delegate to their `Map` counterparts with a dummy value (`PRESENT`).

| | HashSet | LinkedHashSet | TreeSet |
|---|---|---|---|
| Backed by | HashMap | LinkedHashMap | TreeMap |
| Ordering | None | Insertion order | Sorted |
| `add`/`contains`/`remove` | O(1) avg | O(1) avg | O(log n) |
| Null element | Yes (one) | Yes (one) | No |

Because they are wrappers, every property of the underlying map transfers: `HashSet` inherits `HashMap`'s mutable-key leak (Q033), `LinkedHashSet` inherits the linked-list memory overhead, and `TreeSet` inherits both the comparator-consistency requirement and the `ConcurrentModificationException` behaviour.

### Why equals/hashCode must be correct

`HashSet` uses the same bucket/chain mechanism as `HashMap`. If two logically equal objects return different hash codes, both will be stored — violating the set contract. Always override both `equals` and `hashCode` together. This is exactly the failure demonstrated in Q005: a `HashSet` of objects with `equals` but no `hashCode` silently keeps duplicates.

### TreeSet sorted iteration use case

```java
TreeSet<LocalDate> dates = new TreeSet<>();
dates.add(LocalDate.of(2024, 1, 15));
dates.add(LocalDate.of(2024, 3, 10));
dates.first(); // 2024-01-15
dates.last();  // 2024-03-10
dates.headSet(LocalDate.of(2024, 2, 1)); // dates before Feb 1 — a view, not a copy
```

### Common follow-ups

- **How does a `Set` detect a duplicate?** It computes `hashCode()`, walks that bucket, and uses `equals()` on each colliding entry. Two consequences: a broken `hashCode` means `equals` is never called, and `TreeSet` skips `equals` entirely — it uses `compareTo`/`Comparator`.
- **`HashSet` vs `TreeSet` for "find all expired subscriptions"?** `TreeSet` — it gives you `headSet(cutoff)` in O(log n) and iterates only the expired prefix. A `HashSet` requires a full O(n) scan.
- **What is a `ConcurrentSkipListSet`?** The concurrent sorted set. Use it, not `Collections.synchronizedSet(new TreeSet<>())`.
- **Does `TreeSet` respect `equals`?** No, and this is the classic trap. `BigDecimal("2.0")` and `BigDecimal("2.00")` are `equals`-different but `compareTo`-equal, so a `TreeSet` holds only one of them while a `HashSet` holds both. See Q006.

### Mistakes to avoid

- Storing elements whose `hashCode` changes while they are in the set — the element becomes unreachable and leaks.
- Relying on `HashSet` iteration order in production code, JSON output, or tests. Use `LinkedHashSet` or sort explicitly.
- Assuming `add()` tells you whether the element was already present — it does: `false` means "already there". That is a legitimate deduplication signal people forget exists.

### Production perspective

For API responses, emitting a `HashSet` produces JSON arrays whose order changes between calls, which breaks client-side diffing and caching. Either return a `LinkedHashSet` (insertion order) or map to a sorted list. For "which of these N items exist in the allowed set?" checks, a `HashSet` is the right tool and orders of magnitude cheaper than a `List.contains` scan.

---

## Q036 — Queue, Deque, PriorityQueue

**The one-line answer:** A queue models ordered consumption and gives you two method families — one that throws on an empty or full queue and one that returns `null`/`false` — while `ArrayDeque` is the concrete choice for FIFO/LIFO work and `PriorityQueue` is the choice when ordering comes from a comparator rather than from arrival order.

### Queue contract

| Method | Throws on empty | Returns null/false |
|---|---|---|
| `add(e)` | `IllegalStateException` if full | — |
| `offer(e)` | — | returns false if full |
| `remove()` | `NoSuchElementException` | — |
| `poll()` | — | returns null |
| `element()` | `NoSuchElementException` | — |
| `peek()` | — | returns null |

Prefer `offer/poll/peek` in production — they never throw on empty.

The `add/remove/element` family exists so that a `Queue` can be used as a `Collection` (which mandates throwing behaviour). Using it for a genuinely empty queue is a bug, not a style choice — an empty queue is a normal state, not an exceptional one.

### ArrayDeque

Resizable circular array. Implements both `Queue` and `Deque`. Faster than `LinkedList` for stack and queue operations due to cache locality. No null elements. Not thread-safe.

```java
Deque<Task> work = new ArrayDeque<>();
work.addLast(newTask);      // enqueue (FIFO)
work.addFirst(newTask);     // push (LIFO)
Task next = work.pollFirst();
Task peek = work.peekLast();
```

### PriorityQueue

Min-heap backed by an array. `poll()` always returns the smallest element (natural order) or per Comparator.

```java
PriorityQueue<int[]> pq = new PriorityQueue<>(Comparator.comparingInt(a -> a[1]));
pq.offer(new int[]{1, 5});
pq.offer(new int[]{2, 3});
pq.poll(); // [2, 3] — smallest by second element
```

- `peek` and `poll` are O(log n). `contains` is O(n) — it's not a set.
- Not thread-safe. Use `PriorityBlockingQueue` for concurrent access.

Two things worth stating that candidates routinely miss: the heap is an array sorted only partially, so **iteration order is not sorted order** — you must `poll()` to get elements in order; and the constructor taking only a capacity, `new PriorityQueue<>(100)`, does *not* bound the queue (unlike `ArrayBlockingQueue`), it only pre-sizes the backing array.

### Common follow-ups

- **What is a `Deque` used for besides a stack and a queue?** As a sliding window or a ring buffer for stream processing, and as the workhorse of the sliding-window rate limiter in Q184 — `pollFirst()` to expire old timestamps, `addLast()` to add new ones.
- **How do I implement a blocking queue?** `ArrayBlockingQueue` (bounded, ideal for backpressure) or `LinkedBlockingQueue` (optionally bounded). Both block on `take()` when empty and on `put()` when full, which is the correct behaviour for a producer/consumer worker pool — it naturally applies backpressure instead of dropping work or exhausting memory.
- **Why is `PriorityQueue.contains()` O(n)?** The heap only guarantees that a parent is smaller than its children, so any element could be anywhere in the array. A linear scan is unavoidable.
- **What happens if elements are not mutually comparable?** `ClassCastException` at runtime on the first comparison. Prefer an explicit `Comparator` in the constructor so the failure is deterministic.

### Mistakes to avoid

- Using `add()` on a bounded queue and letting `IllegalStateException` escape, or `peek()` and dereferencing a `null` result.
- Iterating a `PriorityQueue` expecting sorted output.
- Using `LinkedList` where `ArrayDeque` is strictly better (Q032) — the only real reason to pick `LinkedList` today is when you need `List` and `Deque` semantics in the same object.

### Production perspective

In worker-pool and job-queue designs, the bounded `ArrayBlockingQueue` is what stops a burst of traffic from turning into unbounded memory growth. An unbounded queue converts a load spike into an `OutOfMemoryError`; a bounded one converts it into slow producers or a rejected-task policy you can actually reason about (see Q057).

---

## Q037 — Fail-Fast vs Fail-Safe Iteration

**The one-line answer:** Fail-fast iterators detect structural modification via a `modCount` check and throw `ConcurrentModificationException`, while the concurrent collections instead expose weakly-consistent iterators that never throw — and neither mechanism is a substitute for actually making your access thread-safe.

### Fail-fast

`ArrayList`, `HashMap`, `HashSet` and most non-concurrent collections are fail-fast. They maintain a `modCount` counter. When an iterator is created, it copies `modCount`. On each `next()`, it checks if the counter has changed. If it has (because the collection was modified outside the iterator), it throws `ConcurrentModificationException`.

This is a **best-effort** check — not a guarantee of thread safety. It can fail to detect concurrent modifications in multi-threaded code.

Crucially, `ConcurrentModificationException` is most often thrown for **single-threaded** modification: you removed from a list while iterating it with a for-each. It is a bug detector, not a concurrency aid.

### Fail-safe

Concurrent collections (`ConcurrentHashMap`, `CopyOnWriteArrayList`) do not throw `ConcurrentModificationException`. Their iterators operate on a snapshot or use weak consistency:

- `CopyOnWriteArrayList`: iterator holds a snapshot of the array at the time it was created. Modifications to the list after iterator creation are invisible.
- `ConcurrentHashMap`: iterator reflects the state at the time of iteration and may or may not reflect subsequent changes.

### Safe removal during iteration

```java
List<String> list = new ArrayList<>(List.of("a", "b", "c"));
Iterator<String> it = list.iterator();
while (it.hasNext()) {
    if (it.next().equals("b")) {
        it.remove(); // Safe — uses iterator's remove
    }
}
// Or with removeIf (Java 8+):
list.removeIf(s -> s.equals("b"));
```

Never call `list.remove()` inside an iterator-based loop. Use `iterator.remove()` or `removeIf`.

`removeIf` is almost always the right answer: it is a single expression, it uses the iterator's own `remove` internally, and it is implemented as a `default` method on `Collection` so it works uniformly. The one case where you still need an explicit `Iterator` is when the removal condition depends on the index or on state accumulated across iterations.

### Common follow-ups

- **Does "fail-safe" mean thread-safe?** No, and conflating them is a common interview mistake. A `CopyOnWriteArrayList` is thread-safe; its iterator's snapshot guarantee is a *consequence* of the copy-on-write design, not the definition. `ConcurrentHashMap`'s weakly-consistent iterator is a deliberate relaxation of the `Iterator` contract.
- **Can a fail-fast iterator throw when there is no bug?** Yes — if another thread modifies the collection concurrently, an unmodifiable-by-you `ArrayList` can throw. That is the "best-effort" caveat: the check is not synchronised and may or may not observe the other thread's write.
- **What about `removeIf` on a stream?** `Collection.removeIf(Predicate)` is the classic API; `Stream.filter(...)` followed by `collect` to a new list is the idiomatic functional alternative when you do not need in-place mutation.
- **Why doesn't `ConcurrentHashMap` throw?** There is no single `modCount` to check. Its iterators read volatile entries bucket by bucket and tolerate concurrent structural change by design.

### Mistakes to avoid

- Calling `map.remove(key)` inside a `for (var e : map.entrySet())` loop — the textbook `ConcurrentModificationException`.
- "Fixing" that exception with `synchronized` on the list while still iterating with a for-each in the same thread. It is not a concurrency problem; use the iterator's remove.
- Assuming a `CopyOnWriteArrayList` iterator will see writes made after it was created. It will not — that is the point, and it surprises people who mutate then iterate.
- Suppressing `ConcurrentModificationException` with a `try/catch` around the loop. It is a symptom, not an event.

### Production perspective

The CME from mutating a collection during iteration shows up in batch processing and cache-eviction code — typically a background job that tries to remove entries from a list it is iterating. The reliable pattern is to build the list of things to remove first, then call `removeAll` or `removeIf` with it. For anything actually shared across threads, `ConcurrentHashMap`'s weakly-consistent iterator is a genuine benefit: a background cleanup thread can iterate while request threads keep writing.

---

## Q038 — Immutable vs Unmodifiable Collections

**The one-line answer:** `Collections.unmodifiable*` returns a read-only *view* that still reflects changes to the backing collection, while `List.of`/`Set.of`/`Map.of`/`List.copyOf` produce genuinely immutable snapshots — the distinction matters the moment the original reference leaks to a caller.

### Unmodifiable (view)

`Collections.unmodifiableList(list)` returns a **view**. The underlying list is still mutable. If someone holds a reference to the original and modifies it, the "unmodifiable" view reflects the change. Mutation through the wrapper throws `UnsupportedOperationException`.

### Truly immutable (Java 9+)

`List.of(...)`, `Set.of(...)`, `Map.of(...)` create **truly immutable** collections:
- Cannot be modified (no add/remove/set).
- No null elements or keys/values (throws `NullPointerException`).
- Iteration order is unspecified for `Set.of` and `Map.of`.
- Not serializable by default.

`List.copyOf(existing)` creates an immutable copy. If the input is already an immutable `List.of`, it returns the same reference.

```java
List<String> mutable = new ArrayList<>(List.of("a", "b"));
List<String> view = Collections.unmodifiableList(mutable);
List<String> immutable = List.copyOf(mutable);

mutable.add("c");
view.size();      // 3 — reflects mutation
immutable.size(); // 2 — independent copy
```

`List.copyOf` is null-safe in a way `List.of` is not: `List.of(null)` throws immediately, whereas `List.copyOf(collectionContainingNull)` also throws — so both reject nulls, but `copyOf` is the one to use when the input might already be immutable (it avoids the copy) or when you are wrapping something of unknown origin.

### Interview answer pattern

"Unmodifiable is a read-only view that still depends on the original; immutable is a true value object. For returning collections from APIs, I prefer `List.copyOf` or `List.of` to prevent callers from mutating shared state."

### Common follow-ups

- **Which should a repository return from a query?** An immutable snapshot, or a fresh `ArrayList`. Returning a view over a live collection (for example one held in a cache) means a caller's iteration can be invalidated by another thread's write. `List.copyOf` is the cheap, safe default.
- **Is `List.copyOf` deep or shallow?** Shallow — the list is immutable but the elements can still be mutable. That ties directly back to Q011: real immutability needs immutable elements too.
- **Why does `Map.of` cap at 10 key/value pairs?** Because it uses a varargs-based overload for small maps and a different implementation above that. `Map.ofEntries(entry(...), entry(...))` or `Map.copyOf` are the general routes.
- **Can I sort an immutable list?** No. `List.sort` / `list.sort` mutate. Use a stream: `list.stream().sorted().toList()`.

### Mistakes to avoid

- Returning `Collections.unmodifiableList(internalList)` from a service method and assuming the caller cannot see later mutations — they can, through the held reference.
- Storing an immutable collection in a field and still writing setters or `add` methods that touch it; the resulting `UnsupportedOperationException` is far from the actual design error.
- Forgetting that `Set.of` and `Map.of` have **unspecified** iteration order. If you emit them to JSON, the array order will differ between JVM runs and sometimes between calls.
- Relying on serializability of `List.of` across a cache — it is not `Serializable`, which surfaces as a confusing `NotSerializableException` under Java serialization.

### Production perspective

Immutable collection snapshots are the standard way to protect shared caches and configuration objects in Spring services: build once, wrap in `List.copyOf`/`Map.copyOf`, inject, and no request can corrupt it. The cost is one array copy at construction, which is paid once and buys thread safety forever after.

---

## Q039 — Generics Fundamentals

**The one-line answer:** Generics add compile-time type safety without runtime overhead — the type parameter is checked at compile time and erased to `Object` (or the bound) in bytecode.

### Generic class

```java
public class Box<T> {
    private T value;
    public Box(T value) { this.value = value; }
    public T get() { return value; }
}
Box<String> s = new Box<>("hello");
Box<Integer> i = new Box<>(42);
```

### Generic method

```java
public <T extends Comparable<T>> T max(T a, T b) {
    return a.compareTo(b) >= 0 ? a : b;
}
```

The type parameter `<T>` is declared before the return type.

### Multiple bounds

```java
public <T extends Serializable & Comparable<T>> void process(T item) { }
```

A class bound must come first if mixed with interface bounds.

### Why not just use Object?

Without generics, `List list = new ArrayList()` compiles and runs but `ClassCastException` can occur at runtime. Generics shift that error to compile time and eliminate explicit casting.

```java
// Pre-generics: the cast is invisible at the point of insertion
List names = new ArrayList();
names.add("Alice");
names.add(42);              // compiles — the list only knows it holds Object
String first = (String) names.get(1); // ClassCastException, far from the bug

// With generics: the bug is rejected where it is introduced
List<String> names2 = new ArrayList<>();
names2.add("Alice");
names2.add(42);              // compile error
String s = names2.get(0);    // no cast needed
```

### Common follow-ups

- **What is a bounded type parameter?** `<T extends Number & Comparable<T>>` constrains what `T` can be so the method body can call `doubleValue()` and `compareTo()` without casts. A class bound must come first; at most one class bound is allowed because Java has single inheritance of classes.
- **What is a type witness?** `Collections.<String>emptyList()` — you supply the type argument explicitly when inference cannot resolve it, most often when passing `null` into an overloaded generic method.
- **Can a generic type parameter be used in a `static` context?** No. Static members belong to the class, not to a particular instantiation, so a static method or field cannot reference the class's type parameter — it must declare its own, which is exactly what a generic *method* does.
- **What about `?` vs `T` in a method signature?** Use `T` when the parameter type relates to the return type or to another parameter (for example `<T> List<T> emptyList()`). Use a wildcard when it does not (see Q041).

### Mistakes to avoid

- Naming type parameters with single letters in production code that has more than one parameter; `Repository<TEntity, TKey>` documents itself, `Repository<T, N>` does not.
- Declaring `<T extends Object>` — it is legal but adds nothing; `extends Object` is the implicit bound.
- Mixing a type variable and a wildcard in the same bound position incorrectly: `List<? extends T>` is fine, `List<T extends ...>` is not valid — bounds belong in the declaration.

### Production perspective

Generics are what make a Spring Data repository or a shared utility reusable without duplicating code per entity type. The practical lesson from production code review is that generic signatures are documentation: a well-typed signature makes a method's contract self-evident and lets the compiler enforce it across every caller, which is why raw types (Q042) show up in code reviews as a defect rather than a style nit.

---

## Q040 — Type Erasure Implications

**The one-line answer:** The Java compiler erases generic type parameters at bytecode level, replacing them with `Object` or the first bound, and inserts casts at call sites — which means generic type information does not exist at runtime, and that single fact explains most of the language's generic restrictions.

### What gets erased

```java
// Source
List<String> names = new ArrayList<>();
names.add("Alice");
String s = names.get(0);

// Bytecode equivalent
List names = new ArrayList();
names.add("Alice");
String s = (String) names.get(0); // cast inserted by compiler
```

This is why generics cost nothing at runtime, and also why they cannot do things that require runtime type information.

### Consequences

1. **`instanceof` check on generic type is illegal:** `if (list instanceof List<String>)` — won't compile.
2. **Cannot create generic arrays:** `new T[10]` — illegal. Use `new Object[10]` and cast, or `Array.newInstance`.
3. **Cannot use primitives as type parameters:** `List<int>` — illegal. Use `List<Integer>`.
4. **Overloading by generic type alone is illegal:**
   ```java
   void process(List<String> list) {}
   void process(List<Integer> list) {} // compile error — same erasure
   ```
5. **Bridge methods** are generated by the compiler to maintain polymorphism after erasure (visible in bytecode, transparent in source).

### Common follow-ups

- **If the type is erased, why can I `instanceof` a raw `List`?** Because `List` itself still exists at runtime — only its type *argument* is gone. `list instanceof List` is fine; `list instanceof List<String>` cannot be expressed.
- **What is the `ClassCastException` I actually see then?** The cast the compiler inserted. If a raw or heap-polluted reference (Q042) smuggles an `Integer` into a `List<String>`, the failure appears at the *read* site, in code that contains no explicit cast at all.
- **How does `Class<T>` get around erasure?** By carrying the type explicitly: `List<T> make(Class<T> clazz) { return new ArrayList<>(); }`. This is the standard workaround and the reason libraries like Jackson and Guava take `Class<T>` parameters.
- **What is a reifiable type?** One whose type is fully available at runtime: primitives, raw types, unbounded wildcards (`List<?>`), and non-generic classes. Only reifiable types may be used with `instanceof`. `List<?>` is reifiable, `List<String>` is not.
- **How does the compiler handle covariant returns then?** With a synthetic bridge method that overrides the erased signature and delegates — the mechanism described in Q004.

### Mistakes to avoid

- Trying to store a type in a field to recover it later: `private Class<T> type` is lost unless you explicitly declare and populate it, which is exactly the boilerplate people are surprised by.
- Writing an overloaded method that differs only by generic type argument and then debugging the compile error, which names "the same erasure".
- Assuming `new T[...]` works because it "looks like an array creation". Use `Array.newInstance(clazz, length)` and cast to `T[]`.

### Production perspective

Erasure is why runtime reflection over collections in JSON mappers and ORMs works the way it does: a `List<Order>` on a field is really a `List` at runtime, and the element type has to be recovered from the field's generic signature or from an explicit type reference. It also explains a recurring production anti-pattern — a method that accepts `List<X>` and then branches on the element class, which cannot be done safely and usually signals a missing interface or visitor (see Q016/Q017 for the sealed-type alternative).

---

## Q041 — Wildcards and PECS

**The one-line answer:** Use `? extends T` for a collection you only read from and `? super T` for one you only write to — the **P**roducer **E**xtends, **C**onsumer **S**uper mnemonic — because erasure means the compiler cannot prove that an arbitrary `List<Subtype>` is a `List<Supertype>` unless you tell it which direction the variance runs.

```java
// This intuitive intuition is WRONG — it will not compile
List<Number> nums = new ArrayList<Integer>(); // incompatible types

// The wildcard is the only way to express "some list of a subtype of Number"
List<? extends Number> nums = new ArrayList<Integer>(); // OK
```

### `? extends T` — covariant (upper-bounded)

Use when you **read** from the collection (it produces items for you).

```java
double sum(List<? extends Number> list) {
    double total = 0;
    for (Number n : list) total += n.doubleValue(); // safe — every element is a Number
    return total;
}
```

You cannot `add` to a `List<? extends Number>` (except `null`) because the compiler cannot verify the exact type.

This asymmetry is the whole point: `List<Integer>` is assignable to `List<? extends Number>`, so the parameter can safely *read* `Number`s out — but the actual runtime list could be `List<Double>` or `List<Byte>`, so any `add` would be unsound.

### `? super T` — contravariant (lower-bounded)

Use when you **write** to the collection (it consumes items you supply).

```java
void addNumbers(List<? super Integer> list) {
    list.add(1);
    list.add(2); // safe — Integer fits in any supertype
}
```

You cannot safely `get` from a `List<? super Integer>` as anything more specific than `Object`.

The fully general form, and the one worth stating: for a type parameter `T`, the compiler will accept `List<? super T>` on a write and `List<? extends T>` on a read, and `List<T>` satisfies both.

### Classic example — `Collections.copy`

```java
public static <T> void copy(List<? super T> dest, List<? extends T> src) {
    // src is a producer (read from it), dest is a consumer (write to it)
}
```

The same shape appears throughout `java.util` — `sort(List<T>)` uses `Comparable<? super T>`, `Collection.max(Collection<? extends T>)` extends.

### Unbounded wildcard `<?>`

Use when you only care that something is a `List` and don't read typed elements:

```java
void printSize(List<?> list) { System.out.println(list.size()); }
```

`List<?>` and `List<Object>` are not the same. `List<Object>` accepts any list *parameter*; `List<?>` means "a list of some unknown type", so you can pass a `List<String>` to it but cannot `add` anything except `null`. Use `<?>` when the logic is genuinely type-agnostic.

### Common follow-ups

- **What is the "Get and Put Principle"?** The precise form of PECS: use `extends` when you only *get* values out, `super` when you only *put* values in, and neither when you do both.
- **Why can't I use PECS everywhere?** Because you cannot always choose — a parameter that is both read and written (`List<T>`) cannot be a wildcard, and a type variable appearing in two places in a signature (`<T> void move(List<? extends T> from, List<? super T> to)`) forces the wildcards to be related, not independent.
- **How do I negate a wildcard?** You cannot. There is no "? not extends T". That absence is the reason sealed types and pattern matching (Q016/Q017) were added — they give the compiler a closed set to reason about.

### Mistakes to avoid

- Using `List<? extends T>` on a parameter you then try to `add` to, and "fixing" the compile error by switching to `List<T>` and losing the variance flexibility you wanted.
- Defaulting to raw `List` when a wildcard was meant. Raw types switch off all checking, not just the variance.
- Reaching for `? super` on a return type. Wildcards belong on parameters; returning `List<? extends T>` is nearly always a sign the return type should be `List<T>`.

### Production perspective

PECS shows up wherever a backend service passes collections into generic helpers: validation pipelines, merge/aggregate utilities, and anything that accepts user-supplied overrides. The practical signal is: if a method accepts a collection it only reads, type it `? extends` and callers can pass a `List` of any subtype; if you typed it `List<T>` you will find callers needlessly copying or downcasting.

---

## Q042 — Raw Types and Heap Pollution

**The one-line answer:** A raw type opts out of generic checking entirely, and that hole is wide enough to smuggle a wrong-typed element into a parameterized collection — "heap pollution" — which then detonates as a `ClassCastException` at a read site that contains no cast at all.

### Raw types

Using a generic class without type parameters: `List list = new ArrayList()`. The compiler issues an **unchecked warning**. All type safety is lost — you can add any object and get `ClassCastException` at a distant call site.

Never use raw types in new code. They exist only for backward compatibility with pre-Java 5 APIs.

The only case where a raw type is unavoidable in modern code is a class literal: `List.class` is legal because of erasure, so `list.getClass()` and `List<Order>.class` do not typecheck. You must write `List.class`, or better, avoid needing it.

### Heap pollution

Heap pollution occurs when a variable of a parameterized type holds a reference to an object of a different parameterized type. It can cause `ClassCastException` on reads even though no explicit cast is written.

```java
List<String> strings = new ArrayList<>();
List raw = strings;         // raw type assignment — unchecked warning
raw.add(42);                // Integer added to raw list — compiles, no warning here
String s = strings.get(0);  // ClassCastException at runtime
```

Note *where* the exception surfaces: on the read, in code that looks completely correct. That distance between cause and effect is what makes heap pollution so expensive to debug.

### Generic varargs and heap pollution

```java
@SafeVarargs
public final <T> List<T> listOf(T... elements) { ... }
```

`@SafeVarargs` suppresses the unchecked warning when you can guarantee no heap pollution occurs inside the method (no writing to the varargs array with a different type).

Varargs of a generic type are implemented as an array, which is subject to array covariance and to erasure — so it *can* be polluted, and the compiler cannot otherwise prove otherwise. `@SafeVarargs` is a promise from you, not a check by the compiler, and it is only permitted on `static`, `final`, or (since Java 9) `private` methods — the cases where a subclass cannot override and re-expose the array.

### Common follow-ups

- **What is the difference between an unchecked warning and a raw type?** A raw type *is* the unchecked usage. The compiler warns at the point of the raw assignment or call, which is why you should never ignore `-Xlint:unchecked` warnings in a build.
- **Can heap pollution happen with a generic *class* rather than a method?** Yes, any time a raw reference is stored and later used through a parameterized one — a cached `Map` field read back as `Map<String, Order>` is a classic instance in real code.
- **How do I avoid the varargs warning safely?** Make the parameter `List<? extends T>` instead of `T...`, or use `@SafeVarargs` only after confirming you never write into the array. `List.of` and `Arrays.asList` are `@SafeVarargs` for exactly this reason.
- **What does `-Xlint:unchecked -Werror` do for me?** Turns these warnings into build failures. That is the single most effective guard against heap pollution entering a codebase.

### Mistakes to avoid

- Adding `@SuppressWarnings("unchecked")` to make a warning disappear instead of fixing the underlying raw usage. This is the most common way heap pollution gets committed.
- Casting through a raw type "just to convert": `(List<String>) (List<?>) rawListOfIntegers` compiles with a warning and fails later at the read.
- Annotating a non-final, non-static, non-private method with `@SafeVarargs` — the compiler rejects it, for good reason.

### Production perspective

Almost every `ClassCastException` at a line with no cast traces back to heap pollution or to a raw type crossing a layer boundary — typically a legacy utility, a deserializer, or a shared cache field. The fix is always the same: reintroduce the type parameter, and let the compiler point at every place that was silently wrong. Treat unchecked warnings as build-breaking, not cosmetic.

---

## Q043 — Stream Fundamentals

**The one-line answer:** Streams are lazy, single-use pipelines over a data source that separate the description of computation (intermediate operations) from execution (terminal operations).

### Key properties

- **Lazy:** Intermediate operations (`filter`, `map`, `sorted`) are not executed until a terminal operation is called.
- **Single-use:** A stream cannot be reused after a terminal operation. Create a new stream from the source.
- **Non-destructive:** Streams do not modify the underlying data source.
- **Possibly infinite:** `Stream.iterate`, `Stream.generate` produce unbounded streams; rely on short-circuit terminals (`findFirst`, `limit`).

### Pipeline structure

```
Source → [intermediate ops...] → terminal op
```

```java
List<String> result = names.stream()           // source
    .filter(n -> n.startsWith("A"))             // intermediate (lazy)
    .map(String::toUpperCase)                   // intermediate (lazy)
    .sorted()                                   // intermediate (lazy, stateful)
    .collect(Collectors.toList());              // terminal (triggers execution)
```

### Short-circuit operations

`findFirst`, `findAny`, `anyMatch`, `allMatch`, `noneMatch`, `limit` can stop the pipeline early without processing all elements.

### Primitive streams

`IntStream`, `LongStream`, `DoubleStream` avoid boxing overhead. Use `mapToInt`, `mapToLong`, `mapToDouble` to transition. They have specialized terminals: `sum()`, `average()`, `min()`, `max()`, `summaryStatistics()`.

```java
// Boxed: every element is an Integer object, and sum() unboxes each one
Integer total = orders.stream().mapToInt(Order::getQuantity).boxed().reduce(0, Integer::sum);

// Primitive: no boxing anywhere in the pipeline
int total2 = orders.stream().mapToInt(Order::getQuantity).sum();
```

### Common follow-ups

- **Why is a stream single-use?** Because it is a *pipeline*, not a data structure. The source is re-traversable (`list.stream()` gives you a fresh stream every time), but the pipeline object itself holds state about where the traversal is. Reusing it throws `IllegalStateException`.
- **Is a stream lazy end-to-end?** Yes, and this is the answer that impresses. In `list.stream().filter(a).filter(b).findFirst()`, `findFirst()` pulls one element through the whole chain of filters before pulling a second — a "vertical" execution, not the two passes people assume.
- **What about infinite streams?** `Stream.iterate(0, i -> i + 1)` is lazy and unbounded; it is safe only with a short-circuiting terminal such as `limit(n).findFirst()`. Since Java 9 the three-arg `iterate(seed, hasNext, next)` is preferred because the predicate is visible in the call.
- **What is a "flattening" stream and why does order matter?** `flatMap` elements arrive in encounter order of the outer stream, then inner order within each — which is why `flatMap` followed by `sorted()` is deterministic but `flatMap` followed by nothing is not parallel-safe in its output order.

### Mistakes to avoid

- Building the same stream twice (a second `list.stream()` call) when you intended to reuse it — that is the fix, not a workaround.
- Using `forEach` on an infinite stream without `limit` — it will run forever and never return.
- Leaving a stream from `Files.lines`/`Stream.iterate` open. Streams holding resources (files, sockets) must be closed with try-with-resources; otherwise you leak file descriptors (see Q010).
- Assuming a stream is thread-safe because it is immutable-looking. It is neither shareable across threads nor safe to mutate during traversal.

### Production perspective

The laziness is what makes streams suitable for large datasets and I/O: a `Files.lines(...).filter(...).limit(100)` reads at most as many lines as it needs, which is the difference between constant memory and loading a 2 GB log into a heap. The single-use property is what makes streams safe to hand to framework code without wondering whether another thread is mid-traversal.

---

## Q044 — map, flatMap, filter, reduce

**The one-line answer:** `map` transforms one element into one, `flatMap` transforms one element into zero-or-more by flattening the resulting stream, `filter` drops elements that fail a predicate, and `reduce` collapses the stream to a single value with an identity and a combiner — together they are the four shapes every stream pipeline is built from.

### `map`

Applies a function to each element, producing a new stream of the same size.

```java
List<String> upper = names.stream()
    .map(String::toUpperCase)
    .collect(toList());
```

One element in, exactly one element out. If the mapper can produce "nothing", you need `flatMap` plus `Stream.empty()` or `Optional.stream()` (see Q013) — `map` cannot drop elements.

### `flatMap`

Maps each element to a stream, then flattens all resulting streams into one. Use when each element produces zero or more elements.

```java
List<List<String>> nested = List.of(List.of("a","b"), List.of("c"));
List<String> flat = nested.stream()
    .flatMap(Collection::stream)
    .collect(toList()); // ["a", "b", "c"]
```

The mental model to say out loud: `map` on `Stream<List<T>>` gives `Stream<Stream<T>>` (nested and useless); `flatMap` gives `Stream<T>`. Every use of `flatMap` in practice is either flattening a collection field or joining a stream of `Optional`/`CompletableFuture`-like wrappers.

```java
// The Optional version — this is why Optional.stream() was added in Java 9
List<Coupon> coupons = orders.stream()
    .map(this::findCoupon)
    .flatMap(Optional::stream)
    .toList();
```

### `filter`

Keeps elements that match a predicate.

```java
long count = orders.stream()
    .filter(o -> o.getTotal() > 100)
    .count();
```

`filter` is not the same as `if` — it is a description of which elements survive, and it can be reordered by the stream implementation for efficiency. Do not put side effects in it.

### `reduce`

Combines elements to a single result using a `BinaryOperator`.

```java
// With identity (safe — always returns a value)
int sum = IntStream.rangeClosed(1, 100).reduce(0, Integer::sum);

// Without identity — returns Optional (stream could be empty)
Optional<Integer> max = Stream.of(3, 1, 4, 1, 5).reduce(Integer::max);
```

**Interview tip on reduce identity:** The identity value must be a true identity for the operation — `0` for sum, `1` for product, `""` for string concatenation. Using a wrong identity (e.g., `reduce(1, Integer::sum)` on a list) gives wrong results silently.

This is not a theoretical warning: `stream().reduce(0, Integer::sum)` on an empty stream returns `0`, but `Collectors.summingInt` would also return `0`. The real hazard is a non-commutative operation with an arbitrary identity — for example `reduce(firstElement, this::merge)` on a collection of date ranges.

The three-argument `reduce(identity, accumulator, combiner)` exists because parallel streams need a way to combine partial results. The combiner must be compatible with the identity (`combiner.apply(identity, a) == a`), which is what makes it associative.

### Common follow-ups

- **`map` vs `mapToObj` vs `flatMapToObj`?** `map` on a primitive stream returns a primitive stream; `mapToObj` boxes into a reference stream; `flatMapToObj` flattens primitive results into a reference stream. Mixing them up produces `IntStream` where you wanted `Stream<Integer>` and vice versa.
- **Why does `reduce` return `Optional` only in the no-identity form?** Because an empty stream has no elements to fold, so there is no answer. With an identity there is always at least the identity, so `Optional` would be pure noise.
- **Is `reduce` associative-safe?** Only if your accumulator is. `Integer::sum` and `String::concat` are; "take the first non-null" is not, because order matters. If you use a non-associative accumulator, parallel streams will produce different results for different inputs.
- **When is `reduce` the wrong tool?** When you want a `Map`, a grouped result, or a joined string — use `collect` with a `Collector` (Q045). `reduce` into a mutable container is strictly worse.

### Mistakes to avoid

- Reusing a stream variable across two terminal operations (Q046) — a very common live-coding slip.
- Calling `reduce` and then unwrapping with `get()` instead of `orElse`/`orElseGet`, which turns a legitimate "empty" case into a `NoSuchElementException`.
- Using `reduce` with a mutable accumulator, for example `reduce(new ArrayList<>(), (acc, x) -> { acc.add(x); return acc; })`. This is both quadratic and, under parallel streams, incorrect. Use `collect`.
- Assuming `filter` order is irrelevant when the predicates have side effects or different costs. Put the cheapest, most selective predicate first in a sequential pipeline.

### Production perspective

Stream pipelines are the dominant style for in-memory aggregation in service code: response assembly, report summarisation, validation aggregation. The two operational lessons are: (1) prefer `collect` with a built-in `Collector` over hand-rolled `reduce` because the built-ins are parallel-safe and well-tested; and (2) prefer the primitive-stream overloads for any numeric aggregation, because boxing a million-element stream for a `sum()` is a measurable GC cost.

---

## Q045 — Collectors in Practice

**The one-line answer:** A `Collector` is a mutable-reduction recipe — supplier, accumulator, combiner, finisher — and `Collectors` supplies the ones you need for 95% of backend aggregation: `toList`/`toUnmodifiableList`, `groupingBy`, `partitioningBy`, `toMap`, and `joining`; knowing which of those returns a mutable result and which throws on duplicates is the part people get wrong.

### `toList()` / `toUnmodifiableList()`

```java
List<String> names = stream.collect(Collectors.toList());       // mutable
List<String> safe  = stream.collect(Collectors.toUnmodifiableList()); // immutable
// Java 16+: stream.toList() — unmodifiable, null-rejecting
```

The difference matters more than it looks. `collect(toList())` guarantees mutability but says nothing about nulls or thread-safety; `toUnmodifiableList()` permits nulls but rejects mutation; `stream.toList()` rejects nulls *and* mutation. For a public API response, `toList()` or `toUnmodifiableList()` is the safer choice specifically because a null slipping into an unmodifiable list is an `UnsupportedOperationException` deep inside a serializer.

### `groupingBy`

```java
Map<Department, List<Employee>> byDept = employees.stream()
    .collect(Collectors.groupingBy(Employee::getDepartment));

// With downstream collector
Map<Department, Long> countByDept = employees.stream()
    .collect(Collectors.groupingBy(Employee::getDepartment, Collectors.counting()));
```

`groupingBy` is the most composable of them all: the downstream collector can be anything, including another `groupingBy`. Two further variants worth knowing: the three-arg `groupingBy(classifier, mapFactory, downstream)` lets you pick the map implementation (`EnumMap`, `TreeMap`, `LinkedHashMap`), and the classifier's result type must be usable as a map key — so it cannot be null.

### `partitioningBy`

Returns a `Map<Boolean, List<T>>`:

```java
Map<Boolean, List<Integer>> partition = numbers.stream()
    .collect(Collectors.partitioningBy(n -> n % 2 == 0));
// true → evens, false → odds
```

`partitioningBy` is `groupingBy` specialised for a boolean predicate, and it is more efficient because both keys are always present — `partition.get(false)` returns an empty list rather than `null`, which removes a null check you would otherwise need with `groupingBy`.

### `toMap`

```java
Map<Long, String> idToName = employees.stream()
    .collect(Collectors.toMap(Employee::getId, Employee::getName));
```

**Important:** throws `IllegalStateException` on duplicate keys. Provide a merge function:

```java
Collectors.toMap(Employee::getDept, Employee::getName, (a, b) -> a + ", " + b)
```

There is a fourth, often-overlooked argument — the map factory. `toMap(keyFn, valFn, mergeFn, LinkedHashMap::new)` preserves insertion order, and `toMap(keyFn, valFn, mergeFn, () -> new EnumMap<>(Status.class))` avoids hash cost entirely for enum keys. If you do not supply a merge function and your data can contain duplicates, the collector will throw at runtime on the second duplicate — always supply one unless duplicates are genuinely a bug you want to surface loudly.

### `joining`

```java
String csv = names.stream().collect(Collectors.joining(", ", "[", "]"));
```

`joining` handles the prefix/suffix and the separator, and (unlike manual concatenation in a loop) uses a `StringBuilder` internally. There is also `Collectors.joining()` for plain concatenation.

### Common follow-ups

- **Why does `toMap` throw on duplicate keys but `groupingBy` does not?** `groupingBy` accumulates into a `List` downstream, so duplicates have somewhere to go. `toMap` has no defined collision policy unless you give it a merge function — the designers chose to fail loudly rather than silently drop a value.
- **`Collectors.toUnmodifiableList()` vs `Stream.toList()`?** The collector works on any stream in a `collect` chain and allows nulls; `toList()` is a direct terminal that rejects nulls. Both return immutable lists.
- **How do I get a `Map<K, Set<V>>`?** `Collectors.groupingBy(classifier, Collectors.toSet())`. Substitute `toUnmodifiableSet` or `toCollection(TreeSet::new)` depending on what the downstream needs.
- **What is a downstream collector, exactly?** The second argument to `groupingBy`/`partitioningBy`, which reduces each *group* rather than the whole stream. That composability is what makes `Collectors` a mini-language for aggregation.
- **How do I pick the map type?** Pass a `mapFactory` as the third argument. The default is `HashMap`, which is right unless you need enum keys, sorted keys, or deterministic iteration order.

### Mistakes to avoid

- Calling `groupingBy` and then getting `null` from `result.get(key)` for a key with no entries. Use `getOrDefault(key, List.of())`, or use `partitioningBy`, which never has missing keys.
- Using `toMap` with a value function that can return `null` — a null value makes the entry vanish, and `HashMap` allows one null key but here the *key* may be null, which throws.
- Assuming `Collectors.toList()` returns an immutable list. It does not — it returns an `ArrayList` you can still mutate. Use `toUnmodifiableList` or `stream.toList()` for that.
- Building a map with a loop and `map.put` when `groupingBy`/`toMap` would express it in one line and be parallel-safe.

### Production perspective

`Collectors` are the standard tool for response assembly and report summarisation in service code, and they are the answer that separates "I have used streams" from "I understand the API" in a live-coding round. The two production-level details are: always pass a merge function to `toMap` unless duplicate keys represent a real bug, and reach for the `mapFactory` overload when the map is an `EnumMap` or needs deterministic ordering, because both are free wins.

---

## Q046 — Stream Pitfalls

**The one-line answer:** Most stream bugs come from breaking the functional contract — side effects in a lambda, stateful intermediate operations in a supposedly lazy pipeline, reusing a consumed stream, or mutating the source mid-traversal — and every one of them is invisible in a single-threaded test and becomes a correctness bug under parallel streams or at scale.

### Side effects in lambdas

Mutating external state from a lambda is unsafe, especially with parallel streams:

```java
// BAD
List<String> result = new ArrayList<>();
stream.filter(...).forEach(result::add); // race condition in parallel

// GOOD
List<String> result = stream.filter(...).collect(toList());
```

This is not a style preference. `forEach` with a side effect makes the operation order-dependent and non-thread-safe; `collect` hands the mutable container to the collector, which is designed to combine partial results. The lambda itself should be a pure function of its input.

### Stateful intermediate operations

`sorted()`, `distinct()`, `limit()`, `skip()` are stateful — they must see all (or many) elements before passing anything downstream. Using `sorted()` in a pipeline that could be short-circuited by `findFirst` still forces full evaluation.

Stateful operations also have a defined interaction with laziness that surprises people: `limit` on an infinite source is safe (`Stream.iterate(...).limit(10)` works), but `sorted` on an infinite source never completes, because `sorted` must buffer the whole stream to know the first element.

### Stream reuse

```java
Stream<String> s = list.stream().filter(...);
s.count();       // OK
s.findFirst();   // IllegalStateException: stream has already been operated upon
```

The stream is consumed, not the data. `list` is re-traversable; `s` is not. The fix is a fresh `list.stream()`, and the signal that you should have extracted the pipeline into a method.

### Modifying source during stream pipeline

```java
List<String> list = new ArrayList<>(List.of("a", "b", "c"));
list.stream().forEach(list::remove); // ConcurrentModificationException
```

This is the stream equivalent of the in-chapter removal bug from Q037: the stream is internally iterating the same list you are mutating.

### Checked exceptions in lambdas

Lambdas cannot throw checked exceptions without wrapping:

```java
// BAD — won't compile
stream.map(path -> Files.readString(path));

// GOOD — wrap with a utility
stream.map(path -> { try { return Files.readString(path); } 
                     catch (IOException e) { throw new UncheckedIOException(e); } });
```

A cleaner production alternative is a small helper that declares a functional interface with the checked exception, which lets the checked exception propagate to the terminal operation where you actually handle it:

```java
@FunctionalInterface
public interface ThrowingFunction<T, R, E extends Exception> {
    R apply(T t) throws E;
    static <T, R> Function<T, R> unchecked(ThrowingFunction<T, R, ?> fn) {
        return t -> { try { return fn.apply(t); } catch (Exception e) { throw new RuntimeException(e); } };
    }
}
stream.map(unchecked(Files::readString));
```

Wrapping in `UncheckedIOException` rather than plain `RuntimeException` matters: it preserves the exception type so a caller can distinguish an I/O failure from a programming bug.

### Common follow-ups

- **Why does `forEach` accept a `Consumer` while `map` needs a `Function`?** Because they are different operations: `forEach` is terminal and returns nothing, `map` is intermediate and must return a value. This is also why `forEach` on a stream does not short-circuit, while `map` can be skipped entirely if a later stage never requests an element.
- **Is `Stream.forEach` the same as `Iterable.forEach`?** No, and this is a classic trap. `Iterable.forEach` is a plain loop over the collection; `Stream.forEach` may run in any order and in parallel. `stream.peek` is for debugging, not for production side effects.
- **What is the safest way to debug a stream pipeline?** Insert `peek(System.out::println)` temporarily, or better, break the chain into statements with typed locals so you can inspect each stage. Peek should never ship in production code.
- **Why can a lambda not throw a checked exception at all?** Because functional interfaces (`Function`, `Predicate`, `Consumer`) do not declare `throws`. Checked exceptions are part of a method's signature and the lambda must conform to the target type's contract — hence the wrapping or the custom interface.

### Mistakes to avoid

- `peek()` performing real work. It is documented as "mainly for debugging" and may be skipped entirely by the implementation.
- Assuming `stream.parallel()` after a `forEach` side effect speeds things up — it introduces a race without any useful parallelism.
- Using `forEach` where `reduce` or `collect` was intended, then wondering why the result is missing elements.
- Suppressing the checked-exception wrapper into a swallowed `catch {}` block. Wrap and rethrow.

### Production perspective

The `ConcurrentModificationException` from mutating a source during a stream, and lost results from side-effectful `forEach` under `parallelStream`, both typically appear in data-processing jobs that were only ever tested on small sequential inputs. The two rules that prevent them: lambdas must be pure functions of their parameters, and any aggregation must go through `collect` rather than a mutated external collection.

---

## Q047 — Parallel Streams

**The one-line answer:** Parallel streams split work across the **common ForkJoinPool** and are beneficial only for CPU-bound, data-parallel, stateless operations on large datasets. They are harmful for IO-bound work, ordered operations, or small collections.

### When parallel streams help

- Large collections (10k+ elements) where per-element work is CPU-intensive.
- Stateless, side-effect-free lambdas.
- Result doesn't require encounter order.

```java
long count = largeList.parallelStream()
    .filter(this::expensiveCheck)
    .count();
```

### When parallel streams hurt

- **IO-bound operations:** Threads block waiting for IO, starving the common pool and hurting other parallel streams in the JVM.
- **Small collections:** Fork/join overhead exceeds benefit.
- **Ordered operations:** `findFirst()` on a parallel stream must still honor encounter order, causing synchronization overhead. Use `findAny()` if order doesn't matter.
- **Stateful lambdas:** Shared mutable state leads to data races.

### Thread pool isolation

The common pool size = `Runtime.getRuntime().availableProcessors() - 1`. For IO tasks, use a custom pool:

```java
ForkJoinPool customPool = new ForkJoinPool(20);
customPool.submit(() -> list.parallelStream().map(this::callExternalService).collect(toList())).get();
```

That last point deserves emphasis: **the same JVM-wide pool backs `parallelStream`, `CompletableFuture.supplyAsync`, and any `Stream.iterate` with an implicit executor.** One blocking call inside a parallel stream therefore slows down unrelated work across the whole application, including other libraries you do not control. This is the single strongest argument against parallel streams in a backend service.

### Common follow-ups

- **When is a parallel stream a net win?** Large, CPU-bound, embarrassingly parallel work on an embarrassingly parallel data structure — image processing, checksum computation, in-memory numerical aggregation on 10k+ elements. Measure, do not assume: on collections under ~1,000 elements the fork/join overhead usually dominates.
- **Why is `findFirst` slower than `findAny` here?** `findFirst` must preserve encounter order, so the parallel implementation has to gather candidates and pick the earliest. `findAny` accepts whichever completes first and needs no ordering machinery — a real win when you do not care which element you get.
- **Why does the common pool use `availableProcessors - 1`?** To leave one core for the calling thread and for the JVM's own work. You can override it with `-Djava.util.concurrent.ForkJoinPool.common.parallelism=N`, but that affects the whole JVM.
- **What about `ArrayList` vs `LinkedList` as a parallel source?** `ArrayList` splits cheaply by index range; `LinkedList` must be traversed to split, so it parallelises badly. This is another reason `ArrayList` is the default.

### Mistakes to avoid

- Wrapping blocking I/O in a parallel stream because it "looks concurrent". Use virtual threads (Q066) or a dedicated executor for I/O.
- Sharing mutable state between the lambda and the outside world. `AtomicInteger` in a parallel stream is a symptom of a design error — use `collect` with a proper collector.
- Assuming `.parallel()` makes it parallel "and therefore faster" without measuring on production-sized data.
- Changing pool size to "fix" sequential slowness. The bottleneck was not parallelism.

### Production perspective

Parallel streams in a Spring Boot service are rarely the right tool: the common pool is shared, the work is usually I/O-bound rather than CPU-bound, and the code becomes order-sensitive in ways that break under load. The same reasoning applies to `CompletableFuture.supplyAsync` with no executor — it lands on the common pool too. When you genuinely need parallelism, bring your own `Executor` so you control isolation and observability.

---

## Q048 — Streams vs Loops

**The one-line answer:** Neither is universally better — streams express *what* result you want and let the implementation decide *how*, which is why they win on clarity and parallelisability, while loops win when you need early exit, mutable per-iteration state, or a checked exception; the correct answer to "which should I use" is "whichever makes the code read as intent".

```java
// Stream — clear intent
int totalActive = users.stream()
    .filter(User::isActive)
    .mapToInt(User::getScore)
    .sum();

// Loop — easier to add debug logging or complex branching
int totalActive = 0;
for (User u : users) {
    if (u.isActive()) totalActive += u.getScore();
}
```

### Prefer streams when

- Expressing a data transformation pipeline (filter → map → collect).
- The logic is simple and maps directly to built-in operations.
- You want lazy evaluation or parallel execution.

### Prefer loops when

- You need `break`/`continue`/early exit within complex logic.
- You must throw checked exceptions.
- You're debugging and need to set breakpoints on individual iterations.
- Performance profiling shows stream overhead is relevant (rare).
- Mutating multiple variables simultaneously during iteration.

### Performance reality

For simple operations on small to medium collections, the performance difference is negligible. The compiler and JIT often produce equivalent bytecode. Optimize for **readability first**, then profile.

It is worth knowing the actual trade-offs rather than repeating "streams are slower": a stream pipeline allocates a pipeline object and a lambda per operation, which costs nanoseconds and some garbage; a hand-written loop is a single method with no allocation. For a 10-element collection the stream overhead is unmeasurable. For a 100-million-element hot loop in a numerical kernel it can be a real percentage — and that is the case where a loop is the right answer.

### Common follow-ups

- **What can a loop do that a stream genuinely cannot?** `break` out early with complex conditions, mutate several locals simultaneously, throw checked exceptions without a wrapper, or short-circuit on a non-local condition (see `Q047`'s `limit`). None of these are language limitations, but each is either awkward or impossible to express idiomatically.
- **Can I use a stream for a state machine that needs to look ahead?** Yes, with an explicit buffer or `reduce`, but the result is usually harder to read than a loop. Prefer the loop when the logic is inherently stateful.
- **Is `forEach` on a stream a good middle ground?** Only if the action is genuinely terminal and order-insensitive. As soon as you want to inspect the result, `collect` first.
- **What does a senior engineer's code review say here?** Usually "this stream is doing too much" — a chain of eight operations with nested ternaries is worse than the equivalent loop. The goal is readable code, not maximal functional purity.

### Mistakes to avoid

- Reaching for a stream to avoid a simple loop, then writing a five-operation pipeline with `map` to `if/else` replacement that reads worse.
- Using a for-each (which throws `ConcurrentModificationException`) where an indexed loop or `removeIf` is required — Q037.
- Premature optimisation: converting a working, readable loop into a stream on the theory that streams are faster, and measuring nothing.
- Ignoring the checked-exception problem and wrapping every checked exception into a rethrow, which hides the real error path.

### Production perspective

In backend code the stream/loop choice is nearly always a readability decision, not a performance one — the measurable wins come from pre-sizing collections (Q031), using primitive streams (Q043), and keeping lambdas side-effect-free so the code is parallelisable when profiling says you need it. The one place it becomes operational is hot loops in serialization, parsing, and arithmetic kernels, which is exactly where you should profile before optimising.

---

## Q049 — Common Stream Coding Patterns

**The one-line answer:** Master canonical Stream pipelines for grouping, frequency counting, finding top-N elements, and multi-field sorting using `Collectors` and `Comparator` chaining without mutating external state.

### Frequency count

```java
Map<String, Long> freq = words.stream()
    .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));
```

### Top N by value

```java
List<String> top3 = words.stream()
    .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()))
    .entrySet().stream()
    .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
    .limit(3)
    .map(Map.Entry::getKey)
    .toList();
```

### Remove duplicates preserving order

```java
List<String> unique = list.stream().distinct().toList();
```

### Group and get max per group

```java
Map<String, Optional<Employee>> topEarner = employees.stream()
    .collect(Collectors.groupingBy(Employee::getDept,
             Collectors.maxBy(Comparator.comparingInt(Employee::getSalary))));
```

### Multi-field sort with null safety

```java
employees.sort(Comparator.comparing(Employee::getDept, Comparator.nullsLast(Comparator.naturalOrder()))
               .thenComparing(Employee::getSalary, Comparator.reverseOrder()));
```

### Flat-map with null safety

```java
List<String> tags = orders.stream()
    .flatMap(o -> o.getTags() == null ? Stream.empty() : o.getTags().stream())
    .distinct()
    .toList();
```

### Partitioning into two groups (Boolean predicate)

```java
Map<Boolean, List<Order>> partitioned = orders.stream()
    .collect(Collectors.partitioningBy(Order::isPriority));
```

### Common follow-ups

- **How do you find the second highest element?**
  `list.stream().distinct().sorted(Comparator.reverseOrder()).skip(1).findFirst()`
- **Can you group by multiple fields?**
  Yes, either by nesting `groupingBy`: `Collectors.groupingBy(Order::getCountry, Collectors.groupingBy(Order::getStatus))` or by grouping on a composite record key: `record GroupKey(String country, OrderStatus status) {}`.

### Mistakes to avoid

- Modifying an external collection inside `.forEach()` instead of using `.collect()`.
- Forgetting that `.distinct()` requires well-implemented `equals()` and `hashCode()` on element types.
- Calling `.parallelStream()` on small collections or operations with I/O blocking.

### Production perspective

Stream pipelines are frequently tested in live coding rounds. Clear, idiomatic pipelines with proper null checks and comparator tie-breakers reflect clean, senior-level code craftsmanship.

---

## Q050 — Functional Composition and Default Methods

**The one-line answer:** Functional interfaces ship composable `default` methods — `andThen`, `compose`, `and`, `or`, `negate` — so whole rule sets (validators, discount strategies, filters) can be assembled from small, independently testable pieces instead of nested `if`-blocks; the cost is that you have taken on multiple inheritance of behaviour, and the compiler resolves conflicts by force rather than by precedence.

```java
Function<String, String> trim   = String::trim;
Function<String, String> upper  = String::toUpperCase;
Function<String, Integer> length = String::length;

// andThen: apply trim, then apply upper to its result
Function<String, String> trimThenUpper = trim.andThen(upper);

// compose: apply upper first, then trim (reverse order)
Function<String, String> upperThenTrim = trim.compose(upper);
```

Note the reading order, which is the thing people get backwards in an interview: `f.andThen(g)` applies `f` **first**; `f.compose(g)` applies `g` **first**. `andThen` reads left-to-right, `compose` reads right-to-left.

```java
// Same result, two readings:
Function<Order, BigDecimal> totalThenTax = Order::total.andThen(this::applyTax); // left to right
Function<Order, BigDecimal> taxThenTotal = applyTax.compose(Order::total);       // right to left
```

### Composing Predicates

```java
Predicate<String> nonEmpty = s -> !s.isEmpty();
Predicate<String> shortStr = s -> s.length() < 10;

Predicate<String> valid = nonEmpty.and(shortStr);
Predicate<String> either = nonEmpty.or(shortStr);
Predicate<String> notEmpty = nonEmpty.negate();
```

Composition is what makes a `Predicate` a reusable rule rather than a one-off lambda. `nonEmpty.and(shortStr).and(hasNoProfanity)` is a validator built from parts that can each be unit-tested alone — which is the real payoff in a service with business rules that change quarterly.

### Default methods in interfaces

Introduced in Java 8 to evolve interfaces without breaking existing implementations. `Function.andThen`, `Predicate.and`, `List.sort`, `Map.getOrDefault` are all default methods.

```java
interface Validator<T> {
    boolean validate(T t);
    
    default Validator<T> and(Validator<T> other) {
        return t -> this.validate(t) && other.validate(t);
    }
}
```

The subtlety in that example: `and` returns a `Validator`, not a boolean, so it composes. This is the difference between a default method that just adds behaviour and one that is designed for chaining — `Function.andThen`, `Comparator.thenComparing`, and `Stream.peek` all follow the same pattern.

### Interface evolution trade-offs

Default methods allow adding behavior to interfaces without breaking all implementors. But they introduce **multiple inheritance of behavior** — two interfaces can define the same default method, creating a compiler error in the implementing class (resolved by overriding the method explicitly).

The Java rule is explicit and worth quoting: a **class always wins over an interface**, and among interfaces, a **more specific declaration wins**. If two unrelated interfaces both declare `default void log()`, the implementing class must override it and can pick which one to call via `InterfaceA.super.log()`. This is not a tie-breaker the language arbitrates for you.

```java
class Service implements Auditable, Traceable {
    @Override
    public void log() {
        // Ambiguity was forced by the compiler; choose deliberately
        Auditable.super.log();
    }
}
```

### Common follow-ups

- **Can an interface default method be abstract again?** No — but a sub-interface can *re-declare* it abstract, which forces implementors of the sub-interface to provide it. This is how a library deprecates a default implementation over several releases.
- **Why can a default method access `this` but not instance state?** Because there are no instance fields on an interface. It can call other interface methods on `this`, which is how `and` works, but it cannot store anything.
- **Why do `Object` methods break the rule?** An interface cannot declare a `default` `equals`, `hashCode`, or `toString` — those are inherited from `Object` and cannot be overridden by a default method. This is a deliberate carve-out so no interface can accidentally break `Object`'s contract.
- **`default` vs `static` on an interface?** A `static` interface method belongs to the interface and cannot be overridden or called through an implementing class; it is the modern home for utilities that used to live on a `*Utils` class (`Comparator.comparing`, `Stream.of`).

### Mistakes to avoid

- Building deep chains of `andThen`/`compose` that nobody can read. Two or three compose cleanly; fifteen do not, and the stack trace when one fails will not tell you which.
- Implementing two interfaces with the same default method and letting the compiler error be the first time you notice the collision. Design the method set to avoid overlap.
- Throwing a checked exception from a composed default method — the composed functional interface cannot declare `throws`, so it has to be wrapped (Q046).
- Putting real business logic in a default method. Keep defaults as thin, composable glue; put the rules in a class you can inject and mock.

### Production perspective

Functional composition is how backend teams keep validation and pricing rules maintainable: each rule is a small, unit-tested `Predicate` or `Function`, and the full rule set is assembled by composition in configuration rather than edited into one large method. The operational caveat is that a failure in a composed chain produces a stacked stack trace, so keep the composition shallow and log at the rule boundary rather than relying on the trace for diagnosis.


<a id="chapter-3"></a>

# Chapter 3: Concurrency, Asynchronous Programming, and JVM

---

## Q051 — Java Threads and Lifecycle

**The one-line answer:** A thread is a unit of execution with its own call stack; its lifecycle moves through NEW → RUNNABLE → BLOCKED/WAITING/TIMED_WAITING → TERMINATED, and understanding each state is essential for reading thread dumps.

### Thread states

| State | Meaning |
|---|---|
| NEW | Created but `start()` not yet called |
| RUNNABLE | Executing or ready to execute on CPU |
| BLOCKED | Waiting to acquire a monitor lock |
| WAITING | Waiting indefinitely (`Object.wait()`, `Thread.join()`, `LockSupport.park()`) |
| TIMED_WAITING | Waiting with a timeout (`Thread.sleep`, `wait(timeout)`, `join(timeout)`) |
| TERMINATED | Execution complete |

### Creating threads

```java
// Option 1 — Runnable (preferred, separates task from execution mechanism)
Thread t = new Thread(() -> System.out.println("running"));
t.start(); // NOT t.run() — run() executes on the calling thread

// Option 2 — Extend Thread (rarely needed)
class MyThread extends Thread { public void run() { ... } }

// Option 3 — Callable via ExecutorService (production preference)
Future<String> f = executor.submit(() -> "result");
```

### Daemon threads

A JVM exits when all non-daemon threads finish. Daemon threads (`t.setDaemon(true)`) are automatically killed on JVM exit — never use them for work that must complete (database writes, file flushing). Set daemon status before `start()`.

### `start()` vs `run()`

`t.run()` executes the `Runnable` synchronously on the calling thread — no new thread is created. Always call `t.start()`.

---

## Q052 — Race Conditions, Visibility, and Happens-Before

**The one-line answer:** A race condition occurs when correctness depends on the relative timing of threads; the Java Memory Model (JMM) defines happens-before relationships that determine when one thread's writes are guaranteed visible to another.

### Race condition example

```java
// NOT thread-safe
private int counter = 0;
public void increment() { counter++; } // read-modify-write — three operations, not atomic
```

Two threads can read the same value, both increment, and both write back the same incremented value — one increment is lost.

### The Java Memory Model and happens-before

The JMM does not guarantee that one thread sees another thread's writes unless a happens-before relationship exists. Key rules:

- **Program order:** Each action in a thread happens-before every subsequent action in that same thread.
- **Monitor unlock → lock:** Unlocking a monitor happens-before any subsequent lock of that monitor.
- **Volatile write → read:** A write to a `volatile` field happens-before every subsequent read of that field.
- **Thread start:** `Thread.start()` happens-before any action in the started thread.
- **Thread join:** All actions in a thread happen-before `Thread.join()` returns.
- **Transitivity:** If A hb B and B hb C, then A hb C.

Without happens-before, the JVM and CPU are free to reorder writes and keep values in registers — another thread may see stale data indefinitely.

### Atomicity vs visibility

- **Visibility:** A thread may cache values in registers. `volatile` guarantees a write is flushed to main memory and a read always goes to main memory.
- **Atomicity:** Even if visible, a compound action (check-then-act, read-modify-write) can be interleaved. `volatile` does not fix this — use `synchronized` or `Atomic*` classes.

---

## Q053 — `synchronized` and Monitors

**The one-line answer:** `synchronized` acquires a monitor lock on an object before entering the block, guaranteeing mutual exclusion and establishing a happens-before relationship between the unlock and the next lock.

### Monitor basics

Every Java object has an associated monitor. `synchronized` on an instance method uses `this` as the lock; on a static method it uses the `Class` object.

```java
public class Counter {
    private int value = 0;

    // Instance method — lock is `this`
    public synchronized void increment() { value++; }

    // Static method — lock is Counter.class
    public static synchronized void reset() { ... }

    // Explicit block — allows finer-grained locking
    public void conditionalIncrement(int max) {
        synchronized (this) {
            if (value < max) value++;
        }
    }
}
```

### Reentrancy

Java monitors are reentrant — a thread already holding a lock can acquire it again without deadlocking. This is essential for synchronized methods calling other synchronized methods on the same object.

### What synchronized guarantees

1. **Mutual exclusion:** Only one thread executes the synchronized block at a time.
2. **Visibility:** All writes made before releasing the lock are visible to any thread that subsequently acquires it.

### Performance considerations

`synchronized` is not expensive for uncontended locks (JVM uses biased locking / lightweight CAS). It becomes a bottleneck under high contention. For read-heavy workloads, consider `ReadWriteLock`.

---

## Q054 — `volatile` Semantics

**The one-line answer:** `volatile` guarantees visibility (reads always see the latest write) and prevents reordering around the field, but does NOT guarantee atomicity of compound operations.

### Correct use — single-writer flag

```java
private volatile boolean shutdown = false;

// Writer thread
public void stop() { shutdown = true; }

// Reader thread
public void run() {
    while (!shutdown) { doWork(); }
}
```

Without `volatile`, the reader may cache `shutdown = false` in a register and loop forever even after the writer sets it to true.

### What volatile does NOT fix

```java
private volatile int counter = 0;
public void increment() { counter++; } // Still a race — read-modify-write is not atomic
```

### Happens-before with volatile

A write to a `volatile` variable happens-before every subsequent read of that variable (by any thread). This means all writes made by the writing thread before the volatile write are also visible to threads that read the volatile.

### Double-checked locking (classic use)

```java
private volatile Singleton instance;

public Singleton getInstance() {
    if (instance == null) {                    // first check — no lock
        synchronized (this) {
            if (instance == null) {            // second check — under lock
                instance = new Singleton();    // volatile ensures safe publication
            }
        }
    }
    return instance;
}
```

Without `volatile`, the partially-constructed object could be published before construction completes.

---

## Q055 — Explicit Locks: ReentrantLock, ReadWriteLock, StampedLock

**The one-line answer:** Explicit locks (`java.util.concurrent.locks`) give capabilities `synchronized` lacks: timed lock attempts, interruptible waiting, multiple condition variables, and read-write separation.

### ReentrantLock

```java
private final ReentrantLock lock = new ReentrantLock();

public void transfer(Account from, Account to, BigDecimal amount) {
    lock.lock();
    try {
        from.debit(amount);
        to.credit(amount);
    } finally {
        lock.unlock(); // always in finally
    }
}

// Timed attempt — avoids indefinite blocking
if (lock.tryLock(500, TimeUnit.MILLISECONDS)) {
    try { ... } finally { lock.unlock(); }
} else {
    // Handle timeout — could not acquire lock
}
```

### ReadWriteLock

Allows multiple concurrent readers OR one exclusive writer. Ideal for read-heavy, write-rare shared data.

```java
private final ReadWriteLock rwLock = new ReentrantReadWriteLock();

public Value read(String key) {
    rwLock.readLock().lock();
    try { return cache.get(key); }
    finally { rwLock.readLock().unlock(); }
}

public void write(String key, Value v) {
    rwLock.writeLock().lock();
    try { cache.put(key, v); }
    finally { rwLock.writeLock().unlock(); }
}
```

### StampedLock (Java 8+)

Adds **optimistic reads** — read without acquiring a lock, then validate:

```java
StampedLock sl = new StampedLock();
long stamp = sl.tryOptimisticRead();
double localX = x; double localY = y;
if (!sl.validate(stamp)) {
    stamp = sl.readLock();
    try { localX = x; localY = y; }
    finally { sl.unlockRead(stamp); }
}
```

`StampedLock` is non-reentrant and has no condition variables — use carefully.

---

## Q056 — Atomic Classes and CAS

**The one-line answer:** `java.util.concurrent.atomic` classes use Compare-And-Swap (CAS) CPU instructions to provide lock-free, thread-safe operations on single variables.

### Key classes

| Class | Use |
|---|---|
| `AtomicInteger` / `AtomicLong` | Counter, sequence generator |
| `AtomicBoolean` | Thread-safe flag |
| `AtomicReference<T>` | Thread-safe object swap |
| `LongAdder` / `LongAccumulator` | High-throughput counter (reduces CAS contention) |

### How CAS works

```java
AtomicInteger count = new AtomicInteger(0);
count.incrementAndGet();            // atomic read-modify-write
count.compareAndSet(5, 10);         // sets to 10 only if current value is 5

// Functional update (Java 8+)
count.updateAndGet(v -> v * 2);     // atomically doubles the value
```

CAS: "Set the value to `newValue` if and only if the current value is `expected`. Return whether it succeeded." This avoids locking — if the CAS fails (another thread changed the value), retry.

### LongAdder vs AtomicLong

Under high contention, multiple threads spinning on the same `AtomicLong` waste CPU. `LongAdder` maintains per-thread cells and only sums them on `sum()`. 

- Use `AtomicLong` when you need the current value frequently.
- Use `LongAdder` for pure high-throughput counters (HTTP request counts, event metrics).

### ABA problem

CAS checks value equality. If a value changes from A → B → A, the CAS succeeds even though the state changed in between. Use `AtomicStampedReference` when this matters (rare in practice).

---

## Q057 — Thread Pools and ExecutorService

**The one-line answer:** Thread pools reuse a fixed set of threads across tasks, avoiding the overhead of creating and destroying threads per request, and provide backpressure through bounded queues.

### Core pool types

```java
// Fixed pool — bounded parallelism
ExecutorService fixed = Executors.newFixedThreadPool(8);

// Single thread — sequential execution, ordered queue
ExecutorService single = Executors.newSingleThreadExecutor();

// Cached pool — unbounded threads, 60s keepalive — DANGEROUS for backend services
ExecutorService cached = Executors.newCachedThreadPool(); // can create thousands of threads

// Scheduled pool
ScheduledExecutorService scheduled = Executors.newScheduledThreadPool(4);

// Virtual thread executor (Java 21)
ExecutorService virtual = Executors.newVirtualThreadPerTaskExecutor();
```

### ThreadPoolExecutor — production configuration

```java
ThreadPoolExecutor pool = new ThreadPoolExecutor(
    4,                              // corePoolSize
    16,                             // maximumPoolSize
    60, TimeUnit.SECONDS,           // keepAliveTime for idle threads above core
    new ArrayBlockingQueue<>(1000), // bounded queue — provides backpressure
    new ThreadFactory() { ... },    // name your threads for diagnostics
    new ThreadPoolExecutor.CallerRunsPolicy() // rejection: execute on calling thread
);
```

### Rejection policies

| Policy | Behavior |
|---|---|
| `AbortPolicy` (default) | Throws `RejectedExecutionException` |
| `CallerRunsPolicy` | Calling thread executes the task — natural backpressure |
| `DiscardPolicy` | Silently discards the task |
| `DiscardOldestPolicy` | Discards oldest queued task, retries submission |

### Pool sizing heuristics

- **CPU-bound:** `N + 1` threads (N = available processors)
- **IO-bound:** `N × (1 + wait_time / service_time)` — more threads to cover IO wait
- **Virtual threads (Java 21):** One per task — let the JVM manage scheduling

### Shutdown

```java
pool.shutdown();                                    // stop accepting new tasks
pool.awaitTermination(30, TimeUnit.SECONDS);        // wait for in-flight tasks
pool.shutdownNow();                                 // interrupt running tasks if needed
```

---

## Q058 — Callable, Future, Timeouts, and Cancellation

**The one-line answer:** `Callable` is like `Runnable` but returns a result and can throw checked exceptions; `Future` is the handle to that result, supporting blocking get, timeouts, and cancellation.

### Basic usage

```java
ExecutorService exec = Executors.newFixedThreadPool(4);
Future<String> future = exec.submit(() -> {
    // can throw checked exceptions
    return httpClient.fetch("https://api.example.com/data");
});

try {
    String result = future.get(5, TimeUnit.SECONDS); // blocks up to 5s
} catch (TimeoutException e) {
    future.cancel(true);  // interrupt the running thread
    throw new ServiceUnavailableException("upstream timeout");
} catch (ExecutionException e) {
    throw new RuntimeException("task failed", e.getCause()); // unwrap real cause
} catch (InterruptedException e) {
    Thread.currentThread().interrupt(); // restore interrupt flag
    throw new RuntimeException(e);
}
```

### `cancel(mayInterruptIfRunning)`

- `false`: Cancels if not yet started; running tasks are unaffected.
- `true`: Interrupts the running thread. The task must check `Thread.isInterrupted()` or block on an interruptible operation to respond.

`isDone()` returns true whether the task completed, threw, or was cancelled. `isCancelled()` distinguishes cancellation.

### Common mistake — swallowing `InterruptedException`

```java
// BAD
try { Thread.sleep(1000); } catch (InterruptedException e) { /* ignored */ }

// GOOD — restore the interrupt flag so callers can detect it
try { Thread.sleep(1000); } catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    throw new RuntimeException("interrupted", e);
}
```

---

## Q059 — CompletableFuture Composition

**The one-line answer:** `CompletableFuture` enables non-blocking async pipelines through composable callbacks — `thenApply` transforms results, `thenCompose` chains async steps, `allOf` waits for all, and `exceptionally` handles failures without stopping the chain.

### Core methods

```java
CompletableFuture<Order> future = CompletableFuture
    .supplyAsync(() -> orderRepo.findById(id), executor)     // start async
    .thenApply(order -> enrich(order))                        // transform result (sync)
    .thenCompose(order -> applyDiscount(order))               // chain another async step
    .exceptionally(ex -> Order.failed(ex.getMessage()))       // handle error, return fallback
    .whenComplete((result, ex) -> log(result, ex));           // side effect, always runs
```

### thenApply vs thenCompose

- `thenApply(fn)` — `fn` is synchronous; returns `CompletableFuture<R>`.
- `thenCompose(fn)` — `fn` itself returns a `CompletableFuture<R>`; avoids `CompletableFuture<CompletableFuture<R>>` nesting.

### Combining multiple futures

```java
CompletableFuture<User>    userFuture    = fetchUser(userId);
CompletableFuture<Account> accountFuture = fetchAccount(userId);

CompletableFuture<Summary> summary = userFuture.thenCombine(
    accountFuture,
    (user, account) -> new Summary(user, account)
);

// Wait for all
CompletableFuture<Void> all = CompletableFuture.allOf(f1, f2, f3);
all.thenRun(() -> System.out.println("all done"));

// First to complete
CompletableFuture<String> first = CompletableFuture.anyOf(f1, f2).thenApply(r -> (String) r);
```

### Executor selection

By default, async stages run on the common `ForkJoinPool`. For IO-bound work, always supply a dedicated executor:

```java
.thenApplyAsync(order -> callExternalService(order), ioExecutor)
```

### Exception propagation

`exceptionally` catches and recovers. `handle(BiFunction<T, Throwable, R>)` always runs and can both recover and transform. If you don't handle an exception, it propagates to the next stage's `exceptionally` or to `get()`'s `ExecutionException`.

---

## Q060 — Thread Interruption

**The one-line answer:** Interruption is a cooperative cancellation mechanism — calling `thread.interrupt()` sets a flag; the thread must check and honor it. It does not forcibly kill a thread.

### How interruption works

```java
// Setting the interrupt flag
thread.interrupt();

// Checking the flag (does NOT clear it)
if (Thread.currentThread().isInterrupted()) { cleanup(); return; }

// Static version — CLEARS the flag
if (Thread.interrupted()) { ... }
```

### Interruptible blocking operations

`Thread.sleep()`, `Object.wait()`, `BlockingQueue.take()`, `Future.get()`, `Lock.lockInterruptibly()` all throw `InterruptedException` when the thread is interrupted, **clearing the interrupt flag**.

### The golden rule

Always restore the interrupt flag when catching `InterruptedException` (unless you are the top-level thread handler):

```java
public void processQueue(BlockingQueue<Task> queue) {
    while (!Thread.currentThread().isInterrupted()) {
        try {
            Task t = queue.take(); // blocks — throws InterruptedException on interrupt
            process(t);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt(); // restore flag
            break; // exit the loop
        }
    }
}
```

### Interruption in thread pools

When `Future.cancel(true)` is called, the executing thread is interrupted. Your task must respond by checking the interrupted flag or using interruptible blocking calls — otherwise cancellation has no effect.

---

## Q061 — Deadlocks

**The one-line answer:** A deadlock occurs when two or more threads each hold a lock the other needs, and all are waiting — none can proceed.

### Classic deadlock

```java
Object lockA = new Object();
Object lockB = new Object();

// Thread 1                        // Thread 2
synchronized (lockA) {             synchronized (lockB) {
    synchronized (lockB) { ... }       synchronized (lockA) { ... }
}                                  }
```

Thread 1 holds lockA, waits for lockB. Thread 2 holds lockB, waits for lockA. Both wait forever.

### Four conditions (Coffman)

All four must hold simultaneously:
1. **Mutual exclusion** — a resource can only be held by one thread.
2. **Hold and wait** — a thread holds resources while waiting for others.
3. **No preemption** — locks cannot be forcibly taken away.
4. **Circular wait** — a cycle of threads waiting on each other.

### Prevention strategies

- **Lock ordering:** Always acquire locks in a consistent global order. If all threads lock A before B, no cycle forms.
- **Timed lock attempts:** `ReentrantLock.tryLock(timeout)` — if acquisition fails, release held locks and retry.
- **Lock-free algorithms:** Use `ConcurrentHashMap`, `AtomicReference`, etc.
- **Single lock:** If possible, serialize access through one lock or a single-threaded executor.

### Detection

Thread dump (`kill -3` or `jstack <pid>`) shows "found one Java-level deadlock" with the cycle of threads and held locks.

---

## Q062 — Livelock and Starvation

### Livelock

Threads are active (not blocked) but repeatedly react to each other and make no progress:

```java
// Two threads both "politely" yield when they detect a conflict
// but always detect a conflict at the same time — neither progresses
while (anotherThreadIsActive) {
    pauseAndRetry(); // both do this simultaneously, forever
}
```

Fix: randomized backoff (`Thread.sleep(random.nextInt(100))`), or a coordinator that grants exclusive turn.

### Starvation

One thread never gets CPU time because higher-priority threads or unfair scheduling always win. In Java thread pools, an unbounded queue can cause low-priority tasks to wait forever if the pool is always occupied.

Fixes:
- Use fair locks: `new ReentrantLock(true)` — threads acquire in arrival order.
- Bound queues and control pool size so all tasks get turns.
- Priority queues with guaranteed minimum throughput.

### How to diagnose

Thread dump: a starved thread will be in RUNNABLE or TIMED_WAITING repeatedly, but its completion counter never increments. Livelock shows in flame graphs as a hot loop with no actual work.

---

## Q063 — ConcurrentHashMap

**The one-line answer:** `ConcurrentHashMap` is a thread-safe hash map that uses lock striping (segment-level or bucket-level CAS in Java 8+) to allow concurrent reads and fine-grained writes without a global lock.

### Key behaviors

- **Reads are lock-free** — `get()` uses volatile reads, never blocks.
- **Writes use CAS or synchronized per bin** — only the affected bucket is locked.
- **Iterators are weakly consistent** — they may or may not reflect updates made after iterator creation; they never throw `ConcurrentModificationException`.
- **`size()` is approximate** — it uses `LongAdder`-style counting and is eventually consistent.
- **Null keys and values are forbidden** — throws `NullPointerException` (unlike `HashMap`).

### Atomic compound operations

```java
ConcurrentHashMap<String, Integer> counts = new ConcurrentHashMap<>();

// Atomic "get or create"
counts.computeIfAbsent("key", k -> 0);

// Atomic increment
counts.merge("key", 1, Integer::sum);

// Atomic conditional update
counts.compute("key", (k, v) -> v == null ? 1 : v + 1);
```

**Never** combine a `get` and a `put` without atomicity:

```java
// WRONG — race condition between get and put
if (!map.containsKey(k)) map.put(k, newValue());

// CORRECT
map.putIfAbsent(k, newValue());
map.computeIfAbsent(k, key -> newValue());
```

---

## Q064 — Thread-Safe Design Strategies

**The one-line answer:** The safest concurrency strategy is to avoid shared mutable state; when state must be shared, prefer immutability and confinement before reaching for locks.

### Hierarchy of strategies (safest to most complex)

1. **Don't share:** Stateless services (Spring singleton beans with no mutable fields) are trivially thread-safe.
2. **Immutability:** Immutable objects can be shared freely without synchronization.
3. **Thread confinement:** Keep mutable state in variables only one thread accesses (`ThreadLocal`, stack-local variables).
4. **Synchronized access:** Protect all reads and writes with a lock.
5. **Concurrent collections:** Use `ConcurrentHashMap`, `CopyOnWriteArrayList` etc. for shared collections.
6. **Atomic variables:** For single-variable counters and flags.

### Spring context

Spring singletons are instantiated once and shared across all request threads. If a singleton bean has a mutable field, every request races to modify it:

```java
// DANGEROUS — mutable instance field on a singleton
@Service
public class OrderService {
    private Order lastOrder; // shared across all threads — data race!
}

// SAFE — stateless, or immutable collaborators
@Service
public class OrderService {
    private final OrderRepository repo; // injected, effectively immutable reference
    public Order findById(String id) { return repo.findById(id).orElseThrow(); }
}
```

Request-scoped data belongs in method parameters, not instance fields.

---

## Q065 — ThreadLocal

**The one-line answer:** `ThreadLocal` provides per-thread storage — each thread accessing the variable sees its own isolated copy, making it useful for request context like correlation IDs and locale, but dangerous in thread pools if not cleaned up.

### Basic usage

```java
private static final ThreadLocal<String> REQUEST_ID = new ThreadLocal<>();

// On request start (e.g., filter)
REQUEST_ID.set(UUID.randomUUID().toString());

// Anywhere in the same thread's call stack
String id = REQUEST_ID.get();

// MUST clean up — or use withInitial + remove
REQUEST_ID.remove();
```

### Memory leak risk

In thread pools, threads are reused. If `remove()` is never called, the `ThreadLocal` value persists for the life of the thread and can be seen by a future, unrelated request:

```java
// Safe pattern with try/finally
try {
    REQUEST_ID.set(generateId());
    handleRequest();
} finally {
    REQUEST_ID.remove(); // always clean up
}
```

### MDC (Mapped Diagnostic Context)

Logback/SLF4J's MDC is built on `ThreadLocal`. Set a correlation ID at the filter/interceptor level and it appears in all log lines from that request thread automatically:

```java
MDC.put("requestId", correlationId);
try { chain.doFilter(request, response); }
finally { MDC.clear(); }
```

Virtual threads (Java 21) have their own `ThreadLocal` copies but scoped locals (`ScopedValue`, preview) are the preferred alternative for structured, lightweight context propagation.

---

## Q066 — Virtual Threads in Java 21

**The one-line answer:** Virtual threads are JVM-managed lightweight threads that mount onto OS threads only during CPU execution, allowing millions of concurrent blocking operations without the overhead of millions of OS threads.

### How they work

Traditional platform threads are 1:1 with OS threads (~1 MB stack each). Virtual threads are N:M — many virtual threads share a small number of carrier (OS) threads from the `ForkJoinPool`. When a virtual thread blocks on IO (`InputStream.read()`, JDBC, HTTP client), it unmounts from the carrier thread, which is then free to run another virtual thread. When the IO completes, the virtual thread is rescheduled.

### Usage

```java
// Per-task executor — simplest model
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    for (var req : requests) {
        executor.submit(() -> processRequest(req)); // thousands of tasks, few OS threads
    }
}

// Spring Boot 3.2+ — enable globally
// application.properties:
// spring.threads.virtual.enabled=true
```

### When virtual threads help

- IO-bound services: REST clients, JDBC, file IO — each blocking call yields the carrier thread.
- High concurrency with blocking APIs — write simple blocking code that scales like reactive.

### When virtual threads don't help

- **CPU-bound work:** Virtual threads don't add parallelism — you're still bound by CPU cores.
- **Pinning:** `synchronized` blocks and native method frames pin the virtual thread to its carrier, blocking it. Replace with `ReentrantLock`.

### Pinning example

```java
// BAD with virtual threads — synchronized pins the carrier
synchronized (lock) {
    var result = jdbcTemplate.queryForObject(...); // IO inside synchronized = pinning
}

// GOOD — ReentrantLock does not pin
lock.lock();
try { var result = jdbcTemplate.queryForObject(...); }
finally { lock.unlock(); }
```

### JVM flags for pinning detection

```
-Djdk.tracePinnedThreads=short
```

---

## Q067 — Structured Concurrency (Java 21 Preview)

**The one-line answer:** Structured concurrency treats a group of concurrent tasks as a single unit of work — if the parent scope exits, all child tasks are cancelled, preventing orphaned threads and simplifying cancellation and error propagation.

### Core API

```java
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Future<User>    userFuture    = scope.fork(() -> fetchUser(id));
    Future<Account> accountFuture = scope.fork(() -> fetchAccount(id));
    
    scope.join();           // wait for both
    scope.throwIfFailed();  // propagate first failure
    
    return new UserSummary(userFuture.resultNow(), accountFuture.resultNow());
}
// scope.close() cancels any still-running subtasks
```

### Why it matters

With plain `CompletableFuture`, if one async task fails, the others may keep running as orphans. With `StructuredTaskScope.ShutdownOnFailure`, the first failure automatically cancels siblings. `ShutdownOnSuccess` returns the first successful result and cancels the rest.

This is a preview API in Java 21 — not yet production-stable, but represents the direction for safe concurrent code.

---

## Q068 — JVM Memory Areas

**The one-line answer:** The JVM divides memory into heap (object instances), stack (per-thread frames and locals), metaspace (class metadata), and native memory (OS allocations), each with distinct failure modes.

### Memory areas

| Area | Contents | Failure |
|---|---|---|
| **Heap** | Object instances, arrays | `OutOfMemoryError: Java heap space` |
| **Stack** | Method frames, local variables, operand stack | `StackOverflowError` |
| **Metaspace** | Class metadata, method bytecode | `OutOfMemoryError: Metaspace` |
| **Code Cache** | JIT-compiled native code | `CodeCache is full` warning |
| **Native/Direct** | NIO direct buffers, JNI memory | `OutOfMemoryError: Direct buffer memory` |

### Young vs Old generation (G1, ZGC)

The heap is divided into **young generation** (new allocations; short-lived objects collected frequently in minor GCs) and **old generation** (long-lived objects; collected in major/full GCs). G1GC and ZGC further partition into regions for concurrent, low-pause collection.

### Common questions

- **StackOverflowError:** Infinite or very deep recursion. Increase with `-Xss` (per thread) or fix the recursion.
- **Heap OOM:** Object leak, oversized cache, or heap too small. Tune `-Xmx` / `-XX:MaxRAMPercentage`.
- **Metaspace OOM:** Dynamic class generation (CGLib proxies, Groovy scripts) without bounds. Set `-XX:MaxMetaspaceSize`.

---

## Q069 — Garbage Collection Basics

**The one-line answer:** GC automatically reclaims objects unreachable from GC roots; the choice of collector (G1, ZGC, Shenandoah) trades throughput for pause time and memory overhead.

### GC algorithms (Java 17/21)

| Collector | Flag | Strengths | Weakness |
|---|---|---|---|
| **G1GC** | Default | Balanced throughput and pauses, heap ≥ 6 GB | Occasional long full GC |
| **ZGC** | `-XX:+UseZGC` | Sub-millisecond pauses, scales to TB heaps | Higher CPU overhead |
| **Shenandoah** | `-XX:+UseShenandoahGC` | Low pause, concurrent evacuation | Higher throughput overhead |
| **SerialGC** | `-XX:+UseSerialGC` | Minimal overhead | Not for production servers |

### GC cycle (G1)

1. **Minor GC (Young):** Short-lived objects in Eden/Survivor regions collected frequently. Most objects die young (generational hypothesis).
2. **Concurrent marking:** Identifies live objects in old regions while application runs.
3. **Mixed GC:** Collects young + most garbage-dense old regions.
4. **Full GC:** Stop-the-world fallback when concurrent cycle can't keep up — the event to avoid.

### Tuning levers

```
-Xms2g -Xmx2g              # fix heap size to avoid resizing pauses
-XX:MaxGCPauseMillis=200    # G1 target pause goal
-XX:G1HeapRegionSize=16m    # for large heaps
-XX:+UseZGC                 # for latency-sensitive services
```

### Key metric: allocation rate

High allocation rates fill Eden quickly, triggering frequent minor GCs. Reducing unnecessary object creation (reusing buffers, avoiding string concatenation in hot paths) reduces GC pressure.

---

## Q070 — Memory Leaks in Java

**The one-line answer:** Java memory leaks occur when objects are kept reachable (through references the application holds) but are no longer needed — the GC cannot collect them because they are not unreachable, just unused.

### Common leak sources

**1. Static caches / collections**
```java
private static final Map<String, byte[]> cache = new HashMap<>();
// Never evicted — grows unboundedly
```
Fix: use `WeakHashMap`, a cache with TTL/size eviction (Caffeine), or `SoftReference`.

**2. Unclosed resources**
Open connections, streams, or files prevent GC of the associated object. Fix: `try-with-resources`.

**3. ThreadLocal not removed**
In a thread pool, `ThreadLocal` values persist for the thread's lifetime. Fix: always call `ThreadLocal.remove()`.

**4. Event listeners / callbacks not deregistered**
An object registered as a listener is held by the event source. Fix: deregister in `@PreDestroy` or lifecycle teardown.

**5. Classloader leaks (application servers)**
Static fields referencing application classes prevent classloader GC during redeployment. Fix: clean up in `ServletContextListener.contextDestroyed`.

### Heap dump analysis

```bash
jmap -dump:format=b,file=heap.hprof <pid>
# Then open in Eclipse MAT (Memory Analyzer Tool)
# Look for: "Leak Suspects", dominator tree, largest retained sets
```

Retained heap = the heap freed if this object were collected (itself + everything it keeps alive).

---

## Q071 — JVM Flags and Container Sizing

**The one-line answer:** In containers, JVM heap sizing must use percentage-based flags (`-XX:MaxRAMPercentage`) rather than absolute `-Xmx` to respect container memory limits and avoid `OOMKilled`.

### Container-aware flags (Java 10+)

```
-XX:MaxRAMPercentage=75.0    # heap = 75% of container memory limit
-XX:InitialRAMPercentage=50.0
-XX:MinRAMPercentage=25.0    # for containers with < 200MB
```

Avoid `-Xmx` hardcoded to a value larger than container limit — the JVM will not be aware of the container's cgroup limit.

### Total JVM memory > heap

Heap is not the only consumer:

```
Total memory = Heap + Metaspace + Code Cache + Thread stacks + Native/Direct buffers
```

A container with 1 GB limit and `-XX:MaxRAMPercentage=75` gives 750 MB heap, leaving ~250 MB for the rest. Monitor `jvm.memory.max` and `jvm.memory.committed` metrics.

### CPU limits

```
-XX:ActiveProcessorCount=4   # override JVM's CPU detection for containers
```

Without this, the JVM may size thread pools based on node CPU count rather than container limits, creating more threads than useful.

### Kubernetes liveness vs readiness startup time

Use `-XX:TieredStopAtLevel=1` or `-XX:+TieredCompilation` flags with startup profiling. Spring Boot 3.x AOT compilation helps. CRaC (Coordinated Restore at Checkpoint) is an option for sub-second startup.

---

## Q072 — Performance Symptom Triage

**The one-line answer:** Structured triage maps symptoms (high CPU, high latency, GC pauses, thread exhaustion) to causes using a layered approach: metrics → logs → thread dump → heap dump → profiler.

### Symptom → likely cause map

| Symptom | Investigate |
|---|---|
| High CPU | Thread dump (busy loops), profiler (hot methods), GC logs |
| High latency (p99) | Slow external calls, DB query plans, lock contention |
| High latency (all) | Thread pool exhaustion, GC pauses |
| OOM / OOMKilled | Heap dump, allocation profiler, large object graphs |
| GC pauses | GC logs (`-Xlog:gc*`), allocation rate, heap size |
| Thread pool full | Thread dump, queue depth metric, upstream slowness |
| Connection pool full | DB slow queries, pool size vs concurrency |

### Toolchain

```bash
# Thread dump — diagnose blocking, deadlocks, hot loops
jstack <pid>
jcmd <pid> Thread.print

# Heap dump
jcmd <pid> GC.heap_dump /tmp/heap.hprof

# GC logs
-Xlog:gc*:file=/logs/gc.log:time,uptime,level,tags:filecount=5,filesize=20m

# Profiler (async-profiler)
./profiler.sh -d 30 -f /tmp/flamegraph.html <pid>
```

### The triage sequence

1. Check **dashboards** — which RED metric (rate, errors, duration) spiked first?
2. Correlate **deployment or config change** — did something change 5 minutes before the spike?
3. Check **GC logs** — is the JVM spending >10% of time in GC?
4. Take a **thread dump** — are threads blocked? On what? Who holds the lock?
5. If OOM suspected — **heap dump** and MAT analysis.

---

## Q073 — Thread and Heap Dump Analysis

**The one-line answer:** Thread dumps show what every thread is doing at a point in time (essential for deadlocks and hot locks); heap dumps show the object graph in memory (essential for memory leaks and OOM diagnosis).

### Reading a thread dump

```
"http-nio-8080-exec-1" #23 prio=5 os_prio=0 cpu=1234ms elapsed=300s tid=0x... nid=0x... waiting on condition
  java.lang.Thread.State: WAITING (parking)
    at sun.misc.Unsafe.park(...)
    at java.util.concurrent.locks.LockSupport.park(...)
    at com.example.OrderService.processOrder(OrderService.java:42)  ← your code
```

Look for:
- **BLOCKED** threads — what lock are they waiting for? Who holds it?
- **Thread count** — hundreds of blocked threads = pool exhaustion or upstream slowness.
- **"deadlock" keyword** — jstack explicitly reports Java-level deadlocks.
- **CPU-hot threads** — cross-reference with `top -H -p <pid>` (Linux) to find the thread consuming most CPU.

### Reading a heap dump (MAT)

1. **Leak Suspects Report** — MAT identifies objects with high retained heap.
2. **Dominator Tree** — shows which single objects keep the most heap alive.
3. **Histogram** — shows instance counts by class; a suspiciously large count of `byte[]` often indicates string or I/O buffering.
4. **OQL (Object Query Language)** — query the heap like SQL for specific object patterns.

### Capturing without restarting

```bash
kill -3 <pid>                  # thread dump to stdout (SIGQUIT on Linux)
jcmd <pid> Thread.print        # preferred — output to console
jcmd <pid> GC.heap_dump /path/to/heap.hprof
```

---

## Q074 — Class Loading Errors

**The one-line answer:** `ClassNotFoundException` means the class file was not found on the classpath; `NoClassDefFoundError` means the class file was found and loaded but failed during static initialization, or was available at compile time but not at runtime.

### `ClassNotFoundException`

- Thrown by `Class.forName()`, `ClassLoader.loadClass()`.
- The class simply doesn't exist on the classpath at runtime.
- Common cause: a `provided` scope dependency not bundled into the fat jar, or a missing optional dependency.

### `NoClassDefFoundError`

- Thrown when a class was used by compiled code (`new Foo()`, `Foo.class`) but is unavailable at runtime.
- Often happens when: a library is a compile-time dependency but excluded from the runtime artifact; or a class was found but its static initializer threw an exception (`ExceptionInInitializerError`) — subsequent uses see `NoClassDefFoundError`.
- Can also indicate classloader isolation: two libraries include different versions of the same class.

### Dependency conflicts

In multi-module Spring Boot projects or when shading JARs, two versions of the same library can end up on the classpath. The JVM loads the first one found (classpath ordering). Use `mvn dependency:tree` or Gradle's `dependencyInsight` to identify conflicts. Use `<excludes>` or dependency constraints to resolve.

---

## Q075 — Java 17 vs Java 21 Runtime Differences

**The one-line answer:** Java 21 adds virtual threads (production-ready), sequenced collections, finalized pattern matching, and ZGC improvements — the most impactful runtime change for backend services is virtual threads enabling high-concurrency blocking IO without reactive frameworks.

### Feature comparison

| Feature | Java 17 | Java 21 |
|---|---|---|
| Virtual threads | Preview (19/20) | **Finalized** |
| Pattern matching switch | Preview | **Finalized** |
| Record patterns | Preview (19/20) | **Finalized** |
| Sequenced collections | — | **New API** |
| Structured concurrency | — | Preview |
| String templates | — | Preview |
| ZGC | Production | Generational ZGC (better) |
| Sealed classes | Finalized (17) | Available |
| Records | Finalized (16) | Available |

### Migration guidance

- Java 21 is LTS. Java 17 is also LTS. Both are appropriate for production.
- The primary migration risk is `synchronized` + IO under virtual threads (pinning). Audit and replace with `ReentrantLock`.
- Spring Boot 3.2+ is required for idiomatic virtual thread support.
- Test GC behavior under load — generational ZGC in 21 can significantly reduce pause times.
- Check for removed/deprecated APIs: `finalize()` removed, some security manager APIs removed.

### Recommended upgrade path

1. Compile and test against Java 21 without enabling virtual threads.
2. Run tests with virtual threads enabled (`spring.threads.virtual.enabled=true`).
3. Monitor for pinning warnings (`-Djdk.tracePinnedThreads=short`).
4. Fix `synchronized` around IO before production rollout.


<a id="chapter-4"></a>

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


<a id="chapter-5"></a>

# Chapter 5: SQL, Transactions, JPA, and Hibernate

---

## Q106 — SELECT, WHERE, GROUP BY, HAVING

**The one-line answer:** These are the fundamental SQL clauses for filtering rows (WHERE), aggregating groups (GROUP BY), and filtering those groups (HAVING) — mastering their execution order is essential for writing correct queries.

### Logical execution order

```
FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT
```

This matters because:
- `WHERE` filters **rows before** grouping — cannot use aggregate functions here.
- `HAVING` filters **groups after** aggregation — can use aggregate functions.
- Column aliases defined in `SELECT` are NOT available in `WHERE` or `HAVING` (in most databases).

### Core examples

```sql
-- Total revenue per customer, only customers who ordered more than 5 times
SELECT customer_id,
       COUNT(*)            AS order_count,
       SUM(total_amount)   AS revenue
FROM   orders
WHERE  status = 'COMPLETED'           -- filter rows first
GROUP  BY customer_id
HAVING COUNT(*) > 5                   -- filter groups
ORDER  BY revenue DESC;

-- NULL behavior: NULL values are excluded from aggregate functions
-- COUNT(*) counts all rows; COUNT(column) excludes NULLs
SELECT COUNT(*), COUNT(discount_code) FROM orders;
-- Different results if discount_code has NULLs
```

### DISTINCT vs GROUP BY

`DISTINCT` removes duplicate rows from the result. `GROUP BY` enables aggregation. Don't use `GROUP BY` just for deduplication — `DISTINCT` is clearer and often faster.

### Interview tip

Interviewers often ask: "Why is `WHERE SUM(total) > 100` a syntax error?" — because `WHERE` runs before `GROUP BY`, so aggregates don't exist yet. Use `HAVING SUM(total) > 100`.

---

## Q107 — SQL Joins

**The one-line answer:** Joins combine rows from multiple tables based on a condition; understanding which rows are included/excluded for each join type prevents common bugs like unexpected nulls and duplicate rows.

### Join types

```sql
-- INNER JOIN — only rows with matches in both tables
SELECT o.id, c.name
FROM   orders o
INNER  JOIN customers c ON o.customer_id = c.id;

-- LEFT JOIN — all rows from left table, NULLs for unmatched right
SELECT c.id, c.name, COUNT(o.id) AS order_count
FROM   customers c
LEFT   JOIN orders o ON o.customer_id = c.id
GROUP  BY c.id, c.name;

-- RIGHT JOIN — all rows from right table (rarely used; rewrite as LEFT JOIN)

-- FULL OUTER JOIN — all rows from both, NULLs where no match
SELECT c.id, o.id
FROM   customers c
FULL   OUTER JOIN orders o ON o.customer_id = c.id;

-- CROSS JOIN — cartesian product, every row × every row
SELECT p1.name, p2.name FROM products p1 CROSS JOIN products p2;
```

### Duplicate rows from joins

A one-to-many join multiplies rows. Joining `orders` to `order_items` returns one row per item, not per order. Use `DISTINCT`, aggregation, or subqueries to handle this.

```sql
-- WRONG — order total appears once per item
SELECT o.id, o.total, i.product_id FROM orders o JOIN order_items i ON i.order_id = o.id;

-- Fix with subquery for item count
SELECT o.id, o.total, (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) AS item_count
FROM orders o;
```

### Join performance

Ensure join columns are **indexed** on both sides. Large table scans on join columns will cause sequential scans — check with `EXPLAIN`.

---

## Q108 — Subqueries, CTEs, and Window Functions

**The one-line answer:** CTEs (`WITH`) make complex queries readable and reusable; window functions apply aggregate calculations over a partition of rows without collapsing them — both are essential for analytical SQL beyond basic aggregations.

### CTE (Common Table Expression)

```sql
WITH active_customers AS (
    SELECT customer_id, SUM(total_amount) AS lifetime_value
    FROM orders
    WHERE status = 'COMPLETED'
    GROUP BY customer_id
),
vip_threshold AS (
    SELECT PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY lifetime_value) AS threshold
    FROM active_customers
)
SELECT ac.customer_id, ac.lifetime_value
FROM   active_customers ac, vip_threshold vt
WHERE  ac.lifetime_value >= vt.threshold;
```

### Recursive CTE — hierarchical data

```sql
WITH RECURSIVE category_tree AS (
    SELECT id, name, parent_id, 1 AS depth
    FROM categories WHERE parent_id IS NULL
    UNION ALL
    SELECT c.id, c.name, c.parent_id, ct.depth + 1
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree ORDER BY depth, name;
```

### Window functions

```sql
-- Rank orders within each customer by total (no grouping collapse)
SELECT
    customer_id,
    id AS order_id,
    total_amount,
    RANK()   OVER (PARTITION BY customer_id ORDER BY total_amount DESC) AS rank,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at)    AS seq,
    SUM(total_amount) OVER (PARTITION BY customer_id)                    AS customer_total,
    LAG(total_amount) OVER (PARTITION BY customer_id ORDER BY created_at) AS prev_order_total
FROM orders;
```

`PARTITION BY` divides rows into groups (like GROUP BY but doesn't collapse). `ORDER BY` inside `OVER` defines frame order. Common functions: `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LEAD`, `LAG`, `SUM`, `AVG`, `FIRST_VALUE`, `LAST_VALUE`.

---

## Q109 — Indexes

**The one-line answer:** Indexes are separate data structures (typically B-trees) that the database maintains to speed up row lookups; the key decisions are which columns to index, in what order, and which index type — because every index has a write cost.

### B-tree index (default)

```sql
-- Single column
CREATE INDEX idx_orders_customer_id ON orders(customer_id);

-- Composite — column order matters
CREATE INDEX idx_orders_customer_status ON orders(customer_id, status);
-- Supports: WHERE customer_id = ?
--           WHERE customer_id = ? AND status = ?
-- Does NOT efficiently support: WHERE status = ? (leading column missing)

-- Covering index — index includes all columns needed for query
CREATE INDEX idx_orders_covering ON orders(customer_id, status) INCLUDE (total_amount, created_at);
-- Query can be answered from index alone — no heap access needed
```

### Index selectivity

High selectivity = few rows per distinct value = index is effective. Low selectivity (e.g., boolean column, status with 3 values over millions of rows) → full scan may be faster. The query planner decides.

### Partial index

```sql
-- Index only rows where status = 'PENDING' — smaller, faster for pending-only queries
CREATE INDEX idx_orders_pending ON orders(created_at) WHERE status = 'PENDING';
```

### Write cost

Every `INSERT`, `UPDATE` (on indexed columns), and `DELETE` must also update all relevant indexes. Over-indexing slows writes. For bulk inserts, consider dropping indexes and rebuilding after.

### Index types

| Type | Use case |
|---|---|
| B-tree | Default, equality, range, ORDER BY, LIKE prefix |
| Hash | PostgreSQL: equality only, faster than B-tree for exact match |
| GIN | JSONB, array, full-text search |
| GiST | Geometric data, ranges |
| BRIN | Very large append-only tables (timestamps) |

---

## Q110 — EXPLAIN and Why Indexes Are Not Used

**The one-line answer:** `EXPLAIN ANALYZE` shows the actual query plan and row counts — understanding when the planner chooses a sequential scan over an index scan (and why) is the core skill for SQL performance tuning.

### Reading EXPLAIN output

```sql
EXPLAIN ANALYZE
SELECT * FROM orders WHERE customer_id = 'C123' AND status = 'PENDING';
```

```
Index Scan using idx_orders_customer_status on orders  (cost=0.42..8.45 rows=3 width=120) (actual time=0.05..0.12 rows=3 loops=1)
  Index Cond: ((customer_id = 'C123') AND (status = 'PENDING'))
```

Key terms:
- **Seq Scan** — reads every row. Expected for small tables or low-selectivity filters.
- **Index Scan** — uses index to find rows, then fetches from heap.
- **Index Only Scan** — all needed data is in the index (covering index).
- **Bitmap Heap Scan** — multiple index lookups combined, then heap fetched.
- **cost=startup..total** — estimated cost units.
- **rows** — estimated vs actual — large divergence = stale statistics (run `ANALYZE`).
- **loops** — how many times this node was executed (in nested loops).

### Why the planner ignores an index

1. **Low selectivity:** The condition matches most rows — full scan is cheaper.
2. **Function on indexed column:** `WHERE LOWER(email) = 'x'` — the B-tree index on `email` is not used. Fix: functional index `CREATE INDEX ON users(LOWER(email))`.
3. **Implicit type cast:** `WHERE user_id = 123` where `user_id` is `VARCHAR` — cast prevents index use. Fix: use `WHERE user_id = '123'` or fix schema types.
4. **Leading column missing from composite index:** `WHERE status = 'ACTIVE'` with index on `(customer_id, status)`.
5. **Stale statistics:** Run `ANALYZE table_name` to refresh.
6. **Very small table:** Planner correctly chooses seq scan.
7. **LIKE with leading wildcard:** `WHERE name LIKE '%smith'` — B-tree cannot help. Use full-text search.

---

## Q111 — ACID and Transaction Boundaries

**The one-line answer:** ACID properties guarantee that database transactions are reliable — Atomicity (all or nothing), Consistency (rules preserved), Isolation (concurrent transactions don't interfere), Durability (committed data survives failure).

### ACID explained

- **Atomicity:** All operations in a transaction succeed or all are rolled back. A partial failure leaves no partial state. Implemented via undo logs.
- **Consistency:** A transaction brings the database from one valid state to another — constraints, triggers, and cascades all fire within the transaction.
- **Isolation:** Concurrent transactions behave as if executed serially (at SERIALIZABLE). Lower isolation levels trade correctness for performance.
- **Durability:** A committed transaction survives crashes. Implemented via WAL (Write-Ahead Log) — changes are logged to durable storage before the commit returns.

### Transaction boundaries in Spring + JPA

```java
// Application transaction
@Transactional  // starts transaction before method, commits/rolls back on exit
public void placeOrder(CreateOrderCommand cmd) {
    Order order = new Order(cmd);
    repository.save(order);               // SQL INSERT — happens in transaction
    eventPublisher.publish(new OrderPlaced(order)); // if this throws, INSERT is rolled back
}
```

Keep transactions **short**. Long-running transactions hold locks, block other transactions, and increase rollback cost. Never hold a transaction open while calling an external HTTP service.

### Two-phase commit (distributed transactions)

In microservices, ACID across services requires 2PC (XA) or the Saga pattern. 2PC is slow and brittle. The Saga pattern with compensating transactions is the modern alternative (covered in Q152).

---

## Q112 — Isolation Levels and Anomalies

**The one-line answer:** Each isolation level prevents a specific set of read anomalies at the cost of concurrency — know which anomaly each level allows and what PostgreSQL's MVCC actually gives you.

### Read anomalies

| Anomaly | Description |
|---|---|
| **Dirty read** | Reading uncommitted data from another transaction |
| **Non-repeatable read** | Same row read twice in same tx returns different values (another tx committed a change) |
| **Phantom read** | Same query returns different rows (another tx inserted/deleted matching rows) |
| **Lost update** | Two transactions read a value, both update it — one update is lost |

### Isolation levels

| Level | Dirty Read | Non-Repeatable | Phantom |
|---|---|---|---|
| READ UNCOMMITTED | ✅ | ✅ | ✅ |
| READ COMMITTED | ❌ | ✅ | ✅ |
| REPEATABLE READ | ❌ | ❌ | ✅ (standard), ❌ (PostgreSQL MVCC) |
| SERIALIZABLE | ❌ | ❌ | ❌ |

### PostgreSQL specifics

PostgreSQL uses **MVCC** (Multi-Version Concurrency Control) — readers never block writers and writers never block readers. Each transaction sees a snapshot of the database at its start (READ COMMITTED) or at first statement (REPEATABLE READ). This eliminates dirty reads at all levels and prevents phantom reads at REPEATABLE READ.

PostgreSQL's SERIALIZABLE uses SSI (Serializable Snapshot Isolation) — detects serialization conflicts and aborts one of the conflicting transactions rather than blocking.

Note that the anomaly table above is the SQL-standard one and it is incomplete for real databases. **Lost update** is the anomaly that actually bites people, and it is possible at READ COMMITTED and REPEATABLE READ — it needs `SELECT ... FOR UPDATE`, an optimistic version column, or `UPDATE ... WHERE version = ?` to prevent. Snapshot isolation also still permits **write skew** (two transactions each read an overlapping set, then write disjoint rows based on what they read), which only true SERIALIZABLE prevents. Say this out loud in an interview — it is the answer that shows you have hit these in production rather than memorised the table.

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

---

## Q113 — Database Locks and Deadlocks

**The one-line answer:** PostgreSQL uses row-level locks to prevent conflicting concurrent writes; `SELECT FOR UPDATE` acquires an exclusive lock; deadlocks are automatically detected and one transaction is killed — the application must retry.

### Lock types (PostgreSQL)

```sql
-- Shared lock — multiple readers allowed, blocks exclusive writers
SELECT * FROM orders WHERE id = 1 FOR SHARE;

-- Exclusive row lock — blocks other exclusive locks
SELECT * FROM orders WHERE id = 1 FOR UPDATE;

-- Skip locked rows — for queue-style processing (job tables)
SELECT * FROM jobs WHERE status = 'PENDING' LIMIT 10 FOR UPDATE SKIP LOCKED;

-- NOWAIT — fail immediately if lock not available
SELECT * FROM accounts WHERE id = 1 FOR UPDATE NOWAIT;
```

### Lock timeout

```sql
SET lock_timeout = '5s';  -- per session
```

Or in Spring: `@QueryHint(name = "javax.persistence.lock.timeout", value = "5000")`

### Deadlock example and prevention

```
Tx1: UPDATE accounts SET balance = balance - 100 WHERE id = 1;
     UPDATE accounts SET balance = balance + 100 WHERE id = 2;

Tx2: UPDATE accounts SET balance = balance - 50  WHERE id = 2;
     UPDATE accounts SET balance = balance + 50  WHERE id = 1;
```

Both acquire row locks in opposite order → deadlock.

**Prevention: always update rows in a consistent order** (e.g., ascending by ID).

PostgreSQL detects deadlocks and rolls back one transaction with `ERROR: deadlock detected`. The application catches this and retries.

```java
@Retryable(value = DeadlockLoserDataAccessException.class, maxAttempts = 3)
@Transactional
public void transfer(long fromId, long toId, BigDecimal amount) {
    // ensure fromId < toId ordering for deterministic lock acquisition
    long first = Math.min(fromId, toId), second = Math.max(fromId, toId);
    Account a = repo.findByIdForUpdate(first);
    Account b = repo.findByIdForUpdate(second);
    ...
}
```

---

## Q114 — Optimistic vs Pessimistic Locking

**The one-line answer:** Optimistic locking detects conflicts at commit time using a version field — best for low-contention reads; pessimistic locking prevents conflicts by locking rows at read time — best for high-contention or when you cannot retry.

### Optimistic locking with JPA

```java
@Entity
public class Order {
    @Id private Long id;

    @Version
    private int version;  // automatically incremented on every update

    private OrderStatus status;
}
```

Hibernate generates: `UPDATE orders SET status = ?, version = version + 1 WHERE id = ? AND version = ?`

If the `WHERE version = ?` matches 0 rows, `OptimisticLockException` is thrown — another transaction already updated this row.

```java
@Transactional
@Retryable(value = OptimisticLockingFailureException.class, maxAttempts = 3)
public void updateStatus(Long orderId, OrderStatus newStatus) {
    Order order = repository.findById(orderId).orElseThrow();
    order.setStatus(newStatus);
    // version check happens on flush/commit
}
```

### Pessimistic locking with JPA

```java
// Acquires a row-level exclusive lock (SELECT FOR UPDATE)
Order order = repository.findById(orderId, LockModeType.PESSIMISTIC_WRITE)
                        .orElseThrow();
```

Or with Spring Data:
```java
@Lock(LockModeType.PESSIMISTIC_WRITE)
@QueryHints(@QueryHint(name = "jakarta.persistence.lock.timeout", value = "5000"))
Optional<Order> findByIdForUpdate(@Param("id") Long id);
```

### When to choose which

| | Optimistic | Pessimistic |
|---|---|---|
| Contention | Low — conflicts are rare | High — conflicts are likely |
| Read:Write ratio | Read-heavy | Write-heavy |
| Recovery | Retry on exception | Blocks until lock released |
| Performance | Higher throughput | Lower throughput under contention |
| Deadlock risk | None | Possible |

---

## Q115 — JSONB in PostgreSQL

**The one-line answer:** `JSONB` stores structured JSON as a binary decomposed format enabling efficient querying and GIN indexing — useful for dynamic attributes, event payloads, or schema-flexible data.

### Basic operations

```sql
-- Column definition
ALTER TABLE products ADD COLUMN attributes JSONB;

-- Insert
INSERT INTO products(name, attributes)
VALUES ('Widget', '{"color": "red", "weight_kg": 1.5, "tags": ["sale", "new"]}');

-- Query by JSON field
SELECT * FROM products WHERE attributes->>'color' = 'red';
SELECT * FROM products WHERE attributes @> '{"color": "red"}'; -- containment operator

-- Extract nested value
SELECT attributes->'dimensions'->>'width' FROM products;

-- GIN index for containment queries
CREATE INDEX idx_products_attrs ON products USING GIN(attributes);

-- GIN index for specific path queries
CREATE INDEX idx_products_color ON products USING GIN((attributes->'color'));
```

### `->>` vs `->`

- `->` returns JSON value (type `json/jsonb`).
- `->>` returns text representation.

Use `->>'field'` when comparing with a string. Cast when comparing with numbers: `(attributes->>'weight_kg')::numeric > 1.0`.

### When to use JSONB vs normalized tables

Use JSONB for: truly variable attributes (product specs, event metadata), external API payloads, rapid prototyping. Use normalized tables for: data with consistent structure, foreign key constraints needed, complex joins required.

---

## Q116 — Database Migrations

**The one-line answer:** Flyway and Liquibase version-control schema changes as migration scripts that run automatically on startup, ensuring every environment's schema matches exactly what the application expects.

### Flyway

```
src/main/resources/db/migration/
  V1__create_orders_table.sql
  V2__add_customer_index.sql
  V3__add_order_items_table.sql
```

Naming convention: `V{version}__{description}.sql`

```sql
-- V1__create_orders_table.sql
CREATE TABLE orders (
    id          BIGSERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    total_amount NUMERIC(12,2),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
```

```properties
spring.flyway.enabled=true
spring.flyway.locations=classpath:db/migration
spring.flyway.baseline-on-migrate=true  # for existing databases
```

### Backward compatibility

In CI/CD with rolling deployments, the new code deploys while the old code is still running. Migrations must be backward-compatible:

- **Don't** rename or drop columns in the same migration as code that uses the new name.
- **Do** add new columns with defaults, deploy code that uses both old and new, then in a later migration remove the old column.
- **Don't** add NOT NULL constraints without a default on populated tables.

### Rollback

Flyway Community doesn't support automatic rollback. Write compensating scripts manually. Liquibase supports rollback via `<rollback>` tags.

---

## Q117 — Connection Pools

**The one-line answer:** HikariCP maintains a pool of open database connections that are reused across requests, avoiding the overhead of establishing a new TCP+auth connection per query — pool exhaustion causes request queuing and latency spikes.

### How HikariCP works

1. On startup, opens `minimumIdle` connections to the DB.
2. On `getConnection()`, returns an idle connection or waits up to `connectionTimeout`.
3. On `close()`, returns the connection to the pool (not actually closed).
4. Validates connections with `connectionTestQuery` or `keepaliveTime`.
5. Closes idle connections exceeding `minimumIdle` after `idleTimeout`.
6. Closes all connections after `maxLifetime` (prevents stale connections after DB restart).

### Configuration

```properties
spring.datasource.hikari.maximum-pool-size=20
spring.datasource.hikari.minimum-idle=5
spring.datasource.hikari.connection-timeout=3000       # ms to wait for connection
spring.datasource.hikari.idle-timeout=600000           # evict idle connections after 10m
spring.datasource.hikari.max-lifetime=1800000          # recycle connections every 30m
spring.datasource.hikari.keepalive-time=60000          # send keepalive every 60s
spring.datasource.hikari.validation-timeout=1000
```

### Pool sizing

Pool size is NOT "bigger is better." The DB server has a maximum connection limit and each connection uses memory (~5–10 MB on PostgreSQL). Too many connections create more context-switching overhead at the DB. Recommended: `(core_count * 2) + effective_spindle_count` per HikariCP's formula.

### Connection leak detection

```properties
spring.datasource.hikari.leak-detection-threshold=2000  # warn if connection held > 2s
```

A connection leak (borrowing a connection and never returning it) eventually exhausts the pool. Check for unclosed `Connection` objects or long transactions.

---

## Q118 — JPA EntityManager and Entity States

**The one-line answer:** A JPA entity exists in one of four states — New (transient), Managed, Detached, or Removed — and understanding transitions between them explains when Hibernate generates SQL.

### Entity lifecycle states

```
new Order() ──────────────────────────────── NEW (transient)
    │ persist() or save()
    ▼
em.persist(entity) ──────────────────────── MANAGED
    │                                         │
    │ em.detach() / clear() / close()         │ em.remove()
    ▼                                         ▼
DETACHED ──── em.merge() ──────────────── REMOVED
                 │                            │ flush/commit
                 ▼                            ▼
              MANAGED                  deleted from DB
```

### New (Transient)

Created with `new` — not associated with any persistence context. No SQL generated. Will be garbage collected if not persisted.

### Managed

Associated with the current persistence context. Hibernate tracks it for dirty checking. Changes to managed entities are automatically persisted on flush.

```java
@Transactional
public void updateStatus(Long id, OrderStatus status) {
    Order order = repository.findById(id).orElseThrow(); // managed
    order.setStatus(status);  // no explicit save() needed!
    // Hibernate detects change on flush (at transaction commit)
}
```

### Detached

No longer tracked by the persistence context. Changes are NOT automatically persisted.

```java
Order order = repository.findById(id).orElseThrow();
// Transaction ends → entity becomes detached
order.setStatus(CANCELLED);           // change is not persisted!
repository.save(order);               // save() merges it back
```

### Removed

Scheduled for deletion. Actual DELETE happens on flush.

---

## Q119 — Dirty Checking and Flush

**The one-line answer:** Hibernate's dirty checking compares every managed entity's current state against its snapshot taken at load time; on flush it generates UPDATE statements only for changed fields — flush happens before queries and at transaction commit.

### How dirty checking works

On load, Hibernate stores a snapshot (copy) of each managed entity's field values. Before executing a query or on transaction commit, it compares current state to snapshot and issues `UPDATE` for any changed entities.

```java
@Transactional
public void processOrder(Long orderId) {
    Order order = repository.findById(orderId).orElseThrow();
    // Snapshot stored: status=PENDING, total=100.0

    order.setStatus(PROCESSING);
    // No SQL yet

    Order another = repository.findById(otherId).orElseThrow();
    // Before executing this query, Hibernate FLUSHES:
    // UPDATE orders SET status='PROCESSING' WHERE id=? → runs here

    order.setTotal(BigDecimal.valueOf(150));
    // Transaction commits → Hibernate flushes again:
    // UPDATE orders SET total=150 WHERE id=?
}
```

### Flush modes

| Mode | When flush happens |
|---|---|
| `AUTO` (default) | Before queries that might be affected by pending changes, and at commit |
| `COMMIT` | Only at transaction commit |
| `ALWAYS` | Before every query |
| `MANUAL` | Only when explicitly called `em.flush()` |

### Performance implications

Dirty checking over a large number of managed entities is expensive. If you load thousands of entities in a transaction but only update a few, consider:
- Using `em.detach(entity)` for read-only entities.
- Using `@Transactional(readOnly = true)` (skips dirty check at flush).
- Using projections/DTOs instead of full entities for read-only queries.

---

## Q120 — Lazy vs Eager Fetching

**The one-line answer:** Lazy fetching loads associations on demand (separate SQL when you access them); eager fetching loads them immediately with the entity — JPA defaults are lazy for collections and eager for `@ManyToOne`/`@OneToOne`, but you should always fetch explicitly for each use case.

### JPA defaults

| Association | Default fetch |
|---|---|
| `@OneToMany` | LAZY |
| `@ManyToMany` | LAZY |
| `@ManyToOne` | EAGER ← often a problem |
| `@OneToOne` | EAGER ← often a problem |

### LazyInitializationException

```java
Order order = repository.findById(id).orElseThrow();
// Transaction ends here (OSIV disabled)

order.getItems().size(); // BOOM — LazyInitializationException
// Hibernate can't load items — no active session
```

Fix options:
1. **Fetch join in query:** `SELECT o FROM Order o JOIN FETCH o.items WHERE o.id = :id`
2. **Entity graph:** `@EntityGraph(attributePaths = {"items"})`
3. **DTO projection:** Load only needed data
4. **Keep in transaction:** Access lazy associations before transaction ends

### Eager loading problems

`@ManyToOne(fetch = EAGER)` means loading any `Order` always loads its `Customer` — even when you don't need the customer. If `Customer` has eager associations too, it cascades. This is called the **N+1 eager fetch trap**.

**Best practice:** Declare all associations `LAZY`, then fetch eagerly per query using join fetch or entity graphs when needed.

---

## Q121 — N+1 Query Problem and Fixes

**The one-line answer:** The N+1 problem occurs when loading N entities triggers N additional queries to load a lazy association — one query to fetch the list, plus one per row to load its association — visible as hundreds of identical queries in logs.

### Classic N+1

```java
List<Order> orders = orderRepo.findAll();         // 1 query: SELECT * FROM orders
for (Order order : orders) {
    order.getCustomer().getName();                 // N queries: SELECT * FROM customers WHERE id = ?
    // Hibernate fires one query per order!
}
// Total: 1 + N queries
```

### Fix 1 — JOIN FETCH

```java
@Query("SELECT o FROM Order o JOIN FETCH o.customer WHERE o.status = :status")
List<Order> findWithCustomerByStatus(@Param("status") OrderStatus status);
// Single query: SELECT o.*, c.* FROM orders o JOIN customers c ON o.customer_id = c.id
```

**Limitation:** Cannot use `JOIN FETCH` with pagination (`Pageable`) on a collection — Hibernate loads all rows into memory and paginates in Java (HHH-000104 warning). Use entity graphs or separate queries for pagination + associations.

### Fix 2 — Entity Graph

```java
@EntityGraph(attributePaths = {"customer", "items"})
List<Order> findByStatus(OrderStatus status);
```

### Fix 3 — Batch fetching

```properties
spring.jpa.properties.hibernate.default_batch_fetch_size=30
```

Instead of N queries, Hibernate issues `SELECT * FROM customers WHERE id IN (?, ?, ... ?)` in batches of 30. Reduces N+1 to N/30 + 1 queries without changing query code.

### Fix 4 — DTO projection

```java
@Query("SELECT new com.example.OrderSummary(o.id, c.name, o.total) " +
       "FROM Order o JOIN o.customer c WHERE o.status = :status")
List<OrderSummary> findSummaries(@Param("status") OrderStatus status);
```

Single query, no entity management overhead, no lazy loading risk.

---

## Q122 — JPQL, Criteria API, and Native Queries

**The one-line answer:** JPQL is the standard object-oriented query language for JPA; Criteria API builds type-safe queries programmatically; native SQL escapes to the database's dialect when JPA cannot express the query.

### JPQL

Object-oriented — queries refer to entity names and field names, not table/column names. Hibernate translates to SQL.

```java
@Query("SELECT o FROM Order o WHERE o.customerId = :cid AND o.total > :minTotal ORDER BY o.createdAt DESC")
List<Order> findByCustomerAndMinTotal(@Param("cid") String cid, @Param("minTotal") BigDecimal min);
```

### Criteria API — dynamic queries

```java
public List<Order> search(OrderSearchRequest req) {
    CriteriaBuilder cb = em.getCriteriaBuilder();
    CriteriaQuery<Order> cq = cb.createQuery(Order.class);
    Root<Order> root = cq.from(Order.class);

    List<Predicate> predicates = new ArrayList<>();
    if (req.customerId() != null)
        predicates.add(cb.equal(root.get("customerId"), req.customerId()));
    if (req.status() != null)
        predicates.add(cb.equal(root.get("status"), req.status()));
    if (req.minTotal() != null)
        predicates.add(cb.greaterThanOrEqualTo(root.get("total"), req.minTotal()));

    cq.where(predicates.toArray(new Predicate[0]));
    cq.orderBy(cb.desc(root.get("createdAt")));

    return em.createQuery(cq).getResultList();
}
```

**Spring Data Specifications** provide a cleaner API over Criteria:

```java
interface OrderRepository extends JpaRepository<Order, Long>, JpaSpecificationExecutor<Order> {}

Specification<Order> spec = (root, query, cb) -> cb.equal(root.get("status"), status);
List<Order> orders = orderRepo.findAll(spec);
```

### Native queries — when to use

```java
@Query(value = "SELECT * FROM orders WHERE tsv_search @@ to_tsquery(:term)", nativeQuery = true)
List<Order> fullTextSearch(@Param("term") String term);
```

Use native queries for: database-specific features (full-text, JSONB operators, window functions, `RETURNING`), bulk operations, complex reporting queries where JPQL can't express the logic.

Caution: native queries return `Object[]` or require `@SqlResultSetMapping` / projections. Parameterize all values — never concatenate into the query string.

---

## Q123 — DTO Projections

**The one-line answer:** DTO projections load only required fields from the database, avoiding full entity instantiation and lazy-load risks — use interface projections for simple cases and constructor expressions or record-based projections for complex ones.

### Interface projection

```java
public interface OrderSummary {
    Long getId();
    String getCustomerId();
    BigDecimal getTotal();
    @Value("#{target.total.multiply(new java.math.BigDecimal('1.1'))}")
    BigDecimal getTotalWithTax();
}

List<OrderSummary> findByStatus(OrderStatus status);
// Spring Data generates: SELECT id, customer_id, total FROM orders WHERE status = ?
```

### Class (DTO) projection with constructor expression

```java
public record OrderSummaryDto(Long id, String customerId, BigDecimal total) {}

@Query("SELECT new com.example.OrderSummaryDto(o.id, o.customerId, o.total) FROM Order o WHERE o.status = :s")
List<OrderSummaryDto> findSummaries(@Param("s") OrderStatus s);
```

### Benefits of projections

- Smaller result sets (fewer columns fetched from DB).
- No first-level cache overhead — results not managed entities.
- No lazy loading risk — what you select is what you get.
- Enables selecting from joins directly.

### When to use full entity vs projection

Use full entity when: you need to update/delete the entity, you need all fields, you want Hibernate dirty checking. Use projection when: read-only API responses, dashboard data, reporting, pagination views.

---

## Q124 — Associations and mappedBy

**The one-line answer:** In a bidirectional JPA association, the `mappedBy` side is the inverse (non-owning) side — Hibernate only looks at the owning side when writing the foreign key, so you must keep both sides in sync in Java.

### Owning side vs inverse side

```java
@Entity
public class Order {
    @Id private Long id;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderItem> items = new ArrayList<>(); // INVERSE side (mappedBy)

    // Helper methods to maintain both sides
    public void addItem(OrderItem item) {
        items.add(item);
        item.setOrder(this); // sync the owning side
    }
    public void removeItem(OrderItem item) {
        items.remove(item);
        item.setOrder(null);
    }
}

@Entity
public class OrderItem {
    @Id private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "order_id")
    private Order order;  // OWNING side — has the FK column
}
```

`mappedBy = "order"` tells Hibernate: "Don't look at the `items` list for FK writes — look at `OrderItem.order`." If you only add to the `items` list without setting `item.setOrder(this)`, Hibernate won't insert the FK.

### Common mistakes

1. Setting only one side of a bidirectional association.
2. Comparing entities in `equals()`/`hashCode()` based on `id` when using `HashSet` with managed entities (id may be null before persist).
3. Using bidirectional associations without lazy fetching on `@ManyToOne` — causes accidental eager loads.

---

## Q125 — Cascade and orphanRemoval

**The one-line answer:** Cascade propagates lifecycle operations (persist, merge, remove) from parent to child entities; `orphanRemoval = true` automatically deletes a child entity when it's removed from the parent's collection.

### Cascade types

```java
@OneToMany(cascade = CascadeType.ALL, orphanRemoval = true)
private List<OrderItem> items;
```

| CascadeType | Effect |
|---|---|
| `PERSIST` | Saving parent also saves new children |
| `MERGE` | Merging parent also merges detached children |
| `REMOVE` | Deleting parent also deletes children |
| `REFRESH` | Refreshing parent also refreshes children |
| `DETACH` | Detaching parent also detaches children |
| `ALL` | All of the above |

### orphanRemoval vs CascadeType.REMOVE

```java
order.getItems().remove(item);  // remove from collection
// With orphanRemoval=true: Hibernate issues DELETE for item automatically
// Without orphanRemoval (even with REMOVE cascade): item remains in DB!
```

`CascadeType.REMOVE` deletes children when the parent is deleted. `orphanRemoval` additionally deletes children when they're unlinked from the parent collection.

### Dangers

- **Accidental delete:** Removing from a collection with `orphanRemoval` deletes the entity even if another entity references it. Only use on truly owned, private collections.
- **CascadeType.ALL on @ManyToMany:** Almost never correct — you don't own the other side. Use `PERSIST` and `MERGE` only.
- **CascadeType.REMOVE across service boundaries:** Deleting one aggregate accidentally deletes unrelated data.

---

## Q126 — Pagination in JPA and Keyset Pagination

**The one-line answer:** Offset pagination (`LIMIT`/`OFFSET`) is simple but degrades at high page numbers; keyset pagination uses the last seen row's value as a cursor, providing O(1) page navigation regardless of depth.

### Offset pagination

```java
Page<Order> page = orderRepo.findByStatus(ACTIVE, PageRequest.of(pageNumber, 20, Sort.by("createdAt").desc()));
```

Generated SQL:
```sql
SELECT * FROM orders WHERE status = 'ACTIVE' ORDER BY created_at DESC LIMIT 20 OFFSET 200;
```

**Performance issue at high offsets:** The DB must scan and skip 200 rows to return rows 201-220. At offset 10,000, it scans 10,000 rows. This is O(offset).

### Keyset (cursor) pagination

```java
@Query("SELECT o FROM Order o WHERE o.status = :s AND " +
       "(o.createdAt < :lastCreatedAt OR (o.createdAt = :lastCreatedAt AND o.id < :lastId)) " +
       "ORDER BY o.createdAt DESC, o.id DESC")
List<Order> findNextPage(@Param("s") OrderStatus s,
                         @Param("lastCreatedAt") Instant lastCreatedAt,
                         @Param("lastId") Long lastId,
                         Pageable pageable);
```

The client receives the cursor (`lastCreatedAt`, `lastId`) from the last item on the current page and sends it back for the next page. The DB uses the index to seek directly to the cursor position — always O(log n) regardless of depth.

**Limitations of keyset:** Cannot jump to arbitrary pages; cursor must be stable (sort key must be unique or tie-broken by unique column); doesn't work with dynamic sorting.

---

## Q127 — Batch Inserts and Updates

**The one-line answer:** Hibernate batching groups multiple INSERT/UPDATE/DELETE statements into a single JDBC `executeBatch()` call, dramatically reducing round-trips for bulk operations.

### Enabling JDBC batching

```properties
spring.jpa.properties.hibernate.jdbc.batch_size=30
spring.jpa.properties.hibernate.order_inserts=true  # group inserts by table
spring.jpa.properties.hibernate.order_updates=true
spring.jpa.properties.hibernate.jdbc.batch_versioned_data=true
```

### Identity generation kills batching

Hibernate must fetch the generated ID after each INSERT to set it on the entity (to map it as managed). This requires a separate DB round-trip per INSERT, breaking batching.

**Fix:** Use `SEQUENCE` instead of `IDENTITY`/`AUTO_INCREMENT`:

```java
@GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "order_seq")
@SequenceGenerator(name = "order_seq", sequenceName = "order_seq", allocationSize = 50)
private Long id;
```

`allocationSize = 50` means Hibernate fetches sequence values in batches of 50, reducing sequence round-trips.

### Bulk insert with JPQL

```java
// For very large datasets — bypasses entity lifecycle
@Modifying
@Transactional
@Query("UPDATE Order o SET o.status = 'EXPIRED' WHERE o.createdAt < :cutoff AND o.status = 'PENDING'")
int expireOldOrders(@Param("cutoff") Instant cutoff);
```

Clears first-level cache if `@Modifying(clearAutomatically = true)`.

---

## Q128 — Hibernate Caching

**The one-line answer:** Hibernate has two cache levels: first-level (per session/transaction, always on) and second-level (cross-session, optional, requires configuration) — the second-level cache reduces DB reads for stable reference data but adds complexity and stale-data risk.

### First-level cache (persistence context)

- One per `EntityManager` / `Session` — scoped to the current transaction.
- `em.find(Order.class, id)` called twice in the same transaction hits the DB only once.
- Cleared on `em.clear()` or at transaction end.
- Prevents duplicate entities in the same session.

### Second-level cache

Shared across transactions. Stores entity data by ID. Backed by Ehcache, Caffeine, Hazelcast, etc.

```java
@Entity
@Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class Country {  // rarely updated reference data — good candidate
    @Id private String code;
    private String name;
}
```

```properties
spring.jpa.properties.hibernate.cache.use_second_level_cache=true
spring.jpa.properties.hibernate.cache.region.factory_class=org.hibernate.cache.jcache.JCacheCacheRegionFactory
```

### Query cache

Caches the list of entity IDs returned by a JPQL query. Only useful when the same query is repeated frequently and the result set rarely changes.

```java
@QueryHints(@QueryHint(name = "org.hibernate.cacheable", value = "true"))
List<Country> findAll();
```

### Stale data risk

Second-level cache is invalidated on writes to that entity — but only in the local JVM. In a clustered deployment with multiple JVMs, cache entries can become stale unless using a distributed cache (Hazelcast, Redis). This is why second-level cache is suitable for read-mostly reference data (countries, currencies, config) but risky for frequently updated business data.

---

## Q129 — OSIV and Transaction Boundaries

**The one-line answer:** Open Session In View (OSIV) keeps the Hibernate session (and a DB connection) open for the entire HTTP request/response cycle, allowing lazy loading in the view/serialization layer — but it ties up DB connections unnecessarily and is disabled by default in Spring Boot for a reason.

### What OSIV does

```
Request arrives
  └─ Hibernate session opened (DB connection taken from pool)
      └─ @Transactional method runs (reads entities lazily)
      └─ Transaction commits — but session stays open
          └─ Jackson serializes response — lazy collections fetched here (still works!)
  └─ Session closed, connection returned to pool
```

With OSIV enabled (`spring.jpa.open-in-view=true` — the old default), lazy loading works outside `@Transactional` because the session is still open.

### Why OSIV is problematic

1. Holds a DB connection for the full HTTP request duration — including time waiting for JSON serialization, slow clients, etc.
2. Encourages lazy loading in the serialization/presentation layer — hidden N+1 queries.
3. Under load, pool exhaustion happens faster.
4. Promotes entangled layers — presentation layer accidentally drives database access.

### Best practice

```properties
spring.jpa.open-in-view=false  # disable OSIV (default since Spring Boot 2.0 warning)
```

Load everything you need within `@Transactional` using fetch joins or DTO projections. `LazyInitializationException` outside the transaction is your indicator that your query doesn't fetch what it needs.

---

## Q130 — JPA Locking and Isolation

**The one-line answer:** JPA exposes optimistic and pessimistic lock modes that map to database constructs; choosing the right mode prevents lost updates and dirty reads for concurrent entity modifications.

### Lock modes

```java
// Optimistic — version check at commit
em.lock(order, LockModeType.OPTIMISTIC);              // read lock, checks version at commit
em.lock(order, LockModeType.OPTIMISTIC_FORCE_INCREMENT); // also increments version on read

// Pessimistic — DB-level lock
em.lock(order, LockModeType.PESSIMISTIC_READ);        // SELECT FOR SHARE
em.lock(order, LockModeType.PESSIMISTIC_WRITE);       // SELECT FOR UPDATE
em.lock(order, LockModeType.PESSIMISTIC_FORCE_INCREMENT); // FOR UPDATE + version increment
```

### Timeout configuration

```java
Map<String, Object> hints = Map.of("jakarta.persistence.lock.timeout", 5000); // 5s
Order order = em.find(Order.class, id, LockModeType.PESSIMISTIC_WRITE, hints);
```

`0` means NOWAIT (fail immediately). `-2` means SKIP LOCKED.

### Combining with @Transactional

Lock modes only make sense inside a transaction. For `PESSIMISTIC_WRITE`, the lock is held until the transaction commits or rolls back. Keep the transaction as short as possible.

---

## Q131 — Normalization vs Denormalization

**The one-line answer:** Normalization removes data redundancy and update anomalies; denormalization selectively reintroduces redundancy to reduce join complexity for read performance — choose based on whether write integrity or read throughput is the priority.

### Normal forms

- **1NF:** No repeating groups, atomic column values.
- **2NF:** 1NF + no partial dependency on composite key.
- **3NF:** 2NF + no transitive dependencies (non-key columns only depend on the PK, not on other non-key columns).
- **BCNF:** Stricter 3NF — every determinant is a candidate key.

### Normalization benefits

- No update anomalies: changing a customer's email requires updating one row.
- No insert anomalies: can add a customer without needing an order.
- No delete anomalies: deleting the last order doesn't delete the customer.
- Smaller row sizes — more rows fit in one DB page.

### When to denormalize

For read-heavy reporting or analytical queries, excessive joins are slow. Denormalize by:

- **Storing derived values:** `order.item_count` cached on the order row.
- **Materialized views:** Pre-computed join results, refreshed periodically.
- **Read models/projections:** CQRS-style separate table optimized for reads.
- **Reporting tables:** Flat denormalized tables populated by ETL.

Always enforce data integrity through the canonical normalized table, and derive/sync denormalized views from it.

---

## Q132 — Database Constraints vs Application Validation

**The one-line answer:** Database constraints are the last line of defense and must exist regardless of application validation; application validation provides user-friendly error messages; both layers together prevent data corruption.

### Defense in depth

```
HTTP Request
  │
  ▼ Bean Validation (@Valid, @NotNull, @Size)
Application layer validation
  │
  ▼ Business rule checks in service
Domain invariants
  │
  ▼ SQL INSERT / UPDATE
Database constraints (NOT NULL, UNIQUE, FK, CHECK)
```

### Why DB constraints are non-negotiable

- Bugs in application code can bypass application validation.
- Direct DB access (migration scripts, admin tools) bypasses the application entirely.
- Race conditions: two requests pass application validation simultaneously and both try to insert a duplicate — a DB UNIQUE constraint will catch one of them.

```sql
ALTER TABLE orders ADD CONSTRAINT uq_order_external_id UNIQUE (external_id, customer_id);
ALTER TABLE order_items ADD CONSTRAINT chk_quantity CHECK (quantity > 0);
ALTER TABLE orders ADD CONSTRAINT fk_orders_customers FOREIGN KEY (customer_id) REFERENCES customers(id);
```

### Mapping DB constraint violations

```java
@ExceptionHandler(DataIntegrityViolationException.class)
public ResponseEntity<ProblemDetail> handleConstraint(DataIntegrityViolationException ex) {
    String msg = ex.getMostSpecificCause().getMessage();
    if (msg.contains("uq_order_external_id")) {
        return ResponseEntity.status(409).body(
            ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, "Order already exists"));
    }
    throw ex; // re-throw unexpected constraint violations
}
```

---

## Q133 — Processing Large Datasets

**The one-line answer:** Loading large result sets all at once into heap causes OOM errors; stream them using JDBC cursors, Spring Data scrolling, or chunk-based batch processing to maintain constant memory usage.

### Spring Data scrolling (Spring Boot 3+)

```java
Window<Order> window = repository.findBy(
    Specification.where(null),
    q -> q.limit(500).scroll(ScrollPosition.offset())
);
while (window.hasNext()) {
    process(window.getContent());
    window = repository.findBy(..., q -> q.limit(500).scroll(window.positionAt(window.size() - 1)));
}
```

### JPQL stream with cursor

```java
@Query("SELECT o FROM Order o WHERE o.status = 'PENDING'")
@QueryHints(value = @QueryHint(name = HINT_FETCH_SIZE, value = "100"))
Stream<Order> streamPendingOrders();

// Usage
@Transactional(readOnly = true)
public void processPendingOrders() {
    try (Stream<Order> orders = repo.streamPendingOrders()) {
        orders.forEach(order -> {
            processOrder(order);
            em.detach(order); // prevent persistence context from growing
        });
    }
}
```

### Spring Batch for bulk jobs

For ETL and bulk processing, Spring Batch provides chunk-oriented processing with restartability, parallel steps, and retry/skip:

```java
@Bean
public Step processOrders(StepBuilderFactory steps, OrderReader reader,
                           OrderProcessor processor, OrderWriter writer) {
    return steps.get("processOrders")
        .<Order, ProcessedOrder>chunk(100)  // read 100, process 100, write 100, repeat
        .reader(reader)
        .processor(processor)
        .writer(writer)
        .build();
}
```

---

## Q134 — Database Deadlock Troubleshooting

**The one-line answer:** Diagnose deadlocks by reading PostgreSQL's deadlock log to find the involved transactions and locked rows, then redesign lock acquisition order or reduce transaction scope to eliminate the cycle.

### PostgreSQL deadlock log

```
ERROR: deadlock detected
DETAIL: Process 12345 waits for ShareLock on transaction 789; blocked by process 67890.
        Process 67890 waits for ShareLock on transaction 456; blocked by process 12345.
HINT:   See server log for query details.
CONTEXT: while updating tuple (0,42) in relation "orders"
```

### Diagnosis steps

1. Enable deadlock logging: `log_lock_waits = on` and `deadlock_timeout = 1s` in `postgresql.conf`.
2. Identify which transactions are involved and which rows they lock.
3. Find what queries each transaction runs and in what order.
4. Identify the cycle: Tx1 holds Row A, wants Row B; Tx2 holds Row B, wants Row A.

### Resolution strategies

1. **Consistent lock ordering:** Always process rows in ascending ID order.
2. **Reduce transaction scope:** Acquire locks as late as possible, release as early as possible.
3. **Use advisory locks for application-level mutual exclusion.**
4. **Retry on deadlock:** Spring's `@Retryable(DeadlockLoserDataAccessException.class)`.
5. **SELECT FOR UPDATE SKIP LOCKED:** For queue-style processing, skip rows locked by another transaction.

---

## Q135 — SQL Injection Prevention

**The one-line answer:** Always use parameterized queries (prepared statements) — never concatenate user input into SQL strings; parameterization separates code from data, making injection structurally impossible.

### The attack

```java
// VULNERABLE
String sql = "SELECT * FROM users WHERE username = '" + username + "'";
// If username = "'; DROP TABLE users; --"
// Executes: SELECT * FROM users WHERE username = ''; DROP TABLE users; --'
```

### Parameterized queries — always use these

```java
// JDBC
PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE username = ?");
ps.setString(1, username);

// Spring JDBC
jdbcTemplate.queryForObject("SELECT * FROM users WHERE username = ?", User.class, username);

// JPA
@Query("SELECT u FROM User u WHERE u.username = :username")
Optional<User> findByUsername(@Param("username") String username);

// Spring Data method derivation (always parameterized)
Optional<User> findByUsername(String username);
```

### Dynamic SQL — allowlists for column names

User-controlled column names or sort orders cannot be safely parameterized (you can only parameterize values, not identifiers). Use an allowlist:

```java
private static final Set<String> ALLOWED_SORT_COLUMNS = Set.of("name", "createdAt", "total");

public List<Order> findSorted(String sortBy) {
    if (!ALLOWED_SORT_COLUMNS.contains(sortBy)) {
        throw new IllegalArgumentException("Invalid sort column: " + sortBy);
    }
    return jdbcTemplate.query("SELECT * FROM orders ORDER BY " + sortBy, ...);
}
```

### ORM doesn't make you immune

Native queries with string concatenation are vulnerable even in Hibernate:

```java
// VULNERABLE in JPA native query
@Query(value = "SELECT * FROM orders WHERE status = '" + status + "'", nativeQuery = true)
// Fix: use :status parameter binding
```

JPQL and Criteria API are safe because they always use parameterization internally.


<a id="chapter-6"></a>

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


<a id="chapter-7"></a>

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


<a id="chapter-8"></a>

# Chapter 8: Testing, Debugging, and Coding Exercises

---

## Q173 — Testing Pyramid for Backend

**The one-line answer:** The testing pyramid guides investment: many fast isolated unit tests at the base, fewer integration tests in the middle, and a small number of slow end-to-end tests at the top — the ratio reflects cost, speed, and specificity.

### The pyramid

```
        /--E2E Tests--\           (few — slow, fragile, expensive)
      /--Integration Tests--\     (moderate — database, Spring context)
    /------Unit Tests--------\    (many — fast, isolated, cheap)
```

### Unit tests

- Test a single class in isolation.
- Dependencies replaced by mocks/stubs.
- Milliseconds to run.
- Cover all business logic branches, edge cases, and error paths.

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {
    @Mock OrderRepository repository;
    @Mock PaymentGateway gateway;
    @InjectMocks OrderService service;

    @Test
    void placeOrder_shouldCreateOrder_whenValidRequest() {
        // Arrange
        when(gateway.charge(any())).thenReturn(PaymentResult.success("tx-1"));
        // Act
        Order result = service.placeOrder(validRequest());
        // Assert
        assertThat(result.getStatus()).isEqualTo(OrderStatus.CONFIRMED);
        verify(repository).save(any(Order.class));
    }
}
```

### Integration tests

- Test components working together.
- May hit a real database (H2, Testcontainers PostgreSQL), real Spring context.
- Seconds to run.
- Cover wiring, JPA mappings, transaction boundaries.

### End-to-end tests

- Test the full application via HTTP.
- May use `@SpringBootTest(webEnvironment = RANDOM_PORT)` or an external environment.
- Tens of seconds to minutes.
- Cover critical user journeys only — not every edge case.

### Coverage guidance

Aim for high unit test coverage (80%+) of service and domain logic. Integration tests cover repository queries, Spring wiring, and security configuration. E2E tests cover 5–10 critical happy paths.

---

## Q174 — JUnit 5 Fundamentals

**The one-line answer:** JUnit 5 (JUnit Platform + JUnit Jupiter + JUnit Vintage) provides annotations for test lifecycle, assertions, parameterized tests, and extension points — know the lifecycle order and assertion API cold.

### Test lifecycle

```java
@TestInstance(TestInstance.Lifecycle.PER_CLASS) // default is PER_METHOD — new instance per test
class OrderServiceTest {

    @BeforeAll  static void setupOnce() { /* runs once before all tests */ }
    @AfterAll   static void teardownOnce() { }
    @BeforeEach void setup() { /* runs before each test method */ }
    @AfterEach  void teardown() { }

    @Test
    @DisplayName("Order should be rejected when customer is suspended")
    void orderRejectedForSuspendedCustomer() { ... }

    @Disabled("Flaky — fix in JIRA-123")
    @Test
    void temporarilyDisabledTest() { ... }
}
```

### Assertions (AssertJ — prefer over JUnit assertions)

```java
// JUnit 5 built-in
assertEquals(OrderStatus.PENDING, order.getStatus());
assertThrows(OrderNotFoundException.class, () -> service.findById("bad-id"));
assertAll(
    () -> assertEquals("C123", order.getCustomerId()),
    () -> assertNotNull(order.getCreatedAt())
);

// AssertJ — more fluent and readable
assertThat(order.getStatus()).isEqualTo(OrderStatus.PENDING);
assertThat(order.getItems()).hasSize(2).extracting(OrderItem::getProductId)
                             .containsExactlyInAnyOrder("P1", "P2");
assertThatThrownBy(() -> service.findById("bad-id"))
    .isInstanceOf(OrderNotFoundException.class)
    .hasMessage("Order bad-id not found");
```

### Parameterized tests

```java
@ParameterizedTest
@CsvSource({
    "PENDING,   true",
    "CONFIRMED, true",
    "DELIVERED, false",
    "CANCELLED, false"
})
void canBeCancelled_shouldMatchStatus(OrderStatus status, boolean expected) {
    Order order = Order.withStatus(status);
    assertThat(order.canBeCancelled()).isEqualTo(expected);
}

@ParameterizedTest
@MethodSource("invalidRequests")
void create_shouldRejectInvalidRequest(CreateOrderRequest request, String expectedError) { ... }

static Stream<Arguments> invalidRequests() {
    return Stream.of(
        Arguments.of(requestWithNullCustomer(), "customerId must not be blank"),
        Arguments.of(requestWithEmptyItems(), "items must not be empty")
    );
}
```

---

## Q175 — Mockito Fundamentals

**The one-line answer:** Mockito creates test doubles — mocks (track interactions), stubs (return predefined values), and spies (partial real objects) — and `verify()` asserts that expected method calls were made.

### Mock vs Stub vs Spy

| Type | Behavior | Use for |
|---|---|---|
| Mock | All methods return defaults (null, 0, false) | Verifying interactions |
| Stub | Configured to return specific values | Providing test data |
| Spy | Real object — override specific methods | Partial mocking of real classes |

In Mockito, mocks and stubs are the same object — you configure (stub) its behavior and then verify (mock) its interactions.

### Stubbing

```java
// Return a value
when(repository.findById("123")).thenReturn(Optional.of(testOrder));

// Throw an exception
when(gateway.charge(any())).thenThrow(new PaymentException("declined"));

// Return different values on successive calls
when(service.nextId()).thenReturn("id1", "id2", "id3");

// Answer dynamically
when(repository.save(any(Order.class))).thenAnswer(invocation -> {
    Order o = invocation.getArgument(0);
    o.setId(System.nanoTime());
    return o;
});
```

### Argument matchers

```java
when(repo.findByCustomerId(anyString())).thenReturn(List.of());
when(repo.findByCustomerId(eq("C123"))).thenReturn(List.of(order1));

// ArgumentCaptor — capture the actual argument for assertions
ArgumentCaptor<Order> captor = ArgumentCaptor.forClass(Order.class);
verify(repository).save(captor.capture());
assertThat(captor.getValue().getStatus()).isEqualTo(OrderStatus.PENDING);
```

### Verification

```java
// Called exactly once
verify(emailService).sendConfirmation(any(Order.class));

// Called N times
verify(retryService, times(3)).attempt(any());

// Never called
verify(fraudService, never()).flag(any());

// At least / at most
verify(logger, atLeast(1)).warn(anyString());
verify(cache, atMost(2)).get(anyString());
```

### Spy

```java
List<String> realList = new ArrayList<>();
List<String> spy = Mockito.spy(realList);

spy.add("hello");                   // calls real add()
verify(spy).add("hello");           // interaction tracked
when(spy.size()).thenReturn(100);   // override one method
```

---

## Q176 — Mockito Pitfalls

**The one-line answer:** Mockito pitfalls include over-mocking (mocking value objects and simple collaborators), verifying implementation details (testing how, not what), and unexpected interactions with `final` classes, `static` methods, and `equals`/`hashCode`.

### Over-mocking — the most common mistake

```java
// BAD — mocking a simple value object
Money price = mock(Money.class);
when(price.getAmount()).thenReturn(BigDecimal.TEN);

// GOOD — use the real object
Money price = Money.of(BigDecimal.TEN, "EUR");
```

Mock only external collaborators and services with side effects (DB, HTTP, messaging). Use real objects for value types, domain objects, and simple utilities.

### Testing implementation, not behavior

```java
// BAD — verifies internal implementation detail
verify(repository, times(1)).findByCustomerId(customerId);
verify(cache, times(1)).get(customerId);
// If you refactor to only use the cache, the test breaks even though behavior is unchanged

// GOOD — verify the observable outcome
assertThat(result.getCustomerName()).isEqualTo("Alice");
// How we fetched the name is an implementation detail
```

### Strict stubs (MockitoExtension default)

`@ExtendWith(MockitoExtension.class)` enables strict stubbing by default: unused stubs cause a `UnnecessaryStubbingException`, preventing dead test code.

```java
// This stub is unused — test fails with UnnecessaryStubbingException in strict mode
when(repository.findAll()).thenReturn(List.of()); // never called in this test
```

### Final classes and static methods

Mockito cannot mock `final` classes or `static` methods by default. Use `mockito-inline` (bundled since Mockito 4+) or MockK (Kotlin):

```java
// Requires mockito-inline
MockedStatic<Files> files = Mockito.mockStatic(Files.class);
files.when(() -> Files.readString(any())).thenReturn("content");
```

Use static mocking sparingly — it's a signal that the code under test has a hidden static dependency that should ideally be injected.

### Deep stubs — use with extreme caution

```java
// Enables: when(order.getCustomer().getAddress().getCity()).thenReturn("London")
Order order = mock(Order.class, RETURNS_DEEP_STUBS);
```

Deep stubs hide design problems (Law of Demeter violations). When you find yourself needing them, refactor the production code.

---

## Q177 — Spring Test Slices

**The one-line answer:** Spring Boot test slices load only a subset of the application context relevant to a specific layer — `@WebMvcTest` for controllers, `@DataJpaTest` for repositories — making tests faster and more focused than loading the full context with `@SpringBootTest`.

### @WebMvcTest — controller layer only

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired MockMvc mockMvc;
    @MockBean OrderService service;     // @Service beans not loaded — must mock
    @MockBean SecurityConfig security;

    @Test
    void getOrder_shouldReturn200_whenOrderExists() throws Exception {
        when(service.findById("123")).thenReturn(testOrder());

        mockMvc.perform(get("/orders/123")
                .header("Authorization", "Bearer " + validToken))
               .andExpect(status().isOk())
               .andExpect(jsonPath("$.id").value("123"))
               .andExpect(jsonPath("$.status").value("PENDING"));
    }

    @Test
    void createOrder_shouldReturn400_whenRequestInvalid() throws Exception {
        mockMvc.perform(post("/orders")
                .contentType(APPLICATION_JSON)
                .content("{\"customerId\": \"\"}"))
               .andExpect(status().isBadRequest())
               .andExpect(jsonPath("$.status").value(400));
    }
}
```

Loads: `@Controller`, `@ControllerAdvice`, filters, `MockMvc`, Jackson config. Does NOT load: `@Service`, `@Repository`.

### @DataJpaTest — JPA layer only

```java
@DataJpaTest  // uses in-memory H2 by default; replaces with Testcontainers for realism
@AutoConfigureTestDatabase(replace = NONE)  // use real DB when combined with Testcontainers
class OrderRepositoryTest {

    @Autowired OrderRepository repository;
    @Autowired TestEntityManager em;

    @Test
    void findByCustomerId_shouldReturnOrders_whenCustomerHasOrders() {
        em.persistAndFlush(orderFor("C123"));
        em.persistAndFlush(orderFor("C123"));
        em.persistAndFlush(orderFor("C456"));

        List<Order> orders = repository.findByCustomerId("C123");
        assertThat(orders).hasSize(2);
    }
}
```

Loads: JPA repositories, `@Entity` classes, data source (H2), transaction management. Does NOT load: controllers, services, full Spring context.

### @SpringBootTest — full context

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
class OrderIntegrationTest {

    @LocalServerPort int port;
    @Autowired TestRestTemplate rest;

    @Test
    void fullOrderJourney_shouldCreateAndConfirmOrder() {
        ResponseEntity<OrderResponse> create = rest.postForEntity(
            "/orders", validCreateRequest(), OrderResponse.class);
        assertThat(create.getStatusCode()).isEqualTo(HttpStatus.CREATED);
    }
}
```

Use for end-to-end integration tests. Load time is high — keep these tests few.

### Other slices

| Annotation | What it loads |
|---|---|
| `@WebFluxTest` | WebFlux controllers only |
| `@DataMongoTest` | MongoDB repositories only |
| `@DataRedisTest` | Redis repositories only |
| `@JsonTest` | JSON serialization/deserialization only |
| `@RestClientTest` | RestTemplate / RestClient with `MockRestServiceServer` |

---

## Q178 — Repository Tests and Testcontainers

**The one-line answer:** H2 in-memory databases are fast but differ from production PostgreSQL in SQL syntax, type behavior, and constraint handling — Testcontainers spins up a real PostgreSQL Docker container for realistic, reliable repository tests.

### H2 limitations

- Different SQL dialect — some PostgreSQL-specific SQL won't work.
- Missing features: `JSONB`, `ARRAY`, window functions, `RETURNING`, full-text.
- Different null handling and type coercion.
- Doesn't expose index behavior issues.

### Testcontainers setup

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = NONE)  // don't replace with H2
@Testcontainers
class OrderRepositoryTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test");

    @DynamicPropertySource
    static void postgresProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired OrderRepository repository;

    @Test
    void findByStatusOrderedByCreatedAt_shouldReturnInCorrectOrder() {
        // Given: orders inserted in different order
        repository.saveAll(List.of(orderWithStatus(PENDING, minus(5, DAYS)),
                                   orderWithStatus(PENDING, minus(1, DAYS)),
                                   orderWithStatus(PENDING, minus(3, DAYS))));

        // When
        List<Order> result = repository.findByStatusOrderByCreatedAtAsc(PENDING);

        // Then
        assertThat(result).extracting(o -> o.getCreatedAt())
                          .isSortedAccordingTo(Comparator.naturalOrder());
    }
}
```

### Container reuse for faster tests

Declare the container as `static` so it's shared across test methods. Use `@TestContainers` with `reuse = true` in `testcontainers.properties` to reuse containers across test classes in the same JVM run.

---

## Q179 — @Transactional in Tests

**The one-line answer:** `@Transactional` on test methods rolls back the transaction after each test — keeping the database clean without explicit teardown — but can hide real issues around flush behavior, constraints, and commit semantics.

### How it works

```java
@DataJpaTest  // @Transactional is meta-annotated here
class OrderRepositoryTest {

    @Test
    void save_shouldPersistOrder() {
        Order order = repository.save(new Order("C123"));
        assertThat(order.getId()).isNotNull();
        // Test ends → transaction ROLLS BACK → order is not in DB
        // Next test starts with a clean slate
    }
}
```

The test transaction wraps the entire test method. Any `@Transactional` methods called in the service/repository join this test transaction (default `REQUIRED` propagation).

### When test @Transactional hides bugs

**Flush timing:** Hibernate defers SQL until flush. Inside a transaction, you can save an entity and `findById` it without the SQL having been executed. In production, a read-only query on a separate connection would hit the database:

```java
@Test
@Transactional
void save_thenFind() {
    repository.save(order);
    // Flush hasn't happened yet — but Hibernate finds from its first-level cache
    Optional<Order> found = repository.findById(order.getId());
    assertThat(found).isPresent(); // passes in test — but passes for wrong reason
}
```

Fix: call `entityManager.flush()` and `entityManager.clear()` between save and find to force a real DB round-trip.

**Constraint violations:** Database constraints are checked at commit time. A test that rolls back never commits, so constraint violations are never triggered. Use `@Commit` or flush explicitly to test constraints.

**REQUIRES_NEW propagation:** A service method using `REQUIRES_NEW` creates a NEW transaction that is NOT part of the test transaction — its changes COMMIT and won't be rolled back. Use `@Sql` cleanup or `@BeforeEach`/`@AfterEach` to clean up.

---

## Q180 — Controller Testing

**The one-line answer:** Test controllers with `MockMvc` (synchronous, in-process) for unit-level tests or `@SpringBootTest` + `TestRestTemplate`/`WebTestClient` for integration-level tests — always test request validation, serialization, status codes, and error responses.

### MockMvc patterns

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired MockMvc mockMvc;
    @Autowired ObjectMapper objectMapper;
    @MockBean OrderService service;

    @Test
    void createOrder_shouldReturn201_withLocationHeader() throws Exception {
        Order created = testOrder("ORD-1");
        when(service.create(any())).thenReturn(created);

        mockMvc.perform(post("/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(validCreateRequest())))
               .andExpect(status().isCreated())
               .andExpect(header().string("Location", containsString("/orders/ORD-1")))
               .andExpect(jsonPath("$.id").value("ORD-1"))
               .andExpect(jsonPath("$.status").value("PENDING"))
               .andDo(print()); // prints request/response to console for debugging
    }

    @Test
    void createOrder_shouldReturn400_forMissingCustomerId() throws Exception {
        mockMvc.perform(post("/orders")
                .contentType(APPLICATION_JSON)
                .content("{\"items\": [{\"productId\": \"P1\", \"quantity\": 1}]}"))
               .andExpect(status().isBadRequest())
               .andExpect(jsonPath("$.status").value(400))
               .andExpect(jsonPath("$.errors[0].field").value("customerId"));
    }

    @Test
    @WithMockUser(roles = "USER")
    void getOrder_shouldReturn403_whenNotOwner() throws Exception {
        when(service.findById("ORD-1")).thenReturn(orderOwnedByOtherUser());
        mockMvc.perform(get("/orders/ORD-1"))
               .andExpect(status().isForbidden());
    }
}
```

### Testing error contract

Always test that your `@ControllerAdvice` error responses match the documented contract. Clients depend on the exact error format being stable.

### WebTestClient (reactive / WebFlux)

```java
@WebFluxTest(OrderController.class)
class ReactiveOrderControllerTest {
    @Autowired WebTestClient client;

    @Test
    void getOrder_shouldReturnOrder() {
        client.get().uri("/orders/123")
              .exchange()
              .expectStatus().isOk()
              .expectBody(OrderResponse.class)
              .value(r -> assertThat(r.getId()).isEqualTo("123"));
    }
}
```

---

## Q181 — Production Debugging Approach

**The one-line answer:** Effective production debugging follows a structured sequence: correlate symptoms with changes, use metrics to narrow the layer, use logs to find the specific request, and use thread/heap dumps only when metrics and logs aren't enough.

### Structured triage process

```
1. DETECT:    Alert fires or user reports issue
2. ASSESS:    What is the impact? (error rate, latency, which endpoints, how many users?)
3. CORRELATE: What changed recently? (deployment, config change, traffic spike, upstream)
4. LOCALIZE:  Which service/component? (RED metrics per service)
5. DIAGNOSE:  What is the specific cause? (logs → thread dump → heap dump → profiler)
6. MITIGATE:  Rollback? Feature flag off? Increase timeout? Shed load?
7. RCA:       What was the root cause? Why wasn't it caught earlier?
```

### Correlating symptoms to causes

| Symptom | Check first |
|---|---|
| Error rate spike | Recent deployment, upstream errors, DB errors in logs |
| Latency spike (all requests) | Thread pool exhaustion, GC pause, DB connection pool exhaustion |
| Latency spike (some endpoints) | Slow DB query, N+1 queries, slow external call |
| Memory growth (OOM) | Heap dump → retention analysis |
| High CPU | Thread dump → hot threads, GC logs → high allocation rate |
| Connection pool full | Thread dump (threads blocked in JDBC), slow queries |

### Key diagnostic commands

```bash
# Get thread dump
jcmd <pid> Thread.print > /tmp/thread.txt
kill -3 <pid>   # Also works on Linux

# Get heap dump
jcmd <pid> GC.heap_dump /tmp/heap.hprof

# GC summary
jstat -gcutil <pid> 1000 10   # every 1s, 10 times

# Open connections
lsof -i -p <pid> | grep ESTABLISHED | wc -l
```

### When to rollback vs fix forward

**Rollback if:**
- The incident is actively causing customer impact.
- The fix requires time to develop and test.
- A feature flag can disable the new behavior.

**Fix forward if:**
- The fix is trivial and safe.
- Rollback would cause data migration issues.
- The bug was in a component not changed recently (rollback won't help).

---

## Q182 — String and Log Parsing Exercise

**The one-line answer:** Count word frequencies in a string or log file using a `Map<String, Long>` built with `Collectors.groupingBy(counting())` — handle edge cases: empty input, punctuation, case sensitivity, very large files.

### Word frequency counter

```java
public Map<String, Long> wordFrequency(String text) {
    if (text == null || text.isBlank()) return Map.of();

    return Arrays.stream(text.toLowerCase()
                             .replaceAll("[^a-z0-9\\s]", "") // strip punctuation
                             .split("\\s+"))
                 .filter(w -> !w.isEmpty())
                 .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));
}

// Top N words
public List<Map.Entry<String, Long>> topN(String text, int n) {
    return wordFrequency(text).entrySet().stream()
        .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
        .limit(n)
        .collect(Collectors.toList());
}
```

### Large file — streaming approach

```java
public Map<String, Long> countFromFile(Path file) throws IOException {
    try (Stream<String> lines = Files.lines(file)) {
        return lines
            .flatMap(line -> Arrays.stream(line.toLowerCase().split("\\s+")))
            .filter(w -> !w.isBlank())
            .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));
    }
    // Files.lines uses lazy line-by-line reading — constant memory regardless of file size
}
```

### Log line parsing — extract fields

```java
// Log format: 2024-01-15 10:30:00 ERROR OrderService - Order ORD-123 failed
Pattern LOG_PATTERN = Pattern.compile(
    "(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}) (\\w+) (\\S+) - (.+)");

record LogEntry(String timestamp, String level, String logger, String message) {}

public List<LogEntry> parse(List<String> lines) {
    return lines.stream()
        .map(LOG_PATTERN::matcher)
        .filter(Matcher::matches)
        .map(m -> new LogEntry(m.group(1), m.group(2), m.group(3), m.group(4)))
        .collect(Collectors.toList());
}

// Count errors per logger
Map<String, Long> errorsPerLogger = parse(lines).stream()
    .filter(e -> "ERROR".equals(e.level()))
    .collect(Collectors.groupingBy(LogEntry::logger, Collectors.counting()));
```

---

## Q183 — Collections and Stream Exercise

**The one-line answer:** Grouping, sorting, and top-N operations on collections test practical stream fluency — practice the Collectors API, comparator chaining, and null-safe sorting.

### Group employees by department, sorted by salary

```java
record Employee(String name, String department, int salary) {}

// Group by department
Map<String, List<Employee>> byDept = employees.stream()
    .collect(Collectors.groupingBy(Employee::department));

// Top earner per department
Map<String, Optional<Employee>> topEarner = employees.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        Collectors.maxBy(Comparator.comparingInt(Employee::salary))
    ));

// Department average salary, sorted descending
Map<String, Double> avgSalary = employees.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        Collectors.averagingInt(Employee::salary)
    ));

avgSalary.entrySet().stream()
    .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
    .forEach(e -> System.out.printf("%s: %.2f%n", e.getKey(), e.getValue()));
```

### Find duplicate elements

```java
Set<String> seen = new HashSet<>();
List<String> duplicates = list.stream()
    .filter(s -> !seen.add(s))   // add returns false if already present
    .distinct()                   // avoid listing each duplicate multiple times
    .collect(Collectors.toList());
```

### Flatten and deduplicate nested lists

```java
List<List<String>> nested = List.of(List.of("a","b"), List.of("b","c"), List.of("c","d"));
List<String> distinct = nested.stream()
    .flatMap(Collection::stream)
    .distinct()
    .sorted()
    .collect(Collectors.toList()); // [a, b, c, d]
```

### Multi-field sort with null safety

```java
employees.sort(
    Comparator.comparing(Employee::department)
              .thenComparing(Comparator.comparingInt(Employee::salary).reversed())
              .thenComparing(Employee::name, Comparator.nullsLast(Comparator.naturalOrder()))
);
```

---

## Q184 — LRU Cache or Rate Limiter Exercise

**The one-line answer:** An LRU cache uses `LinkedHashMap` in access-order mode with `removeEldestEntry` override; a sliding-window rate limiter uses a `LinkedList` or `Deque` of request timestamps with expiry of entries older than the window.

### LRU Cache with LinkedHashMap

```java
public class LruCache<K, V> {
    private final Map<K, V> cache;

    public LruCache(int capacity) {
        this.cache = new LinkedHashMap<>(capacity, 0.75f, true) { // true = access order
            @Override
            protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
                return size() > capacity;
            }
        };
    }

    public synchronized V get(K key) {
        return cache.getOrDefault(key, null);
    }

    public synchronized void put(K key, V value) {
        cache.put(key, value);
    }

    public synchronized int size() { return cache.size(); }
}
```

For thread safety under high concurrency, use `ConcurrentHashMap` with a `ConcurrentLinkedDeque` to track access order (more complex but non-blocking reads).

### Sliding Window Rate Limiter

```java
public class SlidingWindowRateLimiter {
    private final int maxRequests;
    private final long windowMs;
    private final Deque<Long> timestamps = new ArrayDeque<>();

    public SlidingWindowRateLimiter(int maxRequests, long windowMs) {
        this.maxRequests = maxRequests;
        this.windowMs = windowMs;
    }

    public synchronized boolean tryAcquire() {
        long now = System.currentTimeMillis();
        long windowStart = now - windowMs;

        // Remove timestamps outside the window
        while (!timestamps.isEmpty() && timestamps.peekFirst() <= windowStart) {
            timestamps.pollFirst();
        }

        if (timestamps.size() < maxRequests) {
            timestamps.addLast(now);
            return true;  // request allowed
        }
        return false; // rate limit exceeded
    }
}
```

**Concurrency note:** For production multi-threaded use, use Redis atomic operations (Lua script) rather than in-memory synchronized blocks that don't scale across JVM instances.

---

## Q185 — SQL Exercise: Duplicates, Second Highest, Aggregation

**The one-line answer:** Common SQL exercises test deduplication, ranking (second highest), and aggregation with GROUP BY and HAVING — know multiple approaches for each because interviewers often ask for alternatives.

### Find duplicate emails

```sql
-- Method 1: GROUP BY + HAVING
SELECT email, COUNT(*) AS count
FROM users
GROUP BY email
HAVING COUNT(*) > 1;

-- Method 2: Window function (also gets row details)
SELECT *
FROM (
    SELECT *, COUNT(*) OVER (PARTITION BY email) AS email_count
    FROM users
) sub
WHERE email_count > 1;
```

### Second highest salary

```sql
-- Method 1: Subquery
SELECT MAX(salary) AS second_highest
FROM employees
WHERE salary < (SELECT MAX(salary) FROM employees);

-- Method 2: DISTINCT with LIMIT/OFFSET
SELECT DISTINCT salary
FROM employees
ORDER BY salary DESC
LIMIT 1 OFFSET 1;

-- Method 3: Window function (generalizes to Nth highest)
SELECT salary
FROM (
    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
    FROM employees
) ranked
WHERE rnk = 2;  -- change 2 to N for Nth highest
```

Edge case: if only one distinct salary exists, the first two methods return NULL — the window function returns no rows.

### Customers with no orders

```sql
-- Method 1: LEFT JOIN
SELECT c.id, c.name
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE o.id IS NULL;

-- Method 2: NOT EXISTS (often better with index on customer_id)
SELECT c.id, c.name
FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.id
);

-- Method 3: NOT IN (avoid — fails if orders.customer_id contains NULLs)
SELECT id, name FROM customers
WHERE id NOT IN (SELECT customer_id FROM orders WHERE customer_id IS NOT NULL);
```

### Running total with window function

```sql
SELECT
    order_date,
    daily_revenue,
    SUM(daily_revenue) OVER (ORDER BY order_date 
                             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM (
    SELECT DATE(created_at) AS order_date, SUM(total) AS daily_revenue
    FROM orders
    WHERE status = 'COMPLETED'
    GROUP BY DATE(created_at)
) daily;
```


<a id="chapter-9"></a>

# Chapter 9: Messaging and Caching

---

## Q186 — Queue vs Topic Patterns

**The one-line answer:** A queue delivers each message to exactly one consumer (point-to-point, competing consumers); a topic delivers each message to all subscribers (publish-subscribe, fan-out) — choose based on whether you need parallel work distribution or broadcast notification.

### Queue (point-to-point)

```
Producer → [Queue] → Consumer A
                  ↓
              Consumer B (competing — one gets it, not both)
```

- Each message is consumed by exactly one consumer.
- Multiple consumers compete for messages (competing consumers pattern) — enables horizontal scaling of workers.
- Messages persist until consumed (or TTL expires).
- Acknowledgement signals successful processing.
- Use for: job queues, order processing, email sending, task distribution.

### Topic (publish-subscribe)

```
Producer → [Topic] → Consumer A (subscription 1)
                  → Consumer B (subscription 2)
                  → Consumer C (subscription 3)
```

- Each subscriber receives every message.
- Fan-out: one event triggers multiple independent downstream actions.
- Subscribers can be durable (miss no messages) or non-durable (miss messages while offline).
- Use for: event broadcasting, change notifications, audit logging, cache invalidation.

### Kafka's hybrid model

Kafka topics have **partitions**, and each partition is consumed by exactly one consumer within a consumer group. Different groups get all messages — this combines queue semantics (within a group) and topic semantics (across groups).

```
Topic: order-events (3 partitions)
  Consumer Group A (order-processor): each partition assigned to one instance
  Consumer Group B (audit-logger): gets all events independently
  Consumer Group C (analytics): gets all events independently
```

### RabbitMQ exchange types

| Type | Routing | Use case |
|---|---|---|
| `direct` | Exact routing key match | Point-to-point, RPC |
| `fanout` | All bound queues, no routing | Broadcast to all consumers |
| `topic` | Pattern matching on routing key | Selective broadcast (`order.*.created`) |
| `headers` | Match on message headers | Complex filtering |

---

## Q187 — Kafka Topics, Partitions, and Consumer Groups

**The one-line answer:** A Kafka topic is divided into ordered, immutable, append-only partitions; consumer groups allow parallel consumption where each partition is assigned to one consumer, enabling horizontal scaling while preserving per-partition ordering.

### Core concepts

```
Topic: orders
  Partition 0: [msg0][msg1][msg4][msg7]  ← offset 0,1,4,7...
  Partition 1: [msg2][msg5][msg8]
  Partition 2: [msg3][msg6][msg9]

Consumer Group: order-processor
  Consumer A → Partition 0
  Consumer B → Partition 1
  Consumer C → Partition 2
```

- **Offset:** Position within a partition. Consumers track their offset per partition.
- **Partition ordering:** Messages within a partition are strictly ordered. Cross-partition ordering is not guaranteed.
- **Partition key:** Determines which partition a message goes to. Same key → same partition → ordering preserved for that key.

### Partition key design

```java
// All events for the same order go to the same partition — preserving order
ProducerRecord<String, OrderEvent> record = new ProducerRecord<>(
    "order-events",
    order.getId(),   // partition key — same order ID → same partition
    new OrderEvent(order)
);
```

If no key is specified, messages are round-robin distributed across partitions — no ordering guarantee.

### Replication

Each partition has a leader and N replicas (replication factor). Producers write to the leader. Followers replicate. If the leader fails, a follower is elected — no data loss if replicated.

```
Topic orders, replication-factor=3:
  Partition 0: Leader=Broker1, Replicas=[Broker2, Broker3]
  Partition 1: Leader=Broker2, Replicas=[Broker1, Broker3]
```

### Choosing partition count

More partitions = more parallelism (up to partition count consumers). But: more partitions = more file handles, more rebalancing overhead. A good default: `max(consumers_per_group, 3)`. You can increase partitions later (with loss of key-ordering guarantee during the change).

---

## Q188 — Delivery Semantics

**The one-line answer:** At-most-once means messages may be lost but never duplicated; at-least-once means messages are delivered but may be duplicated; exactly-once requires idempotent consumers or transactional producers and is the hardest to achieve.

### At-most-once

Acknowledge before processing. If the consumer crashes after acknowledging but before completing processing, the message is lost.

```
Consumer receives message → auto-acknowledges → processes → (crash here = message lost)
```

Kafka: `enable.auto.commit=true` with `auto.commit.interval.ms` — commits offsets periodically regardless of whether processing succeeded.

Use for: low-value events where occasional loss is acceptable (analytics, non-critical metrics).

### At-least-once

Process then acknowledge. If the consumer crashes after processing but before acknowledging, the message is redelivered — **duplicate processing is possible**.

```
Consumer receives message → processes → (crash here = redelivery) → acknowledges
```

Kafka: `enable.auto.commit=false` with manual `consumer.commitSync()` after processing.

**The consumer must be idempotent** — processing the same message twice must produce the same result.

```java
@KafkaListener(topics = "order-events")
public void processOrder(OrderEvent event) {
    if (processedEvents.contains(event.getEventId())) return; // idempotency check
    orderService.process(event);
    processedEvents.add(event.getEventId()); // mark as processed
}
```

### Exactly-once

Kafka 0.11+ supports exactly-once semantics (EOS) within Kafka → Kafka pipelines using transactional producers and idempotent consumers. For Kafka → external systems (database, HTTP), you need the outbox pattern or application-level idempotency.

```java
// Kafka transactional producer
Properties props = new Properties();
props.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, "order-producer-1");
producer.initTransactions();

producer.beginTransaction();
try {
    producer.send(new ProducerRecord<>("orders", key, value));
    producer.commitTransaction();
} catch (Exception e) {
    producer.abortTransaction();
}
```

Spring Kafka supports this via `@Transactional` on `KafkaTemplate` with a configured `KafkaTransactionManager`.

---

## Q189 — Ordering, Retries, and DLQ

**The one-line answer:** Partition keys preserve per-entity ordering in Kafka; retry storms are prevented with backoff and DLQs catch poison-pill messages that repeatedly fail processing.

### Ordering guarantee

Kafka guarantees ordering within a partition. To preserve event order for a specific entity (order, user, account):
- Use the entity's ID as the partition key.
- All events for that entity land in the same partition → processed in order.

### Retry strategy

Don't retry indefinitely — use bounded retries with backoff:

```java
// Spring Kafka retry configuration
@Bean
public CommonErrorHandler errorHandler() {
    return new DefaultErrorHandler(
        new DeadLetterPublishingRecoverer(kafkaTemplate,
            (record, ex) -> new TopicPartition(record.topic() + ".DLQ", record.partition())),
        new FixedBackOff(1000L, 3L) // retry 3 times, 1s apart
    );
}
```

### Dead Letter Queue (DLQ)

A DLQ receives messages that failed after all retries. Benefits:
- Prevents a poison-pill message from blocking the entire partition.
- Messages in DLQ can be inspected, fixed, and reprocessed manually.
- Alerts on DLQ depth catch persistent processing failures.

```
Normal flow:   topic → consumer → success
Retry flow:    topic → consumer (fail) → retry 1 → retry 2 → retry 3 → DLQ
DLQ:           topic.DLQ → manual inspection / replay
```

### Poison pills

A message that always fails (bad data, schema mismatch) will retry indefinitely, blocking the partition. Always:
1. Catch deserialization errors (`ErrorHandlingDeserializer`).
2. Limit retries.
3. Route unprocessable messages to DLQ.
4. Set an alert on DLQ depth > 0.

---

## Q190 — Offset Commits and Rebalancing

**The one-line answer:** Offset commits record the consumer's position in a partition; manual commit after processing ensures at-least-once semantics; consumer group rebalancing reassigns partitions when consumers join or leave — during rebalance, all processing pauses.

### Manual offset commit

```java
@KafkaListener(topics = "orders", containerFactory = "kafkaListenerContainerFactory")
public void process(ConsumerRecord<String, OrderEvent> record,
                    Acknowledgment ack) {
    try {
        orderService.process(record.value());
        ack.acknowledge(); // commit offset only on success
    } catch (NonRetriableException e) {
        ack.acknowledge(); // acknowledge to skip poison pill
        dlqProducer.send(record); // send to DLQ
    }
    // Don't ack on retriable exceptions — let the container retry
}
```

```properties
spring.kafka.listener.ack-mode=manual_immediate
enable.auto.commit=false
```

### Auto-commit dangers

`enable.auto.commit=true` commits offsets at intervals (default 5s) regardless of processing status. If a consumer crashes between the commit and processing completion, messages appear processed but weren't. Use manual commit for at-least-once guarantees.

### Consumer group rebalancing

Triggered by:
- A consumer joins the group (new instance deployed).
- A consumer leaves (graceful shutdown, crash, missed heartbeat).
- Topic partition count changes.

During rebalance:
- All consumers in the group pause consumption (`stop-the-world`).
- Kafka reassigns partitions to consumers.
- Consumers resume from committed offsets.

Minimize rebalances:
- Use `session.timeout.ms` and `heartbeat.interval.ms` appropriately to distinguish slow processing from dead consumers.
- Use `ConsumerRebalanceListener` to commit offsets before partitions are revoked.
- Incremental cooperative rebalancing (Kafka 2.4+) reduces pause time — only partitions being moved are paused.

### Consumer lag

Consumer lag = latest offset − committed offset per partition. High lag means the consumer is falling behind. Monitor with:
```bash
kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --group order-processor
```

---

## Q191 — Redis Data Structures

**The one-line answer:** Redis provides multiple data structures beyond simple key-value strings — each optimized for specific use cases: strings for counters/flags, hashes for objects, lists for queues, sets for membership, sorted sets for leaderboards and rate limiting.

### Data structures

```
STRING:      GET/SET/INCR/EXPIRE       → counters, flags, session tokens, cached responses
HASH:        HSET/HGET/HGETALL         → objects (user profile, session attributes)
LIST:        LPUSH/RPOP/LRANGE         → queues, activity feeds, recent items
SET:         SADD/SMEMBERS/SISMEMBER   → unique membership, tags, "who liked this"
SORTED SET:  ZADD/ZRANGE/ZRANGEBYSCORE → leaderboards, rate limiting, priority queues
STREAM:      XADD/XREAD                → event log, message queue (similar to Kafka at small scale)
```

### String — counter and cache

```java
// Atomic counter
redisTemplate.opsForValue().increment("api:calls:today");

// Cached response with TTL
redisTemplate.opsForValue().set("order:123", orderJson, Duration.ofMinutes(5));
String cached = (String) redisTemplate.opsForValue().get("order:123");
```

### Hash — object storage

```java
// Store user session as hash fields
redisTemplate.opsForHash().putAll("session:" + sessionId,
    Map.of("userId", "U123", "role", "USER", "createdAt", Instant.now().toString()));

String role = (String) redisTemplate.opsForHash().get("session:" + sessionId, "role");
```

### Sorted Set — sliding window rate limiting

```java
// Track request timestamps in a sorted set, score = timestamp
double now = System.currentTimeMillis();
double windowStart = now - 60_000; // 60 second window

redisTemplate.opsForZSet().removeRangeByScore("ratelimit:" + userId, 0, windowStart);
Long count = redisTemplate.opsForZSet().zCard("ratelimit:" + userId);

if (count < MAX_REQUESTS_PER_MINUTE) {
    redisTemplate.opsForZSet().add("ratelimit:" + userId, String.valueOf(now), now);
    redisTemplate.expire("ratelimit:" + userId, Duration.ofMinutes(2));
    return true; // allowed
}
return false; // rate limited
```

### TTL and eviction

Always set TTL on cache entries: `redisTemplate.expire(key, Duration.ofMinutes(10))`. Configure eviction policy for memory management:
```
maxmemory-policy: allkeys-lru    # evict least recently used keys when memory full
```

---

## Q192 — Cache-Aside and Invalidation

**The one-line answer:** Cache-aside (lazy loading) checks the cache first, loads from DB on miss, and writes to cache — ensuring the cache only contains actually-needed data; invalidation strategies (TTL, event-driven, write-through) keep the cache consistent with the source of truth.

### Cache-aside pattern

```java
public Order findById(String orderId) {
    // 1. Check cache
    String key = "order:" + orderId;
    Order cached = (Order) cache.get(key);
    if (cached != null) return cached;

    // 2. Cache miss — load from DB
    Order order = repository.findById(orderId).orElseThrow();

    // 3. Populate cache with TTL
    cache.put(key, order, Duration.ofMinutes(5));

    return order;
}
```

With Spring's `@Cacheable`:

```java
@Cacheable(value = "orders", key = "#orderId", unless = "#result == null")
public Order findById(String orderId) {
    return repository.findById(orderId).orElseThrow();
}

@CacheEvict(value = "orders", key = "#order.id")
public Order update(Order order) {
    return repository.save(order);
}

@CachePut(value = "orders", key = "#result.id")
public Order create(Order order) {
    return repository.save(order); // cache updated, not just evicted
}
```

### Invalidation strategies

| Strategy | How it works | Consistency | Complexity |
|---|---|---|---|
| TTL | Cache expires after fixed time | Eventually consistent | Low |
| Write-through | Update cache on every write | Strong | Medium |
| Write-behind | Update cache immediately, DB asynchronously | Eventually consistent | High |
| Event-driven | Service publishes event → cache evicts on event | Strong | Medium |

### Cache stampede prevention

When a popular cache entry expires, thousands of requests simultaneously miss and all try to load from DB. Fixes:
1. **Mutex / distributed lock:** First thread loads, others wait.
2. **Stale-while-revalidate:** Return stale data while refreshing in background.
3. **Probabilistic early expiry:** Randomly refresh before TTL expires (seen in Q193).

---

## Q193 — Cache Stampede

**The one-line answer:** A cache stampede (thundering herd) happens when a highly-used cache entry expires simultaneously for many requests — solutions include probabilistic early expiry, background refresh, and distributed locking.

### The problem

```
T=0: Cache entry for "homepage" set, TTL=60s
T=60: Entry expires
T=60+ε: 500 concurrent requests → all miss → all query DB → DB overloaded
```

### Solution 1 — TTL Jitter

Add random variation to TTL so entries don't expire all at once:

```java
int baseTtl = 300; // 5 minutes
int jitter = ThreadLocalRandom.current().nextInt(60); // 0-60 seconds
cache.put(key, value, Duration.ofSeconds(baseTtl + jitter));
```

### Solution 2 — Probabilistic Early Expiry (XFetch algorithm)

Refresh the cache early with increasing probability as TTL approaches zero:

```java
public Value getWithXFetch(String key) {
    CacheEntry entry = getRaw(key); // includes creation time, TTL, value
    if (entry == null) return loadAndCache(key);

    double ttlRemaining = entry.expiresAt - System.currentTimeMillis() / 1000.0;
    double delta = entry.computeTimeMs / 1000.0; // how long to recompute

    // Early recompute if: random factor exceeds remaining time / recompute time ratio
    if (-delta * Math.log(Math.random()) >= ttlRemaining) {
        return loadAndCache(key); // this instance recomputes early
    }
    return entry.value;
}
```

### Solution 3 — Background Refresh

Keep a background thread refreshing popular entries before they expire:

```java
@Scheduled(fixedDelay = 30_000)
public void refreshPopularEntries() {
    popularKeys.forEach(key -> {
        Value fresh = loadFromDb(key);
        cache.put(key, fresh, Duration.ofMinutes(5));
    });
}
```

### Solution 4 — Distributed lock (Redis SETNX)

```java
public Value getWithLock(String key) {
    Value cached = cache.get(key);
    if (cached != null) return cached;

    String lockKey = "lock:" + key;
    Boolean acquired = redisTemplate.opsForValue()
        .setIfAbsent(lockKey, "1", Duration.ofSeconds(10));

    if (Boolean.TRUE.equals(acquired)) {
        try {
            Value fresh = loadFromDb(key);
            cache.put(key, fresh, Duration.ofMinutes(5));
            return fresh;
        } finally {
            redisTemplate.delete(lockKey);
        }
    } else {
        Thread.sleep(50); // brief wait
        return cache.get(key); // another thread should have populated it
    }
}
```

---

## Q194 — Distributed Locks with Redis

**The one-line answer:** Use `SET key value NX PX timeout` (SETNX) for a single-node distributed lock with automatic expiry; for multi-node Redis (Redlock), be aware of clock-drift caveats and prefer purpose-built tools like ZooKeeper or etcd for strong consistency requirements.

### Basic SETNX lock

```java
public boolean acquireLock(String lockKey, String lockValue, Duration ttl) {
    // NX = only set if Not eXists, PX = TTL in milliseconds
    Boolean acquired = redisTemplate.opsForValue()
        .setIfAbsent(lockKey, lockValue, ttl);
    return Boolean.TRUE.equals(acquired);
}

public void releaseLock(String lockKey, String lockValue) {
    // Lua script for atomic check-and-delete (prevents releasing another holder's lock)
    String script = "if redis.call('get', KEYS[1]) == ARGV[1] then " +
                    "  return redis.call('del', KEYS[1]) " +
                    "else return 0 end";
    redisTemplate.execute(new DefaultRedisScript<>(script, Long.class),
                          List.of(lockKey), lockValue);
}

// Usage
String lockValue = UUID.randomUUID().toString(); // unique per holder
if (acquireLock("job:daily-report", lockValue, Duration.ofMinutes(5))) {
    try { runDailyReport(); }
    finally { releaseLock("job:daily-report", lockValue); }
} else {
    log.info("Another instance is running the report — skipping");
}
```

### Redlock — multi-node locking

The Redlock algorithm acquires the lock on N independent Redis nodes (N ≥ 5). Lock is valid if acquired on a majority (N/2 + 1) within a time window.

**Redlock caveats (Martin Kleppmann's critique):**
- Relies on timing assumptions (clocks don't drift by more than a few milliseconds).
- Under GC pause or clock jump, the lock TTL can expire while the client still thinks it holds it.
- For truly safe distributed locking, use a consensus-based system (etcd, ZooKeeper).

For most application-level locking (preventing duplicate cron jobs, rate limiting), single-node Redis locks are sufficient and practical.

### Lease renewal for long-running operations

```java
ScheduledFuture<?> renewal = scheduler.scheduleAtFixedRate(
    () -> redisTemplate.expire(lockKey, Duration.ofSeconds(30)),
    15, 15, TimeUnit.SECONDS
);
try { longRunningOperation(); }
finally { renewal.cancel(true); releaseLock(lockKey, lockValue); }
```

---

## Q195 — Message Serialization and Schema Evolution

**The one-line answer:** JSON is flexible but schema-free; Avro and Protobuf provide schema-based, compact binary serialization with explicit compatibility rules for schema evolution — use a schema registry in production Kafka setups.

### JSON pros and cons

**Pros:** Human-readable, no schema needed, easy to debug, universal tooling support.  
**Cons:** Verbose (field names repeated in every message), no type validation, no evolution rules, easy to accidentally break consumers with field renames.

### Avro with Schema Registry (Confluent)

```json
{
  "type": "record",
  "name": "OrderCreated",
  "namespace": "com.example.events",
  "fields": [
    {"name": "orderId", "type": "string"},
    {"name": "customerId", "type": "string"},
    {"name": "total", "type": "double"},
    {"name": "createdAt", "type": "long", "logicalType": "timestamp-millis"},
    {"name": "notes", "type": ["null", "string"], "default": null}  // optional field
  ]
}
```

The schema is registered in the Confluent Schema Registry. Each message contains a schema ID, not the full schema — messages are compact.

### Schema compatibility modes

| Mode | Allows | Prevents |
|---|---|---|
| `BACKWARD` | Add optional fields | Remove required fields |
| `FORWARD` | Remove optional fields | Add required fields |
| `FULL` | Both backward + forward | Any breaking change |
| `NONE` | Anything | Nothing |

Use `BACKWARD` compatibility — new consumers can read messages produced by old producers. When adding a field, always provide a default value.

### Evolution rules

```
SAFE:
  Add a field with a default value
  Remove a field (backward: old consumer ignores unknown; forward: new consumer uses default)
  Change field order (Avro uses field names, not positions)

BREAKING:
  Rename a field (appears as removal + addition)
  Change a field's type
  Add a field with no default (breaks old consumers)
  Remove a required field
```

### Poison messages from schema changes

A consumer running old code receives a message with a new schema it doesn't understand. Solutions:
1. Schema compatibility enforcement prevents this in a registry.
2. `ErrorHandlingDeserializer` catches deserialization errors and routes to DLQ.
3. Deploy consumers before producers when adding fields.


<a id="chapter-10"></a>

# Chapter 10: Deployment, Observability, and Production Troubleshooting

---

## Q196 — Docker for Spring Boot

**The one-line answer:** Containerize Spring Boot with a multi-stage Dockerfile using layered JARs so unchanged dependency layers are cached, resulting in fast incremental rebuilds and small image diffs on push.

### Layered JAR Dockerfile

```dockerfile
# Stage 1 — extract layers from the fat JAR
FROM eclipse-temurin:21-jre-alpine AS builder
WORKDIR /app
COPY target/*.jar app.jar
RUN java -Djarmode=layertools -jar app.jar extract

# Stage 2 — final image with layers in cache-optimal order
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app

# These layers rarely change — cached across builds
COPY --from=builder /app/dependencies/ ./
COPY --from=builder /app/spring-boot-loader/ ./
COPY --from=builder /app/snapshot-dependencies/ ./

# This layer changes on every code change — rebuilt last
COPY --from=builder /app/application/ ./

# Run as non-root user — security best practice
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# JVM flags for container awareness
ENV JAVA_OPTS="-XX:MaxRAMPercentage=75.0 -XX:+UseZGC -Djava.security.egd=file:/dev/./urandom"
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS org.springframework.boot.loader.launch.JarLauncher"]

EXPOSE 8080
```

### Image size optimization

- Use `eclipse-temurin:21-jre-alpine` (~180 MB) not `eclipse-temurin:21` (~450 MB) — JRE only, Alpine base.
- Consider `distroless/java21-debian12` for minimal attack surface (no shell).
- Use multi-stage builds to exclude build tools from the final image.

### Spring Boot Maven/Gradle Buildpacks (alternative)

```bash
# Let Spring Boot build a production-ready image without a Dockerfile
./mvnw spring-boot:build-image -Dspring-boot.build-image.imageName=myapp:latest
```

Buildpacks handle JVM flags, layering, and security patching automatically.

### Essential Dockerfile security practices

- Run as non-root user.
- Use a specific image tag, not `latest` — ensures reproducible builds.
- Scan images with `docker scout` or Trivy for known CVEs.
- Don't copy secrets or `.env` files into the image — inject via environment variables or secrets mounts at runtime.

---

## Q197 — Health Checks and Graceful Shutdown

**The one-line answer:** Kubernetes uses liveness and readiness probes to manage container lifecycle — liveness triggers restarts, readiness gates traffic; graceful shutdown drains in-flight requests before the process exits on SIGTERM.

### Probe types

| Probe | Question | Failure action |
|---|---|---|
| **Liveness** | "Is this container alive or deadlocked?" | Restart the container |
| **Readiness** | "Is this container ready to serve traffic?" | Remove from load balancer |
| **Startup** | "Has the container finished starting?" | Restart if not ready within time limit |

### Spring Boot Actuator health groups

```properties
management.endpoint.health.probes.enabled=true
management.endpoint.health.group.liveness.include=livenessState
management.endpoint.health.group.readiness.include=readinessState,db,redis
management.health.db.enabled=true
management.health.redis.enabled=true
```

### Kubernetes probe configuration

```yaml
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 30    # wait for app startup
  periodSeconds: 10
  failureThreshold: 3        # restart after 3 consecutive failures

readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 3

startupProbe:                # replaces initialDelaySeconds for slow-starting apps
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  failureThreshold: 30       # allow up to 30 × 10s = 5 minutes for startup
  periodSeconds: 10
```

### Graceful shutdown flow

```properties
server.shutdown=graceful
spring.lifecycle.timeout-per-shutdown-phase=30s
```

```
Kubernetes sends SIGTERM
  │
  ▼ Spring Boot receives SIGTERM
  │  → marks readiness DOWN (stop receiving new traffic)
  │  → waits up to 30s for in-flight requests to complete
  │  → calls @PreDestroy / SmartLifecycle.stop()
  │  → closes DB connections, Kafka consumers, scheduled tasks
  │
  ▼ Process exits (code 0)
```

Kubernetes `terminationGracePeriodSeconds` must be greater than `timeout-per-shutdown-phase` plus the time for `preStop` hooks and actual termination.

### Custom readiness state

```java
@Autowired ApplicationContext applicationContext;

public void markNotReady(String reason) {
    AvailabilityChangeEvent.publish(applicationContext,
        ReadinessState.REFUSING_TRAFFIC);
    log.warn("Service marked not ready: {}", reason);
}
```

---

## Q198 — Logs, Metrics, and Tracing

**The one-line answer:** The three pillars of observability are logs (what happened), metrics (how much/fast), and traces (how long each step took across services) — together they enable diagnosing production issues without reproducing them locally.

### The three pillars

**Logs:** Timestamped, structured events. Searchable. High cardinality. Good for "what happened to order ORD-123?"

**Metrics:** Aggregated numerical measurements over time. Low cardinality. Good for "what is the error rate right now?"

**Traces:** Distributed call trees showing the path and duration of a request across multiple services. Good for "why is this endpoint slow?"

### RED metrics (per service/endpoint)

- **R**ate: requests per second
- **E**rror: error rate (% of requests failing)
- **D**uration: latency distribution (p50, p95, p99)

```java
@Bean
public WebMvcObservationFilter observationFilter(ObservationRegistry registry) {
    return new WebMvcObservationFilter(registry); // auto-records RED metrics per endpoint
}
```

```properties
management.metrics.distribution.percentiles-histogram.http.server.requests=true
management.metrics.distribution.percentiles.http.server.requests=0.5,0.95,0.99
```

### Structured logging for log aggregation

```json
{
  "timestamp": "2024-01-15T10:00:00.123Z",
  "level": "INFO",
  "logger": "com.example.OrderService",
  "message": "Order placed",
  "requestId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "U123",
  "orderId": "ORD-456",
  "durationMs": 42
}
```

```xml
<!-- logback-spring.xml -->
<appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
    <encoder class="net.logstash.logback.encoder.LogstashEncoder">
        <includeMdcKeyName>requestId</includeMdcKeyName>
        <includeMdcKeyName>userId</includeMdcKeyName>
    </encoder>
</appender>
```

### Distributed tracing

```properties
management.tracing.sampling.probability=0.1        # sample 10% in production
management.zipkin.tracing.endpoint=http://zipkin:9411/api/v2/spans
# Or OpenTelemetry:
management.otlp.tracing.endpoint=http://otel-collector:4318/v1/traces
```

Trace context propagates via `traceparent` HTTP header (W3C standard) and Kafka message headers. In logs, the trace/span ID is injected via MDC automatically with Micrometer Tracing.

### Alerting principles

Alert on symptoms, not causes:
- ✅ "Error rate > 5% for 5 minutes"
- ✅ "p99 latency > 2s for 2 minutes"
- ❌ "CPU > 80%" — may be normal; not always a problem
- ❌ "GC pause > 100ms" — too implementation-specific for an alert

Set `Severity: Page` (wake someone up) only for customer-impacting issues. Use `Warning` for degraded-but-not-broken states.

---

## Q199 — OOM, GC, and Thread Exhaustion Troubleshooting

**The one-line answer:** OOM errors require a heap dump to identify the retained object tree; GC issues require GC log analysis and allocation profiling; thread exhaustion requires a thread dump to identify what threads are blocked on.

### OutOfMemoryError: Java heap space

**Diagnosis:**
```bash
# Capture heap dump automatically on OOM
java -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp/

# Or on a live JVM showing memory growth
jcmd <pid> GC.heap_dump /tmp/heap-$(date +%s).hprof
```

**Analysis with Eclipse MAT:**
1. Open heap.hprof.
2. Run "Leak Suspects" report.
3. Check "Dominator Tree" — which object retains the most heap?
4. Use "List objects" to find all instances of a suspicious class.

**Common causes:**
- Static `Map`/`List` growing without eviction.
- Hibernate `persistence context` holding thousands of managed entities.
- Large query results loaded fully into memory.
- String interning (`String.intern()` fills metaspace/heap).

### OOMKilled in Kubernetes

The container was killed by the OS because it exceeded its cgroup memory limit.

```
Process JVM heap + metaspace + code cache + thread stacks + off-heap
← All of this must fit within container memory limit
```

Fix: `XX:MaxRAMPercentage=75.0` leaves 25% for non-heap. Set container limit and request appropriately:
```yaml
resources:
  requests: { memory: "512Mi", cpu: "250m" }
  limits:   { memory: "512Mi", cpu: "1000m" }  # memory limit = memory request (stable)
```

### GC issues

```bash
# GC log analysis
java -Xlog:gc*:file=/logs/gc.log:time,uptime:filecount=5,filesize=20m

# Quick GC summary on live JVM
jstat -gcutil <pid> 1000 30  # every 1s for 30 iterations
# Output: S0   S1   E     O    M  CCS  YGC  YGCT  FGC  FGCT  CGC  CGCT  GCT
# O (old gen) growing toward 100%  → memory leak
# FGC count increasing rapidly     → full GC storm
```

**High allocation rate:** Objects created faster than GC can collect them. Profile with async-profiler's allocation mode:
```bash
./asprof -e alloc -d 30 -f /tmp/alloc.html <pid>
```

### Thread exhaustion

**Symptoms:** Requests timeout, `RejectedExecutionException`, thread pool queue full.

**Diagnosis:**
```bash
jcmd <pid> Thread.print > threads.txt
grep -c "java.lang.Thread.State" threads.txt  # total thread count
grep -c "BLOCKED" threads.txt                  # blocked threads
grep -c "WAITING" threads.txt                  # waiting threads
```

**Common causes:**
- All Tomcat threads blocked on slow DB queries → increase pool, fix queries.
- All threads blocked on external HTTP call → timeout too long, add circuit breaker.
- Thread leak: `Executors.newCachedThreadPool()` creating unbounded threads.
- Virtual thread pinning: `synchronized` block around IO.

---

## Q200 — Incident Troubleshooting Runbook

**The one-line answer:** A production incident requires structured triage — detect, assess impact, mitigate quickly (rollback/feature flag), then diagnose the root cause; communication to stakeholders runs in parallel, not after resolution.

### Incident response phases

#### Phase 1: Detect and Assess (0–5 minutes)

```
1. Alert fires / user reports
2. Confirm it's real (not a monitoring fluke): check multiple signals
3. Assess impact:
   - Which endpoints/features are affected?
   - How many users? (error rate × traffic)
   - Is it getting better or worse?
   - Customer-facing or internal?
4. Declare severity:
   - SEV1: Service down, data loss risk, security breach
   - SEV2: Major feature degraded, significant user impact
   - SEV3: Minor degradation, workaround available
```

#### Phase 2: Mitigate (5–30 minutes)

Goal: stop the bleeding, not necessarily fix the root cause.

```
□ Recent deployment? → Rollback immediately
□ Feature flagged? → Toggle off
□ Elevated traffic? → Enable rate limiting / shed load
□ Upstream dependency? → Enable circuit breaker fallback
□ Database issue? → Kill long-running queries, failover to replica
□ Memory/CPU exhaustion? → Restart pod (if stateless), scale out
```

**Rollback decision criteria:**
- Error rate > 5% and growing → rollback without further diagnosis.
- Error rate < 5% and stable → continue investigating, rollback is an option.
- Data mutation involved → very careful — rollback may cause inconsistencies.

#### Phase 3: Communicate (in parallel with phases 1–2)

```
Internal: alert on-call team, escalate to team lead / manager
External: update status page within 5 minutes of confirming customer impact
  "We are investigating reports of [X]. Our team is working to resolve this."
  (Never say "we have identified the cause" until you're sure)
```

Update every 15–30 minutes even if there's no new information:
```
"We continue to investigate. [X] users affected. No ETA yet. Next update in 15 minutes."
```

#### Phase 4: Diagnose (during or after mitigation)

```
1. Correlate timing with deployments, config changes, traffic
2. Check metrics: which RED metric degraded first?
3. Check logs: errors appearing? Which service?
4. Check upstream dependencies: status pages, health endpoints
5. Thread dump if threads exhausted
6. Heap dump if memory issue
7. Query slow log if database issue
```

#### Phase 5: Resolve and Recover

```
□ Deploy fix (or confirm rollback is stable)
□ Verify metrics return to baseline
□ Update status page: "Resolved"
□ Inform stakeholders
□ Run post-incident review within 48 hours
```

### Post-Incident Review (blameless)

```
Timeline: What happened, when?
Impact: How many users? Duration? Data affected?
Root cause: What caused the incident?
Contributing factors: What made detection harder? What made impact worse?
Action items:
  - Improve monitoring (detect earlier)
  - Add test for this failure mode
  - Fix the root cause
  - Improve runbooks
```

A good post-incident review is blameless — focus on systems and processes, not individuals. The goal is to prevent recurrence, not assign fault.

### Production readiness checklist

Before deploying a new service or major feature:

```
Observability:
□ Structured logging with correlation IDs
□ RED metrics instrumented
□ Distributed tracing enabled
□ Alerts configured (error rate, latency, saturation)
□ Dashboard created

Reliability:
□ Health checks (liveness + readiness)
□ Graceful shutdown configured
□ Timeouts on all external calls
□ Retries with backoff and jitter
□ Circuit breakers on critical dependencies
□ Rate limiting on public endpoints

Operations:
□ Rollback plan documented
□ Feature flags for risky features
□ Runbook written and linked from alerts
□ On-call rotation updated
□ Load tested at expected peak traffic

Security:
□ Secrets not in source code
□ Authentication and authorization configured
□ Input validation at API boundary
□ Dependency scan (no critical CVEs)
□ TLS configured
```


<a id="top-40"></a>

# Highest-Priority Questions to Revise First

These 69 high-signal questions are the core technical foundation tested in mid-to-senior Java backend developer interviews (3–5 years experience), grouped into three revision tiers rather than one flat list:

- **Tier 1 — Non-negotiable (25):** asked in almost every loop at this level. You must be able to answer these cold, with code, follow-ups, and a production example.
- **Tier 2 — Common depth probes (28):** usually surfaced as follow-ups to a Tier 1 answer, or as the second half of a question pair.
- **Tier 3 — Senior differentiators (16):** the answers that separate "solid mid-level" from "hire" — production reasoning, trade-off judgement, and operational literacy.

Every question referenced here has a full answer in its chapter.

## Tier 1 — Non-negotiable

| ID | Title | Why start here |
|---|---|---|
| Q005 | equals and hashCode contract | Equality and hashing mistakes are a premier source of production bugs in sets, maps, and caches. |
| Q007 | String immutability and string pool | Essential language mechanics with direct security, thread-safety, and heap memory consequences. |
| Q009 | Checked vs unchecked exceptions and API design | Dictates error translation strategy, transaction rollback behavior, and boundary design. |
| Q011 | Immutability and defensive copying | Eliminates state aliasing and data races in concurrent Spring backend services. |
| Q012 | Records in Java 17/21 | Modern data carrier syntax; crucial to know why records excel for DTOs but fail for JPA entities. |
| Q013 | Optional done right | Distinguishes clean null-safety design from anti-patterns like Optional fields or `get()` calls. |
| Q031 | Choosing the right collection | Architectural decision-making based on ordering, uniqueness, and access complexity. |
| Q033 | HashMap internals | Classic deep-dive: hashing, bucket indexing, collision resolution, treeification, and resizing. |
| Q039 | Generics fundamentals | Type safety foundation required for reusable service, repository, and library design. |
| Q041 | Wildcards and PECS | Producer Extends, Consumer Super — senior-level generic API flexibility. |
| Q043 | Stream fundamentals | Lazy evaluation, intermediate vs terminal operations, and avoiding multiple traversal pitfalls. |
| Q044 | map, flatMap, filter, reduce | Core transformation and aggregation building blocks tested in live coding interviews. |
| Q049 | Common stream coding patterns | Canonical solutions for frequency counting, top N, grouping, and multi-field sorting. |
| Q052 | Race conditions, visibility, happens-before | Core concurrency concept separating atomicity from memory model visibility guarantees. |
| Q053 | synchronized and monitors | Fundamental intrinsic locking, monitor reentrancy, and thread synchronization. |
| Q057 | Thread pools and ExecutorService | Pool sizing formulas, queue bounding, rejection policies, and graceful shutdown in production. |
| Q061 | Deadlocks | The four Coffman conditions, thread dump diagnosis, lock ordering, and deadlock prevention. |
| Q076 | Dependency injection and constructor injection | IoC container foundation, immutability, testability, and circular dependency prevention. |
| Q083 | Spring MVC request flow | `DispatcherServlet`, handler mapping, message converters, and request lifecycle. |
| Q089 | @Transactional mechanics | CGLIB proxy interception, self-invocation traps, and checked vs unchecked rollback rules. |
| Q090 | Transaction propagation and isolation | `REQUIRED` vs `REQUIRES_NEW`, nested transactions, and database isolation levels. |
| Q120 | Lazy vs eager fetching | `FetchType.LAZY` vs `EAGER`, `LazyInitializationException`, and avoiding eager cartesian products. |
| Q121 | N+1 query problem and fixes | Root cause of slow endpoints; resolution via `JOIN FETCH`, `@EntityGraph`, and batch sizing. |
| Q136 | HTTP methods and semantics | Safe vs idempotent methods, request/response headers, and REST semantic correctness. |
| Q161 | Authentication vs authorization | Identity verification vs permission enforcement, 401 Unauthorized vs 403 Forbidden. |

## Tier 2 — Common depth probes

| ID | Title | Why it matters |
|---|---|---|
| Q001 | OOP in realistic backend code | Evaluates rich domain modeling vs anemic models and pragmatic abstraction boundaries. |
| Q016 | Sealed classes and interfaces | Type-safe domain modeling and compiler-enforced exhaustiveness in pattern matching switch. |
| Q024 | Core functional interfaces | Foundation for Stream pipelines, lazy evaluation, and functional Spring programming. |
| Q025 | Lambdas and effectively final | Clarifies variable capture, closures, and concurrency safety on thread stacks. |
| Q030 | Java 17 vs Java 21 for backend developers | Proves currency with modern LTS capabilities: virtual threads, sequenced collections, switch patterns. |
| Q032 | ArrayList vs LinkedList | Debunks the "LinkedList is faster for insertions" myth with CPU cache locality facts. |
| Q051 | Java threads and lifecycle | Thread states, thread dumps, and lifecycle transitions for debugging concurrency issues. |
| Q059 | CompletableFuture composition | Composing non-blocking asynchronous pipelines, thread pool isolation, and exception recovery. |
| Q064 | Thread-safe design strategies | Immutability, thread confinement, and stateless service design to eliminate concurrency bugs. |
| Q068 | JVM memory areas | Heap, Stack, Metaspace, and Native memory model required for diagnosing OOM errors. |
| Q077 | Bean scopes | Singleton vs Prototype, stateful singleton concurrency traps, and proxy modes for web scopes. |
| Q080 | Spring Boot auto-configuration | Conditional beans (`@ConditionalOnMissingBean`), starters, and override mechanics. |
| Q086 | Exception handling with @ControllerAdvice | Centralized API error contracts, `ProblemDetail` RFC 7807 formatting, and status mapping. |
| Q107 | SQL joins | Inner, left, right, full outer joins, row multiplication traps, and query optimization. |
| Q109 | Indexes | B-Tree index structure, composite index column ordering, covering indexes, and write costs. |
| Q111 | ACID and transaction boundaries | Correctness foundation for relational data integrity and transaction scoping. |
| Q112 | Isolation levels and anomalies | Dirty reads, non-repeatable reads, phantom reads, and PostgreSQL MVCC behavior. |
| Q114 | Optimistic vs pessimistic locking | `@Version` fields, `SELECT FOR UPDATE`, conflict handling, and retry strategies. |
| Q139 | Idempotency and retry-safe endpoints | Idempotency keys, duplicate payment prevention, and distributed deduplication strategies. |
| Q144 | Error response design | Consistent error schemas, machine-readable codes, correlation IDs, and security redaction. |
| Q162 | Session vs JWT trade-offs | Stateful server sessions vs stateless JWT tokens, token revocation, and refresh token rotation. |
| Q165 | CSRF vs CORS | Browser security policies, cross-origin resource sharing vs cross-site request forgery defenses. |
| Q168 | OWASP API vulnerabilities | BOLA/IDOR, broken authentication, mass assignment, injection, and security defenses. |
| Q173 | Testing pyramid for backend | Unit, slice, and integration test distribution, test execution speed, and fidelity. |
| Q177 | Spring test slices | `@WebMvcTest`, `@DataJpaTest`, `@SpringBootTest` context caching and test isolation. |
| Q187 | Kafka topics, partitions, consumer groups | Scaling event streams, partition key hashing, per-partition ordering, and consumer rebalancing. |
| Q191 | Redis data structures | Strings, Hashes, Lists, Sets, Sorted Sets (ZSET), TTL expiry, and backend use cases. |
| Q192 | Cache-aside and invalidation | Cache-aside read/write patterns, cache invalidation vs TTL expiry, and eventual consistency. |

## Tier 3 — Senior differentiators

| ID | Title | Why it matters |
|---|---|---|
| Q066 | Virtual threads in Java 21 | High-throughput blocking I/O, carrier thread unmounting, and the synchronized pinning caveat. |
| Q070 | Memory leaks in Java | Static caches, unclosed resources, ThreadLocal leaks, and Eclipse MAT heap dump analysis. |
| Q101 | Spring Security filter chain basics | Request security pipeline, authentication vs authorization, and security context propagation. |
| Q118 | JPA EntityManager and entity states | New, Managed, Detached, Removed lifecycle states and the persistence context first-level cache. |
| Q129 | OSIV and transaction boundaries | Open Session In View anti-pattern, connection pool exhaustion, and safe DTO projections. |
| Q150 | Timeouts, retries, backoff, jitter | Preventing cascading failures, retry storms, exponential backoff, and circuit breakers. |
| Q152 | Partial failures, saga, outbox | Distributed transaction patterns, transactional outbox for reliable messaging, and compensation. |
| Q178 | Repository tests and Testcontainers | Running disposable real database containers (PostgreSQL) vs H2 false positives. |
| Q186 | Queue vs topic patterns | Point-to-point competing consumers vs publish-subscribe event broadcast patterns. |
| Q188 | Delivery semantics | At-most-once, at-least-once, exactly-once, and consumer idempotency requirements. |
| Q193 | Cache stampede | Thundering herd problem, mutual exclusion locking, TTL jitter, and cache pre-warming. |
| Q196 | Docker for Spring Boot | Multi-stage Dockerfiles, layered JARs (`extract`), unprivileged non-root users, and small base images. |
| Q197 | Health checks and graceful shutdown | Kubernetes liveness and readiness probes, `server.shutdown=graceful`, SIGTERM draining. |
| Q198 | Logs, metrics, tracing | The three observability pillars, RED metrics, trace correlation IDs via MDC, and OpenTelemetry. |
| Q199 | OOM, GC, thread exhaustion troubleshooting | Diagnosing heap exhaustion, container limits (`MaxRAMPercentage`), thread dumps, and leak triage. |
| Q200 | Incident troubleshooting runbook | Production incident response lifecycle: triage, mitigation, rollback, root cause analysis, and prevention. |


<a id="study-plan"></a>

# How to Use This Book

For each question, speak the short answer aloud without looking for 45–90 seconds. Then compare it with the text, explain one trade-off in your own words, and answer the follow-ups. Rebuild the code example in a small project, test suite, or SQL console when it involves concrete syntax or algorithms. Mark a question revised only when you can explain the edge cases, common pitfalls, and production implications. Prioritize conceptual clarity and architectural reasoning over verbatim memorization. All 200 questions across all 10 chapters are answered with a one-line headline, in-depth mechanics, code, follow-ups, mistakes to avoid, and a production perspective.

---

# 7-Day Interview Preparation Plan

Plan for roughly 90–120 focused minutes each day: 35–45 minutes reading, 25–30 minutes answering aloud, 25–30 minutes hands-on coding or SQL practice, and 10 minutes reviewing misses.

| Day | Chapters and Focus Topics | Spoken Drill & Hands-on Practice |
|---|---|---|
| **Day 1** | **Chapter 1: Core Java & OOP (Q001–Q030)**<br>OOP design, equals/hashCode, immutability, records, exceptions, Date/Time, Java 21 features | Speak Q001, Q005, Q009, Q011, Q012, Q021, and Q030 aloud.<br>Hands-on: Implement an immutable record with compact constructor validation and test equals/hashCode behavior. |
| **Day 2** | **Chapter 2: Collections, Generics & Streams (Q031–Q050)**<br>HashMap internals, ArrayList vs LinkedList, PECS, stream pipelines, collectors | Speak Q031, Q033, Q039, Q041, Q044, and Q049 aloud.<br>Hands-on: Code frequency counting, grouping by department, and multi-field sorting without an IDE. |
| **Day 3** | **Chapter 3: Concurrency, Async & JVM (Q051–Q075)**<br>JMM happens-before, thread pools, CompletableFuture, deadlocks, virtual threads, JVM memory areas | Speak Q051, Q052, Q057, Q059, Q061, Q066, and Q070 aloud.<br>Hands-on: Write a CompletableFuture pipeline with timeouts and fallback; inspect a simulated thread dump. |
| **Day 4** | **Chapter 4: Spring Framework & Spring Boot (Q076–Q105)**<br>Constructor injection, bean scopes, auto-configuration, MVC flow, @Transactional propagation, Spring Security | Speak Q076, Q077, Q080, Q083, Q086, Q089, and Q090 aloud.<br>Hands-on: Sketch a controller, service, repository, and transaction boundary; write a `@RestControllerAdvice` ProblemDetail handler. |
| **Day 5** | **Chapter 5: SQL, JPA & Hibernate (Q106–Q135)**<br>JOINs, indexing, ACID, isolation levels, optimistic locking, entity states, N+1 problem, OSIV | Speak Q107, Q109, Q111, Q112, Q114, Q120, and Q121 aloud.<br>Hands-on: Write a window function query and a JOIN FETCH query; explain an EXPLAIN ANALYZE plan. |
| **Day 6** | **Chapter 6: HTTP, REST & Microservices (Q136–Q160)**<br>**Chapter 7: Security (Q161–Q172)**<br>REST semantics, idempotency, error schemas, saga/outbox, JWT vs session, OWASP API Top 10 | Speak Q136, Q139, Q150, Q152, Q161, Q162, and Q165 aloud.<br>Hands-on: Design an idempotent payment API endpoint with retry backoff and authorization ownership checks. |
| **Day 7** | **Chapter 8: Testing & Debugging (Q173–Q185)**<br>**Chapter 9: Messaging & Caching (Q186–Q195)**<br>**Chapter 10: Production Operations (Q196–Q200)**<br>Test slices, Testcontainers, Kafka partitions, Redis caching, Docker, graceful shutdown, incident triage | Speak Q173, Q177, Q187, Q191, Q192, Q197, and Q200 aloud.<br>Hands-on: Rehearse an incident triage scenario for rising p99 latency; code an LRU cache or sliding-window rate limiter. Revisit weak areas across all days. |

---

### Spoken Practice Strategy
In technical interviews, knowing an answer is only half the battle — articulating it concisely under pressure is what secures the hire. Use the **STAR-L** or **Headline-First** technique:
1. **Headline (10 seconds):** Lead with the crisp one-line answer.
2. **Mechanism (30 seconds):** Explain how the JVM, framework, or database executes it under the hood.
3. **Trade-off / Gotcha (20 seconds):** Explain when this approach breaks, common edge cases, or what to avoid.
4. **Production Context (20 seconds):** Cite a concrete operational situation where this mattered.

<a id="mini-exercises"></a>

# Practical Mini-Exercises

Work first without looking at the outlines. These are tied to specific questions in the guide, so read the referenced answer only after you have attempted the exercise.

## 1. Stable value key (Q005, Q012, Q026)

Implement a key for `(tenantId, externalOrderId)` that can be used in a `HashMap`. Explain why a mutable field would be unsafe.

**Solution outline:** `record OrderKey(long tenantId, String externalOrderId) { OrderKey { Objects.requireNonNull(externalOrderId); } }` provides value equality because both components are immutable. Do not include a mutable order status in its hash.

## 2. First non-repeating character (Q049, Q182)

Return the first non-repeating UTF-16 `char` of an input string or an empty result. State how the solution changes for Unicode code points.

**Solution outline:** Traverse once into a `LinkedHashMap<Character, Integer>` using `merge(c, 1, Integer::sum)`; traverse entries in insertion order and return the first count of one. For code points, use `input.codePoints()` with `Integer` keys and return an `OptionalInt` or convert with `Character.toChars`. Clarify what counts as a character before coding.

## 3. Merge intervals (Q049, Q180)

Merge closed integer intervals, including intervals that touch at an endpoint. Input: `[1,3], [2,5], [8,9]`.

**Solution outline:** Sort by start with `Integer.compare`; maintain the latest merged interval. If `next.start <= current.end`, replace the end with `max(current.end, next.end)`; otherwise append a new interval. Result: `[1,5], [8,9]`. Decide whether adjacent non-overlapping intervals such as `[1,2]` and `[3,4]` should merge; for closed continuous intervals they do not overlap.

## 4. Monthly customers (Q108, Q181)

Given `orders(id, customer_id, placed_at, total, status)`, find the top five customers by completed-order total in January 2026. Assume `placed_at` is a UTC timestamp and `total` is numeric.

```sql
SELECT customer_id, SUM(total) AS monthly_total
FROM orders
WHERE status = 'COMPLETED'
  AND placed_at >= TIMESTAMPTZ '2026-01-01 00:00:00+00'
  AND placed_at <  TIMESTAMPTZ '2026-02-01 00:00:00+00'
GROUP BY customer_id
ORDER BY monthly_total DESC, customer_id ASC
LIMIT 5;
```

**Solution note:** The half-open range handles timestamp precision. Confirm how refunds and currencies are represented before calling this a revenue report.

## 5. Transaction proxy trap (Q088, Q089)

A public `create()` method calls `this.saveInTransaction()`, which is annotated `@Transactional`. Why might no transaction start?

**Solution outline:** In proxy-based Spring transaction management the internal call bypasses the proxy. Put the transaction boundary on the externally invoked public method or move the transactional operation to another injected bean. Test database behavior, not just the annotation's presence.

## 6. Slow endpoint after deployment (Q098, Q110, Q121, Q199)

An order list's p95 latency jumps after a deployment. Database CPU and query count rise, but JVM CPU stays normal. What do you check?

**Solution outline:** Compare traces and query counts before/after; inspect N+1 fetches, changed pagination and query plans; check connection-pool wait time and DB locks. Reproduce on representative data, mitigate by rollback if needed, then use a bounded projection/fetch plan and a regression test. Do not raise thread-pool size without identifying the bottleneck.

<a id="glossary"></a>

# Glossary

**ACID:** Database transaction properties: Atomicity, Consistency, Isolation, and Durability.  
**Anemic Domain Model:** An anti-pattern where domain entities contain only getters and setters, and all business rules reside in service classes.  
**Atomicity:** An operation is indivisible; either all of its steps succeed, or none do.  
**Backpressure:** Mechanism allowing a consumer to signal a producer to slow down rate of emission when overloaded.  
**Bean:** An object instantiated, assembled, and managed by the Spring IoC ApplicationContext.  
**Cache-aside:** Application reads from cache; on miss, fetches from database, populates cache, and returns data.  
**Circuit Breaker:** Resilience pattern that detects failures and encapsulates the logic of preventing an operation from constantly recurring during maintenance or downtime.  
**Dirty Checking:** Hibernate/JPA mechanism that compares managed entity states against their loaded snapshots to automatically emit SQL updates on flush.  
**DTO (Data Transfer Object):** Object carrying data between processes or application boundaries without business behavior.  
**ETag:** HTTP response header providing an entity tag / hash used for cache revalidation and optimistic concurrency control (`If-Match`).  
**Flush:** Synchronizing pending in-memory ORM entity changes with the database; does NOT necessarily commit the transaction.  
**Happens-before:** Java Memory Model relation that formally guarantees memory visibility and order between actions across threads.  
**Idempotency:** Property where repeating an operation multiple times produces the exact same system state as executing it once.  
**Isolation Level:** Database configuration (Read Uncommitted, Read Committed, Repeatable Read, Serializable) controlling concurrency anomalies.  
**JPA:** Jakarta Persistence API, the standard specification for ORM in modern Java / Spring Boot 3 applications.  
**JWT (JSON Web Token):** Open standard (RFC 7519) compact, URL-safe means of representing claims signed with HMAC or RSA; not encrypted by default.  
**N+1 Query Problem:** Performance defect where fetching $N$ parent records results in executing 1 initial query plus $N$ additional queries to fetch associated child entities.  
**Optimistic Locking:** Concurrency control mechanism using a version field (`@Version`) to detect conflicting concurrent updates without database row locks.  
**Outbox Pattern:** Architecture pattern where business data and outbound event messages are written to the same database in a single ACID transaction, then relayed asynchronously.  
**Pessimistic Locking:** Concurrency control acquiring exclusive database row locks (`SELECT ... FOR UPDATE`) to prevent concurrent updates during a transaction.  
**Persistence Context:** First-level cache and identity map managed by JPA `EntityManager` where all entities are tracked during a transaction.  
**Readiness Probe:** Kubernetes probe verifying that an application instance has completed warm-up and is capable of servicing incoming HTTP traffic.  
**Retry Budget:** Maximum percentage or count of requests that can be retries, preventing cascading retry storms from overwhelming failing downstream dependencies.  
**Safe Publication:** Initializing an object and making its reference visible to other threads such that the object's initialized state is guaranteed visible according to the JMM.  
**TTL (Time To Live):** Lifetime duration assigned to cached keys or messages after which they are automatically expired and evicted.  
**Virtual Thread:** Lightweight JVM-managed thread (Project Loom / Java 21) designed for high-concurrency blocking I/O without exhausting OS thread quotas.

---

# Coverage Checkpoint

The master question plan defines **Q001–Q200** across 10 structured chapters with question counts:
**30 / 20 / 25 / 30 / 30 / 25 / 12 / 13 / 10 / 5 = 200 Questions**.

All 200 questions across all 10 chapters are fully answered with interview-ready one-line summaries, technical mechanics, code examples, follow-up questions, pitfalls, and production perspectives.