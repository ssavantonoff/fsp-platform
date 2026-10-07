# Assessment Bank P3 — Controlled Remediation Plan

## A. Header and scope

- Base: `main`, `f6ac399bd84f7379cb957d2c8f4b4c1fc31d5193`.
- Branch: `feat/assessment-bank-remediation`.
- Design date: 2026-10-07.
- Status: **DESIGN ONLY — NOT IMPLEMENTED**.
- Scope: versioned replacement designs for exactly **27 IMPORTANT** findings.
- Excluded: **6 MINOR** findings; the other 42 records also remain unchanged.
- Deliverable: this document only. P3-B implementation, P3-C audit, P3-D technical gate and PR creation have not started.

### Inspected baseline

Read the actual files at the base above: [content audit](assessment-bank-audit-draft.md), [methodology](assessment-methodology-draft.md), [implementation evidence](assessment-task3-implementation-map.md), `backend/app/content/backend_questions.json`, `backend/app/question_bank.py`, `backend/app/assessment_validation.py`, `backend/app/services/assessments.py`, `backend/tests/test_assessment_validation.py`, `backend/tests/test_assessments.py`, and the assessment sections of README.

The original audit's older provenance is retained in those documents. Its source SHA-256 still matches current main: `7d2c7f2db8a7986d3027e250ac47786e700e4babf0c80e7c46ce6fce34442096`. All 27 target codes, metadata and categories below match both current JSON and the audit findings. Current inventory has 73 v1 and two v2 records; only one of those v2 records is a target. No source/mapping discrepancy was found.

The seed already rejects changed published content, inserts new codes and deactivates an explicitly superseded predecessor if present. The validator permits absent historical predecessors while requiring exact current source inventory. Runtime selects active DB records and persists attempt membership and option order. These boundaries support the requested replacements without an engine redesign.

## B. Frozen contract

| Area | Unchanged requirement |
|---|---|
| Current Backend source | 75 records; 25 per grade; five competencies |
| Each grade × competency source bucket | 1 BASIC / 3 APPLIED / 1 ADVANCED; five records |
| Attempt | 20 questions; 30 minutes; four options; single choice |
| Each competency in an attempt | 1 BASIC / 2 APPLIED / 1 ADVANCED |
| Scoring | Five points per correct answer; wrong/unanswered zero; no new weights |
| PASS | Overall ≥70 **and** every competency ≥50 |
| Cooldown | FAIL seven days; PASS 90 days for the same specialization/grade |
| Verification | Existing canonical CandidateProfile fields and synchronization; no new qualification state |
| Retake/restoration | Existing same-grade latest successful result, failed-result preservation and specialization restoration |
| Replacement | New code, incremented version, exact immediate predecessor in supersedes; predecessor removed from current JSON and retained in DB/history |
| Metadata | Preserve each predecessor's grade, competency and difficulty |
| Other contracts | Assessment API/models/schemas, selection/shuffle, lifecycle, Matching, Invitations, FSP and frontend unchanged |

No threshold tuning, difficulty relabeling, new competencies, algorithms, weighting or empirical calibration is authorized. A DIFFICULTY_MISMATCH is addressed by the cognitive demand of the new content. Difficulty remains relative to its grade.

## C. Current audit baseline

| Baseline outcome | Records |
|---|---:|
| Reviewed | 75 |
| BLOCKER | 0 |
| IMPORTANT | 27 |
| MINOR | 6 |
| Without findings | 42 |

Baseline content readiness: **NOT_READY**. These are pre-remediation observations, not results of this design or a future audit. Task 3's technical gate does not resolve content findings.

Excluded MINOR backlog, with no proposed code/content/metadata changes:

- `backend-junior-http_api-2-v1`
- `backend-junior-architecture-2-v1`
- `backend-junior-architecture-3-v1`
- `backend-junior-testing_security_debugging-3-v1`
- `backend-junior-testing_security_debugging-4-v1`
- `backend-senior-testing_security_debugging-3-v1`

## D. Remediation matrix — 27 designs

Each numbered design has the same 19 fields. Scenario shapes, constraints and concepts are authoring requirements, not final stems/options or solutions. Distractor families are unordered concepts; they are not a proposed source/display order. Every later option must be comparable in length, specificity and grammar. Do not encode the concept label in the stem.

For compact neighbor references: `J`, `M`, `S` mean JUNIOR, MIDDLE, SENIOR; `P`, `H`, `D`, `A`, `T` mean PROGRAMMING, HTTP_API, DATABASES, ARCHITECTURE, TESTING_SECURITY_DEBUGGING. For example, `M-H2` means `backend-middle-http_api-2-v1` in the inspected baseline. All slots 1–5 are v1 except `J-A1` and `S-A4`, which are v2. Proposed neighbors refer to the designs below while current neighbors refer to inspected JSON. Ranges such as `J-H1–5` identify all five records, not a sampling. Section E registers every slot in affected buckets; section F supplies the cross-grade comparison. This notation contains no answer positions.

### D01 — Junior local diagnosis

| Field | Design |
|---|---|
| 1. Current code | `backend-junior-testing_security_debugging-5-v1` |
| 2. Replacement code | `backend-junior-testing_security_debugging-5-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-junior-testing_security_debugging-5-v1` |
| 5. Frozen metadata | JUNIOR / TESTING_SECURITY_DEBUGGING / ADVANCED |
| 6. Audit categories | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS |
| 7. Root cause | Recognizing a generic first debugging step suffices; alternatives do not investigate the failure. |
| 8. Cognitive target | Rank local diagnostic hypotheses from two or three observations. |
| 9. Scenario shape | A parsing change fails only for an optional-field input; sanitized exception location and a contrasting successful input are supplied. |
| 10. Explicit constraints | Single handler/process; reproducible inputs; failure occurs before DB/network access; no production mutation; next check must distinguish the remaining local hypotheses. |
| 11. Decision dimensions | Evidence relevance, discriminating power, reproducibility and cost of the next check. |
| 12. Abstract correct-option concept | Evidence-directed local diagnosis. |
| 13. Three distractor families | Infrastructure probe useful after external access; broad end-to-end reproduction that conflates inputs; valid-case check that leaves the failing boundary untested. |
| 14. Ambiguity risks | Missing exception location could make infrastructure equally plausible; show enough observations without naming the defect. |
| 15. Near-duplicate checks | J-T1–4 cover secrets, SQL input, validation regression and safe errors; M-T1–5 and S-T1–5 cover access, test orchestration and system diagnosis. D12/D26 require different evidence and scope. |
| 16. Grade fit | Local behavior and standard debugging, without distributed ownership. |
| 17. Difficulty fit | ADVANCED requires correlating multiple facts and eliminating plausible hypotheses. |
| 18. Competency fit | Interpretation of failure evidence, rather than implementation of parsing. |
| 19. Wording exclusions | Generic “start with logs”; exact exception naming the solution; absurd actions; a list of diagnostic steps serving as a solution. |

### D02 — Middle blocking I/O integration

| Field | Design |
|---|---|
| 1. Current code | `backend-middle-programming-2-v1` |
| 2. Replacement code | `backend-middle-programming-2-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-middle-programming-2-v1` |
| 5. Frozen metadata | MIDDLE / PROGRAMMING / APPLIED |
| 6. Audit categories | WEAK_DISTRACTORS |
| 7. Root cause | Relevant async/I/O topic, but no realistic constrained implementation choice. |
| 8. Cognitive target | Compare integration approaches for a blocking dependency. |
| 9. Scenario shape | A fixed synchronous SDK is called by an async handler; load measurements show unrelated handlers stalling. |
| 10. Explicit constraints | SDK cannot be replaced in this release; blocking I/O, not CPU work; SDK concurrency rules supplied; bounded worker capacity; caller timeout does not stop running SDK work. |
| 11. Decision dimensions | Event-loop responsiveness, actual resource lifetime, concurrency and migration feasibility. |
| 12. Abstract correct-option concept | Dependency isolation within a bounded execution budget. |
| 13. Three distractor families | Async wrapper retaining blocking execution; compatible async-client migration unavailable in this release; executor use that releases capacity before underlying work ends. |
| 14. Ambiguity risks | State SDK thread safety and timeout behavior; do not imply cancellation forcibly terminates a running thread. |
| 15. Near-duplicate checks | M-P1/3/4/5 concern local races, streaming, key identity and load admission; J-P1–5 remain local language tasks; S-P1–5 concern lifecycle/workload/system coordination. D04 assesses pipeline admission rather than SDK placement. |
| 16. Grade fit | Interaction of handler, SDK and execution capacity. |
| 17. Difficulty fit | APPLIED selects an implementation under fixed dependency constraints. |
| 18. Competency fit | Execution model and resource ownership in program code. |
| 19. Wording exclusions | “Just add async”; undefined executor limits; framework trivia; one option containing the complete implementation. |

### D03 — Middle bounded streaming

| Field | Design |
|---|---|
| 1. Current code | `backend-middle-programming-3-v1` |
| 2. Replacement code | `backend-middle-programming-3-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-middle-programming-3-v1` |
| 5. Frozen metadata | MIDDLE / PROGRAMMING / APPLIED |
| 6. Audit categories | GRADE_TOO_EASY, DIFFICULTY_MISMATCH, WEAK_DISTRACTORS |
| 7. Root cause | Local file iteration without component interaction or trade-off. |
| 8. Cognitive target | Preserve streaming properties through a producer/consumer boundary. |
| 9. Scenario shape | A file reader feeds an async transformation stage and a slower batch sink; memory grows despite lazy file reading. |
| 10. Explicit constraints | Supplied row-size/memory bounds; ordered output; no loss; batch sink has bounded throughput; throughput goal rules out fully serial per-row writes; no full materialization. |
| 11. Decision dimensions | End-to-end buffering, throughput, ordering and shutdown ownership. |
| 12. Abstract correct-option concept | Bounded flow across all pipeline stages. |
| 13. Three distractor families | Lazy reader with an unbounded intermediate buffer; bounded batches accumulated as pending tasks; fully serial streaming that misses the supplied throughput requirement. |
| 14. Ambiguity risks | Without throughput and row-size bounds serial execution or larger batches might also be best; make those limits explicit. |
| 15. Near-duplicate checks | M-P1/2/4/5 separate races, SDK isolation, key identity and overload; J-P1–5 include local file lifetime, not pipeline flow; S-P1–5 add admission, remote lifecycle and shared work. D04 adds failures/deadlines, not file streaming. |
| 16. Grade fit | Coordinates producer, transformer and sink. |
| 17. Difficulty fit | APPLIED combines a measurable limit with viable streaming alternatives. |
| 18. Competency fit | Data flow and buffering in an implementation. |
| 19. Wording exclusions | Mere “iterate by lines”; contradicting throughput figures; an answer identifiable solely by the word “bounded”. |

### D04 — Middle overload and task lifetime

| Field | Design |
|---|---|
| 1. Current code | `backend-middle-programming-5-v1` |
| 2. Replacement code | `backend-middle-programming-5-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-middle-programming-5-v1` |
| 5. Frozen metadata | MIDDLE / PROGRAMMING / ADVANCED |
| 6. Audit categories | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS |
| 7. Root cause | Basic concurrency limiting, without queue/error consequences. |
| 8. Cognitive target | Compare bounded task strategies under burst load and partial failures. |
| 9. Scenario shape | A batch issues independent read-only lookups; burst arrivals, retryable failures and slow calls compete for fixed capacity. |
| 10. Explicit constraints | Fixed dependency concurrency ceiling; finite pending-work budget; end-to-end deadline; incomplete result must be reported explicitly; retries consume the same budget; running calls own capacity until completion. |
| 11. Decision dimensions | Admission versus execution, queue residence, retries, partial results and cancellation accounting. |
| 12. Abstract correct-option concept | Coherent capacity and lifetime accounting across the operation. |
| 13. Three distractor families | Semaphore with unlimited task admission; bounded queue with a renewed deadline on every retry; early capacity release after timeout while underlying calls continue. |
| 14. Ambiguity risks | Specify permissible partial results and actual cancellation behavior; do not silently assume loss is acceptable. |
| 15. Near-duplicate checks | M-P1–4 remain race/integration/streaming/key tasks; J-P1–5 require local behavior; S-P1–5 include the existing overload BASIC S-P1, but this design adds interacting retry/lifetime constraints. It does not reuse D15's shared-result ownership problem. |
| 16. Grade fit | Implementation-level coordination of components, not global architecture. |
| 17. Difficulty fit | ADVANCED combines admission, deadlines, retries and failure accounting. |
| 18. Competency fit | Scheduling and program resource control. |
| 19. Wording exclusions | A semaphore as a complete answer; unrealistic infinite retries; unstated failure policy; merely longer option text. |

### D05 — Middle document update contract

| Field | Design |
|---|---|
| 1. Current code | `backend-middle-http_api-2-v1` |
| 2. Replacement code | `backend-middle-http_api-2-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-middle-http_api-2-v1` |
| 5. Frozen metadata | MIDDLE / HTTP_API / APPLIED |
| 6. Audit categories | WEAK_DISTRACTORS |
| 7. Root cause | Concurrency topic without plausible update-contract alternatives. |
| 8. Cognitive target | Choose a client/server contract that detects stale full-document writes. |
| 9. Scenario shape | Two clients edit from the same representation; server must expose conflict for user reconciliation. |
| 10. Explicit constraints | Full replacement; no automatic merge; strong validator of relevant representation; comparison and write are atomic server capabilities; missing/stale preconditions cannot silently overwrite. |
| 11. Decision dimensions | Validator semantics, stale-client detection and observable failure contract. |
| 12. Abstract correct-option concept | Conditional mutation tied to the edited representation. |
| 13. Three distractor families | Last-writer-wins with audit history; read-before-write contract with a race window; creation-only precondition applied to an existing document. |
| 14. Ambiguity risks | If automatic merging or unconditional updates are allowed, other contracts become reasonable; rule them out in the scenario. |
| 15. Near-duplicate checks | M-H1/3/4/5 cover repeat effects, caches, retry decisions and pagination; J-H1–5 cover basic API boundaries; S-H1–5 include D18, which requires multi-replica authority rather than selection of a conditional client contract. Compare M-D1 local write concurrency separately. |
| 16. Grade fit | Applied HTTP/client contract under concurrent editing. |
| 17. Difficulty fit | APPLIED compares plausible contracts, not header-name recall. |
| 18. Competency fit | HTTP representation and precondition semantics. |
| 19. Wording exclusions | Header in stem that names the intended choice; arbitrary status trivia; generic “protect concurrency” alternative. |

### D06 — Middle personalized caching

| Field | Design |
|---|---|
| 1. Current code | `backend-middle-http_api-3-v1` |
| 2. Replacement code | `backend-middle-http_api-3-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-middle-http_api-3-v1` |
| 5. Frozen metadata | MIDDLE / HTTP_API / APPLIED |
| 6. Audit categories | WEAK_DISTRACTORS |
| 7. Root cause | Alternatives fail to compare realistic browser/shared-cache strategies. |
| 8. Cognitive target | Distinguish storage from reuse validation at an account boundary. |
| 9. Scenario shape | Sensitive personal response traverses a shared intermediary and a browser; accounts switch on the same device. |
| 10. Explicit constraints | All caches obey HTTP directives; no stored response is permitted for this endpoint; authentication on every origin request; fresh rollout with no preexisting copies; application memory/history outside HTTP caching is explicitly out of scope. |
| 11. Decision dimensions | Private versus shared storage, revalidation versus storage prohibition, account isolation. |
| 12. Abstract correct-option concept | Cache behavior consistent with the stated non-retention boundary. |
| 13. Three distractor families | Private browser storage with revalidation; user-partitioned shared storage; short-lived private storage with logout eviction. |
| 14. Ambiguity risks | Do not claim headers erase old copies or secure a malicious cache; make storage prohibition and compliant-cache context explicit. |
| 15. Near-duplicate checks | M-H1/2/4/5 test other contracts; J-H1–5 test status/access/CSRF; S-H1–5 concern system contracts. S-T3 remains the untouched application-cache risk item; M-A4 concerns cache-aside freshness, not HTTP storage. |
| 16. Grade fit | Compares plausible cache/auth strategies across components. |
| 17. Difficulty fit | APPLIED distinguishes two independent cache properties under a supplied constraint. |
| 18. Competency fit | HTTP caching policy and personalized response contract. |
| 19. Wording exclusions | Public caching as the only alternative; “headers guarantee privacy”; undefined browser history behavior; directive-name echo. |

### D07 — Middle retry decision from operation state

| Field | Design |
|---|---|
| 1. Current code | `backend-middle-http_api-4-v1` |
| 2. Replacement code | `backend-middle-http_api-4-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-middle-http_api-4-v1` |
| 5. Frozen metadata | MIDDLE / HTTP_API / APPLIED |
| 6. Audit categories | GRADE_TOO_EASY, NEAR_DUPLICATE |
| 7. Root cause | Repeats Junior safe-retry recognition without new constraints. |
| 8. Cognitive target | Apply an already-defined retry/status contract to a specific client state. |
| 9. Scenario shape | Payment request timed out; an authenticated operation lookup reports a supplied nonterminal state and retry window. |
| 10. Explicit constraints | Stable client intent reference and unchanged payload; operation-state responses and terminality supplied; status lookup authoritative; duplicate request behavior specified; retention exceeds the shown interval; no server redesign requested. |
| 11. Decision dimensions | Unknown versus pending versus terminal outcome, allowed next client action and deadline. |
| 12. Abstract correct-option concept | Client action consistent with the supplied operation-state contract. |
| 13. Three distractor families | Fresh intent after a transport timeout; replay appropriate for a terminal state but not the shown pending state; continued polling beyond the supplied terminality/deadline policy. |
| 14. Ambiguity risks | State precise allowed behavior while pending; otherwise replay and polling could both be equally legitimate. |
| 15. Near-duplicate checks | M-H1/2/3/5 do not interpret a state sequence; J-H1–5 remain basic contracts. Known J-A5 recognizes duplicate prevention, D16 assesses durable acceptance semantics, D20 designs lifecycle boundaries; neither is this client's constrained action. Compare S-H1–5 in full. |
| 16. Grade fit | Applies a contract using response evidence and retry constraints. |
| 17. Difficulty fit | APPLIED needs state interpretation, not naming an idempotency mechanism. |
| 18. Competency fit | Observable API retry/status behavior. |
| 19. Wording exclusions | “Use an idempotency key” as a complete choice; unspecified pending behavior; payment-provider lore. |

### D08 — Middle relationship loading

| Field | Design |
|---|---|
| 1. Current code | `backend-middle-databases-2-v1` |
| 2. Replacement code | `backend-middle-databases-2-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-middle-databases-2-v1` |
| 5. Frozen metadata | MIDDLE / DATABASES / APPLIED |
| 6. Audit categories | WEAK_DISTRACTORS |
| 7. Root cause | N+1 recognition replaces comparison of loading strategies. |
| 8. Cognitive target | Select data loading from measured cardinality and result requirements. |
| 9. Scenario shape | Paginated orders need all line items; an execution trace includes round trips and multiplicative joined-row volume. |
| 10. Explicit constraints | Fixed parent page; bounded parent IDs; high child fanout; all children needed; round-trip/transfer budget supplied; no cache or snapshot-consistency requirement; any join alternative must preserve parent pagination. |
| 11. Decision dimensions | Query count, transferred rows, pagination correctness and memory. |
| 12. Abstract correct-option concept | Loading strategy compatible with both parent selection and child fanout. |
| 13. Three distractor families | Per-parent queries within the latency budget assumption that evidence disproves; correctly paginated joined loading with excessive row amplification; projection-only loading that omits required child detail. |
| 14. Ambiguity risks | Joined loading is valid in other cardinalities; provide distinguishing costs and avoid claiming ORM syntax always breaks pagination. |
| 15. Near-duplicate checks | M-D1/3/4/5 cover writes, index shape, transaction scope and deadlocks; J-D1–5 cover integrity/joins; S-D1–5 cover invariants, retries, rollout and workers. D12 reads diagnostic evidence rather than choosing relationship loading. |
| 16. Grade fit | Applies data-access trade-offs to component output needs. |
| 17. Difficulty fit | APPLIED compares viable strategies using supplied measurements. |
| 18. Competency fit | Query shape/cardinality and data retrieval. |
| 19. Wording exclusions | Asking only for the name N+1; ORM spelling trivia; universal claim that joins or lazy loading are wrong. |

### D09 — Middle transaction boundary

| Field | Design |
|---|---|
| 1. Current code | `backend-middle-databases-4-v1` |
| 2. Replacement code | `backend-middle-databases-4-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-middle-databases-4-v1` |
| 5. Frozen metadata | MIDDLE / DATABASES / APPLIED |
| 6. Audit categories | GRADE_TOO_EASY, DIFFICULTY_MISMATCH, WEAK_DISTRACTORS |
| 7. Root cause | Recognizes lock lifetime without applying it to alternative boundaries. |
| 8. Cognitive target | Choose a DB transaction boundary from atomicity and lock-budget requirements. |
| 9. Scenario shape | Handler validates order state, performs a slow read-only external calculation and writes two dependent DB rows. |
| 10. Explicit constraints | PostgreSQL 17 READ COMMITTED; external calculation has no effects and returns input-version-bound data; DB writes must be atomic; external call exceeds lock budget; relevant state can change meanwhile; final write supports revalidation. |
| 11. Decision dimensions | Lock duration, stale assumptions, external latency and atomic DB state. |
| 12. Abstract correct-option concept | Transaction scope preserving validity and atomicity within the lock budget. |
| 13. Three distractor families | Single long transaction across external calculation; early transaction completion followed by writes using stale assumptions; independent short transactions for dependent writes. |
| 14. Ambiguity risks | Specify the calculation is replayable and side-effect-free; otherwise compensation or a different architecture is required. |
| 15. Near-duplicate checks | M-D1/2/3/5 cover local atomic updates, retrieval, indexes and deadlocks; J-D1–5 include rollback basics; S-D1–5 cover multi-row/system invariants and rollout. D18 is HTTP replica authority, D23 adds competing lifecycle events, not one handler boundary. |
| 16. Grade fit | Applies transaction knowledge across handler/dependency interaction. |
| 17. Difficulty fit | APPLIED compares workable boundaries against one operation's constraints. |
| 18. Competency fit | Transaction lifetime, locks and DB atomicity. |
| 19. Wording exclusions | Lock-lifetime yes/no; unspecified external side effects; mandatory distributed architecture for a local handler. |

### D10 — Middle dependency failure containment

| Field | Design |
|---|---|
| 1. Current code | `backend-middle-architecture-3-v1` |
| 2. Replacement code | `backend-middle-architecture-3-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-middle-architecture-3-v1` |
| 5. Frozen metadata | MIDDLE / ARCHITECTURE / APPLIED |
| 6. Audit categories | WEAK_DISTRACTORS |
| 7. Root cause | All alternatives are obviously unreasonable responses to failure. |
| 8. Cognitive target | Select a containment policy for interacting services from failure evidence. |
| 9. Scenario shape | Optional recommendation dependency slows down; synchronous callers exhaust a shared request pool while core checkout remains healthy. |
| 10. Explicit constraints | Recommendations may be omitted; checkout SLO supplied; separate dependency concurrency/retry budget feasible; bounded recovery probes; errors occur across instances; fixed fleet, no immediate scaling. |
| 11. Decision dimensions | Failure isolation, fallback value, deadline consumption and recovery traffic. |
| 12. Abstract correct-option concept | Containment aligned with dependency criticality and recovery budget. |
| 13. Three distractor families | Bounded retries within each call but no aggregate isolation; cached fallback with synchronized recovery traffic; global admission reduction protecting the dependency but starving healthy checkout. |
| 14. Ambiguity risks | Explicitly permit fallback and give recovery/admission limits; otherwise competing policies may be equally suitable. |
| 15. Near-duplicate checks | M-A1/2/4/5 cover source of truth, outbox, cache freshness and consumer deduplication; J-A1–5 include one-request timeout; S-A1–5 cover distributed boundaries and ownership. J/M/S architecture all compared; D04 is task scheduling, not dependency criticality. |
| 16. Grade fit | Chooses policy at a service interaction boundary. |
| 17. Difficulty fit | APPLIED relates observed overload to a constrained fallback/recovery policy. |
| 18. Competency fit | Architectural isolation across components. |
| 19. Wording exclusions | Name recognition for a circuit breaker; unbounded retries as every distractor; claiming a breaker alone solves all overload. |

### D11 — Middle deterministic deadline test

| Field | Design |
|---|---|
| 1. Current code | `backend-middle-testing_security_debugging-3-v1` |
| 2. Replacement code | `backend-middle-testing_security_debugging-3-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-middle-testing_security_debugging-3-v1` |
| 5. Frozen metadata | MIDDLE / TESTING_SECURITY_DEBUGGING / APPLIED |
| 6. Audit categories | ARTIFICIAL_WORDING, WEAK_DISTRACTORS |
| 7. Root cause | Exaggerated test practice reveals the answer through wording. |
| 8. Cognitive target | Choose deterministic coverage that exercises the real deadline enforcement boundary. |
| 9. Scenario shape | Expiry is persisted and enforced by a server service; a fast existing test misses the exact-boundary mutation. |
| 10. Explicit constraints | UTC deadline; server semantics explicitly supplied; injectable server time; real persistence required; browser timer not authoritative; no concurrent operation under test; evaluate before/on/after and resulting state. |
| 11. Decision dimensions | Control of time, production-path coverage, boundary precision and side effects. |
| 12. Abstract correct-option concept | Deterministic evidence at the actual enforcement boundary. |
| 13. Three distractor families | Fast browser-clock simulation without service time; production-path test with a shortened deadline and real-time waits; deterministic service mock that bypasses persisted enforcement. |
| 14. Ambiguity risks | State the intended boundary semantics, do not make the candidate infer an undocumented product rule. |
| 15. Near-duplicate checks | M-T1/2/4/5 cover ownership, SSRF, diagnosis and concurrent starts; J-T1–5 cover local errors/regressions; S-T1–5 cover system evidence/faults. D01 uses failure clues, S-T2 tests rollback, D27 tests crash/replay. |
| 16. Grade fit | Integrates test control, service boundary and persistence. |
| 17. Difficulty fit | APPLIED chooses a meaningful deterministic test rather than recalling a clock API. |
| 18. Competency fit | Test validity and deadline regression coverage. |
| 19. Wording exclusions | Week-long sleep caricature; production-rule changes as alternatives; exact test code or asserted result as a published solution. |

### D12 — Middle measured SQL regression

| Field | Design |
|---|---|
| 1. Current code | `backend-middle-testing_security_debugging-4-v1` |
| 2. Replacement code | `backend-middle-testing_security_debugging-4-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-middle-testing_security_debugging-4-v1` |
| 5. Frozen metadata | MIDDLE / TESTING_SECURITY_DEBUGGING / APPLIED |
| 6. Audit categories | WEAK_DISTRACTORS |
| 7. Root cause | No diagnostic evidence is interpreted; alternatives are unrelated. |
| 8. Cognitive target | Select the next discriminating measurement from a before/after query trace. |
| 9. Scenario shape | Comparable inputs show unchanged connection wait but increased rows processed and a new expensive plan stage after a query change. |
| 10. Explicit constraints | Same data distribution/load; relevant stage counts/times supplied; no lock wait or network regression in evidence; read-only staging reproduction; next action diagnoses rather than changes production. |
| 11. Decision dimensions | Causal evidence, alternative hypotheses, plan estimates versus actual work and measurement cost. |
| 12. Abstract correct-option concept | Targeted measurement of the remaining query-execution hypothesis. |
| 13. Three distractor families | Connection-pool instrumentation useful for a different wait pattern; network payload measurement despite unchanged transfer; aggregate throughput measurement that obscures the changed stage. |
| 14. Ambiguity risks | Include sufficient stage observations without printing the cause; do not assume EXPLAIN ANALYZE is harmless for arbitrary mutations. |
| 15. Near-duplicate checks | M-T1/2/3/5 concern security/test orchestration; J-T1–5 include D01's local diagnosis; S-T1–5 include D26's sampled distributed tail latency. M-D2/3 concern query design rather than evidence-driven investigation. |
| 16. Grade fit | Applies diagnostic reasoning to query/component interaction. |
| 17. Difficulty fit | APPLIED requires interpreting a small evidence set. |
| 18. Competency fit | Performance debugging rather than recalling SQL/index syntax. |
| 19. Wording exclusions | “Get a query plan” as the entire task; irrelevant HTML/code metrics; production mutation presented as diagnosis. |

### D13 — Senior cancellation across ownership boundaries

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-programming-2-v1` |
| 2. Replacement code | `backend-senior-programming-2-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-senior-programming-2-v1` |
| 5. Frozen metadata | SENIOR / PROGRAMMING / APPLIED |
| 6. Audit categories | GRADE_TOO_EASY, WEAK_DISTRACTORS |
| 7. Root cause | Generic cleanup, without system ownership/failure judgment. |
| 8. Cognitive target | Compare task/resource ownership when local cancellation cannot establish a remote outcome. |
| 9. Scenario shape | Request reserves remote capacity; caller cancels as the provider accepts it, before the response is received; the application can restart. |
| 10. Explicit constraints | Provider supports durable intent lookup and repeatable release; reservation lifetime exceeds the required cleanup window; remote cancellation is not guaranteed; cancellation may race acceptance; recovery must survive application restart. |
| 11. Decision dimensions | Ownership transfer, uncertain outcome, cleanup durability and bounded resource retention. |
| 12. Abstract correct-option concept | Recoverable ownership of resources beyond caller lifetime. |
| 13. Three distractor families | Request-scoped cleanup requiring an already-known handle; background cleanup owned only by the same process; provider expiry that is safe but exceeds the required cleanup window. |
| 14. Ambiguity risks | State lookup/release capabilities and the exact ownership interval; otherwise no strategy can promise bounded cleanup. |
| 15. Near-duplicate checks | S-P1/3/4/5 concern overload, workload placement, total deadline and shared work; J-P1–5 include local file cleanup; M-P1–5 include bounded SDK execution. S-A2 addresses stale writer authority; D20 addresses API operation identity, not resource-owner lifetime. |
| 16. Grade fit | Remote outcome uncertainty and process failure affect ownership. |
| 17. Difficulty fit | APPLIED compares lifecycle strategies under a concrete remote contract. |
| 18. Competency fit | Cancellation and task/resource lifecycle in program execution. |
| 19. Wording exclusions | “Use finally” alone; assumed remote rollback; exact recovery algorithm or implementation steps. |

### D14 — Senior measured compute placement

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-programming-3-v1` |
| 2. Replacement code | `backend-senior-programming-3-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-senior-programming-3-v1` |
| 5. Frozen metadata | SENIOR / PROGRAMMING / APPLIED |
| 6. Audit categories | GRADE_TOO_EASY, WEAK_DISTRACTORS |
| 7. Root cause | Runtime-property recognition, despite an already-explicit GIL context. |
| 8. Cognitive target | Choose compute placement using measured execution, transfer and memory costs. |
| 9. Scenario shape | A service mixes small interactive work with large pure-Python calculations; benchmarks compare unbatched and bounded batched execution. |
| 10. Explicit constraints | GIL-enabled CPython 3.13; no GIL-releasing native code in measured function; fixed CPU/RAM; serialization/startup costs and p99 requirement supplied; no approved native replacement or remote service in this release; batching limit supplied. |
| 11. Decision dimensions | CPU utilization, IPC cost, resident memory, request latency and deployment feasibility. |
| 12. Abstract correct-option concept | Workload placement justified by the supplied cost envelope. |
| 13. Three distractor families | More threads appropriate for I/O but not this measured workload; one process per small unit with dominant IPC/startup cost; throughput-maximizing large batches exceeding p99 or memory limits. |
| 14. Ambiguity risks | Provide comparable benchmarks; make runtime mode explicit; do not imply every Python runtime or native extension behaves identically. |
| 15. Near-duplicate checks | S-P1/2/4/5 concern overload/lifecycle/deadlines/shared work; J-P1–5 are language-local; M-P1–5 concern I/O and pipeline execution. D02 isolates blocking I/O and D26 investigates latency, rather than selecting CPU placement from costs. |
| 16. Grade fit | Balances measured system capacity and operational constraints. |
| 17. Difficulty fit | APPLIED needs evidence comparison beyond naming the GIL. |
| 18. Competency fit | Runtime execution and computation placement. |
| 19. Wording exclusions | “Processes are always faster”; missing IPC costs; obscure runtime release trivia; invented VERSION_SPECIFIC finding. |

### D15 — Senior shared computation lifecycle

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-programming-5-v1` |
| 2. Replacement code | `backend-senior-programming-5-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-senior-programming-5-v1` |
| 5. Frozen metadata | SENIOR / PROGRAMMING / ADVANCED |
| 6. Audit categories | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS |
| 7. Root cause | One local concurrency pattern, without consequences of shared ownership. |
| 8. Cognitive target | Compare shared-work strategies across waiter cancellation, worker restart and late completion. |
| 9. Scenario shape | Several instances request an expensive result for the same key; one waiter times out, the compute owner restarts and a delayed result later arrives. |
| 10. Explicit constraints | Shared compute service has durable job identity/status; freshness generations are supplied; live waiters still need a result; finite key/concurrency budget; independent caller deadlines; late older generation must not replace newer data; stale serving explicitly disallowed. |
| 11. Decision dimensions | Caller versus work lifetime, cross-instance coordination, retry ownership, freshness and bounded state. |
| 12. Abstract correct-option concept | Shared-result ownership consistent with independent waiters and generation validity. |
| 13. Three distractor families | Process-local coalescing that cannot cover other instances/restart; shared work owned by the first caller's cancellation; cross-instance coordination that accepts late completions without generation validation. |
| 14. Ambiguity risks | Declare durable compute capabilities and freshness policy; do not assume a TTL proves an older worker has stopped. |
| 15. Near-duplicate checks | S-P1–4 concern capacity, remote resource cleanup, compute cost and deadline; J-P1–5 and M-P1–5 do not coordinate shared results across independent callers. S-A2 is stale-write fencing alone; this design must require waiter/lifecycle/capacity reasoning as well. Compare D13 ownership carefully. |
| 16. Grade fit | Cross-instance ownership and operational failure determine the strategy. |
| 17. Difficulty fit | ADVANCED combines cancellation, restart, generations and bounded shared state. |
| 18. Competency fit | Shared task/result lifecycle and synchronization. |
| 19. Wording exclusions | Singleflight name as the answer; lock TTL as proof of safety; hiding architectural guarantees behind an unspecified library. |

### D16 — Senior API acceptance boundary

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-http_api-1-v1` |
| 2. Replacement code | `backend-senior-http_api-1-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-senior-http_api-1-v1` |
| 5. Frozen metadata | SENIOR / HTTP_API / BASIC |
| 6. Audit categories | GRADE_TOO_EASY, NEAR_DUPLICATE |
| 7. Root cause | No meaningful progression from Junior/Middle retry recognition. |
| 8. Cognitive target | Determine what an API may promise from evidence at different commitment boundaries. |
| 9. Scenario shape | API supplies a durable acceptance receipt; worker subsequently restarts; queue-delivery acknowledgement and an older cached status are also observed, but no authoritative terminal result exists. |
| 10. Explicit constraints | Acceptance is durable across restart; queue acknowledgement means delivery, not business completion; cache may lag; terminal operation status is authoritative; client-visible promise must remain true after recovery. |
| 11. Decision dimensions | Accepted work versus completed effect, authority of evidence and truthful observable guarantees. |
| 12. Abstract correct-option concept | Commitment claim bounded by authoritative lifecycle evidence. |
| 13. Three distractor families | Business completion inferred from durable acceptance; completion inferred from transport acknowledgement; durable commitment denied because a cached status lags. |
| 14. Ambiguity risks | Supply each acknowledgement's semantics; do not equate a bare HTTP status with durability or completion. |
| 15. Near-duplicate checks | S-H2–5 cover rollout, write authority, proxy trust and identity lifecycle; J-H1–5 include synchronous creation status; M-H1–5 include D07's client action. Known J-A5 is duplicate prevention. This design compares commitment evidence and requests no retry mechanism. |
| 16. Grade fit | Foundational system-contract judgment across transport, worker and durable state. |
| 17. Difficulty fit | BASIC has one central commitment-boundary principle, applied to contrasting evidence; no multi-step architecture design. |
| 18. Competency fit | Meaning and durability of API-visible acknowledgements. |
| 19. Wording exclusions | HTTP status-name quiz; “timeout means unknown” as the whole task; idempotency-key recognition; assuming a delivery ack proves a business effect. |

### D17 — Senior mixed-version API rollout

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-http_api-2-v1` |
| 2. Replacement code | `backend-senior-http_api-2-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-senior-http_api-2-v1` |
| 5. Frozen metadata | SENIOR / HTTP_API / APPLIED |
| 6. Audit categories | GRADE_TOO_EASY, WEAK_DISTRACTORS |
| 7. Root cause | Generic migration declaration without viability comparison. |
| 8. Cognitive target | Select API transition strategy from an explicit mixed-client/server compatibility matrix. |
| 9. Scenario shape | New callers send a required business attribute; old callers cannot upgrade immediately; old/new server instances coexist and rollback remains possible. |
| 10. Explicit constraints | Old semantics remain permitted for a stated transition window; omitted value cannot safely be guessed; routed versioned contracts are available; supported client/server combinations and rollback duration given; no coordinated all-client deployment. |
| 11. Decision dimensions | Consumer compatibility, routing, semantic completeness and rollback. |
| 12. Abstract correct-option concept | Transition preserving supported semantics throughout the mixed-version window. |
| 13. Three distractor families | Optional field with a semantically invalid default; new client rollout before compatible server routing; retirement of the old contract while mandated old clients remain. |
| 14. Ambiguity risks | If old semantics become forbidden immediately, retaining them is invalid; supply the permitted window and supported matrix. |
| 15. Near-duplicate checks | S-H1/3/4/5 test different system contracts; J-H1–5 are request-level rules; M-H1–5 apply existing contracts. D22 concerns DB schema/backfill, while this design judges consumer/server interoperability and versioned semantics. |
| 16. Grade fit | Compatibility and rollback across independently deployed participants. |
| 17. Difficulty fit | APPLIED compares viable rollout strategies against a supplied matrix. |
| 18. Competency fit | API evolution and externally observable contract compatibility. |
| 19. Wording exclusions | “Use versioning” alone; invented canonical default; changing this platform's API; vague compatibility with no supported combinations. |

### D18 — Senior mutation authority across replicas

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-http_api-3-v1` |
| 2. Replacement code | `backend-senior-http_api-3-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-senior-http_api-3-v1` |
| 5. Frozen metadata | SENIOR / HTTP_API / APPLIED |
| 6. Audit categories | WEAK_DISTRACTORS |
| 7. Root cause | Concurrency without serious alternative authority architectures. |
| 8. Cognitive target | Compare conditional-write authorities with lagging regional reads. |
| 9. Scenario shape | Multiple API regions read asynchronously replicated documents; competing edits must not silently succeed from the same version. |
| 10. Explicit constraints | One authoritative write store supports atomic version predicates; replica lag supplied; authoritative routing fits latency budget; stale writes must be rejected, not automatically merged; partition behavior explicitly favors consistency over regional write availability. |
| 11. Decision dimensions | Read versus write authority, conditional atomicity, partition policy and latency. |
| 12. Abstract correct-option concept | Mutation authority preserving the required conditional contract. |
| 13. Three distractor families | Regional precondition checks against lagging replicas; independent regional writes with later last-writer reconciliation; process-local locks around separately checked versions. |
| 14. Ambiguity risks | Multi-primary stores or permitted merge change the choice; fix topology and supplied capabilities rather than asserting a universal architecture. |
| 15. Near-duplicate checks | S-H1/2/4/5 cover other API boundaries; J-H1–5 are local rules; M-H1–5 include D05, where atomicity is already a supplied capability. M-D1 is local update protection; S-A5 is read-your-writes, not rejecting stale competing mutations. |
| 16. Grade fit | Distributed authority and partition consequences drive judgment. |
| 17. Difficulty fit | APPLIED compares system strategies in one fixed topology. |
| 18. Competency fit | Enforcement of a client-visible conditional mutation contract. |
| 19. Wording exclusions | Conditional UPDATE alone as the complete answer; “eventual consistency is always wrong”; unstated routing budget. |

### D19 — Senior proxy-derived authority

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-http_api-4-v1` |
| 2. Replacement code | `backend-senior-http_api-4-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-senior-http_api-4-v1` |
| 5. Frozen metadata | SENIOR / HTTP_API / APPLIED |
| 6. Audit categories | WEAK_DISTRACTORS |
| 7. Root cause | Alternatives use obviously invalid trust evidence. |
| 8. Cognitive target | Compare trust reconstruction for a multi-hop API ingress during topology change. |
| 9. Scenario shape | Edge and internal proxy forward host/scheme for security-sensitive links; a rolling change introduces a shorter internal route while direct backend access is still possible. |
| 10. Explicit constraints | Hop identities and overwrite/append behavior supplied; backend network exposure explicit; permitted host set supplied; client-origin values can enter at the untrusted edge; trusted ingress normalization is controllable. |
| 11. Decision dimensions | Hop provenance, normalization, route variability and destination authority. |
| 12. Abstract correct-option concept | Derived authority bounded by verifiable ingress provenance. |
| 13. Three distractor families | Fixed hop-count trust that fails on the shorter route; immediate-proxy trust with unsanitized inherited values; host allowlist without scheme/provenance protection. |
| 14. Ambiguity risks | Header rules differ by proxy; provide topology semantics and avoid relying on a framework's default parsing. |
| 15. Near-duplicate checks | S-H1/2/3/5 assess other contract boundaries; J-H1–5 include basic trusted identity/Origin; M-H1–5 cover representation/retry/caching. M-T2 tests outbound SSRF destinations, not inbound proxy authority. |
| 16. Grade fit | Security boundary changes across deployment paths require system judgment. |
| 17. Difficulty fit | APPLIED compares reasonable trust configurations against explicit routes. |
| 18. Competency fit | API request authority reconstructed through HTTP intermediaries. |
| 19. Wording exclusions | Trust by header length/User-Agent; arbitrary proxy syntax; a fixed hop rule asserted valid for every deployment. |

### D20 — Senior operation identity lifecycle

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-http_api-5-v1` |
| 2. Replacement code | `backend-senior-http_api-5-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-senior-http_api-5-v1` |
| 5. Frozen metadata | SENIOR / HTTP_API / ADVANCED |
| 6. Audit categories | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS |
| 7. Root cause | Fingerprint mismatch recognition without operation-lifecycle reasoning. |
| 8. Cognitive target | Compare operation identity policies under overlapping retry, retention and completion windows. |
| 9. Scenario shape | Long-running operation can outlive a response-cache TTL; clients restart and retry, changed payloads reuse a reference, and delayed terminal callbacks arrive. |
| 10. Explicit constraints | Caller/operation scope defined; payload-equivalence rules supplied; provider can identify intent; nonterminal work may exceed ordinary response retention; retry horizon and late-callback bound supplied; new legitimate intent has an explicit new identity; no claim of automatic exactly-once effects. |
| 11. Decision dimensions | Intent identity, nonterminal ownership, retirement horizon, conflicts and stale completion. |
| 12. Abstract correct-option concept | Operation identity valid across the complete retry/completion envelope. |
| 13. Three distractor families | Response-cache TTL treated as operation lifetime; deduplication by payload that merges distinct legitimate intents; renewed identity for a pending retry that permits a second effect. |
| 14. Ambiguity risks | Unbounded late arrivals would invalidate finite retirement; make bounds and provider guarantees explicit; distinguish terminal failure from uncertain outcome. |
| 15. Near-duplicate checks | S-H1–4 remain acceptance, rollout, authority and ingress tasks; J-H1–5 and M-H1–5 inspected. Known J-A5 recognizes deduplication; D07 follows a supplied client contract; D16 judges acknowledgement evidence. S-A3 handles projection event order, not API intent retirement. |
| 16. Grade fit | Lifecycle guarantees span clients, server persistence and remote completion. |
| 17. Difficulty fit | ADVANCED combines identity, retention, pending work and late events. |
| 18. Competency fit | Long-running API operation/retry/conflict contract. |
| 19. Wording exclusions | Fingerprint alone as the whole task; unspecified TTLs; exactly-once slogans; full state-transition solution. |

### D21 — Senior multi-row invariant foundation

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-databases-1-v1` |
| 2. Replacement code | `backend-senior-databases-1-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-senior-databases-1-v1` |
| 5. Frozen metadata | SENIOR / DATABASES / BASIC |
| 6. Audit categories | TRIVIA, WEAK_DISTRACTORS |
| 7. Root cause | Naming an anomaly without choosing invariant protection. |
| 8. Cognitive target | Identify whether protection covers the complete invariant, including an empty qualifying set. |
| 9. Scenario shape | Concurrent booking transactions each observe capacity remaining and insert different rows; candidate strategies protect different scopes. |
| 10. Explicit constraints | PostgreSQL 17 READ COMMITTED baseline; invariant applies to all bookings for a resource; an empty result is possible; no existing uniqueness constraint represents the limit; shared per-resource coordination record available; no external effects. |
| 11. Decision dimensions | Predicate scope, common coordination point and insert concurrency. |
| 12. Abstract correct-option concept | Protection scope matching the complete resource invariant. |
| 13. Three distractor families | Locks only on existing matching bookings; independent transactions using a consistent but nonexclusive view; per-booking uniqueness that does not enforce total capacity. |
| 14. Ambiguity risks | Supply isolation and schema; do not include two equally effective invariant strategies without a distinguishing constraint. |
| 15. Near-duplicate checks | S-D2/3/4/5 cover serialization recovery, schema rollout, queue workers and lifecycle invariants; J-D1–5 cover elementary constraints/transactions; M-D1–5 include one-row lost update. D23 adds lifecycle races rather than reasking predicate protection. |
| 16. Grade fit | Foundation of system consistency: identify the invariant's coordination scope. |
| 17. Difficulty fit | BASIC focuses on one principle with a meaningful empty-set counterexample. |
| 18. Competency fit | DB concurrency and invariant enforcement. |
| 19. Wording exclusions | Anomaly-name quiz; incorrectly implying row locks protect absent rows; choosing SERIALIZABLE by keyword with no stated context. |

### D22 — Senior constrained schema rollout

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-databases-3-v1` |
| 2. Replacement code | `backend-senior-databases-3-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-senior-databases-3-v1` |
| 5. Frozen metadata | SENIOR / DATABASES / APPLIED |
| 6. Audit categories | WEAK_DISTRACTORS |
| 7. Root cause | No comparison of viable rollout strategies. |
| 8. Cognitive target | Compare migration plans against writer compatibility, backfill and lock requirements. |
| 9. Scenario shape | Large PostgreSQL table gains a required derived attribute while old/new writers coexist and a batch backfill can restart. |
| 10. Explicit constraints | PostgreSQL 17; no universally valid constant default; old writers must remain supported during rollback window; write traffic cannot pause; lock budget and measured DDL characteristics supplied; backfill can race new writes; enforcement follows demonstrated complete coverage. |
| 11. Decision dimensions | Writer coverage, rollout order, stale backfill, restart safety and locking. |
| 12. Abstract correct-option concept | Schema transition preserving valid writes and convergence throughout rollout. |
| 13. Three distractor families | Immediate default-based constraint that changes meaning; backfill before protecting writes from old instances; correct phased migration with one long blocking backfill beyond the operational budget. |
| 14. Ambiguity risks | Do not claim every NOT NULL/add-column operation rewrites a table; supply relevant DDL behavior and recovery semantics. |
| 15. Near-duplicate checks | S-D1/2/4/5 cover invariants/retries/workers/lifecycle; J-D1–5 cover schema fundamentals; M-D1–5 cover transaction/query implementation. D17 judges external API compatibility, not DB writer/backfill convergence. |
| 16. Grade fit | Mixed deployments and ongoing mutations determine rollout safety. |
| 17. Difficulty fit | APPLIED compares plans under a specified operating envelope. |
| 18. Competency fit | Database schema evolution and data migration. |
| 19. Wording exclusions | Expand/contract slogan alone; destructive absurd alternatives; version-dependent lock claims without stated behavior; exact migration script. |

### D23 — Senior reservation lifecycle invariant

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-databases-5-v1` |
| 2. Replacement code | `backend-senior-databases-5-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-senior-databases-5-v1` |
| 5. Frozen metadata | SENIOR / DATABASES / ADVANCED |
| 6. Audit categories | GRADE_TOO_EASY, DIFFICULTY_MISMATCH, NEAR_DUPLICATE |
| 7. Root cause | One-row conflict resembles Middle BASIC, not Senior ADVANCED. |
| 8. Cognitive target | Compare DB state models that maintain an invariant across competing reservation transitions. |
| 9. Scenario shape | Reservation expiry releases capacity while delayed confirmation and redelivered commands concurrently arrive; process restart may interrupt a transition. |
| 10. Explicit constraints | Capacity and reservations share one authoritative transactional DB; confirmation/expiry policy supplied; command identities stable; each reservation has one terminal disposition; stock/reservation updates atomic; expired confirmation has an explicit business outcome; external payment effects excluded. |
| 11. Decision dimensions | Transition ownership, duplicate effects, inventory conservation, crash atomicity and late commands. |
| 12. Abstract correct-option concept | Transactional lifecycle model preserving conservation across competing commands. |
| 13. Three distractor families | Atomic stock decrement without reservation-transition guard; per-command deduplication that cannot prevent different commands winning the same reservation; durable reservation state and separate stock update that split on crash. |
| 14. Ambiguity risks | Supply late-confirmation policy and DB topology; do not force inference of cancellation/payment rules. |
| 15. Near-duplicate checks | S-D1–4 cover predicate protection/retries/rollout/worker claiming; J-D1–5 cover local integrity; M-D1–5 inspected. Known M-D1 guards one lost update; this design combines distinct transitions and conservation. M-A5 is duplicate consumer effect alone, not competing reservation dispositions. |
| 16. Grade fit | Concurrent lifecycle and crash consistency drive the state-model judgment. |
| 17. Difficulty fit | ADVANCED combines different commands, duplicates, late arrival and atomic invariants. |
| 18. Competency fit | Canonical DB state transitions and transaction correctness. |
| 19. Wording exclusions | Conditional decrement as a complete solution; unspecified business policy; payment-distribution architecture; multiple unrelated invariants. |

### D24 — Senior canonical order across services

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-architecture-4-v2` |
| 2. Replacement code | `backend-senior-architecture-4-v3` |
| 3. Version | 3 |
| 4. Supersedes | `backend-senior-architecture-4-v2` |
| 5. Frozen metadata | SENIOR / ARCHITECTURE / APPLIED |
| 6. Audit categories | GRADE_TOO_EASY, WEAK_DISTRACTORS |
| 7. Root cause | Local order-price snapshot, without system trade-offs or partial failures. |
| 8. Cognitive target | Compare canonical-data ownership across catalog and order service failure boundaries. |
| 9. Scenario shape | Catalog issues a trusted price decision; order creation retries during a catalog rollout/outage; billing and historical reads must retain the accepted terms. |
| 10. Explicit constraints | Trusted server-issued quote identity/version/expiry; quote may be accepted before expiry only; accepted terms cannot change retrospectively; repeated creation has stable intent; services do not share a transaction; accepted quote/order association must survive restart. |
| 11. Decision dimensions | Authority, decision time, canonical ownership, replay and partial availability. |
| 12. Abstract correct-option concept | Durable order ownership of an accepted, verifiable commercial decision. |
| 13. Three distractor families | Catalog remains canonical for historical reads after acceptance; trusted quote cached only in process through retry/restart; order stores a price but discards the decision identity needed to distinguish replay from a fresh quote. |
| 14. Ambiguity risks | Supply acceptance/expiry policy and trusted quote guarantees; a mutable-price product would require another answer. |
| 15. Near-duplicate checks | S-A1/2/3/5 cover DB/broker boundary, fencing, projection order and read-your-writes; J-A1–5 cover service placement/local resilience; M-A1–5 cover outbox/cache/consumer behavior. D20 is operation identity lifecycle; this design must decide commercial-data authority across services. |
| 16. Grade fit | Canonical ownership across independent services and partial failure. |
| 17. Difficulty fit | APPLIED compares data-boundary strategies in a concrete system. |
| 18. Competency fit | Architecture of canonical domain data and service ownership. |
| 19. Wording exclusions | “Store price in the order” alone; client-provided canonical price; platform economy changes; exact multi-service protocol. |

### D25 — Senior observable privacy boundary

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-testing_security_debugging-1-v1` |
| 2. Replacement code | `backend-senior-testing_security_debugging-1-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-senior-testing_security_debugging-1-v1` |
| 5. Frozen metadata | SENIOR / TESTING_SECURITY_DEBUGGING / BASIC |
| 6. Audit categories | GRADE_TOO_EASY, WEAK_DISTRACTORS |
| 7. Root cause | Only fundamental sensitive-logging recognition; obvious unsafe alternatives. |
| 8. Cognitive target | Locate the evidence/privacy boundary before diagnostic data crosses service ownership. |
| 9. Scenario shape | Authentication incidents need cross-service correlation; a collector managed by another team receives events from independently deployed producers. |
| 10. Explicit constraints | Incident correlation requirement supplied; collector must never receive reusable credentials or raw identities; producer-side schema/filtering available; allowed pseudonymous correlation fields specified; downstream encryption/access controls do not satisfy pre-ingestion minimization. |
| 11. Decision dimensions | Evidence sufficiency, data-flow boundary, independent producers and control timing. |
| 12. Abstract correct-option concept | Diagnostic evidence bounded before crossing the protected ingestion boundary. |
| 13. Three distractor families | Encryption/access restriction after collection; collector-side redaction after forbidden data arrives; complete correlation suppression that meets privacy but defeats the incident requirement. |
| 14. Ambiguity risks | State the precise forbidden data boundary and allowed correlation; avoid treating all hashes or identifiers as inherently anonymous. |
| 15. Near-duplicate checks | S-T2–5 concern atomicity, cache risk, tail diagnosis and fault coverage; J-T1–5 include password/safe-error fundamentals; M-T1–5 concern local access/testing. D19 reconstructs request authority, not observability-data minimization. |
| 16. Grade fit | Foundation of observability governance across producer/collector boundaries. |
| 17. Difficulty fit | BASIC focuses on control placement with both evidence and privacy obligations. |
| 18. Competency fit | Security and operational diagnostic evidence. |
| 19. Wording exclusions | Password logging as the only distractor; hash equals anonymization; arbitrary compliance law; a complete event-schema answer. |

### D26 — Senior distributed tail diagnosis

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-testing_security_debugging-4-v1` |
| 2. Replacement code | `backend-senior-testing_security_debugging-4-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-senior-testing_security_debugging-4-v1` |
| 5. Frozen metadata | SENIOR / TESTING_SECURITY_DEBUGGING / APPLIED |
| 6. Audit categories | WEAK_DISTRACTORS |
| 7. Root cause | Generic observability category recognition without measurements. |
| 8. Cognitive target | Choose the next discriminating investigation from contradictory sampled and population evidence. |
| 9. Scenario shape | Population p99 rises in one request cohort while sampled dependency execution spans stay stable; queue residence and retries are not yet linked to the same requests. |
| 10. Explicit constraints | Cohort/load comparability; sampling coverage and missing span boundaries supplied; independent stage timings; no cross-machine timestamp subtraction without clock assumptions; fixed observability budget; investigation must distinguish queue/retry amplification from dependency execution. |
| 11. Decision dimensions | Sampling bias, omitted latency, cohort correlation and causal discrimination. |
| 12. Abstract correct-option concept | Evidence collection that distinguishes the remaining system-latency hypotheses. |
| 13. Three distractor families | More of the same dependency-only samples; fleet-wide averages concealing the affected cohort; symptom-oriented timeout changes before linking delay stages. |
| 14. Ambiguity risks | Give collection gaps and population evidence explicitly; otherwise additional tracing of any stage might be equally useful. |
| 15. Near-duplicate checks | S-T1/2/3/5 cover privacy/atomicity/cache risk/crash coverage; J-T1–5 include D01; M-T1–5 include D12's query-local evidence. S-P3 chooses measured compute placement, not a discriminating cross-service investigation. |
| 16. Grade fit | System evidence gaps and sampling affect causal judgment. |
| 17. Difficulty fit | APPLIED compares investigative strategies using a concrete distributed evidence set. |
| 18. Competency fit | Observability and performance diagnosis. |
| 19. Wording exclusions | “Add tracing” alone; equating quantiles with per-request sums; misleading unsynchronized timestamps; generic instrumentation shopping list. |

### D27 — Senior recovery verification design

| Field | Design |
|---|---|
| 1. Current code | `backend-senior-testing_security_debugging-5-v1` |
| 2. Replacement code | `backend-senior-testing_security_debugging-5-v2` |
| 3. Version | 2 |
| 4. Supersedes | `backend-senior-testing_security_debugging-5-v1` |
| 5. Frozen metadata | SENIOR / TESTING_SECURITY_DEBUGGING / ADVANCED |
| 6. Audit categories | WEAK_DISTRACTORS |
| 7. Root cause | Alternatives evade the requirement instead of offering comparable recovery tests. |
| 8. Cognitive target | Select fault coverage and independent oracles for unknown external outcome plus replay. |
| 9. Scenario shape | Consumer rollout may crash after the provider applies an effect but before local receipt/ack; redelivery and a second legitimate command then occur after restart. |
| 10. Explicit constraints | Provider supports durable intent lookup/deduplication; broker redelivers unacked messages; process actually restarts; effects independently observable; both duplicate suppression and legitimate progress required; fault locations/old-new compatibility supplied; finite test budget. |
| 11. Decision dimensions | Unknown outcome, durable restart, replay identity, independent effect oracle and false suppression. |
| 12. Abstract correct-option concept | Recovery evidence covering both invariant safety and legitimate progress. |
| 13. Three distractor families | Fault only before effect, missing uncertain completion; crash/replay test with provider mocked as always known-success; duplicate test proving no second effect but never checking a distinct legitimate command. |
| 14. Ambiguity risks | Without provider guarantees the claimed invariant may be impossible; distinguish deduplication of one intent from loss of future intents. |
| 15. Near-duplicate checks | S-T1–4 cover privacy, local atomic rollback, cache access and diagnosis; J-T1–5 test local regression/errors; M-T1–5 include concurrent-start orchestration. S-T2 is one-DB rollback; M-A5 is consumer implementation, while this design judges fault placement and independent recovery evidence. |
| 16. Grade fit | Operational failure and interoperability determine whether evidence proves the claim. |
| 17. Difficulty fit | ADVANCED combines unknown effect, restart, redelivery, independent oracles and legitimate progress. |
| 18. Competency fit | Resilience test design and interpretation of recovery evidence. |
| 19. Wording exclusions | “Inject a failure” alone; magic exactly-once claim; no-replay alternatives; full test implementation or expected answer sequence. |

## E. Bucket review — 11 affected groups

The following is the intended cognitive spread after implementation, not a new source or a post-remediation finding. Slot aliases resolve to inspected current codes under section D's convention. An unchanged slot retains its current text, metadata and audit outcome, including MINOR. Within each row the five tasks are deliberately different; none of the three APPLIED designs merely restates the BASIC/ADVANCED task.

| Group | Replacements | Current weakness | BASIC: slot 1 | APPLIED: slot 2 | APPLIED: slot 3 | APPLIED: slot 4 | ADVANCED: slot 5 |
|---|---:|---|---|---|---|---|---|
| E01 JUNIOR / TESTING_SECURITY_DEBUGGING | 1 | Diagnostic ADVANCED lacks fact/hypothesis analysis; two MINOR items untouched. | J-T1: password-storage fundamentals, unchanged. | J-T2: input/query boundary, unchanged. | J-T3: local validation regression, MINOR unchanged. | J-T4: safe client error boundary, MINOR unchanged. | J-T5/D01: correlate local observations and choose a discriminating check. |
| E02 MIDDLE / PROGRAMMING | 3 | I/O alternatives weak; streaming remains Junior-local; load limiting lacks consequences. | M-P1: local async race, unchanged. | M-P2/D02: constrained blocking SDK integration. | M-P3/D03: end-to-end streaming through a slower sink. | M-P4: stable hash/equality identity, unchanged. | M-P5/D04: admission, retries and task lifetime under overload. |
| E03 MIDDLE / HTTP_API | 3 | Weak editing/cache choices and repeated Junior retry task. | M-H1: method-effect semantics, unchanged. | M-H2/D05: stale full-representation mutation contract. | M-H3/D06: account-boundary storage/reuse policy. | M-H4/D07: action from supplied retry/status state. | M-H5: pagination under changing data, unchanged. |
| E04 MIDDLE / DATABASES | 2 | ORM recognition and lock-lifetime fact replace application. | M-D1: one-row lost-update protection, unchanged. | M-D2/D08: loading under cardinality/latency constraints. | M-D3: query/index shape, unchanged. | M-D4/D09: transaction boundary across a slow pure dependency. | M-D5: lock ordering and transaction recovery, unchanged. |
| E05 MIDDLE / ARCHITECTURE | 1 | Cascading-failure options do not compete. | M-A1: canonical versus derived state, unchanged. | M-A2: DB/event publication boundary, unchanged. | M-A3/D10: optional-dependency containment/recovery. | M-A4: cache-aside invalidation, unchanged. | M-A5: durable duplicate-event effect, unchanged. |
| E06 MIDDLE / TESTING_SECURITY_DEBUGGING | 2 | Deadline wording giveaway and evidence-free SQL diagnosis. | M-T1: object ownership, unchanged. | M-T2: outbound request destination risk, unchanged. | M-T3/D11: deterministic persisted deadline enforcement. | M-T4/D12: discriminating measurement from query evidence. | M-T5: actual concurrent-start evidence, unchanged. |
| E07 SENIOR / PROGRAMMING | 3 | Cleanup/runtime recognition and local coalescing below cognitive target. | S-P1: overload admission foundation, unchanged. | S-P2/D13: remote resource ownership after cancellation/restart. | S-P3/D14: measured compute placement under IPC/RAM/p99 limits. | S-P4: overall operation deadline, unchanged. | S-P5/D15: independent waiters, restart and generation-valid shared work. |
| E08 SENIOR / HTTP_API | 5 | All five tasks are flagged; duplicate retry recognition and weak system alternatives. | S-H1/D16: commitment evidence across API/worker boundaries. | S-H2/D17: mixed-version consumer/server compatibility. | S-H3/D18: distributed conditional mutation authority. | S-H4/D19: ingress trust during topology change. | S-H5/D20: complete operation identity/retirement envelope. |
| E09 SENIOR / DATABASES | 3 | Invariant vocabulary, generic migration and Middle-like local stock update. | S-D1/D21: protection scope for a multi-row invariant. | S-D2: serialization-failure recovery, unchanged. | S-D3/D22: writer/backfill/lock-safe rollout. | S-D4: concurrent worker claiming semantics, unchanged. | S-D5/D23: competing reservation dispositions and conservation after crash. |
| E10 SENIOR / ARCHITECTURE | 1 | Order decision remains local rather than cross-service ownership. | S-A1: local transaction versus broker boundary, unchanged. | S-A2: stale-owner write protection, unchanged. | S-A3: projection ordering/recovery, unchanged. | S-A4/D24: accepted commercial decision across catalog/order lifecycle. | S-A5: read-your-writes across replication lag, unchanged. |
| E11 SENIOR / TESTING_SECURITY_DEBUGGING | 3 | Logging fundamental too easy; evidence-free diagnosis; shallow fault alternatives. | S-T1/D25: pre-ingestion evidence/privacy boundary. | S-T2: atomic rollback evidence, unchanged. | S-T3: application-cache access risk, MINOR unchanged. | S-T4/D26: sampled versus population evidence for tail latency. | S-T5/D27: unknown external effect, restart, replay and legitimate-progress evidence. |

### Senior HTTP/API coherence and duplicate controls

| Slot | Required distinguishing reasoning | Boundary that keeps it separate |
|---|---|---|
| BASIC D16 | Reconcile durable receipt, delivery acknowledgement and stale observation to bound a public commitment. | One foundational evidence/commitment distinction; no operation-identity architecture or retry-choice question. |
| APPLIED D17 | Test each proposed rollout against old/new client/server combinations and rollback. | Compatibility in time, not HTTP cache behavior or database migration syntax. |
| APPLIED D18 | Determine which store can enforce conditional mutations given replica lag and partition policy. | Write authority under concurrency; not just choosing a header or satisfying read-your-writes. |
| APPLIED D19 | Follow header provenance through variable ingress routes and permitted hosts/schemes. | Trust boundary across deployment topology; not outbound SSRF or a generic “do not trust client” rule. |
| ADVANCED D20 | Compare identity/retirement policies against overlapping nonterminal work, retries, changed intent and delayed completion. | Several lifecycle constraints interact; not just receipt meaning, key existence or fingerprint mismatch. |

All five compare viable families under stated constraints. BASIC contains one system principle; APPLIED asks for a strategy in a fixed system; ADVANCED requires checking several interacting lifecycle conditions. D16/D20 share an operation topic but have different evidence and required actions. D17/D22 share evolution, with separate API-consumer and DB-writer guarantees. D18/D05 share concurrency, with distributed authority versus an already-supported client precondition. D19 must not borrow D25's observability-data control question.

Known overlap triple is split deliberately: unchanged J-A5 tests basic duplicate prevention; D07 applies an existing state contract to one client action; D16 evaluates API commitment evidence. D20 adds identity retirement across uncertain long-running work. Merely replacing “order” with “payment” is insufficient. For the second known pair, unchanged M-D1 remains a one-row lost-update task; D23 requires competing reservation dispositions, replay and crash conservation. P3-C must check whether final wording actually achieves these distinctions.

## F. Cross-grade progression review

Every replacement was compared with all ten current same-competency records in the other grades, and with proposed same-competency replacements. The compact registry here identifies those comparison sets: J/M/S-P1–5; J/M/S-H1–5; J/M/S-D1–5; J/M/S-A1–5; J/M/S-T1–5. Section D identifies the closest cross-competency overlaps. Remaining current questions retain their text and audit result; designs do not silently repair unflagged or MINOR neighbors.

| Competency | Junior measures | Middle measures | Senior measures | Planned progression |
|---|---|---|---|---|
| PROGRAMMING | Object/list behavior, collection choice, defaults, file lifetime, sorting. | Local async race, constrained SDK integration, pipeline buffering, key identity and overload/task lifetime. | Admission foundation, remote ownership, measured runtime placement, total deadline and cross-instance shared work. | Local behavior → implementation/component consequences → ownership, measured system costs and operational failure. D02 and D14 explicitly distinguish I/O from measured CPU work. D03/D04/D15 distinguish flow, overload and shared-result lifetime. |
| HTTP_API | Status/validation/access/identity/CSRF in standard requests. | Existing method semantics, constrained editing, HTTP storage boundaries, client state/retry application and pagination. | Commitment evidence, compatibility matrix, write authority, ingress provenance and long-running identity. | Request correctness → applying a concrete contract → comparing system guarantees across deployment and failure. Progression is a different required reasoning operation, not harder protocol vocabulary. |
| DATABASES | Uniqueness, referential integrity, local atomicity, indexes, outer joins. | One-row concurrency, measured retrieval, index shape, transaction scope and deadlock recovery. | Complete invariant scope, serialization recovery, online rollout, worker claiming and multi-command lifecycle conservation. | Local guarantees → interaction/cost/transaction implementation → multi-row authority and operational consistency. D21/D23 are distinct foundation/lifecycle tasks; the known Middle/Senior overlap is not carried forward. |
| ARCHITECTURE | Shared service placement, single-request resilience, test dependency, shared sessions and duplicate intent. | Canonical/derived state, publication boundary, dependency containment, cache race and durable consumer effect. | Transaction boundary, stale owner, event order, accepted commercial authority and replicated reads. | Local component boundary → interacting service policy → canonical ownership and partial failure. D24 requires catalog/order authority across time and restart, not a local snapshot-placement recall. |
| TESTING_SECURITY_DEBUGGING | Secrets/query safety, local regression, client error boundary and local evidence diagnosis. | Ownership/SSRF, deterministic deadline enforcement, query evidence and actual concurrency testing. | Ingestion privacy, atomic rollback, cache access risk, biased distributed evidence and external-effect recovery tests. | Local safe behavior/evidence → validating interacting implementation → proof/evidence limitations across ownership and failure. D01/D12/D26 are local, query-level and distributed inference respectively; D11 and D27 have different test obligations. |

These are qualitative platform-rubric judgments. They are not empirical item difficulty, discrimination, reliability, cross-grade score equivalence or a claim that a competent Middle developer cannot ever answer a Senior question.

## G. Exact version map — 27 rows

| Old code | New code | New version | Supersedes |
|---|---|---:|---|
| backend-junior-testing_security_debugging-5-v1 | backend-junior-testing_security_debugging-5-v2 | 2 | backend-junior-testing_security_debugging-5-v1 |
| backend-middle-programming-2-v1 | backend-middle-programming-2-v2 | 2 | backend-middle-programming-2-v1 |
| backend-middle-programming-3-v1 | backend-middle-programming-3-v2 | 2 | backend-middle-programming-3-v1 |
| backend-middle-programming-5-v1 | backend-middle-programming-5-v2 | 2 | backend-middle-programming-5-v1 |
| backend-middle-http_api-2-v1 | backend-middle-http_api-2-v2 | 2 | backend-middle-http_api-2-v1 |
| backend-middle-http_api-3-v1 | backend-middle-http_api-3-v2 | 2 | backend-middle-http_api-3-v1 |
| backend-middle-http_api-4-v1 | backend-middle-http_api-4-v2 | 2 | backend-middle-http_api-4-v1 |
| backend-middle-databases-2-v1 | backend-middle-databases-2-v2 | 2 | backend-middle-databases-2-v1 |
| backend-middle-databases-4-v1 | backend-middle-databases-4-v2 | 2 | backend-middle-databases-4-v1 |
| backend-middle-architecture-3-v1 | backend-middle-architecture-3-v2 | 2 | backend-middle-architecture-3-v1 |
| backend-middle-testing_security_debugging-3-v1 | backend-middle-testing_security_debugging-3-v2 | 2 | backend-middle-testing_security_debugging-3-v1 |
| backend-middle-testing_security_debugging-4-v1 | backend-middle-testing_security_debugging-4-v2 | 2 | backend-middle-testing_security_debugging-4-v1 |
| backend-senior-programming-2-v1 | backend-senior-programming-2-v2 | 2 | backend-senior-programming-2-v1 |
| backend-senior-programming-3-v1 | backend-senior-programming-3-v2 | 2 | backend-senior-programming-3-v1 |
| backend-senior-programming-5-v1 | backend-senior-programming-5-v2 | 2 | backend-senior-programming-5-v1 |
| backend-senior-http_api-1-v1 | backend-senior-http_api-1-v2 | 2 | backend-senior-http_api-1-v1 |
| backend-senior-http_api-2-v1 | backend-senior-http_api-2-v2 | 2 | backend-senior-http_api-2-v1 |
| backend-senior-http_api-3-v1 | backend-senior-http_api-3-v2 | 2 | backend-senior-http_api-3-v1 |
| backend-senior-http_api-4-v1 | backend-senior-http_api-4-v2 | 2 | backend-senior-http_api-4-v1 |
| backend-senior-http_api-5-v1 | backend-senior-http_api-5-v2 | 2 | backend-senior-http_api-5-v1 |
| backend-senior-databases-1-v1 | backend-senior-databases-1-v2 | 2 | backend-senior-databases-1-v1 |
| backend-senior-databases-3-v1 | backend-senior-databases-3-v2 | 2 | backend-senior-databases-3-v1 |
| backend-senior-databases-5-v1 | backend-senior-databases-5-v2 | 2 | backend-senior-databases-5-v1 |
| backend-senior-architecture-4-v2 | backend-senior-architecture-4-v3 | 3 | backend-senior-architecture-4-v2 |
| backend-senior-testing_security_debugging-1-v1 | backend-senior-testing_security_debugging-1-v2 | 2 | backend-senior-testing_security_debugging-1-v1 |
| backend-senior-testing_security_debugging-4-v1 | backend-senior-testing_security_debugging-4-v2 | 2 | backend-senior-testing_security_debugging-4-v1 |
| backend-senior-testing_security_debugging-5-v1 | backend-senior-testing_security_debugging-5-v2 | 2 | backend-senior-testing_security_debugging-5-v1 |

Totals: **26 v1→v2**, **one v2→v3**. Each supersedes is the exact current predecessor. J-A1 v2 remains unchanged. Intended eventual current-source version distribution: 47 v1, 27 v2, one v3; total 75. This is a design expectation, not a changed inventory.

## H. Implementation constraints for P3-B

P3-B requires separate authorization following human review of this design.

1. Replace the 27 current source records one-for-one using section G. Do not retain old + new source copies: current JSON remains 75, with 25 per grade and 1/3/1 in every bucket.
2. Preserve grade/competency/difficulty, schema and Backend seed identity. Do not edit a published code's prompt/options/version in place. The 48 nontarget records, including all six MINOR, remain byte/content-equivalent.
3. Author final stems and four options privately in the production source under the unchanged internal source-correctness and ordering convention implemented by `seed_questions`. Retain that convention; verify marking through seed tests. Its positional rule, final order, key, solution and final correct-answer text must not be repeated in repository documentation or UI. No explicit positional rule is disclosed in this plan because the P3-A answer-key protection requirement applies here.
4. Preserve published DB rows/options/IDs and attempt references. An explicit replacement may deactivate the immediate predecessor; it must not rewrite content or delete history. Physical DB counts may exceed 75. Repeated seed preserves deliberate inactive flags; do not reactivate manually disabled questions to make tests pass.
5. Run the existing structural validator through `load_bank`; maintain safe error diagnostics, typed metadata, unique codes/options and supersedes graph checks. Source validity does not replace a runtime active-bank check.
6. Verify fresh seed, repeated seed and seed over the previous baseline bank. The previous current bank has 75 rows; with its 27 predecessors retained, a simple baseline-only DB would have 102 physical question rows after replacement, including 27 newly inactive predecessors and 75 current rows. Databases with earlier historical versions may have more; do not require a universal physical count.
7. Old+new seed regression must assert exact immutable old content/options and IDs, predecessor inactivity, new versions/metadata, repeated-seed idempotency, persisted attempt membership/option order and continued valid historical scoring. Exercise an active attempt referencing an old version across seed; it must still use that immutable version. Also exercise deliberate deactivation and fresh DBs with absent historical predecessors.
8. The existing validator/loader tests currently assert exactly two current v2 supersedes records. Later adjust those inventory expectations to the approved mapping and retain absent-predecessor/graph/privacy coverage; do not weaken count or history assertions. Reuse `test_bank_integrity_and_immutable_seed`, existing fixture infrastructure and the current assessment regressions. No seed/version redesign, dependency or new storage layer is implied.
9. Seed deactivates only the named immediate predecessor. Before a live rollout, verify the database already applied the inspected baseline's v2 replacements. A database that skipped that baseline could retain an older v1 as active when v3 supersedes an absent v2. Such a deployment needs explicit baseline-seed sequencing/operational review; do not silently invent transitive deactivation or mutate historical rows. This is a rollout caveat, not a blocker for design against the requested baseline.
10. No backend service, API/model/schema, migrations, scoring/threshold/selection/cooldown, canonical qualification, frontend, Matching, Invitations/O2 or FSP changes. If a real code-boundary blocker arises, stop and report before changing it.

### Technical fact checks used in the design

References support engineering assumptions only; they do not define platform grades or product rules. Scenario capabilities, policies and budgets must still appear in final stems. No reference supplies a question key.

- D02/D13/D14 use explicit execution/cancellation context: blocking I/O and GIL-enabled CPU work have different placement constraints; cancellation does not imply all underlying work has stopped. Checked against [Python 3.13 asyncio task/cancellation/thread documentation](https://docs.python.org/3.13/library/asyncio-task.html) and [executor Future cancellation](https://docs.python.org/3.13/library/concurrent.futures.html#concurrent.futures.Future.cancel).
- D05/D16 distinguish conditional request semantics and asynchronous acceptance from eventual completion, consistent with [HTTP Semantics, RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html). Durability/status capabilities in D16 are explicit scenario guarantees, not consequences inferred from a status number.
- D06 distinguishes storage prohibition, private storage and revalidation; compliant-cache and no-preexisting-copy assumptions are essential. Checked against [HTTP Caching, RFC 9111](https://datatracker.ietf.org/doc/html/rfc9111#section-5.2.2). Application history is not automatically an HTTP cache.
- D09/D21/D22/D23 pin DB context and avoid assuming row locks protect absent rows or that every schema change has the same lock/rewrite cost. Checked against [PostgreSQL 17 locking](https://www.postgresql.org/docs/17/explicit-locking.html) and [transaction isolation](https://www.postgresql.org/docs/17/transaction-iso.html). D22 requires operation-specific measured DDL facts at implementation time.
- D08 compares legitimate loading families without declaring joined loading intrinsically wrong: [SQLAlchemy 2.0 relationship loading](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html). The final question must provide costs rather than require framework API recall.

## I. Future audit plan — P3-C

Audit **all 75 active current source records**, including the 27 replacements, six unchanged MINOR and 42 previously unflagged records. Here “active current source” means the selected current JSON inventory, not every physical historical DB row. Freeze the inspected commit/source hash and record codes/versions; do not reconstruct the audit set from all live DB history. Live activation/availability is a separate P3-D gate.

1. Read each final stem and all four alternatives privately, using the same baseline rubric/severity definitions. Apply the baseline's 16 criteria: Backend specialization, grade fit, difficulty fit, competency fit, single best answer, multiple reasonable answers, ambiguity, hidden context dependency, trivia, version specificity, engineering knowledge versus wording guess, answer leakage, distractor quality, near-duplicates, difficulty within grade and overall rubric fit.
2. For each option concept, check technical validity under stated constraints and assumptions that could flip the choice. A valid competing architecture is not automatically a defect; two equally defensible choices under the actual stem are. Missing decisive context must become a finding, not an unwritten author assumption. Fact-check version-sensitive behavior against primary documentation with explicit version/context.
3. Reapply baseline severity: BLOCKER for unsupported unique scoring or missing decisive context; IMPORTANT for materially weakened grade/difficulty/competency measurement; MINOR for localized issues without established scoring failure. Count one record at its highest severity even when multiple categories apply.
4. Review all 15 grade × competency buckets, including the four unaffected buckets, for source 1/3/1 mix and cognitive spread. Compare all same-competency cross-grade records and relevant cross-competency overlap; explicitly revisit the two known overlap groups from section E. Detect new overlaps involving formerly unflagged records as well as replacements.
5. Perform the Senior recognition check on all 25 current Senior records, not only the 15 new ones. Evaluate final alternatives, not merely a sophisticated topic in the stem. Evaluate Junior local scope and Middle concrete application similarly.
6. Record a complete 75-code coverage register, metadata, maximum severity/category/reason, and resolved/persisting/new findings relative to baseline. Keep rationale safe: no final option text, positions, key or solution. Preserve the original baseline audit as provenance; a later result must identify its own commit/date/limitations.
7. Target **0 IMPORTANT**. This is a target, **not an allowed hardcoded conclusion**. Replacements may retain IMPORTANT or introduce BLOCKER/MINOR; the untouched records may acquire new findings through cross-bank comparison. Do not subtract 27 from the baseline without reviewing actual content. Six MINOR remain outside remediation scope; their current audit classification must still be honestly reevaluated.
8. Submit actual outcomes and a supported readiness recommendation for human review. No pilot, psychometric calibration, empirical discrimination, reliability or hiring-success claim follows from this expert audit.

## J. Readiness policy and P3-A quality review

Baseline remains **NOT_READY** until P3-B implementation, P3-C full audit and P3-D technical gate have completed. P3-A does not change readiness or claim findings resolved. A future **MVP_READY_WITH_MINOR_FINDINGS** may be used only if actual re-audit and technical evidence support it; neither the status nor resulting counts are predetermined here.

### Fourteen checks applied to each design

Q1 finding directly addressed; Q2 grade unchanged; Q3 competency unchanged; Q4 difficulty unchanged; Q5 cognitive task matches slot; Q6 three plausible distractor families; Q7 uniquely best choice can be authored under constraints; Q8 assumptions explicit; Q9 cognitive near-duplicate avoided in design comparison; Q10 no unnecessary framework/version trivia; Q11 no answer leakage; Q12 no obvious wording giveaways; Q13 materially different cognitive operation where required; Q14 intended competency preserved.

The table records **YES at design level for Q1–Q14 for every entry** after review of fields 6–19 and sections E/F. It is not a claim about unwritten final options, demonstrated empirical grade separation or post-remediation readiness. Final wording can fail these checks and must be reviewed in P3-B/P3-C.

| Design | Q1–Q14 | Extra Senior recognition pass: why generic best-practice recall alone is insufficient |
|---|---|---|
| D01 | YES, 14/14 | Junior: requires two/three local evidence facts. |
| D02 | YES, 14/14 | Middle: dependency capability and actual lifetime constrain execution choice. |
| D03 | YES, 14/14 | Middle: downstream buffering and throughput distinguish viable streaming. |
| D04 | YES, 14/14 | Middle: retry/deadline/admission accounting must be combined. |
| D05 | YES, 14/14 | Middle: full replacement and no-merge policy distinguish contracts. |
| D06 | YES, 14/14 | Middle: storage prohibition differs from revalidation/isolation. |
| D07 | YES, 14/14 | Middle: concrete nonterminal state constrains next action. |
| D08 | YES, 14/14 | Middle: measured fanout/page/cost envelope determines loading. |
| D09 | YES, 14/14 | Middle: atomic writes and slow pure dependency constrain transaction scope. |
| D10 | YES, 14/14 | Middle: optionality and shared pool/recovery budget distinguish policies. |
| D11 | YES, 14/14 | Middle: real enforcement and persisted boundary coverage both required. |
| D12 | YES, 14/14 | Middle: changed execution evidence discriminates hypotheses. |
| D13 | YES, 14/14 | Remote acceptance is uncertain; local cancellation and process recovery do not share ownership lifetime. |
| D14 | YES, 14/14 | IPC, memory, batching and p99 evidence can invalidate the generic “use processes” choice. |
| D15 | YES, 14/14 | Independent waiters, restart and late generations invalidate generic local coalescing. |
| D16 | YES, 14/14 | Several acknowledgements have different authority after worker recovery; a familiar HTTP status alone cannot justify the promise. |
| D17 | YES, 14/14 | Each mixed-version/rollback combination must preserve supplied semantics; “version the API” is insufficient. |
| D18 | YES, 14/14 | Replication lag and partition policy determine enforcement authority; a local precondition check is insufficient. |
| D19 | YES, 14/14 | Route lengths and normalization differ during rollout; a generic trusted-proxy setting is insufficient. |
| D20 | YES, 14/14 | Nonterminal work outlives response retention; changed intent and delayed callbacks affect retirement. |
| D21 | YES, 14/14 | Empty-set concurrency exposes protection that covers individual rows but not the resource invariant. |
| D22 | YES, 14/14 | Old writers, rollback, concurrent backfill and lock budget must all remain valid. |
| D23 | YES, 14/14 | Different terminal commands compete; deduplicating one command does not prove conservation after crash. |
| D24 | YES, 14/14 | Trusted decision expiry, accepted terms and replay cross independent service ownership. |
| D25 | YES, 14/14 | Safe storage is insufficient if forbidden data already crossed ingestion; correlation still must work. |
| D26 | YES, 14/14 | Sampled spans omit competing delay hypotheses; population/cohort evidence limits inference. |
| D27 | YES, 14/14 | Recovery evidence must distinguish unknown effect, duplicate replay and distinct legitimate progress. |

For all 15 Senior designs, difficulty comes from reasoning about the stated system, evidence or failure boundary, never obscurity. Senior BASIC D16/D21/D25 focuses on a foundational system distinction; it does not acquire an ADVANCED requirement to compensate for its grade. The extra pass found no design that reduces to the predecessor's generic recognition task under the required constraints. Human design review and final-option audit remain necessary.

### P3-A verification record

- 27 matrix entries, each with 19 fields: one Junior, 11 Middle, 15 Senior; all original IMPORTANT records covered exactly once.
- 27 version-map rows: 26 v1→v2 and one v2→v3; exact immediate supersedes, including S-A4 v2→v3.
- Six exact MINOR codes excluded; 11 affected buckets reviewed; all five competencies compared across grades.
- Current codes, frozen metadata/categories and old versions verified against actual source and audit. Proposed codes are unique and absent from current source.
- No current prompt/option copied, final answer text/key/index/order published, or executable solution authored. Abstract concepts and unordered distractor families only. Internal positional convention remains in code rather than this documentation.
- Source/engine/tests/existing docs/README/dependencies/CI/Matching/Invitations remain unchanged. All 117 existing tracked baseline files were compared byte-for-byte and match. Only this new document is staged; `git diff --check` and `git diff --cached --check` passed before commit.
- No pytest/linter/build gate run for P3-A: this is explicitly docs-only and adds no code or tests. P3-B/P3-D must run their separately authorized technical gates.

**P3-A DESIGN COMPLETE · 27 IMPORTANT COVERED · 6 MINOR UNCHANGED**

**PRODUCTION BANK UNCHANGED · ASSESSMENT ENGINE UNCHANGED · P3-B NOT STARTED · PR NOT CREATED**

Stop for human design review.
