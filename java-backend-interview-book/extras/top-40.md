# Top 40 Questions to Revise First

These forty questions are the ones to rehearse if your interview is soon. The selection is a study judgement about coverage and consequence — questions whose answers unlock several others, and topics where a weak answer is expensive. It is not a claim about measured interview frequency, and no such statistics are used anywhere in this book.

Each row gives the question ID and the reason it earns a place. Speak each answer aloud in 45–90 seconds and answer at least one follow-up before moving on.

| ID | Why start here |
|---|---|
| Q004 | The equals and hashCode contract silently breaks sets, maps and caches, and it is asked constantly. |
| Q008 | Checked versus unchecked exceptions shapes every API boundary you design. |
| Q012 | Immutability is the cheapest defence against shared-state bugs, and it leads into records and thread safety. |
| Q019 | Date, time and time-zone handling is where real APIs quietly produce wrong data. |
| Q020 | Money requires deliberate precision and rounding; floating point here is a visible correctness failure. |
| Q031 | Collection choice by semantics rather than habit is the entry point to the whole collections chapter. |
| Q032 | HashMap internals explain collisions, resizing and why broken keys lose data. |
| Q038 | Grouping and aggregating with streams is the most common practical stream task in backend code. |
| Q041 | Knowing when not to use parallel streams shows judgement rather than enthusiasm. |
| Q051 | Separating visibility from atomicity is the foundation of every concurrency answer. |
| Q053 | Volatile is the most misused keyword in Java; explaining its limits is a strong signal. |
| Q055 | Thread-pool sizing, queueing and rejection are daily production concerns in a Spring service. |
| Q058 | Deadlock detection and prevention comes up whenever concurrency is discussed seriously. |
| Q064 | Virtual threads in Java 21 are current, frequently asked, and easy to get subtly wrong. |
| Q076 | Dependency injection and constructor injection underpins everything in the Spring chapter. |
| Q080 | Auto-configuration explains why a Spring Boot application behaves as it does, and how to debug it. |
| Q082 | The MVC request lifecycle is the map you need for error handling, filters and security questions. |
| Q085 | Proxy-based `@Transactional` and self-invocation is one of the most common real Spring bugs. |
| Q086 | REQUIRED versus REQUIRES_NEW decides whether your rollback behaviour is what you think it is. |
| Q099 | Connection pool configuration connects Spring, the database and production latency in one answer. |
| Q111 | Why an index exists but is not used separates people who read plans from people who guess. |
| Q112 | Reading EXPLAIN ANALYZE calmly is the single most useful database skill in an interview. |
| Q114 | Isolation levels and the anomalies they prevent is the classic transaction question. |
| Q116 | Optimistic versus pessimistic locking is a decision you will be asked to justify, not just define. |
| Q121 | N+1 diagnosis and repair is the most frequently encountered Hibernate performance problem. |
| Q126 | Calling an external service inside a transaction is a design mistake interviewers love to probe. |
| Q137 | Status code choices are a quick, high-signal test of API literacy. |
| Q141 | Idempotency for payment creation is the retry-safety question, and it recurs in Chapters 6 and 9. |
| Q143 | Timeouts, retries and backoff interact in ways that cause outages when misunderstood. |
| Q150 | The end-to-end order workflow is the integrative design question for the REST chapter. |
| Q152 | Preventing duplicate resources from duplicate requests tests constraints, not just controller code. |
| Q162 | Sessions versus JWT is where candidates repeat slogans; a trade-off answer stands out immediately. |
| Q165 | CORS and CSRF are routinely confused, and the confusion leads to disabling the wrong protection. |
| Q168 | Resource-level authorization is the flaw class most often found in real systems. |
| Q173 | A coherent test strategy is a design skill, and it frames every other testing question. |
| Q182 | A systematic method for debugging a slow endpoint is what senior interviewers are listening for. |
| Q187 | At-least-once delivery and idempotent consumers is the core correctness rule of messaging. |
| Q189 | The transactional outbox is the standard answer to dual writes and comes up in system design too. |
| Q197 | Logs, metrics and traces — knowing what each signal is for shows you have operated a service. |
| Q200 | The final integrative question rehearses an end-to-end investigation across every layer. |

## Using this list

- **First pass:** read the interview-ready answer only, and speak it back. Roughly two hours for all forty.
- **Second pass:** answer the follow-ups and read the in-depth explanation for anything that felt shaky.
- **Third pass:** cover the page and answer from the ID alone. Anything you cannot start within five seconds goes on a short list for the day before the interview.

If you have time for only ten, take Q004, Q051, Q085, Q112, Q114, Q121, Q137, Q143, Q173 and Q197 — they span every chapter's core reasoning.
