# P8-B1 — Critical Backend Remediation

## Provenance and scope

Baseline: `17b8f656fdc648eae2a2af9a60fbb6ba353370f9`, current GitHub main
when work started on 2026-10-10. GitHub confirmed PR #15 merged at that SHA.
Branch: `fix/p8-b1-backend-remediation`, in a new isolated worktree.
Tested code commit: `b823df5d3246e71da915898f131b1dcf84dd01c6`.
Before publication, GitHub/main had advanced to
`02db6f3ca6d6dff9b11191f1b9cbb02067ce6f11`. Fetch and ancestry/diff checks
confirmed its only additional commit changes `frontend/Dockerfile` and
`.github/workflows/checks.yml` for logo assets: no backend changes or overlap.
The branch retains the verified starting baseline; no rebase/merge was performed.
The full local checks below cover the tested branch, not a simulated merge build
or the newer Docker/CI logo check.
Primary checkout, P8-B0/P8-A0 workspaces, manual project and shared databases
were not used for remediation. No foreign container or volume was modified.

Analysis source: [Draft PR #16](https://github.com/ssavantonoff/fsp-platform/pull/16),
audit commit `9b5a73e5f754e21fef03a45cacba662877bb8d3a`, audit baseline
`acead7a5ea8eb93c1344107440ddb6c16b42173f`, findings 001–003 and Appendix B1–B3.
The audit report/branch were not edited or merged. Its older filtered 793-test
result is not credited to this remediation. This is not a new broad audit.

All three defects were reproduced on the actual post-PR-15 main before fixing.
The final regression files were also copied into a separate canonical export of
unfixed main: **14 selected target failures, zero setup errors and skips**.
No production fixes were copied into that export.

## 001 / P1 — Coherent Matching inputs

**Root cause:** READ COMMITTED gives the profile, select-in skills, canonical
qualification and FSP SELECTs different snapshots. Authentication already starts
the request Session transaction; `no_autoflush` does not make its reads repeatable.
The old consent value could combine with a later Assessment PASS.

**Fix:** new `services/matching_snapshot.py` reads scalar profile values, canonical
grade/score/time, candidate skill links, verified FSP evidence and required Skill
catalog in one `UNION ALL` statement. Streams have additive cardinality rather
than skills × achievements multiplication. Assembly does not assume branch order.
Scalar projections avoid stale ORM identity-map values and retain caller dirty
objects. `ProfileAssessmentProvider.matching_snapshot()` supplies the preloaded
frozen assessment values to the same instance/method, restoring state in `finally`.
Its normal batch behavior and the shared Invitations dependency stay unchanged;
FakeProvider overrides remain honored.

| Evaluated option | Decision |
|---|---|
| Transaction-scoped read-only REPEATABLE READ | Correct before the first query, with all loaders bound to that Session. Too late on the authenticated Session. A dedicated Session holds a second pool connection while auth holds the first, risking saturation/timeouts; a route-specific auth transaction would need to preserve direct calls and the provider shared by Invitations. |
| One projected query at READ COMMITTED | Selected: same statement snapshot and existing connection; no new isolation/schema/API change, candidate locks or child cross-product. |

The existing immutable Need criteria are retained for the invocation. Concurrent
ACTIVE edits remain allowed; a writer can commit during the reader checkpoint,
while fresh calls read updated criteria. No Architecture Stop Gate was crossed.
These guarantees follow [PostgreSQL 17 isolation](https://www.postgresql.org/docs/17/transaction-iso.html)
and [SQLAlchemy Session transaction behavior](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html).

**Regressions:** `test_p8_matching_snapshot.py` checks three real API sequences
`[true,null,null] → [false,null,null] → [false,MIDDLE,100]`: Red `total=1`, score100;
Green `total=0` and no items. Controlled SQL checkpoints cover skills/spec changes,
consent grant without qualification, qualification/experience/nice-skill/FSP changes,
FSP reset and achievement replacement. Three-candidate rank changes retain a coherent
old offset page and fresh new order. Stale/dirty ORM state and provider exception
cleanup are tested. Existing Matching query guards require <=4 queries and one
shared qualification/skills/FSP statement, including 501 candidates; privacy,
criteria, sorting and pagination assertions remain.

Production files: `services/matching.py`, `services/matching_snapshot.py`,
`services/candidate_assessments.py`. Existing `test_matching.py` SQL-shape guards
were adapted to coherent reads without changing business/privacy expectations.

## 002 / P2 — Atomic consent/FSP update

**Root cause:** consent timestamp changed before its boolean; FSP DELETE could
autoflush the inconsistent pair against `consistent_consent`. Four initial consent
true/false × verified/unverified cases all returned HTTP 500 on main.

**Fix:** align the boolean immediately after the existing timestamp rule, before
FSP SQL can autoflush. This retains autoflush, constraints, owner lock and evidence
reset. Complete assignment of the pair is smaller than introducing another
no-autoflush preparation region; no global flush policy change is needed.

`test_p8_profile_atomic.py` requires HTTP 200 for all four real PUT branches, correct
boolean/timestamp and ID, cleared FSP metadata/evidence and exact readback. Four
further injected **post-flush** failures require HTTP 409 and complete old profile,
skills and FSP state. No partial operation persists. File: `services/profiles.py`.

## 003 / P2 — Coherent response DTOs

**Root cause:** post-commit scalar refresh and select-in relations can read A/B
versions after the write lock has been released. The same parent/relationship
read split existed in Candidate GET, Need GET and individual list NeedOut values.

**Fix:** mutations flush and refresh under the existing parent lock, copy a detached
CandidateOut/NeedOut, commit, then return success. Refresh before commit preserves
database timestamp representation and skills ordering. Both flush and commit errors
retain rollback/409 mapping. DTOs copy values; Pydantic models are not newly frozen.
GET/list use one joined eager statement plus `unique()`. Need's mutation
`for_update=True` owner-lock/select-in path remains. NeedPage count/items remain
separate SELECTs; a whole-page snapshot is not claimed.

`test_p8_response_snapshot.py` has four real concurrent PUT cases (Candidate/Need,
expire_on_commit false/true): Red `(A scalar,B skills)`; Green returns a complete
version even when B commits before A's HTTP response finishes. Three controlled
GET/list races have the same Red/Green proof. Two commit-failure controls prohibit
successful prepared DTOs and verify full rollback. Bounded Events/SQL checkpoints
and distinct PostgreSQL PIDs prove concurrency; no arbitrary sleeps were added.

Files: `services/profiles.py`, `services/employer_needs.py`,
`routes/employer_needs.py`. Direct callers of new mutation DTO return types were
inspected; public schemas stay unchanged. Existing `test_employer_needs.py` fault
injection now identifies the target write by id/values after explicit flush clears
`Session.dirty`; its injected-fault/409/full rollback expectations remain.

## Verification

Own native PostgreSQL **17.11**, separate loopback port/database/data directory,
UUID schemas; Python 3.13.7 with explicit UTF-8. Docker initially failed to start;
the user repaired it and read-only status confirmed engine 29.4.3. Evidence is
native PostgreSQL, not Docker/CI/production proof. Frozen files and checks were
not changed. On this host checkout and initial export converted LF to CRLF;
tests use a separate `git -c core.autocrlf=false archive` export with only scoped
source/test edits overlaid. Reviewed Assessment bank source SHA256 stays
`76cda12d6358f14da84cce0ac584035ab189ae7a2f43e18d1e3cfed41276023c`.
Hash prerequisite failures were not credited as Red.

| Check | Result |
|---|---|
| 001 initial Red / focused Green | 3 target failures → 64 passed |
| 002 initial Red / focused Green | 4 HTTP500-versus-200 failures → 78 passed |
| 003 confirmed Red | 7 mixed-version failures, 2 rollback controls passed |
| Final shipped tests on unfixed main | 14 target failures; 0 errors/skips |
| New regressions / PG17 Europe-Moscow session | 28 passed, 0 failures/skips |
| Regressions + affected integration controls / PG17 UTC | 38 passed, 0 failures/skips; PID traces retained |
| Full backend / PostgreSQL17 | 1073 passed, 0 failures/errors/skips; 1241.50s; no file exclusions |
| Full backend / SQLite | 1034 passed, 0 failures/errors, 39 PostgreSQL-only skips; 872.57s; no file exclusions |
| Frontend unit/API contract tests | 184 passed, 0 failures/skips |
| Frontend typecheck | Passed |
| Frontend lint / production build | Passed on Node 24.1.0; Next.js production build completed |
| Ruff check / format | Passed; 79 formatted Python files |
| mypy app | Passed; 39 source files |
| Alembic | Isolated PG17 upgrade head + check passed: no new upgrade operations; head c3d9b7e21a40; existing round-trip tests also included |
| Independent review | Final immutable code commit reviewed; no actionable finding; rollback injection and JUnit independently checked |
| Codex Security | Final immutable range completed: all 11 changed source/test files, complete diff coverage, 0 findings/deferred items |
| git diff --check / scope | Passed; exact 11 source/test paths plus this report; commit blobs match fully tested LF runtime |

First existing integration attempt: **519 passed / 9 failed**. Eight timestamp-offset
failures in unchanged Assessment/Invitations also failed on untouched main. Only the
own test DB was set to UTC; those sources/assertions were not changed. The ninth was
the obsolete fault-injection dirty-set guard. All ten affected controls plus28 new
regressions then passed. Earlier targeted attempts exposed timestamp representation,
an equal-bonus FSP fixture and a checkpoint intercepting precommit refresh; these
were corrected and failed attempts are retained, not presented as Green.

The final 11 source/test files were compared byte-for-byte (canonical LF) with
the completed full-suite runtime before the code commit. Existing warnings:
PostgreSQL has one Starlette TestClient deprecation warning; SQLite has five
warnings, including deprecated Python datetime adapters. No warning was hidden
by disabling a check or changing frozen artifacts.

### Deterministic PostgreSQL interleavings

The controlled events pause after the initial SELECT or after A's actual commit,
then allow an independent writer Session to commit before the reader continues.
Event timeouts are bounded failure guards, not delay-based race scheduling.
These sample traces are from `targeted-and-integration-utc.log`:

| Scenario | Reader / writer backend PID | Observed invariant |
|---|---|---|
| Skills + specialization change | 24372 / 23592 | Paused read returns coherent old eligibility; fresh call reads new state |
| Qualification/experience/nice-skill/FSP change | 15924 / 19604 | Old Professional Fit, FSP bonus and Ranking Score stay together; fresh call changes coherently |
| FSP unlink/reset | 24024 / 23776 | Old verified evidence remains coherent for paused call; new call sees reset |
| Achievement replacement | 23880 / 17956 | No mixed old verification/new achievement score |
| PUT Candidate, expire_on_commit=false | 23824 / 21468 | B commits before A's HTTP response completes; A returns its complete committed DTO |
| PUT Need, expire_on_commit=false | 14660 / 23824 | A scalar/requirements remain one version; final DB is B |
| PUT Candidate / Need, expire_on_commit=true | 8916 / 15524; 23228 / 24056 | Same DTO guarantee with ORM expiration enabled |

The primary Matching race repeats three times through real profile/Assessment/
Matching API routes. The test independently reads each committed state and asserts
none was eligible: consent is revoked before Assessment PASS commits. Correct
Matching response is empty, not an expected defective response. Ranking/pagination
tests compare the entire frozen old page and the fresh changed page. PUT tests
assert both responses and final B state; GET/list races require one complete
scalar/relation version. Four profile fault cases and two response commit-failure
controls require rollback and prohibit a successful partially committed response.

### Exact SQLite omissions

The PostgreSQL run executes all these cases. SQLite skips only unsupported
concurrent-connection/row-lock checks and its NaN-to-NULL integrity case:

| Test file | PostgreSQL-only cases skipped by SQLite |
|---|---:|
| test_assessments.py | 1 |
| test_auth.py | 1 |
| test_employer_needs.py | 1 |
| test_fsp_concurrency.py | 3 |
| test_infrastructure.py | 1 |
| test_invitation_concurrency.py | 7 |
| test_invitation_persistence.py | 6 |
| test_matching.py | 3 |
| test_p8_matching_snapshot.py | 9 |
| test_p8_response_snapshot.py | 7 |
| Total | 39 |

Previously excluded dataset/golden/review/Assessment bank/diversity files were
included this time. P6 checks validate artifact structure, preservation and
Stage 1/`--check` behavior using temporary copies; they do not run Stage 2 scoring
evaluation or change human-review labels.

Local evidence under ignored `.cache/p8-b1/`: `001-red-lf.xml`, `002-red.xml`,
`003-red-confirmed.xml`, `final-tests-baseline-red.xml`, `all-targeted-verified.xml`,
`targeted-and-integration-utc.xml`, corresponding logs and full-suite JUnit/logs.
Cache/runtime artifacts are not shipped. Reproduce on independent PG17 via the
standard `TEST_DATABASE_URL` fixture configuration:

```text
python -m pytest tests/test_p8_matching_snapshot.py tests/test_p8_profile_atomic.py tests/test_p8_response_snapshot.py -q
python -m pytest -q
```

For Red, copy only final regression files into a separate canonical baseline
export and select the primary Matching, four combined-update and seven response
cases. Do not copy fixes or alter publication/frozen integrity checks.

Run from that unfixed export's backend, with PG17 configured:

```text
python -m pytest tests/test_p8_matching_snapshot.py tests/test_p8_profile_atomic.py tests/test_p8_response_snapshot.py -k "never_combines_old_consent or combined_consent_and_fsp_id_is_one_successful or concurrent_put_response or get_response_uses_one_scalar" -q
```

Actual final Red assertions: Matching `1 == 0` (three cases), profile
`500 == 200` (four), response `(A scalar, B skill IDs)` outside the two real
versions (seven). The saved run selected those 14 cases by node ID and recorded
14 failures, zero errors or skips. The `-k` selector above reproduces that case
set while deselecting the other controls. The same three complete files pass
all 28 cases on the fixed commit.

## Preserved boundaries and risk

Assessment business source, matching rules/matrix/hard filters/frozen weights,
FSP scoring/bonus, Invitations/contact policy, models, API schemas, migrations,
frontend and frozen validation/human-review artifacts are unchanged. Nine existing
Matching rule/output function bodies match baseline ASTs. P3, Potential and Product
Decision Required findings were not fixed. P6-B2 Stage2 was not executed; structural
and artifact-integrity unit checks are not runtime ranking evaluation.

Matching still materializes the pool before ranking/pagination. Wider additive
rows may change memory/wire costs: no production load benchmark or speed claim.
DTO copy/refresh extends part of the existing parent-lock section. Guarantees rely
on supported writers respecting that lock and request-scoped Sessions/providers.
No deployment, browser acceptance or real FSP ownership claim follows from these
local checks. Existing deprecation warnings remain. Deliverable: independent
**Draft PR** for review; no merge.

## Final security review provenance

Codex Security scan `cfd1efbb-62f3-4553-8eec-f4f3be14a9cb`, completed/sealed
2026-10-10 10:32:24 UTC, reviews immutable range
`17b8f656fdc648eae2a2af9a60fbb6ba353370f9..b823df5d3246e71da915898f131b1dcf84dd01c6`.
The canonical manifest, findings, coverage, Markdown and SARIF were finalized
through the plugin and read back: 11 surfaces, no findings, no unresolved
questions/deferred items. Necessary supporting role/Origin, ownership, FSP reset,
Assessment lock reacquisition and ACCEPTED contact gates were inspected.
This is targeted static security review, not a whole-repository or deployment
audit. The reviewer did not execute the test suites; runtime evidence above was
executed by the main implementer and independently read from logs/JUnit.

Initial working-tree scan `98588e71-a390-4708-9071-b0b2a01b6d9d` was separately
completed with explicit partial/stale-snapshot coverage. It is not credited as
final-source proof. The subsequent immutable-range review resolves that limitation
and accounts for all six production modules and five test files. This report is
added in a documentation-only commit after the reviewed code was frozen.

Managed review receipt: `artifacts/03_coverage/p8-b1-final-range-review.md`,
SHA256 `6e764ca35ba640f2b1b72ce70c666311a555597f3b8a8532f53c300a75224230`.
The plugin's measured completion accounting is `totalTokens=2199937`, including
`cachedInputTokens=2143488`, `inputTokens=2186416`, `outputTokens=13521`,
`source=codex_rollout`, `threadCount=1`. This is the tool's rollout accounting,
not an estimate of billed cost or an independent per-file workload metric.

Production deployment exposure, privileged direct DB/catalog writers and load
benchmarks remain outside this targeted review. Need criteria and candidate
inputs intentionally retain their separate invocation/statement boundaries;
Need-list count/page have no combined snapshot guarantee. Documentation does
not expand the reviewed source range or promise unrelated behavior.
