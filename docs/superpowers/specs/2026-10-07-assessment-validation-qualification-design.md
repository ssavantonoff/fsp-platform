# TASK 3 — Assessment Validation + Verified Qualification

## Status / provenance

Status: DESIGN READY FOR HUMAN REVIEW. Date: 2026-10-07.
This is the authoritative Task #3 design submitted for review, not authorization
to start implementation. No implementation plan is created in Step 2.

- Branch: `feat/assessment-validation-qualification`.
- Reviewed HEAD: `fd4d51f251a3418fa666b1358946266fb85573e3`.
- Current production main: `671ad354658ec9c092b00e6811e6a5a73f66f5af`.
- Approved prework source: `39bd567b11497c7d0121cd1c675d7a3f57068a0e`.
- The three imported prework documents remain unchanged in this step. Their
  `9892400d57b57fe3104d1871fa3513e56e24c4b5` references describe the original audit.

## Problem / Goal

Strengthen evidence, explanation and presentation of the existing assessment
engine: demonstrate the Backend source blueprint, freeze independent scoring
oracles, preserve canonical qualification after unsuccessful retakes, and clearly
separate declared level, current qualification and historical attempt results.
The existing algorithm and domain boundaries remain authoritative.

The source structure and functioning demo do not establish content validity.
Approved human audit: 75 reviewed, 0 BLOCKER, 27 IMPORTANT, 6 MINOR, 42 without
findings. Its NOT_READY recommendation for confirming grades under the reviewed
rubric remains visible; structural validation does not resolve those findings.

## Existing system boundaries / actual code reviewed

| Files | Existing responsibility and design consequence |
|---|---|
| `backend/app/question_bank.py` | `SeedQuestion` is Pydantic input with extra fields forbidden; `load_bank()` parses the source once and performs limited semantic checks. `seed_questions()` enforces immutable content and preserves deliberate inactivity. Extend the loader, preserve the seed writer. |
| `backend/app/services/assessments.py` | Owns competencies, runtime availability, question selection, scoring, deadline, cooldown, locks, finalization and qualification restoration. No rewrite required. |
| `backend/app/models.py` | Existing question/option/attempt entities and CandidateProfile; `consistent_verification` enforces the all-null/all-filled triple. No new entity or fields. |
| `backend/app/assessment_schemas.py`, `backend/app/schemas.py` | Existing start/answer inputs, aggregate attempt responses and CandidateOut. CandidateWrite rejects canonical verification fields. No schema changes. |
| `backend/app/services/profiles.py` | Specialization edits block a live attempt and synchronize qualification from successful history for the new specialization. Preserve this mechanism. |
| `backend/app/routes/assessments.py` | Existing candidate endpoints, role/ownership and trusted-Origin protection. No new routes. |
| `backend/tests/test_assessments.py` | Blueprint, scoring, retakes, restoration, timeout, immutability, privacy, rollback, idempotency and PostgreSQL concurrency coverage. Strengthen existing oracles. |
| `frontend/src/assessment.ts`, `frontend/src/types.ts` | Existing API/types, aggregate data, labels, server clock and late-save protection. Reuse; make date formatting deterministic. |
| `frontend/src/components/assessment-dashboard.tsx` | Availability and current CandidateOut are already loaded; declared/verified fields already exist. Add a small explicit summary. |
| `frontend/src/components/assessment-result.tsx` | Pure renderable result receives AttemptSummary plus optional current CandidateProfile; qualification currently shows only grade. Expand presentation. |
| `frontend/src/components/assessment-history.tsx` | Fetches AttemptSummary[] and handles loading/error/empty; has no current verification. Keep history historical. |
| `frontend/src/components/assessment-attempt.tsx` | Passes `attempt.verification` to AssessmentResult for finished attempts. No modification needed. |
| `frontend/tests/assessment.test.ts` | Node test runner, React static rendering, fetch stubs, clock/API regressions. Existing PASS fixture retains a 25% block and must be corrected. |
| Three `docs/assessment-*-draft.md` / implementation map | Approved methodology, complete human audit and source-based gap map. Finalize later with accurate implementation evidence. |

Also inspected README assessment/check sections, `backend/pyproject.toml`,
`backend/tests/conftest.py`, `frontend/package.json`, existing design-document
conventions and `.github/workflows/checks.yml`. Source JSON metadata confirms
75 records, 73 version 1 and two version 2 replacements with absent historical
predecessors; no question text or answer key is reproduced here.

### Actual API boundary

Under `/candidate/assessments`, preserve GET `/availability`, POST root with
`{target_grade}`, GET `/current`, GET `/history`, GET `/{attempt_id}`, PUT
`/{attempt_id}/answers/{attempt_question_id}` with `{selected_option_id}`, and
POST `/{attempt_id}/submit`.

`AttemptOut` includes current `verification: CandidateOut`, `server_now` and
`questions`; `AvailabilityOut` also includes current verification. Finished detail
has `questions=[]`. `AttemptSummary` used by history has specialization,
target_grade, status, completion_reason, aggregate scores and dates, but no
verification. Viewing an old attempt returns current profile verification, not
a qualification snapshot from when the attempt finished.

There is no unavoidable API or schema gap. Existing endpoints can lazily finalize
expired attempts; preserve this behavior and do not describe every GET as having
no side effects. Submit remains idempotent with result/qualification committed
atomically under existing locks.

## Frozen assessment rules

| Rule | Fixed contract |
|---|---|
| Attempt | 20 questions, 30 minutes, 4 options per question, 1 correct option |
| Grades | JUNIOR / MIDDLE / SENIOR |
| Competencies | PROGRAMMING / HTTP_API / DATABASES / ARCHITECTURE / TESTING_SECURITY_DEBUGGING |
| Attempt per competency | 4 questions: 1 BASIC + 2 APPLIED + 1 ADVANCED |
| Source per grade × competency | 5 questions: 1 BASIC + 3 APPLIED + 1 ADVANCED |
| Source inventory | 75 Backend records, 25 per grade, 15 grade × competency buckets |
| Correct answer | 5 points; overall = correct answers × 5 |
| Competency score | Correct answers in that block × 25; allowed values 0/25/50/75/100 |
| PASS | Overall >=70 AND every one of five competencies >=50 |
| Wrong / unanswered | 0 points; no partial credit, no reduced denominator |

A high overall score cannot compensate for a weak block. Grade/difficulty do not
change point weights. Declared grade does not affect selection, scoring or status.

Selection remains SystemRandom sampling without replacement inside each bucket,
then question/option shuffle; membership and orders are persisted in
AssessmentAttemptQuestion and remain stable on reload. No anti-repeat mechanism
is added. With unchanged source/active pool, BASIC/ADVANCED repeat and two
same-grade attempts share at least 15 questions; all 20 can repeat. These bounds
are specific to that pool, not guaranteed for an arbitrarily changed active DB.

## Structural validator design

### One public function / dependency boundary

Create `backend/app/assessment_validation.py` with this single validation entry:

```python
validate_source_bank(
    questions: Sequence[SeedQuestion],
) -> list[AssessmentValidationFinding]
```

It validates the complete parsed current Backend source inventory. Empty findings
means structurally valid; findings are errors, not human content severities.
The function is pure: no file reads, Session, database queries, writes, scoring,
randomization or content normalization. It never mutates records or their order.

Keep SeedQuestion in `question_bank.py`. Use a TYPE_CHECKING-only import for its
annotation with deferred annotations to avoid the loader→validator→loader import
cycle. Reuse Grade, Difficulty, Specialization from existing models and Backend
competency names from existing `assessments.COMPETENCIES`; do not move or copy the
assessment rules into another domain layer. Validator-local 75/25/1:3:1 counts
describe source structure, distinct from runtime selection's 1:2:1 minima.

### Findings / frozen semantics

`AssessmentValidationFinding` is a small immutable internal value with
`category` (closed enum below), `code: str | None`, and `context: str`.
Context uses fixed templates and allowlisted structural metadata/counts; no
arbitrary object repr, prompt, options or parser input is interpolated.

| Category | Meaning / permitted context |
|---|---|
| INVALID_TOTAL | Source length differs from 75; expected/actual count |
| INVALID_GRADE_COUNT | Known grade count differs from 25; grade and counts |
| INVALID_BUCKET_COUNT | Any expected grade × competency difficulty count differs from 1/3/1; bucket, difficulty and counts; total must be 5 |
| BLANK_CODE | Code empty after strip; no content echoed |
| DUPLICATE_CODE | Same exact source code appears more than once |
| BLANK_PROMPT | Prompt empty after strip; code only |
| INVALID_OPTIONS | Not exactly four options or any option empty after strip; code and generic reason, no option text/position |
| DUPLICATE_OPTION | Two options equivalent under whitespace comparison; code only |
| INVALID_GRADE | Grade not a valid existing Grade |
| INVALID_DIFFICULTY | Difficulty not a valid existing Difficulty |
| INVALID_COMPETENCY | Not one of the five Backend competencies; code, no arbitrary invalid value |
| INVALID_VERSION | Not an integer >=1 |
| INVALID_SUPERSEDES | Blank non-null predecessor, self-reference or conflicting replacement ownership; question/predecessor codes and generic reason only |
| SUPERSEDES_CYCLE | Cycle among current source records; codes, no content |

Return findings in deterministic inventory/category and source traversal order;
traverse grades, competencies and difficulties in their existing fixed order.
Accumulate independent issues instead of crashing on invalid metadata. Do not
include invalid values in expected bucket counters. Skip ambiguous duplicate-code
nodes when checking graph edges; DUPLICATE_CODE already rejects that inventory.

#### Record / identity checks

- Code must be nonblank after strip, with exact-code uniqueness as in the existing
  loader. Strip is for checking only; no stored code is rewritten.
- Prompt must be nonblank after strip, without rewriting stored text.
- Options must be exactly four, each nonblank. Compare with
  `" ".join(option.split())`: collapse whitespace only, preserving case,
  punctuation and words. Reject comparison duplicates; do not rewrite options.
- Grade/difficulty use current enums, competency the Backend set, version >=1.
  Pydantic already enforces grade/difficulty/version/option count during parsing;
  the validator may defensively diagnose these for model-constructed test inputs.
  That does not authorize bypassing parsing in production.
- Codes conventionally contain a version suffix, but no current parser contract
  requires a naming regex or defines how arbitrary codes map to metadata. Freeze
  nonblank/unique code and valid numeric version only; do not invent a suffix,
  grade-prefix or competency-prefix restriction from examples.
- Backend specialization is implicit in source file and seed boundary; no JSON
  specialization field is added. Four source options map to exactly one marked
  correct option through the existing seed convention, which remains unchanged.
  Validator diagnostics never disclose that convention's position or key.

#### Supersedes graph

Build replacement→predecessor edges from explicit non-null supersedes. Reject
self-reference, cycles among present nodes and two current records claiming the
same predecessor, including when that predecessor is absent from current JSON.
A historical predecessor missing from source is allowed: it terminates traversal.
Do not require all predecessors in the JSON, query live DB, delete history or
invent ordering/version rules for external predecessor codes.

Real version 2 replacements must pass. Inactive historical DB rows are outside
the validator's scope. No classifier for distractors, ambiguity, difficulty,
trade-offs, near duplicates or psychometric quality is added.

### Minimal integration / safe failures

`load_bank()` continues to read/parse JSON once using existing SeedQuestion
validation, then calls validate_source_bank on the full parsed list. It returns
that unchanged list only when findings are empty. Existing semantic code/options/
competency loops are consolidated into this validator, not kept as a parallel
check implementation. No selection/scoring calls use the source validator.

If structural findings exist, loader raises ValueError containing only the safe
categories/codes/contexts. JSON/Pydantic parsing failures raise a fixed safe
ValueError (e.g. `Invalid assessment source format`) with raw exception chaining
suppressed; do not stringify ValidationError, input arrays, option positions or
source lines. A non-list JSON root is also a safe source-format failure before
record parsing. Parsing stays in the existing loader; no second parser/API error
schema is created. Diagnostic serialization itself must be covered for leakage.

`seed_questions()` continues to reject content changes to a published code,
preserve deliberate `is_active=False`, and deactivate an existing predecessor
without deleting it. Source validation makes no claim that live DB has exactly
75 physical AssessmentQuestion rows: inactive predecessors may remain. Runtime
availability still uses active DB questions and existing blueprint minima.
Historical attempts retain their links and results.

## Golden scoring cases — literal independent oracles

Order for all vectors: PROGRAMMING, HTTP_API, DATABASES, ARCHITECTURE,
TESTING_SECURITY_DEBUGGING. Each block has four questions. These are product
oracles, not generated expected values from production scoring.

| Case | Correct /20 | Correct per block | Literal competency scores | Overall | Status | Explanation |
|---|---:|---|---|---:|---|---|
| G1 | 14 | 3 / 3 / 3 / 3 / 2 | 75 / 75 / 75 / 75 / 50 | 70 | PASSED | Both conditions met, including boundaries |
| G2 | 16 | 4 / 4 / 1 / 4 / 3 | 100 / 100 / 25 / 100 / 75 | 80 | FAILED | Competency threshold fails |
| G3 | 13 | 3 / 3 / 3 / 2 / 2 | 75 / 75 / 75 / 50 / 50 | 65 | FAILED | Overall threshold fails |
| G4 | 20 | 4 / 4 / 4 / 4 / 4 | 100 / 100 / 100 / 100 / 100 | 100 | PASSED | All correct |
| G5 | 0 | 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 | 0 | FAILED | Neither condition met |

Strengthen `test_scoring_and_initial_verification` with G1–G5 case IDs and full
literal expected dictionaries keyed by those five names. Replace expected
`count * 25` assertions; do not duplicate the five scenarios in a second scoring
suite or introduce an expected-score helper. Existing answer_counts may prepare
chosen correct answers from the test DB, but it cannot calculate expectations.

## Canonical qualification semantics

Current qualification is exclusively CandidateProfile.specialization plus
verified_grade / normalized_assessment_score / assessment_verified_at. All three
canonical fields are either null or non-null. Declared grade is self-reported and
separate; it is never inferred from scores, nor used to choose specialization.
No VerifiedQualification entity, profile field, persistent snapshot or frontend
storage copy is created. No expiration policy is added.

After success, existing synchronize_verification chooses highest successful
grade in the current specialization, then latest successful finished_at at that
grade. A same-grade successful retake replaces canonical score/date with the new
successful result even when its score is lower; no highest-score rule. Failed
same-grade or higher-grade retakes preserve all canonical fields and specialization.

Critical demonstration: successful Backend/Middle with the passing vector
`4 / 3 / 3 / 3 / 3` yields literal overall 80 and blocks
`100 / 75 / 75 / 75 / 75` at T1. A later Backend/Senior G3 attempt finishes FAILED
with 65 at T2. Current qualification must remain Backend/Middle/80/T1, while
Senior/FAILED/65/T2 remains in history. Senior failure neither upgrades nor
downgrades qualification, and does not replace score/date. Keep this scenario
coherent in backend, frontend and manual acceptance fixtures.

On specialization change, restore highest/latest successful qualification for
the new specialization or clear all three fields. The current specialization
always comes from CandidateProfile. Active nonexpired attempts still prevent a
switch; expired attempts finalize under existing rules before restoration.
Returning to Backend restores its history-derived qualification.

Cooldown remains specialization/target-grade scoped: FAILED 7 days, PASSED
90 days from finished_at. Exact boundary permits a new attempt; a different
higher grade has independent cooldown, lower-than-verified grades remain blocked.
TIMEOUT finished_at equals expires_at even when discovered later; timeout can
PASS. Do not change these semantics or server finalization.

## Frontend semantics

Reuse RoleGate, api, Feedback, existing labels, responsive card/dl/score-row styles
and data already loaded. No new fetch, store or UI framework is needed.

### Dashboard

Keep declared grade under `Заявленный уровень`, separately from the summary
heading `Текущая подтверждённая квалификация`. Summary shows profile specialization,
verified grade, `Оценка подтверждения` (/100), `Дата подтверждения`.
For all-null canonical triple show `Подтверждённой квалификации пока нет.`
Never substitute selected target grade or a latest attempt. Keep availability
cards, explicit start and existing loading/profile-missing/error/disabled flows.

### Finished result

Heading `Результат попытки`, with attempt specialization, target grade, literal
server PASSED/FAILED, overall /100, `Дата завершения попытки` from finished_at,
five competency scores and TIMEOUT notice if applicable. Wording for historical
success describes this attempt passing, not a current-level promotion.

Show both explanatory conditions for every finished attempt:

- `Общий балл >=70`: `Выполнено` / `Не выполнено`.
- `Каждая компетенция >=50`: `Выполнено` / `Не выполнено`.

Derive these labels from returned aggregate numbers only; status stays the server
status even if fixture/server data is inconsistent. Missing aggregate data or
missing expected competency keys cannot satisfy a condition by an empty every().
Do not recompute authoritative status, canonical score or qualification. Do not
display answer/options/solutions or create a finished question review.

A separate `Текущая подтверждённая квалификация` block uses only
`attempt.verification` (passed through the existing verification prop), with the
same four fields/unverified copy as dashboard. It may have another grade or
specialization than the attempt. For FAILED Senior with current Middle/80/T1,
both meanings and their independent scores/dates are visible simultaneously.
Retain the optional render prop contract; absent verification is unavailable
data, not proof of a null canonical triple. Do not derive qualification from the
attempt or assert an unverified profile when that prop was omitted.

### History

Keep history endpoint and its loading/error/retry/empty behavior. Add exact copy:
`История попыток не заменяет текущую подтверждённую квалификацию.`
Each row explicitly says `Попытка`, displays its specialization/target grade,
status, score, start/completion dates, competency scores and existing completion
reason. IN_PROGRESS remains distinct from a finished result. History stays pure:
no fabricated qualification or additional profile fetch. Detail pages show
current verification using the existing detail response.

### Dates

Reuse existing ISO dates, but change dateLabel in `frontend/src/assessment.ts`
to explicit `ru-RU` formatting with `timeZone: "UTC"`, 24-hour time and consistent
day/month/year/hour/minute/second fields plus visible `UTC`. Preserve null → `—`.
The current toLocaleString call implicitly uses the host timezone, so this small
helper change is necessary for deterministic presentation/tests; it applies
consistently to assessment date consumers and does not change instants or timers.

Labels distinguish finished_at (attempt completion), assessment_verified_at
(current qualification confirmation), and available_at (cooldown boundary for
that specialization/grade). Label the latter as a next retake not before that
time; it is not a guarantee of availability when other existing gates fail.

### Minimal render test seams

Within the existing three component files, reuse one exported pure current
qualification view from assessment-result for result and dashboard. Expose a
small pure dashboard summary and history list view where needed for static
render assertions. Keep API loading/hooks/orchestration in their existing
components and files; this is limited presentation reuse, not a second state
layer or page rewrite. No new component file or dependency is proposed.

## Testing strategy — future implementation only

### Structural tests: `backend/tests/test_assessment_validation.py`

Freeze named cases below (names describe individual obligations). Reuse the real
parsed bank for a passing integration and mutate copies for count-specific
negatives. Small synthetic lists suffice for graph/text negatives, asserting the
relevant category even if their inventory is deliberately incomplete. Do not
copy 75 question texts into fixtures or suppress unrelated findings globally.

| Proposed test | Required assertion |
|---|---|
| test_real_source_bank_passes | Real loader succeeds and validate_source_bank returns [] |
| test_wrong_total_rejected | INVALID_TOTAL |
| test_wrong_grade_count_rejected | INVALID_GRADE_COUNT with total kept 75 |
| test_wrong_bucket_difficulty_mix_rejected | INVALID_BUCKET_COUNT with grade total kept 25 |
| test_blank_trimmed_code_rejected | BLANK_CODE |
| test_duplicate_code_rejected | DUPLICATE_CODE |
| test_blank_trimmed_prompt_rejected | BLANK_PROMPT |
| test_wrong_option_count_rejected | INVALID_OPTIONS; parser also rejects raw malformed input |
| test_blank_option_rejected | INVALID_OPTIONS |
| test_whitespace_equivalent_options_rejected | DUPLICATE_OPTION; whitespace-only comparison, no mutation |
| test_invalid_competency_rejected | INVALID_COMPETENCY |
| test_invalid_grade_rejected | Invalid grade safely rejected by parser or defensive INVALID_GRADE finding |
| test_invalid_difficulty_rejected | Invalid difficulty safely rejected by parser or defensive INVALID_DIFFICULTY finding |
| test_invalid_version_rejected | Invalid version safely rejected by parser or defensive INVALID_VERSION finding |
| test_supersedes_self_reference_rejected | INVALID_SUPERSEDES |
| test_supersedes_cycle_rejected | SUPERSEDES_CYCLE for two-node and longer cycles |
| test_duplicate_predecessor_claim_rejected | INVALID_SUPERSEDES, including absent predecessor |
| test_missing_historical_predecessor_allowed | No graph finding; real replacements remain valid |
| test_blank_supersedes_rejected | INVALID_SUPERSEDES |
| test_diagnostics_do_not_expose_answers | Findings, serialized ValueError and parse failures contain no sentinel option/answer/solution text, key or option index |
| test_validation_is_deterministic_and_nonmutating | Repeat findings equal; content/options/order unchanged |

Raw invalid enums/version/option counts use the existing Pydantic boundary.
Defensive validator cases may use SeedQuestion.model_construct/model_copy only
inside tests. Exercise loader integration without duplicating parsing or adding
DB dependency to these tests. Keep existing seed immutability/inactivity tests.

### Scoring / qualification: `backend/tests/test_assessments.py`

- Literal G1–G5 overall/status/full competency dictionaries; assert exactly five
  named keys and every value in {0,25,50,75,100}.
- Strengthen existing failed-higher-grade test or add one focused regression
  using Middle/80/T1 then Senior/G3: compare specialization and all three
  canonical fields in submit, profile, availability and subsequent detail;
  history retains the Senior FAILED attempt and its own aggregates.
- Failed same-grade preserves canonical triple; successful lower-score retake
  updates score/date; existing specialization restoration remains covered.
- Parameterize declared JUNIOR/MIDDLE/SENIOR with the same fixed target grade
  and coherent answer vector; literal score/status/block expectations identical.
  Use isolated fixtures, not sleeps or bypassing cooldown via UI state.
- Explicit wrong-option and unanswered cases give zero, including mixed wrong/
  missing selections; selected correct answer overwritten by a wrong one no
  longer contributes. Prepare selections only in tests and exercise server finish.
- Keep privacy, blueprint, cooldown/deadline boundaries, stable reload,
  ownership, atomic rollback, idempotent submit and PostgreSQL concurrency tests.

Do not change services/assessments.py unless a separate actual bug is proven and
reviewed; none was found in this design review. Tests strengthen working logic.

### Frontend: `frontend/tests/assessment.test.ts`

Use existing node:test/assert, React renderToStaticMarkup and fetch stubs. No new
test framework, DOM emulation or dependencies. Required assertions:

1. Coherent G4 PASS, five 100s, overall 100: server PASSED, both conditions met,
   completion date visible. Replace the current contradictory PASS fixture.
2. G2 FAILED, overall 80 and block 25: overall met, competency condition unmet.
3. G3 FAILED, overall 65 and all blocks >=50: overall unmet, competency met.
4. Senior/G3 FAILED at T2 with current Backend/Middle/80/T1: separate headings,
   specialization/grades/scores/dates, canonical fields displayed unchanged.
5. Dashboard declared Senior versus verified Middle are under separate labels.
6. Canonical all-null profile gives explicit unverified copy; missing verification
   prop is not treated as such a profile.
7. History row/copy explicitly refers to attempts; old PASSED Middle does not
   claim current qualification, even when a separately viewed detail is now Senior.
8. Finished result renders no answer/options/solution text even with sentinel
   properties in an adversarial render fixture; backend still returns questions=[].
9. Explicit UTC date formatting and distinct completion/verification/retake labels;
   contradictory status/aggregate fixture cannot cause UI status rewriting, and
   empty competency aggregates cannot produce an all-blocks success label.

Render the small pure views above for dashboard/history coverage. Existing
autosave, clock, API, retry and availability tests remain. Loading/retry/navigation
with actual hooks and mobile layout are covered by browser smoke, not claimed
from static markup alone.

### Manual browser acceptance / full gate

In an isolated test environment use coherent server-created Middle/80/T1, then
Senior/G3 FAIL; verify dashboard, result and history show preserved qualification
and separate attempt. Also inspect G4/G2/G3 condition explanations, an all-null
profile, an old Middle PASS detail while current qualification is higher or in
another specialization, TIMEOUT, next-retake labels, history empty/loading/error
retry and width 375px. No production question content edits or answer-key display.

Future implementation gate uses existing tools: backend targeted tests and full
PostgreSQL pytest suite, ruff check/format check, mypy app, Alembic check with
unchanged schema; frontend targeted assessment tests, npm test, lint, typecheck,
build; existing Docker build/health/idempotent seed smoke and all CI jobs, including
existing Matching regression/seed checks without changing their implementation.
Use repository test schemas; do not run destructive checks on application data.
Record exact results and any unavailable external check. Step 2 runs no tests.

## Documentation strategy

Finalize the same three imported documents during future implementation, retain
their paths and original audit provenance; do not invent evidence before checks:

- Methodology: purpose/scope, blueprint, scoring and both thresholds, grade and
  relative difficulty interpretation, repeats/randomization, canonical versus
  attempts, retakes/cooldowns, G1–G5 and limitations. Replace illustrative 82
  demonstration with coherent backend-generated 80 where appropriate; no claim
  that different-grade scores measure an equivalent absolute quantity.
- Audit: keep all 75 reviewed, 0/27/6/42 facts and all human findings, safe codes/
  reasons, NOT_READY rationale and separate future versioned-remediation need.
  Add structural evidence separately; do not relabel IMPORTANT findings resolved.
- Implementation map: finalize as technical validation/evidence note stating
  completed boundaries, tested commits/checks, browser evidence and remaining
  limitations. Distinguish original source observations from actual runtime work.

Permitted claims after successful implementation: technically functioning,
structurally validated, deterministic under documented rubric, verified platform
qualification under platform rules. No psychometric validity, scientific grade
calibration, industry certification, hiring probability, universal objective
developer grade or cross-grade score equivalence claim. Content audit remains
human review; no pilot/calibration/reliability study is implied.

## File map — future implementation

| Action | File | Purpose |
|---|---|---|
| CREATE | `backend/app/assessment_validation.py` | Pure structural validator and safe findings |
| CREATE | `backend/tests/test_assessment_validation.py` | Source/negative/graph/privacy regressions |
| MODIFY | `backend/app/question_bank.py` | One post-parsing integration and safe errors |
| MODIFY | `backend/tests/test_assessments.py` | Literal G1–G5 and qualification/declared/wrong-answer assertions |
| MODIFY | `frontend/src/components/assessment-dashboard.tsx` | Declared/current summary separation |
| MODIFY | `frontend/src/components/assessment-result.tsx` | Attempt/conditions/current qualification presentation and reused pure view |
| MODIFY | `frontend/src/components/assessment-history.tsx` | Explicit historical copy and testable row rendering |
| MODIFY | `frontend/tests/assessment.test.ts` | Coherent rendering/date/privacy regressions |
| MODIFY | `frontend/src/assessment.ts` | Explicit UTC dateLabel; current helper lacks deterministic timezone |
| MODIFY | `docs/assessment-methodology-draft.md` | Final methodology/limitations |
| MODIFY | `docs/assessment-bank-audit-draft.md` | Retained audit plus structural evidence |
| MODIFY | `docs/assessment-task3-implementation-map.md` | Final implementation/check evidence |

No globals.css change is planned: existing card/dl/score-row/responsive classes
suffice. No new source file beyond the two backend files is needed for render seams.

Do not touch models.py, schemas.py, assessment_schemas.py, services/assessments.py,
services/profiles.py, assessment-attempt.tsx, routes, migrations, question JSON,
Matching/Need implementation, README, CI, dependency/package files or frozen
holdout data. Any proven bug or unavoidable API/schema deviation requires STOP
and separate review, not automatic scope expansion.

## Non-goals

- New assessment algorithm, weights, thresholds, selection or timer behavior.
- New specialization banks, inference, progression or cooldown policy.
- Question remediation or distractor edits, even for the 27 IMPORTANT findings.
- Psychometric/content classifier, pilot calibration or certification claims.
- New qualification persistence/store, best-ever-score policy or history rewrite.
- New endpoints/schema/migration, whole-page redesign or test framework.
- Matching tuning, holdout evaluation, Need changes, deployment or PR creation.

## Security / privacy considerations

Validator findings/errors/logs/docs contain structural metadata only, never
correct option text/position/index, key or solution explanations. Source parser
errors must not leak raw source arrays through exception text/chaining. Finished
UI uses aggregate results only, ignoring any injected question-review data.
Retain existing candidate ownership, session, Origin and role controls. Canonical
fields remain server-owned; UI labels cannot mutate profile or attempt status.
No new frontend storage snapshots or additional personal-data endpoints.

## Definition of Done — future implementation

- Real 75-record source passes exact per-grade/per-bucket structural validation.
- Malformed source fixtures fail safely; graph handles absent historical targets.
- Findings and parse errors leak no answer data; content/seed history unchanged.
- G1–G5 literal regression cases pass with exactly five competency keys.
- Failed Senior preserves Middle grade/score/date/specialization, visible beside
  the failed attempt; same-grade and specialization behavior unchanged.
- Existing scoring, selection, cooldown, timeout, transaction and privacy behavior
  retained and existing regressions pass.
- Dashboard separates declared/current verified; result separates attempt/current
  verified and explains both conditions; history clearly remains historical.
- Dates use explicit consistent UTC labels and retain their separate meanings.
- No schema/API/migration/qualification-state additions or question content edits.
- Full PostgreSQL backend suite/static checks, frontend tests/lint/typecheck/build,
  Docker/CI regressions and stated browser acceptance pass.
- Docs preserve audit findings and accurately state limitations without unsupported
  psychometric/grade/hiring claims.

## Implementation sequencing

After human architecture/specification approval, prepare a separate reviewed
implementation plan. Then add validator and source integration with structural
tests; strengthen scoring/qualification regressions; make limited presentation/
date changes with coherent render tests; execute browser and full existing gates;
finalize documentation with evidence and submit for human review. This is the
high-level dependency order only, not an implementation plan created in Step 2.
No production implementation begins under this commit.

## Self-review against current code

| Question | Answer |
|---|---|
| DB migration required? | No |
| API change required? | No |
| Scoring altered? | No |
| Cooldown altered? | No |
| Question selection altered? | No |
| Question content edited? | No |
| Matching affected/modified? | No; existing regression checks only |
| Second qualification state added? | No |

Step 2 diff must contain exactly this new spec. Existing three prework documents,
production code, tests and question JSON remain byte-equivalent to reviewed HEAD.
Commit: `docs: define assessment validation and qualification design`.
Push only to `feat/assessment-validation-qualification`; no PR, plan or implementation.
