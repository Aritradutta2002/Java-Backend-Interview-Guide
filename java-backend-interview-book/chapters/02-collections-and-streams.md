# Chapter 2. Collections, generics, streams, and functional Java

Assume Java 17 unless a question explicitly mentions Java 21. Complexity claims describe the standard OpenJDK implementations; where behaviour is an implementation detail rather than a specification guarantee, the text says so.

## Q031. How do you choose among List, Set and Map in a service?

**Priority:** Must Know  
**Why interviewers ask it:** Collection choice is the first design decision in almost every backend method, and a wrong one shows up later as duplicate rows, quadratic loops or unstable output.

**Interview-ready answer:** I start from semantics, not performance. If order matters and duplicates are legal I use a `List`. If the collection answers "have I already seen this?" I use a `Set`. If I need lookup by key I use a `Map`. Then I refine the implementation: `ArrayList` for almost all lists, `HashSet` for membership, `LinkedHashSet` when I must keep insertion order, `TreeSet`/`TreeMap` when I need sorted traversal or range queries, and `EnumMap` for enum keys. The last question is concurrency: if multiple threads write, I move to `ConcurrentHashMap` or an immutable copy rather than wrapping with `Collections.synchronizedMap`.

**In-depth explanation:** The interface expresses a contract; the implementation expresses a cost model. `List` guarantees positional access and allows duplicates; `contains` is O(n). `Set` guarantees uniqueness by `equals`/`hashCode` (or by comparator for `TreeSet`), with O(1) average membership for hash sets. `Map` is a key-to-value association with the same hashing rules for keys. A very common backend smell is scanning a list inside a loop — `for (Order o : orders) if (ids.contains(o.id()))` with `ids` as a `List` is O(n*m); converting `ids` to a `Set` makes it effectively O(n). Sorted structures cost O(log n) per operation but give you `firstKey`, `headMap`, `subMap` and ordered iteration, which hash structures cannot provide at any price. Also consider iteration order stability: `HashMap` iteration order is unspecified and may change between versions, so never let API output depend on it — sort explicitly or use `LinkedHashMap`.

**Practical backend example:** Filtering a batch of incoming order events against a set of blocked customer IDs:

```java
Set<UUID> blocked = Set.copyOf(blockedCustomerRepository.findAllIds()); // O(1) membership
Map<UUID, List<OrderEvent>> byCustomer = events.stream()
        .filter(e -> !blocked.contains(e.customerId()))
        .collect(Collectors.groupingBy(OrderEvent::customerId));
```

**Common follow-ups:**
- How do you keep insertion order in a map? Use `LinkedHashMap`; `HashMap` order is unspecified and must not leak into an API response.
- When is `TreeMap` worth the log-n cost? When you need sorted iteration, a floor/ceiling lookup or range scans, such as tiered pricing bands.
- What about arrays? Use them only for fixed-size primitive data in hot paths; they lack the API and safety of collections.

**Mistakes to avoid:** Using `List.contains` inside a loop over another list; assuming `HashSet` preserves insertion order; sorting a `HashMap` by "just iterating it"; choosing `Collections.synchronizedList` for a hot path and expecting scalability.

**Production perspective:** Collection choice changes the shape of CPU profiles far more often than micro-optimisations do. It also affects memory: each `HashMap` entry carries an object header, hash, key, value and next pointer, so caching millions of small entries on-heap is usually worse than an external store such as Redis.

**Related concepts covered:** Big-O reasoning, equals/hashCode, iteration order, enum collections, concurrent collections, memory footprint.

## Q032. How does HashMap locate a key, handle collisions and resize?

**Priority:** Must Know  
**Why interviewers ask it:** It reveals whether you understand hashing well enough to debug missing keys, pathological performance and broken key classes.

**Interview-ready answer:** `HashMap` keeps an array of buckets whose length is a power of two. On `put` it takes the key's `hashCode`, applies a spreading function that XORs the high bits into the low bits, and masks it to an index. If the bucket is empty it stores the entry; otherwise it walks the bucket comparing hashes first and then `equals`. Colliding entries form a linked list, and in OpenJDK a heavily collided bin converts to a balanced tree so worst-case lookup degrades to O(log n) instead of O(n). When size exceeds capacity times the 0.75 load factor the table doubles and entries are redistributed. All of that assumes `hashCode` and `equals` are consistent and stable — if a key mutates after insertion, the entry becomes unreachable.

**In-depth explanation:** The contract-level facts are: equal objects must have equal hash codes, unequal objects may share one, and average O(1) lookup depends on a reasonable hash distribution. The rest — the `h ^ (h >>> 16)` spread, treeification at eight entries in a bin when the table has at least 64 slots, the 0.75 default load factor and the default capacity of 16 — are OpenJDK implementation details worth knowing but worth labelling as such. Resizing is not free: it allocates a new array and rehashes every entry, so pre-sizing with `new HashMap<>(expectedSize / 0.75f + 1)` matters for large bulk loads. A poor `hashCode` (for example, returning a constant) is functionally correct but turns the map into a list. Treeification only helps when keys are `Comparable`, otherwise the tree falls back to comparing hash codes and identity ordering.

**Practical backend example:** Building a lookup for a nightly reconciliation job over roughly 500,000 rows:

```java
Map<String, PaymentRow> byReference = new HashMap<>(700_000); // avoid repeated resizes
for (PaymentRow row : rows) {
    byReference.put(row.reference(), row); // reference is an immutable String key
}
```

**Common follow-ups:**
- What happens if two keys collide? They share a bucket; the map compares hash then `equals` to distinguish them, so correctness is preserved and only speed suffers.
- Is iteration order guaranteed? No. It depends on hashes and capacity and can change after a resize or a JDK upgrade.
- What breaks if a key is mutated? The entry stays in its old bucket, so `get`, `remove` and `containsKey` can all fail to find it. Prefer immutable keys.
- Is `HashMap` thread-safe? No. Concurrent writes can corrupt it or produce lost updates; use `ConcurrentHashMap`.

**Mistakes to avoid:** Saying collisions overwrite values; claiming treeification is part of the Java specification; using a mutable entity with a database-generated ID as a map key; overriding `equals` without `hashCode`.

**Production perspective:** Pathological hashing has been a real denial-of-service vector for user-controlled keys, which is why the JDK added treeification. In services, the more common problem is memory: a `HashMap` used as an unbounded cache is a classic slow leak, because nothing evicts entries.

**Related concepts covered:** equals/hashCode contract, load factor and capacity, treeified bins, immutable keys, ConcurrentHashMap, memory leaks.

## Q033. When would you use ArrayList versus LinkedList?

**Priority:** Important  
**Why interviewers ask it:** It separates candidates who recite Big-O tables from those who understand memory locality and real measurements.

**Interview-ready answer:** In practice I use `ArrayList` almost always. It stores elements in a contiguous array, so indexed access is O(1) and iteration is cache-friendly. `LinkedList` gives O(1) insertion and removal only when you already hold the position — typically via a `ListIterator` — because finding the position is still O(n). Its per-element node objects add memory overhead and pointer chasing, so even for queue-like workloads `ArrayDeque` usually beats it. I would consider `LinkedList` only for a genuine deque-with-frequent-middle-splicing pattern, and I would measure first.

**In-depth explanation:** `ArrayList.add` at the end is amortised O(1): when the array is full it grows by roughly 50% and copies. Insert or remove in the middle is O(n) because of the arraycopy, but arraycopy is a fast intrinsic, so for lists of a few thousand elements it frequently outperforms a linked traversal. `LinkedList` implements both `List` and `Deque`; its `get(int)` walks from the nearer end, which makes an index-based loop over a `LinkedList` accidentally O(n²). Memory matters too: each `LinkedList` node holds item, next and previous references plus a header, typically far more bytes per element than an array slot. `ArrayDeque` is the recommended stack and queue implementation; `Stack` and `Vector` are legacy synchronised classes you should not introduce in new code.

**Practical backend example:** Batching outbound webhook payloads for delivery:

```java
List<WebhookPayload> batch = new ArrayList<>(BATCH_SIZE); // sized once, no resize churn
Deque<RetryTask> retryQueue = new ArrayDeque<>();          // better than LinkedList for FIFO
```

**Common follow-ups:**
- Is `LinkedList` insertion really O(1)? Only with an existing iterator or at the ends; index-based insertion pays O(n) to locate the node.
- Why is `ArrayList` faster despite equal Big-O for iteration? Contiguous memory means fewer cache misses and no pointer chasing.
- What replaces `Stack` and `Vector`? `ArrayDeque` and `ArrayList`, plus explicit synchronisation or a concurrent collection if needed.

**Mistakes to avoid:** Choosing `LinkedList` because "inserts are O(1)" without considering the search cost; looping with `get(i)` over a `LinkedList`; forgetting that `Arrays.asList` returns a fixed-size view whose `add` throws `UnsupportedOperationException`.

**Production perspective:** Pre-sizing an `ArrayList` when the count is known removes copy churn in high-throughput paths. Conversely, an `ArrayList` built from an unbounded query result is a memory risk: stream or paginate instead.

**Related concepts covered:** Amortised complexity, cache locality, ArrayDeque, legacy collections, defensive sizing.

## Q034. Which Set implementation fits deduplication, order or sorting?

**Priority:** Important  
**Why interviewers ask it:** Choosing the wrong `Set` silently changes output ordering or, with `TreeSet`, silently changes what "duplicate" means.

**Interview-ready answer:** `HashSet` is the default for pure membership and deduplication, with average O(1) operations and no order guarantee. `LinkedHashSet` keeps insertion order for a small extra cost per element, which is what I use when the result is returned to a client and needs to be stable. `TreeSet` keeps elements sorted and offers navigation methods like `first`, `ceiling` and `headSet`, at O(log n). The important subtlety is that `TreeSet` decides equality with `compareTo` or the supplied `Comparator`, not with `equals`, so an ordering that ignores a field will treat distinct objects as duplicates.

**In-depth explanation:** `HashSet` is backed by a `HashMap`, so everything about hashing, resizing and mutable keys applies to it directly. `LinkedHashSet` adds a doubly linked list through the entries, giving predictable iteration at the cost of two extra references per element. `TreeSet` is backed by a `TreeMap` red-black tree. Its contract asks for an ordering "consistent with equals"; when it is not, the set still works but its notion of duplicates comes from `compare(...) == 0`. That is occasionally useful — for example a case-insensitive `TreeSet<>(String.CASE_INSENSITIVE_ORDER)` that intentionally treats "Alice" and "alice" as the same. `EnumSet` is a specialised, extremely compact bitset for enum elements and should be preferred for flags. For immutable results, `Set.of(...)` and `Set.copyOf(...)` reject nulls and duplicates at construction and have an unspecified, deliberately randomised iteration order.

**Practical backend example:** Deduplicating notification recipients while keeping the order the business rules produced:

```java
Set<String> recipients = new LinkedHashSet<>();
recipients.add(order.customerEmail());
recipients.addAll(account.billingContacts());       // duplicates dropped, order preserved
Set<Channel> channels = EnumSet.of(Channel.EMAIL, Channel.PUSH);
```

**Common follow-ups:**
- Why did my `TreeSet` drop a distinct element? Its comparator returned 0, so the set considered the element a duplicate.
- Does `Set.of()` keep insertion order? No; its iteration order is unspecified and intentionally varies between runs.
- Can a `HashSet` contain null? Yes, one null; `TreeSet` and `Set.of` reject null.

**Mistakes to avoid:** Returning a `HashSet` from an API and assuming stable JSON array order; writing a comparator on one field and being surprised at lost elements; using a `TreeSet` of mutable objects whose sort keys change.

**Production perspective:** Unstable ordering makes responses non-deterministic, which breaks client caching, snapshot tests and diff-based debugging. If the order is part of the contract, make it explicit with a sort or a linked implementation.

**Related concepts covered:** Comparator consistency, EnumSet, immutable collections, deduplication, deterministic API output.

## Q035. How do iterators and fail-fast behavior work?

**Priority:** Important  
**Why interviewers ask it:** `ConcurrentModificationException` is a rite of passage, and the right answer shows you know it is a bug detector, not a thread-safety feature.

**Interview-ready answer:** Most `java.util` collections return fail-fast iterators. They record a modification count when created and check it on each step; if the collection was structurally modified through anything except the iterator itself, they throw `ConcurrentModificationException`. The safe ways to remove during iteration are `Iterator.remove()`, `Collection.removeIf(...)`, or building a new collection. Importantly, fail-fast is best effort: the exception is a debugging aid, not a guarantee, so it must never be relied on to detect concurrent access between threads. Concurrent collections like `ConcurrentHashMap` and `CopyOnWriteArrayList` instead give weakly consistent iterators that never throw but may not see the newest updates.

**In-depth explanation:** "Structural modification" means adding or removing elements, or in the case of a map, changing the key set; replacing a value with `set` or `put` on an existing key is not structural. The check lives in `modCount` and is not synchronised, so in a multithreaded scenario it can be missed entirely — this is precisely why the documentation calls the behaviour best effort. `CopyOnWriteArrayList` iterates over an immutable snapshot taken at iterator creation: reads never block and never throw, but each write copies the whole array, so it suits listener lists and rarely changing configuration, not high-write data. `ConcurrentHashMap`'s iterators traverse live state with weak consistency: they reflect some updates made after creation and never throw `ConcurrentModificationException`.

**Practical backend example:** Removing expired sessions from an in-memory registry:

```java
sessions.entrySet().removeIf(e -> e.getValue().expiresAt().isBefore(Instant.now())); // safe
// unsafe: for (var e : sessions.entrySet()) if (expired(e)) sessions.remove(e.getKey());
```

**Common follow-ups:**
- Is `ConcurrentModificationException` always thrown for concurrent modification? No; the check is best effort and can be missed, especially across threads.
- Can you modify values while iterating a map? Yes — `entry.setValue(...)` and `put` on an existing key are not structural changes.
- What does `CopyOnWriteArrayList` cost? Every mutation copies the backing array, so it is only appropriate for read-dominated collections.

**Mistakes to avoid:** Catching `ConcurrentModificationException` and retrying instead of fixing the iteration; treating a fail-fast iterator as a concurrency guard; calling `list.remove(index)` inside an enhanced for loop.

**Production perspective:** A `ConcurrentModificationException` in a log is usually a shared-mutable-state bug: a collection in a singleton bean is being modified by request threads. The fix is normally a concurrent collection or a per-request copy, not a try/catch.

**Related concepts covered:** modCount and structural modification, removeIf, copy-on-write collections, weakly consistent iterators, shared mutable state.

## Q036. What do generic type parameters and wildcards protect?

**Priority:** Must Know  
**Why interviewers ask it:** Generic APIs are where library-quality code shows, and PECS is the compact test of whether you can design one.

**Interview-ready answer:** Generics move type checking to compile time and remove casts. The key rule is that generics are invariant: `List<Dog>` is not a `List<Animal>`, because if it were, you could insert a `Cat` into a list of dogs. Wildcards restore flexibility safely. `? extends T` means "some unknown subtype of T", so you can read `T` values but cannot add anything except null — a producer. `? super T` means "some unknown supertype of T", so you can add `T` values but reads come back as `Object` — a consumer. That is PECS: producer extends, consumer super. I use a bounded type parameter when several positions in the signature must agree, and a wildcard when only one position needs flexibility.

**In-depth explanation:** Invariance exists because Java arrays made the opposite choice — `Object[] a = new String[1]` compiles and then throws `ArrayStoreException` at runtime. Generics chose compile-time safety instead. A method that only reads from a collection should take `Collection<? extends T>` so callers can pass `List<SubType>`. A method that only writes should take `Collection<? super T>`. `Collections.copy(List<? super T> dest, List<? extends T> src)` is the canonical illustration. Bounded type parameters such as `<T extends Comparable<? super T>>` let the compiler relate several arguments and the return type. An unbounded wildcard `List<?>` is useful for code that only needs `size`, `isEmpty` or iteration as `Object`. Note that `? extends` does not mean "class only"; it also accepts interfaces, and multiple bounds are written `<T extends Number & Comparable<T>>`.

**Practical backend example:** A reporting helper that must accept any subtype collection:

```java
public static Money sum(Collection<? extends Invoice> invoices) {   // producer -> extends
    return invoices.stream().map(Invoice::total).reduce(Money.ZERO, Money::plus);
}

public static void drainTo(List<? super AuditEvent> sink, Queue<AuditEvent> source) { // consumer -> super
    AuditEvent event;
    while ((event = source.poll()) != null) sink.add(event);
}
```

**Common follow-ups:**
- Why is `List<Dog>` not a `List<Animal>`? Because assignment would permit inserting a `Cat`, breaking the dog list at runtime.
- What can you add to a `List<? extends Animal>`? Only `null`; the concrete element type is unknown.
- When do you prefer `<T>` over a wildcard? When the same type must appear in more than one place, such as parameter and return type.

**Mistakes to avoid:** Declaring `List<Object>` and casting; using wildcards on return types, which forces callers to deal with unknown types; believing arrays and generics behave alike.

**Production perspective:** Wildcards mostly pay off in shared internal libraries and SPIs. In ordinary application services, a clear concrete type is more readable than a clever signature; generic gymnastics should earn their keep.

**Related concepts covered:** Invariance versus covariance, PECS, bounded type parameters, array store exceptions, API design.

## Q037. What does type erasure mean for overloads and runtime checks?

**Priority:** Important  
**Why interviewers ask it:** Erasure explains a family of confusing compiler errors and unchecked warnings that appear in real code.

**Interview-ready answer:** Generic type arguments exist at compile time and are erased in the bytecode: `List<String>` and `List<Integer>` are both `List` at runtime. Consequences are that you cannot overload two methods whose parameters differ only by type argument, you cannot write `new T()` or `new T[10]`, `instanceof List<String>` is illegal, and a cast to a generic type produces an unchecked warning because the runtime cannot verify it. The compiler inserts casts and sometimes bridge methods to keep polymorphism working. When I need the type at runtime I pass a `Class<T>` token or a framework-provided type reference.

**In-depth explanation:** Erasure was chosen for migration compatibility with pre-generics code, which is also why raw types still compile with warnings. Because of erasure, a `List<String>` can be polluted with a non-String through a raw reference, and the failure surfaces later at the implicit cast — this is heap pollution, and `@SafeVarargs` exists to document generic varargs methods that do not cause it. Generic arrays are forbidden for the same reason: an array knows its component type at runtime, a generic does not. Frameworks work around erasure by capturing type information in class literals or subclassed type tokens, for example Jackson's `TypeReference` or Spring's `ParameterizedTypeReference`, which read the generic supertype metadata that the class file does retain.

**Practical backend example:** Deserialising a generic response body in a Spring client:

```java
ResponseEntity<List<OrderDto>> response = restClient.get()
        .uri("/orders")
        .retrieve()
        .toEntity(new ParameterizedTypeReference<List<OrderDto>>() {}); // keeps the generic type
```

**Common follow-ups:**
- Can you write `new T()`? No; pass a `Supplier<T>` or a `Class<T>` and use reflection if you truly need instantiation.
- Why does `instanceof List<String>` not compile? The runtime cannot distinguish it from any other `List`; only `instanceof List<?>` is allowed.
- What are bridge methods? Compiler-generated methods that preserve overriding when erasure changes a signature, for example in `Comparable` implementations.

**Mistakes to avoid:** Using raw types to silence errors; suppressing unchecked warnings without a comment explaining why the cast is safe; expecting reflection to reveal a collection's element type from an instance.

**Production perspective:** Erasure surprises typically appear at integration boundaries — JSON mapping, caching libraries and message converters — where a value is stored as `Object` and cast back incorrectly, producing a `ClassCastException` far from the original code.

**Related concepts covered:** Raw types, heap pollution, @SafeVarargs, type tokens, reflection limits, bridge methods.

## Q038. How would you group and aggregate orders with streams?

**Priority:** Must Know  
**Why interviewers ask it:** Grouping and aggregation is the most common real stream task, and it exposes how comfortable you are with collectors.

**Interview-ready answer:** I build a pipeline of `filter`, `map` and then a collector. For "total revenue per customer" I use `Collectors.groupingBy` with a downstream `Collectors.reducing` or `summingLong`. For counts I use `counting()`. If I need an ordered result I supply a map factory such as `LinkedHashMap` or `TreeMap`, because the default is a `HashMap` with unspecified order. If the grouping is over a large dataset that lives in the database, I prefer to push the aggregation into SQL with `GROUP BY` and only stream the summarised rows — moving a million rows into the JVM to sum them is the classic mistake.

**In-depth explanation:** `groupingBy(classifier)` returns `Map<K, List<T>>`; the two- and three-argument forms let you replace the downstream collector and the map supplier. Useful downstreams are `counting()` (returns `Long`), `summingInt/Long/Double`, `averagingDouble`, `mapping(fn, downstream)`, `filtering(...)`, `toSet()`, `reducing(...)` and `teeing(...)` for two aggregates at once. `partitioningBy` is the boolean-key specialisation and always contains both `true` and `false` keys. Two sharp edges matter: the classifier must not return null or `groupingBy` throws a `NullPointerException`, and money should be summed with `BigDecimal` via `reducing` rather than with `summingDouble`, which introduces binary floating point error. For ordering, remember that `groupingBy` does not preserve encounter order in its keys, while the lists inside each group do preserve it for an ordered source.

**Practical backend example:** Monthly revenue per customer for a small in-memory report:

```java
Map<UUID, BigDecimal> revenueByCustomer = orders.stream()
        .filter(o -> o.status() == OrderStatus.PAID)
        .collect(Collectors.groupingBy(
                Order::customerId,
                TreeMap::new,                                   // deterministic key order
                Collectors.reducing(BigDecimal.ZERO, Order::total, BigDecimal::add)));

Map<OrderStatus, Long> countByStatus = orders.stream()
        .collect(Collectors.groupingBy(Order::status, () -> new EnumMap<>(OrderStatus.class),
                 Collectors.counting()));
```

**Common follow-ups:**
- What if two records map to the same key with `toMap`? Without a merge function `toMap` throws `IllegalStateException`; supply one, for example `(a, b) -> b`.
- Is `groupingBy` ordered? The returned `HashMap` is not; pass a map factory if order matters.
- Why not `summingDouble` for money? Doubles cannot represent decimal fractions exactly; use `BigDecimal` reduction or integer minor units.
- Should this run in Java or SQL? If the data is in a table and the result is an aggregate, `GROUP BY` in SQL is almost always cheaper.

**Mistakes to avoid:** Loading whole tables to aggregate in memory; a classifier that can return null; using `Collectors.toMap` on data with duplicate keys; assuming `counting()` returns an `int`.

**Production perspective:** In-memory aggregation is bounded by heap and GC; it also hides the cost from database metrics, making slow endpoints harder to attribute. Aggregate at the source, cache the summary if it is read often, and keep the stream code for shaping the response.

**Related concepts covered:** Collectors API, EnumMap, BigDecimal arithmetic, SQL GROUP BY trade-offs, deterministic ordering.

## Q039. What is the difference between map and flatMap?

**Priority:** Must Know  
**Why interviewers ask it:** It is a quick check that you understand stream shape, and the same idea recurs in `Optional`, reactive types and `CompletableFuture`.

**Interview-ready answer:** `map` transforms each element one-to-one, so a stream of N elements stays N elements — if the function returns a collection you end up with a stream of collections. `flatMap` transforms each element into a stream and concatenates the results, flattening one level, so N elements can become any number. I use `map` for field extraction and conversion, `flatMap` when each element contains many child elements, such as orders containing line items. The same distinction applies to `Optional.map` versus `Optional.flatMap`, where `flatMap` avoids an `Optional<Optional<T>>`.

**In-depth explanation:** `flatMap` takes a function returning a `Stream`, and the returned streams are consumed and closed as the pipeline runs; returning a null stream throws, so return `Stream.empty()` instead. It is also the idiomatic way to drop empties: `stream.flatMap(o -> o.map(Stream::of).orElseGet(Stream::empty))` in Java 8, or simply `stream.flatMap(Optional::stream)` from Java 9 onwards. `mapMulti` (Java 16+) is a lower-allocation alternative when each element produces few results, because it pushes results into a consumer rather than creating a stream per element. Note that `flatMap` can weaken laziness: short-circuit operations like `findFirst` may still consume an entire inner stream in older JDKs, although modern implementations improved this.

**Practical backend example:** Collecting all SKUs across a batch of orders, and unwrapping optional lookups:

```java
List<String> skus = orders.stream()
        .flatMap(order -> order.lines().stream())   // one order -> many lines
        .map(OrderLine::sku)                        // one line  -> one sku
        .distinct()
        .toList();

List<Customer> found = ids.stream()
        .map(customerRepository::findById)          // Stream<Optional<Customer>>
        .flatMap(Optional::stream)                  // drops the empties
        .toList();
```

**Common follow-ups:**
- What does `map` return when the function returns a list? `Stream<List<T>>`, which you then have to flatten.
- Does `flatMap` flatten deeply? No, one level per call; nest calls for deeper structures.
- What is `Optional.flatMap` for? Chaining a lookup that itself returns an `Optional` without nesting.

**Mistakes to avoid:** Returning null from a `flatMap` function; calling `.map(...).collect(...)` then flattening with nested loops; using `flatMap` where a simple `map` would do, which adds allocation.

**Production perspective:** `flatMap` over a lazily loaded JPA association triggers N+1 queries — the stream looks elegant while issuing one query per parent. Fetch the children with a join or an entity graph first.

**Related concepts covered:** Optional composition, stream laziness, mapMulti, N+1 query risk, distinct and toList.

## Q040. How do lazy streams and terminal operations affect side effects?

**Priority:** Must Know  
**Why interviewers ask it:** Misunderstanding laziness produces code that silently does nothing, or does work twice.

**Interview-ready answer:** Intermediate operations such as `filter`, `map` and `peek` only build a pipeline; nothing runs until a terminal operation such as `collect`, `forEach`, `count` or `findFirst` is invoked. Elements are then pulled through the pipeline one at a time, which is why `findFirst` can stop early. Two practical consequences: a pipeline with no terminal operation performs zero work, and `peek` is not a reliable place for side effects because it may be skipped or partially executed. Streams are also single-use — a second terminal operation on the same stream throws `IllegalStateException`.

**In-depth explanation:** The pull model means the order of operations is per element, not per stage: for `filter().map().findFirst()` the JDK processes one element through both stages before touching the next. Short-circuit operations (`findFirst`, `anyMatch`, `limit`) exploit this. `count()` may skip the pipeline entirely when it can compute the size from the source without executing the stages, so counting a stream that has a `peek` logging statement can log nothing at all. Stateful operations — `sorted`, `distinct`, `limit` after `sorted` — must buffer, which removes much of the laziness benefit and can be expensive on large sources. Side effects inside pipelines are discouraged because they interact badly with laziness, ordering and parallelism; the JDK documentation explicitly warns against them. Streams over resources (`Files.lines`) hold file handles and should be closed with try-with-resources.

**Practical backend example:** A pipeline that appears to audit every rejected order but may not:

```java
long rejected = orders.stream()
        .peek(o -> auditLog.record(o))     // unreliable: may be skipped or short-circuited
        .filter(Order::isRejected)
        .count();

// do this instead
List<Order> rejectedOrders = orders.stream().filter(Order::isRejected).toList();
rejectedOrders.forEach(auditLog::record); // explicit, always runs
```

**Common follow-ups:**
- Why did nothing happen? There was no terminal operation, so the pipeline never executed.
- Can a stream be reused? No; create a new stream from the source, or collect once into a list.
- Is `forEach` ordered? Not for parallel streams; use `forEachOrdered` when encounter order matters.
- Why did `peek` not print? `count()` can elide stages, and short-circuiting stops traversal early.

**Mistakes to avoid:** Using `peek` for logging or persistence; mutating an external collection inside `map`; forgetting to close streams backed by I/O; assuming a stream is a data structure you can iterate twice.

**Production perspective:** Side effects hidden inside pipelines make behaviour dependent on optimisations, which is very hard to reproduce in a debugger. Keep pipelines pure and perform I/O in explicit statements where retries, metrics and error handling are visible.

**Related concepts covered:** Short-circuiting, stateful operations, stream closing, forEachOrdered, pure functions.

## Q041. When should you avoid parallel streams?

**Priority:** Must Know  
**Why interviewers ask it:** Parallelism is the easiest place to give a confidently wrong answer, and production incidents follow.

**Interview-ready answer:** Parallel streams are not a general speed switch. By default they run on the shared common ForkJoinPool sized to the number of cores minus one, so any blocking work inside them — a JDBC call, an HTTP request, a lock — starves every other user of that pool, including other parallel streams in the same JVM. They only help for large, CPU-bound, independent work over a source that splits evenly, such as an array or `ArrayList`. They hurt for small collections, for sources that split poorly like `LinkedList` or `Iterator`-based streams, for order-sensitive pipelines, and for anything touching shared mutable state. In a web service, requests are already parallel across threads, so intra-request parallelism usually adds contention rather than throughput.

**In-depth explanation:** `parallelStream()` splits the source with a `Spliterator`, processes segments in fork-join tasks, and combines results. The combine step matters: `collect` with a mutable container needs a proper combiner, and collectors like `groupingBy` must merge maps, which costs allocation. If you must parallelise blocking work, submit the pipeline to your own `ForkJoinPool` — `pool.submit(() -> list.parallelStream()...).get()` — so you do not contaminate the common pool, though a plain `ExecutorService` with explicit tasks is usually clearer. Encounter-order-sensitive operations (`findFirst`, `forEachOrdered`, `limit`, `sorted`) add synchronisation overhead in parallel mode. Any claim about speedup must come from a measurement on representative data, ideally with JMH, not from intuition: JIT warm-up alone can make a naive timing loop misleading.

**Practical backend example:** Hashing a large in-memory batch of documents is a reasonable candidate; enriching records over HTTP is not.

```java
// reasonable: CPU-bound, independent, large, ArrayList source
List<String> digests = documents.parallelStream().map(this::sha256).toList();

// unsafe in a server: blocking I/O on the shared common pool
// List<Profile> profiles = ids.parallelStream().map(httpClient::fetchProfile).toList();
ExecutorService io = Executors.newFixedThreadPool(16); // bounded, dedicated pool instead
```

**Common follow-ups:**
- Which pool runs a parallel stream? The common ForkJoinPool, unless the pipeline is submitted from inside another ForkJoinPool.
- How do you benchmark fairly? Use JMH with warm-up iterations, realistic data sizes and the same JVM flags as production.
- Is `Collectors.toMap` safe in parallel? It works, but prefer `toConcurrentMap` for unordered concurrent collection; either way the merge function must be associative.
- Does `parallel()` guarantee ordering? Results of ordered collectors stay ordered, but `forEach` execution order does not.

**Mistakes to avoid:** Claiming parallel streams are always faster; doing I/O or locking inside them; mutating a shared `ArrayList` from a parallel pipeline; parallelising a 50-element list.

**Production perspective:** Common-pool starvation shows up as unrelated endpoints slowing together, which is very hard to diagnose. If you need concurrency in a service, use an explicit, bounded, named executor whose queue and rejection policy you can monitor.

**Related concepts covered:** ForkJoinPool, spliterators, JMH benchmarking, thread pool isolation, shared mutable state.

## Q042. How do collectors handle grouping, ordering and duplicate keys?

**Priority:** Important  
**Why interviewers ask it:** Collector edge cases — duplicate keys, nulls and map types — are where stream code fails in production rather than in tests.

**Interview-ready answer:** `Collectors.toMap(keyFn, valueFn)` throws `IllegalStateException` when two elements produce the same key, so I supply a merge function when duplicates are possible, and a map supplier when I need a specific map type such as `LinkedHashMap`. `toMap` also rejects null values with a `NullPointerException`, which surprises people migrating from a loop with `map.put`. `groupingBy` never has the duplicate-key problem because it accumulates into a downstream collector, but its classifier must not return null. If I need a specific iteration order I pass a `TreeMap` or `LinkedHashMap` factory, since the default `HashMap` order is unspecified.

**In-depth explanation:** The four-argument `toMap(key, value, merge, mapSupplier)` is the form worth memorising. The merge function receives the existing and the new value and decides the winner — `(first, second) -> first` for "keep earliest", or a real merge for accumulation. `Collectors.toList()` historically returns an `ArrayList` but the API deliberately does not guarantee mutability; `Stream.toList()` (Java 16+) returns an unmodifiable list that does allow nulls, while `Collectors.toUnmodifiableList()` rejects nulls. `joining`, `summarizingInt`, `flatMapping`, `filtering` and `teeing` cover most remaining reporting needs. For concurrency, `groupingByConcurrent` and `toConcurrentMap` are unordered concurrent collectors — meaningful only for parallel, unordered pipelines.

**Practical backend example:** Indexing the latest price per SKU from an unsorted feed:

```java
Map<String, PriceRow> latestBySku = feed.stream()
        .collect(Collectors.toMap(
                PriceRow::sku,
                Function.identity(),
                (a, b) -> a.updatedAt().isAfter(b.updatedAt()) ? a : b, // duplicate policy
                LinkedHashMap::new));                                    // stable order
```

**Common follow-ups:**
- What happens without a merge function? A duplicate key throws `IllegalStateException` at collection time, often only with production data.
- Can `toMap` hold null values? No — it calls `map.merge`, which rejects nulls; use `groupingBy` or a manual loop.
- Is `Collectors.toList()` mutable? In practice yes today, but the contract does not promise it; use `toList()` or `toCollection(ArrayList::new)` deliberately.

**Mistakes to avoid:** Assuming test data has no duplicates; returning `Collectors.toList()` results and mutating them; expecting `groupingBy` keys in encounter order; using concurrent collectors on sequential streams for no benefit.

**Production perspective:** A `toMap` without a merge function is a latent outage: it works until one duplicate arrives from an upstream system. Decide the duplicate policy explicitly and log when a merge actually happens if the duplicates are unexpected.

**Related concepts covered:** toMap merge semantics, unmodifiable results, null handling, concurrent collectors, deterministic ordering.

## Q043. When is a loop clearer or faster than a stream?

**Priority:** Important  
**Why interviewers ask it:** They want engineering judgement, not style dogma in either direction.

**Interview-ready answer:** I use streams when the code reads as a declarative transformation — filter, map, group, collect — because the intent is clearer than the mechanics. I use a plain loop when I need early exit with complex conditions, when I must mutate several accumulators at once, when I need the index, when exceptions make lambda code awkward, or when the body is easier to step through in a debugger. On performance, a simple loop over an `ArrayList` is often slightly faster because it avoids lambda and boxing overhead, but the difference is usually irrelevant compared with a database call; I would only optimise after profiling shows a hot path.

**In-depth explanation:** Streams add allocation: a pipeline object per stage, boxed values unless you use `IntStream`/`LongStream`/`DoubleStream`, and lambda capture objects when they are not stateless. The JIT inlines simple pipelines well, so the gap is small for straightforward work, but megamorphic call sites — the same pipeline shape used with many different lambdas — can inhibit inlining in very hot code. Checked exceptions are a genuine ergonomic problem: a lambda cannot throw a checked exception unless the functional interface declares it, which leads to wrapper helpers that obscure stack traces. Conversely, loops encourage accidental complexity: nested loops with flags and manual index arithmetic are where off-by-one bugs live. A good rule is to keep the pipeline flat and short; if you need a comment to explain a stream, a loop is probably clearer.

**Practical backend example:** Validation that must collect several results and stop early on a fatal error reads better as a loop:

```java
List<String> problems = new ArrayList<>();
for (OrderLine line : order.lines()) {
    if (line.quantity() <= 0) problems.add("quantity must be positive: " + line.sku());
    if (line.sku() == null) return List.of("fatal: missing sku");   // early exit
}
```

**Common follow-ups:**
- Are streams slower? Sometimes marginally, mostly due to allocation and boxing; measure before caring.
- How do you avoid boxing? Use `IntStream`, `LongStream` and `mapToInt` for primitive pipelines.
- How do you handle checked exceptions in a lambda? Wrap them in an unchecked exception at the boundary, or use a loop.

**Mistakes to avoid:** Rewriting readable loops as unreadable one-liners; claiming streams are "always slower"; hiding I/O inside a pipeline; using `Optional` chains where an `if` is clearer.

**Production perspective:** Readability wins in code that on-call engineers must debug at 3 a.m. Reserve micro-optimised loops for measured hot paths and comment why they exist so a future refactor does not undo the reason.

**Related concepts covered:** Primitive streams, boxing costs, JIT inlining, exception handling in lambdas, code review judgement.

## Q044. What is a functional interface, and how do lambdas capture variables?

**Priority:** Important  
**Why interviewers ask it:** Capture rules explain compile errors, memory retention and a real class of concurrency bugs.

**Interview-ready answer:** A functional interface has exactly one abstract method, so a lambda or method reference can implement it; `@FunctionalInterface` makes that intent compile-checked. The standard set is `Function`, `BiFunction`, `Supplier`, `Consumer`, `Predicate`, `UnaryOperator` and the primitive variants. A lambda can capture local variables only if they are final or effectively final, because it captures the value, not the variable. Instance and static fields are captured by reference through `this`, so they can change and are not thread-safe by default. Unlike an anonymous class, a lambda does not create a new `this` — inside it, `this` refers to the enclosing instance.

**In-depth explanation:** The effectively-final rule avoids the confusing semantics of mutable capture and supports safe publication to other threads. The common workaround — capturing an `AtomicInteger` or a one-element array to mutate it — compiles but reintroduces the shared-state problem the rule was avoiding; in a stream, prefer a proper reduction. Lambdas are compiled to `invokedynamic` with a bootstrap that creates the implementation at runtime, so a non-capturing lambda is typically a reused singleton while a capturing lambda allocates per call; that matters only in very hot loops. A capturing lambda stored in a long-lived structure keeps the captured objects — including an implicit `this` — reachable, which is a subtle memory leak when listeners are registered and never removed. Method references come in four flavours: static, bound instance, unbound instance and constructor.

**Practical backend example:** A retry helper parameterised by a supplier, plus a listener that must be removed to avoid retention:

```java
public <T> T withRetry(int attempts, Supplier<T> action) {
    RuntimeException last = null;
    for (int i = 0; i < attempts; i++) {
        try { return action.get(); } catch (RuntimeException e) { last = e; }
    }
    throw last;
}

Money total = withRetry(3, () -> pricingClient.quote(order)); // captures 'order' (effectively final)
```

**Common follow-ups:**
- Why must captured locals be effectively final? The lambda copies the value; allowing reassignment would make the semantics ambiguous and unsafe across threads.
- What does `this` mean inside a lambda? The enclosing instance, not the lambda itself, unlike an anonymous inner class.
- Can a lambda throw a checked exception? Only if the functional interface declares it; otherwise wrap it.

**Mistakes to avoid:** Mutating an array or `AtomicInteger` purely to bypass the capture rule; assuming each lambda evaluation creates a new object; leaking `this` into a long-lived callback registry.

**Production perspective:** Callback-heavy code with captured state is a frequent source of heap growth in long-running services. When registering listeners or cache loaders, make ownership and deregistration explicit.

**Related concepts covered:** invokedynamic, method references, effectively final, memory retention, reductions versus mutation.

## Q045. How would you safely build an immutable collection result?

**Priority:** Important  
**Why interviewers ask it:** Returning internal mutable state is one of the quietest ways to break encapsulation in a service.

**Interview-ready answer:** I return an unmodifiable copy, not the internal collection. `List.copyOf(...)`, `Set.copyOf(...)`, `Map.copyOf(...)` and `Stream.toList()` all produce collections that reject modification. The important caveat is that these are shallow: the elements themselves can still be mutable, so an immutable list of mutable entities does not protect the entities. `Collections.unmodifiableList(internal)` is a view, not a copy — if the backing list changes, the view changes with it, which is usually not what a caller expects. For truly immutable data I combine an immutable container with immutable elements, typically records or value objects.

**In-depth explanation:** There are three distinct concepts: a defensive copy (a new collection with the same references), an unmodifiable view (a wrapper that throws on mutation but reflects backing changes) and a deep copy (new elements too). `List.of` and `copyOf` reject null elements and throw `NullPointerException`, while `Stream.toList()` permits nulls — a difference that bites when mapping data that may be absent. Mutating through an unmodifiable wrapper throws `UnsupportedOperationException` at runtime, not compile time, so the safety is a contract, not a type guarantee. For JPA entities, returning the live collection is worse than a style issue: Hibernate tracks that collection for dirty checking, and callers modifying it can trigger unexpected inserts or deletes at flush time.

**Practical backend example:** An aggregate exposing its lines safely:

```java
@Entity
public class Order {
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private final List<OrderLine> lines = new ArrayList<>();

    public List<OrderLine> lines() { return List.copyOf(lines); }  // callers cannot mutate persistence state
    public void addLine(OrderLine line) { line.assignTo(this); lines.add(line); } // one controlled entry point
}
```

**Common follow-ups:**
- Does `List.copyOf` deep-copy elements? No; the elements are shared, so mutable elements remain mutable.
- What is the difference between a view and a copy? A view reflects later changes to the backing collection; a copy does not.
- Can `List.of` contain null? No; it throws `NullPointerException`, unlike `Stream.toList()`.

**Mistakes to avoid:** Returning the internal `ArrayList` field directly; assuming `unmodifiableList` freezes the data; using `List.of` on a mapped stream that may contain nulls.

**Production perspective:** Immutable returns make concurrency reasoning much simpler and remove a class of "who changed this list?" bugs. The cost is one copy per call, which is negligible for small collections and worth measuring for large hot ones.

**Related concepts covered:** Defensive copying, unmodifiable views, records, JPA collection management, null handling.

## Q046. How do you use computeIfAbsent safely?

**Priority:** Important  
**Why interviewers ask it:** It is the idiomatic map-populating method and also the easiest way to corrupt a map or hang a thread.

**Interview-ready answer:** `computeIfAbsent(key, fn)` computes and inserts a value only when the key is absent or mapped to null, and returns the current value either way, which makes it perfect for multimaps and lazy initialisation. The rule is that the mapping function must be short, side-effect free and must not modify the same map. In `HashMap`, modifying the map inside the function can corrupt it — modern JDKs detect many cases and throw `ConcurrentModificationException`. In `ConcurrentHashMap` the computation runs while the bin is locked, so a recursive update on the same map can deadlock or livelock, and a slow function blocks other writers to that bin.

**In-depth explanation:** The related methods form a family worth knowing: `putIfAbsent` (value already computed), `computeIfAbsent` (lazy creation), `computeIfPresent`, `compute` and `merge` (accumulate). `merge(key, one, Integer::sum)` is the cleanest counter idiom. Returning null from the `computeIfAbsent` function means no mapping is recorded and null is returned — useful for "absent means genuinely missing". In `ConcurrentHashMap`, these methods are atomic, which is exactly why compound sequences like `if (!map.containsKey(k)) map.put(k, v)` should be replaced by them. For caches, `computeIfAbsent` on a plain `HashMap` is not a cache: nothing bounds or evicts it. Use Caffeine or Redis when you need TTL, size limits or metrics.

**Practical backend example:** Building an index of lines per order, and an atomic per-tenant counter:

```java
Map<UUID, List<OrderLine>> byOrder = new HashMap<>();
for (OrderLine line : lines) {
    byOrder.computeIfAbsent(line.orderId(), id -> new ArrayList<>()).add(line);
}

ConcurrentMap<String, AtomicLong> hits = new ConcurrentHashMap<>();
hits.computeIfAbsent(tenantId, t -> new AtomicLong()).incrementAndGet(); // atomic creation
```

**Common follow-ups:**
- Can the mapping function modify the map? No. `HashMap` may throw `ConcurrentModificationException` and `ConcurrentHashMap` can deadlock on the same bin.
- What if the function returns null? No entry is stored and the call returns null.
- How is it different from `putIfAbsent`? `putIfAbsent` requires the value up front; `computeIfAbsent` creates it only when needed.

**Mistakes to avoid:** Doing I/O or a database call inside the mapping function of a `ConcurrentHashMap`; using a plain map as an unbounded cache; replacing atomic map methods with check-then-act sequences.

**Production perspective:** Long-running mapping functions in `ConcurrentHashMap` serialise writers on the same bin, which appears as unexplained latency under load. Keep the function to object construction and perform the expensive work outside the map.

**Related concepts covered:** merge and compute family, atomic map operations, multimap idiom, cache boundaries, ConcurrentHashMap locking.

## Q047. How would you count duplicate events efficiently?

**Priority:** Important  
**Why interviewers ask it:** It is a small coding exercise that reveals collection fluency, null handling and awareness of scale limits.

**Interview-ready answer:** For an in-memory list I build a frequency map: either `map.merge(key, 1L, Long::sum)` in a loop, or `Collectors.groupingBy(key, Collectors.counting())` with a stream. Both are O(n) with O(distinct) memory. If the input is a large stream of events I would not hold it all in memory: I would count in the database with `GROUP BY ... HAVING COUNT(*) > 1`, or use a Redis counter per key with a TTL for a rolling window. If the question is "have I already processed this?", a persisted idempotency key is the right structure, not a map.

**In-depth explanation:** The main trade-off is memory versus fidelity. A `HashMap` of counts is exact but grows with cardinality; for very high-cardinality streams, approximate structures such as a count-min sketch or HyperLogLog trade a bounded error for constant memory. Keys must be immutable and have correct `equals`/`hashCode`, otherwise counts silently split across entries. For concurrent producers, use `ConcurrentHashMap` with `merge` or `LongAdder` values — `LongAdder` scales better than `AtomicLong` under heavy contention. If you also need the top N, avoid sorting the whole map: use a bounded min-heap of size N, which is O(n log N).

**Practical backend example:** Detecting duplicate payment references in a batch, with a bounded top-offenders list:

```java
Map<String, Long> counts = new HashMap<>();
for (PaymentEvent e : events) counts.merge(e.reference(), 1L, Long::sum);

List<Map.Entry<String, Long>> worst = counts.entrySet().stream()
        .filter(e -> e.getValue() > 1)
        .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
        .limit(10)
        .toList();
```

```sql
-- the same job pushed to PostgreSQL when the data already lives there
SELECT reference, COUNT(*) AS occurrences
FROM payment_event
WHERE received_at >= now() - interval '1 day'
GROUP BY reference
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 10;
```

**Common follow-ups:**
- What if the input does not fit in memory? Aggregate in the database, or use a streaming/approximate counter with bounded memory.
- How do you make it thread-safe? `ConcurrentHashMap` with `merge`, or values of type `LongAdder`.
- How do you get the top N without full sorting? Keep a size-N min-heap while scanning.

**Mistakes to avoid:** Using `map.get` plus null checks instead of `merge`; using mutable keys; sorting a huge map just to take ten rows; conflating duplicate detection with idempotency guarantees.

**Production perspective:** Duplicate detection usually exists to protect a side effect — do not send the email twice. The durable answer is a unique constraint or an idempotency key in the database; in-memory counting only helps within one process and is lost on restart.

**Related concepts covered:** merge idiom, groupingBy with counting, LongAdder, approximate counting, idempotency, SQL aggregation.

## Q048. How do you handle nulls in stream pipelines and collectors?

**Priority:** Important  
**Why interviewers ask it:** Null handling differs between apparently interchangeable APIs, and the failures appear only with real data.

**Interview-ready answer:** I filter nulls explicitly and early with `Objects::nonNull`, or better, I stop producing them at the source. The rules worth knowing are: `Stream.of(null)` is fine but `List.of(null)` and `Map.of` reject nulls; `Collectors.toMap` throws `NullPointerException` on a null value; `groupingBy` throws if the classifier returns null; `Collectors.toUnmodifiableList()` rejects nulls while `Stream.toList()` allows them; and `Optional.of(null)` throws while `Optional.ofNullable(null)` gives an empty `Optional`. For mapping functions that may find nothing, I return `Optional` and flatten with `Optional::stream`.

**In-depth explanation:** These differences come from the immutable collection factories deliberately treating null as a programming error, while older APIs tolerated it. The practical consequence is that a refactor from `Collectors.toList()` to `toUnmodifiableList()` can start throwing on data that previously worked. `Comparator.nullsFirst`/`nullsLast` wrap a comparator so sorting does not throw on null keys. `Objects.requireNonNullElse` and `Optional.orElseGet` give explicit defaults. When nulls come from a database column, the cleanest fix is to decide at the mapping layer whether absence means "unknown", "not applicable" or "zero" and encode that in the domain type rather than propagating null into the pipeline.

**Practical backend example:** Building a lookup from rows where an optional column may be null:

```java
Map<String, String> emailByUser = users.stream()
        .filter(u -> u.email() != null)                        // decide the policy explicitly
        .collect(Collectors.toMap(User::username, User::email)); // toMap would throw on a null value

List<String> sortedNames = users.stream()
        .map(User::displayName)
        .sorted(Comparator.nullsLast(Comparator.naturalOrder()))
        .toList();
```

**Common follow-ups:**
- Why did `toMap` throw a `NullPointerException`? It delegates to `merge`, which forbids null values; filter or map them to a sentinel first.
- Can `Stream.toList()` contain null? Yes; `List.copyOf` and `toUnmodifiableList` cannot.
- How do you sort data containing nulls? Wrap the comparator with `Comparator.nullsFirst` or `nullsLast`.

**Mistakes to avoid:** Assuming every immutable-collection factory tolerates null; hiding nulls with `Optional` fields on entities; using `Optional.of` where `ofNullable` is meant.

**Production perspective:** Null-related pipeline failures usually appear as a `NullPointerException` deep inside JDK collector code, with a stack trace that does not name your field. Fail fast at the boundary — validate or normalise on input — so the error message points at the source system.

**Related concepts covered:** Immutable collection factories, Optional semantics, null-safe comparators, boundary validation, error diagnosis.

## Q049. What is the cost of sorting and what comparator mistakes matter?

**Priority:** Important  
**Why interviewers ask it:** Sorting is everywhere in APIs, and a broken comparator throws an exception that most developers have never debugged.

**Interview-ready answer:** Sorting objects is O(n log n) and uses a stable merge sort (TimSort), so equal elements keep their relative order; primitive arrays use a dual-pivot quicksort that is not stable. The comparator must be a total order: consistent, antisymmetric and transitive. If it is not, `Arrays.sort` may throw `IllegalArgumentException: Comparison method violates its general contract!`, usually because someone subtracted ints and overflowed, compared floating point with tolerance, or returned inconsistent results for equal objects. I build comparators with `Comparator.comparing(...).thenComparing(...)` and `Integer.compare` rather than hand-written arithmetic, and I add a tie-breaker so paging is deterministic.

**In-depth explanation:** `a - b` overflows when the difference exceeds `Integer.MAX_VALUE`, silently inverting the sign; `Integer.compare(a, b)` never does. Comparing doubles with an epsilon breaks transitivity, which is exactly what TimSort detects. Sorting mutable objects whose sort keys change after insertion into a `TreeSet` or `PriorityQueue` corrupts the structure. For large result sets, the important realisation is architectural rather than algorithmic: sorting in the database with an index that matches the `ORDER BY` avoids loading and sorting everything in the JVM, and keyset pagination avoids the deep-offset problem entirely. Also remember that stability is what makes multi-pass sorting work, and that `Comparator.reverseOrder()` versus `reversed()` differ in what they reverse.

**Practical backend example:** A deterministic, overflow-safe comparator for a paged listing:

```java
Comparator<Order> byRecency = Comparator
        .comparing(Order::createdAt, Comparator.reverseOrder())
        .thenComparing(Order::id);                 // tie-breaker keeps paging stable

orders.sort(byRecency);
// avoid: (a, b) -> (int) (a.amountCents() - b.amountCents())  // can overflow
```

**Common follow-ups:**
- Why does sorting throw "Comparison method violates its general contract"? TimSort detected an inconsistent comparator, commonly from subtraction overflow or epsilon comparison.
- Is Java's object sort stable? Yes, TimSort is stable; primitive sorts are not, which is invisible because primitives are indistinguishable.
- Why add a tie-breaker for pagination? Without a unique final key, rows can repeat or vanish between pages.

**Mistakes to avoid:** Subtracting to compare; sorting in memory what the database can sort with an index; mutating sort keys of elements inside a `TreeSet`; relying on an unstable sort for multi-key ordering.

**Production perspective:** Deep `OFFSET` pagination combined with in-memory sorting is a classic slow endpoint. Prefer indexed `ORDER BY` with keyset pagination, and sort in Java only for small, already-bounded result sets.

**Related concepts covered:** TimSort stability, comparator contracts, integer overflow, pagination determinism, database sorting and indexes.

## Q050. How would you choose a bounded in-memory data structure?

**Priority:** Bonus  
**Why interviewers ask it:** Unbounded in-memory state is one of the most common causes of memory exhaustion in long-running services.

**Interview-ready answer:** The first question is whether the state must be in memory at all. If it must, it has to be bounded: a maximum size, a TTL, or both. `LinkedHashMap` in access order with an overridden `removeEldestEntry` gives a simple LRU; Caffeine gives size and time eviction, refresh, and hit-rate statistics without writing that logic yourself. If the data must be shared across instances or survive a restart, that is Redis, not a local map. I also make sure the eviction policy matches the access pattern and that cache misses are cheap enough to absorb, because every local cache is also a source of stale data after a deployment or a write on another node.

**In-depth explanation:** A local cache multiplies memory by the number of instances and gives each one a different view of the truth; that is acceptable for reference data that changes rarely and intolerable for balances. Sizing must be expressed in entries or weight, not vague intent, because heap pressure appears as longer GC pauses before it appears as `OutOfMemoryError`. `WeakHashMap` and soft references look attractive but make behaviour depend on GC timing and are rarely the right tool for caching. Bounded queues matter for the same reason: an unbounded `LinkedBlockingQueue` in an executor turns backpressure into heap growth. Finally, measure hit rate; a cache below a useful hit rate adds complexity, memory and staleness with no benefit.

**Practical backend example:** A small LRU for feature flags plus a Caffeine cache with statistics:

```java
Map<String, FeatureFlag> lru = new LinkedHashMap<>(256, 0.75f, true) {
    @Override protected boolean removeEldestEntry(Map.Entry<String, FeatureFlag> eldest) {
        return size() > 1_000;                      // hard bound
    }
};

Cache<String, ExchangeRate> rates = Caffeine.newBuilder()
        .maximumSize(10_000)
        .expireAfterWrite(Duration.ofMinutes(5))    // bounded staleness
        .recordStats()
        .build();
```

**Common follow-ups:**
- When should Redis replace a local map? When data must be shared across replicas, survive restarts, or exceed comfortable heap size.
- Is a `HashMap` cache a memory leak? Effectively yes if nothing bounds or evicts it; it grows with distinct keys until the heap is exhausted.
- What eviction policy should you choose? Size plus TTL is a safe default; access-order LRU suits skewed access, and per-key TTL suits data with known freshness rules.

**Mistakes to avoid:** Caching per-user data locally in a multi-replica deployment; using `WeakHashMap` as a cache; unbounded queues in executors; caching without measuring hit rate or staleness impact.

**Production perspective:** Local caches change failure modes: a deploy invalidates them all at once, which can produce a thundering herd against the database. Stagger TTLs with jitter and make sure the origin can survive a cold cache.

**Related concepts covered:** LRU eviction, Caffeine, Redis trade-offs, GC pressure, backpressure, cache staleness and stampedes.
