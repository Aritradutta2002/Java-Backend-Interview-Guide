# Java Backend Interview Questions — 3-4 Years Experience

**200 primary (umbrella) questions**, each with **follow-up (child) questions** that interviewers typically drill into. Answer the main question first, then be ready for the follow-ups; that's how real panels go deeper.

## How to use this file
- Treat each **Q** as an opening question; the bullets are where the panel pushes next.
- At 3-4 years, interviewers expect: clear fundamentals, *why* behind decisions, trade-offs, and production experience (debugging, performance, failures).
- Always back answers with a real example from your project.

## Contents

| Section | Topic | Questions |
|---|---|---|
| A | Core Java & OOP | Q1-Q15 |
| B | Collections | Q16-Q30 |
| C | Multithreading & Concurrency | Q31-Q48 |
| D | JVM, Memory & GC | Q49-Q58 |
| E | Modern Java (8 to 21) | Q59-Q68 |
| F | Exceptions, Generics, I/O, Logging | Q69-Q74 |
| G | Spring Core | Q75-Q88 |
| H | Spring Boot | Q89-Q102 |
| I | REST & Spring MVC | Q103-Q116 |
| J | JPA & Hibernate | Q117-Q130 |
| K | SQL & PostgreSQL | Q131-Q144 |
| L | Microservices | Q145-Q160 |
| M | Messaging & Kafka | Q161-Q167 |
| N | Security | Q168-Q174 |
| O | Testing & Code Quality | Q175-Q180 |
| P | Design Principles & Patterns | Q181-Q186 |
| Q | System Design, Caching & Performance | Q187-Q192 |
| R | DevOps, Build & Tooling | Q193-Q197 |
| S | Project & Behavioral | Q198-Q200 |

---

## A. Core Java & OOP

**Q1. Explain the four pillars of OOP and how you apply them in real projects.**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Abstraction vs encapsulation: what is the actual difference?
- Compile-time vs runtime polymorphism; overloading vs overriding rules
- Composition vs inheritance: when do you prefer which?


**Q2. Abstract class vs interface (Java 8+): how do you choose?**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Default, static and private interface methods; how is the diamond problem resolved?
- Can an interface hold state? What is a functional interface?
- Which one do you use when designing a service/strategy layer?


**Q3. `==` vs `equals()` vs `hashCode()`: what is the contract?**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- Equality must be symmetric, transitive, consistent, and null-safe; equal objects must have equal hash codes. Do not mutate fields used by a hashed key.
- Equality must be symmetric, transitive, consistent, and null-safe; equal objects must have equal hash codes. Do not mutate fields used by a hashed key.
- Equality must be symmetric, transitive, consistent, and null-safe; equal objects must have equal hash codes. Do not mutate fields used by a hashed key.

- What breaks if you override `equals()` but not `hashCode()` and use the object as a HashMap key?
- How does `String.equals` work, and what is the String pool?
- Write a correct `equals`/`hashCode`; how do records handle it?


**Q4. Why is String immutable? String vs StringBuilder vs StringBuffer.**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- How many objects does `new String("a")` create? What does `intern()` do?
- Security, caching and thread-safety benefits of immutability
- Concatenation in loops: performance and compiler optimizations


**Q5. How do you create an immutable class?**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.

- Final fields, no setters, defensive copies of mutable members
- Records vs Lombok `@Value`
- Why are immutable objects ideal as map keys and in concurrent code?


**Q6. `final` vs `finally` vs `finalize()`.**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.

- Final reference vs mutability of the object it points to
- Does `finally` always run? What about `return` in `finally`, or `System.exit`?
- Why is `finalize()` deprecated? What replaces it (try-with-resources, Cleaner)?


**Q7. How does the `static` keyword work (blocks, methods, nested classes)?**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.

- Order of initialization with inheritance (static blocks, instance blocks, constructors)
- Can static methods be overridden? What is method hiding?
- Static nested vs inner class; memory leak risk from inner classes


**Q8. Method overloading vs overriding in depth.**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Covariant return types; overriding and checked exceptions
- Can you override private, static or final methods?
- How does the JVM pick an overload with `null` or boxed/varargs arguments?


**Q9. Is Java pass-by-value or pass-by-reference?**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.

- Demonstrate mutating an object vs reassigning the reference inside a method
- Design implications: returning modified copies vs in-place mutation
- Integer cache (-128 to 127) and `==` pitfalls


**Q10. Autoboxing/unboxing: what are the pitfalls?**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.

- NPE on unboxing `null`; `Long` vs `long` in entities and DTOs
- Performance cost of boxing in collections and streams; primitive streams
- Integer cache surprises with `==`


**Q11. Shallow copy vs deep copy; problems with `Cloneable`.**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.

- Why is `clone()` considered broken? Copy constructors as the alternative
- Deep copy via serialization: pros and cons
- Defensive copying in getters and constructors


**Q12. What is serialization? Explain `serialVersionUID` and `transient`.**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Security risks of Java deserialization
- Alternatives: JSON, Protobuf, Avro
- Serializable vs Externalizable; serialization and singletons


**Q13. Which methods of the `Object` class matter and why?**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- Equality must be symmetric, transitive, consistent, and null-safe; equal objects must have equal hash codes. Do not mutate fields used by a hashed key.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Equality must be symmetric, transitive, consistent, and null-safe; equal objects must have equal hash codes. Do not mutate fields used by a hashed key.

- `toString`, `equals`, `hashCode`, `clone`, `wait/notify`
- Why do `wait/notify` live on `Object`?
- `getClass()` vs `instanceof` in `equals`


**Q14. Anonymous classes vs lambdas vs inner classes.**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Meaning of `this` inside a lambda vs an anonymous class
- "Effectively final" variable capture; why the restriction?
- How are lambdas compiled (`invokedynamic`)?


**Q15. How do enums work and where have you used them?**

**Interview-ready answer:** Encapsulation hides mutable state behind invariants; abstraction exposes essential behavior; inheritance models genuine is-a relationships; polymorphism lets one contract have multiple implementations. Prefer composition, small interfaces, dependency injection, and tests.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Define ownership and cascade deliberately, keep session and transaction boundaries clear, and use fetch plans or projections to prevent N+1 queries.

- Enum singleton, `EnumMap`/`EnumSet`
- Enums with fields/abstract methods (strategy-like behavior)
- Persisting enums in JPA: `ORDINAL` vs `STRING` and why it matters


---

## B. Collections

**Q16. Explain HashMap internals.**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Hashing, buckets, load factor, resizing; why capacity is a power of 2
- Collision handling; treeification (threshold 8) and why
- Java 8 changes; null key handling; time complexity


**Q17. HashMap vs Hashtable vs ConcurrentHashMap vs `synchronizedMap`.**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- How does ConcurrentHashMap achieve concurrency in Java 8 (CAS + bin-level locking)?
- Why does ConcurrentHashMap reject null keys/values?
- Atomic operations: `compute`, `merge`, `putIfAbsent`


**Q18. ArrayList vs LinkedList: when use which?**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.

- Growth strategy and memory overhead
- Time complexity of add/get/remove at different positions
- Why LinkedList rarely wins in practice (cache locality)


**Q19. HashSet vs LinkedHashSet vs TreeSet.**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- Equality must be symmetric, transitive, consistent, and null-safe; equal objects must have equal hash codes. Do not mutate fields used by a hashed key.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Equality must be symmetric, transitive, consistent, and null-safe; equal objects must have equal hash codes. Do not mutate fields used by a hashed key.

- HashSet is backed by what? How are duplicates detected?
- Ordering guarantees and performance
- TreeSet with `compareTo` inconsistent with `equals`


**Q20. Comparable vs Comparator.**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Multi-field sorting with `Comparator.comparing().thenComparing()`
- Sort stability and TimSort
- Null-safe sorting (`nullsFirst`/`nullsLast`)


**Q21. Fail-fast vs fail-safe iterators; `ConcurrentModificationException`.**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- What is `modCount`? How do you safely remove while iterating (`Iterator.remove`, `removeIf`)?
- CopyOnWriteArrayList trade-offs
- Modifying a collection while streaming it


**Q22. How do you implement an LRU cache?**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- `LinkedHashMap` with `accessOrder` and `removeEldestEntry`
- Making it thread-safe
- Custom implementation with HashMap + doubly linked list; complexity


**Q23. `List.of` vs `Arrays.asList` vs `Collections.unmodifiableList`.**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Immutable vs unmodifiable view
- Which operations throw `UnsupportedOperationException`?
- `Arrays.asList` is backed by the array: what does that imply?


**Q24. Which collection would you pick for: frequency count, dedupe preserving order, top-K?**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Equality must be symmetric, transitive, consistent, and null-safe; equal objects must have equal hash codes. Do not mutate fields used by a hashed key.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.

- Frequency: `Map.merge` / `Collectors.groupingBy`
- Dedupe with order: `LinkedHashSet`
- Top-K with `PriorityQueue` (min-heap) and its complexity


**Q25. TreeMap and NavigableMap: use cases.**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Red-black tree complexity
- `floorKey`/`ceilingKey` for range lookups
- ConcurrentSkipListMap as the concurrent alternative


**Q26. WeakHashMap, IdentityHashMap, EnumMap: when are they useful?**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.

- Weak, soft and phantom references
- Memory leaks from static maps/caches
- Using weak references for caches: caveats


**Q27. What goes wrong when you use mutable objects as HashMap keys?**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Define ownership and cascade deliberately, keep session and transaction boundaries clear, and use fetch plans or projections to prevent N+1 queries.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Mutating a key after insertion: what happens to lookups?
- Using JPA entities as keys
- Best practices for key types


**Q28. BlockingQueue implementations and where they are used.**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- ArrayBlockingQueue vs LinkedBlockingQueue vs SynchronousQueue
- `put/take` vs `offer/poll` semantics
- Role of queues inside thread pools


**Q29. How does sorting work in Java (`Arrays.sort`, `Collections.sort`)?**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.

- Dual-pivot quicksort vs TimSort; stability
- Binary search preconditions
- How would you sort data too large to fit in memory (external sort)?


**Q30. Iterable, Iterator, ListIterator, Spliterator.**

**Interview-ready answer:** Hash-based collections use hashCode to select buckets and equals to resolve identity; choose collections by access pattern, ordering, uniqueness, mutability, and concurrency. State complexity and memory cost, then verify with representative data.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Implementing a custom `Iterable` so it works in for-each
- ListIterator capabilities
- Spliterator and parallel streams


---

## C. Multithreading & Concurrency

**Q31. Process vs thread; ways to create threads; Runnable vs Callable.**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.

- Thread lifecycle states
- Why implement Runnable instead of extending Thread?
- Future, FutureTask, and handling results/exceptions


**Q32. `synchronized` vs `ReentrantLock`.**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- Intrinsic locks/monitors; method vs block level
- `tryLock`, fairness, `Condition`
- ReadWriteLock and StampedLock: when helpful?


**Q33. Explain `volatile` and the Java Memory Model.**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- Visibility vs atomicity; happens-before
- Why is `count++` on a volatile field still unsafe?
- Double-checked locking: why is `volatile` needed?


**Q34. `wait/notify/notifyAll` vs `sleep` vs `join` vs `yield`.**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.

- Why must `wait` be called inside `synchronized`? Spurious wakeups
- Does `sleep` release the lock?
- Implement producer-consumer with wait/notify


**Q35. Deadlock, livelock and starvation.**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- Four necessary conditions for deadlock
- Detecting deadlock using thread dumps (`jstack`)
- Prevention: lock ordering, `tryLock` with timeout


**Q36. Explain ExecutorService and thread pool types.**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- ThreadPoolExecutor parameters: core/max size, queue, rejection policy
- Why avoid `Executors.newFixedThreadPool/newCachedThreadPool` in production?
- Sizing pools for CPU-bound vs IO-bound work
- `shutdown` vs `shutdownNow`; graceful shutdown


**Q37. CompletableFuture: how and when do you use it?**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- `thenApply` vs `thenCompose` vs `thenCombine`
- Exception handling: `exceptionally`, `handle`
- Which executor runs your stages? Calling multiple services in parallel with `allOf`


**Q38. Atomic classes and CAS.**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- ABA problem
- `AtomicLong` vs `LongAdder`
- Lock-free vs lock-based trade-offs


**Q39. How do you make a class thread-safe?**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- Stateless design, immutability, thread confinement, synchronization
- Are Spring singleton beans thread-safe?
- Check-then-act race conditions in service code


**Q40. ThreadLocal: use cases and leaks.**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- MDC logging and request context
- Why can ThreadLocal leak in thread pools? Role of `remove()`
- Alternatives (scoped values) and virtual-thread implications


**Q41. CountDownLatch vs CyclicBarrier vs Semaphore vs Phaser.**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Differences and reusability
- Rate-limiting/resource-limiting with Semaphore
- A real use case for each


**Q42. Fork/Join framework and parallel streams.**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Work-stealing algorithm
- Pitfalls: common pool sharing, blocking tasks
- When does `parallelStream()` hurt performance?


**Q43. Virtual threads (Java 21): what problem do they solve?**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- Platform vs virtual threads; best-fit workloads
- Pinning with `synchronized`/native calls
- Impact on thread pool sizing; Spring Boot 3.2 support


**Q44. Race condition vs data race; how do you debug concurrency bugs?**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Test behavior at the cheapest useful boundary; isolate external systems in unit tests and use deterministic integration or contract tests for wiring.

- Reproducing and detecting (thread dumps, tools)
- Idempotency under concurrent requests
- Testing concurrent code


**Q45. Thread interruption, daemon threads and cancellation.**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Correct handling of `InterruptedException`
- Daemon vs user threads and JVM shutdown
- Cancelling long-running tasks cleanly


**Q46. `synchronized` on static vs instance methods; object-level vs class-level lock.**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- Locking on `this` vs a private lock object
- Reentrancy
- Pitfalls of locking on String literals or boxed Integers


**Q47. Coding: implement a bounded blocking queue / producer-consumer / token-bucket rate limiter.**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- With `wait/notify`, then with `Lock/Condition`
- Using `BlockingQueue`
- Making the rate limiter thread-safe and fast


**Q48. Common concurrency problems in production services.**

**Interview-ready answer:** Use the narrowest concurrency primitive that makes the invariant obvious: immutable state, synchronization or locks for compound actions, atomics for independent variables, and executors for lifecycle. Define visibility, cancellation, and shutdown; measure contention.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- Thread pool exhaustion and DB connection pool starvation: symptoms and diagnosis
- Bulkheads and timeouts
- Tuning Tomcat threads and Hikari pool together


---

## D. JVM, Memory & GC

**Q49. Explain JVM architecture; JDK vs JRE vs JVM.**

**Interview-ready answer:** The JVM loads, verifies, and JIT-compiles bytecode. Objects normally live in the heap, thread stacks hold frames, and class metadata is separate; collectors reclaim unreachable objects. Diagnose with dumps, GC logs, profilers, and latency metrics.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Class loader subsystem, runtime data areas, execution engine
- Interpreter vs JIT; tiered compilation
- GraalVM native image / AOT: trade-offs


**Q50. JVM memory structure: heap, stack, metaspace.**

**Interview-ready answer:** The JVM loads, verifies, and JIT-compiles bytecode. Objects normally live in the heap, thread stacks hold frames, and class metadata is separate; collectors reclaim unreachable objects. Diagnose with dumps, GC logs, profilers, and latency metrics.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Young (Eden/Survivor) vs Old generation
- PermGen to Metaspace change
- What lives where: objects, locals, statics, class metadata


**Q51. How does garbage collection decide what to free?**

**Interview-ready answer:** The JVM loads, verifies, and JIT-compiles bytecode. Objects normally live in the heap, thread stacks hold frames, and class metadata is separate; collectors reclaim unreachable objects. Diagnose with dumps, GC logs, profilers, and latency metrics.

**Follow-up answer points:**
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.

- Reachability and GC roots
- Mark-sweep-compact; generational hypothesis
- Minor vs Major vs Full GC; stop-the-world pauses


**Q52. GC algorithms: Serial, Parallel, G1, ZGC, Shenandoah.**

**Interview-ready answer:** The JVM loads, verifies, and JIT-compiles bytecode. Objects normally live in the heap, thread stacks hold frames, and class metadata is separate; collectors reclaim unreachable objects. Diagnose with dumps, GC logs, profilers, and latency metrics.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.

- Default collector in Java 8 vs 17/21
- G1 regions and pause-time goals
- Choosing for a low-latency API vs a batch job


**Q53. Types of `OutOfMemoryError` and how to debug them.**

**Interview-ready answer:** The JVM loads, verifies, and JIT-compiles bytecode. Objects normally live in the heap, thread stacks hold frames, and class metadata is separate; collectors reclaim unreachable objects. Diagnose with dumps, GC logs, profilers, and latency metrics.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Heap space, Metaspace, GC overhead, unable to create native thread
- `-XX:+HeapDumpOnOutOfMemoryError`; analyzing with MAT/VisualVM
- Typical causes in real systems


**Q54. Can Java have memory leaks despite GC?**

**Interview-ready answer:** The JVM loads, verifies, and JIT-compiles bytecode. Objects normally live in the heap, thread stacks hold frames, and class metadata is separate; collectors reclaim unreachable objects. Diagnose with dumps, GC logs, profilers, and latency metrics.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.

- Common sources: static collections, listeners, ThreadLocal, unclosed resources
- How to detect with profilers/heap histograms
- Role of weak/soft references


**Q55. Class loading and the parent-delegation model.**

**Interview-ready answer:** The JVM loads, verifies, and JIT-compiles bytecode. Objects normally live in the heap, thread stacks hold frames, and class metadata is separate; collectors reclaim unreachable objects. Diagnose with dumps, GC logs, profilers, and latency metrics.

**Follow-up answer points:**
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Bootstrap, Platform, Application class loaders; custom class loaders
- `ClassNotFoundException` vs `NoClassDefFoundError`
- Class loader leaks in application servers


**Q56. JVM tuning flags and running Java in containers.**

**Interview-ready answer:** The JVM loads, verifies, and JIT-compiles bytecode. Objects normally live in the heap, thread stacks hold frames, and class metadata is separate; collectors reclaim unreachable objects. Diagnose with dumps, GC logs, profilers, and latency metrics.

**Follow-up answer points:**
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.

- `-Xms`, `-Xmx`, `-Xss`, `-XX:MaxRAMPercentage`
- Why set Xms = Xmx? Container memory limits and OOMKilled
- Enabling and reading GC logs


**Q57. StackOverflowError: causes and fixes.**

**Interview-ready answer:** The JVM loads, verifies, and JIT-compiles bytecode. Objects normally live in the heap, thread stacks hold frames, and class metadata is separate; collectors reclaim unreachable objects. Diagnose with dumps, GC logs, profilers, and latency metrics.

**Follow-up answer points:**
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Stack frames, `-Xss`
- Does Java optimize tail recursion?
- Converting deep recursion to iteration


**Q58. The service is slow / CPU is at 100% in production: how do you investigate?**

**Interview-ready answer:** The JVM loads, verifies, and JIT-compiles bytecode. Objects normally live in the heap, thread stacks hold frames, and class metadata is separate; collectors reclaim unreachable objects. Diagnose with dumps, GC logs, profilers, and latency metrics.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- `top -H`, `jstack`, thread dump analysis
- `jcmd`, JFR, async-profiler
- Distinguishing GC problems vs lock contention vs slow DB/downstream calls


---

## E. Modern Java (8 to 21)

**Q59. Lambdas and functional interfaces.**

**Interview-ready answer:** Use modern Java features when they improve clarity: streams for transformations, Optional for explicit absence, records for data carriers, and newer syntax only with supported tooling. Consider allocation, debugging, and compatibility.

**Follow-up answer points:**
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.

- `Predicate`, `Function`, `Consumer`, `Supplier`, `BiFunction`
- Custom `@FunctionalInterface`; the four types of method references
- Handling checked exceptions inside lambdas


**Q60. Streams API: intermediate vs terminal operations; lazy evaluation.**

**Interview-ready answer:** Use modern Java features when they improve clarity: streams for transformations, Optional for explicit absence, records for data carriers, and newer syntax only with supported tooling. Consider allocation, debugging, and compatibility.

**Follow-up answer points:**
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- `map` vs `flatMap`; `reduce`; short-circuiting operations
- Why does reusing a stream throw `IllegalStateException`?
- Using `peek` for debugging; stateful vs stateless operations


**Q61. Collectors: `groupingBy`, `partitioningBy`, `toMap`, `joining`.**

**Interview-ready answer:** Use modern Java features when they improve clarity: streams for transformations, Optional for explicit absence, records for data carriers, and newer syntax only with supported tooling. Consider allocation, debugging, and compatibility.

**Follow-up answer points:**
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- `toMap` duplicate-key exception and merge function
- Downstream collectors (`counting`, `summingInt`, `mapping`)
- Writing a custom collector


**Q62. Using `Optional` correctly.**

**Interview-ready answer:** Use modern Java features when they improve clarity: streams for transformations, Optional for explicit absence, records for data carriers, and newer syntax only with supported tooling. Consider allocation, debugging, and compatibility.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- `orElse` vs `orElseGet`; `map` vs `flatMap`
- Anti-patterns: Optional as field/parameter, calling `get()` blindly
- Optional as a repository return type


**Q63. Java 8 Date/Time API.**

**Interview-ready answer:** Use modern Java features when they improve clarity: streams for transformations, Optional for explicit absence, records for data carriers, and newer syntax only with supported tooling. Consider allocation, debugging, and compatibility.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- `LocalDate`, `LocalDateTime`, `ZonedDateTime`, `Instant`, `Duration`, `Period`
- Why is it better than `Date`/`SimpleDateFormat` (thread safety)?
- Handling time zones in backends; storing UTC


**Q64. Records, sealed classes and pattern matching (Java 14-21).**

**Interview-ready answer:** Use modern Java features when they improve clarity: streams for transformations, Optional for explicit absence, records for data carriers, and newer syntax only with supported tooling. Consider allocation, debugging, and compatibility.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Define ownership and cascade deliberately, keep session and transaction boundaries clear, and use fetch plans or projections to prevent N+1 queries.

- Record features, compact constructors, limitations
- Sealed hierarchies with switch pattern matching
- Records as DTOs; can they be JPA entities?


**Q65. Which LTS versions matter (8, 11, 17, 21) and what changed between them?**

**Interview-ready answer:** Use modern Java features when they improve clarity: streams for transformations, Optional for explicit absence, records for data carriers, and newer syntax only with supported tooling. Consider allocation, debugging, and compatibility.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- `var`, text blocks, switch expressions, `HttpClient`
- Migration pain points from Java 8 to 17/21 (removed APIs, `javax` to `jakarta`, illegal reflective access)
- How would you plan a large migration?


**Q66. Stream coding problems you should be able to solve on the spot.**

**Interview-ready answer:** Use modern Java features when they improve clarity: streams for transformations, Optional for explicit absence, records for data carriers, and newer syntax only with supported tooling. Consider allocation, debugging, and compatibility.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Group employees by department and compute average salary
- Find duplicates / first non-repeating character / character frequency
- Flatten nested lists; sort by multiple fields; second highest salary


**Q67. Functional programming style in Java.**

**Interview-ready answer:** Use modern Java features when they improve clarity: streams for transformations, Optional for explicit absence, records for data carriers, and newer syntax only with supported tooling. Consider allocation, debugging, and compatibility.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Function composition: `andThen`, `compose`
- Replacing if-else/strategy classes with lambdas
- Side effects in streams and why to avoid them


**Q68. Headline features of Java 21.**

**Interview-ready answer:** Use modern Java features when they improve clarity: streams for transformations, Optional for explicit absence, records for data carriers, and newer syntax only with supported tooling. Consider allocation, debugging, and compatibility.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.

- Virtual threads, sequenced collections, record patterns
- Structured concurrency / scoped values (preview status)
- Why Spring Boot 3 requires Java 17+


---

## F. Exceptions, Generics, I/O, Logging

**Q69. Checked vs unchecked exceptions; designing custom exceptions.**

**Interview-ready answer:** Make failure and data boundaries explicit: preserve causes, use checked exceptions only for recoverable decisions, parameterize generic APIs, close resources with try-with-resources, and log once at the boundary without secrets.

**Follow-up answer points:**
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.

- When to use each; exception translation and preserving the cause
- Swallowing exceptions: why it is an anti-pattern
- Exception strategy across layers (repository, service, controller)


**Q70. try-with-resources and `AutoCloseable`.**

**Interview-ready answer:** Make failure and data boundaries explicit: preserve causes, use checked exceptions only for recoverable decisions, parameterize generic APIs, close resources with try-with-resources, and log once at the boundary without secrets.

**Follow-up answer points:**
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- Order of closing; suppressed exceptions
- Multiple resources in one statement
- Typical leaks: connections, streams, executors


**Q71. Generics: type erasure, wildcards and PECS.**

**Interview-ready answer:** Make failure and data boundaries explicit: preserve causes, use checked exceptions only for recoverable decisions, parameterize generic APIs, close resources with try-with-resources, and log once at the boundary without secrets.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- `? extends` vs `? super`; when to use which
- Why can't you create generic arrays or do `instanceof List<String>`?
- Bounded type parameters and generic methods


**Q72. Reflection and annotations: how do frameworks use them?**

**Interview-ready answer:** Make failure and data boundaries explicit: preserve causes, use checked exceptions only for recoverable decisions, parameterize generic APIs, close resources with try-with-resources, and log once at the boundary without secrets.

**Follow-up answer points:**
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.

- Writing and processing a custom annotation
- Performance and security trade-offs of reflection
- JDK dynamic proxy vs CGLIB


**Q73. Java I/O vs NIO vs NIO.2; reading large files efficiently.**

**Interview-ready answer:** Make failure and data boundaries explicit: preserve causes, use checked exceptions only for recoverable decisions, parameterize generic APIs, close resources with try-with-resources, and log once at the boundary without secrets.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.

- Streams vs channels/buffers
- `Files.lines`, buffered readers, memory-mapped files
- Processing a 10 GB file with limited memory


**Q74. Logging best practices (SLF4J + Logback).**

**Interview-ready answer:** Make failure and data boundaries explicit: preserve causes, use checked exceptions only for recoverable decisions, parameterize generic APIs, close resources with try-with-resources, and log once at the boundary without secrets.

**Follow-up answer points:**
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.

- Log levels; parameterized logging vs string concatenation
- What never to log (PII, secrets, tokens); MDC correlation IDs
- Async appenders and logging overhead


---

## G. Spring Core

**Q75. What are IoC and Dependency Injection? Why use them?**

**Interview-ready answer:** Spring builds a context, creates beans, injects dependencies, and applies post-processors and proxies. Prefer constructor injection, explicit scopes, transactional boundaries, and testable configuration; understand proxy limitations such as self-invocation.

**Follow-up answer points:**
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.

- Constructor vs setter vs field injection: which one and why?
- BeanFactory vs ApplicationContext
- Circular dependencies: how do they arise and how do you fix them?


**Q76. Bean scopes in Spring.**

**Interview-ready answer:** Spring builds a context, creates beans, injects dependencies, and applies post-processors and proxies. Prefer constructor injection, explicit scopes, transactional boundaries, and testable configuration; understand proxy limitations such as self-invocation.

**Follow-up answer points:**
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- Injecting a prototype bean into a singleton: the problem and solutions
- Request/session scope and scoped proxies
- Is a singleton bean thread-safe?


**Q77. Spring bean lifecycle.**

**Interview-ready answer:** Spring builds a context, creates beans, injects dependencies, and applies post-processors and proxies. Prefer constructor injection, explicit scopes, transactional boundaries, and testable configuration; understand proxy limitations such as self-invocation.

**Follow-up answer points:**
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Define ownership and cascade deliberately, keep session and transaction boundaries clear, and use fetch plans or projections to prevent N+1 queries.

- `@PostConstruct`, `@PreDestroy`, `InitializingBean`
- `BeanPostProcessor` vs `BeanFactoryPostProcessor`
- Lazy initialization trade-offs


**Q78. `@Component` vs `@Service` vs `@Repository` vs `@Controller`; `@Bean` vs `@Component`.**

**Interview-ready answer:** Spring builds a context, creates beans, injects dependencies, and applies post-processors and proxies. Prefer constructor injection, explicit scopes, transactional boundaries, and testable configuration; understand proxy limitations such as self-invocation.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.

- `@Configuration` full vs lite mode
- Exception translation provided by `@Repository`
- How component scanning decides what to register


**Q79. How does `@Autowired` resolve dependencies?**

**Interview-ready answer:** Spring builds a context, creates beans, injects dependencies, and applies post-processors and proxies. Prefer constructor injection, explicit scopes, transactional boundaries, and testable configuration; understand proxy limitations such as self-invocation.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Define ownership and cascade deliberately, keep session and transaction boundaries clear, and use fetch plans or projections to prevent N+1 queries.

- `@Qualifier`, `@Primary`; multiple implementations of one interface
- Injecting `List<T>` / `Map<String,T>` of beans
- Optional dependencies, `@Lazy`, `ObjectProvider`


**Q80. Spring AOP concepts.**

**Interview-ready answer:** Spring builds a context, creates beans, injects dependencies, and applies post-processors and proxies. Prefer constructor injection, explicit scopes, transactional boundaries, and testable configuration; understand proxy limitations such as self-invocation.

**Follow-up answer points:**
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Keep the transaction short and explicit; choose isolation and retry behavior for consistency, and make external effects idempotent.

- Join point, pointcut, advice types, aspect
- JDK proxy vs CGLIB; limitations with final classes/methods
- Real use cases: logging, auditing, transactions, metrics


**Q81. Why does self-invocation break `@Transactional`, `@Async` and `@Cacheable`?**

**Interview-ready answer:** Spring builds a context, creates beans, injects dependencies, and applies post-processors and proxies. Prefer constructor injection, explicit scopes, transactional boundaries, and testable configuration; understand proxy limitations such as self-invocation.

**Follow-up answer points:**
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Do not expose mutable internals; use final state and defensive copies. Immutability simplifies sharing and hash-based use.

- The proxy mechanism explained
- Fixes: refactor into another bean, self-injection, AspectJ weaving
- Visibility rules for proxied methods (private/final)


**Q82. `@Transactional` in depth.**

**Interview-ready answer:** Spring builds a context, creates beans, injects dependencies, and applies post-processors and proxies. Prefer constructor injection, explicit scopes, transactional boundaries, and testable configuration; understand proxy limitations such as self-invocation.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Keep the transaction short and explicit; choose isolation and retry behavior for consistency, and make external effects idempotent.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Keep the transaction short and explicit; choose isolation and retry behavior for consistency, and make external effects idempotent.

- Propagation: `REQUIRED`, `REQUIRES_NEW`, `NESTED`, `SUPPORTS`
- Rollback rules: default rollback only for unchecked exceptions; `rollbackFor`
- `readOnly = true`: what does it really do?
- Pitfalls: swallowed exceptions, long transactions, external calls inside transactions


**Q83. Spring application events.**

**Interview-ready answer:** Spring builds a context, creates beans, injects dependencies, and applies post-processors and proxies. Prefer constructor injection, explicit scopes, transactional boundaries, and testable configuration; understand proxy limitations such as self-invocation.

**Follow-up answer points:**
- Keep the transaction short and explicit; choose isolation and retry behavior for consistency, and make external effects idempotent.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.

- `@EventListener` vs `@TransactionalEventListener` (after commit)
- Sync vs async listeners
- Using events to decouple modules in a modular monolith vs using Kafka


**Q84. Profiles and externalized configuration.**

**Interview-ready answer:** Spring builds a context, creates beans, injects dependencies, and applies post-processors and proxies. Prefer constructor injection, explicit scopes, transactional boundaries, and testable configuration; understand proxy limitations such as self-invocation.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.

- `@Value` vs `@ConfigurationProperties`
- Property source precedence; config per environment
- Handling secrets; Spring Cloud Config


**Q85. Scheduling with `@Scheduled`.**

**Interview-ready answer:** Spring builds a context, creates beans, injects dependencies, and applies post-processors and proxies. Prefer constructor injection, explicit scopes, transactional boundaries, and testable configuration; understand proxy limitations such as self-invocation.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- `fixedRate` vs `fixedDelay` vs `cron`
- Running a job only once across multiple instances (ShedLock, Quartz)
- Scheduler thread pool and long-running jobs


**Q86. `@Async` and task executors.**

**Interview-ready answer:** Spring builds a context, creates beans, injects dependencies, and applies post-processors and proxies. Prefer constructor injection, explicit scopes, transactional boundaries, and testable configuration; understand proxy limitations such as self-invocation.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.

- Enabling async; return types (`void`, `Future`, `CompletableFuture`)
- Default executor pitfalls; configuring a custom pool
- Exception handling and context propagation (security context, MDC)


**Q87. Spring Cache abstraction.**

**Interview-ready answer:** Spring builds a context, creates beans, injects dependencies, and applies post-processors and proxies. Prefer constructor injection, explicit scopes, transactional boundaries, and testable configuration; understand proxy limitations such as self-invocation.

**Follow-up answer points:**
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.

- `@Cacheable`, `@CachePut`, `@CacheEvict`; key generation
- Providers (Caffeine, Redis); TTL and eviction
- Cache stampede and stale data handling


**Q88. Bean Validation in Spring.**

**Interview-ready answer:** Spring builds a context, creates beans, injects dependencies, and applies post-processors and proxies. Prefer constructor injection, explicit scopes, transactional boundaries, and testable configuration; understand proxy limitations such as self-invocation.

**Follow-up answer points:**
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.

- `@Valid` vs `@Validated`; common constraint annotations
- Writing a custom constraint validator
- Handling `MethodArgumentNotValidException` and returning clean errors


---

## H. Spring Boot

**Q89. What does `@SpringBootApplication` do? How does auto-configuration work?**

**Interview-ready answer:** Spring Boot provides convention-based auto-configuration, starters, externalized configuration, embedded servers, and production endpoints. Keep configuration typed and environment-specific, expose only safe actuator endpoints, and verify health and graceful shutdown.

**Follow-up answer points:**
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- `@EnableAutoConfiguration`, `AutoConfiguration.imports` (formerly `spring.factories`)
- `@ConditionalOnClass`, `@ConditionalOnMissingBean`
- Debugging with the conditions report (`--debug`)


**Q90. Spring Boot startup sequence.**

**Interview-ready answer:** Spring Boot provides convention-based auto-configuration, starters, externalized configuration, embedded servers, and production endpoints. Keep configuration typed and environment-specific, expose only safe actuator endpoints, and verify health and graceful shutdown.

**Follow-up answer points:**
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Define ownership and cascade deliberately, keep session and transaction boundaries clear, and use fetch plans or projections to prevent N+1 queries.

- What happens inside `SpringApplication.run`; `CommandLineRunner` vs `ApplicationRunner`
- Embedded Tomcat vs Jetty/Undertow
- Reducing startup time (lazy init, AOT, CDS)


**Q91. Starters and dependency management.**

**Interview-ready answer:** Spring Boot provides convention-based auto-configuration, starters, externalized configuration, embedded servers, and production endpoints. Keep configuration typed and environment-specific, expose only safe actuator endpoints, and verify health and graceful shutdown.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Parent POM / BOM; overriding managed versions
- Excluding transitive dependencies; resolving version conflicts
- Creating a custom starter


**Q92. Spring Boot Actuator and monitoring.**

**Interview-ready answer:** Spring Boot provides convention-based auto-configuration, starters, externalized configuration, embedded servers, and production endpoints. Keep configuration typed and environment-specific, expose only safe actuator endpoints, and verify health and graceful shutdown.

**Follow-up answer points:**
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Health, metrics, info endpoints; custom `HealthIndicator`
- Securing actuator endpoints
- Micrometer + Prometheus + Grafana


**Q93. Global exception handling in Boot REST APIs.**

**Interview-ready answer:** Spring Boot provides convention-based auto-configuration, starters, externalized configuration, embedded servers, and production endpoints. Keep configuration typed and environment-specific, expose only safe actuator endpoints, and verify health and graceful shutdown.

**Follow-up answer points:**
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.

- `@ControllerAdvice` / `@ExceptionHandler`; `ProblemDetail` (RFC 7807)
- Designing a consistent error response model
- Mapping validation and domain errors to HTTP status codes


**Q94. Spring Boot 2 to 3 migration: what changed?**

**Interview-ready answer:** Spring Boot provides convention-based auto-configuration, starters, externalized configuration, embedded servers, and production endpoints. Keep configuration typed and environment-specific, expose only safe actuator endpoints, and verify health and graceful shutdown.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.

- `javax` to `jakarta`; Java 17 baseline
- Hibernate 6 and Spring Security 6 changes (`WebSecurityConfigurerAdapter` removed)
- Observability changes (Micrometer Tracing replacing Sleuth)


**Q95. Configuring the datasource and HikariCP.**

**Interview-ready answer:** Spring Boot provides convention-based auto-configuration, starters, externalized configuration, embedded servers, and production endpoints. Keep configuration typed and environment-specific, expose only safe actuator endpoints, and verify health and graceful shutdown.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- `maximumPoolSize`, timeouts, leak detection
- How to size the pool; symptoms of pool exhaustion
- Multiple datasources in one application


**Q96. Logging configuration and structured logging in Boot.**

**Interview-ready answer:** Spring Boot provides convention-based auto-configuration, starters, externalized configuration, embedded servers, and production endpoints. Keep configuration typed and environment-specific, expose only safe actuator endpoints, and verify health and graceful shutdown.

**Follow-up answer points:**
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.

- Per-profile Logback config; log levels at runtime
- Correlation/trace IDs across requests
- JSON logs for ELK/Loki


**Q97. Embedded server tuning.**

**Interview-ready answer:** Spring Boot provides convention-based auto-configuration, starters, externalized configuration, embedded servers, and production endpoints. Keep configuration typed and environment-specific, expose only safe actuator endpoints, and verify health and graceful shutdown.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.

- Tomcat max threads, max connections, accept count
- Graceful shutdown
- Timeouts, compression, HTTP/2


**Q98. Database migrations with Flyway/Liquibase.**

**Interview-ready answer:** Spring Boot provides convention-based auto-configuration, starters, externalized configuration, embedded servers, and production endpoints. Keep configuration typed and environment-specific, expose only safe actuator endpoints, and verify health and graceful shutdown.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Keep the transaction short and explicit; choose isolation and retry behavior for consistency, and make external effects idempotent.

- Versioned vs repeatable migrations
- Zero-downtime and backward-compatible schema changes
- Rollback strategy


**Q99. Packaging and deploying Boot apps.**

**Interview-ready answer:** Spring Boot provides convention-based auto-configuration, starters, externalized configuration, embedded servers, and production endpoints. Keep configuration typed and environment-specific, expose only safe actuator endpoints, and verify health and graceful shutdown.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Fat JAR structure vs WAR
- Layered JARs and Docker image optimization; buildpacks
- Externalizing configuration in containers


**Q100. Managing secrets and sensitive configuration.**

**Interview-ready answer:** Spring Boot provides convention-based auto-configuration, starters, externalized configuration, embedded servers, and production endpoints. Keep configuration typed and environment-specific, expose only safe actuator endpoints, and verify health and graceful shutdown.

**Follow-up answer points:**
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.

- Env vars, Vault, Kubernetes Secrets; never committing secrets
- Encrypted properties
- Secret rotation without redeploy


**Q101. RestTemplate vs WebClient vs RestClient vs Feign.**

**Interview-ready answer:** Spring Boot provides convention-based auto-configuration, starters, externalized configuration, embedded servers, and production endpoints. Keep configuration typed and environment-specific, expose only safe actuator endpoints, and verify health and graceful shutdown.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Test behavior at the cheapest useful boundary; isolate external systems in unit tests and use deterministic integration or contract tests for wiring.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.

- Blocking vs non-blocking; timeout configuration
- Retry, circuit breaker integration
- Error handling and interceptors


**Q102. Spring WebFlux / reactive programming: when to use it?**

**Interview-ready answer:** Spring Boot provides convention-based auto-configuration, starters, externalized configuration, embedded servers, and production endpoints. Keep configuration typed and environment-specific, expose only safe actuator endpoints, and verify health and graceful shutdown.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- `Mono`/`Flux`; backpressure
- Reactive vs virtual threads
- Pitfalls: blocking calls, JDBC in a reactive stack


---

## I. REST & Spring MVC

**Q103. Walk through the Spring MVC request flow.**

**Interview-ready answer:** A REST API models resources with stable URLs, uses HTTP methods and status codes consistently, validates input, returns documented representations, and defines error and compatibility behavior. Make retries safe through idempotency, authorize operations, and observe failures.

**Follow-up answer points:**
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.

- `DispatcherServlet`, `HandlerMapping`, `HttpMessageConverter`
- Filter vs Interceptor vs AOP: differences and ordering
- Role of the servlet container


**Q104. `@RestController` vs `@Controller`; request binding annotations.**

**Interview-ready answer:** A REST API models resources with stable URLs, uses HTTP methods and status codes consistently, validates input, returns documented representations, and defines error and compatibility behavior. Make retries safe through idempotency, authorize operations, and observe failures.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.

- `@RequestParam` vs `@PathVariable` vs `@RequestBody`
- Content negotiation and Jackson customization
- Form data vs JSON binding


**Q105. REST principles and good API design.**

**Interview-ready answer:** A REST API models resources with stable URLs, uses HTTP methods and status codes consistently, validates input, returns documented representations, and defines error and compatibility behavior. Make retries safe through idempotency, authorize operations, and observe failures.

**Follow-up answer points:**
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Resource naming and HTTP verb semantics
- Safe and idempotent methods: PUT vs POST vs PATCH
- HATEOAS: is it used in practice?


**Q106. HTTP status codes: which one when?**

**Interview-ready answer:** A REST API models resources with stable URLs, uses HTTP methods and status codes consistently, validates input, returns documented representations, and defines error and compatibility behavior. Make retries safe through idempotency, authorize operations, and observe failures.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Test behavior at the cheapest useful boundary; isolate external systems in unit tests and use deterministic integration or contract tests for wiring.

- 200/201/202/204; 400/401/403/404/409/422; 429; 500/502/503/504
- 401 vs 403
- Designing the error contract


**Q107. API versioning strategies.**

**Interview-ready answer:** A REST API models resources with stable URLs, uses HTTP methods and status codes consistently, validates input, returns documented representations, and defines error and compatibility behavior. Make retries safe through idempotency, authorize operations, and observe failures.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- URI vs header vs media-type versioning
- Backward compatibility and deprecation policy
- What counts as a breaking change?


**Q108. Pagination, filtering and sorting for large datasets.**

**Interview-ready answer:** A REST API models resources with stable URLs, uses HTTP methods and status codes consistently, validates input, returns documented representations, and defines error and compatibility behavior. Make retries safe through idempotency, authorize operations, and observe failures.

**Follow-up answer points:**
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Offset vs cursor/keyset pagination
- Spring Data `Pageable`; cost of deep offsets and total counts
- Consistent results while data changes


**Q109. Idempotency in APIs.**

**Interview-ready answer:** A REST API models resources with stable URLs, uses HTTP methods and status codes consistently, validates input, returns documented representations, and defines error and compatibility behavior. Make retries safe through idempotency, authorize operations, and observe failures.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Idempotency keys for payment-like POST requests
- Implementation using a unique constraint or Redis
- Safe client retries and duplicate detection


**Q110. DTO vs Entity; mapping between them.**

**Interview-ready answer:** A REST API models resources with stable URLs, uses HTTP methods and status codes consistently, validates input, returns documented representations, and defines error and compatibility behavior. Make retries safe through idempotency, authorize operations, and observe failures.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Define ownership and cascade deliberately, keep session and transaction boundaries clear, and use fetch plans or projections to prevent N+1 queries.

- Why not expose entities directly?
- MapStruct vs ModelMapper
- Lazy-loading serialization issues and Jackson infinite recursion


**Q111. Servlet filters and interceptors in practice.**

**Interview-ready answer:** A REST API models resources with stable URLs, uses HTTP methods and status codes consistently, validates input, returns documented representations, and defines error and compatibility behavior. Make retries safe through idempotency, authorize operations, and observe failures.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.

- `OncePerRequestFilter`; filter ordering
- Reading the request body twice
- Request logging and correlation ID injection


**Q112. File upload/download and large payloads.**

**Interview-ready answer:** A REST API models resources with stable URLs, uses HTTP methods and status codes consistently, validates input, returns documented representations, and defines error and compatibility behavior. Make retries safe through idempotency, authorize operations, and observe failures.

**Follow-up answer points:**
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.

- `MultipartFile` limits; streaming vs buffering in memory
- Pre-signed URLs with S3-like storage
- Timeouts and memory pressure


**Q113. CORS, rate limiting and API abuse protection.**

**Interview-ready answer:** A REST API models resources with stable URLs, uses HTTP methods and status codes consistently, validates input, returns documented representations, and defines error and compatibility behavior. Make retries safe through idempotency, authorize operations, and observe failures.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.

- Why CORS exists; what is a preflight request?
- Rate-limiting approaches (token bucket, API gateway)
- CSRF relevance for REST APIs


**Q114. Design a robust REST API for an Order service end to end.**

**Interview-ready answer:** A REST API models resources with stable URLs, uses HTTP methods and status codes consistently, validates input, returns documented representations, and defines error and compatibility behavior. Make retries safe through idempotency, authorize operations, and observe failures.

**Follow-up answer points:**
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.

- Resource model, endpoints, payloads, error handling
- Concurrency, idempotency and versioning
- Documentation with OpenAPI/Swagger


**Q115. Handling long-running operations in APIs.**

**Interview-ready answer:** A REST API models resources with stable URLs, uses HTTP methods and status codes consistently, validates input, returns documented representations, and defines error and compatibility behavior. Make retries safe through idempotency, authorize operations, and observe failures.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.

- `202 Accepted` + polling or webhooks
- SSE / WebSocket alternatives
- Timeouts and job status tracking


**Q116. Jackson serialization: customization and pitfalls.**

**Interview-ready answer:** A REST API models resources with stable URLs, uses HTTP methods and status codes consistently, validates input, returns documented representations, and defines error and compatibility behavior. Make retries safe through idempotency, authorize operations, and observe failures.

**Follow-up answer points:**
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.

- `@JsonIgnore`, `@JsonProperty`, `@JsonInclude`, custom (de)serializers
- Date/time formats; unknown-property handling
- Polymorphic deserialization security risks


---

## J. JPA & Hibernate

**Q117. JPA vs Hibernate vs Spring Data JPA.**

**Interview-ready answer:** JPA maps entities through a persistence context. Keep transactions explicit, model ownership and fetch plans deliberately, avoid lazy-loading outside a transaction and N+1 queries, and use migrations, constraints, and indexes.

**Follow-up answer points:**
- Define ownership and cascade deliberately, keep session and transaction boundaries clear, and use fetch plans or projections to prevent N+1 queries.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.

- `EntityManager`, `SessionFactory`, repository abstraction
- Derived queries, `@Query`, Specifications
- When to drop to native SQL or `JdbcTemplate`


**Q118. Entity lifecycle and the persistence context.**

**Interview-ready answer:** JPA maps entities through a persistence context. Keep transactions explicit, model ownership and fetch plans deliberately, avoid lazy-loading outside a transaction and N+1 queries, and use migrations, constraints, and indexes.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Transient, managed, detached, removed states
- First-level cache, flush modes, dirty checking
- `persist` vs `merge`; what does `save()` actually do?


**Q119. What is the N+1 problem and how do you fix it?**

**Interview-ready answer:** JPA maps entities through a persistence context. Keep transactions explicit, model ownership and fetch plans deliberately, avoid lazy-loading outside a transaction and N+1 queries, and use migrations, constraints, and indexes.

**Follow-up answer points:**
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- How to detect it (SQL logs, Hibernate statistics)
- `JOIN FETCH`, `@EntityGraph`, `@BatchSize`
- DTO projections as an alternative


**Q120. Lazy vs eager loading; `LazyInitializationException`.**

**Interview-ready answer:** JPA maps entities through a persistence context. Keep transactions explicit, model ownership and fetch plans deliberately, avoid lazy-loading outside a transaction and N+1 queries, and use migrations, constraints, and indexes.

**Follow-up answer points:**
- Define ownership and cascade deliberately, keep session and transaction boundaries clear, and use fetch plans or projections to prevent N+1 queries.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Default fetch type per association
- Open Session in View: pros and cons
- Strategies to fix it properly


**Q121. Mapping relationships: `@OneToMany`, `@ManyToOne`, `@ManyToMany`.**

**Interview-ready answer:** JPA maps entities through a persistence context. Keep transactions explicit, model ownership and fetch plans deliberately, avoid lazy-loading outside a transaction and N+1 queries, and use migrations, constraints, and indexes.

**Follow-up answer points:**
- Define ownership and cascade deliberately, keep session and transaction boundaries clear, and use fetch plans or projections to prevent N+1 queries.
- Equality must be symmetric, transitive, consistent, and null-safe; equal objects must have equal hash codes. Do not mutate fields used by a hashed key.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.

- Owning side and `mappedBy`; cascade types and `orphanRemoval`
- Keeping bidirectional associations in sync; `equals/hashCode` for entities
- Join tables with extra columns


**Q122. Inheritance mapping strategies.**

**Interview-ready answer:** JPA maps entities through a persistence context. Keep transactions explicit, model ownership and fetch plans deliberately, avoid lazy-loading outside a transaction and N+1 queries, and use migrations, constraints, and indexes.

**Follow-up answer points:**
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- `SINGLE_TABLE` vs `JOINED` vs `TABLE_PER_CLASS` trade-offs
- `@MappedSuperclass` vs `@Embeddable`
- Impact on queries and performance


**Q123. Hibernate caching.**

**Interview-ready answer:** JPA maps entities through a persistence context. Keep transactions explicit, model ownership and fetch plans deliberately, avoid lazy-loading outside a transaction and N+1 queries, and use migrations, constraints, and indexes.

**Follow-up answer points:**
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.

- L1 vs L2 vs query cache
- Providers and invalidation; when not to use L2
- Consistency in clustered deployments


**Q124. Optimistic vs pessimistic locking in JPA.**

**Interview-ready answer:** JPA maps entities through a persistence context. Keep transactions explicit, model ownership and fetch plans deliberately, avoid lazy-loading outside a transaction and N+1 queries, and use migrations, constraints, and indexes.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- `@Version`; handling `OptimisticLockException` and retries
- `PESSIMISTIC_WRITE`, `SELECT ... FOR UPDATE`, `SKIP LOCKED`
- Choosing based on contention level


**Q125. Batch inserts/updates and bulk operations.**

**Interview-ready answer:** JPA maps entities through a persistence context. Keep transactions explicit, model ownership and fetch plans deliberately, avoid lazy-loading outside a transaction and N+1 queries, and use migrations, constraints, and indexes.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.

- `hibernate.jdbc.batch_size`; why `IDENTITY` blocks batching
- `saveAll` pitfalls; `flush()` and `clear()` in loops
- Bulk JPQL updates; JDBC batch / Postgres `COPY` for huge loads


**Q126. Primary key generation strategies.**

**Interview-ready answer:** JPA maps entities through a persistence context. Keep transactions explicit, model ownership and fetch plans deliberately, avoid lazy-loading outside a transaction and N+1 queries, and use migrations, constraints, and indexes.

**Follow-up answer points:**
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- `IDENTITY` vs `SEQUENCE` vs UUID: performance and index impact
- Postgres sequences and `allocationSize`
- Distributed ID options (Snowflake, ULID)


**Q127. JPQL vs Criteria API vs native queries; projections.**

**Interview-ready answer:** JPA maps entities through a persistence context. Keep transactions explicit, model ownership and fetch plans deliberately, avoid lazy-loading outside a transaction and N+1 queries, and use migrations, constraints, and indexes.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.

- Interface and DTO projections
- Building dynamic queries (Specifications)
- SQL injection safety in each approach


**Q128. Soft delete and auditing.**

**Interview-ready answer:** JPA maps entities through a persistence context. Keep transactions explicit, model ownership and fetch plans deliberately, avoid lazy-loading outside a transaction and N+1 queries, and use migrations, constraints, and indexes.

**Follow-up answer points:**
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- `@SQLDelete` / `@Where` / `@Filter`
- Spring Data auditing: `@CreatedDate`, `@LastModifiedBy`
- Unique constraints with soft-deleted rows


**Q129. Hibernate performance tuning checklist.**

**Interview-ready answer:** JPA maps entities through a persistence context. Keep transactions explicit, model ownership and fetch plans deliberately, avoid lazy-loading outside a transaction and N+1 queries, and use migrations, constraints, and indexes.

**Follow-up answer points:**
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Define ownership and cascade deliberately, keep session and transaction boundaries clear, and use fetch plans or projections to prevent N+1 queries.

- SQL logging, statistics, slow query log
- Fetch strategies, indexes, projections, pagination
- `MultipleBagFetchException` and Cartesian product issues


**Q130. Schema design: how do you design tables for a new module (e.g., Orders)?**

**Interview-ready answer:** JPA maps entities through a persistence context. Keep transactions explicit, model ownership and fetch plans deliberately, avoid lazy-loading outside a transaction and N+1 queries, and use migrations, constraints, and indexes.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Normalization (1NF-3NF) and deliberate denormalization
- Constraints, indexes and naming conventions
- Evolving the schema without downtime


---

## K. SQL & PostgreSQL

**Q131. SQL joins and classic query problems.**

**Interview-ready answer:** Relational design uses keys, constraints, transactions, and indexes for correctness. Write parameterized queries, inspect EXPLAIN plans, index actual predicates and joins, and choose isolation and locking based on contention.

**Follow-up answer points:**
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- INNER / LEFT / RIGHT / FULL / CROSS / SELF join
- Nth highest salary; find duplicates; employees without a department
- `NOT IN` vs `NOT EXISTS` (the NULL trap)


**Q132. GROUP BY, HAVING and window functions.**

**Interview-ready answer:** Relational design uses keys, constraints, transactions, and indexes for correctness. Write parameterized queries, inspect EXPLAIN plans, index actual predicates and joins, and choose isolation and locking based on contention.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- `ROW_NUMBER` vs `RANK` vs `DENSE_RANK`; `LAG`/`LEAD`
- Running totals and top-N per group
- `WHERE` vs `HAVING`


**Q133. How do indexes work and when should you add one?**

**Interview-ready answer:** Relational design uses keys, constraints, transactions, and indexes for correctness. Write parameterized queries, inspect EXPLAIN plans, index actual predicates and joins, and choose isolation and locking based on contention.

**Follow-up answer points:**
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.

- B-tree structure; clustered vs non-clustered (Postgres heap)
- Composite indexes, leftmost prefix rule, covering indexes
- Write overhead; why an index might not be used


**Q134. PostgreSQL index types.**

**Interview-ready answer:** Relational design uses keys, constraints, transactions, and indexes for correctness. Write parameterized queries, inspect EXPLAIN plans, index actual predicates and joins, and choose isolation and locking based on contention.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.

- B-tree, Hash, GIN, GiST, BRIN
- Partial and expression indexes; JSONB and full-text search
- `CREATE INDEX CONCURRENTLY`


**Q135. Query optimization with `EXPLAIN ANALYZE`.**

**Interview-ready answer:** Relational design uses keys, constraints, transactions, and indexes for correctness. Write parameterized queries, inspect EXPLAIN plans, index actual predicates and joins, and choose isolation and locking based on contention.

**Follow-up answer points:**
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.

- Seq scan vs index scan vs bitmap scan; join algorithms
- Statistics, `ANALYZE`, planner misestimates
- Walk through fixing a slow query step by step


**Q136. ACID and transaction isolation levels.**

**Interview-ready answer:** Relational design uses keys, constraints, transactions, and indexes for correctness. Write parameterized queries, inspect EXPLAIN plans, index actual predicates and joins, and choose isolation and locking based on contention.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Dirty, non-repeatable and phantom reads
- Postgres default `READ COMMITTED`; how MVCC works
- `SERIALIZABLE` and retry handling


**Q137. Locks and deadlocks in the database.**

**Interview-ready answer:** Relational design uses keys, constraints, transactions, and indexes for correctness. Write parameterized queries, inspect EXPLAIN plans, index actual predicates and joins, and choose isolation and locking based on contention.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- Row-level locks, `SELECT FOR UPDATE`, `SKIP LOCKED`
- Detecting and resolving deadlocks; consistent lock ordering
- Advisory locks


**Q138. MVCC and VACUUM in PostgreSQL.**

**Interview-ready answer:** Relational design uses keys, constraints, transactions, and indexes for correctness. Write parameterized queries, inspect EXPLAIN plans, index actual predicates and joins, and choose isolation and locking based on contention.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Keep the transaction short and explicit; choose isolation and retry behavior for consistency, and make external effects idempotent.
- Keep the transaction short and explicit; choose isolation and retry behavior for consistency, and make external effects idempotent.

- Dead tuples, bloat, autovacuum
- Transaction ID wraparound
- Impact of long-running transactions


**Q139. SQL vs NoSQL: how do you choose?**

**Interview-ready answer:** Relational design uses keys, constraints, transactions, and indexes for correctness. Write parameterized queries, inspect EXPLAIN plans, index actual predicates and joins, and choose isolation and locking based on contention.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.

- CAP theorem and consistency models
- JSONB in Postgres vs a document store
- Polyglot persistence: Redis, Elasticsearch, Cassandra use cases


**Q140. Connection pooling and database scalability.**

**Interview-ready answer:** Relational design uses keys, constraints, transactions, and indexes for correctness. Write parameterized queries, inspect EXPLAIN plans, index actual predicates and joins, and choose isolation and locking based on contention.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.

- PgBouncer and `max_connections`
- Read replicas and replication lag
- Partitioning vs sharding


**Q141. Table partitioning and archival of large tables.**

**Interview-ready answer:** Relational design uses keys, constraints, transactions, and indexes for correctness. Write parameterized queries, inspect EXPLAIN plans, index actual predicates and joins, and choose isolation and locking based on contention.

**Follow-up answer points:**
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Range / list / hash partitioning; partition pruning
- Archival strategy
- Deleting millions of rows safely


**Q142. Keys, constraints and referential integrity.**

**Interview-ready answer:** Relational design uses keys, constraints, transactions, and indexes for correctness. Write parameterized queries, inspect EXPLAIN plans, index actual predicates and joins, and choose isolation and locking based on contention.

**Follow-up answer points:**
- Define ownership and cascade deliberately, keep session and transaction boundaries clear, and use fetch plans or projections to prevent N+1 queries.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.

- PK/FK/Unique/Check; cascade rules
- Surrogate vs natural keys
- Partial unique indexes for soft-delete scenarios


**Q143. Views, materialized views, triggers, CTEs, stored procedures.**

**Interview-ready answer:** Relational design uses keys, constraints, transactions, and indexes for correctness. Write parameterized queries, inspect EXPLAIN plans, index actual predicates and joins, and choose isolation and locking based on contention.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Recursive CTE use cases
- When should logic live in the DB vs the application?
- Refreshing materialized views


**Q144. Handling millions of rows efficiently.**

**Interview-ready answer:** Relational design uses keys, constraints, transactions, and indexes for correctness. Write parameterized queries, inspect EXPLAIN plans, index actual predicates and joins, and choose isolation and locking based on contention.

**Follow-up answer points:**
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Define ownership and cascade deliberately, keep session and transaction boundaries clear, and use fetch plans or projections to prevent N+1 queries.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.

- Keyset pagination in SQL
- Bulk loading (`COPY`, batch inserts); streaming with fetch size
- Avoiding OOM when processing large result sets


---

## L. Microservices

**Q145. Monolith vs microservices: when should you NOT use microservices?**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Modular monolith as a middle path (module separation)
- Costs: distributed complexity, operational overhead
- Migration approach: strangler fig


**Q146. How do you define service boundaries?**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- DDD bounded contexts and aggregates
- Data ownership and database-per-service
- Avoiding chatty services and the "distributed monolith"


**Q147. Synchronous (REST/gRPC) vs asynchronous (messaging) communication.**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Trade-offs and temporal coupling
- gRPC/Protobuf benefits and limitations
- Choosing per use case


**Q148. API Gateway: role and responsibilities.**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Routing, auth, rate limiting, aggregation
- Spring Cloud Gateway; Backend-for-Frontend pattern
- Avoiding a single point of failure


**Q149. Service discovery and load balancing.**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Eureka/Consul vs Kubernetes DNS
- Client-side vs server-side load balancing
- Health checks and instance removal


**Q150. Resilience patterns: circuit breaker, retry, timeout, bulkhead, fallback.**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Resilience4j circuit breaker states
- Retry storms; exponential backoff with jitter
- Why idempotency matters when retrying


**Q151. Distributed transactions: the Saga pattern.**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Keep the transaction short and explicit; choose isolation and retry behavior for consistency, and make external effects idempotent.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Choreography vs orchestration
- Compensating transactions
- Why not two-phase commit?


**Q152. Transactional Outbox and the dual-write problem.**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.

- Why is "save to DB, then publish to Kafka" unsafe?
- Polling publisher vs CDC (Debezium)
- Idempotent consumers and deduplication


**Q153. Data consistency: eventual consistency and distributed locks.**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Strong vs eventual consistency; explaining it to the business
- Distributed locks with Redis/DB and their pitfalls
- Read-your-writes problems


**Q154. CQRS and Event Sourcing.**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- When is it worth the complexity?
- Read-model projections
- Event versioning


**Q155. Observability: tracing, logging, metrics.**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Trace/span ID propagation (Micrometer, OpenTelemetry)
- Centralized logging (ELK/Loki); Prometheus metrics
- SLI/SLO and alerting design


**Q156. Configuration and feature flags across services.**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Spring Cloud Config vs Kubernetes ConfigMaps
- Refreshing config at runtime
- Feature toggles for safe releases


**Q157. Service-to-service security.**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.

- JWT propagation, OAuth2 client credentials, mTLS
- Gateway-level vs service-level authentication
- Zero-trust principles


**Q158. Contract testing and API/event evolution.**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.

- Pact / Spring Cloud Contract; consumer-driven contracts
- Backward-compatible changes
- Handling multiple consumer versions


**Q159. Describe a cascading failure in a microservice system and how you'd prevent it.**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.

- Timeouts, bulkheads, load shedding
- Graceful degradation and fallbacks
- Post-incident review


**Q160. Deployment strategies: rolling, blue-green, canary.**

**Interview-ready answer:** A service has a bounded responsibility and owns its data. Use synchronous calls only where latency and availability permit; add timeouts, backoff, circuit breaking, idempotency, and correlation IDs. Design for partial failure and observable contracts.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Keep the transaction short and explicit; choose isolation and retry behavior for consistency, and make external effects idempotent.
- Test behavior at the cheapest useful boundary; isolate external systems in unit tests and use deterministic integration or contract tests for wiring.

- Readiness vs liveness probes
- Rollback approach
- Zero-downtime DB changes with expand-contract migrations


---

## M. Messaging & Kafka

**Q161. Why use messaging? Kafka vs RabbitMQ vs SQS.**

**Interview-ready answer:** Kafka is an ordered append-only log per partition. Consumer groups assign partitions to one consumer; offsets and acknowledgement determine replay and delivery. Use keys for ordering, idempotent processing, bounded retries, and a dead-letter path.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Queue vs pub/sub semantics
- Ordering, retention, throughput
- When to use which


**Q162. Kafka core concepts.**

**Interview-ready answer:** Kafka is an ordered append-only log per partition. Consumer groups assign partitions to one consumer; offsets and acknowledgement determine replay and delivery. Use keys for ordering, idempotent processing, bounded retries, and a dead-letter path.

**Follow-up answer points:**
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Topic, partition, offset, broker, replication
- Consumer groups; partition key and ordering
- Leader and ISR


**Q163. Delivery semantics: at-most-once, at-least-once, exactly-once.**

**Interview-ready answer:** Kafka is an ordered append-only log per partition. Consumer groups assign partitions to one consumer; offsets and acknowledgement determine replay and delivery. Use keys for ordering, idempotent processing, bounded retries, and a dead-letter path.

**Follow-up answer points:**
- Keep the transaction short and explicit; choose isolation and retry behavior for consistency, and make external effects idempotent.
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.

- Producer `acks`, idempotent producer, transactions
- Offset commit strategies
- Making consumers idempotent


**Q164. Consumer lag, rebalancing and scaling consumers.**

**Interview-ready answer:** Kafka is an ordered append-only log per partition. Consumer groups assign partitions to one consumer; offsets and acknowledgement determine replay and delivery. Use keys for ordering, idempotent processing, bounded retries, and a dead-letter path.

**Follow-up answer points:**
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.

- Why max consumers = number of partitions
- Rebalance causes and cooperative rebalancing
- Slow consumers and poison messages


**Q165. Error handling in Spring Kafka.**

**Interview-ready answer:** Kafka is an ordered append-only log per partition. Consumer groups assign partitions to one consumer; offsets and acknowledgement determine replay and delivery. Use keys for ordering, idempotent processing, bounded retries, and a dead-letter path.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Retry with backoff; retry topics
- Dead Letter Topic; `ErrorHandlingDeserializer`
- Replaying messages


**Q166. Ordering and partition-key design.**

**Interview-ready answer:** Kafka is an ordered append-only log per partition. Consumer groups assign partitions to one consumer; offsets and acknowledgement determine replay and delivery. Use keys for ordering, idempotent processing, bounded retries, and a dead-letter path.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.
- Choose the partition key deliberately, commit offsets after durable processing, and make handlers idempotent because retries and replays occur.

- Ordering guarantees per key
- Hot partitions
- How to choose partition count


**Q167. Event design and schema evolution.**

**Interview-ready answer:** Kafka is an ordered append-only log per partition. Consumer groups assign partitions to one consumer; offsets and acknowledgement determine replay and delivery. Use keys for ordering, idempotent processing, bounded retries, and a dead-letter path.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Event vs command; fat vs thin events
- Avro/Schema Registry; backward/forward compatibility
- Idempotency keys in events


---

## N. Security

**Q168. Authentication vs authorization; Spring Security architecture.**

**Interview-ready answer:** Apply defense in depth: authenticate, authorize with least privilege, validate and encode untrusted data, protect secrets and transport, and log security events without credentials. Threat-model trust boundaries.

**Follow-up answer points:**
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.

- Filter chain, `AuthenticationManager`, `SecurityContext`
- `UserDetailsService`; password encoding with BCrypt
- Method security with `@PreAuthorize`


**Q169. JWT: structure, validation and pitfalls.**

**Interview-ready answer:** Apply defense in depth: authenticate, authorize with least privilege, validate and encode untrusted data, protect secrets and transport, and log security events without credentials. Threat-model trust boundaries.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Signing algorithms, expiry, refresh tokens
- Cookie vs localStorage storage; token revocation
- The `alg=none` class of attacks


**Q170. OAuth2 and OpenID Connect.**

**Interview-ready answer:** Apply defense in depth: authenticate, authorize with least privilege, validate and encode untrusted data, protect secrets and transport, and log security events without credentials. Threat-model trust boundaries.

**Follow-up answer points:**
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.

- Authorization Code + PKCE vs Client Credentials
- Resource server vs authorization server (e.g., Keycloak)
- Scopes vs roles


**Q171. OWASP Top 10 for backend developers.**

**Interview-ready answer:** Apply defense in depth: authenticate, authorize with least privilege, validate and encode untrusted data, protect secrets and transport, and log security events without credentials. Threat-model trust boundaries.

**Follow-up answer points:**
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- SQL injection prevention (prepared statements)
- XSS, CSRF, SSRF, broken access control (IDOR)
- Mass assignment


**Q172. Password storage and secrets handling.**

**Interview-ready answer:** Apply defense in depth: authenticate, authorize with least privilege, validate and encode untrusted data, protect secrets and transport, and log security events without credentials. Threat-model trust boundaries.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.

- Hashing vs encryption; salting; BCrypt/Argon2
- Secrets management
- Data at rest and in transit (TLS)


**Q173. CORS, CSRF, HTTPS and security headers.**

**Interview-ready answer:** Apply defense in depth: authenticate, authorize with least privilege, validate and encode untrusted data, protect secrets and transport, and log security events without credentials. Threat-model trust boundaries.

**Follow-up answer points:**
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- When CSRF protection applies
- HSTS, CSP
- TLS termination


**Q174. Protecting APIs from abuse.**

**Interview-ready answer:** Apply defense in depth: authenticate, authorize with least privilege, validate and encode untrusted data, protect secrets and transport, and log security events without credentials. Threat-model trust boundaries.

**Follow-up answer points:**
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Preserve causes and add context at a boundary; do not swallow or repeatedly log failures, and never include secrets.

- Validation and sanitization; rate limiting; audit logs
- PII handling, masking, GDPR basics
- Dependency vulnerability scanning; lessons from Log4Shell


---

## O. Testing & Code Quality

**Q175. The test pyramid: unit vs integration vs end-to-end.**

**Interview-ready answer:** Test at the right boundary: unit tests for logic, integration tests for persistence and messaging, and contract or end-to-end tests for seams. Use deterministic fixtures and meaningful assertions; coverage is not correctness.

**Follow-up answer points:**
- Test behavior at the cheapest useful boundary; isolate external systems in unit tests and use deterministic integration or contract tests for wiring.
- Test behavior at the cheapest useful boundary; isolate external systems in unit tests and use deterministic integration or contract tests for wiring.
- Test behavior at the cheapest useful boundary; isolate external systems in unit tests and use deterministic integration or contract tests for wiring.

- What to mock and what not to
- JUnit 5 and Mockito basics
- Coverage vs test quality


**Q176. Mockito: mock vs spy vs stub; `@Mock` vs `@MockBean`.**

**Interview-ready answer:** Test at the right boundary: unit tests for logic, integration tests for persistence and messaging, and contract or end-to-end tests for seams. Use deterministic fixtures and meaningful assertions; coverage is not correctness.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Test behavior at the cheapest useful boundary; isolate external systems in unit tests and use deterministic integration or contract tests for wiring.
- Test behavior at the cheapest useful boundary; isolate external systems in unit tests and use deterministic integration or contract tests for wiring.

- `verify`, `ArgumentCaptor`
- Mocking static/final
- Over-mocking smells


**Q177. Spring Boot test slices.**

**Interview-ready answer:** Test at the right boundary: unit tests for logic, integration tests for persistence and messaging, and contract or end-to-end tests for seams. Use deterministic fixtures and meaningful assertions; coverage is not correctness.

**Follow-up answer points:**
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.
- Test behavior at the cheapest useful boundary; isolate external systems in unit tests and use deterministic integration or contract tests for wiring.
- Test behavior at the cheapest useful boundary; isolate external systems in unit tests and use deterministic integration or contract tests for wiring.

- `@SpringBootTest` vs `@WebMvcTest` vs `@DataJpaTest`
- MockMvc usage
- Context caching and test speed


**Q178. Integration testing with Testcontainers.**

**Interview-ready answer:** Test at the right boundary: unit tests for logic, integration tests for persistence and messaging, and contract or end-to-end tests for seams. Use deterministic fixtures and meaningful assertions; coverage is not correctness.

**Follow-up answer points:**
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Test behavior at the cheapest useful boundary; isolate external systems in unit tests and use deterministic integration or contract tests for wiring.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.

- Why prefer real Postgres/Kafka over H2
- Container reuse and test data cleanup
- Running in CI


**Q179. Testing time, external APIs and concurrency.**

**Interview-ready answer:** Test at the right boundary: unit tests for logic, integration tests for persistence and messaging, and contract or end-to-end tests for seams. Use deterministic fixtures and meaningful assertions; coverage is not correctness.

**Follow-up answer points:**
- Test behavior at the cheapest useful boundary; isolate external systems in unit tests and use deterministic integration or contract tests for wiring.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- WireMock / MockWebServer
- Injecting a `Clock`
- Awaitility for async assertions


**Q180. Code quality practices.**

**Interview-ready answer:** Test at the right boundary: unit tests for logic, integration tests for persistence and messaging, and contract or end-to-end tests for seams. Use deterministic fixtures and meaningful assertions; coverage is not correctness.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Test behavior at the cheapest useful boundary; isolate external systems in unit tests and use deterministic integration or contract tests for wiring.

- What do you look for in a code review?
- Static analysis (SonarQube) and handling technical debt
- Refactoring safely when tests are missing (characterization tests)


---

## P. Design Principles & Patterns

**Q181. SOLID principles with Java examples.**

**Interview-ready answer:** Prefer cohesive, loosely coupled code with explicit dependencies. SOLID and patterns are tools: introduce one when it removes a recurring change or failure mode, and document trade-offs.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.

- SRP and OCP in a real service
- A realistic LSP violation
- DIP and how Spring DI supports it


**Q182. Design patterns you have actually used.**

**Interview-ready answer:** Prefer cohesive, loosely coupled code with explicit dependencies. SOLID and patterns are tools: introduce one when it removes a recurring change or failure mode, and document trade-offs.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Prefer constructor injection and test the proxied boundary; proxy-based advice does not apply to direct self-invocation.

- Thread-safe Singleton (enum, holder idiom) vs Spring singleton
- Strategy replacing if-else/switch; Factory; Builder; Observer; Decorator
- Patterns inside Spring itself (Proxy, Template, Factory)


**Q183. Layered vs hexagonal/clean architecture.**

**Interview-ready answer:** Prefer cohesive, loosely coupled code with explicit dependencies. SOLID and patterns are tools: introduce one when it removes a recurring change or failure mode, and document trade-offs.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Responsibilities of controller, service and repository
- Ports and adapters
- Anemic vs rich domain model


**Q184. DDD basics.**

**Interview-ready answer:** Prefer cohesive, loosely coupled code with explicit dependencies. SOLID and patterns are tools: introduce one when it removes a recurring change or failure mode, and document trade-offs.

**Follow-up answer points:**
- Define ownership and cascade deliberately, keep session and transaction boundaries clear, and use fetch plans or projections to prevent N+1 queries.
- Keep the transaction short and explicit; choose isolation and retry behavior for consistency, and make external effects idempotent.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Entity vs value object vs aggregate vs repository
- Aggregate boundaries and transactions
- Domain events


**Q185. Low-level design: parking lot / URL shortener / notification service.**

**Interview-ready answer:** Prefer cohesive, loosely coupled code with explicit dependencies. SOLID and patterns are tools: introduce one when it removes a recurring change or failure mode, and document trade-offs.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Classes, interfaces and extensibility
- Concurrency considerations
- Patterns applied


**Q186. Coupling, cohesion and refactoring a god class.**

**Interview-ready answer:** Prefer cohesive, loosely coupled code with explicit dependencies. SOLID and patterns are tools: introduce one when it removes a recurring change or failure mode, and document trade-offs.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- How would you break up a 2,000-line service?
- Cyclic dependencies between packages/modules
- Package-by-feature vs package-by-layer


---

## Q. System Design, Caching & Performance

**Q187. Caching strategies with Redis.**

**Interview-ready answer:** Start with measured latency, throughput, and error budgets. Remove the dominant bottleneck using profiling, query plans, bounded caches, batching, and backpressure; preserve correctness and verify with load tests.

**Follow-up answer points:**
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.

- Cache-aside, write-through, write-behind
- Eviction policies, TTL and invalidation
- Cache stampede, penetration and avalanche


**Q188. Design a URL shortener (system design approach).**

**Interview-ready answer:** Start with measured latency, throughput, and error budgets. Remove the dominant bottleneck using profiling, query plans, bounded caches, batching, and backpressure; preserve correctness and verify with load tests.

**Follow-up answer points:**
- Use HTTP semantics consistently, validate and document representations, return stable errors, and define compatibility and idempotency.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.

- Requirements, capacity estimation, API, data model
- ID generation and scaling reads
- Trade-offs and bottlenecks


**Q189. How would you scale a Java service to 10x traffic?**

**Interview-ready answer:** Start with measured latency, throughput, and error budgets. Remove the dominant bottleneck using profiling, query plans, bounded caches, batching, and backpressure; preserve correctness and verify with load tests.

**Follow-up answer points:**
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Use parameterized SQL and inspect EXPLAIN; index selective filters and joins while accounting for write and storage cost.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Stateless horizontal scaling and load balancing
- DB bottlenecks: indexes, replicas, caching
- Async processing and queues


**Q190. Design a rate limiter.**

**Interview-ready answer:** Start with measured latency, throughput, and error budgets. Remove the dominant bottleneck using profiling, query plans, bounded caches, batching, and backpressure; preserve correctness and verify with load tests.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Token bucket vs leaky bucket vs sliding window
- Distributed implementation with Redis (Lua scripts)
- `429` and `Retry-After` handling


**Q191. Handling high concurrency without overselling (inventory/ticket booking).**

**Interview-ready answer:** Start with measured latency, throughput, and error budgets. Remove the dominant bottleneck using profiling, query plans, bounded caches, batching, and backpressure; preserve correctness and verify with load tests.

**Follow-up answer points:**
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- State visibility and atomicity guarantees, lock ownership, and shutdown. Avoid blocking while holding locks; use timeouts and bounded executors.

- Optimistic locking vs `SELECT FOR UPDATE` vs atomic Redis decrement
- Idempotency and queue-based serialization
- Distributed lock trade-offs


**Q192. Performance optimization and load testing.**

**Interview-ready answer:** Start with measured latency, throughput, and error budgets. Remove the dominant bottleneck using profiling, query plans, bounded caches, batching, and backpressure; preserve correctness and verify with load tests.

**Follow-up answer points:**
- Define staleness tolerance, TTL, invalidation, size bounds, and behavior for misses, stampedes, outages, and incompatible serialization.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Finding bottlenecks with profilers/APM
- JMeter/Gatling; p95/p99 latency
- Quick wins: N+1 fixes, caching, pooling, batching, compression


---

## R. DevOps, Build & Tooling

**Q193. Dockerizing a Java application.**

**Interview-ready answer:** Reproducible builds pin dependencies and run tests, static checks, and security scans. CI produces immutable artifacts; deployment uses environment configuration, health checks, rollback, and least-privilege credentials.

**Follow-up answer points:**
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.

- Multi-stage builds, layered JARs, non-root user
- JVM behaviour with container memory limits
- Image size reduction (distroless/slim)


**Q194. Kubernetes basics for backend developers.**

**Interview-ready answer:** Reproducible builds pin dependencies and run tests, static checks, and security scans. CI produces immutable artifacts; deployment uses environment configuration, health checks, rollback, and least-privilege credentials.

**Follow-up answer points:**
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Explain reachability and allocation lifetime, then name the dump, log, or profiler used to confirm the diagnosis.

- Pod, Deployment, Service, ConfigMap, Secret
- Liveness vs readiness probes; HPA
- Resource requests/limits and `OOMKilled`


**Q195. CI/CD pipeline design.**

**Interview-ready answer:** Reproducible builds pin dependencies and run tests, static checks, and security scans. CI produces immutable artifacts; deployment uses environment configuration, health checks, rollback, and least-privilege credentials.

**Follow-up answer points:**
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Keep the transaction short and explicit; choose isolation and retry behavior for consistency, and make external effects idempotent.

- Typical stages; Jenkins / GitHub Actions / GitLab CI
- Build once, deploy many; artifact repository
- Quality gates and rollback


**Q196. Git workflow questions.**

**Interview-ready answer:** Reproducible builds pin dependencies and run tests, static checks, and security scans. CI produces immutable artifacts; deployment uses environment configuration, health checks, rollback, and least-privilege credentials.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Merge vs rebase; cherry-pick; resolving conflicts
- Trunk-based vs GitFlow
- `revert` vs `reset` on shared branches


**Q197. Maven/Gradle essentials.**

**Interview-ready answer:** Reproducible builds pin dependencies and run tests, static checks, and security scans. CI produces immutable artifacts; deployment uses environment configuration, health checks, rollback, and least-privilege credentials.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Dependency scopes; transitive conflicts and `mvn dependency:tree`
- Multi-module projects (module separation)
- BOMs, plugins and profiles


---

## S. Project & Behavioral

**Q198. Walk me through your current project architecture and your role.**

**Interview-ready answer:** Give situation, action, reasoning, and measurable result. Be honest about trade-offs and failures, and connect the example to reliability, maintainability, or user impact.

**Follow-up answer points:**
- Make builds reproducible, run checks before packaging, publish immutable artifacts, configure environments safely, and provide health checks and rollback.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Why were these design decisions made; what were the trade-offs?
- Your biggest technical challenge and how you solved it
- Modules, schema design or microservices you personally built; what would you change?


**Q199. Tell me about a production incident you handled.**

**Interview-ready answer:** Give situation, action, reasoning, and measurable result. Be honest about trade-offs and failures, and connect the example to reliability, maintainability, or user impact.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Keep the transaction short and explicit; choose isolation and retry behavior for consistency, and make external effects idempotent.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.

- Debugging steps, root cause, and fix
- Communication, rollback decisions, monitoring gaps
- What you changed to prevent a repeat


**Q200. Behavioral and growth questions.**

**Interview-ready answer:** Give situation, action, reasoning, and measurable result. Be honest about trade-offs and failures, and connect the example to reliability, maintainability, or user impact.

**Follow-up answer points:**
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Clarify the contract, normal case, failure mode, and trade-off; validate the choice with focused tests and observable metrics.
- Authenticate, authorize at the resource boundary, validate input, use TLS and secure secret storage, and never log credentials or tokens.

- Handling tight deadlines and changing scope; estimating work
- Disagreeing with a senior engineer on design
- Mentoring juniors, learning new tech, and why you're switching roles


---

*Total: 200 primary questions (Q1-Q200), each with 3-4 follow-up questions.*
