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
