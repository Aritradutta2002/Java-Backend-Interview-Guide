# Master Question Plan

**Stack:** Java 17/21, Spring Boot 3, PostgreSQL, JPA/Hibernate, JUnit 5, Mockito, Redis, Kafka and Docker. Each line records ID, title, priority, concepts, likely follow-up, and selection rationale. Priority reflects study value, not measured interview frequency.

## 1. Core Java, OOP, exceptions, and language fundamentals (30)

| ID | Question title | Priority | Main concepts | Likely follow-up | Why it belongs |
|---|---|---|---|---|---|
| Q001 | How would you apply encapsulation, abstraction, inheritance and polymorphism in an order service? | Must Know | OOP; domain boundaries | Where would you avoid inheritance? | Grounds OOP in maintainable backend design. |
| Q002 | When would you choose an interface, abstract class or concrete class? | Must Know | contracts; default methods; shared state | Can an interface hold state? | Tests extension design without rote definitions. |
| Q003 | Why prefer composition over inheritance in service design? | Must Know | delegation; coupling; testability | When is inheritance still appropriate? | Prevents fragile hierarchies in application code. |
| Q004 | What is the equals and hashCode contract, and how can it break a HashSet? | Must Know | equality; hashing; mutability | Should entities use generated IDs in equality? | A frequent source of subtle data bugs. |
| Q005 | How is Comparable different from Comparator, and what must ordering agree with? | Important | natural order; sorting; equality | What happens in TreeSet with inconsistent ordering? | Connects ordering to collection correctness. |
| Q006 | Why are Strings immutable, and how do StringBuilder and the pool affect code? | Must Know | strings; concatenation; pooling | Is `==` safe for strings? | Combines language basics with performance. |
| Q007 | What is pass-by-value in Java, including object references? | Must Know | parameter passing; aliasing | Can a method replace its caller's object? | Clears a persistent debugging misconception. |
| Q008 | How do checked and unchecked exceptions influence API design? | Must Know | exception taxonomy; boundaries | When should you wrap an exception? | Tests recoverability and service-layer contracts. |
| Q009 | How would you design exception handling for a Spring service? | Must Know | domain exceptions; translation; logging | Where should an exception be logged? | Makes error handling actionable, not decorative. |
| Q010 | How does try-with-resources work and what happens with suppressed exceptions? | Important | AutoCloseable; resource safety | Which exception is primary? | Essential for reliable I/O and JDBC code. |
| Q011 | What do final, finally and finalize mean in modern Java? | Important | final; cleanup; deprecated finalization | Is final a deep immutability guarantee? | Avoids legacy cleanup mistakes. |
| Q012 | How do you make a class truly immutable? | Must Know | defensive copies; safe publication | Are unmodifiable views enough? | Valuable for safe DTO and concurrent design. |
| Q013 | When are records suitable for backend DTOs, and when are they not? | Important | records; shallow immutability; JPA | Can a record be a JPA entity? | Clarifies a modern Java feature's boundaries. |
| Q014 | How should Optional be used at service boundaries? | Must Know | absence; return types; anti-patterns | Should fields or parameters be Optional? | Prevents null-handling APIs from getting worse. |
| Q015 | What is the difference between overloading and overriding? | Important | dispatch; inheritance; signatures | Can static methods be overridden? | Underpins polymorphic behavior and API design. |
| Q016 | How do access modifiers and packages shape a module's API? | Important | visibility; encapsulation | Is protected visible to every class in a package? | Helps keep implementation details private. |
| Q017 | What happens during class loading and static initialization? | Important | initialization order; classloader | What if static initialization fails? | Explains startup and initialization failures. |
| Q018 | How do primitives, wrappers and autoboxing create bugs? | Must Know | null; caches; numeric conversion | Why can `Integer == Integer` mislead? | Exposes common correctness and hot-path issues. |
| Q019 | How would you handle dates, times and time zones in an API? | Must Know | Instant; LocalDate; ZoneId | Where should UTC conversion happen? | Production-critical temporal correctness. |
| Q020 | How should BigDecimal be used for money? | Must Know | precision; scale; rounding | Why can equals differ from compareTo? | Avoids financial rounding defects. |
| Q021 | When should you use enums rather than strings or booleans? | Important | domain states; parsing; evolution | How do you handle unknown enum values? | Improves domain modeling and compatibility. |
| Q022 | What does a sealed hierarchy buy you in Java 17? | Bonus | permitted subtypes; exhaustive modeling | How does it compare with an enum? | Modern alternative for closed result types. |
| Q023 | How do switch expressions and pattern matching differ across Java 17 and 21? | Important | version compatibility; exhaustive switch | Which patterns are finalized in Java 21? | Prevents suggesting unavailable syntax in Java 17. |
| Q024 | What do annotations do, and when is reflection appropriate? | Important | metadata; runtime processing | Does an annotation execute by itself? | Supports understanding Spring magic. |
| Q025 | How would you design a value object for an email address? | Important | validation; equality; immutability | Where should normalization occur? | Turns language rules into domain design. |
| Q026 | What are the risks of mutable keys and shallow copies? | Important | aliasing; HashMap; cloning | Does `List.copyOf` deep-copy elements? | Catches corruption caused by shared references. |
| Q027 | How do you avoid null-related bugs without hiding invalid states? | Must Know | validation; Optional; nullability | When is null meaningful? | Tests disciplined boundary design. |
| Q028 | What is the difference between fail-fast validation and accumulating errors? | Important | Bean Validation; domain invariants | Where should each happen? | Useful for request and business-rule handling. |
| Q029 | How would you refactor a long conditional into a maintainable strategy? | Important | polymorphism; strategy; registry | When is a switch simpler? | Tests pragmatic extensibility. |
| Q030 | What makes a Java API backward-compatible for callers? | Important | signatures; behavior; serialization | Can adding an enum constant break clients? | Introduces safe change management. |

## 2. Collections, generics, streams, and functional Java (20)

| ID | Question title | Priority | Main concepts | Likely follow-up | Why it belongs |
|---|---|---|---|---|---|
| Q031 | How do you choose among List, Set and Map in a service? | Must Know | semantics; complexity; ordering | How do you preserve insertion order? | Starts with the right abstraction. |
| Q032 | How does HashMap locate a key, handle collisions and resize? | Must Know | hash buckets; equality; capacity | Is iteration order stable? | Explains real lookup behavior and pitfalls. |
| Q033 | When would you use ArrayList versus LinkedList? | Important | locality; indexing; insertion | Does O(1) linked insertion include search? | Tests complexity beyond Big-O slogans. |
| Q034 | Which Set implementation fits deduplication, order or sorting? | Important | HashSet; LinkedHashSet; TreeSet | What comparator equality caveat exists? | Practical collection selection. |
| Q035 | How do iterators and fail-fast behavior work? | Important | structural modification; iterator remove | Is ConcurrentModificationException guaranteed? | Prevents unsafe mutation assumptions. |
| Q036 | What do generic type parameters and wildcards protect? | Must Know | invariance; bounds; PECS | Why is List<Dog> not List<Animal>? | Makes reusable APIs type-safe. |
| Q037 | What does type erasure mean for overloads and runtime checks? | Important | erasure; bridge methods | Can you create `new T()`? | Explains generic runtime limits. |
| Q038 | How would you group and aggregate orders with streams? | Must Know | map; filter; groupingBy; reducing | What about duplicate map keys? | Tests everyday data transformation. |
| Q039 | What is the difference between map and flatMap? | Must Know | flattening; Optional; streams | How do you flatten nested lists? | Removes common pipeline confusion. |
| Q040 | How do lazy streams and terminal operations affect side effects? | Must Know | laziness; encounter order | Why did peek not run? | Prevents hidden behavioral bugs. |
| Q041 | When should you avoid parallel streams? | Must Know | fork-join; state; blocking | How do you benchmark fairly? | Avoids unsafe performance advice. |
| Q042 | How do collectors handle grouping, ordering and duplicate keys? | Important | Collectors; merge function | Is groupingBy concurrent? | Important reporting implementation detail. |
| Q043 | When is a loop clearer or faster than a stream? | Important | readability; allocation; profiling | Should streams always be avoided in hot paths? | Rewards judgment rather than style dogma. |
| Q044 | What is a functional interface, and how do lambdas capture variables? | Important | SAM; effectively final | Can a captured local variable change? | Explains lambda semantics in service code. |
| Q045 | How would you safely build an immutable collection result? | Important | copyOf; unmodifiable views | Can nested values still mutate? | Prevents accidental shared-state leaks. |
| Q046 | How do you use computeIfAbsent safely? | Important | map updates; side effects | Should mapping functions modify the map? | Covers a common cache-like operation. |
| Q047 | How would you count duplicate events efficiently? | Important | frequency map; merge | What if the input is concurrent? | Useful small coding interview problem. |
| Q048 | How do you handle nulls in stream pipelines and collectors? | Important | null filtering; Optional | Do all collectors accept null? | Catches runtime surprises. |
| Q049 | What is the cost of sorting and what comparator mistakes matter? | Important | stable sort; transitivity | Can subtraction implement numeric comparison? | Links algorithmic and correctness concerns. |
| Q050 | How would you choose a bounded in-memory data structure? | Bonus | memory limits; eviction; cache | When should Redis replace local state? | Connects collection choices to production scale. |

## 3. Concurrency, asynchronous programming, and JVM (25)

| ID | Question title | Priority | Main concepts | Likely follow-up | Why it belongs |
|---|---|---|---|---|---|
| Q051 | What makes a race condition, and how do visibility and atomicity differ? | Must Know | JMM; data races | Is `count++` atomic? | Core concurrency reasoning. |
| Q052 | What happens-before guarantees does synchronized provide? | Must Know | monitors; visibility | Is synchronized reentrant? | Connects locking to the memory model. |
| Q053 | When is volatile sufficient and when is it not? | Must Know | visibility; ordering; compound actions | Is volatile increment safe? | Prevents broken shared counters. |
| Q054 | When would you use AtomicInteger, LongAdder or a lock? | Important | CAS; contention; invariants | Is LongAdder a linearizable snapshot? | Practical counter design. |
| Q055 | How do you size and manage an ExecutorService? | Must Know | queues; rejection; shutdown | Why are unbounded queues risky? | Production thread-pool hygiene. |
| Q056 | How do CompletableFuture failures and timeouts propagate? | Must Know | composition; exception handling | What executor runs continuations? | Makes async orchestration reliable. |
| Q057 | How is ConcurrentHashMap different from synchronizedMap? | Must Know | concurrent access; compound operations | Is check-then-put atomic? | Shared map correctness. |
| Q058 | How do you identify and prevent deadlocks? | Must Know | lock order; thread dump | Can database deadlocks also occur? | Troubleshooting essential. |
| Q059 | What are safe ways to publish and share mutable objects? | Important | safe publication; immutability | Is a final reference enough? | Prevents subtle visibility defects. |
| Q060 | When are thread-local values helpful and dangerous? | Important | context; cleanup; pools | What happens after thread reuse? | Relevant to request context leaks. |
| Q061 | How would you implement bounded producer-consumer work? | Important | BlockingQueue; backpressure | What should happen at saturation? | Practical concurrency design. |
| Q062 | What do CountDownLatch and Semaphore solve? | Important | coordination; permits | Can a latch reset? | Distinguishes coordination primitives. |
| Q063 | How should interruption be handled? | Must Know | cancellation; interrupt flag | Why restore interrupt after catching? | Prevents shutdown failures. |
| Q064 | What are virtual threads in Java 21 and when should you use them? | Important | blocking I/O; pinning; scaling | Do they make CPU work faster? | Version-specific concurrency choice. |
| Q065 | How do you avoid oversubscription when composing async calls? | Important | executors; fan-out; limits | How many parallel downstream calls are safe? | Real service reliability issue. |
| Q066 | What memory areas does the JVM use for an application? | Must Know | heap; stacks; metaspace | Where do class metadata and locals live? | Basis for diagnosing memory symptoms. |
| Q067 | How does garbage collection impact latency and throughput? | Must Know | allocation; pauses; collectors | Is a full GC always a leak? | Sensible performance discussion. |
| Q068 | How would you investigate increasing heap usage? | Must Know | heap dump; retention; metrics | Can a cache be a memory leak? | Practical production diagnosis. |
| Q069 | How do heap OOM and native/thread exhaustion differ? | Important | memory limits; thread stacks | Does raising `-Xmx` fix every OOM? | Avoids incorrect incident fixes. |
| Q070 | What do JIT warm-up and profiling mean for benchmarks? | Important | JIT; allocation; JMH | Why not benchmark with currentTimeMillis? | Prevents unsupported performance claims. |
| Q071 | How do you read a thread dump during a latency incident? | Important | blocked; waiting; runnable | What indicates pool starvation? | Operational troubleshooting skill. |
| Q072 | What happens if a task throws inside execute versus submit? | Important | Future; uncaught exception | How do you observe submit failures? | Prevents silent background errors. |
| Q073 | How do you prevent lost updates in a shared in-memory counter? | Important | synchronization; atomics | What about a distributed counter? | Bridges coding and distributed correctness. |
| Q074 | What are the trade-offs between blocking and nonblocking APIs? | Important | I/O; complexity; capacity | Does reactive always improve latency? | Guides architecture pragmatically. |
| Q075 | How would you diagnose a service with high CPU but low throughput? | Bonus | profiling; contention; GC | What metrics would you inspect first? | Integrates JVM and concurrency knowledge. |

## 4. Spring Framework and Spring Boot (30)

| ID | Question title | Priority | Main concepts | Likely follow-up | Why it belongs |
|---|---|---|---|---|---|
| Q076 | What does dependency injection solve, and why prefer constructor injection? | Must Know | IoC; testability; required dependencies | What about circular dependencies? | Spring design foundation. |
| Q077 | How are component scanning and bean registration different? | Must Know | stereotypes; @Bean; scanning | How do you register third-party classes? | Makes wiring understandable. |
| Q078 | What happens during bean creation and lifecycle? | Important | post-processors; initialization; destruction | When does @PostConstruct run? | Diagnoses startup behavior. |
| Q079 | What are bean scopes and singleton thread-safety implications? | Must Know | singleton; prototype; request | Is a singleton automatically thread-safe? | Prevents shared mutable controller state. |
| Q080 | How does Spring Boot auto-configuration decide what to create? | Must Know | conditions; starters; overrides | How do you inspect condition reports? | Demystifies Boot startup. |
| Q081 | How should profiles and external configuration be managed? | Must Know | properties; env; secrets | What wins in property precedence? | Safe deployment configuration. |
| Q082 | What is the Spring MVC request lifecycle? | Must Know | filters; dispatcher; handler; serialization | Where does validation run? | Connects API request layers. |
| Q083 | How do @RequestParam, @PathVariable and @RequestBody differ? | Important | binding; transport semantics | How are invalid bodies reported? | Prevents incorrect endpoint signatures. |
| Q084 | How would you validate requests and return consistent errors? | Must Know | Bean Validation; advice; ProblemDetail | How do you validate nested objects? | Tests public API quality. |
| Q085 | How does @Transactional work through proxies? | Must Know | AOP; transaction boundary | Why does self-invocation bypass it? | Critical real-world Spring trap. |
| Q086 | What do propagation modes REQUIRED and REQUIRES_NEW actually do? | Must Know | nested boundaries; rollback | Does REQUIRES_NEW share the same transaction? | Explains surprising commit behavior. |
| Q087 | What determines transaction rollback and isolation in Spring? | Must Know | unchecked exceptions; isolation | Do checked exceptions roll back by default? | Prevents partial updates. |
| Q088 | Why can a read-only transaction still write? | Important | hints; flush; database behavior | Does readOnly enforce immutability? | Tests understanding of hints versus guarantees. |
| Q089 | How do Spring filters and interceptors differ? | Important | servlet chain; MVC | Where should auth checks live? | Useful request processing choice. |
| Q090 | How do you avoid circular dependency and oversized services? | Important | boundaries; decomposition | Does @Lazy solve the design problem? | Tests architecture rather than workarounds. |
| Q091 | When would you use @ConfigurationProperties instead of @Value? | Important | typed configuration; validation | How do you handle missing settings? | Improves config safety. |
| Q092 | How do application events work, and what do they not guarantee? | Important | event listeners; transactions | Can listeners run before commit? | Avoids treating local events as durable messaging. |
| Q093 | What are the risks of @Async in a web application? | Important | executor; context; errors | Are transactions propagated? | Prevents fire-and-forget surprises. |
| Q094 | How should scheduled tasks be designed for multiple replicas? | Important | @Scheduled; distributed coordination | Can two pods run the same job? | Production scaling concern. |
| Q095 | How does Spring Security's filter chain fit into a request? | Must Know | authentication; authorization; filters | Where is SecurityContext populated? | Connects security to Spring runtime. |
| Q096 | How do you test a Spring MVC controller slice? | Important | @WebMvcTest; MockMvc | Which dependencies are loaded? | Focused test strategy. |
| Q097 | What happens on application startup and how do you debug failure? | Important | context refresh; binding; conditions | Where do you find condition reports? | Useful operational skill. |
| Q098 | How do you troubleshoot a bean not found or ambiguous bean? | Important | qualifiers; scanning; conditions | When use @Primary? | Common Boot debugging scenario. |
| Q099 | How do you configure database connections and pool limits? | Must Know | DataSource; HikariCP; timeouts | What if all connections are borrowed? | Prevents hidden bottlenecks. |
| Q100 | What causes slow Spring endpoints besides slow Java code? | Must Know | SQL; pool; serialization; network | How do traces narrow it down? | Practical performance triage. |
| Q101 | How do you handle validation of business rules versus DTO shape? | Important | layering; invariants | Can @Valid replace service validation? | Prevents trusting input validation alone. |
| Q102 | What is the difference between @Controller and @RestController? | Important | view rendering; response body | What does ResponseEntity add? | Basic web API precision. |
| Q103 | How do you implement graceful shutdown for a Boot service? | Important | readiness; inflight work | What about async consumers? | Avoids lost work during deploys. |
| Q104 | How would you structure a small Spring feature end to end? | Must Know | controller; service; repository; DTO | Where is the transaction boundary? | Evaluates maintainable application design. |
| Q105 | What should you check before upgrading a Boot 2 app to Boot 3? | Important | Java 17; Jakarta; dependencies | Why do javax imports break? | Stack-specific migration awareness. |

## 5. SQL, transactions, JPA, and Hibernate (30)

| ID | Question title | Priority | Main concepts | Likely follow-up | Why it belongs |
|---|---|---|---|---|---|
| Q106 | Write a join to find customers and their latest orders. | Must Know | joins; aggregation; ties | How do you include customers without orders? | Practical SQL fluency. |
| Q107 | How do INNER, LEFT and FULL joins differ? | Must Know | join semantics; nulls | Can WHERE turn LEFT into INNER? | Common query correctness trap. |
| Q108 | When do WHERE and HAVING apply in grouped SQL? | Must Know | grouping; aggregates | How do you filter count > 3? | Essential reporting SQL. |
| Q109 | How do subqueries, EXISTS and joins compare? | Important | semi-joins; duplicates | When is NOT IN dangerous with NULL? | Query selection and correctness. |
| Q110 | How would you page through a large table safely? | Must Know | offset; keyset; ordering | What if rows arrive between pages? | Real API/database scaling topic. |
| Q111 | How do B-tree indexes help and when are they not used? | Must Know | selectivity; composite indexes; plans | Does an index help `LIKE '%x'`? | Performance reasoning without absolutes. |
| Q112 | How do you read EXPLAIN ANALYZE without overreacting? | Must Know | plan nodes; estimates; actuals | Why might a seq scan be correct? | Evidence-led optimization. |
| Q113 | What are ACID properties in a money transfer? | Must Know | atomicity; consistency; isolation; durability | Does ACID cover remote APIs? | Anchors transaction reasoning. |
| Q114 | What anomalies do isolation levels prevent? | Must Know | dirty/nonrepeatable/phantom reads | What does PostgreSQL Read Committed do? | Correct concurrency expectations. |
| Q115 | How do database locks and deadlocks arise? | Must Know | row locks; lock order; retry | What SQLSTATE signals a deadlock? | Real contention troubleshooting. |
| Q116 | When choose optimistic versus pessimistic locking? | Must Know | @Version; lock mode | What happens on optimistic conflict? | Prevents lost updates. |
| Q117 | What are JPA entity lifecycle states? | Must Know | transient; managed; detached; removed | What does merge return? | Foundation for ORM behavior. |
| Q118 | How do persistence context and dirty checking work? | Must Know | identity map; flush | Does save always execute SQL immediately? | Explains surprising writes. |
| Q119 | When does flush happen, and how is it different from commit? | Must Know | flush mode; constraints | Can flushed SQL be rolled back? | Transaction timing precision. |
| Q120 | How do lazy and eager loading affect endpoint performance? | Must Know | proxies; fetch plans | Why does LazyInitializationException occur? | Common ORM production issue. |
| Q121 | How do you diagnose and fix an N+1 query? | Must Know | query counts; fetch joins; graphs | Can fetch join break pagination? | Key JPA performance skill. |
| Q122 | How should entities and DTOs be separated? | Must Know | API boundary; serialization | Why not return entities directly? | Avoids data leakage and lazy loading. |
| Q123 | What do cascade and orphanRemoval mean? | Important | aggregate ownership; child lifecycle | Should CascadeType.REMOVE be on many-to-one? | Prevents accidental deletes. |
| Q124 | How do one-to-many mappings affect SQL and ownership? | Important | owning side; mappedBy; join columns | Which side writes foreign keys? | Common ORM mapping confusion. |
| Q125 | How do JPQL, native SQL and projections compare? | Important | abstraction; read models | When use a DTO projection? | Keeps query code fit for purpose. |
| Q126 | What happens when a transaction calls an external service? | Must Know | long transactions; consistency | How do outbox patterns help? | Critical boundary design. |
| Q127 | How do you batch writes without exhausting memory? | Important | JDBC batching; flush/clear | Does IDENTITY always batch inserts? | Practical bulk processing. |
| Q128 | How should schema migrations be deployed? | Important | Flyway/Liquibase; expand-contract | Why avoid destructive changes first? | Safe production evolution. |
| Q129 | What do unique constraints protect that application checks cannot? | Must Know | race conditions; uniqueness | How do you map constraint violations? | DB as source of truth. |
| Q130 | How do you make a transfer atomic in SQL and service code? | Must Know | transaction; row locks; balance invariant | What happens under concurrent transfers? | End-to-end correctness exercise. |
| Q131 | Why can a composite index's column order matter? | Important | prefix; sort; selectivity | Does an index `(a,b)` help `WHERE b=?`? | More nuanced indexing. |
| Q132 | How do connection pools interact with database transactions? | Important | pool exhaustion; duration | Why is a long idle transaction harmful? | Production resource management. |
| Q133 | How do you detect duplicate rows from a join and fix the query? | Important | join cardinality; distinct | Does DISTINCT fix the root cause? | Practical SQL debugging. |
| Q134 | How would you store and query audit history? | Bonus | audit table; temporal data | Should history updates share the transaction? | Useful feature-design extension. |
| Q135 | When would you choose SQL over JPA for a complex report? | Important | aggregation; projections; maintainability | Can both approaches coexist? | Rewards tool choice over ideology. |

## 6. HTTP, REST APIs, and microservices (25)

| ID | Question title | Priority | Main concepts | Likely follow-up | Why it belongs |
|---|---|---|---|---|---|
| Q136 | How do GET, POST, PUT, PATCH and DELETE differ? | Must Know | safety; idempotency; semantics | Is DELETE always repeat-response identical? | HTTP contract foundation. |
| Q137 | Which HTTP status codes should an API use for common outcomes? | Must Know | 2xx; 4xx; 5xx | When return 409 versus 422? | Client behavior depends on accurate status. |
| Q138 | How would you design a resource-oriented order API? | Must Know | URLs; representations; boundaries | Should verbs appear in URLs? | Practical REST design. |
| Q139 | How should validation and error responses be structured? | Must Know | ProblemDetail; field errors | How do you avoid leaking internals? | Usable and safe contracts. |
| Q140 | How would you implement pagination, filtering and stable sorting? | Must Know | query params; keyset; limits | What happens if sort keys tie? | Common API design challenge. |
| Q141 | How does idempotency make payment creation retry-safe? | Must Know | idempotency key; atomic storage | What if same key has different payload? | Prevents duplicate side effects. |
| Q142 | What are ETag and Cache-Control used for? | Important | conditional requests; caches | What does 304 mean? | Reduces bandwidth and stale data. |
| Q143 | How do timeouts, retries and backoff interact? | Must Know | deadlines; jitter; retry budget | Which requests are safe to retry? | Essential resilience design. |
| Q144 | When should you add a circuit breaker or bulkhead? | Important | failure isolation; fallback | Can a breaker replace a timeout? | Addresses cascading failures. |
| Q145 | How do synchronous calls compare with asynchronous messaging? | Must Know | coupling; latency; consistency | How do clients learn async status? | Fundamental distributed trade-off. |
| Q146 | How would you version an API without breaking clients? | Important | compatible evolution; versioning | Is a new field always safe? | Contract longevity. |
| Q147 | How do correlation IDs and trace context travel across services? | Important | headers; tracing; logs | Why not log personal data? | Debuggable distributed requests. |
| Q148 | What failure modes occur with a chain of service calls? | Important | partial failures; fan-out | What is a deadline? | Real microservice reliability. |
| Q149 | What is eventual consistency and when is it acceptable? | Important | distributed updates; reconciliation | How do users see pending state? | Explains asynchronous correctness. |
| Q150 | How would you design an order placement workflow end to end? | Must Know | API; transaction; payment; events | Where is idempotency enforced? | Appropriately scoped system design. |
| Q151 | How do API gateways differ from service-to-service concerns? | Important | routing; auth; rate limits | Should business logic live at the gateway? | Clarifies deployment boundaries. |
| Q152 | How do you prevent duplicate requests from creating duplicate resources? | Must Know | unique keys; upsert; idempotency | Is a client-generated ID enough? | Common production failure. |
| Q153 | What should happen when a downstream service times out after committing? | Must Know | ambiguous outcome; reconciliation | Should you immediately retry? | Tests distributed uncertainty. |
| Q154 | How do you make a webhook consumer safe? | Important | signatures; dedup; retries | What if events arrive out of order? | Practical integration pattern. |
| Q155 | How would you rate-limit an API? | Important | token bucket; distributed counters | What response headers help clients? | Protects reliability and fairness. |
| Q156 | How do content negotiation and media types affect an API? | Bonus | Accept; Content-Type | What does 415 mean? | Correct protocol use. |
| Q157 | What is the difference between liveness and readiness? | Important | health; routing; dependencies | Should a failed DB make liveness fail? | Safe deployment behavior. |
| Q158 | How do you handle file upload and download safely? | Important | streaming; limits; headers | How do you avoid path traversal? | Common endpoint security/performance. |
| Q159 | How would you design a small notification service? | Important | queues; retries; templates | How do you avoid duplicate emails? | Scoped design interview practice. |
| Q160 | When should you split a service, and when keep a modular monolith? | Important | boundaries; operations; coupling | What is the cost of a network boundary? | Prevents architecture fashion answers. |

## 7. Security (12)

| ID | Question title | Priority | Main concepts | Likely follow-up | Why it belongs |
|---|---|---|---|---|---|
| Q161 | How do authentication and authorization differ? | Must Know | identity; permissions; least privilege | Why check ownership on every request? | Security foundation. |
| Q162 | When choose server sessions versus JWT bearer tokens? | Must Know | revocation; state; expiry | Is a JWT encrypted by default? | Avoids token dogma. |
| Q163 | How should passwords be stored and verified? | Must Know | adaptive hashes; salt; reset | Why not SHA-256 alone? | Essential credential safety. |
| Q164 | What are OAuth2 and OpenID Connect at a practical level? | Important | authorization; identity; roles | Is OAuth2 itself authentication? | Common integration literacy. |
| Q165 | How do CORS and CSRF differ? | Must Know | browser policy; cookie auth | Does CORS protect an API from curl? | Widely confused security concepts. |
| Q166 | How do you prevent SQL injection and unsafe deserialization? | Must Know | parameters; input boundaries | Is escaping sufficient? | Common exploitable mistakes. |
| Q167 | How would you secure a Spring Boot API endpoint? | Must Know | filter chain; authorization rules | What about method-level security? | Applies security to stack. |
| Q168 | How do you design resource-level authorization? | Must Know | ownership; IDOR | Why isn't hidden UI enough? | Stops cross-account data exposure. |
| Q169 | What should an access token contain and how is it validated? | Important | signature; issuer; audience; expiry | How does key rotation work? | Practical token validation. |
| Q170 | How do you manage secrets across environments? | Important | secret store; rotation; logging | Should secrets be in images? | Production deployment hygiene. |
| Q171 | How do you handle sensitive data in logs and responses? | Important | redaction; minimization | How do you debug without logging tokens? | Limits exposure during incidents. |
| Q172 | What security checks belong in a public file-upload endpoint? | Important | size; type; malware; path safety | Can Content-Type be trusted? | Realistic attack surface. |

## 8. Testing, debugging, and coding exercises (13)

| ID | Question title | Priority | Main concepts | Likely follow-up | Why it belongs |
|---|---|---|---|---|---|
| Q173 | How do unit, slice, integration and end-to-end tests differ? | Must Know | test pyramid; speed; fidelity | When use @SpringBootTest? | Sensible testing strategy. |
| Q174 | How would you test a service with Mockito without over-mocking? | Must Know | stubs; verify; behavior | Should you mock a value object? | Meaningful unit tests. |
| Q175 | How do you test repository queries and database constraints? | Must Know | @DataJpaTest; real database | Why can H2 differ from PostgreSQL? | Prevents false confidence. |
| Q176 | How do you test MVC status, validation and security? | Must Know | MockMvc; JSON; security | How do you test unauthorized requests? | Verifies public contracts. |
| Q177 | How would you test transaction rollback and concurrency? | Important | flush; separate transactions | Why can a test transaction mask behavior? | Catches difficult persistence bugs. |
| Q178 | What makes a flaky test and how do you diagnose one? | Important | isolation; time; async | Should you add a sleep? | Improves build reliability. |
| Q179 | Write a function to find the first non-repeating character. | Important | counts; Unicode assumptions | What changes for code points? | Compact string/collection exercise. |
| Q180 | Write a function to merge overlapping intervals. | Important | sorting; edge cases | Are touching intervals merged? | Basic coding reasoning. |
| Q181 | Write SQL for top customers by monthly order total. | Must Know | GROUP BY; dates; sorting | How do refunds affect total? | Practical SQL test. |
| Q182 | How do you debug a slow endpoint systematically? | Must Know | tracing; SQL; pools; profiling | What do you measure first? | Production diagnostic method. |
| Q183 | How do you investigate a sporadic 500 response? | Important | reproduction; logs; correlation | How do you avoid leaking stack traces? | Applied incident reasoning. |
| Q184 | What test data and clock strategies make tests deterministic? | Important | fixtures; Clock; random seeds | How do you test time zones? | Prevents unstable business tests. |
| Q185 | How do you review a PR for correctness and maintainability? | Bonus | contracts; security; tests | What feedback is highest priority? | Reflects 3-4 year engineering judgment. |

## 9. Messaging and caching (10)

| ID | Question title | Priority | Main concepts | Likely follow-up | Why it belongs |
|---|---|---|---|---|---|
| Q186 | What do Kafka topics, partitions and consumer groups do? | Must Know | ordering; scaling; offsets | Is ordering global? | Messaging foundation. |
| Q187 | What does at-least-once delivery require from a consumer? | Must Know | duplicates; idempotency; offsets | When commit an offset? | Prevents duplicate side effects. |
| Q188 | How do retries and dead-letter handling work for poison messages? | Important | backoff; DLQ; alerting | Can retries block a partition? | Reliable consumption. |
| Q189 | How does the transactional outbox reduce dual-write risk? | Must Know | DB commit; relay; duplicates | Does it give exactly-once processing? | Critical event publishing pattern. |
| Q190 | How do you preserve useful event ordering? | Important | partition key; sequence | What if producers race? | Event stream correctness. |
| Q191 | What is cache-aside and when should Redis be used? | Must Know | read-through flow; source of truth | What happens on cache miss? | Common backend optimization. |
| Q192 | How do TTL and invalidation affect correctness? | Must Know | staleness; eviction; update order | Should every key have the same TTL? | Makes caching trade-offs explicit. |
| Q193 | How do you prevent a cache stampede or hot key? | Important | jitter; single-flight; prewarming | What if Redis is down? | Operational cache resilience. |
| Q194 | How do Redis data structures and atomic operations help? | Important | counters; sets; expiry | Is increment plus expire atomic? | Practical Redis correctness. |
| Q195 | How do you choose between an event and a synchronous request? | Important | latency; consistency; ownership | How does failure recovery differ? | Integrates messaging with architecture. |

## 10. Deployment, observability, and production troubleshooting (5)

| ID | Question title | Priority | Main concepts | Likely follow-up | Why it belongs |
|---|---|---|---|---|---|
| Q196 | What belongs in a production-ready Docker image? | Must Know | runtime; layers; non-root | How should secrets enter the container? | Basic deployment competence. |
| Q197 | Which logs, metrics and traces would you add to an API? | Must Know | signals; cardinality; correlation | What must not be logged? | Observability foundation. |
| Q198 | How do readiness, liveness and graceful shutdown work together? | Important | probes; draining; termination | What if a consumer is mid-message? | Safe rolling deployments. |
| Q199 | How would you triage rising latency and errors after a deploy? | Must Know | rollback; comparisons; bottlenecks | What evidence points to DB pool saturation? | Incident response exercise. |
| Q200 | How would you investigate an intermittent production order failure end to end? | Must Know | trace; logs; DB; queues; remediation | How do you prevent recurrence? | Final integrative interview scenario. |

## Selection review

Counts by chapter: 30 + 20 + 25 + 30 + 30 + 25 + 12 + 13 + 10 + 5 = **200**. The questions progress from language and runtime to application, data, distributed systems and operations. Adjacent topics deliberately connect without duplicating a main question: for example Q085 is about proxy interception, Q086 about propagation, Q087 about rollback; Q141 is endpoint-level retry safety, Q152 is resource uniqueness, and Q187 is consumer deduplication. SQL querying, ORM behavior, security, coding, testing, and incident diagnosis each have explicit coverage.