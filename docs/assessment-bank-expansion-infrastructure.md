# P8-A0 — Assessment multi-bank infrastructure

## Scope and baseline

- Starting main: `acead7a5ea8eb93c1344107440ddb6c16b42173f`.
- This phase adds infrastructure and regression coverage, not new question content.
- Current production source remains Backend: 120 questions, 40 per grade,
  2 BASIC / 4 APPLIED / 2 ADVANCED per competency.
- Its byte SHA256 remains
  `76cda12d6358f14da84cce0ac584035ab189ae7a2f43e18d1e3cfed41276023c`.
- All 120 records, codes, versions, options and ordering are unchanged. Their P5
  provenance and content findings remain in `assessment-bank-diversity.md`.

## Sources and specialization boundary

`question_bank.BANK_SOURCES` explicitly binds each source filename to one
`Specialization`. Question records keep the existing JSON schema; specialization
is taken from the registry, never inferred from a code or client input.

| Specialization | Source under backend/app/content | A0 publication |
| --- | --- | --- |
| BACKEND | backend_questions.json | Existing P5 source only |
| FRONTEND | frontend_questions.json | Not published; content not created |
| DATA_ML | data_ml_questions.json | Not published; content not created |

The existing competency sets are shared by the validator and runtime through
`assessment_bank_config.py`. Runtime `assessments.COMPETENCIES` retains the same
values and remains available to existing callers. There is no second competency
definition, storage model or API layer.

`load_bank()` keeps its Backend default and source order. Passing an explicit
specialization supports technical preflight of a registered draft, but does not
publish it. `load_banks()` returns only approved sources and validates their
shared namespace before seeding.

## Target structure and compatibility

New/expanded sources use `EXPANDED_BLUEPRINT`: 150 per specialization, 50 per
grade, five competencies with 2 BASIC / 6 APPLIED / 2 ADVANCED each. The published
120-question Backend source has an explicit `LEGACY_BACKEND_BLUEPRINT` during A0.
It is not silently accepted as a completed 150-question bank.
The registry rejects other distributions and rejects the legacy blueprint for
Frontend/Data-ML. The legacy validator default is retained only for Backend;
new specialization defaults are 150 / 50 / 2-6-2.

Validation requires exact totals and buckets, specialization-specific
competencies, typed grade/difficulty metadata, strict integer version >=1,
nonblank codes/prompts, four nonblank distinct options and valid supersedes
graphs. Codes are globally unique across loaded banks. A predecessor cannot
cross specialization boundaries or be claimed by multiple successors.
Missing historical predecessors remain allowed; existing version/lineage
semantics are otherwise unchanged.

The existing private answer-storage convention is unchanged; runtime still
randomizes and persists option IDs. No keys, marking positions, solutions or
alternatives are emitted in validation diagnostics. JSON/parser/file errors
suppress sensitive exception context.

## Publication gate

A source is published only with both:

1. A reviewed byte SHA256 in its registry entry.
2. A nonblank reference to the separate content review.

These fields are release metadata entered after authorized review. Technical
validation does not set them. Their presence is not a claim of psychometric or
professional validation by AI.

Unpublished entries are skipped without reading their draft files. They cannot
become candidate-accessible merely by adding JSON or manually inserting rows.
An approved source must match its reviewed digest and pass every structural
and global identity check. A malformed approved registry/source fails closed.

New starts additionally require a complete active persisted copy of the reviewed
specialization source, including immutable metadata, version and alternatives.
A missing grade, inactive record, unreviewed extra record or changed alternative
blocks all new starts for that specialization using the existing UNAVAILABLE
response. Deliberate deactivation is preserved by repeated seed; reseeding does
not override it. Existing attempts can still save, finish, time out and be read
without a currently published bank; results and verification are not withdrawn.

Source files and registry metadata are rechecked without a persistent cache.
Publication checks use existing database tables; no migration is needed.

## Seed and historical safety

All approved banks are parsed and validated before mutation. Existing immutable
questions and historical predecessor ownership are preflighted before any row
is added/deactivated. Seed retains the existing transaction boundary, global DB
code uniqueness, generated IDs and option IDs. A replacement only deactivates
its predecessor; it never rewrites or deletes historical content/membership.
Repeated seed preserves prior active flags, questions, options, attempts, answers,
results and verified qualification.

P8-A1 must append 30 Backend questions and change only its explicit blueprint
and reviewed release metadata after its separate content audit/authorization.
P8-A2/A3 must supply their 150-question sources and independent content audits
before their registry entries can be promoted. Technical preflight of all three
banks is available through `validate_source_banks`; it is not a content audit.

## Unchanged exam contracts

No Assessment API/schema, scoring, PASS threshold, eligibility, verified-grade
rule, cooldown, profile, Matching V2, FSP or invitation logic changes.
One attempt still selects 20 questions: 1 BASIC / 2 APPLIED / 1 ADVANCED per
competency, using persisted least-exposed families and secure random tie
selection. Options/membership remain persisted. Time remains 30 minutes,
scores 0–100, PASS >=70 plus >=50% per competency, cooldown 7/90 days.

## Regression coverage

`test_question_banks.py` uses explicitly synthetic, private test-only 450-record
fixtures; their review metadata is labelled TEST_FIXTURE_ONLY. They are never
production content and are not professionally audited question banks.

Coverage includes all nine specialization/grade pairs, 150/50/2-6-2 inventory,
20-question forms, disjoint first two forms, unused APPLIED choices in the third,
answer saving/order/reload, submit idempotency, PASS/failure preservation,
timeout/deadline, history, cooldown, privacy, publication/incomplete-bank
rejection, global collisions, atomic seed rejection and immutable 120→150
expansion across active/finished attempts.

Existing P3/P5 history tests reconstruct their earlier 75-record releases with
an explicitly scoped test-only publication-gate override for the historical
start. After that start the real current gate resumes. Historical fixtures,
score expectations and source contents are unchanged.

## Final local verification

| Check | Result |
| --- | --- |
| SQLite, Python 3.13 | 1022 passed / 23 PostgreSQL-only skips |
| PostgreSQL 17.11, Python 3.13 | 1045 passed / no skips |
| New infrastructure regression cases | 57, including all nine pairs |
| Ruff / format / mypy | PASS; 75 files formatted, 38 typed source files |
| Alembic | Unchanged c3d9b7e21a40 head; no new upgrade operations |
| Frontend npm ci / lint / typecheck / tests / build | PASS; 184 tests |
| Fresh Docker build / startup / health / API proxy | PASS |
| Repeated base / demo / matching-demo seeds | PASS; all 16 public table snapshots unchanged |
| Existing source and protected scope diff | No differences |
| git diff --check | PASS |

The final Docker API smoke started 20-question forms, saved/reloaded an answer,
finished with the existing failure/cooldown semantics and retained qualification.
All table snapshots also remained identical across repeated seeds after two
real API attempts.

The first container test invocation inherited the smoke site's Origin and lacked
repository-level validation documents. It was replaced by read-only whole-repo
test containers with the normal test Origin; both complete final suites above
passed. No application fix or security relaxation was used for that setup issue.
Existing dependency deprecation warnings remain; npm ci reports the unchanged
five high advisories in the frontend dev dependency chain.

The exact head/CI identity is reported in the Draft PR and execution report.
P8-A1/A2/A3 are not started by this phase.

**Draft PR only. Stop for infrastructure review. No merge authorized.**
