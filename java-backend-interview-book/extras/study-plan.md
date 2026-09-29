# 7-Day Interview Preparation Plan

Seven sessions of roughly 90–120 focused minutes: about 40 minutes reading, 30 minutes answering aloud, 30 minutes hands-on, and 10 minutes writing down what you missed. Every one of the 200 questions is assigned exactly once as a primary reading block; the spoken-practice IDs repeat deliberately, because retrieval is what makes an answer available under pressure.

If you have fewer than seven days, run Day 1, Day 4, Day 5 and Day 6 — they carry the largest chapters — and use `top-40.md` for the rest.

## Day 1 — Core Java, OOP and exceptions

**Read:** Chapter 1, Q001–Q030.

**Speak aloud (45–90 s each):** Q001, Q004, Q008, Q012, Q019, Q020, Q027.

**Hands-on:** Implement an immutable `Money` value object with `BigDecimal`, correct `equals`/`hashCode`, and a scale and rounding policy. Write a test that puts it in a `HashSet` and proves lookup works. Then write a small exception hierarchy for a service and map it to HTTP status codes on paper.

**Check yourself:** Can you explain why a mutable field in a hash key loses entries, and why `BigDecimal.equals` is not the same as `compareTo == 0`?

## Day 2 — Collections, generics, streams, and two coding exercises

**Read:** Chapter 2, Q031–Q050. Then Chapter 8, Q179 and Q180.

**Speak aloud:** Q031, Q032, Q036, Q038, Q039, Q041, Q046.

**Hands-on:** Code the first non-repeating character (Q179) and merge intervals (Q180) without an IDE, on paper or in a plain editor, then run them against edge cases: empty input, all duplicates, touching intervals, a string containing an emoji. Then write a `groupingBy` pipeline that produces a summary per customer and handles a null grouping key deliberately.

**Check yourself:** Can you say what `Collectors.toMap` does on a duplicate key, and when a plain loop is the better choice?

## Day 3 — Concurrency, async and the JVM

**Read:** Chapter 3, Q051–Q075.

**Speak aloud:** Q051, Q053, Q055, Q056, Q058, Q064, Q067.

**Hands-on:** Reproduce a lost update with two threads incrementing a shared `int`, then fix it three ways — `synchronized`, `AtomicInteger`, `LongAdder` — and explain when each is appropriate. Then create a `ThreadPoolExecutor` with a bounded queue and a `CallerRunsPolicy`, saturate it, and observe the behaviour. Finally, take a thread dump with `jcmd <pid> Thread.print` and find the state of your pool threads.

**Check yourself:** Can you explain the core-pool, queue, max-pool ordering, and what happens to an exception thrown inside `submit`?

## Day 4 — Spring Framework and Spring Boot

**Read:** Chapter 4, Q076–Q105.

**Speak aloud:** Q076, Q080, Q082, Q085, Q086, Q087, Q099, Q104.

**Hands-on:** Build one vertical slice end to end: controller, service, repository, DTO, Bean Validation, a `@ControllerAdvice` returning `ProblemDetail`, and a transaction boundary in the service. Then deliberately break it — call a `@Transactional` method from within the same bean and watch the transaction not start. Open `/actuator/conditions` and find why one auto-configuration did or did not apply.

**Check yourself:** Can you draw the request path from the servlet container to your controller method and back, naming where validation, security and exception handling sit?

## Day 5 — SQL, transactions, JPA, Hibernate, and a SQL exercise

**Read:** Chapter 5, Q106–Q135. Then Chapter 8, Q181.

**Speak aloud:** Q111, Q112, Q114, Q116, Q119, Q121, Q126, Q129.

**Hands-on:** In a local PostgreSQL instance, write the latest-order-per-customer query (Q106) and the monthly top-customers query (Q181). Run `EXPLAIN (ANALYZE, BUFFERS)` on both, add an index, and compare. Then write a JPA test that proves an N+1 problem exists by counting statements, fix it with an entity graph, and assert the count dropped.

**Check yourself:** Can you explain what flush does that commit does not, and name two reasons an existing index is not used?

## Day 6 — HTTP, REST, microservices and security

**Read:** Chapter 6, Q136–Q160. Then Chapter 7, Q161–Q172.

**Speak aloud:** Q137, Q141, Q143, Q144, Q150, Q162, Q165, Q168.

**Hands-on:** Design a retry-safe `POST /payments` on paper: idempotency key storage, the conflict rule, the timeout and retry policy with a circuit breaker, and the error body shape. Then write the Spring Security configuration for it — deny by default, scope-based rules, and an ownership check in the query — and list the three tests that prove it: 401, 403, 200.

**Check yourself:** Can you explain why CORS does not protect an API, and what makes a retry safe rather than merely repeated?

## Day 7 — Testing, messaging, caching, production, and consolidation

**Read:** Chapter 8, Q173–Q178 and Q182–Q185. Then Chapter 9, Q186–Q195, and Chapter 10, Q196–Q200.

**Speak aloud:** Q173, Q174, Q182, Q187, Q189, Q191, Q197, Q199, Q200.

**Hands-on:** Write one `@DataJpaTest` against a Testcontainers PostgreSQL instance that proves a unique constraint fires. Then rehearse Q200 out loud as a five-minute incident narrative — definition, correlation, layer-by-layer investigation, fix, prevention — because that is the shape of most final-round questions. Finish by reviewing every question you marked as weak on Days 1–6.

**Check yourself:** Can you give the first four things you would check when latency rises after a deploy, and say which evidence distinguishes pool saturation from a slow query?

## Coverage of the plan

| Day | Primary reading | Question IDs | Count |
|---|---|---|---|
| 1 | Chapter 1 | Q001–Q030 | 30 |
| 2 | Chapter 2 + coding exercises | Q031–Q050, Q179, Q180 | 22 |
| 3 | Chapter 3 | Q051–Q075 | 25 |
| 4 | Chapter 4 | Q076–Q105 | 30 |
| 5 | Chapter 5 + SQL exercise | Q106–Q135, Q181 | 31 |
| 6 | Chapters 6 and 7 | Q136–Q160, Q161–Q172 | 37 |
| 7 | Chapters 8, 9 and 10 | Q173–Q178, Q182–Q185, Q186–Q195, Q196–Q200 | 25 |
| | | **Total** | **200** |

Every ID from Q001 to Q200 appears exactly once as a primary assignment. The day before the interview, do not read anything new: speak the Top 40 aloud and re-read only your own notes on what you missed.
