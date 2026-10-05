# Employer Needs + Matching Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver employer-owned needs and live, deterministic, explainable, privacy-safe candidate matching with the approved frozen scoring rules.

**Architecture:** Extend the existing synchronous FastAPI/SQLAlchemy services and thin routes. Keep normalized need persistence, a read-only assessment provider, pure matching rules, and ORM orchestration separate; use the existing Next.js page/component composition and API transport. Candidate Assessment Engine remains the sole owner of canonical verification persistence.

**Tech Stack:** Python 3.13+, FastAPI, SQLAlchemy 2, Pydantic 2, Alembic, PostgreSQL 17, pytest, Ruff, mypy; Node 22+, Next.js App Router, React, TypeScript, ESLint, Node test runner through tsx, Docker Compose.

**Spec:** docs/superpowers/specs/2026-10-05-employer-needs-matching-design.md

## Global Constraints

- Planning baseline: `origin/main = 9892400d57b57fe3104d1871fa3513e56e24c4b5`; feature HEAD before this plan: `3c16baed9e4160f043a92b654173ea1bc074866e`. The feature contains this main; no additional rebase was needed when preparing the plan.
- Work on `feat/employer-needs-matching`; preserve unrelated changes. The user's subsequent explicit approval supersedes the historical unapproved-status paragraphs in the spec. This plan itself still requires team review before execution.
- Reuse User, Role, CandidateProfile, EmployerProfile, Skill, Specialization, Grade, TimestampMixin, sessions, Origin protection and the existing error envelope. No replacement auth, catalogs, profiles, repository layer or transaction framework.
- Specialization exact match, consent true, verified grade, compatible grade, all must-haves and available valid normalized assessment are hard filters. No declared-grade fallback.
- Frozen base weights: Assessment 45%, Grade fit 25%, Nice-to-have 15%, Experience 15%. Optional-factor omission renormalizes remaining weights to 100.
- Explicit zero experience target gives ExperienceFit 1, including missing candidate experience. Positive target with missing experience gives 0; null target excludes the factor.
- `DRAFT → ACTIVE → CLOSED`; DRAFT/ACTIVE editable; CLOSED immutable, update 409. Matching only ACTIVE. Scalar fields and skill relationships update atomically.
- Every matching request uses fresh committed inputs; no persisted MatchScore, ranking snapshot or ranking cache. Retain no-store responses.
- Assessment Engine owns `verified_grade`, `normalized_assessment_score`, `assessment_verified_at`, their consistency and history. O1 reads them, never migrates/writes them or calls assessment synchronization/finalization.
- No real confirmed-FSP achievement source exists at this baseline. No FSP production flag/tie-breaker; neither fsp_id nor profile/assessment recency affects fit or rank.
- Preview allowlist only; omit about, full surname, contacts, consent and internal fields. `assessment_verified_at` is allowed solely for display.
- Skills are self-declared. Labels are «Соответствие» / Professional fit, never probability or verified skills.
- Invitations, contacts disclosure, Testing Engine internals, ATS, charts, AI ranking, admin, deployment and merge are outside O1.
- Production implementation, migration creation and test changes are not authorized during this plan-writing turn. All unchecked steps below describe future execution.

## Review Focus

1. CLOSED transition racing an ACTIVE update: reload the locked parent before mutation; CLOSED remains immutable. Task 2 state tests and Task 7 PostgreSQL concurrency test own this risk.
2. A rejected ACTIVE edit mixes changed scalars with old/replaced skills: reject before mutation or roll back the entire transaction; next matching remains unchanged. Tasks 2 and 7 own validation and persistence-failure tests.
3. Null, zero, nonfinite or out-of-range provider values: null/invalid exclude, zero remains available; no fallback or assessment writes. Tasks 3–4 own provider/eligibility tests.
4. Scores displaying the same decimal and pagination cutting the pool: unrounded ordering precedes pagination; exact ties use normalized assessment then stable ID. Tasks 5–6 own numeric/ranking/pagination tests.
5. A source profile containing contacts or changed dates/FSP/declared grade: exact preview allowlist, informational assessment date and invariant fit/rank. Tasks 6 and 10 own API/presentation tests; Task 7 retains candidate-flow regression.

## Repository patterns and file map

Paths below are repository-relative. Backend does **not** have schemas/services repositories as separate architectural layers: `app/schemas.py` is shared; `assessment_schemas.py` already demonstrates a feature schema module. Routes live in `app/routes`, not `app/api`. Keep these conventions.

| File | Action and responsibility | Owning tasks |
| --- | --- | --- |
| `backend/app/models.py` | Modify: need enums, EmployerNeed, EmployerNeedSkill only; reuse existing IDs/timestamps/catalog | 1 |
| `backend/alembic/versions/<generated_revision>_employer_needs.py` | Create during execution: O1-owned schema, downgrade | 1 |
| `backend/app/need_schemas.py` | Create: strict need input, need/page outputs, dedicated matching preview/breakdown outputs | 2, 6 |
| `backend/app/services/employer_needs.py` | Create: ownership, validation, transactions, lifecycle and need serialization | 2 |
| `backend/app/services/candidate_assessments.py` | Create: batch read contract, canonical profile adapter | 3 |
| `backend/app/services/matching_rules.py` | Create: pure eligibility, fit and deterministic ranking types/functions | 4–5 |
| `backend/app/services/matching.py` | Create: fresh ORM inputs, provider, orchestration and safe output construction | 6 |
| `backend/app/routes/employer_needs.py` | Create: seven thin routes, permission/Origin/query validation/provider dependency | 2, 6 |
| `backend/app/main.py` | Modify: include the employer-needs router | 2 |
| `backend/app/seed.py` | Modify: explicit local matching demo; preserve existing modes/accounts | 8 |
| `backend/tests/conftest.py` | Modify: small reusable employer/need/candidate factories using existing fixtures | 2, 6 |
| `backend/tests/test_infrastructure.py` | Modify: table expectations, O1 migration round-trip and PostgreSQL integrity tests | 1 |
| `backend/tests/test_employer_needs.py` | Create: Need API, validation, lifecycle, ownership, atomic edits | 2 |
| `backend/tests/test_candidate_assessments.py` | Create: provider batching/read-only contract | 3 |
| `backend/tests/test_matching_rules.py` | Create: independent eligibility/numeric/ranking unit tests | 4–5 |
| `backend/tests/test_matching.py` | Create: matching API/privacy, batching, live edits and integration regressions | 6–7 |
| `backend/tests/test_matching_seed.py` | Create: demo idempotency, canonical consistency, expected matching | 8 |
| `frontend/src/employer-needs.ts` | Create: feature DTOs, API functions and form/presentation helpers | 9–10 |
| `frontend/src/components/employer-need-form.tsx` | Create: reusable controlled need form | 9 |
| `frontend/src/components/employer-needs-screen.tsx` | Create: RoleGate, list/editor orchestration and states | 9 |
| `frontend/src/components/employer-matches-screen.tsx` | Create: RoleGate, matches loading, safe cards and details | 10 |
| `frontend/src/app/employer/needs/page.tsx` | Create: thin list page | 9 |
| `frontend/src/app/employer/needs/new/page.tsx` | Create: thin create page | 9 |
| `frontend/src/app/employer/needs/[id]/edit/page.tsx` | Create: async params page, keyed editor | 9 |
| `frontend/src/app/employer/needs/[id]/matches/page.tsx` | Create: async params page, keyed matching screen | 10 |
| `frontend/src/components/auth.tsx` | Modify only existing Header: employer-only Needs navigation; retain AuthProvider/RoleGate | 9 |
| `frontend/src/components/feedback.tsx` | Modify: labels for Need validation fields | 9 |
| `frontend/src/app/globals.css` | Modify: minimal need badges/form/card responsive rules | 9–10 |
| `frontend/tests/employer-needs.test.ts` | Create: helpers/API/form/list SSR tests | 9 |
| `frontend/tests/employer-matches.test.ts` | Create: matching state/card/details SSR and API tests | 10 |
| `.github/workflows/checks.yml` | Modify only demo smoke step if needed: exercise matching seed twice | 8 |
| `README.md` | Modify: Need API, privacy/matching rules, demo and manual checks | 8, 10 |

The revision placeholder is intentional: the spec forbids assigning an ID before creation. During Task 1, `alembic revision -m "employer needs"` determines this one file's actual path and revision; record both in execution notes. Its `down_revision` must be the actual head (0002 at this baseline). No other file path is deferred.

Do not create a second Skill catalog, candidate/employer model, assessment snapshot, repository module, scoring endpoint, preview-detail endpoint, frontend transport, shared form framework or test framework. Reuse `schemas.InputModel/SkillOut`, `profiles.employer_profile`, `dependencies.EmployerUser/Db/require_trusted_origin`, `errors.ApiError`, `api()`, `RoleGate`, `Feedback`, shared grade/specialization labels and existing CSS. Do not modify `0001`, `0002_assessment_engine.py`, `assessment_schemas.py`, assessment services/content or candidate screens.

## Execution conventions

Run backend commands from `backend`, frontend commands from `frontend`, Git/Compose commands from the repository root. Use the installed virtual environment and Node version matching CI. Tests use the existing migrated SQLite fixture by default and `TEST_DATABASE_URL` for isolated PostgreSQL schemas; PostgreSQL-only assertions must not be reported as proven by SQLite.

For each task, repeat its RED → minimal implementation → GREEN cycle for each focused behavior before broadening. Assertions below are test oracles, not duplicated scoring algorithms. Write literal expected numbers and use `pytest.approx` only for floating-point tolerance. SSR tests follow `tests/assessment.test.ts`: `node:test`, `node:assert/strict`, `createElement`, `renderToStaticMarkup`, and restored fetch mocks; no new framework. They do not prove browser event handling; the final browser gate does.

Each commit stages only that task's declared files, with explicit paths; never `git add .`. Commit only after the focused tests and relevant regressions pass. If the baseline moves before execution, fetch/rebase and recheck the migration head without changing approved product rules.

### Task 1: Normalized Need persistence and migration

**Files**
- Modify: `backend/app/models.py`, `backend/tests/test_infrastructure.py`.
- Create: `backend/alembic/versions/<generated_revision>_employer_needs.py` (resolved as described above).

**Interfaces**
- Consumes: existing `Base`, `new_id`, `TimestampMixin`, `EmployerProfile`, `Skill`, `Grade`, `Specialization`.
- Produces: `NeedStatus(StrEnum)` = DRAFT/ACTIVE/CLOSED; `NeedSkillKind(StrEnum)` = MUST_HAVE/NICE_TO_HAVE.
- Produces: `EmployerNeed`: String(36) ID, employer FK, title String(200), specialization/required_grade enums, nullable Float target experience, Numeric(12,2) salary bounds, Text description/additional requirements, status and existing timestamps.
- Produces: `EmployerNeedSkill`: composite PK `(need_id, skill_id)`, cascade need FK, catalog skill FK, kind; `EmployerNeed.skill_requirements: list[EmployerNeedSkill]` with selectin loading/cascade delete-orphan and stable skill-ID ordering; each association exposes `skill: Skill` with eager loading.

- [ ] Write `test_need_migration_round_trip_preserves_assessment_state`: upgrade 0002 → new head → 0002 → head, asserting canonical trio and existing profiles/catalog unchanged; new tables present only at O1 head. Extend the existing head-table assertion.
- [ ] Write `test_need_database_integrity` using savepoints/rollback: negative/reversed salaries, invalid kind/status, negative/nonfinite target, unknown FK and duplicate/cross-kind `(need_id, skill_id)` must raise `IntegrityError`; a valid association persists. Mark backend-specific nonfinite checks explicitly PostgreSQL-only if SQLite cannot represent them.
- [ ] Run `pytest -q tests/test_infrastructure.py -k need_migration`; expect failure because Need tables/revision are absent, not because the test database is unavailable.
- [ ] Add the two model classes/enums in `app/models.py` using existing non-native enum/check conventions; add salary nonnegative/order and finite nonnegative target checks, employer/status indexes and FK integrity. Keep all candidate columns unchanged.
- [ ] Generate and author the new migration from the real head; align constraints/index names with model metadata and implement downgrade removing only O1 tables/indexes.
- [ ] Run `pytest -q tests/test_infrastructure.py`; expect all infrastructure tests pass and `alembic check` finds no schema drift after head upgrade.
- [ ] Run the same file with `TEST_DATABASE_URL` pointing to PostgreSQL; expect actual FK/check/round-trip assertions pass.
- [ ] Commit these files: `feat: add normalized employer need persistence`.

The database cannot enforce “at least one must-have” with a simple row check; Task 2 enforces it transactionally. Reject infinity/NaN at the input layer as well. Numeric(12,2) provides a concrete storage limit; schema validation in Task 2 must agree with it.

### Task 2: Need API, ownership, lifecycle and atomic editing

**Files**
- Create: `backend/app/need_schemas.py`, `backend/app/services/employer_needs.py`, `backend/app/routes/employer_needs.py`, `backend/tests/test_employer_needs.py`.
- Modify: `backend/app/main.py`, `backend/tests/conftest.py`.

**Interfaces**
- Consumes: Task 1 models, `EmployerUser`, `Db`, `require_trusted_origin`, `employer_profile(db, user)`, `InputModel`, `SkillOut`, `ApiError`.
- Produces: `NeedWrite(InputModel)` with position_title, specialization, required_grade, nullable target_experience_years, salary_from/to, description, nullable additional_requirements, `must_have_skill_ids: list[str]`, `nice_to_have_skill_ids: list[str]` (default empty). No owner/status/calculated/assessment input fields.
- Produces: `NeedOut`, `NeedPage(items: list[NeedOut], total: int, limit: int, offset: int)`. NeedOut contains own need scalars/timestamps and `must_have_skills`/`nice_to_have_skills: list[SkillOut]`.
- Produces service functions: `create_need(db: Session, user: User, data: NeedWrite) -> EmployerNeed`; `get_need(db: Session, user: User, need_id: str, *, for_update: bool = False) -> EmployerNeed`; `list_needs(db: Session, user: User, *, limit: int, offset: int) -> NeedPage`; `update_need(db: Session, user: User, need_id: str, data: NeedWrite) -> EmployerNeed`; `activate_need(db: Session, user: User, need_id: str) -> EmployerNeed`; `close_need(db: Session, user: User, need_id: str) -> EmployerNeed`; `need_out(need: EmployerNeed) -> NeedOut`.
- Produces six thin routes: GET/POST `/employer/needs`, GET/PUT `/{need_id}`, POST `/{need_id}/activate`, POST `/{need_id}/close`. POST create 201; reads/updates/transitions 200. Task 6 adds the seventh route.

Test rows belong to `test_employer_needs.py`; parameterize parallel validation/access cases rather than duplicating setup.

| Test name | Required assertion |
| --- | --- |
| `test_employer_creates_own_draft` | `status_code == 201`; persisted employer ID equals authenticated profile; status DRAFT; catalog links preserved |
| `test_need_routes_require_employer` | every six-route method: anonymous 401, Candidate 403 |
| `test_need_routes_hide_foreign_and_missing_ids` | GET/PUT/activate/close foreign or absent IDs 404; own list omits foreign records |
| `test_need_mutations_require_trusted_origin` | mutation with cookie and wrong/missing Origin rejected by existing dependency |
| `test_need_requires_employer_profile` | existing `profile_not_found` error; no Need created |
| `test_need_input_validation` | empty/blank title or description, reversed/negative salary, NaN/infinite/negative target, salary exceeding Numeric(12,2), duplicate IDs within either list, overlap, zero must-haves rejected 422 |
| `test_unknown_need_skill_rejected` | unknown catalog ID rejected 422 in existing envelope; no scalar/association mutation |
| `test_need_rejects_mass_assignment` | owner/status/score/eligibility/grade-fit/assessment-trio extra keys each rejected 422 |
| `test_need_lifecycle_and_editing` | DRAFT edit 200, activate ACTIVE, ACTIVE edit 200, close CLOSED; invalid transition 409 |
| `test_need_skill_kind_reassignment` | valid update moves an existing skill from must to nice, retaining another must; exactly one row per skill with its new kind |
| `test_closed_need_update_is_immutable` | PUT 409; scalars, timestamps and both skill lists unchanged |
| `test_invalid_active_update_is_atomic` | each validation failure above: attempted scalar AND skill changes rejected; persisted original scalars/relations unchanged |
| `test_active_update_persistence_failure_rolls_back` | injected flush/commit IntegrityError returns conflict envelope; independent Session reads original scalars/relations |
| `test_need_list_pagination` | `{items,total,limit,offset}`, created_at DESC/id ASC, default20/max100, negative offset/invalid limit422 |

- [ ] Write the first creation/access tests and shared factories; factories preserve canonical assessment consistency and existing fixture behavior.
- [ ] Run `pytest -q tests/test_employer_needs.py -k 'creates_own_draft or require_employer'`; expect 404 for missing routes before implementation.
- [ ] Implement NeedWrite/NeedOut/NeedPage in `need_schemas.py`; title length1–200 and nonempty description after trimming, salary Decimal finite/nonnegative/max_digits12/decimal_places2/order, nonnegative finite target, unique/disjoint IDs and nonempty must-have.
- [ ] Implement service creation/reads/list and `need_out` with stable skill ordering and profile-derived ownership; unknown skills produce `ApiError(422, "unknown_skill", ...)` using the existing error envelope.
- [ ] Register the router with existing employer/Origin dependencies in `main.py`.
- [ ] Run the creation/access tests; expect PASS.
- [ ] Write the remaining validation/lifecycle/atomicity tests from the table.
- [ ] Run `pytest -q tests/test_employer_needs.py`; expect missing update/transition behavior to fail.
- [ ] Implement mutations: select the owner-scoped parent using `with_for_update().execution_options(populate_existing=True)`, load relationships after the lock, validate all skill IDs before changing anything, reconcile associations by skill ID (update existing kinds, add new, remove absent), then one commit and refresh. On persistence failure roll back and return `ApiError(409, "need_conflict", ...)`; no partial commits or duplicate-PK insert during kind changes.
- [ ] Implement invalid lifecycle/CLOSED-update errors as `ApiError(409, "need_state_conflict", ...)`; foreign/missing IDs as `ApiError(404, "need_not_found", ...)`.
- [ ] Run `pytest -q tests/test_employer_needs.py`; expect PASS.
- [ ] Run `pytest -q tests/test_auth.py tests/test_profiles.py tests/test_infrastructure.py`; expect existing suites remain green.
- [ ] Commit declared files: `feat: add employer need management API`.

Transaction boundary is the existing request Session, not a nested replacement framework: auth/reads may already have started its transaction. Parent lock, scalar changes, association reconciliation/delete-orphan removals and commit occur in that transaction. Set updated_at even for a skills-only edit. Input failures happen before changes; DB failures roll it back. Route input validation must not “save the valid part.”

### Task 3: Read-only batch CandidateAssessmentProvider

**Files**
- Create: `backend/app/services/candidate_assessments.py`, `backend/tests/test_candidate_assessments.py`.

**Interfaces**
- Consumes: `Session`, existing canonical `CandidateProfile` fields.
- Produces frozen `CandidateAssessment(candidate_id: str, verified_grade: Grade | None, normalized_assessment_score: int | None, assessment_verified_at: datetime | None)`.
- Produces Protocol `CandidateAssessmentProvider.get_assessments(self, candidate_ids: Sequence[str]) -> Mapping[str, CandidateAssessment]`.
- Produces `ProfileAssessmentProvider(db: Session)` implementing that protocol with projected canonical-column queries, de-duplicated IDs and chunks of at most 500. Empty input returns `{}` without SQL; absent profile IDs omitted.
- Test-local `FakeAssessmentProvider` implements the same interface, returns configured records and records calls. No production fake, cache, snapshot or write endpoint.

- [ ] Write `test_provider_returns_canonical_current_state`, `test_provider_empty_and_missing_ids`, `test_provider_batches_and_deduplicates`, `test_provider_does_not_write_assessment_fields`; assert trio equals persisted values, empty zero queries, 501 unique IDs at most two provider SELECTs, no UPDATE/INSERT/DELETE/commit and trio unchanged in an independent read. Include a dirty Session object to prove a provider SELECT does not auto-flush pending assessment changes.
- [ ] Run `pytest -q tests/test_candidate_assessments.py`; expect import/implementation failure for the absent provider.
- [ ] Implement the DTO/protocol/production provider with one projected SELECT per chunk inside `db.no_autoflush`; no writes, assessment attempt/history queries or calls to `synchronize_verification`.
- [ ] Run `pytest -q tests/test_candidate_assessments.py`; expect PASS.
- [ ] Run `pytest -q tests/test_assessments.py tests/test_profiles.py`; expect canonical state ownership behavior preserved.
- [ ] Commit declared files: `feat: add read-only batch assessment provider`.

The provider is an integration abstraction, not a persistence owner. Future Assessment Engine changes remain behind its read adapter; all matching tests can inject the fake without building questions/attempts. Persisted fixtures must set all three canonical fields together; partial states belong only to defensive fake-provider tests.

### Task 4: Pure hard-filter eligibility

**Files**
- Create: `backend/app/services/matching_rules.py`, `backend/tests/test_matching_rules.py`.

**Interfaces**
- Consumes: Task 3 `CandidateAssessment` DTO, existing Grade/Specialization enums only; no Session or ORM access in rules.
- Produces frozen `NeedCriteria(specialization: Specialization, required_grade: Grade, must_have_skill_ids: frozenset[str], nice_to_have_skill_ids: frozenset[str], target_experience_years: float | None)`.
- Produces frozen `CandidateMatchInput(candidate_id: str, specialization: Specialization, personal_data_consent: bool, skill_ids: frozenset[str], years_of_experience: float | None)`; no declared grade, FSP or recency fields.
- Produces frozen `EligibleCandidate(candidate: CandidateMatchInput, verified_grade: Grade, normalized_assessment_score: int, assessment_verified_at: datetime | None, grade_fit: float)`; construct it only after validating the provider DTO, so downstream grade/score types are nonnullable.
- Produces `grade_fit(required_grade: Grade, verified_grade: Grade) -> float | None` and `eligible_candidate(need: NeedCriteria, candidate: CandidateMatchInput, assessment: CandidateAssessment | None) -> EligibleCandidate | None`.

- [ ] Write parameterized `test_grade_compatibility`: literal matrix JUNIOR→JUNIOR1/MIDDLE0.75/SENIORNone, MIDDLE→JUNIORNone/MIDDLE1/SENIOR0.75, SENIOR→JUNIORNone/MIDDLENone/SENIOR1.

Test assertions use the producing interface directly, for example:

```python
assert grade_fit(Grade.MIDDLE, Grade.MIDDLE) == 1.0
assert grade_fit(Grade.MIDDLE, Grade.SENIOR) == 0.75
assert grade_fit(Grade.MIDDLE, Grade.JUNIOR) is None
assert grade_fit(Grade.JUNIOR, Grade.SENIOR) is None
```

- [ ] Run `pytest -q tests/test_matching_rules.py -k grade_compatibility`; expect absent function/module failure.
- [ ] Implement the explicit compatibility lookup in `matching_rules.py`.
- [ ] Run the grade tests; expect PASS.
- [ ] Write `test_eligibility_hard_filters` with one altered input per case: wrong specialization, consent false, null verified grade, incompatible grade, one missing must-have, missing provider record, mismatched record candidate ID, null score, score -1/101/NaN/infinity; each `result is None`. `test_eligible_zero_score` asserts score0 is eligible with otherwise valid inputs. `test_consent_false_excludes_verified_perfect_candidate` uses score100, all skills and exact grade.
- [ ] Run `pytest -q tests/test_matching_rules.py -k 'eligibility or eligible_zero or consent_false'`; expect missing eligibility function failure.
- [ ] Implement ordered filters according to the spec: consent, specialization, present grade, compatible grade, all must-have, available finite 0–100 score. Return no eligible object on failure; do not call scoring here.
- [ ] Run `pytest -q tests/test_matching_rules.py`; expect PASS.
- [ ] Run `pytest -q tests/test_candidate_assessments.py`; expect PASS.
- [ ] Commit declared files: `feat: implement matching hard-filter eligibility`.

### Task 5: Pure scoring, explainable contributions and deterministic ranking

**Files**
- Modify: `backend/app/services/matching_rules.py`, `backend/tests/test_matching_rules.py`.

**Interfaces**
- Consumes: Task 4 eligible objects/NeedCriteria.
- Produces frozen `ScoringInput(normalized_assessment_score: int, grade_fit: float, matched_nice_to_have: int, total_nice_to_have: int, years_of_experience: float | None, target_experience_years: float | None)`.
- Produces frozen `FactorContribution(score: float, max: float, active: bool)` and `ProfessionalFit(score: float, assessment: FactorContribution, grade: FactorContribution, nice_to_have: FactorContribution, experience: FactorContribution)`.
- Produces `score_professional_fit(data: ScoringInput) -> ProfessionalFit` and frozen `RankedCandidate(eligible: EligibleCandidate, fit: ProfessionalFit)`; `rank_candidates(candidates: Sequence[RankedCandidate]) -> list[RankedCandidate]`.
- Scoring validates internal preconditions (finite score0–100, grade fit exactly1/.75, valid skill counts and finite nonnegative experience). Eligibility normally ensures them; invalid direct calls raise ValueError instead of producing NaN ranking.

Numeric fixtures use score80, exact grade, 1/2 nice matches and 2/4 years unless overridden. These are independent literals, not a copied formula in tests.

| Test name | Exact assertion/oracle |
| --- | --- |
| `test_score_contributions` | assessment36/max45, grade25/max25, nice7.5/max15, experience7.5/max15; total76 |
| `test_overqualified_contribution` | grade18.75, total69.75 |
| `test_experience_cap` | 8/4 years: experience15, total83.5 |
| `test_missing_candidate_experience` | positive target, yearsNone: experience0, total68.5 |
| `test_zero_experience_target` | target0 with yearsNone/0/8: experience15, total83.5 |
| `test_no_nice_factor_renormalization` | total `approx(80.58823529411765)`, excluded nice activeFalse/max0; assessment max `approx(52.94117647058823)` |
| `test_no_experience_factor_renormalization` | total `approx(80.58823529411765)`, experience activeFalse/max0; grade max `approx(29.41176470588235)` |
| `test_both_optional_factors_absent` | total `approx(87.14285714285714)`; maxima assessment `approx(64.28571428571429)`, grade `approx(35.714285714285715)` |
| `test_scoring_bounds_and_invalid_inputs` | maximum100, assessment0 contribution0; all valid combinations `0 <= score <= 100`; invalid preconditions raise ValueError |
| `test_unrounded_score_wins` | two different scores with same one-decimal display sort by their actual floats |
| `test_deterministic_ties` | equal total: greater assessment first; equal assessment: candidate ID ASC; permutations give identical IDs |
| `test_exact_grade_advantage` | score88 Middle exact/all optional full =94.6 outranks score100 Senior overqualified =93.75 |

- [ ] Write the numerical tests through `test_both_optional_factors_absent`, asserting every active/excluded contribution and max.

The primary numerical oracle is literal and independently checkable:

```python
def test_score_contributions():
    fit = score_professional_fit(ScoringInput(80, 1.0, 1, 2, 2.0, 4.0))
    assert fit.assessment.score == 36.0
    assert fit.grade.score == 25.0
    assert fit.nice_to_have.score == 7.5
    assert fit.experience.score == 7.5
    assert fit.score == 76.0
    assert fit.assessment.max == 45.0
    assert fit.grade.max == 25.0
```

- [ ] Run `pytest -q tests/test_matching_rules.py -k 'score or experience or renormalization or optional'`; expect absent scoring interface failure.
- [ ] Implement `score_professional_fit`: frozen base weights, omit absent optional factors, normalize effective maxima, calculate factors/contributions once. Do not round intermediates or total; guard only floating-point epsilon at the 0–100 boundary, never hide a substantive calculation error by clamping.
- [ ] Run the focused numerical tests; expect PASS.
- [ ] Write bounds/invalid-input/ranking/grade-advantage tests from the remaining rows. Construct ties with different factor tradeoffs and close scores via tiny experience differences, not mocked rounded outputs.
- [ ] Run `pytest -q tests/test_matching_rules.py -k 'bounds or unrounded or ties or advantage'`; expect missing validation/ranking behavior failure.
- [ ] Implement `rank_candidates` with key `(-fit.score, -normalized_assessment_score, candidate_id)` and the specified precondition guards; no FSP flag or date input.
- [ ] Run `pytest -q tests/test_matching_rules.py`; expect PASS.
- [ ] Run `ruff check app/services/matching_rules.py` and `mypy app`; expect no violations.
- [ ] Commit declared files: `feat: add frozen professional fit scoring and ranking`.

A zero assessment does not mean a zero total: an eligible exact-grade candidate still earns grade contribution. Boundary tests check component endpoints and valid totals; do not invent GradeFit0 to manufacture total0.

### Task 6: Live matching API, batching, explainability and privacy

**Files**
- Create: `backend/app/services/matching.py`, `backend/tests/test_matching.py`.
- Modify: `backend/app/need_schemas.py`, `backend/app/routes/employer_needs.py`, `backend/tests/conftest.py`.

**Interfaces**
- Consumes: Task 2 `get_need`, Task 3 provider, Task 4 eligibility and Task 5 score/rank functions.
- Produces `FactorBreakdown(score: float, max: float, active: bool)`; `GradeBreakdown` additionally exact_match; `NiceToHaveBreakdown` additionally matched/total; `MatchBreakdown` has assessment/grade/nice_to_have/experience.
- Produces `EmployerCandidatePreview` with exactly candidate_id, display_name, specialization, verified_grade, skills, years_of_experience, normalized_assessment_score, assessment_verified_at, professional_fit_score, breakdown, matched_must_have_skills, matched_nice_to_have_skills, missing_nice_to_have_skills. Skill arrays use SkillOut with stable ordering. UTC-date handling follows the existing CandidateOut validator convention without using CandidateOut itself.
- Produces `MatchesPage(items: list[EmployerCandidatePreview], total: int, limit: int, offset: int)` and `match_need(db: Session, user: User, need_id: str, provider: CandidateAssessmentProvider, *, limit: int, offset: int) -> MatchesPage`.
- Produces route dependency `get_assessment_provider(db: Db) -> CandidateAssessmentProvider` returning `ProfileAssessmentProvider(db)`; override this dependency in boundary tests.
- Produces GET `/employer/needs/{need_id}/matches`, default limit20/max100/offset0, EmployerUser required, ACTIVE-only409, foreign/missing404.

- [ ] Write `test_matching_permissions_and_status`: anonymous401, Candidate403, foreign/missing404, DRAFT/CLOSED409, ACTIVE200 and standard error envelopes.
- [ ] Run `pytest -q tests/test_matching.py -k permissions_and_status`; expect missing endpoint404 in the ACTIVE case.
- [ ] Implement explicit response schemas and provider dependency in the declared files.
- [ ] Implement `match_need`: owner/state check, fresh parent/skill inputs, batched pool query with selectin candidate skills, one provider call for all pool IDs, eligibility, single pure scoring function, full deterministic rank, then pagination and explicit DTO construction. Preserve unrounded score in service/API; UI formats it later.
- [ ] Add the seventh thin route using these interfaces and existing no-store behavior.
- [ ] Run the permission/status test; expect PASS.
- [ ] Write the focused tests in the table below.
- [ ] Run `pytest -q tests/test_matching.py`; expect uncovered batching/privacy/breakdown cases fail before refinements.
- [ ] Complete only the missing orchestration/serialization behavior; serialize allowlisted attributes manually, never ORM dictionaries or CandidateOut.
- [ ] Run `pytest -q tests/test_matching.py tests/test_matching_rules.py tests/test_candidate_assessments.py tests/test_employer_needs.py`; expect PASS.
- [ ] Run existing auth/profile/assessment tests; expect unchanged behavior.
- [ ] Commit declared files: `feat: expose privacy-safe explainable need matching`.

| `test_matching.py` test name | Assertions |
| --- | --- |
| `test_matching_uses_injected_assessment_provider` | fake call contains pool IDs once; configured score affects fit; canonical trio stays unchanged |
| `test_matching_excludes_failed_hard_filters` | strong score100 missing must-have, unverified ideal stack, wrong spec, consentfalse and incompatible grade absent; no scoring call for excluded IDs |
| `test_matching_breakdown_and_optional_exclusion` | literal76 example and renormalized examples match Task 5 oracles; matched/missing arrays, exact_match, actual maxima and exclusion flags correct |
| `test_matching_preview_exact_allowlist` | exact set of preview keys above, nested SkillOut only id/name; contacts/consent/about/user_id/full surname/declared grade absent recursively; masked name `Анна И.` |
| `test_matching_allows_assessment_verified_at` | permitted UTC date survives; null date with a valid fake assessment remains informational and does not exclude |
| `test_matching_ignores_declared_grade_fsp_and_recency` | change declared grade, fsp_id, profile updated_at or assessment_verified_at independently; IDs/score/order unchanged |
| `test_matching_ranks_before_pagination` | first/second pages equal slices of full ranking; total equals eligible pool, not page size; top candidate can occur last in DB input |
| `test_matching_batches_queries` | SQL event counts for 5 and 50 candidates remain bounded, provider SELECTs follow ceil(n/500), no single-candidate SELECT loop or lazy per-skill loads |
| `test_matching_is_read_only` | GET issues no data mutation, no attempt/history query or synchronization/finalization; canonical trio unchanged |

For privacy fixtures populate User.email, candidate fsp_id, consent timestamp and about containing phone/Telegram markers; assert forbidden key names and marker values never appear. Since phone/telegram columns do not exist at this baseline, assert their absence without inventing them. Keep consent inside CandidateMatchInput and away from all response types.

Use the existing parent row lock for a coherent Need scalar/association read when matching overlaps editing: `get_need(..., for_update=True)` loads owner-scoped committed state before associated skills, and the request Session releases the lock on close. Do not commit inside GET or cache the loaded ORM entity across requests. The provider batch reads canonical state, not CandidateOut verification copied earlier; SQL filters are optimizations, with pure eligibility still authoritative.

### Task 7: ACTIVE-edit live recalculation and integrated regressions

**Files**
- Modify: `backend/tests/test_matching.py`, `backend/tests/test_employer_needs.py`; touch Task 2/6 services only if a failing behavior requires a correction.

**Interfaces**
- Consumes: existing POST/PUT/lifecycle/matches contracts; new TestClient requests after every successful/failed update, independent Session readback.
- Produces: regression proof of fresh committed inputs and parent-lock ordering; no new product API/type.

- [ ] Write `test_active_must_have_edit_changes_eligibility`: initial candidate present, successful PUT adds PostgreSQL absent from that candidate, next GET excludes it.
- [ ] Run that test; expect it to detect stale inputs if present. If already PASS, record that fact and do not claim an artificial RED.
- [ ] Write `test_active_nice_to_have_edit_changes_score_and_order`: candidates with equal initial inputs and different optional skills remain eligible, changed nice set reverses order with expected contributions.
- [ ] Write `test_active_grade_edit_changes_eligibility_and_fit`: Middle need includes Middle/Senior; editing to Junior excludes Senior and makes Middle GradeFit0.75; expected grade contribution reflects renormalization.
- [ ] Write `test_active_experience_edit_changes_score`: positive target changes factor/contribution on the next GET; null and zero edits exercise omit/full behavior.
- [ ] Write parameterized `test_failed_active_edit_preserves_matching`: invalid salary/unknown skill/overlap/empty must-have request attempts title and skill changes; independent readback AND fresh matches exactly retain original inputs/contributions/order.
- [ ] Write PostgreSQL-only `test_close_racing_update_preserves_closed_state`: two independent Sessions/connections, updating Session first preloads ACTIVE, controlled lock acquisition and bounded waits; close wins lock and commits, blocked update refreshes its cached state, raises ApiError with status409 and cannot reopen/change CLOSED. Avoid timing-only sleeps as proof.
- [ ] Run `pytest -q tests/test_matching.py tests/test_employer_needs.py`; expect PASS, with PostgreSQL-only test explicitly skipped on SQLite.
- [ ] Correct a demonstrated service regression, if any, through the existing transaction/locking interfaces; do not add a cache or alternate score path.
- [ ] Run the two test files with `TEST_DATABASE_URL`; expect actual concurrency/rollback tests pass, not skip.
- [ ] Run `pytest -q`; expect entire candidate/auth/assessment flow preserved, including canonical reset/restoration after specialization changes.
- [ ] Commit the explicit changed files: `test: cover atomic active edits and live matching`.

### Task 8: Explicit idempotent matching demo and documented API

**Files**
- Modify: `backend/app/seed.py`, `.github/workflows/checks.yml`, `README.md`.
- Create: `backend/tests/test_matching_seed.py`.

**Interfaces**
- Consumes: existing transactional `seed(db, *, demo=False, demo_password=None)`, Skill catalog, Task 1 models and Task 6 live matching.
- Produces backward-compatible `seed(db: Session, *, demo: bool = False, matching_demo: bool = False, demo_password: str | None = None) -> None`; CLI `--matching-demo` with the same production prohibition/password rules as --demo. This mode includes base demo identities plus separately named matching fixtures; ordinary --demo stays exactly as before.
- New records are create-if-absent by explicit demo email/Need ID; reruns never overwrite profile verification, password, Need edits/status/skills or existing assessment history.

Use the existing Python/Django/FastAPI/PostgreSQL/React/TypeScript/SQL catalog. Demo employer's ACTIVE BACKEND/MIDDLE need: must Python/FastAPI, nice PostgreSQL/Django, target3, sensible salary; include DRAFT and CLOSED need examples. Include the following small case set, not calibration/holdout imports:

| Case | Profile setup | Outcome |
| --- | --- | --- |
| exact | Middle, score88, both nice, experience3 | 94.6, ahead of senior |
| overqualified | Senior, score100, both nice, experience3 | 93.75 |
| optional gap | Middle, score90, one nice, experience1.5 | eligible, lower contribution |
| no experience | Middle, score90, all nice, experienceNone | eligible, ExperienceFit0 |
| wrong grade | Junior, score100, full stack | excluded |
| missing must | Middle, score100, missing FastAPI | excluded |
| unverified | all trio NULL, ideal skills | excluded; models cannot persist nonnull grade with null score |
| no consent | Middle, score100, full stack, consentfalse/timeNULL | excluded |
| wrong specialization | FRONTEND verified fixture/full stack | excluded |

Verified local fixtures set the canonical trio together with a fixed UTC verification date, as permitted by the spec. This is explicit demo preparation, not a write API or a claim that O1 implements assessment history. Original demo candidate remains unverified. Explain demo provenance in README.

- [ ] Write `test_matching_demo_is_explicit_and_preserves_base_demo`, `test_matching_demo_is_idempotent_and_preserves_edits`, `test_matching_demo_ranking_and_adversarial_cases`, `test_matching_demo_rejected_in_production`; assert ordinary demo user/catalog counts unchanged and trio constraints hold.
- [ ] Run `pytest -q tests/test_matching_seed.py`; expect missing matching_demo option failure.
- [ ] Add the opt-in CLI/function behavior inside the existing seed transaction without modifying Assessment Engine history/questions or existing users.
- [ ] Run `pytest -q tests/test_matching_seed.py tests/test_infrastructure.py`; expect PASS.
- [ ] Document all seven endpoints, own/role/Origin protections, error/page shapes, lifecycle/editing/live recalculation, frozen formula/renormalization, privacy and demo cases in README.
- [ ] Extend the existing Compose CI seed smoke to run `python -m app.seed --matching-demo` twice after its ordinary demo check; use existing password environment, never commit credentials. Backend/frontend jobs already discover new test files through their existing commands.
- [ ] Run the matching seed tests with PostgreSQL; expect idempotency and integrity PASS.
- [ ] Commit declared files: `feat: add explicit employer matching demo fixtures`.

### Task 9: Employer Needs frontend management

**Files**
- Create: `frontend/src/employer-needs.ts`, `frontend/src/components/employer-need-form.tsx`, `frontend/src/components/employer-needs-screen.tsx`, `frontend/tests/employer-needs.test.ts`.
- Create: `frontend/src/app/employer/needs/page.tsx`, `frontend/src/app/employer/needs/new/page.tsx`, `frontend/src/app/employer/needs/[id]/edit/page.tsx`.
- Modify: `frontend/src/components/auth.tsx` (Header only), `frontend/src/components/feedback.tsx`, `frontend/src/app/globals.css`.

**Interfaces**
- Consumes: existing `api<T>()`, AuthProvider/RoleGate, Feedback, Skill/grade/specialization types/labels and six Need endpoints; use existing `/skills` catalog.
- Produces feature TS `NeedStatus = "DRAFT" | "ACTIVE" | "CLOSED"`; `NeedWrite` mirrors backend fields with Grade/Specialization enums, salary_from/to strings, target_experience_years number|null, additional_requirements string|null and skill-ID string arrays. `EmployerNeed` mirrors NeedOut with ISO-string timestamps and Skill arrays; `Page<T> = {items: T[]; total: number; limit: number; offset: number}`.
- Produces `NeedFormValues = Omit<NeedWrite, "target_experience_years" | "additional_requirements"> & {target_experience_years: string; additional_requirements: string}`; salary strings are already preserved by NeedWrite. Empty optional text/target normalize to null, no owner/calculated fields. Server salaries are decimal JSON strings and converted only for display/form input, not fit calculations.
- Produces `validateNeedForm(values: NeedFormValues): Record<string, string>`; `needPayload(values: NeedFormValues): NeedWrite`; `needActions(status: NeedStatus): {edit: boolean; activate: boolean; close: boolean; matches: boolean}`.
- Produces API helpers `listNeeds(limit?: number, offset?: number): Promise<Page<EmployerNeed>>`, `getNeed(id: string): Promise<EmployerNeed>`, `createNeed(data: NeedWrite): Promise<EmployerNeed>`, `updateNeed(id: string, data: NeedWrite): Promise<EmployerNeed>`, `activateNeed(id: string): Promise<EmployerNeed>`, `closeNeed(id: string): Promise<EmployerNeed>` through the existing transport.
- Produces `NeedFormProps = {values: NeedFormValues; skills: Skill[]; busy: boolean; errors: Record<string, string>; onChange: (values: NeedFormValues) => void; onSubmit: () => void}`; `EmployerNeedForm(props: NeedFormProps)`; `EmployerNeedsScreen()`; `EmployerNeedEditor({needId?: string})`. A single editor composes create/edit, wrapped in RoleGate(role EMPLOYER).
- Produces exported presentational `NeedsListView({items, loading, error, onRetry, onAction})`, with items `EmployerNeed[]`, loading boolean, error unknown, retry `() => void`, action `(id: string, action: "activate" | "close") => void`.
- Produces exported `NeedEditorView({need, loading, error, form, onRetry})`, with need `EmployerNeed | null`, loading boolean, error unknown, form `NeedFormProps`, retry `() => void`; this view renders the CLOSED block without router/auth hooks and is directly SSR-testable. `EmployerNeedEditor` owns fetch/navigation, not the presentational view.
- Produces `needsNavigationVisible(role: Role | null): boolean`, used by existing Header and tested for Employer/Candidate/anonymous visibility.

- [ ] Write named Node tests: `need form rejects empty title and must-have`, `need form rejects salary order and nonfinite negative experience`, `need form rejects duplicate and overlapping skills`, `need payload excludes ownership and calculated fields`, `need API uses cookie transport and correct methods`, `need statuses expose correct actions`, `needs navigation is employer only`, `ACTIVE editor remains editable`, `CLOSED editor is blocked`, `need list renders loading empty and API error states`, `need form disables invalid or busy submit`. Render exported views/forms, not auth/router orchestration components.

Pin action/role oracles in `employer-needs.test.ts`:

```typescript
assert.deepEqual(needActions("DRAFT"), {edit: true, activate: true, close: false, matches: false});
assert.deepEqual(needActions("ACTIVE"), {edit: true, activate: false, close: true, matches: true});
assert.deepEqual(needActions("CLOSED"), {edit: false, activate: false, close: false, matches: false});
assert.equal(needsNavigationVisible("EMPLOYER"), true);
assert.equal(needsNavigationVisible("CANDIDATE"), false);
assert.equal(needsNavigationVisible(null), false);
```

Other test assertions: invalid field key is present in validateNeedForm errors; valid data errors equal `{}`; empty target payload is null and zero is0; payload keys exactly match NeedWrite; busy/invalid form markup has disabled submit; CLOSED editor markup contains no form; ACTIVE contains one; state markup has role=status/alert and retry button where applicable. Fetch mocks assert exact URL/method/body and restore global fetch in finally.

- [ ] Run `node --import tsx --test tests/employer-needs.test.ts`; expect missing module/component behavior failure.
- [ ] Implement DTO/helper/API functions in `employer-needs.ts`; validate numeric strings before Number conversion (empty target → null; "0" → 0), send scalar strings for Decimal salary, derive no owner/status/calculated fields.
- [ ] Run focused helper/API tests; expect PASS.
- [ ] Implement the controlled form for every NeedWrite field with disjoint skill checkboxes, validation/Feedback, fieldset disabled while saving and disabled invalid submit. Do not initialize edit controls with create defaults before GET finishes.
- [ ] Implement list/editor orchestration and exported views with GET loading/empty/error-retry, own results, simple previous/next pagination, save success/navigation, DRAFT/ACTIVE edit and CLOSED block. A `profile_not_found` response links to existing `/employer/edit` rather than leaving a retry-only dead end. Mutation failure preserves current form/committed display; backend remains authoritative on stale CLOSED status.
- [ ] Add the three thin pages; dynamic edit awaits params and keys the editor by id, following existing assessment dynamic page convention.
- [ ] Add employer-only navigation in the existing Header in `auth.tsx` and minimal responsive status/action styles; no Candidate links/actions to these screens.
- [ ] Run `node --import tsx --test tests/employer-needs.test.ts`; expect PASS.
- [ ] Run `npm test`, `npm run lint`, `npm run typecheck`; expect existing assessment/proxy tests preserved and no TS/ESLint errors.
- [ ] Commit explicit declared frontend files: `feat: add employer need management screens`.

Tests use real presentational components/validation helpers, not a new mocked UI framework. RoleGate itself is reused rather than reimplemented; test action visibility through the exported view and verify actual role redirects at the browser gate.

### Task 10: Employer matching frontend and safe details

**Files**
- Create: `frontend/src/components/employer-matches-screen.tsx`, `frontend/src/app/employer/needs/[id]/matches/page.tsx`, `frontend/tests/employer-matches.test.ts`.
- Modify: `frontend/src/employer-needs.ts`, `frontend/src/app/globals.css`, `README.md`.

**Interfaces**
- Consumes: Task 6 preview/breakdown/page contract, Task 9 Need DTO/API/state patterns and shared grade/specialization labels.
- Produces distinct TS `EmployerCandidatePreview` mirroring Task 6 exact fields, with nonnullable Grade/normalized numeric score, nullable number experience and nullable ISO-string assessment_verified_at; `FactorBreakdown = {score: number; max: number; active: boolean}`, grade additionally exact_match boolean, nice additionally matched/total numbers; `MatchBreakdown` contains four named factors. `MatchesPage = Page<EmployerCandidatePreview>`; no extension of full CandidateProfile type.
- Produces `getMatches(id: string, limit?: number, offset?: number): Promise<MatchesPage>`; `EmployerMatchesScreen({needId: string})`; exported `MatchingView({need, result, loading, error, onRetry})`, with need EmployerNeed|null, result MatchesPage|null, loading boolean, error unknown and retry `() => void`; `MatchCard({candidate: EmployerCandidatePreview})`. Exported views have no router/auth hooks.
- UI renders server scores to one decimal, server normalized assessment out of100, skill matches/gaps, experience/null, permitted verification date in Russian and expandable `<details>` contributions with actual max/active flags. It never scores or sorts locally.

- [ ] Write named tests: `matching renders loading`, `matching renders empty pool`, `matching renders API error with retry`, `matching preserves ranked candidate order`, `matching renders effective breakdown and excluded factors`, `matching renders assessment verification date`, `matching preview renders masked name and no contacts`, `matching blocks non ACTIVE need`, `matching API forwards limit offset and errors`.

Pin SSR oracles: role=status while loading, empty explanatory text for `{items: [], total: 0}`, role=alert and retry on ApiError, rendered name positions preserve input order, server76 displays `76.0`, renormalized maxima display server values, excluded factors are marked excluded, and verification timestamp `2026-09-18T12:00:00Z` displays `18.09.2026`. Private sentinel values and contact actions must be absent; do not add a private field to the typed preview merely to test rendering. Use an exact API fixture allowlist and a separate serialized unknown-property injection test if testing defensive rendering.

- [ ] Run `node --import tsx --test tests/employer-matches.test.ts`; expect missing preview/view/interface failure.
- [ ] Add the feature preview types and getMatches helper in `employer-needs.ts`; do not import full candidate response types.
- [ ] Implement MatchCard and MatchingView with «Соответствие», assessment, self-declared skill lists, missing optional markers, candidate experience and «Компетенция подтверждена: …». Omitted factors show exclusion rather than full contribution; dates never feed any ordering.
- [ ] Implement RoleGate/loading/retry and ACTIVE-only matching orchestration, plus thin async-params keyed page. Provide previous/next server pagination, respect total and preserve server order; refresh GET after returning from edits, no persistent client ranking cache.
- [ ] Add responsive card/details rules and README manual steps for create/edit/activate/live matching/close/forbidden access; do not add charts, animations, contact or invitation actions.
- [ ] Run `node --import tsx --test tests/employer-matches.test.ts`; expect PASS.
- [ ] Run `npm test`, `npm run lint`, `npm run typecheck`, `npm run build`; expect PASS including existing candidate assessment pages.
- [ ] Commit declared files: `feat: render explainable employer matching results`.

## Final verification gate (after all implementation tasks, not authorized now)

This gate checks completed behavior; it is not another product implementation task and does not manufacture a failing test after implementation. Record commands, runtime versions, actual exit codes, counts and skips. Fix demonstrated failures through the owning task, then repeat only affected checks before the final full gate.

- [ ] Inspect `git diff origin/main...HEAD` and confirm only O1-owned changes; inspect staging and run `git diff --check`.
- [ ] Run the Codex Security security-diff workflow for the immutable implementation diff, focusing on owner scoping, mass assignment, Origin/session reuse, canonical assessment provenance, numerical bounds and preview allowlist; fix validated issues without scope expansion.
- [ ] Verify local runtime availability using `python --version`, `node --version`, `docker version` and `docker compose version`; Python3.13+/Node22+ and a running Docker Engine are prerequisites, not claims based on historical observations.
- [ ] Run `docker compose up --build -d --wait --wait-timeout 180` from the root; expect all configured services healthy. Use existing `.env`/example setup without printing secrets.
- [ ] Run `docker compose exec backend alembic upgrade head`; expect actual O1 revision applied above0002.
- [ ] Run `docker compose exec backend alembic check`; expect “No new upgrade operations detected.”
- [ ] Run PostgreSQL tests in the existing backend image: `docker compose exec -T backend python -c "import os, subprocess; env = dict(os.environ, TEST_DATABASE_URL=os.environ['DATABASE_URL']); raise SystemExit(subprocess.call(['pytest', '-q'], env=env))"`. The existing fixture creates and drops a unique test schema per test on that PostgreSQL connection; all migration round-trips operate on those schemas. Expect full suite PASS including check/FK constraints and concurrency tests. Do not downgrade the populated application schema for testing; if the account lacks schema privileges, use the dedicated test database setup from CI and record the environment change.
- [ ] Run backend `pytest -q`, `ruff check .`, `ruff format --check .`, `mypy app` in its Python3.13 environment; expect PASS, no formatting drift and no type errors. Record PostgreSQL and SQLite runs distinctly.
- [ ] Run frontend `npm ci`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`; expect successful actual commands, not inferred green status.
- [ ] Run `docker compose exec backend python -m app.seed --demo` twice; expect original two-account behavior preserved.
- [ ] Run `docker compose exec backend python -m app.seed --matching-demo` twice; expect no duplicates or overwrites and the documented demo ranking.
- [ ] Check `/health` and the frontend `/api/skills` proxy using the actual configured ports from `compose.yaml`; expect healthy backend and catalog JSON.
- [ ] Perform browser smoke as employer: fill profile, create with must/nice skills, edit DRAFT, activate, see94.6 exact Middle ahead of93.75 Senior, details/date, edit ACTIVE and see changed next matching, reject invalid edit, close and confirm edit/matches blocked. Verify 375px layout, busy submit, empty/error/retry states and page navigation.
- [ ] Perform browser smoke as candidate/anonymous: employer screens redirect through RoleGate; direct API access401/403; existing profile/auth/assessment flow still works.
- [ ] Read the actual CI workflow: backend PostgreSQL migration/check/pytest/Ruff/mypy, frontend lint/typecheck/test/build, Docker health/seed/proxy smoke must execute these new tests; record CI run evidence separately from local checks.
- [ ] Review privacy responses in API/browser network output: exactly allowlisted preview fields and verification date, no consent/contact fields. Confirm no probability copy and no frontend scoring code.
- [ ] Commit only any verified final documentation/check fixes with explicit paths; leave a clean working tree or identify unrelated changes.

The original implementation delivery scope eventually includes pushing the branch and creating/attaching a PR to main without merge. That happens only after execution authorization and this gate; it is not part of the present plan review. Do not create a PR, deploy, merge or start execution when submitting this plan.

## Specification coverage and plan self-review

| Approved spec requirement | Owning task / evidence |
| --- | --- |
| Foundation/auth/error/catalog reuse; normalized Need persistence | 1–2, existing auth/profile regression |
| Ownership, validation, lifecycle, ACTIVE editable, CLOSED409 | 2, parameterized API tests |
| Atomic updates and lifecycle races | 2 rollback tests; 7 independent readback/PostgreSQL lock test |
| Canonical assessment ownership, read-only batch boundary, no snapshots | 1 migration preservation; 3 provider SQL/write tests; 6 boundary/read-only API tests |
| Consent/spec/verified grade/compatibility/must-have/score hard filters | 4 unit matrix; 6 adversarial API; 8 demo |
| Frozen formula, cap/missing/zero experience, renormalization | 5 literal numeric oracles; 6 breakdown API |
| Deterministic unrounded ranking and post-ranking pagination | 5 ranking; 6 pagination; 8 grade-advantage demo |
| No declared grade, FSP or recency effect; date informational | 4 input exclusions; 5 rank key; 6 invariance; 10 rendering |
| Exact preview allowlist, consent/contacts/private fields excluded | 6 recursive privacy API assertions; 10 separate TS DTO/card tests |
| Live recalculation after successful/failed ACTIVE edits | 7 four focused edits and failed-update match comparison |
| Employer list/form/matches, status/actions, state/validation/responsive UI | 9–10 Node tests; final browser gate |
| Preserved base seed; idempotent explicit adversarial demo | 8 tests, README and Compose CI smoke |
| Migration chain/downgrade/check/PG integrity, backend/frontend/CI/Docker | 1; final actual verification gate |
| No Invitations/Testing Engine internals/production deployment/merge | Global constraints and file-map exclusions |

Self-review decisions recorded while preparing this plan:

- Keep a generated Alembic revision path instead of inventing0003 or modifying0002; the upgrade/downgrade boundary remains explicit.
- Add score-zero/invalid-provider and canonical-trio consistency tests; persisted partial verification is not a valid fixture under the real0002 constraints.
- Add failed-commit rollback and PostgreSQL lock-order tests alongside validation tests; validation-only tests cannot prove transactional atomicity/concurrency.
- Add exact nested preview-key checks and contact marker-value checks; merely omitting UI fields cannot prove API privacy.
- Keep sorting before pagination and test same-displayed-decimal scores; displayed rounding cannot drive rank.
- Separate existing Node SSR/helper proof from browser event/navigation proof; no additional test stack.
- Scan function/DTO names across tasks: all consumes reference the producing interfaces above; validated eligibility fields are nonnullable, Header modifications target the real `auth.tsx`, and presentational editor tests do not require unavailable router/browser mocks. No undeclared repository, snapshot, scoring copy or assessment writer is introduced.
- Each task has named tests/oracles, a focused command, expected RED/GREEN behavior and a scoped future commit; regression-only tests honestly allow existing PASS instead of inventing failures.

This file contains implementation instructions, not implementation bodies. The approved spec is unchanged. After committing/pushing this plan, stop and await team review; do not invoke an execution skill or start TASK O1 production implementation.
