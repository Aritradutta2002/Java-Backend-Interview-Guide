# Chapter 3. Concurrency, asynchronous programming, and JVM

Baseline is Java 17 on a modern HotSpot JVM with G1 as the default collector. Java 21 features are named explicitly where they change the answer. Garbage collector and JIT behaviour are implementation characteristics of HotSpot, not language guarantees.

## Q051. What makes a race condition, and how do visibility and atomicity differ?

**Priority:** Must Know  
**Why interviewers ask it:** Every later concurrency answer depends on separating "another thread cannot see my write" from "two threads interleaved mid-operation".

**Interview-ready answer:** A race condition is when the correctness of a result depends on the timing of threads. Two distinct mechanisms cause it. Atomicity failures happen when an operation that looks like one step is several: `count++` is a read, an add and a write, so two threads can both read 5 and both write 6. Visibility failures happen when a thread writes a value and another thread never sees it, because the Java Memory Model allows values to be kept in registers or caches and allows reordering unless a happens-before relationship exists. `volatile` fixes visibility and ordering but not atomicity; `synchronized`, locks and atomic classes fix both. Immutability and confinement avoid the problem entirely.

**In-depth explanation:** The JMM defines happens-before: if action A happens-before action B, then A's effects are visible to B. Program order gives it inside one thread; across threads you need a synchronisation edge — unlocking a monitor happens-before a later lock of the same monitor, a `volatile` write happens-before a later read of the same field, `Thread.start()` happens-before everything in the started thread, and everything in a thread happens-before another thread's successful `join()`. Without such an edge the code has a data race, and a data race means the result is not merely "sometimes stale" but undefined by the model. That is why the classic "stop flag" loop can spin forever: the JIT may hoist a non-volatile field read out of the loop, which is a legal transformation for race-free semantics. Note the vocabulary distinction interviewers appreciate: a data race is a specific JMM-level condition, while a race condition is any timing-dependent correctness bug — a check-then-act on a perfectly synchronised map is still a race condition.

**Practical backend example:** A shutdown flag and a counter in a Spring singleton:

```java
@Component
public class ImportJob {
    private volatile boolean running = true;              // visibility only
    private final AtomicLong processed = new AtomicLong(); // atomicity for the increment

    public void stop() { running = false; }

    public void run(List<Row> rows) {
        for (Row row : rows) {
            if (!running) return;      // reliably observes stop() because the field is volatile
            handle(row);
            processed.incrementAndGet();
        }
    }
}
```

**Common follow-ups:**
- Is `count++` atomic? No. It is read-modify-write; use `AtomicLong`, `LongAdder` or a lock.
- Does `volatile` make a counter safe? No; it guarantees each read sees the latest write but not that the increment is indivisible.
- Do 64-bit `long` and `double` have special rules? Non-volatile 64-bit writes are not guaranteed atomic by the JMM, so tearing is theoretically possible; declaring them `volatile` removes that.

**Mistakes to avoid:** Saying `volatile` "synchronises" access; assuming a missing lock only causes occasional staleness rather than undefined behaviour; adding `synchronized` to random methods without identifying the invariant being protected.

**Production perspective:** Concurrency bugs rarely reproduce under a debugger and are timing sensitive, so they appear as rare data corruption or as a job that hangs after a deploy. Design shared state out of existence where possible — stateless beans, immutable objects, per-request data — instead of hunting the bug later.

**Related concepts covered:** Java Memory Model, happens-before, data race versus race condition, volatile semantics, atomic classes, thread confinement.

## Q052. What happens-before guarantees does synchronized provide?

**Priority:** Must Know  
**Why interviewers ask it:** It tests whether you know that a monitor gives visibility as well as mutual exclusion, and where the boundaries of that guarantee lie.

**Interview-ready answer:** `synchronized` acquires the monitor of an object. Only one thread holds it at a time, so the block is mutually exclusive, and releasing the monitor happens-before any later acquisition of the same monitor, so everything written inside the block is visible to the next thread that enters. Monitors are reentrant: a thread already holding the lock can re-enter. The critical detail is that the guarantee is per monitor object — `synchronized` on an instance method locks `this`, on a static method it locks the `Class` object, and two threads locking different objects exclude nobody. I keep critical sections small, never call external services inside them, and never lock on a mutable or shared-by-accident object such as a `String` literal or a boxed `Integer`.

**In-depth explanation:** The lock's memory effects are as important as the exclusion: entering flushes the thread's view so it reads fresh values, exiting publishes writes. This is why a field only ever accessed inside blocks synchronised on the same monitor does not additionally need `volatile`. Choosing the monitor is a design decision: a private `final Object lock = new Object()` prevents callers from locking your instance and causing surprising interactions, whereas `synchronized` methods expose the lock as part of your API. `wait`/`notifyAll` must be called while holding the monitor and `wait` must always be used in a loop, because spurious wakeups are permitted. `ReentrantLock` adds tryLock with timeout, interruptible acquisition, fairness and multiple conditions; plain `synchronized` is simpler and benefits from JVM optimisations, so use the lock class only when you need its extra capabilities. In Java 21, blocking inside `synchronized` can pin a virtual thread to its carrier, which is a reason to prefer `ReentrantLock` in virtual-thread-heavy code.

**Practical backend example:** Guarding a compound invariant in a rate limiter:

```java
public class WindowCounter {
    private final Object lock = new Object();   // private monitor, not exposed to callers
    private long windowStart = System.nanoTime();
    private int count;

    public boolean tryAcquire(int limit, long windowNanos) {
        synchronized (lock) {                   // exclusion + visibility for both fields
            long now = System.nanoTime();
            if (now - windowStart > windowNanos) { windowStart = now; count = 0; }
            return count++ < limit;
        }
    }
}
```

**Common follow-ups:**
- Is `synchronized` reentrant? Yes; the same thread can acquire the same monitor repeatedly, with a hold count.
- Do two `synchronized` methods on different instances block each other? No, unless they are static, in which case they share the class monitor.
- When would you use `ReentrantLock` instead? For `tryLock` with a timeout, interruptible locking, fairness, or multiple condition queues.

**Mistakes to avoid:** Locking on `this` in a public class, on a `String` constant, or on a boxed `Integer` from the cache; performing network or database calls inside a synchronised block; using `notify` when several distinct conditions share one monitor.

**Production perspective:** Long critical sections show up in thread dumps as many threads BLOCKED on the same monitor while CPU sits idle. That pattern — high latency, low CPU — usually means contention, not a slow database.

**Related concepts covered:** Monitor semantics, reentrancy, lock granularity, wait/notify, ReentrantLock, virtual thread pinning.

## Q053. When is volatile sufficient and when is it not?

**Priority:** Must Know  
**Why interviewers ask it:** `volatile` is the most misused keyword in Java concurrency, and misuse produces intermittent, unreproducible bugs.

**Interview-ready answer:** `volatile` guarantees that every read sees the most recent write and prevents the compiler and CPU from reordering surrounding memory operations across it. It is sufficient for a single variable written by one thread and read by others — a status flag, a cached immutable reference, a "configuration reloaded" pointer. It is not sufficient for compound actions: `volatile int count; count++` is still three steps, and `if (instance == null) instance = create();` is still check-then-act. For those I use an atomic class, a lock, or an immutable swap where the whole new state is published as one reference assignment.

**In-depth explanation:** The ordering guarantee is what makes the immutable-swap pattern work: writes to a new object's fields happen-before the volatile write of its reference, so a reader that sees the reference sees a fully constructed object. This is the correct way to publish reloaded configuration. Without `volatile`, safe publication requires some other edge — `final` field semantics, a concurrent collection, a static initialiser or a lock. `volatile` reads are close to free on common hardware; volatile writes are more expensive because they involve a memory barrier, but still far cheaper than lock contention. Two related facts are worth stating: `volatile` does not make the referenced object thread-safe, only the reference itself; and the double-checked locking idiom requires the field to be `volatile` to be correct on the Java Memory Model.

**Practical backend example:** Hot-reloading pricing rules without locking readers:

```java
@Component
public class PricingRules {
    private volatile RuleSet current = RuleSet.empty();     // one-writer, many-readers

    public Money price(Order order) { return current.apply(order); } // always a consistent snapshot

    @Scheduled(fixedDelay = 60_000)
    void reload() {
        RuleSet fresh = ruleLoader.load();  // build fully, then publish atomically
        current = fresh;                    // volatile write publishes the whole object graph
    }
}
```

**Common follow-ups:**
- Is `volatile count++` safe? No; it is a read-modify-write and can lose updates.
- Does `volatile` on a `List` reference make the list thread-safe? No; only the reference assignment is safe. Use a concurrent list or publish an immutable copy.
- Is double-checked locking safe without `volatile`? No; the field must be `volatile` or a reader can see a partially constructed object.

**Mistakes to avoid:** Using `volatile` to protect invariants spanning two fields; assuming it provides mutual exclusion; sprinkling it on fields as a "just in case" fix.

**Production perspective:** The immutable-snapshot-plus-volatile-reference pattern gives lock-free reads for configuration, feature flags and reference data, which is valuable on hot request paths where a shared lock would serialise every request.

**Related concepts covered:** Safe publication, double-checked locking, memory barriers, immutable snapshots, atomic references.

## Q054. When would you use AtomicInteger, LongAdder or a lock?

**Priority:** Important  
**Why interviewers ask it:** It probes whether you understand compare-and-swap, contention and the difference between a counter and an invariant.

**Interview-ready answer:** Atomic classes use compare-and-swap: read the value, compute the new one, and swap it only if nothing changed, retrying otherwise. `AtomicInteger`/`AtomicLong` are ideal for a single counter or flag with low to moderate contention, and `AtomicReference` with `compareAndSet` or `updateAndGet` handles a single mutable reference. Under heavy contention, CAS retries waste CPU, and `LongAdder` performs better because it spreads increments across internal cells and only sums them when you read — the trade-off is that `sum()` is not an atomic point-in-time snapshot. When the invariant spans more than one variable — debit one account and credit another — no atomic class is enough and I use a lock or, in a real system, a database transaction.

**In-depth explanation:** CAS is optimistic: correctness comes from the retry loop, not from blocking, so it scales well until many threads contend on the same cache line. That is the essence of the `LongAdder` design — reduce contention by using more memory. `AtomicReference.updateAndGet` takes a function that may be invoked multiple times, so it must be pure and side-effect free. The classic theoretical hazard is the ABA problem, where a value changes from A to B and back to A and CAS cannot tell; `AtomicStampedReference` adds a version to detect it, and in practice immutable values make ABA irrelevant. Atomics give linearisable single-variable operations only; multi-variable consistency requires a lock, and multi-row consistency requires a database transaction with appropriate isolation.

**Practical backend example:** Per-endpoint metrics counters and a compare-and-set state transition:

```java
private final LongAdder requests = new LongAdder();          // hot path, high contention
private final AtomicReference<JobState> state =
        new AtomicReference<>(JobState.IDLE);

public void onRequest() { requests.increment(); }            // cheap under load
public long requestCount() { return requests.sum(); }        // approximate while updating

public boolean start() {
    return state.compareAndSet(JobState.IDLE, JobState.RUNNING); // only one thread wins
}
```

**Common follow-ups:**
- Is `LongAdder.sum()` a consistent snapshot? No; it can miss concurrent updates, which is fine for metrics and wrong for balances.
- What is the ABA problem? A value returning to its original between reads makes CAS succeed incorrectly; use a stamped reference or immutable values.
- When do atomics stop helping? When the invariant involves multiple variables, or when contention is so high that CAS retries dominate.

**Mistakes to avoid:** Using `AtomicInteger.get()` then `set()` instead of an atomic update; assuming atomics coordinate several fields; using a distributed system's in-memory counter as a business source of truth.

**Production perspective:** In-process counters vanish on restart and differ per replica, so a "count" that matters to the business belongs in the database or a shared store such as Redis. Use atomics for metrics and local coordination, not for money.

**Related concepts covered:** Compare-and-swap, contention and cache lines, ABA, atomic state machines, distributed counters.

## Q055. How do you size and manage an ExecutorService?

**Priority:** Must Know  
**Why interviewers ask it:** Thread pool misconfiguration is one of the most common causes of production outages in Java services.

**Interview-ready answer:** I choose the pool by workload. For CPU-bound work, roughly the number of cores; for blocking I/O, more threads, sized from the target throughput and the average wait time, and always bounded. The queue matters as much as the thread count: with `ThreadPoolExecutor`, if the queue is unbounded the pool never grows beyond the core size and work simply accumulates in memory until the heap dies. I use a bounded queue with an explicit rejection policy — `CallerRunsPolicy` for natural backpressure, or a rejection that returns 503 — and I name the threads so thread dumps are readable. On shutdown I call `shutdown()`, wait with `awaitTermination`, then `shutdownNow()`, and I never let a pool hold work that has already been acknowledged to a client without a durable record.

**In-depth explanation:** `ThreadPoolExecutor`'s algorithm is specific: it creates a thread per task until `corePoolSize`, then queues, then creates threads up to `maximumPoolSize` only when the queue is full, then rejects. So `Executors.newFixedThreadPool` (unbounded `LinkedBlockingQueue`) can never reject and never grows — the failure mode is memory. `Executors.newCachedThreadPool` has the opposite problem: unbounded thread creation under load. Little's law gives a starting point for I/O pools — concurrency equals throughput times latency — but the real constraint is usually downstream: a pool of 200 threads hitting a database with 20 connections just moves the queue. Separate pools per dependency (a bulkhead) stop one slow downstream from consuming every thread. In Spring Boot 3, `@Async` and `@Scheduled` use configurable `TaskExecutor`/`TaskScheduler` beans, and the scheduler defaults to a single thread, which surprises teams whose jobs overlap.

**Practical backend example:** A bounded, named, observable pool for outbound calls:

```java
@Bean(destroyMethod = "shutdown")
public ThreadPoolExecutor notificationExecutor() {
    ThreadPoolExecutor executor = new ThreadPoolExecutor(
            8, 16,                                   // core, max
            60, TimeUnit.SECONDS,
            new ArrayBlockingQueue<>(500),           // bounded: backpressure, not heap growth
            new CustomizableThreadFactory("notify-"),// readable thread dumps
            new ThreadPoolExecutor.CallerRunsPolicy()); // slows producers instead of dropping
    return executor;
}
```

**Common follow-ups:**
- Why are unbounded queues risky? They convert overload into unbounded memory use and hide the pressure until an `OutOfMemoryError`.
- What does `CallerRunsPolicy` do? Runs the task on the submitting thread, throttling the producer naturally.
- Difference between `shutdown()` and `shutdownNow()`? `shutdown()` stops accepting new tasks and drains the queue; `shutdownNow()` also interrupts running tasks and returns the pending ones.
- How many threads for I/O work? Start from target concurrency, verify against downstream limits such as the connection pool, then load test.

**Mistakes to avoid:** Using `Executors.newFixedThreadPool` for load-sensitive work; unnamed threads; forgetting shutdown in tests and in application context close; sizing the pool larger than the database connection pool.

**Production perspective:** Instrument queue depth, active threads, completed count and rejection count. Rising queue depth is the earliest warning signal that a downstream dependency is slowing, usually well before error rates move.

**Related concepts covered:** ThreadPoolExecutor mechanics, backpressure, bulkheads, Little's law, graceful shutdown, pool metrics.

## Q056. How do CompletableFuture failures and timeouts propagate?

**Priority:** Must Know  
**Why interviewers ask it:** Async composition silently swallows errors unless you know exactly which callbacks run on failure.

**Interview-ready answer:** A `CompletableFuture` completes either normally or exceptionally. If it completes exceptionally, `thenApply` and `thenCompose` stages are skipped and the failure propagates down the chain; `exceptionally` and `handle` can recover, and `whenComplete` observes both outcomes without changing them unless it throws. `join()` throws an unchecked `CompletionException` wrapping the cause, while `get()` throws a checked `ExecutionException` — in both cases you must unwrap to find the real error. There is no implicit timeout, so I add `orTimeout` or `completeOnTimeout` (Java 9+); otherwise a hung downstream call blocks a thread forever. For fan-out I use `allOf` and remember it completes exceptionally if any input fails, so I attach per-future recovery when partial results are acceptable.

**In-depth explanation:** Which thread runs a stage matters. The non-async variants (`thenApply`) run on whichever thread completed the previous stage, or on the calling thread if it is already complete — so a heavy continuation can run on a Netty or scheduler thread by accident. The `*Async` variants default to the common ForkJoinPool unless you pass an executor, which you usually should. `supplyAsync` without an executor also uses the common pool, so blocking calls there compete with parallel streams elsewhere in the JVM. Exception wrapping differs subtly between `join` and `get`; `CompletableFuture.completedFuture` plus `exceptionallyCompose` (Java 12+) covers retry-style recovery. Cancellation is weak: `cancel(true)` completes the future with `CancellationException` but does not interrupt the underlying work, so cancellation must be cooperative. In Spring Boot 3, `@Async` methods returning `CompletableFuture` integrate with this model, but the thread does not carry the security context, MDC or transaction unless you propagate them explicitly.

**Practical backend example:** Fan-out with per-call timeout and graceful degradation:

```java
CompletableFuture<Profile> profile = CompletableFuture
        .supplyAsync(() -> profileClient.fetch(userId), ioExecutor)   // explicit pool
        .orTimeout(800, TimeUnit.MILLISECONDS)
        .exceptionally(ex -> Profile.unknown(userId));                // degrade, do not fail the page

CompletableFuture<List<Offer>> offers = CompletableFuture
        .supplyAsync(() -> offerClient.fetch(userId), ioExecutor)
        .completeOnTimeout(List.of(), 500, TimeUnit.MILLISECONDS);

Dashboard dashboard = profile.thenCombine(offers, Dashboard::new).join();
```

**Common follow-ups:**
- Which executor runs continuations? The completing thread for non-async stages, the common pool for `*Async` without an executor, otherwise the executor you pass.
- What does `allOf` do on failure? It completes exceptionally with the first failure; handle each future individually if partial success is acceptable.
- Difference between `handle` and `whenComplete`? `handle` can transform the result or recover; `whenComplete` only observes and re-propagates.
- Does `cancel` stop the running task? No; it completes the future as cancelled but the underlying work continues unless it checks for interruption.

**Mistakes to avoid:** Calling `join()` on the request thread and destroying the benefit of async; omitting timeouts; ignoring the return value of `exceptionally`; assuming MDC, security context or transactions propagate automatically.

**Production perspective:** Async code without timeouts turns a slow dependency into a thread leak. Always pair `orTimeout` with a bounded executor and a metric on rejection and timeout counts, so degradation is visible rather than silent.

**Related concepts covered:** Async composition, exception wrapping, executor selection, timeouts and degradation, context propagation.

## Q057. How is ConcurrentHashMap different from synchronizedMap?

**Priority:** Must Know  
**Why interviewers ask it:** It distinguishes "every method is locked" from "concurrent by design", and exposes the check-then-act trap.

**Interview-ready answer:** `Collections.synchronizedMap` wraps a map and guards every method with one lock, so all operations serialise and iteration still requires manual synchronisation on the wrapper. `ConcurrentHashMap` allows fully concurrent reads without locking and locks only the affected bin on write, so throughput scales with cores. It also provides atomic compound operations — `putIfAbsent`, `computeIfAbsent`, `merge`, `replace` — which is the key point: with either map, `if (!map.containsKey(k)) map.put(k, v)` is a race, because two threads can pass the check. `ConcurrentHashMap` forbids null keys and values, and its iterators are weakly consistent rather than fail-fast, so they never throw `ConcurrentModificationException`.

**In-depth explanation:** Aggregate operations like `size()` and `isEmpty()` are approximations while other threads mutate, by design; if you need an exact count you need external coordination. `computeIfAbsent` runs the mapping function while holding the bin lock, so it must be short and must not update the same map. `ConcurrentHashMap` also offers bulk parallel methods (`forEach`, `reduce`, `search`) with a parallelism threshold, which are rarely needed but good to know. For read-mostly lists, `CopyOnWriteArrayList` is the equivalent trade-off in the other direction: free reads, expensive writes. The general design lesson is that thread-safe components do not compose into a thread-safe workflow: a sequence of individually atomic calls is not atomic, so either use a single atomic operation or guard the whole sequence.

**Practical backend example:** A per-tenant lock registry and an idempotency guard:

```java
private final ConcurrentMap<String, Object> tenantLocks = new ConcurrentHashMap<>();
private final ConcurrentMap<String, Boolean> processed = new ConcurrentHashMap<>();

Object lock = tenantLocks.computeIfAbsent(tenantId, t -> new Object()); // atomic creation

if (processed.putIfAbsent(messageId, Boolean.TRUE) == null) {  // exactly one thread proceeds
    handle(message);                                           // in-process guard only
}
```

**Common follow-ups:**
- Is check-then-put atomic? No; use `putIfAbsent`, `computeIfAbsent` or `merge`.
- Can `ConcurrentHashMap` store null? No, neither keys nor values, because null would be ambiguous with "absent".
- Is `size()` exact? It is an estimate under concurrent modification.
- Does `ConcurrentHashMap` make my service correct across replicas? No; it is per JVM. Cross-instance coordination needs the database or Redis.

**Mistakes to avoid:** Wrapping with `synchronizedMap` and iterating without holding the lock; treating a sequence of atomic calls as atomic; long computations inside `computeIfAbsent`; using a local map to deduplicate work in a multi-instance deployment.

**Production perspective:** An in-memory registry that grows per key — locks, dedup markers, per-user state — is an unbounded cache in disguise. Bound it or give entries a lifetime, and prefer a database unique constraint when duplication must be prevented for real.

**Related concepts covered:** Lock striping, atomic map operations, weakly consistent iterators, composition of thread-safe parts, distributed coordination.

## Q058. How do you identify and prevent deadlocks?

**Priority:** Must Know  
**Why interviewers ask it:** Deadlock diagnosis is a concrete operational skill, and prevention shows you can design lock ordering.

**Interview-ready answer:** A deadlock needs four conditions: mutual exclusion, hold-and-wait, no preemption and a circular wait. The practical prevention is to break the cycle by always acquiring locks in a globally consistent order — for example by sorted entity ID — and to use `tryLock` with a timeout so a thread can back off and retry instead of waiting forever. To diagnose, I take a thread dump with `jstack` or `jcmd`; the JVM explicitly reports "Found one Java-level deadlock" with the participating threads and monitors. The same cycle can occur in the database when two transactions lock rows in opposite order; PostgreSQL detects it and aborts one transaction with a deadlock error, so the application must retry.

**In-depth explanation:** Java monitors are not preemptible and have no timeout, which is why `ReentrantLock.tryLock(timeout)` is valuable for code that cannot be ordered. Lock ordering is the cheapest structural fix: if every code path locks account A before account B by comparing IDs, a cycle cannot form. Reducing lock scope helps too — never hold a lock across an I/O call, because the window for a cycle grows with the hold time. Beyond classic deadlock, watch for livelock, where threads keep responding to each other and make no progress, and for thread-pool starvation deadlock, where tasks in a pool wait on results computed by tasks queued behind them in the same pool; the fix there is separate pools or non-blocking composition. Database deadlocks deserve explicit handling: catch the specific exception, apply jittered retry, and make the operation idempotent so a retry is safe.

**Practical backend example:** Ordered locking for a transfer, and the equivalent database-level ordering:

```java
public void transfer(Account from, Account to, Money amount) {
    Account first  = from.id().compareTo(to.id()) < 0 ? from : to;   // global order
    Account second = first == from ? to : from;
    synchronized (first) {
        synchronized (second) { from.debit(amount); to.credit(amount); }
    }
}
```

```sql
-- the database version: lock rows in a deterministic order inside one transaction
SELECT id, balance FROM account WHERE id IN (:a, :b) ORDER BY id FOR UPDATE;
```

**Common follow-ups:**
- How do you detect a deadlock in production? A thread dump (`jcmd <pid> Thread.print`) names the deadlocked threads and monitors; JMX `ThreadMXBean.findDeadlockedThreads` can alert automatically.
- Can databases deadlock too? Yes; PostgreSQL detects the cycle and aborts one transaction, so retry with backoff.
- Does `tryLock` eliminate deadlock? It prevents indefinite waiting, but you must handle the failure path and avoid livelock.

**Mistakes to avoid:** Acquiring locks in data-dependent order; holding a lock during an HTTP or JDBC call; nesting `synchronized` blocks across layers; retrying a database deadlock without backoff or idempotency.

**Production perspective:** Deadlocks manifest as a subset of requests hanging while CPU stays low, and they often start after a seemingly unrelated change reorders two calls. Automated deadlock detection through `ThreadMXBean` plus an alert saves hours during an incident.

**Related concepts covered:** Lock ordering, tryLock and backoff, thread dumps, pool starvation, database deadlock retries, idempotency.

## Q059. What are safe ways to publish and share mutable objects?

**Priority:** Important  
**Why interviewers ask it:** Safe publication explains why "the object exists but its fields look empty" happens, which is otherwise mystifying.

**Interview-ready answer:** Safe publication means that when another thread sees a reference, it also sees the object's fully initialised state. The guaranteed mechanisms are: initialise it from a static initialiser; store it in a `volatile` field or `AtomicReference`; store it in a final field of a properly constructed object; or place it in a concurrent collection or guard it with a lock. Simply assigning to a plain field is not safe publication, and the reader can observe default values. The simplest strategy is to avoid the problem: make the object immutable with final fields, or confine it to one thread and publish only copies.

**In-depth explanation:** Final field semantics are a specific JMM guarantee: if an object is properly constructed — meaning the `this` reference does not escape during construction — then any thread that sees the reference sees the correctly initialised final fields, with no extra synchronisation. That is what makes immutable value objects and records naturally thread-safe. Escaping `this` breaks it: registering a listener, starting a thread or passing `this` to a collaborator inside the constructor lets another thread see a half-built object. For mutable shared objects there is no shortcut — every access, read and write, must go through the same synchronisation. A useful middle ground is the copy-on-write style: keep the shared state immutable, and replace the whole reference through a volatile field when it changes.

**Practical backend example:** Immutable snapshot plus controlled mutation:

```java
public record TaxTable(Map<String, BigDecimal> ratesByRegion) {          // effectively immutable
    public TaxTable {
        ratesByRegion = Map.copyOf(ratesByRegion);                       // defensive, unmodifiable copy
    }
}

private volatile TaxTable table = new TaxTable(Map.of());                 // safe publication point
public void refresh(Map<String, BigDecimal> fresh) { table = new TaxTable(fresh); }
```

**Common follow-ups:**
- Is a final reference enough? Final field semantics cover the fields of a properly constructed object; they do not make a mutable object it points to thread-safe.
- What does "this escaping" mean? Publishing the instance before the constructor finishes, so other threads can observe partial state.
- Are records thread-safe? Their components are final, so yes for the record itself, provided the component values are themselves immutable.

**Mistakes to avoid:** Starting a thread or registering a callback in a constructor; publishing a builder's mutable internals; assuming that a synchronised setter makes an object safe when getters are unsynchronised.

**Production perspective:** Unsafe publication typically fails rarely and only under load or on certain CPU architectures, so it survives testing and appears in production. Immutability is the cheapest insurance and also makes caching and sharing safe by construction.

**Related concepts covered:** Final field semantics, immutability, this-escape, volatile publication, defensive copies.

## Q060. When are thread-local values helpful and dangerous?

**Priority:** Important  
**Why interviewers ask it:** `ThreadLocal` underpins MDC, security context and transaction management, and it leaks in pooled environments when misused.

**Interview-ready answer:** `ThreadLocal` gives each thread its own copy of a value, which is how frameworks carry ambient context: Spring's `SecurityContextHolder`, request attributes, the transaction-bound `EntityManager`, and SLF4J's MDC. The danger is that application servers reuse threads, so a value left behind is visible to the next unrelated request, which can leak a previous user's identity, and the retained object never becomes garbage. Every `set` needs a matching `remove` in a finally block, normally in a filter or interceptor. With Java 21 virtual threads, thread locals still work but the "few threads, reused" assumption disappears, and scoped values are the direction of travel for immutable context.

**In-depth explanation:** Internally each `Thread` holds a `ThreadLocalMap` whose keys are weak references to the `ThreadLocal` object but whose values are strong. So if the `ThreadLocal` itself is a static field — the normal case — the entry survives as long as the thread does, and in a pool that is the lifetime of the application. This is a classic container class-loader leak during redeploys. `InheritableThreadLocal` copies values to child threads, which sounds convenient but propagates stale context into pool threads unpredictably. The async case is the trickiest: a value set on the request thread is not visible in a `@Async` or `CompletableFuture` continuation, which is why frameworks provide context-propagating decorators. If you only need to pass data down a call chain, a method parameter is simpler, more testable and impossible to leak.

**Practical backend example:** A correlation-ID filter with guaranteed cleanup:

```java
@Component
public class CorrelationIdFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        String id = Optional.ofNullable(request.getHeader("X-Correlation-Id"))
                            .orElseGet(() -> UUID.randomUUID().toString());
        MDC.put("correlationId", id);          // ThreadLocal under the hood
        try {
            chain.doFilter(request, response);
        } finally {
            MDC.remove("correlationId");       // mandatory: threads are pooled
        }
    }
}
```

**Common follow-ups:**
- What happens if you forget `remove()`? The value leaks into the next request handled by that pooled thread and is never collected.
- Does a thread local propagate to `@Async` methods? No, unless you install a task decorator that copies the context.
- What replaces it in Java 21? Scoped values offer immutable, structured context for virtual threads; thread locals still work but do not scale as a per-thread cache.

**Mistakes to avoid:** Using `ThreadLocal` as a general-purpose cache; skipping `remove` on exceptional paths; relying on `InheritableThreadLocal` in pooled executors; storing large objects per thread.

**Production perspective:** A missing `remove` is a genuine security issue — it can attribute one user's action to another in logs, or worse, in authorisation checks. Centralise context management in one filter and test it with concurrent requests.

**Related concepts covered:** MDC and correlation IDs, SecurityContextHolder, context propagation in async code, classloader leaks, virtual threads and scoped values.

## Q061. How would you implement bounded producer-consumer work?

**Priority:** Important  
**Why interviewers ask it:** It is the canonical backpressure design, and it appears in import jobs, batch processing and message consumers.

**Interview-ready answer:** I use a `BlockingQueue` with a fixed capacity between producers and consumers. Producers call `put`, which blocks when the queue is full, or `offer` with a timeout when I would rather reject than wait; consumers call `take`. The bound is the entire point: it applies backpressure to the producer instead of letting an unbounded queue consume the heap. For shutdown I use a poison-pill sentinel or interrupt the consumers and drain. If the work must survive a crash, an in-memory queue is the wrong tool and the queue belongs in Kafka, a database table or a broker.

**In-depth explanation:** `ArrayBlockingQueue` has a fixed array and optional fairness; `LinkedBlockingQueue` can be bounded or unbounded and has separate put and take locks, which often gives better throughput; `SynchronousQueue` has no capacity and hands off directly, which is what `newCachedThreadPool` uses; `PriorityBlockingQueue` is unbounded and ordered; `DelayQueue` releases elements at a time. Choosing the saturation policy is a business decision: block the producer, drop the oldest, drop the newest, or reject with an error to the caller. In a web application the last option is usually correct — return 429 or 503 quickly rather than queue work the user is no longer waiting for. Consumers should handle `InterruptedException` by restoring the flag and exiting, and any partially consumed work should be idempotent so a restart cannot double-apply it.

**Practical backend example:** A bounded ingestion pipeline with a poison pill:

```java
private static final Row POISON = new Row(null);
private final BlockingQueue<Row> queue = new ArrayBlockingQueue<>(1_000); // hard bound

void produce(Stream<Row> rows) throws InterruptedException {
    for (Row row : (Iterable<Row>) rows::iterator) queue.put(row);        // blocks when full
    for (int i = 0; i < consumerCount; i++) queue.put(POISON);
}

void consume() {
    try {
        for (Row row = queue.take(); row != POISON; row = queue.take()) persist(row);
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();   // restore the flag and stop
    }
}
```

**Common follow-ups:**
- What should happen at saturation? Choose deliberately: block (backpressure), reject fast (429/503), or shed low-priority work. Silent unbounded growth is never acceptable.
- How do you stop consumers cleanly? A poison pill per consumer, or interruption plus a drain loop.
- Why not an unbounded queue? It converts overload into memory exhaustion and long GC pauses, and it hides the problem from metrics.

**Mistakes to avoid:** Using `add` instead of `put`/`offer` and getting `IllegalStateException` on a full queue; swallowing `InterruptedException`; assuming in-memory queues survive a restart; making the consumer non-idempotent.

**Production perspective:** Queue depth is a leading indicator: export it as a gauge and alert on sustained growth. A queue that is always full means the consumer is the bottleneck; a queue that is always empty means the producer is.

**Related concepts covered:** Backpressure, BlockingQueue variants, graceful shutdown, interruption, durability boundaries, queue metrics.

## Q062. What do CountDownLatch and Semaphore solve?

**Priority:** Important  
**Why interviewers ask it:** Choosing the right coordination primitive shows you can express intent rather than improvise with sleeps and flags.

**Interview-ready answer:** `CountDownLatch` is a one-shot gate: threads wait until a counter reaches zero, which suits "wait for N parallel calls to finish" or "wait until initialisation completes". It cannot be reset. `CyclicBarrier` is the reusable version where a fixed number of threads meet repeatedly. `Semaphore` limits concurrent access to a resource by handing out a fixed number of permits — the right tool for "at most 10 simultaneous calls to this legacy system". `Phaser` generalises barriers with dynamic registration. In modern code I often express the same fan-out with `CompletableFuture.allOf`, but a semaphore remains the clearest way to cap concurrency.

**In-depth explanation:** The distinction that matters is one-shot versus reusable, and counting-down versus permit-holding. A latch's `await` returns immediately once the count hits zero forever after, which makes it ideal for readiness signals; always use the timed `await` in production code so a lost countdown cannot hang a thread indefinitely. A semaphore's permits must be released in a `finally` block, otherwise permits leak and the system slowly grinds to a halt — a subtle bug that looks like a gradual slowdown. `tryAcquire` with a timeout gives fast failure instead of waiting, which is usually what an HTTP handler wants. Fair mode for both lock and semaphore eliminates starvation at a throughput cost. Note that these are all in-process: limiting concurrency across replicas requires a distributed mechanism such as a Redis-based limiter or a database token.

**Practical backend example:** Capping concurrency against a fragile downstream system:

```java
private final Semaphore legacyPermits = new Semaphore(10);   // at most 10 in flight

public Report fetchReport(String id) {
    if (!legacyPermits.tryAcquire()) {                        // fail fast under load
        throw new TooManyRequestsException("legacy system saturated");
    }
    try {
        return legacyClient.fetch(id);
    } finally {
        legacyPermits.release();                              // always release
    }
}
```

**Common follow-ups:**
- Can a latch be reset? No; use `CyclicBarrier` or a new latch instance.
- What happens if a permit is never released? Capacity shrinks permanently; always release in `finally`.
- How do you limit concurrency across instances? A distributed limiter — Redis counters with expiry, or a gateway rate limit — because these primitives are per JVM.

**Mistakes to avoid:** Using `Thread.sleep` as a coordination mechanism; untimed `await` calls; releasing a semaphore on a different code path than the acquire; assuming in-process limits protect a shared downstream.

**Production perspective:** Semaphores are the simplest bulkhead: they stop one slow dependency from consuming all request threads. Pair the limit with metrics for rejections so capacity decisions are based on data.

**Related concepts covered:** Bulkhead pattern, fail-fast versus waiting, CyclicBarrier and Phaser, distributed rate limiting, fairness.

## Q063. How should interruption be handled?

**Priority:** Must Know  
**Why interviewers ask it:** Swallowed `InterruptedException` is the reason services refuse to shut down, and it is visible in almost every legacy codebase.

**Interview-ready answer:** Interruption is a cooperative cancellation request, not a forced stop. Calling `interrupt()` sets a flag; blocking methods such as `sleep`, `wait`, `take` and `join` throw `InterruptedException` and clear the flag as they do so. The two correct responses are to propagate the exception, or to catch it and restore the flag with `Thread.currentThread().interrupt()` before returning, so callers up the stack can still see the cancellation. Long CPU-bound loops should check `Thread.currentThread().isInterrupted()` periodically, because nothing will throw for them. Swallowing the exception with an empty catch or a log line destroys shutdown behaviour.

**In-depth explanation:** `Future.cancel(true)` interrupts the running thread; `ExecutorService.shutdownNow()` interrupts all workers. If those interrupts are ignored, `awaitTermination` times out and the JVM hangs on shutdown, which in Kubernetes becomes a SIGKILL after the grace period and potentially lost in-flight work. Interruption does not unblock everything: a socket read on a classic blocking stream or a JDBC call will not throw `InterruptedException`, which is why network timeouts must be configured separately. Also note that `InterruptedIOException` and channel-based I/O behave differently. Inside a task, treat interruption as a request to stop promptly and leave state consistent — commit or roll back, release resources, then exit.

**Practical backend example:** A cancellable worker that stays responsive during shutdown:

```java
public void process(BlockingQueue<Job> queue) {
    while (!Thread.currentThread().isInterrupted()) {   // CPU-bound check
        Job job;
        try {
            job = queue.poll(1, TimeUnit.SECONDS);      // throws on interrupt
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();         // restore the flag
            break;                                      // exit promptly
        }
        if (job != null) handle(job);
    }
}
```

**Common follow-ups:**
- Why restore the interrupt flag? Because catching the exception cleared it, and callers or the pool rely on it to know cancellation was requested.
- Does `interrupt()` stop a running thread? No; it requests cancellation, and code must cooperate.
- What about blocking I/O? Classic socket reads are not interruptible; use socket and HTTP client timeouts instead.

**Mistakes to avoid:** `catch (InterruptedException e) { }`; logging and continuing as if nothing happened; using `Thread.stop()`, which is unsafe and removed; relying on interruption to cancel a JDBC query.

**Production perspective:** Correct interruption handling is what makes rolling deployments safe: the container sends SIGTERM, Spring Boot closes the context, executors stop, and in-flight work finishes or aborts cleanly within the grace period.

**Related concepts covered:** Cooperative cancellation, shutdownNow, graceful shutdown, I/O timeouts, Future.cancel semantics.

## Q064. What are virtual threads in Java 21 and when should you use them?

**Priority:** Important  
**Why interviewers ask it:** It checks whether you can evaluate a new platform feature honestly instead of treating it as a universal speed-up.

**Interview-ready answer:** Virtual threads, finalised in Java 21, are lightweight threads scheduled by the JVM onto a small pool of carrier platform threads. When a virtual thread blocks on most JDK I/O it unmounts from its carrier, so the operating system thread is free to run something else. That makes the thread-per-request model viable at very high concurrency without rewriting code in a reactive style. They do not make CPU-bound work faster — parallelism is still limited by cores — and they are not a replacement for bounded concurrency, because you still need to limit pressure on databases and downstream services. You do not pool virtual threads; you create one per task, typically through `Executors.newVirtualThreadPerTaskExecutor()`.

**In-depth explanation:** The main caveats in Java 21 are pinning and resource limits. A virtual thread that blocks inside a `synchronized` block or during a native call is pinned to its carrier and cannot unmount, so heavily synchronised blocking code can exhaust carriers; the guidance is to prefer `ReentrantLock` on such paths (later JDK releases reduce this restriction, so state the version you are assuming). Thread locals still work but per-thread caching patterns become expensive when there are a million threads; scoped values are the intended replacement. Because tasks are cheap, the bottleneck moves downstream: unbounded virtual threads can open more JDBC connections than the pool has, so you still need semaphores or pool limits. Spring Boot 3.2+ can run web requests on virtual threads with a single property, which is the easiest way to benefit for I/O-bound services.

**Practical backend example:** Fanning out many blocking calls with structured, bounded concurrency:

```java
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {   // Java 21
    List<Future<Quote>> futures = suppliers.stream()
            .map(s -> executor.submit(() -> quoteClient.fetch(s)))   // blocking call is fine
            .toList();
    for (Future<Quote> f : futures) collect(f.get());
}
```

```properties
# Spring Boot 3.2+ : handle web requests on virtual threads
spring.threads.virtual.enabled=true
```

**Common follow-ups:**
- Do virtual threads speed up CPU-bound work? No; throughput there is bounded by cores, and the extra scheduling adds no benefit.
- Should you pool them? No; create one per task. Pooling exists to amortise expensive platform threads, which virtual threads are not.
- What is pinning? A virtual thread blocked inside a `synchronized` block or native frame cannot unmount from its carrier in Java 21; prefer `ReentrantLock` there.
- Do they remove the need for limits? No; the database connection pool and downstream services still need bounded concurrency.

**Mistakes to avoid:** Calling them "faster threads"; keeping a fixed pool of virtual threads; assuming existing `synchronized`-heavy code scales unchanged; forgetting that the JDBC pool remains the real constraint.

**Production perspective:** For an I/O-bound Spring service, enabling virtual threads can raise concurrency substantially with minimal code change, but capacity planning shifts to the database and downstream quotas. Measure connection pool saturation and downstream error rates before and after.

**Related concepts covered:** Thread-per-request scaling, carrier threads and pinning, structured concurrency, scoped values, connection pool limits.

## Q065. How do you avoid oversubscription when composing async calls?

**Priority:** Important  
**Why interviewers ask it:** Fan-out looks harmless in code review and is a common cause of downstream overload.

**Interview-ready answer:** Oversubscription happens when concurrency multiplies: 200 request threads each firing 10 parallel downstream calls is 2,000 in-flight requests that no downstream system agreed to. I control it with explicit bounded executors per dependency, a semaphore or client-level connection limit, and timeouts on every call so slow work releases capacity. I also avoid sharing one pool across unrelated dependencies, because a bulkhead per dependency prevents one slow service from consuming all capacity. Finally, I make the degradation explicit: return partial results or a cached value instead of queueing indefinitely.

**In-depth explanation:** The total in-flight work equals request concurrency times per-request fan-out, capped by whichever pool is smallest. Three layers usually enforce limits: the HTTP client connection pool (max connections and per-route maximum), the executor running the tasks, and an explicit semaphore for a fragile dependency. A common hidden multiplier is using the ForkJoin common pool by default, which is sized to cores and shared by everything, so it both limits and entangles unrelated work. Timeouts must be smaller than the caller's timeout and should include connect, read and overall request deadlines; without a deadline, retries stack on top of a slow dependency and amplify load. Circuit breakers close the loop by stopping calls entirely when error rates spike, giving the downstream time to recover.

**Practical backend example:** Bounded fan-out with a dedicated pool, a client limit and a deadline:

```java
private final ExecutorService pricingPool =
        new ThreadPoolExecutor(8, 8, 0L, TimeUnit.MILLISECONDS,
                new ArrayBlockingQueue<>(100), new CustomizableThreadFactory("pricing-"),
                new ThreadPoolExecutor.AbortPolicy());     // reject instead of piling up

public List<Price> priceAll(List<Sku> skus) {
    List<CompletableFuture<Price>> calls = skus.stream()
            .map(sku -> CompletableFuture
                    .supplyAsync(() -> pricingClient.price(sku), pricingPool)
                    .orTimeout(300, TimeUnit.MILLISECONDS)
                    .exceptionally(ex -> Price.unavailable(sku)))   // degrade per item
            .toList();
    return calls.stream().map(CompletableFuture::join).toList();
}
```

**Common follow-ups:**
- How many parallel downstream calls are safe? Whatever the downstream can absorb; derive it from its published limits and verify with load tests, not intuition.
- Why not use the common ForkJoinPool? It is shared JVM-wide and sized for CPU work, so blocking calls there affect unrelated code.
- What happens when the bound is hit? Decide explicitly: reject fast, queue briefly with a bounded queue, or degrade to a cached response.

**Mistakes to avoid:** Unbounded `CompletableFuture` fan-out; retries without a budget; sharing one executor for all integrations; timeouts longer than the caller's own timeout.

**Production perspective:** Fan-out amplification turns a small downstream slowdown into a service-wide outage. Bulkheads plus deadlines plus circuit breakers are the standard defence, and each should emit metrics so saturation is observable.

**Related concepts covered:** Bulkheads, deadlines and timeouts, circuit breakers, connection pools, graceful degradation, retry amplification.

## Q066. What memory areas does the JVM use for an application?

**Priority:** Must Know  
**Why interviewers ask it:** Without a mental map of JVM memory you cannot interpret an `OutOfMemoryError` or size a container correctly.

**Interview-ready answer:** The heap holds all objects and is where garbage collection happens; it is split into young and old generations for generational collectors like G1. Each thread has its own stack holding frames, locals and references — that is where `StackOverflowError` comes from. Metaspace holds class metadata and lives in native memory, so it is not bounded by `-Xmx`. There is also the JIT code cache, thread structures, GC bookkeeping, and direct or mapped byte buffers used by NIO and some drivers. That last group matters in containers: total process memory is heap plus all native areas, so a container limit equal to `-Xmx` will be killed by the OOM killer.

**In-depth explanation:** Objects are allocated in the young generation's eden space, usually via a thread-local allocation buffer so allocation is a pointer bump. Surviving objects are copied between survivor spaces and eventually promoted to the old generation. Large objects may be allocated directly in old space or, in G1, in humongous regions. Strings are interned in the heap since Java 7. Metaspace grows dynamically and can be capped with `-XX:MaxMetaspaceSize`; leaks there usually come from dynamic class generation or repeated redeploys. Modern JVMs are container-aware: they read cgroup limits and size the heap from `-XX:MaxRAMPercentage`, which is the recommended way to configure Kubernetes workloads rather than a fixed `-Xmx`. Native Memory Tracking (`-XX:NativeMemoryTracking=summary` with `jcmd VM.native_memory`) is the tool for attributing non-heap growth.

**Practical backend example:** Container-aware sizing for a Spring Boot service:

```dockerfile
ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=70 -XX:+HeapDumpOnOutOfMemoryError \
  -XX:HeapDumpPath=/tmp/heap.hprof -XX:NativeMemoryTracking=summary"
# container memory limit 1Gi -> heap ~700Mi, leaving room for metaspace, stacks and buffers
```

**Common follow-ups:**
- Where do class metadata and locals live? Metadata in metaspace (native memory), locals and frames on the thread stack.
- Why was my container killed although the heap looked fine? Non-heap memory — stacks, metaspace, direct buffers, GC overhead — counts toward the limit.
- What causes `StackOverflowError`? Deep or infinite recursion exhausting one thread's stack, tunable with `-Xss` but usually a bug.

**Mistakes to avoid:** Setting `-Xmx` equal to the container limit; assuming metaspace is part of the heap; ignoring direct buffer usage from HTTP clients and serialisation libraries; treating thread count as free when each thread reserves stack space.

**Production perspective:** Always enable `-XX:+HeapDumpOnOutOfMemoryError` with a writable path, and ensure the dump survives pod restarts through a mounted volume. Without the dump, diagnosing a memory incident after the fact is guesswork.

**Related concepts covered:** Generational heap layout, metaspace, thread stacks, direct buffers, container awareness, heap dumps.

## Q067. How does garbage collection impact latency and throughput?

**Priority:** Must Know  
**Why interviewers ask it:** GC knowledge separates "restart the service" from "understand what the pause graph is telling you".

**Interview-ready answer:** Garbage collection trades CPU and pause time for automatic memory management. Generational collectors exploit the observation that most objects die young: minor collections of the young generation are frequent but short, while old-generation work is less frequent and more expensive. G1, the default since Java 9, is region-based, collects concurrently and aims at a pause target you can set. ZGC and Shenandoah push pauses to single-digit milliseconds at some throughput cost, which suits latency-sensitive services. The practical points are that a full GC is not automatically a leak, that high allocation rate — not just heap size — drives GC cost, and that the fix for GC pressure is usually to allocate less or bound caches rather than to enlarge the heap.

**In-depth explanation:** Key signals are allocation rate, promotion rate, pause duration distribution and the proportion of time spent in GC. Continuous full GCs with little memory reclaimed indicate a real leak or an undersized heap; frequent long young collections often mean a very high allocation rate or an oversized young generation. Enlarging the heap reduces collection frequency but can lengthen individual pauses for older collectors; G1 mitigates this by collecting a subset of regions. `-XX:MaxGCPauseMillis` is a goal, not a guarantee. GC logs (`-Xlog:gc*`) and JDK Flight Recorder are the right diagnostic tools; a simple metric such as `jvm.gc.pause` from Micrometer is enough to alert on. Note that GC does not compact native memory, does not free direct buffers promptly, and cannot reclaim objects that are still referenced, which is why a growing cache looks exactly like a leak.

**Practical backend example:** Enabling useful GC observability without guessing:

```properties
# JVM flags
-Xlog:gc*:file=/var/log/app/gc.log:time,uptime:filecount=5,filesize=20M
-XX:+UseG1GC -XX:MaxGCPauseMillis=200
```

```java
// Micrometer exposes jvm.gc.pause, jvm.memory.used and jvm.gc.memory.promoted automatically
@Bean
MeterBinder jvmGcMetrics() { return new JvmGcMetrics(); }
```

**Common follow-ups:**
- Is a full GC always a leak? No; it can be triggered by heap pressure, metaspace, or an explicit `System.gc()`. A leak shows as heap-after-GC trending upward over time.
- Which collector should you choose? G1 for general services; ZGC or Shenandoah when tail latency matters more than raw throughput; measure rather than assume.
- Does a bigger heap always help? It reduces frequency but can increase pause length and hide leaks; it also costs container memory.

**Mistakes to avoid:** Calling `System.gc()`; quoting pause numbers as guarantees; tuning flags before measuring allocation behaviour; blaming GC for latency without checking GC logs.

**Production perspective:** Track heap used after collection rather than instantaneous heap. A sawtooth returning to the same baseline is healthy; a rising baseline is a leak. Correlate pause spikes with request latency percentiles before tuning anything.

**Related concepts covered:** Generational hypothesis, G1/ZGC trade-offs, allocation rate, GC logging, leak versus pressure, Micrometer JVM metrics.

## Q068. How would you investigate increasing heap usage?

**Priority:** Must Know  
**Why interviewers ask it:** It is a realistic incident scenario that reveals whether you have actually debugged memory problems.

**Interview-ready answer:** First I confirm it is a leak rather than normal variation by looking at heap used after full collections over hours or days; a rising floor is the signal. Then I capture a heap dump — either automatically on `OutOfMemoryError` or on demand with `jcmd GC.heap_dump` — and open it in a tool such as Eclipse MAT, which shows the dominator tree and leak suspects. I look for the largest retained sets and ask what is holding the reference: usually an unbounded cache or map, a collection in a static field, accumulating `ThreadLocal` values, unclosed resources, or listeners never deregistered. I fix ownership and bound the structure rather than raising `-Xmx`, which only delays the failure.

**In-depth explanation:** Retained size is the important metric, not shallow size: it tells you how much memory would be freed if the object were collected. `jcmd <pid> GC.class_histogram` gives a quick class-count view without a full dump, and JFR can record allocation profiles with modest overhead in production. Distinguish leak classes: a genuine leak (references retained forever), a cache with no eviction (bounded by traffic, unbounded in effect), memory pressure from oversized working sets such as loading whole tables, and native memory growth, which will not appear in a heap dump at all — that needs Native Memory Tracking. In Spring applications, common culprits are `@Component` beans with mutable collections, static registries, un-evicted Hibernate second-level or session caches during batch jobs, and streaming responses accumulated in memory instead of streamed.

**Practical backend example:** Capturing evidence safely and fixing an unbounded cache:

```bash
jcmd <pid> GC.heap_info                    # current occupancy
jcmd <pid> GC.class_histogram | head -25   # quick top classes by size
jcmd <pid> GC.heap_dump /tmp/heap.hprof    # full dump (pauses the JVM briefly)
```

```java
// before: unbounded, grows with distinct keys forever
private final Map<String, Quote> cache = new ConcurrentHashMap<>();
// after: bounded with eviction and metrics
private final Cache<String, Quote> cache = Caffeine.newBuilder()
        .maximumSize(50_000).expireAfterWrite(Duration.ofMinutes(10)).recordStats().build();
```

**Common follow-ups:**
- Can a cache be a memory leak? Effectively yes, if nothing bounds or evicts it.
- What if the heap dump looks small but the container still dies? Suspect native memory: direct buffers, metaspace, thread stacks; use Native Memory Tracking.
- Does a heap dump pause the application? Yes, briefly, and it writes a file roughly the size of the live heap, so plan disk and timing.

**Mistakes to avoid:** Raising `-Xmx` as the fix; restarting before collecting evidence; analysing a dump taken after a restart; ignoring `ThreadLocal` and classloader leaks in redeployed applications.

**Production perspective:** Make the evidence automatic: heap dump on OOM to a persisted volume, GC logs retained, and memory metrics scraped continuously. In an incident you rarely get a second chance to capture the failing state.

**Related concepts covered:** Retained size and dominator trees, heap dumps and JFR, unbounded caches, ThreadLocal leaks, native memory tracking.

## Q069. How do heap OOM and native/thread exhaustion differ?

**Priority:** Important  
**Why interviewers ask it:** The message text tells you where to look, and picking the wrong remedy wastes an incident.

**Interview-ready answer:** `OutOfMemoryError: Java heap space` means live objects exceed the heap: look for leaks, oversized working sets or an undersized heap. `Metaspace` means class metadata exhausted native memory, usually from dynamic class generation or repeated redeploys. `unable to create new native thread` means the OS or container refused another thread — too many threads, or a thread/process limit, not a heap problem. `Direct buffer memory` points at NIO buffers, often an HTTP client or serialisation library, governed by `-XX:MaxDirectMemorySize`. `GC overhead limit exceeded` means the collector is running constantly and reclaiming almost nothing, which is a heap problem in disguise. Raising `-Xmx` only helps the first and last, and can make thread exhaustion worse by leaving less room for stacks.

**In-depth explanation:** Each Java thread reserves stack space (typically around 512 KB to 1 MB), so thousands of platform threads consume gigabytes of native memory before doing any work — one of the motivations for virtual threads. In containers, the cgroup memory limit counts everything: heap, metaspace, stacks, code cache, direct buffers and JVM overhead, so heap should be a percentage of the limit rather than all of it. An `OutOfMemoryError` is an `Error`, not an `Exception`; catching it is almost always wrong because the JVM state is unreliable afterwards, and the usual configuration is `-XX:+ExitOnOutOfMemoryError` so an orchestrator can restart a clean instance. Note that a container kill by the Linux OOM killer produces no Java error at all — the process simply disappears with exit code 137, which is itself a diagnostic clue.

**Practical backend example:** Distinguishing the failure modes from evidence:

```text
java.lang.OutOfMemoryError: Java heap space          -> heap dump, look for retained sets
java.lang.OutOfMemoryError: Metaspace                -> class loading, redeploy leaks
java.lang.OutOfMemoryError: unable to create new native thread -> thread count, ulimits, pool sizes
java.lang.OutOfMemoryError: Direct buffer memory     -> NIO buffers, client library settings
exit code 137, no Java error                          -> container limit exceeded (kernel OOM killer)
```

**Common follow-ups:**
- Does raising `-Xmx` fix every OOM? No; it is irrelevant for metaspace, native thread and direct buffer exhaustion, and it can worsen them in a fixed-size container.
- Should you catch `OutOfMemoryError`? Generally no; fail fast and let the orchestrator restart the instance.
- How do you find the thread count? `jcmd Thread.print | grep -c 'java.lang.Thread.State'` or JVM metrics; compare with pool configuration.

**Mistakes to avoid:** Assuming every OOM is a leak; catching and continuing; setting a huge heap in a small container; creating one thread per task with platform threads.

**Production perspective:** Alert on both JVM heap metrics and container memory working set, and record exit codes. Exit code 137 with no stack trace is a container-limit problem and needs a different fix from a Java heap error.

**Related concepts covered:** OOM taxonomy, thread stack cost, container limits and cgroups, direct memory, fail-fast configuration.

## Q070. What do JIT warm-up and profiling mean for benchmarks?

**Priority:** Important  
**Why interviewers ask it:** It guards against confident but unsupported performance claims, which is exactly what this book avoids.

**Interview-ready answer:** HotSpot starts by interpreting bytecode, then compiles hot methods with C1 and later C2, using runtime profiles to inline, unroll and eliminate code. So the first thousands of iterations are unrepresentative, and a naive timing loop measures the interpreter plus compilation. JMH exists to handle warm-up, forking, dead-code elimination and statistics correctly. Even then, results are specific to the JVM version, flags, hardware and data shape, which is why I avoid quoting benchmark numbers as universal facts. For production questions I prefer profiling the real system — JFR or async-profiler — over microbenchmarks, because real bottlenecks are usually I/O, locks or GC rather than raw code speed.

**In-depth explanation:** The JIT can also deoptimise: an optimisation based on a profile, such as a monomorphic inline cache, is discarded when a new implementation class appears, so a benchmark that exercises one implementation will overstate speed for a polymorphic production path. Dead-code elimination is the classic microbenchmark trap — if a result is unused, the compiler may remove the computation entirely; JMH's `Blackhole` prevents that. Other confounders are constant folding of fixed inputs, on-stack replacement, GC interference and CPU frequency scaling. Class loading and framework initialisation also make the first requests to a Spring Boot application slower, which is why readiness probes and warm-up requests matter more than they appear to.

**Practical backend example:** A correctly structured microbenchmark and a production profile:

```java
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
@Warmup(iterations = 5) @Measurement(iterations = 10) @Fork(2)
@State(Scope.Benchmark)
public class SerializationBenchmark {
    private ObjectMapper mapper; private OrderDto order;
    @Setup public void setup() { mapper = new ObjectMapper(); order = OrderDto.sample(); }
    @Benchmark public String serialize() throws Exception { return mapper.writeValueAsString(order); }
}
```

```bash
# production profiling instead of guessing
jcmd <pid> JFR.start name=app settings=profile duration=120s filename=/tmp/app.jfr
```

**Common follow-ups:**
- Why not benchmark with `System.currentTimeMillis()`? It has coarse resolution, ignores warm-up and cannot prevent dead-code elimination; use JMH with `System.nanoTime()` semantics handled for you.
- What is deoptimisation? Reverting a speculative optimisation when its assumption breaks, such as a second implementation class appearing.
- Are microbenchmark results transferable? Only within the same JVM, flags, hardware and data shape; always re-measure in context.

**Mistakes to avoid:** Timing a cold loop; benchmarking with unrealistic constant inputs; reporting a single run; optimising code paths that the profiler shows are not hot.

**Production perspective:** Continuous profiling in a canary instance gives better information than any microbenchmark, and JFR's overhead is low enough for routine use. Base optimisation decisions on flame graphs and latency percentiles, not on intuition.

**Related concepts covered:** Tiered compilation, deoptimisation, JMH methodology, JDK Flight Recorder, profiling versus benchmarking, warm-up effects.

## Q071. How do you read a thread dump during a latency incident?

**Priority:** Important  
**Why interviewers ask it:** Reading a dump is a hands-on skill; it immediately distinguishes people who have handled incidents.

**Interview-ready answer:** I take two or three dumps a few seconds apart with `jcmd <pid> Thread.print`, because a single snapshot cannot show whether threads are stuck or simply busy. Then I group threads by pool name and state. Many threads BLOCKED on the same monitor means lock contention; many WAITING on a connection pool means the database is the bottleneck; many TIMED_WAITING in a socket read means a slow downstream; RUNNABLE threads in application code with high CPU means real work or a hot loop. If the same stack appears in every dump, it is stuck; if it changes, it is progressing. The JVM also reports detected deadlocks explicitly at the end of the dump.

**In-depth explanation:** Thread names are the most valuable diagnostic asset, which is why executors should always get a thread factory with a meaningful prefix — `http-nio-8080-exec-*`, `hikari-pool-1-connection-adder`, `kafka-consumer-*`. HikariCP starvation appears as request threads waiting in `getConnection`, often with a helpful HikariPool log line about pool stats. A pool with all threads in `parkNanos` inside `ForkJoinPool.managedBlock` suggests blocking work on the common pool. Combine the dump with CPU data: `top -H -p <pid>` gives per-thread CPU, and converting the thread ID to hex lets you find the matching `nid=` in the dump — that is how you identify a spinning thread. JFR gives the same information with timeline context and lower manual effort.

**Practical backend example:** Correlating a hot thread with its stack:

```bash
jcmd $(pgrep -f myapp.jar) Thread.print > dump1.txt; sleep 5
jcmd $(pgrep -f myapp.jar) Thread.print > dump2.txt
top -H -p $(pgrep -f myapp.jar)        # note the top TID, e.g. 4812
printf '%x\n' 4812                      # -> 12cc, then grep 'nid=0x12cc' dump2.txt
grep -c 'java.lang.Thread.State: BLOCKED' dump2.txt
```

**Common follow-ups:**
- What indicates pool starvation? All worker threads busy or waiting while the queue grows, plus requests timing out before being processed.
- BLOCKED versus WAITING? BLOCKED means waiting to acquire a monitor; WAITING means parked until another thread signals, for example in a queue or lock condition.
- Why take several dumps? To distinguish stuck threads from threads that are simply doing work.

**Mistakes to avoid:** Drawing conclusions from one dump; ignoring thread names; assuming RUNNABLE means consuming CPU (a socket read can appear RUNNABLE); restarting the process before capturing evidence.

**Production perspective:** Make dumps easy to take in production — a documented `kubectl exec` command or an operator runbook — and store them alongside the incident timeline. Combined with connection pool and GC metrics, a dump usually identifies the bottleneck within minutes.

**Related concepts covered:** jcmd and jstack, thread states, connection pool starvation, CPU-to-thread correlation, JFR, incident runbooks.

## Q072. What happens if a task throws inside execute versus submit?

**Priority:** Important  
**Why interviewers ask it:** Silently swallowed background exceptions are a classic production blind spot.

**Interview-ready answer:** With `execute(Runnable)`, an uncaught exception propagates out of the worker, the thread's `UncaughtExceptionHandler` runs (the default prints to stderr), and the pool replaces the thread. With `submit(...)`, the exception is captured inside the returned `Future` and nothing is logged; if nobody calls `get()`, the failure is completely invisible. That is why background tasks should either use `execute`, or wrap the body in try/catch with logging and metrics, or always inspect the `Future`. For scheduled tasks the consequence is worse: with `scheduleAtFixedRate`, an uncaught exception cancels all future executions of that task, so a job can stop silently.

**In-depth explanation:** `submit` wraps the task in a `FutureTask` that stores the throwable and rethrows it, wrapped in `ExecutionException`, when `get()` is called. `CompletableFuture` behaves similarly — an exceptional completion is invisible unless a stage observes it, which is why every chain should end in `exceptionally`, `handle` or `whenComplete` that logs. You can also override `ThreadPoolExecutor.afterExecute` to centralise logging for both styles, or set a `Thread.UncaughtExceptionHandler` via the thread factory. In Spring, `@Async` methods returning `void` route exceptions to an `AsyncUncaughtExceptionHandler` you can configure, while methods returning a future behave like `submit`. Scheduled task cancellation deserves special emphasis because the symptom — "the nightly job stopped running three weeks ago" — is usually discovered far too late.

**Practical backend example:** Making background failures visible in Spring:

```java
@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {
    @Override public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        return (ex, method, params) ->
                LoggerFactory.getLogger(AsyncConfig.class)
                        .error("async failure in {}", method.getName(), ex);  // never silent
    }
}

@Scheduled(fixedDelay = 60_000)
public void reconcile() {
    try { reconciliationService.run(); }
    catch (Exception e) { log.error("reconciliation failed", e); }   // keeps the schedule alive
}
```

**Common follow-ups:**
- How do you observe `submit` failures? Call `get()`, or wrap the task body, or override `afterExecute` in the executor.
- Why did my scheduled task stop? An uncaught exception from `scheduleAtFixedRate` cancels subsequent runs; catch inside the task.
- Does `CompletableFuture` log failures? No; attach `exceptionally`/`whenComplete` or the error disappears.

**Mistakes to avoid:** Fire-and-forget `submit` with no inspection; catching `Exception` and logging at debug level; assuming the framework reports background errors; letting a scheduled job die silently.

**Production perspective:** Add a metric counter for background task failures and alert on it. Logs alone are easy to miss; a counter at zero that suddenly moves is actionable, and a job that stopped running is detectable by a freshness metric on its output.

**Related concepts covered:** FutureTask semantics, UncaughtExceptionHandler, @Async error handling, scheduled task cancellation, background observability.

## Q073. How do you prevent lost updates in a shared in-memory counter?

**Priority:** Important  
**Why interviewers ask it:** It connects a small concurrency exercise to the distributed version of the same problem.

**Interview-ready answer:** In one JVM, the fix is to make the read-modify-write atomic: `AtomicLong.incrementAndGet`, `LongAdder.increment`, a `synchronized` block, or `ConcurrentHashMap.merge`. Across multiple instances, in-memory state cannot work at all, because each replica has its own copy. Then the counter must live somewhere shared: a single SQL statement such as `UPDATE ... SET count = count + 1` (atomic at the database), a Redis `INCR`, or an optimistic-locking update with a version column that retries on conflict. The general rule is that the update must happen where the data is authoritative, not in application memory.

**In-depth explanation:** Lost updates happen whenever a value is read into a variable, modified and written back without a guarantee that nothing changed in between. The three standard remedies map cleanly across layers: atomic instructions (CAS) in memory, atomic statements or row locks in the database, and atomic commands in Redis. Optimistic locking — `UPDATE ... WHERE version = :expected` — is preferable when conflicts are rare because it avoids holding locks; pessimistic locking with `SELECT ... FOR UPDATE` suits high-contention rows. A read-then-write in the application combined with `@Transactional` alone does not prevent lost updates unless the isolation level or an explicit lock enforces it, since at READ COMMITTED both transactions can read the same value. For counters that tolerate approximation, per-instance aggregation flushed periodically reduces contention significantly.

**Practical backend example:** The same increment at three layers:

```java
private final AtomicLong inFlight = new AtomicLong();       // per JVM only
inFlight.incrementAndGet();
```

```sql
-- authoritative and atomic in PostgreSQL, no read-modify-write in the application
UPDATE inventory SET reserved = reserved + 1
WHERE sku = :sku AND reserved < available;   -- also enforces the invariant
```

```java
// optimistic locking with JPA; retry on OptimisticLockException
@Version private long version;
```

**Common follow-ups:**
- Is `@Transactional` enough to stop lost updates? No; at READ COMMITTED two transactions can read the same value. Use an atomic statement, a version check or a row lock.
- What about a distributed counter? Use Redis `INCR` or a database column; in-memory counters diverge per replica and vanish on restart.
- When is optimistic better than pessimistic? When conflicts are rare; it avoids lock holding but requires retry handling.

**Mistakes to avoid:** Using a local cache as the source of truth; `select` then `save` without a version; ignoring `OptimisticLockException` instead of retrying; assuming a synchronised method protects anything across replicas.

**Production perspective:** Counters that drive business outcomes — inventory, credit limits, quotas — must be enforced by a database constraint or an atomic statement. Application-level checks are advisory and race under concurrency.

**Related concepts covered:** Atomic operations, optimistic and pessimistic locking, isolation levels, Redis atomic commands, retry with backoff.

## Q074. What are the trade-offs between blocking and nonblocking APIs?

**Priority:** Important  
**Why interviewers ask it:** It tests architectural judgement and immunity to hype in either direction.

**Interview-ready answer:** Blocking, thread-per-request code is simple: the stack trace is the story, debugging and profiling work normally, and transactions and thread-bound context are straightforward. Its cost is a thread per in-flight request, which limits concurrency when work is I/O-bound. Non-blocking or reactive code multiplexes many in-flight operations onto few threads, giving higher concurrency per unit of memory, but it costs readability, harder debugging, a different programming model end to end, and it fails badly if any library in the chain blocks. Reactive improves throughput and resource efficiency; it does not reduce the latency of a single call. In Java 21, virtual threads offer much of the scalability benefit while keeping blocking code, which makes them the pragmatic default for many services.

**In-depth explanation:** The decision depends on where the bottleneck is. If a service is database-bound, the connection pool caps concurrency long before threads do, so reactive plumbing adds complexity without capacity. If a service fans out to many slow HTTP dependencies and must hold tens of thousands of concurrent connections, non-blocking pays off. Mixed stacks are the real danger: one blocking JDBC call inside a reactive pipeline blocks an event-loop thread and can stall the whole application, which is why reactive systems need R2DBC or a bounded dedicated scheduler for blocking work. Backpressure is a genuine advantage of reactive streams, since demand is signalled explicitly, whereas blocking systems rely on bounded pools and queues for the same effect. Observability differs too: stack traces in reactive code are fragmented, so tracing context propagation must be configured deliberately.

**Practical backend example:** Choosing the model per workload:

```java
// Blocking, transactional, database-bound: simplest and perfectly scalable behind a bounded pool
@Transactional
public Order place(OrderRequest request) { return orderRepository.save(Order.from(request)); }

// Non-blocking client for a high-fan-out, latency-tolerant aggregation
Flux<Quote> quotes = Flux.fromIterable(suppliers)
        .flatMap(s -> webClient.get().uri(s.url()).retrieve().bodyToMono(Quote.class)
                        .timeout(Duration.ofMillis(300))
                        .onErrorResume(e -> Mono.empty()), 8);   // bounded concurrency
```

**Common follow-ups:**
- Does reactive always improve latency? No; it improves resource efficiency and concurrency. A single request is not faster and may be marginally slower.
- What breaks a reactive pipeline? Any blocking call on an event-loop thread; use a dedicated scheduler or a non-blocking driver.
- Where do virtual threads fit? They give thread-per-request code much better scalability without the reactive programming model.

**Mistakes to avoid:** Adopting reactive for a database-bound CRUD service; mixing blocking JDBC into an event loop; claiming reactive reduces latency; ignoring the operational cost of a less debuggable model.

**Production perspective:** The scarce resource is usually the database connection pool or a downstream quota, not threads. Fix the real bottleneck first; the programming model should follow the measurement.

**Related concepts covered:** Thread-per-request versus event loop, backpressure, R2DBC, virtual threads, tracing in async code, bottleneck analysis.

## Q075. How would you diagnose a service with high CPU but low throughput?

**Priority:** Bonus  
**Why interviewers ask it:** It is an integrative question requiring JVM, concurrency and observability knowledge together.

**Interview-ready answer:** I start with the cheap signals: GC metrics, thread states and request latency percentiles. High CPU with low throughput usually means the CPU is doing work that is not progress — most often garbage collection thrash, lock contention with spinning, an accidental hot loop, or excessive serialisation and logging. I check the proportion of time in GC and heap after collection first, because a nearly full heap causes constant collections that look like application CPU. Then I take thread dumps and per-thread CPU to find the hot stacks, or attach a profiler such as JFR or async-profiler to get a flame graph. The fix follows the evidence: bound a cache, remove a hot allocation, reduce lock scope, or fix the loop.

**In-depth explanation:** Distinguish three CPU consumers: application code, GC threads and the JIT compiler. `top -H` plus a dump attributes them precisely; GC threads are typically named `GC Thread#n` or `G1 Conc#n`. Very frequent full collections with small reclaimed amounts indicate heap pressure; in that state throughput collapses while CPU stays pinned. Lock contention with `synchronized` shows as BLOCKED threads and moderate CPU, while spin-heavy CAS contention shows as high CPU in `Unsafe` or atomic operations. Other common causes are regular expression backtracking on user input, debug-level logging of large payloads, JSON serialisation of oversized responses, and per-request creation of expensive objects like `ObjectMapper`, `SecureRandom` or a compiled `Pattern`. Flame graphs make these obvious in minutes compared with hours of guessing.

**Practical backend example:** A profiling sequence and a typical fix:

```bash
kubectl top pod api-7d9f                   # confirm the container is CPU-bound
jcmd 1 JFR.start name=diag settings=profile duration=60s filename=/tmp/diag.jfr
jcmd 1 GC.heap_info                        # heap after GC rising? -> pressure, not code
```

```java
// typical culprit: per-request construction of expensive, thread-safe objects
private static final ObjectMapper MAPPER = new ObjectMapper();              // reuse
private static final Pattern SKU = Pattern.compile("^[A-Z]{3}-\\d{6}$");    // compile once
```

**Common follow-ups:**
- What metrics do you inspect first? GC time and heap after collection, thread pool saturation, latency percentiles, then CPU by thread.
- How do you find a hot method quickly? A flame graph from JFR or async-profiler; a single stack sample is not enough.
- Could the cause be outside the JVM? Yes — noisy neighbours, CPU throttling from cgroup quotas, or encryption overhead; check throttling counters in Kubernetes.

**Mistakes to avoid:** Scaling out before diagnosing, which multiplies the cost of the same waste; assuming high CPU means efficient work; profiling only in a development environment with unrepresentative data.

**Production perspective:** CPU throttling in containers is a frequently missed cause: a low CPU limit makes the application appear slow while the JVM still sees many cores and sizes its thread pools accordingly. Always check throttling metrics and align pool sizes with the actual CPU quota.

**Related concepts covered:** Flame graphs and JFR, GC thrash, lock contention, cgroup CPU limits, object reuse, latency percentiles.
