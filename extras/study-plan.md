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