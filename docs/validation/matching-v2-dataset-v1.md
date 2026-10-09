# Matching V2 validation dataset v1 — P6-A review checkpoint

## Identity and freeze policy

- Dataset namespace: `matching-v2-validation-v1`; schema version: **1**.
- Source contracts: `main@f5d460f9888b8bfe94a90e495254974a0d2043e7`.
- Exactly **8 Needs and 36 fully synthetic candidates**, twelve per specialization.
- JSON SHA256 (UTF-8 without BOM, LF, final newline): `ef362631fc3104c50f29bca301b1fc9368b74a3a1ae95d2c0ba1e491ced0add5`.
- The freeze checkpoint is the scoped Git commit containing this JSON, this document,
  the standalone validator, its tests and two targeted LF Git attributes.
  Its exact SHA is reported after commit;
  no file contains its own commit SHA. Review the immutable commit, not a moving branch.
- After that commit, **do not edit v1**. Corrections require owner approval and a new
  explicitly versioned dataset; retain this v1 artifact.
- P6-B evaluation and human relevance review are **not authorized by this artifact**.
  No golden Top-3/Top-5, Professional Fit values, FSP scores/bonuses, Ranking Scores,
  precision/recall or overlap metrics have been generated.

## Methodology and independence

These are newly authored scenario inputs, not reconstructed N1–N8/C01–C36 records.
The earlier 8/36 description was a design intention; Sava authorized a fresh dataset.
The existing production matching-demo (3 Needs/9 matching candidates plus a separate
base candidate) and the frozen H1–H4/C01–C15 holdout are separate namespaces. Neither
was copied, imported, relabeled or changed. Identical short labels do not imply a shared
identity: the stable identity is the pair `(dataset namespace, record id)`.

Inputs were chosen for positive/negative coverage and controlled qualification inputs,
not for agreement with production ranking. The structural checker independently applies
consent, specialization, coherent canonical Assessment, the approved grade matrix and
must-have set inclusion. It does not import or call `eligible_candidate`,
`evaluate_candidate`, `match_need`, `score_professional_fit`, `score_achievements`,
`rank_evaluations` or a Matching API. It does not connect to a DB or seed anything.

The independent grade matrix is JUNIOR→JUNIOR/MIDDLE, MIDDLE→MIDDLE/SENIOR,
SENIOR→SENIOR. Missing must-have, consent=false, specialization mismatch or absent
canonical verification exclude. Declared grade, FSP, salary, nice-to-have and experience
are never structural admission filters. All applicable exclusion reasons are retained,
not just the first failing condition. Eligible IDs below are in **ID order only**.

This is structural/scenario validation, not blind ranking evaluation, independent
psychometric validation or proof of hiring quality. Dataset review must precede any
later relevance labels or evaluation. No production coefficients were adjusted.

## Schema and provenance

`backend/validate_matching_v2_dataset.py` defines strict Pydantic `Dataset`,
`NeedRecord`, `CandidateRecord`, `FspRecord` and `Evidence` models. Unknown fields are
forbidden at every level; primitive types, enums, bounds, UTC timestamps, ordered
salaries, consent/timestamp consistency, canonical verification trio, exact record
counts and unique ordered IDs are checked. `--schema` emits the exact JSON Schema;
cross-record and provider-equality invariants are validated by the same CLI.

The production skill catalog is read from its literal `SKILLS` definition using AST,
without importing seed/DB initialization. The embedded catalog snapshot must agree
exactly. Only Python, Django, FastAPI, PostgreSQL, React, TypeScript and SQL are used.
Skill names are symbolic references; a future isolated adapter must resolve them to
existing catalog IDs. It must never create skills or change taxonomy.

Assessment evidence is explicitly synthetic: fixed UTC canonical grade/score/date,
not completed attempts or a claim of a genuine test pass. `OfflineAssessmentProvider`
implements the existing `CandidateAssessmentProvider` interface and returns canonical
`CandidateAssessment` records, including all-null C36. It has no writes or sync effects.
No frontend/data-ML question bank exists in this base; FRONTEND and DATA_ML verification
is offline fixture evidence only, not an actual assessment of those disciplines.

FSP VERIFIED evidence was obtained through the existing `MockFspRegistryProvider.lookup`
boundary at this base, with the normalized records from
`backend/app/content/fsp_registry_mock.json`. The validator replays this lookup and
requires exact equality of every achievement field. Seven verified mock identities are
unique across candidates; no duplicate verified IDs need to bypass the DB invariant.
Entered IDs may repeat a verified ID because entering an ID is not verification.
NONE and ENTERED_UNVERIFIED states contain no evidence or verification/sync timestamps.
No `CandidateWrite` accepts achievements, no FSP service/DB mutation is executed, and
no score or provider payload is client-injected. This mock is not a real FSP connection
or authentication of ownership of a real identity.

## Needs and catalog limitations

All Needs are ACTIVE **offline input fixtures**; salaries are synthetic RUB gross,
«до вычета налогов», represented by authoritative decimal strings. Salary and prose
rationale are informational; experience is a soft target. Titles and directions retain
Sava's eight approved labels. Requirements, descriptions and rationale are in JSON.

| Need / position | Specialization / grade | Must-have | Nice-to-have | Target years | RUB gross range | Catalog limitation |
|---|---|---|---|---:|---|---|
| N1 — Python API / Junior | BACKEND / JUNIOR | Python, FastAPI | SQL | 1 | 90000.00–140000.00 | No missing target technology in the stated catalog requirements |
| N2 — Python Django / Middle | BACKEND / MIDDLE | Python, Django | PostgreSQL, SQL | 3 | 180000.00–260000.00 | No missing target technology in the stated catalog requirements |
| N3 — Java / Senior | BACKEND / SENIOR | SQL, PostgreSQL | None | 6 | 280000.00–400000.00 | LIMITED |
| N4 — React / Junior | FRONTEND / JUNIOR | React | TypeScript | 1 | 80000.00–130000.00 | No missing target technology in the stated catalog requirements |
| N5 — Next.js / Middle | FRONTEND / MIDDLE | React, TypeScript | None | 3 | 180000.00–280000.00 | LIMITED |
| N6 — Frontend / Senior | FRONTEND / SENIOR | React, TypeScript | None | 6 | 280000.00–420000.00 | No missing target technology in the stated catalog requirements |
| N7 — ML Engineer / Middle | DATA_ML / MIDDLE | Python, SQL | PostgreSQL | 3 | 200000.00–300000.00 | LIMITED |
| N8 — ML Platform / Senior | DATA_ML / SENIOR | Python, SQL, PostgreSQL | None | 6 | 300000.00–450000.00 | LIMITED |

**N3 is catalog-limited and does not test Java proficiency.** SQL/PostgreSQL matching
is not evidence of Java knowledge. **N5 is catalog-limited and does not test Next.js
proficiency.** React/TypeScript matching is not evidence of Next.js knowledge.
**N7 and N8 are catalog-limited and do not test ML frameworks or specialized ML
competencies.** Python/SQL/PostgreSQL matching is not evidence of ML qualification.
The four flags and limitations are explicit in JSON and in this coverage matrix;
reviewers must not generalize their structural results to those missing technologies.
N6 also does not infer architecture proficiency or individual contribution from tenure.

## Candidate coverage matrix

Every record is synthetic and includes all requested canonical fields. `—` means null,
not a hidden value. Verified Assessment time is `2026-10-08T12:00:00Z`; consent=true
uses `2026-10-08T10:00:00Z`. VERIFIED FSP verification and sync timestamps are fixed
`2026-10-09T00:00:00Z` synthetic fixture times, not measured live sync times.

| Candidate | Direction | Declared / verified grade | Assessment | Years | Consent | FSP fixture state / ID | Structurally eligible Needs (ID order, not rank) |
|---|---|---|---:|---:|---|---|---|
| C01 | BACKEND | JUNIOR / JUNIOR | 100 | 2.0 | true | NONE | N1 |
| C02 | BACKEND | JUNIOR / JUNIOR | 70 | 1.0 | true | VERIFIED / MOCK-MULTI | N1 |
| C03 | BACKEND | SENIOR / JUNIOR | 85 | 0.5 | true | ENTERED_UNVERIFIED / MOCK-WINNER | N1 |
| C04 | BACKEND | MIDDLE / MIDDLE | 90 | 3.0 | true | NONE | N1 |
| C05 | BACKEND | MIDDLE / MIDDLE | 85 | 4.0 | true | NONE | N2 |
| C06 | BACKEND | MIDDLE / MIDDLE | 85 | 4.0 | true | VERIFIED / MOCK-PARTICIPANT | N2 |
| C07 | BACKEND | MIDDLE / MIDDLE | 75 | 1.0 | true | NONE | N2 |
| C08 | BACKEND | SENIOR / SENIOR | 100 | 7.0 | true | NONE | N2, N3 |
| C09 | BACKEND | SENIOR / SENIOR | 88 | 6.0 | true | NONE | N3 |
| C10 | BACKEND | SENIOR / SENIOR | 80 | 8.0 | true | VERIFIED / MOCK-FINALIST | N2, N3 |
| C11 | BACKEND | MIDDLE / MIDDLE | 95 | 3.0 | false | ENTERED_UNVERIFIED / MOCK-MISSING | None |
| C12 | BACKEND | JUNIOR / JUNIOR | 90 | 1.0 | true | NONE | None |
| C13 | FRONTEND | JUNIOR / JUNIOR | 95 | 2.0 | true | NONE | N4 |
| C14 | FRONTEND | JUNIOR / JUNIOR | 80 | 1.0 | true | NONE | N4 |
| C15 | FRONTEND | JUNIOR / JUNIOR | 100 | 2.0 | true | VERIFIED / MOCK-TEAM | None |
| C16 | FRONTEND | MIDDLE / MIDDLE | 90 | 4.0 | true | NONE | N4, N5 |
| C17 | FRONTEND | MIDDLE / MIDDLE | 85 | 3.0 | true | NONE | N4, N5 |
| C18 | FRONTEND | SENIOR / MIDDLE | 85 | 3.0 | true | VERIFIED / MOCK-PRIZE | N4, N5 |
| C19 | FRONTEND | MIDDLE / MIDDLE | 70 | 1.0 | true | ENTERED_UNVERIFIED / MOCK-FINALIST | N4 |
| C20 | FRONTEND | SENIOR / SENIOR | 100 | 7.0 | true | NONE | N5, N6 |
| C21 | FRONTEND | SENIOR / JUNIOR | 88 | 0.8 | true | NONE | N4 |
| C22 | FRONTEND | SENIOR / SENIOR | 90 | 6.0 | true | VERIFIED / MOCK-WINNER | N5, N6 |
| C23 | FRONTEND | SENIOR / SENIOR | 95 | 8.0 | false | NONE | None |
| C24 | FRONTEND | SENIOR / SENIOR | 75 | 5.0 | true | ENTERED_UNVERIFIED / MOCK-MULTI | N5, N6 |
| C25 | DATA_ML | MIDDLE / MIDDLE | 100 | 5.0 | true | NONE | N7 |
| C26 | DATA_ML | MIDDLE / MIDDLE | 85 | 3.0 | true | ENTERED_UNVERIFIED / MOCK-PARTICIPANT | N7 |
| C27 | DATA_ML | MIDDLE / MIDDLE | 100 | 4.0 | true | NONE | None |
| C28 | DATA_ML | MIDDLE / MIDDLE | 80 | 2.0 | true | NONE | N7 |
| C29 | DATA_ML | SENIOR / SENIOR | 100 | 8.0 | true | NONE | N7, N8 |
| C30 | DATA_ML | SENIOR / SENIOR | 85 | 6.0 | true | NONE | N7, N8 |
| C31 | DATA_ML | JUNIOR / JUNIOR | 95 | 1.0 | true | NONE | None |
| C32 | DATA_ML | MIDDLE / MIDDLE | 75 | — | true | ENTERED_UNVERIFIED / MOCK-MISSING | N7 |
| C33 | DATA_ML | SENIOR / SENIOR | 90 | 7.0 | true | NONE | None |
| C34 | DATA_ML | MIDDLE / MIDDLE | 90 | 4.0 | false | NONE | None |
| C35 | DATA_ML | SENIOR / SENIOR | 82 | 10.0 | true | ENTERED_UNVERIFIED / MOCK-TEAM | N7, N8 |
| C36 | DATA_ML | SENIOR / — | — | 3.0 | true | VERIFIED / MOCK-EMPTY | None |

## Structural admission counts — no ranking evaluation

Every Need was checked against all 36 candidates: **288 pairs; 38 admitted, 250
excluded**. Counts are input-consistency checks, not measured eligibility
precision/recall against independent human labels. Each Need has positive and negative
cases within its direction. Cross-specialization candidates are always excluded.

| Need | Eligible count | Eligible IDs in ID order only | Excluded count | Catalog limitation |
|---|---:|---|---:|---|
| N1 | 4 | C01, C02, C03, C04 | 32 | Catalog-supported requirements |
| N2 | 5 | C05, C06, C07, C08, C10 | 31 | Catalog-supported requirements |
| N3 | 3 | C08, C09, C10 | 33 | LIMITED |
| N4 | 7 | C13, C14, C16, C17, C18, C19, C21 | 29 | Catalog-supported requirements |
| N5 | 6 | C16, C17, C18, C20, C22, C24 | 30 | LIMITED |
| N6 | 3 | C20, C22, C24 | 33 | Catalog-supported requirements |
| N7 | 7 | C25, C26, C28, C29, C30, C32, C35 | 29 | LIMITED |
| N8 | 3 | C29, C30, C35 | 33 | LIMITED |

N1/N3/N6/N8 have fewer than five structurally eligible candidates. A later fixed-denominator
overlap@5 cannot be reported as fully applicable for those pools. No Top-3/Top-5 is
selected here; eligible pool size is not a ranking-quality measurement.

## Required edge cases and FSP coverage

- C15 and C27 have assessment 100 but miss React/Python respectively. C15 also has a
  trusted team achievement; it still fails N4/N5/N6 must-have. C27 fails N7/N8 must-have.
- C36 has an all-null canonical Assessment trio. Its mock verified-empty FSP link
  supplies no canonical qualification and cannot make it eligible for N7/N8.
- C03 and C21 declare SENIOR while verified JUNIOR; C18 declares SENIOR while verified
  MIDDLE. Structural checks use the verified grade, including adjacent-grade cases.
- C11/C23/C34 have consent=false and null consent timestamps despite strong grades/scores.
- C31 is a verified JUNIOR with complete ML catalog skills but incompatible grade.
  C33 is SENIOR and misses SQL. C09 has no Python/Django but may satisfy N3's explicitly
  limited SQL/PostgreSQL requirements: this is not proof of Java proficiency.
- C07/C14/C19/C26/C32 have optional-skill or experience gaps; C32 has experience=null.
  Soft gaps do not exclude them when hard filters are satisfied.
- C01 without FSP and C02 with MOCK-MULTI provide a later controlled stronger-assessment
  versus achievement scenario. No Professional Fit comparison or winning label is made.
- C05/C06 and C17/C18 have identical canonical qualification, skills and experience
  inputs with differing FSP evidence; declared-grade difference in C17/C18 is intentionally
  irrelevant. No Professional Fit or rank is computed to verify this input equality.

| FSP scenario | Candidates | Provenance / scope |
|---|---|---|
| No entered ID or evidence | 22 records | NONE |
| Entered, unverified | C03, C11, C19, C24, C26, C32, C35 | 7 records; no evidence; both known/missing mock IDs |
| Verified participant | C06 | MOCK-PARTICIPANT / individual |
| Verified finalist | C10 | MOCK-FINALIST / individual |
| Verified prize winner | C18 | MOCK-PRIZE / individual |
| Verified winner | C22 | MOCK-WINNER / individual |
| Multiple competitions | C02 | MOCK-MULTI: three competitions, mixed results and scopes |
| Verified team result | C15 | MOCK-TEAM / team win; personal contribution not inferred |
| Verified but no achievements | C36 | MOCK-EMPTY; no canonical Assessment |

FSP states total **22 NONE + 7 ENTERED_UNVERIFIED + 7 VERIFIED = 36**.


## Exact reproduction and review instructions

Use the existing repository virtual environment and pinned requirements. Do not recreate
or upgrade dependencies merely for this dataset. From the repository root on Windows:

```powershell
cd backend
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe validate_matching_v2_dataset.py
.\.venv\Scripts\python.exe validate_matching_v2_dataset.py --schema
.\.venv\Scripts\python.exe -m pytest -q tests/test_matching_v2_dataset.py
.\.venv\Scripts\python.exe -m ruff check validate_matching_v2_dataset.py tests/test_matching_v2_dataset.py
.\.venv\Scripts\python.exe -m ruff format --check validate_matching_v2_dataset.py tests/test_matching_v2_dataset.py
.\.venv\Scripts\python.exe -m mypy validate_matching_v2_dataset.py
cd ..
Get-FileHash -Algorithm SHA256 docs/validation/matching-v2-dataset-v1.json
git log -1 --format=%H -- docs/validation/matching-v2-dataset-v1.json
git diff --check
```

On Linux, use the existing Python 3.13+ environment with the same pinned requirements
and replace the Python executable above with its environment path (e.g. `.venv/bin/python`).
CLI accepts `--dataset <path>` for explicitly versioned offline artifacts. It prints
only structural admission IDs/counts and the byte hash. `--schema` writes schema to
stdout; no generated schema or temporary database is needed in the commit.

Run the validator twice and compare the JSON byte hash. Same inputs and provider fixture
produce identical structural output; there is no randomness, network, DB state or clock
sampling. Two exact-path `.gitattributes` rules enforce LF for these JSON/Markdown files,
including Windows checkouts with `core.autocrlf=true`; no other file's attributes or
the user's Git configuration are changed. To reproduce an older checkpoint, inspect
its files at the freeze commit in
an isolated checkout; do not overwrite another person's work.

The standalone provider adapter may be consumed in a later separately authorized
P6-B offline validation; do not use this file as a production seed. There is no demo
mode or account importer here, no passwords/tokens, no real names/emails and no
completed AssessmentAttempt records. All identifiers are synthetic dataset/mock IDs.

## Assumptions, limitations and stop condition

Catalog proxies for N3/N5/N7/N8 were explicitly approved by the owner. They preserve
names/directions without adding missing technology tags or making unsupported claims.
Balanced directions and small eligible pools serve deterministic scenario coverage,
not labor-market prevalence, statistical representativeness or hiring accuracy.
Fixed dates, salaries and scores are synthetic design inputs. Common-grade scores
are not claimed to be psychometrically equivalent across disciplines or grades.

Seven available mock verified identities are each used once. A future scenario needing
additional unique verified identities requires an approved offline adapter design;
do not duplicate a verified ID or broaden production registry fixtures silently.
Any live demo requires separate authorization and an isolated dataset import design;
this checkpoint creates no DB records or credentials and is not a ready-made jury demo.

Schema/structural validation and hostile-input tests are the P6-A gate. Full production
backend/frontend suites, PostgreSQL/Docker verification, browser demo, ranking metrics,
security scan of a future importer and P6-B evaluation remain future separate work.
Matching, Assessment, FSP scoring, Invitations, migrations, production seed and frozen
holdout materials are unchanged. No PR, push or merge is part of this checkpoint.

**STOP FOR DATASET REVIEW. P6-B requires separate authorization.**
