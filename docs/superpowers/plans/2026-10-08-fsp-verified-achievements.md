# Verified FSP achievements implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline. Steps use checkbox syntax for tracking.

**Goal:** Implement P4 verified mock FSP evidence and Ranking V2 without changing Professional Fit, Assessment or invitation lifecycle/privacy.

**Architecture:** Candidate-owned entered identifiers stay separate from server-owned verification and normalized achievement rows. A deterministic fixture provider feeds atomic, parent-row-locked verification transactions. Ranking V2 wraps the existing single-candidate evaluator; historical invitation fields remain optional when reading V1 snapshots.

**Tech Stack:** Existing Python 3.13, SQLAlchemy, Alembic, FastAPI/Pydantic, PostgreSQL 17, Next.js/React/TypeScript and existing test tools. No new dependency.

**Spec:** Sava's complete P4 document supplied in `C:/Users/olego/.codex/attachments/4a20e727-7caa-4423-80b9-5e5e2f8d28f5/Pasted text.txt`, plus the user's P4 Execution instructions.

## Global constraints

- Base: `f4fc87ccad953979be82cbe8118142d74be50c1d`; branch: `feat/fsp-verified-achievements`.
- One migration after `a812e4c79b60`; preserve existing data and one head.
- Participation = `min(distinct_competitions, 3) / 3 * 30`; result qualities = 0, 0.50, 0.80, 1.00.
- Achievement = participation + best result quality * 70, bounded 0..100; bonus = achievement / 100 * 5.
- Ranking = `0.95 * professional_fit_unrounded + fsp_bonus`.
- Sort unrounded ranking, unrounded Professional Fit, assessment descending, then candidate ID ascending.
- Assessment/question bank/thresholds/cooldown/selection/P3 docs and frozen holdout evidence are unchanged.
- Mock provider only: no runtime network; no claim of real registry identity authentication.
- Salary is RUB gross, «до вычета налогов»; no new salary mode.
- Push and PR only after required gates pass. Do not merge.

## Review focus

- Refresh failure must preserve the entire previously verified snapshot (Task 2 rollback test).
- Two accounts concurrently claiming the same verified identifier must produce one winner (Task 2 PostgreSQL test).
- Verification/edit races must not retain evidence for a changed identifier (Task 2 parent-lock test).
- Old invitation snapshots must remain readable without synthesizing historical V2 scores (Task 3 legacy test).
- Fabricated private provider/contact fields must not render in employer UI (Task 4 marker test).

## Task 1: Evidence persistence, provider and pure scoring

**Files:** `backend/app/models.py`, one new migration, `backend/app/services/fsp_registry.py`, `backend/app/services/fsp_rules.py`, `backend/app/content/fsp_registry_mock.json`, `backend/tests/test_fsp_rules.py`, `backend/tests/test_fsp_persistence.py`.

**Interfaces:** `FspRegistryProvider.lookup(fsp_id: str) -> RegistryProfile | None`; `MockFspRegistryProvider`; immutable achievement DTOs; `score_achievements(Iterable[tuple[str, FspResultLevel]]) -> FspSignal`.

- [ ] Write and run failing provider/scoring/model tests: unknown/empty IDs, all levels, multiple competitions, duplicate competition entries, 10/30/80/100 examples, scope/discipline/date invariance and max bonus 5.
- [ ] Add normalized server-owned evidence, timestamp/identity consistency checks, unique verified identifier, achievement foreign key/uniqueness/placement checks; implement fixture provider and pure scoring.
- [ ] Run focused tests and migration upgrade/downgrade/upgrade with existing rows retained.

## Task 2: Candidate verification transactions/APIs

**Files:** `backend/app/fsp_schemas.py`, `backend/app/services/fsp.py`, `backend/app/routes/fsp.py`, `backend/app/main.py`, `backend/app/services/profiles.py`, `backend/tests/test_fsp.py`, `backend/tests/test_fsp_concurrency.py`.

**Interfaces:** GET `/candidate/fsp`, POST `/candidate/fsp/verify`, POST `/candidate/fsp/refresh`, DELETE `/candidate/fsp/verification`; verify current stored identifier only, empty extra-forbidden mutation body. `load_signals(db, candidate_ids)` reads allowlisted aggregate evidence.

- [ ] Write and observe failing tests for verify/refresh/unlink/status, role/Origin/profile ownership, unknown IDs, rollback, mass assignment and atomic ID change invalidation.
- [ ] Implement one locked profile transaction; replace achievements and timestamps atomically; translate unique violations to a generic conflict; preserve canonical assessment.
- [ ] Run focused API tests and PostgreSQL races with Events/Barriers, separate connections, bounded timeouts and independent readback.

## Task 3: Ranking V2 and invitation snapshots

**Files:** `backend/app/services/matching.py`, `backend/app/need_schemas.py`, `backend/app/invitation_schemas.py`, `backend/app/services/invitations.py`, matching/invitation regression tests and `backend/tests/test_fsp_matching.py`.

**Interfaces:** `evaluate_candidate(..., *, fsp: FspSignal = unverified) -> EvaluatedCandidate | None` retains existing eligibility and fit calls; V2 sort uses unrounded scores. Employer aggregate allowlist: `fsp_verified`, `fsp_achievement_score`, `fsp_bonus`, `competition_count`, `best_result_level`, `ranking_score`.

- [ ] Establish baseline, then write failing tests for unverified/no-FSP matching, unchanged hard filters/fit, deterministic ties, stronger fit, safe serialization, immutable and legacy snapshots.
- [ ] Extend the shared evaluator and both callers; invitation send reads evidence under its existing candidate lock; old snapshots accept absent P4 fields.
- [ ] Run Matching and invitation regressions; update exact allowlist expectations only for the explicitly authorized P4 fields.

## Task 4: UI, salary and documentation

**Files:** `frontend/src/fsp.ts`, `frontend/src/components/fsp-profile.tsx`, candidate/Matching/history components, public types, API proxy DELETE export, salary labels, frontend tests, `docs/fsp-integration-and-ranking.md`.

**Interfaces:** Existing `api()` transport, typed current-state responses, explicit verify/refresh/unlink controls, mock label; aggregate-only employer ranking explanation, send-time history explanation.

- [ ] Write and run failing API/render/handler tests, including error/retry/busy behavior and private marker exclusions.
- [ ] Implement explicit controls with server response replacing state, no automatic verification; distinguish entered ID, verified evidence, Professional Fit and Ranking Score.
- [ ] Update relevant salary text to RUB gross and document formulas, fixture IDs, privacy, assessment independence and prototype limitations.
- [ ] Run frontend focused/full tests, lint, typecheck and build.

## Task 5: Final verification, review and delivery

- [ ] Run full SQLite and PostgreSQL 17 suites, all required concurrency tests without skip, Ruff/format/mypy, Alembic current/heads/check and round-trip, npm ci/lint/typecheck/test/build, diff check.
- [ ] Confirm Docker target volumes are disposable before any volume deletion; rebuild healthy project, verify PG 17.x, repeat existing seeds.
- [ ] Perform real desktop and 375px browser flows: enter ID/verify/rank/invite/accept/contact unlock, unverified no bonus, responsive privacy states.
- [ ] Review whole diff for frozen files and security; obtain one fresh whole-branch code review and fix current-scope important findings with regression tests.
- [ ] Stage explicit paths, make logical scoped commits, push, independently verify remote and create the specified PR to main only after all mandatory gates pass. Stop for human review.
