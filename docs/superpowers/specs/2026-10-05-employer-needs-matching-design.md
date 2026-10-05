# TASK O1 — Employer Needs + Matching Engine

## Status and intent

Architecture initially approved by the user on 2026-10-05, with subsequent
team-agreed corrections recorded below. This written specification is NOT approved;
it requires review before the implementation plan and product implementation.

Deliver Employer Profile → Create Need → Publish Need → Eligibility → Matching
→ Ranking → Explainability → Candidate Preview. Preserve the existing platform
foundation. Correctness, privacy, reproducibility and tests take priority over
visual design. No production deployment or PR merge.

Baseline: `origin/main`, commit `e47509b6055674b8872e49fdbb15a507bbb85895`.
Implementation branch: `feat/employer-needs-matching`.

## Existing architecture and reuse

- Backend: FastAPI routes, synchronous SQLAlchemy 2 Session, services, Pydantic 2
  schemas, Alembic; no repository layer. Keep that structure.
- Reuse User, Role, CandidateProfile, EmployerProfile, Skill, Specialization,
  Grade, TimestampMixin and UUID string IDs from `backend/app/models.py`.
- Reuse EmployerUser, Db and require_trusted_origin from dependencies. Employer
  ownership is resolved through authenticated User → existing EmployerProfile.
- Reuse InputModel (`extra=forbid`, whitespace stripping), SkillOut and ApiError.
  Retain `{error: {code, message, fields}}` and existing session/Origin protection.
- Frontend: Next.js App Router, RoleGate, AuthProvider, api(), Feedback, same-origin
  backend proxy and existing responsive CSS. No additional UI framework.
- Tests: pytest/TestClient with per-test Alembic migrations, optional PostgreSQL
  schemas; Node test runner through tsx for frontend. Extend these patterns.
- Seed is transactional and idempotent. Existing demo users, profiles and
  passwords must survive reruns unchanged.

## Persistence

Add EmployerNeed in the existing models module:

- UUID id; employer_id FK → employer_profiles.id, indexed.
- position_title, specialization, required_grade.
- nullable target_experience_years; nonnegative finite values.
- salary_from and salary_to as nonnegative decimal amounts, salary_from <= salary_to.
- description; nullable additional_requirements.
- status enum DRAFT / ACTIVE / CLOSED; existing timestamp mixin.

Add one normalized association object EmployerNeedSkill:

- need_id FK → employer_needs.id with cascade delete.
- skill_id FK → existing skills.id.
- kind enum MUST_HAVE / NICE_TO_HAVE.
- Composite PK (need_id, skill_id) forbids duplicate and cross-kind assignments.
- Eager/batched relationship loading; deterministic skill ordering.

CandidateProfile is the sole source of truth for current verification/assessment
state: verified_grade, nullable normalized_assessment_score (finite 0–100 when
present), and nullable assessment_verified_at. Candidate Assessment Engine owns
persistence/schema evolution of the assessment fields and their consistency with
verified_grade. The last two fields are absent from the inspected baseline; their
addition belongs to Candidate Assessment Engine, not TASK O1. Matching consumes
canonical current state read-only; it is not an assessment source of truth.
Assessment history also belongs to Candidate Assessment Engine and is outside O1.

Future TASK O1 Alembic migrations may create only the EmployerNeed and
EmployerNeedSkill tables and their required indexes/checks. Matching must not
create assessment columns, temporary assessment storage, or assessment-field
migrations. Candidate Assessment Engine owns normalized_assessment_score and
assessment_verified_at schema changes. Select the O1 revision and down_revision
against the actual migration head after integrating current main; do not reserve
`0002` independently of parallel development. Do not create a migration at this
specification-review stage, rewrite `0001`, or use create_all(). O1 downgrade removes
only O1-owned need tables/indexes/checks and preserves CandidateProfile assessment
fields. Verify upgrade/downgrade/upgrade against the integrated migration chain,
baseline/assessment data preservation, and Alembic schema consistency on PostgreSQL.

## Assessment integration boundary

Keep CandidateAssessmentProvider as a read-only batch abstraction over current
CandidateProfile state, exposing candidate_id (CandidateProfile.id), verified_grade,
nullable normalized_assessment_score and nullable assessment_verified_at.
Conceptually, it receives candidate profile IDs and returns their current assessment
data in batches. It is the integration boundary between Matching and Candidate
Assessment Engine. Select the concrete interface during implementation to fit the
existing synchronous Session/service patterns; this specification does not prescribe
a method signature or add a repository layer.

CandidateProfile is the only current source of truth. Candidate Assessment Engine
owns and writes these canonical fields and maintains their consistency; Matching
only reads them and never modifies any of the three. Employer API cannot modify
them either. Matching owns its read layer/provider integration, not assessment
persistence. Do not create a second assessment table or duplicate source of truth.
Do not design Testing Engine internals or assessment history/attempts in TASK O1.

A missing candidate entry or normalized_assessment_score = null fails eligibility
before scoring. Present scores must be finite and in 0–100; zero is a valid available
score. Invalid values fail eligibility, never become a fallback score.
assessment_verified_at is exclusively informational: it does not affect eligibility,
Professional Fit Score, sorting, tie-breakers or any recency bonus.

TASK O1 exposes no public, employer or manual API to write assessment scores,
verified_grade or assessment_verified_at. Future unit/integration tests may prepare canonical fields
through fixtures/factories/seed following existing test patterns; this is not a
production write API. Tests may inject an in-memory read provider. Do not derive
normalized scores from declared_grade, raw percentages or FSP IDs; raw percentages
from different assessments must not be compared directly.

### Parallel development and integration

If O1 implementation starts before Candidate Assessment Engine merges, preserve
CandidateAssessmentProvider as the integration boundary and use a fake/in-memory
provider for unit tests. Do not add temporary production persistence, migrations
for assessment fields, or substitute for Candidate Assessment Engine work. The real
assessment-backed endpoint/demo integration remains dependent on that branch's merge.

After Candidate Assessment Engine merges:

1. Update/rebase feat/employer-needs-matching from the latest main, integrating its
   canonical CandidateProfile fields and actual Alembic migration chain.
2. Connect the production CandidateAssessmentProvider implementation to the real
   canonical CandidateProfile fields, using batch reads.
3. Keep Matching access read-only; schema ownership and assessment history remain
   with Candidate Assessment Engine.

## Need API, validation and lifecycle

Seven endpoints under `/employer/needs`:

| Method | Path | Behavior |
| --- | --- | --- |
| GET | /employer/needs | Own needs, limit/offset |
| POST | /employer/needs | Create own DRAFT, 201 |
| GET | /employer/needs/{id} | Own need |
| PUT | /employer/needs/{id} | Replace fields/skills of own DRAFT |
| POST | /employer/needs/{id}/activate | DRAFT → ACTIVE |
| POST | /employer/needs/{id}/close | ACTIVE → CLOSED |
| GET | /employer/needs/{id}/matches | Own ACTIVE need, limit/offset |

Use `{items, total, limit, offset}` for paginated results; no existing pagination
contract needs to be preserved. Default limit 20, maximum 100, offset >= 0.
List order: created_at DESC, id ASC. Matching pagination follows full ranking.

All endpoints require EmployerUser. Mutations also require trusted Origin.
The existing employer_profile service resolves ownership; missing employer profile
returns the existing profile_not_found response. Query needs by both id and owner;
foreign and missing need IDs return 404 without revealing another employer's data.

Request fields contain must_have_skill_ids and nice_to_have_skill_ids. Forbid extra
fields, including employer_id, status, calculated scores, grade fit and eligibility.
Validate title, description, >= 1 must-have, duplicates, overlap, existing skill IDs,
salary bounds/order, and nonnegative finite experience. Validate before mutation so
rejected updates leave the original need intact. Protect edits/transitions against
concurrent lifecycle changes with the existing row-locking ORM pattern.

Only DRAFT is editable. Invalid transitions and matching on DRAFT/CLOSED return 409.
CLOSED is terminal. No delete, reopen or invitation behavior.

## Eligibility, scoring and deterministic ranking

Keep eligibility and scoring logically separate. Eligibility requires, in order:

1. CandidateProfile.personal_data_consent == true.
2. Exact specialization (BACKEND / FRONTEND / DATA_ML).
3. verified_grade present.
4. Compatible verified grade.
5. All must-have skill IDs present in profile skills.
6. Available valid normalized_assessment_score from the provider.

All six hard filters must pass before scoring. personal_data_consent = false
excludes a candidate from new ranked matching results regardless of specialization,
verified_grade, assessment score, skills, experience or FSP. A null normalized score
also excludes the candidate before scoring; no declared-grade fallback is allowed.

declared_grade never enters the matching input contract. Skills are self-declared;
an assessment score does not verify individual skills. Do not label them verified.

| Required grade | Eligible candidate grade and GradeFit |
| --- | --- |
| JUNIOR | JUNIOR 1.00; MIDDLE 0.75 |
| MIDDLE | MIDDLE 1.00; SENIOR 0.75 |
| SENIOR | SENIOR 1.00 |

One reusable pure scoring implementation uses frozen base weights 45/25/15/15:

- AssessmentFit = normalized_assessment_score / 100.
- GradeFit = the compatibility table above.
- NiceFit = matched nice-to-have / total nice-to-have.
- ExperienceFit = min(candidate years / target years, 1).
- For a positive target and missing candidate experience, ExperienceFit = 0.
- User-approved zero-target behavior: ExperienceFit = 1, including missing
  candidate experience, since the explicitly requested target is zero.
- Omit NiceFit when no nice skills exist; omit ExperienceFit when target is null.
- Effective maximum contribution = base weight × 100 / sum(active base weights).
- Each contribution = effective maximum × factor. Total remains in 0–100.

Sort using unrounded professional score DESC, normalized assessment DESC, stable
candidate ID ASC. FSP infrastructure does not exist in the baseline; do not invent
achievement flags or use fsp_id as evidence. No FSP tie-breaker until a real
confirmed-achievement source exists. Profile updated_at never affects ranking.

Candidate pool loading uses existing selectin relationships and batched provider
reads, with SQL hard filters where suitable. No per-candidate DB/provider queries.
Rank before slicing by limit/offset; query-count regression checks cover batching.
The MVP evaluates the eligible pool in memory; large-scale ranking is future work.

## Explainability and privacy

Add a dedicated employer-facing response schema. Explicitly construct previews;
never serialize CandidateOut or CandidateProfile.__dict__.

Allow only candidate_id, display_name (first name + surname initial), specialization,
verified_grade, self-declared skills, years_of_experience, normalized_assessment_score,
optional assessment_verified_at, professional_fit_score, breakdown,
matched_must_have_skills, matched_nice_to_have_skills and missing_nice_to_have_skills.

assessment_verified_at is permitted in employer preview/detail and is not a
privacy-sensitive field. It is informational only; for example, UI may show
«Компетенция подтверждена: 18.09.2026». The date never affects eligibility, score,
sorting, tie-breakers or recency bonuses. Profile recency also remains outside ranking.

User-approved privacy choice: exclude free-text about, which could contain contacts.
Also exclude email, phone, Telegram/messenger fields, address, fsp_id,
personal_data_consent, personal_data_consent_at, user_id,
full surname, declared_grade and other internal fields. personal_data_consent is
an internal eligibility field and must never be returned in employer preview responses.
No separate endpoint reveals full candidate data or contacts.

Breakdown contains assessment, grade (including exact_match), nice_to_have
(matched/total) and experience. Each active factor returns actual contribution and
effective max. Excluded optional factors explicitly indicate exclusion and zero max;
do not render them as perfect 15/15. UI only formats server values; no frontend
scoring formula. Use «Соответствие» / Professional fit, never hiring probability.

## Frontend

Add `/employer/needs`, `/employer/needs/new`, `/employer/needs/[id]/edit`, and
`/employer/needs/[id]/matches`, following existing page/component composition.
Link needs from the employer profile/navigation.

- List position, specialization, required grade, status badge, salary and actions.
- Create/edit all required need fields and normalized skill selections. Enforce
  duplicate/overlap, salary order and numeric constraints, with disabled submit.
- Show matching action only for ACTIVE needs; backend independently checks status.
- Cards show masked name, verified grade, Professional fit to one decimal,
  assessment, must-have/nice skills and candidate experience.
- «Подробнее» expands server breakdown on the card using a simple details block.
- Include loading, empty, API error/retry, field feedback and responsive layout.

## Demo data and tests

Extend existing seed through an explicit matching-demo option that preserves the
current --demo behavior, existing account counts and original unverified candidate.
Matching-demo data remain local/development only and idempotent. Include candidates
with wrong specialization, missing score, missing must-have with score 100, null
verified grade with ideal skills, Junior/Middle/Senior grades, optional skill gaps,
missing experience and an exact Middle outranking a slightly higher-scoring Senior.
Populate a demo ACTIVE need and DRAFT/CLOSED examples without overwriting edits.
Do not manufacture 36 users or tune weights using calibration/holdout datasets.

Tests precede implementation and exercise behavior:

- Need creation, roles, anonymous access, ownership on all routes, trusted Origin,
  invalid IDs/skills/duplicates/overlap/missing must-have/salary/experience/extra fields,
  atomic rejected updates, DRAFT editing and lifecycle restrictions.
- Required backend test: a verified candidate with valid specialization, compatible
  grade, all must-have skills and an available normalized assessment, but
  personal_data_consent = false, is excluded from matching results before scoring.
- Provider-boundary tests: Matching obtains normalized assessment data through
  CandidateAssessmentProvider and never writes verified_grade,
  normalized_assessment_score or assessment_verified_at. A fake/in-memory provider
  supports unit tests before Candidate Assessment Engine merges; real canonical-field
  integration is verified after its merge, without O1-owned assessment persistence.
- Every consent/specialization/verified-grade/grade/must-have/score eligibility branch,
  including score zero and invalid/nonfinite provider values.
- Independent numeric expectations for each contribution, experience cap/missing/zero,
  all optional-factor exclusions and renormalization, score bounds.
- Unrounded ordering (scores with same displayed decimal), deterministic ties,
  pagination after ranking, grade advantage, declared-grade/FSP/recency independence.
- Vary assessment_verified_at while keeping eligibility/scoring inputs fixed;
  eligibility, Professional Fit Score, ordering and tie-breakers must be unchanged.
- API privacy: assert the exact allowed preview keys recursively and absence of
  sensitive/internal fields, using source profiles populated with identifying values.
  The response may contain assessment_verified_at, but must not contain
  personal_data_consent, personal_data_consent_at, email, phone, telegram, fsp_id
  or other private/internal contact fields. Never return the full CandidateOut.
- Batched query behavior, migration round-trip/schema consistency and idempotent
  matching-demo seeding; retain the existing auth/candidate suites.
- Frontend tests cover form payload/validation and safe presentation via the
  existing Node runner; browser smoke separately checks actual navigation/forms.

## Verification and completion

Run the actual project commands: backend pytest -q, ruff check ., ruff format
--check ., mypy app, alembic upgrade head / alembic check; frontend npm ci,
npm run lint, npm run typecheck, npm test, npm run build; Docker Compose
up --build -d --wait with health/API/UI checks. PostgreSQL-specific behavior must
be verified on PostgreSQL, not inferred from SQLite results.

Review the entire diff and run the Codex Security diff workflow focused on ownership,
mass assignment, preview privacy, trusted Origin, assessment provenance and bounds.
Fix findings, repeat affected checks, update README with API/matching/demo behavior.
Record real results and remaining environment limitations; never claim unrun checks.
Commit implementation, push the feature branch, create/attach PR to main, and stop
without merge. Use the user's requested final report section structure.

## Current environment observations

Repository cloned and main pulled successfully. Working tree was clean before
branch creation. Node v24.1.0 is available. Python is not on shell PATH; the bundled
interpreter is Python 3.12.14, below the project's required Python 3.13+.
`docker version` finds the Docker client, but no docker_engine named pipe;
Docker Compose runtime verification needs a working engine. No product dependencies
have been installed and no product checks have been run at this specification stage.
