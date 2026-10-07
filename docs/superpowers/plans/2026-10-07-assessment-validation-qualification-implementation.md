# TASK 3 — Assessment Validation + Verified Qualification Implementation Plan

## Context / authorization

Status: PLAN READY FOR HUMAN REVIEW. Date: 2026-10-07.
Step 3 adds this checklist only; every unchecked item below is future work.
Production implementation, tests and existing documentation are unchanged.
Execution requires a subsequent task authorization. Do not automatically proceed
past a task's commit/push/review boundary.

- Branch: `feat/assessment-validation-qualification`.
- Base main: `671ad354658ec9c092b00e6811e6a5a73f66f5af`.
- Planning HEAD/local remote: `253a0724d40271e0890f7b9ba85d80be2cf694dc`.
- Authoritative approved design:
  [2026-10-07-assessment-validation-qualification-design.md](../specs/2026-10-07-assessment-validation-qualification-design.md).
- Approved prework source: `39bd567b11497c7d0121cd1c675d7a3f57068a0e`.

The assessment engine already exists. This work strengthens validation, evidence
and presentation; it does not implement another engine. The complete design and
all eight required implementation/test files were re-opened during planning.
Their behavior matches the reviewed design; the only change since its reviewed
implementation baseline is the design document itself.

## Frozen constraints

- 20 questions, 30 minutes, four options and one correct option per question.
- Backend competencies, in order: PROGRAMMING, HTTP_API, DATABASES, ARCHITECTURE,
  TESTING_SECURITY_DEBUGGING. Grades JUNIOR / MIDDLE / SENIOR.
- Source: 75 records, 25 per grade, each grade × competency has
  1 BASIC / 3 APPLIED / 1 ADVANCED. Attempt: 1 / 2 / 1, four per competency.
- Correct = 5 points; wrong/unanswered = 0, no partial points. Overall >=70 AND
  every competency >=50 required for PASS. No compensation between blocks.
- Existing SystemRandom selection/shuffle, saved membership/order and server
  timeout remain. No new repeat prevention, changed denominator or weighting.
- Cooldown: failed 7 days, passed 90 days for specialization/grade; lower verified
  grade restrictions and independent higher-grade cooldown remain unchanged.
- Current qualification comes only from CandidateProfile's current specialization
  and canonical triple: verified_grade, normalized_assessment_score,
  assessment_verified_at; all three null or all three filled.
- Failed higher/same grade preserves canonical state; successful same-grade retake
  replaces score/date even if lower. Specialization restores highest successful
  grade/latest success at that grade. No highest-score-wins policy.
- No question content, Matching, Need, migration, API/schema or dependency changes.
- Audit remains 75 reviewed / 0 BLOCKER / 27 IMPORTANT / 6 MINOR / 42 clean and
  NOT_READY under the reviewed content rubric. No psychometric claims.

## File ownership / dependencies

| Task | Sole change ownership |
|---|---|
| 1 | CREATE `backend/app/assessment_validation.py`, `backend/tests/test_assessment_validation.py` |
| 2 | MODIFY `backend/app/question_bank.py`; extend `backend/tests/test_assessment_validation.py` |
| 3 | MODIFY `backend/tests/test_assessments.py` for golden/zero/declared regressions |
| 4 | MODIFY `backend/tests/test_assessments.py` for qualification/retake/restoration regressions |
| 5 | MODIFY `frontend/src/assessment.ts` dateLabel only; `frontend/tests/assessment.test.ts` date tests |
| 6 | MODIFY dashboard/result component files and `frontend/tests/assessment.test.ts` |
| 7 | MODIFY history component file and `frontend/tests/assessment.test.ts` |
| 8 | MODIFY only the three existing assessment prework documents |
| 9 | Verification only; no feature file changes or test-results-only commit |

Use Tasks 1→2→3→4→5→6→7→8→9, with human review after each committed task.
Task 1 precedes loader integration; Task 2 precedes claims of enforced source
validation. Tasks 3/4 follow integration and cannot change scoring. Task 5 precedes
UI date assertions. Task 6 precedes Task 7 where presentation/test conventions are
shared. Task 8 requires actual code/test evidence; Task 9 is the final gate.
No parallel work may edit shared files without explicit ownership coordination;
in particular Tasks 3/4 and Tasks 5/6/7 are sequential. This plan does not request
subagents or autonomous parallel execution.

## Execution / command conventions

Backend commands below run from `backend/` with the existing Python 3.13+ virtual
environment activated and existing requirements-dev installed. Frontend commands
run from `frontend/` with Node 22+; Git/Compose commands run from repository root.
Do not add packages. If local runtime is unavailable, use the existing backend
container with the same commands rather than changing dependencies.

Default pytest uses migrated temporary SQLite DBs when TEST_DATABASE_URL is
unset. PostgreSQL tests use existing conftest's temporary `fsp_test_*` schemas;
the test account needs CREATE SCHEMA. No production DB or application data is used.
For PostgreSQL commands below, TASK3_TEST_DATABASE_URL must be configured to an
isolated local PostgreSQL 17 test database; never print credentials. Do not
attribute PostgreSQL lock coverage to SQLite or report skipped checks as passing.

For each future task: write focused assertions, observe the intended failure when
applicable, implement the minimum approved behavior, then run the stated checks.
Do not weaken assertions to make implementation pass. Inspect the full diff,
stage only that task's explicit files, run `git diff --cached --check`, commit
with its message, then `git push origin feat/assessment-validation-qualification`.
Check `git rev-parse HEAD`, `git ls-remote origin
refs/heads/feat/assessment-validation-qualification`, and `git status`.
Report exact local/remote SHA, commands/results, changed files and limits; STOP
for human review. Do not create PR or merge from an intermediate task.

If expected branch/SHA/tree or design assumptions differ on resumption, STOP and
report rather than rebasing or resolving product/architecture changes silently.
The reviewed design/plan and unrelated files remain unchanged during these task
commits unless a later instruction explicitly authorizes updating them.

## TASK 1 — Structural validator core

**Files:** CREATE `backend/app/assessment_validation.py` and
`backend/tests/test_assessment_validation.py`. Do not modify question_bank.py yet.

### Core checklist

- [ ] Add deferred annotations, Sequence typing and TYPE_CHECKING-only SeedQuestion
  import from question_bank. Reuse current Grade/Difficulty/Specialization and
  Backend COMPETENCIES; do not move them out of the existing assessment service.
- [ ] Define `AssessmentValidationCategory` closed enum and immutable
  `AssessmentValidationFinding` with category, code (optional) and context.
  Categories exactly: INVALID_TOTAL, INVALID_GRADE_COUNT, INVALID_BUCKET_COUNT,
  BLANK_CODE, DUPLICATE_CODE, BLANK_PROMPT, INVALID_OPTIONS, DUPLICATE_OPTION,
  INVALID_GRADE, INVALID_DIFFICULTY, INVALID_COMPETENCY, INVALID_VERSION,
  INVALID_SUPERSEDES, SUPERSEDES_CYCLE.
- [ ] Implement the sole public validator:
  `validate_source_bank(questions: Sequence[SeedQuestion]) -> list[AssessmentValidationFinding]`.
  Return [] on success; no Session, DB access, source read, scoring or mutation.
- [ ] Check total75/grade25 and all 15 expected source buckets for exact BASIC1,
  APPLIED3, ADVANCED1 (five total). Iterate known grades/competencies/difficulties
  deterministically; invalid metadata is rejected and excluded from counters.
- [ ] Check blank-after-strip code/prompt, exact-code duplicates, exactly four
  nonblank options. Compare options using `" ".join(option.split())`, preserving
  case/punctuation and stored text. Version is integer >=1; metadata uses existing
  enums and Backend competency names. No new specialization field or naming regex.
- [ ] Build code→predecessor edges, rejecting blank supersedes, self-reference,
  cycles and two current replacements owning one predecessor. Missing historical
  nodes terminate traversal and are allowed. Skip ambiguous duplicate-code graph
  nodes already diagnosed; never query DB history.
- [ ] Emit deterministic findings using fixed safe context templates and codes/
  known metadata/counts only. No prompt/options/object repr, answer key, correct
  index, option position or solution enters findings. Input objects/order unchanged.

### Core test checklist

Use a test fixture that calls existing load_bank() for real parsed source once
per fixture, with deep model copies before mutation. Tests may read the bank;
the validator itself cannot. Small incomplete synthetic lists may assert a
specific graph/text category without pretending total-count validity. Use
model_construct/model_copy only for defensive invalid parsed-record tests.

- [ ] `test_real_source_bank_passes`: real 75 records return [].
- [ ] `test_wrong_total_rejected`: remove a record → INVALID_TOTAL.
- [ ] `test_wrong_grade_count_rejected`: change one valid grade while total stays75.
- [ ] `test_wrong_bucket_difficulty_mix_rejected`: change APPLIED to BASIC with
  grade count still25 → INVALID_BUCKET_COUNT.
- [ ] Blank trimmed code, exact duplicate code, blank trimmed prompt, wrong option
  count, blank option, whitespace-equivalent options each get dedicated tests.
- [ ] Invalid competency, grade, difficulty and version (0/negative) each get
  dedicated tests for their approved category; raw parser checks remain for Task2.
- [ ] Self-reference, two-node/longer cycle, shared predecessor including absent
  predecessor, blank supersedes each get dedicated tests. Absent historical
  predecessor produces no graph error; real v2 replacements pass.
- [ ] `test_diagnostics_do_not_expose_answers`: use sentinel options/solution-like
  content, inspect every finding including context/representation, assert no
  option text/key/index leaks. Loader error serialization belongs to Task2.
- [ ] `test_validation_is_deterministic_and_nonmutating`: equal repeat findings;
  source fields, options and order byte/content-equivalent before/after.

### TASK 1 Verification / commit boundary

```sh
python -m pytest -q tests/test_assessment_validation.py
python -m ruff check app/assessment_validation.py tests/test_assessment_validation.py
python -m ruff format --check app/assessment_validation.py tests/test_assessment_validation.py
python -m mypy app
```

- [ ] No full suite required here unless targeted failures justify it.
- [ ] Confirm exactly the two new files, with no loader change.
- [ ] Commit `feat: add assessment source bank validator`; push, report, STOP.

## TASK 2 — Integrate validator into source loader

**Files:** MODIFY `backend/app/question_bank.py` and, for integration tests,
`backend/tests/test_assessment_validation.py`. Dependencies: approved Task1.

### Loader / integration checklist

- [ ] Modify load_bank only: read source once, json.loads once, reject non-list
  root safely, parse every record through existing SeedQuestion.model_validate.
  Keep SeedQuestion schema/content semantics unchanged; no duplicate parser.
- [ ] After full parsing call validate_source_bank once. Return the parsed list
  unchanged on no findings. Remove superseded duplicate/options/competency loops.
- [ ] Serialize only finding category/code/safe context in a ValueError. A small
  private formatting helper in question_bank is acceptable only if needed to
  keep safe serialization clear; no extra module or public exception hierarchy.
- [ ] JSON/Pydantic/root failures become fixed `Invalid assessment source format`
  ValueError with raw cause chaining suppressed. Do not stringify raw parse
  exceptions, source lines, error inputs or option indices.
- [ ] Leave seed_questions body/algorithm unchanged: immutable existing content,
  deliberate inactivity, predecessor deactivation and historical links retained.
  Never require live DB to have75 physical rows. Runtime active-bank logic stays
  in services/assessments unchanged.

### Integration tests / invariants

- [ ] Real load returns75 records and both v2 replacements succeed with missing
  historical predecessors; no question metadata/content mutation.
- [ ] Use pytest tmp_path and scoped module __file__ substitution to point the
  existing loader at temporary content/backend_questions.json. No new production
  path/config injection; never alter repository source JSON.
- [ ] Test invalid JSON, non-list roots and raw invalid SeedQuestion inputs
  (enums/version/options). Include sentinel answer/option text in malformed data;
  fixed exception text and formatted exception chain must not expose it.
- [ ] Test parsed but structurally invalid total/buckets/duplicates/options and
  graph → safe structural ValueError. Verify category present and no answer text,
  index, key or explanation exposed. Test valid list/order returned unchanged.
- [ ] Run existing test_bank_integrity_and_immutable_seed and infrastructure seed
  idempotency/rollback tests. No assertion that every live DB always has75 rows.

### TASK 2 Verification / commit boundary

```sh
python -m pytest -q tests/test_assessment_validation.py
python -m pytest -q tests/test_assessments.py -k bank_integrity_and_immutable_seed
python -m pytest -q tests/test_infrastructure.py -k seed
python -m ruff check app/question_bank.py app/assessment_validation.py tests/test_assessment_validation.py
python -m ruff format --check app/question_bank.py app/assessment_validation.py tests/test_assessment_validation.py
python -m mypy app
```

- [ ] Confirm source JSON and seed writer/service algorithms unchanged.
- [ ] Commit `feat: validate assessment source bank on load`; push, report, STOP.

## TASK 3 — Freeze scoring golden cases

**File:** MODIFY `backend/tests/test_assessments.py` only. Dependencies: Task2.
No production assessment-service changes are authorized.

### Literal regression checklist

- [ ] Strengthen existing test_scoring_and_initial_verification; parameterize
  counts, literal overall, literal status and literal full expected dictionary,
  with G1–G5 IDs. Do not add a second scoring suite/helper computing expectations.
- [ ] Use this frozen table in Backend competency order from constraints:

| Case | Correct counts | Literal scores | Overall | Status |
|---|---|---|---:|---|
| G1 | 3/3/3/3/2 | 75/75/75/75/50 | 70 | PASSED |
| G2 | 4/4/1/4/3 | 100/100/25/100/75 | 80 | FAILED |
| G3 | 3/3/3/2/2 | 75/75/75/50/50 | 65 | FAILED |
| G4 | 4/4/4/4/4 | 100/100/100/100/100 | 100 | PASSED |
| G5 | 0/0/0/0/0 | 0/0/0/0/0 | 0 | FAILED |

- [ ] Write all five named competency keys/values literally in each expected
  dictionary. Remove `count * 25` expected-value assertions; do not generate
  dictionaries from counts or call finalize to produce an oracle.
- [ ] Keep answer_counts as arrangement only, then exercise start/finish and
  existing profile checks. Assert exact five-key set and values in {0,25,50,75,100}.
- [ ] Add `test_wrong_and_unanswered_score_zero`, covering all-wrong,
  all-unanswered and a mixed vector with literal zero expectations. For overwriting
  a correct selection with wrong, use a literal one-correct-before/zero-after
  setup or isolated attempts, no recalculated expected-score helper.
- [ ] Add `test_declared_grade_does_not_affect_result` parameterized across
  JUNIOR/MIDDLE/SENIOR declared grade, fixed Backend/Middle target and G1 answers;
  literal70/PASSED/five block expectations in isolated per-case fixtures.
- [ ] Preserve existing blueprint/privacy, timeout, cooldown and atomicity tests.
  If a real scoring bug is revealed, STOP with evidence; do not patch service.

### TASK 3 Verification / commit boundary

```sh
python -m pytest -q tests/test_assessments.py -k 'scoring_and_initial_verification or wrong_and_unanswered or declared_grade'
python -m pytest -q tests/test_assessments.py
env -u TEST_DATABASE_URL python -m pytest -q -ra
python -m ruff check tests/test_assessments.py
python -m ruff format --check tests/test_assessments.py
python -m mypy app
```

- [ ] Run default full suite when practical; document unavailable prerequisites
  and defer full PostgreSQL proof to Task9, not a false default-suite claim.
- [ ] Commit `test: freeze assessment scoring golden cases`; push, report, STOP.

## TASK 4 — Canonical qualification regressions

**File:** MODIFY `backend/tests/test_assessments.py` only. Dependencies: Task3.
Keep start/answer_counts/finish helpers; add focused regression or strengthen
test_grade_upgrade_fail_preservation_same_grade_and_specialization without
duplicating production synchronization logic.

### Qualification checklist

- [ ] Add `test_failed_higher_grade_preserves_current_qualification`. Freeze
  assessments.utcnow to explicit aware test times using monkeypatch, no sleeps:
  Middle starts before T1 and finishes at T1; Senior starts after T1, finishes
  at T2 within its30-minute window. Higher-grade cooldown is independent.
- [ ] Middle correct vector4/3/3/3/3 gives literal80/PASSED and blocks
  100/75/75/75/75. Save returned T1 canonical fields. Senior vector3/3/3/2/2
  gives literal65/FAILED and blocks75/75/75/50/50 at T2.
- [ ] After Senior failure assert exact specialization BACKEND, verified_grade
  MIDDLE, canonical score80 and verification dateT1 through submit verification,
  GET profile, GET availability verification, GET Senior detail verification.
  Also inspect DB profile with existing db_factory for persisted canonical state.
- [ ] History contains the Senior id/specialization/target/status65/T2 and its
  five literal blocks; older Middle remains. Detail/history attempt result must
  not contain substituted canonical score/date. Finished detail questions=[];
  no key/solutions. Repeat submit cannot replace canonical fields.
- [ ] Strengthen same-grade FAIL to compare all canonical fields and specialization.
  At allowed times after cooldown, successful same-grade G1 retake replaces80
  with70 and new date. Keep lower-grade prohibition and existing restoration
  regression; returning after specialization switch restores highest/latest PASS,
  not highest score. All-null new-specialization state is asserted as a triple.

### TASK 4 Verification / commit boundary

```sh
python -m pytest -q tests/test_assessments.py -k 'failed_higher_grade or grade_upgrade or specialization or cooldown or submit_idempotent'
DATABASE_URL="$TASK3_TEST_DATABASE_URL" TEST_DATABASE_URL="$TASK3_TEST_DATABASE_URL" python -m pytest -q tests/test_assessments.py -k 'failed_higher_grade or grade_upgrade or specialization or concurrent_start_and_submit_postgres or database_verification'
python -m ruff check tests/test_assessments.py
python -m ruff format --check tests/test_assessments.py
python -m mypy app
```

- [ ] PostgreSQL path demonstrates persisted state/lock regressions; record actual
  pass/skip counts. Do not change lock/service or schema code for this task.
- [ ] Commit `test: strengthen verified qualification regressions`; push, report, STOP.

## TASK 5 — Deterministic assessment date presentation

**Files:** MODIFY `frontend/src/assessment.ts` and
`frontend/tests/assessment.test.ts`. Dependencies: approved backend tasks.

### Date checklist

- [ ] Change dateLabel only: explicit ru-RU, UTC, 24-hour time, day/month/year and
  hour/minute/second fields, visible UTC suffix, null remains `—`.
- [ ] Keep serverClock, secondsRemaining, timerLabel, API helpers and late-save
  handling unchanged. Preserve date instants; no qualification computation.
- [ ] Add dateLabel tests with literal expected UTC date/time, including equivalent
  ISO representations with an offset and crossing a calendar day, plus null.
  Run targeted tests in two host timezones to prove host-independent output.
- [ ] Audit callers: finished_at → `Дата завершения попытки` in Task6;
  assessment_verified_at → `Дата подтверждения` in Task6; available_at → next
  retake/cooldown boundary, never a completion or verification date. Caller label
  edits belong to Tasks6/7; do not touch those files in Task5.
- [ ] Retain existing availability/clock/API tests; no contradictory PASS fixture
  changes until the result-specific Task6 boundary.

### TASK 5 Verification / commit boundary

```sh
TZ=UTC node --import tsx --test tests/assessment.test.ts
TZ=Europe/Moscow node --import tsx --test tests/assessment.test.ts
npm run typecheck
```

- [ ] Commit `fix: make assessment date presentation deterministic`; push, report, STOP.

## TASK 6 — Current qualification presentation

**Files:** MODIFY `frontend/src/components/assessment-dashboard.tsx`,
`frontend/src/components/assessment-result.tsx`, `frontend/tests/assessment.test.ts`.
Dependencies: Task5. History remains untouched in this task.

### Pure view / dashboard checklist

- [ ] Export a small pure `CurrentQualification` view from assessment-result,
  taking current CandidateProfile, reused by result and dashboard. No new file,
  fetch/store or optional state mutation. Existing card/dl/score-row styles suffice.
- [ ] Export `AssessmentDashboardSummary` in dashboard's existing file for pure
  static rendering; existing Dashboard passes data.verification. Keep hooks,
  loading, profile missing, error/retry, selection, availability and start intact.
- [ ] Keep `Заявленный уровень` outside the separate heading
  `Текущая подтверждённая квалификация`. Current block displays profile
  specialization, verified grade, `Оценка подтверждения` and `Дата подтверждения`.
  All-null triple shows `Подтверждённой квалификации пока нет.`; never substitute
  selected grade, declared grade or latest attempt. Do not add persistent state.

### Result checklist

- [ ] Modify AssessmentResult while preserving its optional verification prop.
  Add `Результат попытки` heading, attempt specialization/target grade, server
  PASSED/FAILED, attempt score, finished_at with explicit completion label,
  TIMEOUT notice and five competency rows. Historical success wording describes
  the attempt, not current qualification.
- [ ] Render `Общий балл >=70` and `Каждая компетенция >=50` with
  `Выполнено` / `Не выполнено` from returned aggregates. For Backend, require all
  five frozen keys; null/missing blocks never satisfy the second condition via
  empty every(). Small local presentation helper is allowed in this existing file;
  it does not derive authoritative status or canonical qualification.
- [ ] Display literal server status even with contradictory aggregate fixture;
  no silent correction. CurrentQualification uses only provided verification from
  attempt.verification, independently of attempt specialization/target/status.
- [ ] Preserve optional prop behavior: omitted verification is unavailable data,
  not an all-null profile and not a reason to infer qualification from attempt.
- [ ] Label available_at as `Следующая попытка на этом уровне — не ранее` using
  UTC dateLabel; this is a cooldown boundary, not guaranteed availability. Keep
  navigation links and weak-block explanation. Do not render questions/answers.

### Render tests / invariants

Use existing node:test, assert, React createElement/renderToStaticMarkup. Extract
only these small pure views; do not introduce DOM/hooks framework or restructure
the orchestration. Give fixtures complete canonical null/filled triples.

- [ ] Replace existing contradictory PASS spread fixture with coherent G4,
  five100s/overall100, appropriate PASSED retake date and finished date.
- [ ] G2 overall80/block25 → FAILED, overall met/block condition unmet.
- [ ] G3 overall65/all>=50 → FAILED, overall unmet/block condition met.
- [ ] Senior/G3 FAILED65/T2 with current Backend/Middle80/T1: scope assertions
  separately to attempt/current blocks, proving each grade/score/date belongs
  to the correct block, not merely that words occur anywhere.
- [ ] Declared Senior vs verified Middle dashboard; null canonical copy; omitted
  verification not falsely unverified; old Middle PASS/current Senior or changed
  specialization remains distinct. No profile fabrication.
- [ ] Adversarial render fixture with sentinel options/solutions produces no answer
  text/key. Contradictory status remains server status; missing competency data
  cannot yield a block-condition success. Dates and timeout meaning remain distinct.
- [ ] Retain autosave/API/clock/availability tests. Browser hooks/layout proof
  remains Task9, not a claim from static HTML tests.

### TASK 6 Verification / commit boundary

```sh
node --import tsx --test tests/assessment.test.ts
npm test
npm run typecheck
npm run lint
```

- [ ] Confirm no new stores, backend/API, CSS or history edits.
- [ ] Commit `feat: clarify verified qualification in assessment UI`; push, report, STOP.

## TASK 7 — History semantics

**Files:** MODIFY `frontend/src/components/assessment-history.tsx` and
`frontend/tests/assessment.test.ts`. Dependencies: Task6 shared semantics/tests.

### History checklist

- [ ] Keep History fetch/RoleGate/hooks/loading/error/retry unchanged and endpoint
  `/candidate/assessments/history` returning AttemptSummary[] only.
- [ ] Export small pure `AssessmentHistoryList` within this existing file for
  empty/list static rendering. Reuse labels, dateLabel and existing list styles;
  receive attempts only, never verification. Keep actual loading/error flows
  in orchestration, with browser acceptance later.
- [ ] Add exact copy `История попыток не заменяет текущую подтверждённую квалификацию.`
  outside the ul list markup but inside the pure view, so static tests cover the
  wording and it remains visible for empty history too.
- [ ] Each row says `Попытка` and keeps specialization, target grade, server status,
  score, started/finished dates, reason and five competency scores when finished.
  IN_PROGRESS stays in progress, not coerced to FAILED. Retain detail/continue link.
- [ ] Add static tests for empty, PASSED old attempt, FAILED attempt, in-progress
  row and explanatory wording. Ensure historical PASS does not claim current
  qualification and emits no fabricated profile/score/date. Do not fetch profile
  or modify backend/history contract.

### TASK 7 Verification / commit boundary

```sh
node --import tsx --test tests/assessment.test.ts
npm test
npm run typecheck
```

- [ ] Commit `feat: clarify assessment attempt history semantics`; push, report, STOP.

## TASK 8 — Assessment docs finalization

**Files:** MODIFY only `docs/assessment-methodology-draft.md`,
`docs/assessment-bank-audit-draft.md`, `docs/assessment-task3-implementation-map.md`.
Dependencies: implementation and targeted test evidence from Tasks1–7.
Do not rename or modify other docs/source/tests in this task.

### Evidence / documentation checklist

- [ ] Methodology: document actual validator integration separately from runtime
  availability, frozen blueprint/scoring/two conditions and literal G1–G5,
  canonical/attempt separation, randomization/repeats, retakes/cooldown/timeout,
  specialization restoration, relative grade meaning and limitations. Use coherent
  backend-generated80 for demonstration; preserve original audit provenance.
- [ ] Audit: retain exactly75 reviewed, 0 BLOCKER,27 IMPORTANT,6 MINOR,42 clean,
  all codes/findings and NOT_READY content conclusion under reviewed rubric.
  Add structural result and tested commit separately; IMPORTANT findings remain
  unresolved. No answer text/key/index/solutions or silent content reclassification.
- [ ] Implementation map: record actual completed files, test names, tested SHA,
  command results and remaining limits. Describe browser/full gate as pending
  until Task9; do not claim it passed based on planned checks. Existing imported
  baseline references remain original-audit provenance, not current-code citations.
- [ ] Claims remain limited to technical functioning, structural validation,
  deterministic documented rules and platform qualification. No psychometric
  validity, scientific grade calibration, cross-grade score equivalence,
  certification, universal developer grade or hiring probability.

### TASK 8 Verification / commit boundary

From repository root, manually read the entire docs diff against actual prior
implementation/test reports; compare counts with the approved audit:

```sh
git diff -- docs/assessment-methodology-draft.md docs/assessment-bank-audit-draft.md docs/assessment-task3-implementation-map.md
rg -n '75|27|IMPORTANT|MINOR|BLOCKER|42|NOT_READY|psychometric' docs/assessment-methodology-draft.md docs/assessment-bank-audit-draft.md docs/assessment-task3-implementation-map.md
git diff --check
git status --short
```

- [ ] Confirm only three docs modified, every claim has existing evidence, Task9
  pending status is explicit and no code change is included.
- [ ] Commit `docs: finalize assessment validation evidence`; push, report, STOP.

## TASK 9 — Full verification gate

**Files:** none planned. Dependencies: reviewed Tasks1–8. No feature development,
new fixtures in production seed, tests-results-only commit or autonomous PR.

### Backend full gate

- [ ] Configure isolated PostgreSQL17 DATABASE_URL (not application production DB).
  Existing tests create/drop their own schemas; Alembic upgrade/check below runs
  against the isolated test DB only. Set APP_ENV=test for backend test execution.
- [ ] Run the full PostgreSQL suite with TEST_DATABASE_URL=DATABASE_URL, then
  default/SQLite separately and report intentional PostgreSQL-only skips.

```sh
export DATABASE_URL="$TASK3_TEST_DATABASE_URL"
export APP_ENV=test
TEST_DATABASE_URL="$DATABASE_URL" python -m pytest -q
env -u TEST_DATABASE_URL python -m pytest -q -ra
python -m ruff check .
python -m ruff format --check .
python -m mypy app
python -m alembic upgrade head
python -m alembic check
```

- [ ] No new migration. Verify full existing Matching/Need/provider/seed tests
  included without changing their files or using holdout tuning/output.

### Frontend full gate

```sh
npm ci
npm run lint
npm run typecheck
npm test
npm run build
```

- [ ] Existing lockfile/dependency list unchanged. Record test totals and each
  command result; npm ci installs locked dependencies, not new ones.

### Docker / existing CI regression

Use an isolated local Compose project `fsp-task3-verification`, preconfigured
git-ignored `.env` with safe local values. Free the existing configured3000/8000/
5432 ports before starting; if occupied, stop and arrange an isolated environment,
do not stop unrelated apps or alter tracked Compose config. Project prefix makes
the volume isolated; do not delete any existing application volume.

From repo root (restore local shell-only test settings before Compose if needed):

```sh
docker compose -p fsp-task3-verification up --build -d --wait --wait-timeout 180
docker compose -p fsp-task3-verification exec -T backend python -m app.seed
docker compose -p fsp-task3-verification exec -T backend python -m app.seed
docker compose -p fsp-task3-verification exec -T backend python -m app.seed --demo
docker compose -p fsp-task3-verification exec -T backend python -m app.seed --demo
docker compose -p fsp-task3-verification exec -T backend python -m app.seed --matching-demo
docker compose -p fsp-task3-verification exec -T backend python -m app.seed --matching-demo
curl --fail http://localhost:8000/health
curl --fail http://localhost:3000/api/skills
docker compose -p fsp-task3-verification ps
```

- [ ] All three existing seed modes succeed twice and full existing seed tests
  assert idempotency. No new demo canonical/history writer is introduced.
- [ ] Reuse existing Checks workflow: backend/frontend/docker jobs. Record final
  pushed SHA and check all jobs for that SHA; no workflow modification planned.
  If a missing command truly makes required verification impossible, STOP with
  evidence for reviewed scope rather than independently editing CI.

### Browser / manual gate

Use the isolated test application, actual existing candidate profile/assessment
APIs, and controlled test-only answer/time arrangement as in current backend
fixtures where needed. No production endpoints, question edits or persistent
demo scripts are added. Use fresh test accounts/attempts so cooldown does not
need bypass in production logic. Run each scenario on desktop and375px; distinguish
real browser observations from static-render or fixture-only evidence.

- [ ] **Current Middle80 + Senior65 FAIL:** establish Middle PASS with4/3/3/3/3
  and capture its canonical dateT1. Finish Senior with3/3/3/2/2 atT2. Inspect
  dashboard/result/history and detail response: current Backend/Middle80/T1,
  attempt Senior/FAILED65/T2; no canonical replacement. Declared Senior separately.
- [ ] **Coherent PASS:** G4-style100/five100s, server PASSED, both labels met,
  finished date and current qualification clearly separate.
- [ ] **Block failure:** G2-style80/one25, server FAILED, overall met, block unmet.
- [ ] **Overall failure:** G3-style65/all>=50, server FAILED, overall unmet, block met.
- [ ] **Unverified:** all-null canonical profile gives explicit copy on dashboard
  and result; no substitution from attempt. Missing render prop isn't a null profile.
- [ ] **History:** exact historical copy, named attempts and all fields; empty,
  loading, backend error/retry, in-progress link and finished detail navigation.
- [ ] **Old success / different current:** view old Middle PASS with current Senior
  or another profile specialization; historical PASS never overwrites current.
- [ ] **TIMEOUT:** aggregate result and timeout notice, finished_at equals server
  deadline, no paused/restarted timer semantics; either PASS or FAIL remains server-owned.
- [ ] **Dates:** UTC visible; completion, verification and next-retake boundary
  independently labelled; next date is not a guaranteed available-grade claim.
- [ ] **Privacy:** finished response questions=[] and page shows aggregate data
  only. No option/key/index/solution review; no new personal-data endpoint or
  qualification localStorage/sessionStorage. Active-question controls unchanged.
- [ ] Check wrapping/readability/disabled states at375px and existing dashboard
  loading/profile-missing/error flows; record exact observed result and tested SHA.

After browser work, inspect logs/health as needed and stop only the verification
project without deleting volumes:

```sh
docker compose -p fsp-task3-verification logs
docker compose -p fsp-task3-verification down
```

### Final source / scope inspection

From root, use the fixed approved production baseline, not a drifting main ref:

```sh
git diff --name-status 671ad354658ec9c092b00e6811e6a5a73f66f5af...HEAD
git diff --stat 671ad354658ec9c092b00e6811e6a5a73f66f5af...HEAD
git diff --exit-code 671ad354658ec9c092b00e6811e6a5a73f66f5af -- backend/app/content/backend_questions.json backend/app/services/assessments.py backend/app/models.py backend/app/assessment_schemas.py backend/app/schemas.py backend/app/services/profiles.py backend/app/routes/assessments.py backend/alembic .github frontend/package.json frontend/package-lock.json backend/requirements.txt backend/requirements-dev.txt
git diff --exit-code 671ad354658ec9c092b00e6811e6a5a73f66f5af -- backend/app/services/matching.py backend/app/services/matching_rules.py backend/app/services/candidate_assessments.py backend/app/services/employer_needs.py backend/app/need_schemas.py backend/app/routes/employer_needs.py frontend/src/employer-needs.ts frontend/src/components/employer-needs-screen.tsx frontend/src/components/employer-need-form.tsx frontend/src/components/employer-matches-screen.tsx frontend/src/app/employer
git diff --check 671ad354658ec9c092b00e6811e6a5a73f66f5af...HEAD
git status
```

- [ ] Inspect the entire changed-file inventory for accidental files outside the
  approved map, including Matching/Need tests, seed, auth, README, globals.css,
  holdout artifacts or dependency changes not covered by the explicit commands.
- [ ] Report exact tests/totals/skips, static/build/CI/browser results and integrity
  evidence. No commit merely recording results. No PR or merge under this plan.
- [ ] If a defect is found, STOP with evidence before a broad fix. A scoped
  presentation/validator fix also requires explicit reviewed scope and a separate
  commit; do not patch frozen services/content under a verification gate.

## Production file freeze / excluded remediation

Frozen unless a proven bug is separately escalated and reviewed:

- `backend/app/services/assessments.py`
- `backend/app/models.py`
- `backend/app/assessment_schemas.py`
- `backend/app/schemas.py`
- `backend/app/services/profiles.py`
- `backend/app/routes/assessments.py`
- `backend/app/content/backend_questions.json`
- `backend/alembic/`, every migration directory/file
- Matching/Need backend and frontend implementation, their models/schemas/routes/
  tests, existing matching demo seed and canonical assessment provider
- `backend/app/seed.py`, README, `.github/workflows/checks.yml`
- Package/lock/requirements/dependency files, `frontend/src/app/globals.css`
- `frontend/src/components/assessment-attempt.tsx`, existing assessment endpoints,
  frozen holdout data and approved design

The27 IMPORTANT questions are NOT fixed in Task3. No new questions/versions,
replacement records, distractor edits or answer changes. Question remediation is
a separate future product task after Task3 and requires versioned history safety.

## Security / privacy checkpoints

Tasks1/2 own safe finding/parser/structural-error diagnostics: no option text,
correct index, answer key or solution. Tasks3/4 retain API ownership, atomicity
and aggregate-only finished output. Tasks6/7/9 ensure finished UI displays no
answer review and history fabricates no current profile. Candidate verification
is always server-owned; no new personal-data endpoint, caller canonical writes,
frontend persistence or duplicate qualification state. No source/answer content
is printed to reports, docs or CI logs to demonstrate coverage.

## Plan self-review / design mapping

| Authorization check | Result |
|---|---|
| Question content/remediation changes | Not authorized |
| Scoring changes | Not authorized |
| Cooldown changes | Not authorized |
| Selection changes | Not authorized |
| Migration changes | Not authorized |
| API/schema changes | Not authorized |
| New qualification persistence | Not authorized |
| Matching/Need changes | Not authorized |
| Package/dependency changes | Not authorized |

Every planned source change maps to the approved design file map: validator
core/tests (Task1), post-parsing loader/safe errors (Task2), existing test
strengthening (Tasks3/4), deterministic dateLabel (Task5), existing presentation
views/render tests (Tasks6/7), existing-doc finalization (Task8). Task9 verifies
the approved DoD without opening new feature scope. No globals.css change needed.

Step3 expected diff: this one new implementation-plan file only. Commit message:
`docs: plan assessment validation implementation`. Push to the existing feature
branch, confirm matching local/remote SHA and clean status, STOP for human review.
IMPLEMENTATION NOT STARTED. PR NOT CREATED.
