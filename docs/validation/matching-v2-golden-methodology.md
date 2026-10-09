# P6-B1 — Independent Matching V2 relevance proposals

Status: **PROPOSED / awaiting human review**. Author: AI, not human experts.
This checkpoint prepares labels before production results are observed. It does
not authorize P6-B2, evaluation, deployment, scoring changes or merge.

## Authority, frozen inputs and implementation plan

The primary requirements are Sava's complete approved P6-B1 specification,
supplied in the user message dated 2026-10-09 19:36 Europe/Moscow. The thirteen
execution-instruction sections supplement it. They agree on scope; the original
specification clarifies that grade 0 is a relevance judgment inside the eligible
pool, never an exclusion, and that full-pool Top-5 overlap is uninformative.

- Repository: `ssavantonoff/fsp-platform`.
- Starting main / freeze commit: `a7590b79227f31abc9dba3e639d567cc0553138d`.
- Branch: `feat/matching-v2-evaluation`.
- Sole input: `docs/validation/matching-v2-dataset-v1.json`.
- Dataset namespace: `matching-v2-validation-v1`; 8 Needs, 36 candidates.
- Frozen byte SHA256: `ef362631fc3104c50f29bca301b1fc9368b74a3a1ae95d2c0ba1e491ced0add5`.
- Proposal: `docs/validation/matching-v2-golden-proposed-v1.json`, UTF-8 without
  BOM, LF, final newline. Its byte hash is recorded after the final checks;
  the file does not contain its own hash.

The bounded implementation plan is: establish source/hash and structural counts;
write failing artifact-integrity tests; materialize manually authored ordinal
judgments and separate literal FSP expectations; implement a read-only closed
contract validator; document future metrics; perform independent review and
scoped security review; verify, commit exact paths, push and create a Draft PR;
stop for independent label review. No additional dependencies are needed.

Identity is `(dataset namespace, Need ID, Candidate ID)`. Short IDs do not identify
records from the separate V1 holdout or production demo. Neither those inputs nor
the P6-A JSON, Markdown or structural validator is edited here.

## Independence boundary

The input byte hash was verified before any proposals were prepared. Structural
eligibility was independently reconstructed directly from the frozen JSON, not
obtained from Matching. The labels were authored as literal holistic judgments
before observing production results. Serialization and integrity checks do not
calculate grades. Records are stored in Need/Candidate ID order for inspection,
never in relevance or production ranking order.

No Matching V2 run, Matching API, `score_professional_fit()`, production ranking
function, production FSP scorer, previous Matching output, actual Professional
Fit, actual Ranking Score or final ranking metric was used. Approved product
contracts may be read; their scoring weights do not create expert grades. The
professional formula and its coefficients are neither reproduced nor applied to
the relevance proposals. FSP expectations use only the approved business formula
and the frozen normalized provider evidence.

The standalone validator imports only Python standard-library modules. It reads
the two JSON artifacts and prints integrity results and hashes; it has no network,
DB, seeding, process execution or application imports. Tests run with
`--noconftest` to avoid loading the application/DB fixture tree. Production test
suites that exercise ranking are outside this checkpoint's verification scope.
An integrity test or security review is not a ranking evaluation.

Independence declarations are auditable process claims, not something a schema
can prove. The validator forbids extra structured fields, including numeric
production ranking outputs and private identifiers. Human review must inspect
prose for unsupported claims, hidden outputs or sensitive content; nonempty text
validation cannot determine the truth of a rationale.

## Structural eligibility, distinct from relevance

All 288 Need–Candidate pairs are considered. Admission requires consent=true,
matching specialization, the coherent canonical verified Assessment trio, allowed
verified grade, and every must-have skill tag. The frozen hash protects the
already validated canonical types/dates and dataset schema. The independent
checker uses all three canonical fields, not declared grade.

| Required grade | Allowed verified grades |
| --- | --- |
| JUNIOR | JUNIOR, MIDDLE |
| MIDDLE | MIDDLE, SENIOR |
| SENIOR | SENIOR |

FSP, declared grade, experience, nice-to-have and salary never admit or exclude.
Skill presence is set inclusion of self-declared catalog tags, not verified
mastery. All applicable exclusion reasons can coexist.

| Need | Eligible labels | Excluded pairs | Label scope |
| --- | ---: | ---: | --- |
| N1 | 4 | 32 | Stated API requirements |
| N2 | 5 | 31 | Stated Django requirements |
| N3 | 3 | 33 | CATALOG_PROXY: relational slice; Java unknown |
| N4 | 7 | 29 | Stated React requirements |
| N5 | 6 | 30 | CATALOG_PROXY: React/TypeScript slice; Next.js unknown |
| N6 | 3 | 33 | Stated frontend stack; architecture unknown |
| N7 | 7 | 29 | CATALOG_PROXY: data-processing slice; specialized ML unknown |
| N8 | 3 | 33 | CATALOG_PROXY: data-stack slice; specialized ML platform unknown |
| Total | 38 | 250 | 288 structural pairs |

The proposed file contains exactly one relevance label per eligible pair and none
for an excluded pair. Excluded examples appear only in the separate negative-case
section, with `expected_eligible: false`. Structural coverage is not hiring
precision/recall or ranking quality.

## Professional relevance rubric

Grades are ordinal categories, not probabilities, percentages or a weighted sum:

| Grade | Interpretation within the admitted pool |
| --- | --- |
| 0 | Low relevance: the observable professional evidence offers little support for the stated work despite structural admission |
| 1 | Partial fit: admitted stack/grade, with substantial soft gaps or insufficient evidence for the work |
| 2 | Good fit: coherent available professional evidence, with meaningful uncertainty or limitations |
| 3 | Very good fit: several mutually consistent available signals support the stated work, within the dataset's evidence limits |

Consider specialization, verified grade, mandatory/optional tags, synthetic
Assessment evidence and experience jointly. Mandatory tags and compatibility
establish admission, not automatic grade 3. An adjacent higher verified grade
can support the role; it receives neither an automatic bonus nor a penalty.
There is no assumed overqualification, salary mismatch or retention problem.
No numeric Assessment threshold mechanically maps to a grade. The Assessment
number can support a qualitative judgment, but a score at one grade/discipline
is not calibrated as equivalent to the same number at another.

Years are general self-declared tenure, not measured relevant project experience.
The rationale may describe how tenure supports the observable work, but cannot
claim specific role experience. A missing value remains unknown, never zero;
more years do not automatically imply better relevance. Unrequested technologies
do not create an advantage. Nice-to-have gaps are soft evidence, never exclusions.
FSP, declared grade, consent strength, salary and record order do not alter grade.

Each proposal includes a rationale, all six factor categories, exact synthetic
Assessment/experience evidence, limitations, uncertainty and any proxy flag.
AI authorship, human-review-pending status and uncalibrated uncertainty remain
explicit. No forced total ranking, selected Top-3/Top-5 or fine-grained score is
stored. Ties express insufficient evidence to distinguish candidates, not
equivalence of real professional ability. The rubric permits all four grades;
it does not force the dataset to populate every category.

## Catalog and evidence limitations

Every N3/N5/N7/N8 label contains `CATALOG_PROXY` and the explicit frozen limitation:
SQL/PostgreSQL does not establish Java; React/TypeScript does not establish
Next.js; Python/SQL/PostgreSQL does not establish specialized ML competence.
Proposed grades assess only the observable slice. As a conservative authoring
choice, proxy proposals do not use grade 3 while the role-defining competence is
unobserved. This is not an eligibility rule, a production cap or a mandated
formula; human reviewers must accept or revise it before evaluation.

The cap and coarse evidence create many ties; some Needs cannot discriminate
rank quality at all with these proposals. Report catalog-supported Needs and
CATALOG_PROXY Needs separately in P6-B2. Do not generalize proxy metrics to the
named missing technology or call them verified hiring relevance.

All candidates and Assessment evidence are synthetic. FRONTEND and DATA_ML
canonical evidence is an offline fixture; the base has no corresponding
production question bank. Backend scores also do not represent observed attempts.
No project details, work samples, task-level Assessment responses, reference
checks or validated confidence probabilities are available. N6 lacks evidence
about architecture, ownership and technical leadership. Human review can improve
judgments against these inputs; it cannot turn absent evidence into fact.

## Separate FSP business-rule expectations

For verified evidence let `d` be the number of distinct competition IDs and `q`
the best result quality: PARTICIPANT=0, FINALIST=0.50, PRIZE_WINNER=0.80,
WINNER=1.00. With no achievements the best result is null and quality is zero.

```text
participation = min(d, 3) / 3 * 30
achievement_score = participation + q * 70
bonus = achievement_score / 100 * 5
```

With no verified FSP evidence, count=0, best=null, score=0 and bonus=0.
A verified link alone produces no bonus. Multiple rows from one competition
count once; the best result is selected over all verified rows. Competition
discipline, recency and team/individual scope do not modify these approved rules.
The ranges follow from the formula: score 0..100 and bonus 0..5. Expected numeric
values are deterministic business-rule oracles, never production scorer output.

| Scenario | Frozen example | Verified | Distinct competitions | Best | Score | Bonus |
| --- | --- | --- | ---: | --- | ---: | ---: |
| NONE | C05 | false | 0 | null | 0 | 0 |
| ENTERED_UNVERIFIED | C03 | false | 0 | null | 0 | 0 |
| VERIFIED_EMPTY | C36 | true | 0 | null | 0 | 0 |
| PARTICIPANT | C06 | true | 1 | PARTICIPANT | 10 | 0.5 |
| FINALIST | C10 | true | 1 | FINALIST | 45 | 2.25 |
| PRIZE_WINNER | C18 | true | 1 | PRIZE_WINNER | 66 | 3.3 |
| WINNER | C22 | true | 1 | WINNER | 80 | 4 |
| MULTIPLE_COMPETITIONS | C02 | true | 3 | WINNER | 100 | 5 |
| TEAM_ACHIEVEMENT | C15 | true | 1 | WINNER | 80 | 4 |

Only synthetic candidate IDs and aggregate expectations are copied to the new
artifact; raw provider/FSP identity IDs and external competition IDs are not.
Normalized evidence is already frozen and authenticated only by the mock provider
contract, not by a real FSP ownership connection. A team win proves no individual
professional contribution.

C05/C06 have equal professional inputs and equal relevance grades for N2;
expected bonuses differ by 0.5. C17/C18 have equal professional inputs and equal
grades for N4 and N5; bonuses differ by 3.3. Their declared-grade difference is
ignored. Expected Professional Fit equality is recorded as `EQUAL_NOT_COMPUTED`:
it follows from identical professional inputs, without calculating either value.
No expected production rank or winner is inferred from these comparisons.

C15 misses React for N4/N5/N6 despite Assessment 100 and a team win. C27 misses
Python for N7/N8 despite Assessment 100. C36 has all-null canonical Assessment
fields for N7/N8 despite verified-empty FSP. Grade incompatibility may additionally
apply; a required exclusion is not necessarily the only reason. FSP never bypasses
hard filters.

## P6-B2 deterministic regression design — not executed

Deterministic regression tests product contracts, separately from relevance.
In a later authorized isolated adapter, compare production output with independent
literal rule oracles. Do not tune professional labels to match those outputs.

| Check | Future comparison and denominator | Ties / small pools / interpretation |
| --- | --- | --- |
| Eligibility | Exact admitted/excluded sets and reasons over all 288 pairs; violation count over 288 | No rank dependence; small pools do not change filters |
| Professional Fit correctness | Absolute difference from independently derived approved-contract oracle for each of 38 eligible pairs; pass fraction over checked eligible pairs | Compare unrounded values with a documented tolerance/precision contract; exclude ineligible pairs; numeric ties are allowed; contract compliance is not professional validity |
| FSP score and bonus | Absolute differences from literal aggregate expectations; pass fraction over checked FSP cases | All nine scenarios, controls and negative cases; verification, zero evidence, deduplication and cap checked separately; no relevance claim |
| Ranking Score correctness | Absolute difference from the separately approved formula oracle per eligible pair; pass fraction over checked pairs | Use unrounded inputs and approved precision convention; equal scores remain ties before deterministic ordering; no ranking-quality claim |
| Tie-breaking | Returned order must follow the approved secondary-key contract for each actual or isolated synthetic score-tie group; pass fraction over checked tied groups | Zero tied groups means N/A, not 100%; IDs can resolve implementation order but never expert relevance ties |
| Explainability | Correct field/reason provenance and aggregate calculations per checked explanation; pass fraction over checked explanations | Requires content checks, not only presence; no claim that plausible prose proves competence |
| Stable ordering | Exact ordered-ID equality across repeated identical-input runs; fraction over repeat comparisons | Same inputs/provider snapshot; all pool sizes; records test stability, not semantic quality |
| Hard-filter violations | Count returned excluded candidates / count returned candidates; also report excluded pairs incorrectly returned / 250 | Empty returned output gives N/A for first rate; zero is necessary but cannot prove relevance |

The future evaluator must distinguish full-precision numerical comparison from
display rounding. A precision tolerance cannot justify a different ordering.
Each fraction needs a reported numerator and denominator; never collapse skipped
or N/A cases into passes. For Professional Fit/Ranking Score, this checkpoint
intentionally creates no numeric expected output or implementation.

## P6-B2 ranking relevance design — not executed

Use only human-reviewed and frozen relevance labels. Let `E_n` be a Need's
independently eligible pool, `m=|E_n|`, `y(c)` its grade and `pi` the returned
production ordering. The later evaluator must verify eligibility/completeness
before ranking metrics. Invalid IDs, duplicates, excluded entries or missing pool
members fail deterministic regression; do not silently discard them and report
relevance on a repaired list. This methodology assumes a complete eligible
ordering; a truncated API needs an explicitly agreed adapter before P6-B2.

### NDCG@3 and NDCG@5

Use `k_eff=min(k,m)`, ranks starting at 1, exponential gain and logarithmic discount:

```text
DCG@k_eff = sum(i=1..k_eff) (2^y(pi_i) - 1) / log2(i + 1)
IDCG@k_eff = the same sum with relevance grades sorted descending
NDCG@k_eff = DCG@k_eff / IDCG@k_eff
```

The denominator is ideal discounted cumulative gain, not `k` or pool size. An
all-zero pool has IDCG=0: report N/A and the reason, never fabricate 0 or 1. An
empty eligible pool also yields N/A. There is no padding with imaginary candidates
or zero relevance; report requested k, effective k and m.

Expert ties have equal gains, so their permutation changes neither ideal gain nor
the comparison; no expert ID tie-break is invented. For production use its actual
returned deterministic order after contract verification, even if primary scores
tie; display-rounded scores are not a definition of tie. If a future system emits
unresolved rank groups instead of a total order, stop and agree a group-aware
convention before evaluating it; do not introduce ID ordering in the metric.

For fewer than five candidates report NDCG@min(5,m), explicitly naming the effective
cutoff. This can still evaluate order, but it is not five-item selection quality.
For an all-equal positive-grade pool every permutation achieves the same NDCG:
such a result is non-discriminating, not evidence of good ranking. The proposed
N3/N8 labels currently have this limitation. Human review may retain these ties.

NDCG measures concentration of ordinal professional relevance near the top. It
does not validate FSP policy or hiring success. Exponential gains are a chosen
convention that values grade 3 more strongly than grade 2; ordinal grades are not
known cardinal utilities. Small synthetic pools and proxy judgments limit
generalization; NDCG cannot overcome absent technology evidence.

### Pairwise ordering agreement

For each Need, form unordered eligible pairs with unequal expert grades:
`P_n = {{a,b} subset E_n : y(a) != y(b)}`. The denominator is `D_n=|P_n|`.
For each pair denote the higher-grade candidate by h and lower by l.

```text
agreement_n = sum({h,l} in P_n) credit(h,l) / D_n
credit = 1 if rank(h) < rank(l); 0 if rank(h) > rank(l)
```

The total returned order supplies distinct rank positions, even on score ties.
Expert ties are excluded from numerator and denominator; no arbitrary order is
assigned to them. Unresolved predicted ties are unsupported by the chosen total
order contract, as for NDCG, and require a reviewed methodological amendment.
If a future amendment admits unresolved predicted ties, half credit can be used,
but it must be versioned rather than mixed into this convention silently.

If D_n=0, report N/A with zero comparable pairs. Pools of one candidate have no
pairs; smaller pools are valid only if unequal-grade pairs exist. Agreement
measures ordinal direction over comparable pairs; it does not emphasize the top,
distinguish distances between grades, or penalize arbitrary order within an expert
tie. Report numerator, denominator and tie-excluded pair count. Larger pools
produce more pairs and can dominate a micro-average.

### Top-3 / Top-5 set agreement

Define an independent expert Top-k membership set only when `m>k` and the
descending grade sequence has a strict boundary `y_(k)>y_(k+1)`. Internal ties
wholly inside/outside the cutoff do not make membership ambiguous. A tie spanning
the cutoff makes the metric N/A; no candidate IDs or FSP values break it.

```text
Top-k set agreement = |production_Top_k intersection expert_Top_k| / k
```

The denominator is k, with both sets containing exactly k eligible distinct IDs.
This evaluates membership, not order. Ordered Top-k agreement requires a separate
reviewed convention and unique expert ordering at every compared position; it is
not claimed here. Where no independent unambiguous membership exists, use NDCG
and comparable-pair agreement subject to their own applicability limits.

If `m<k` or `m=k`, set agreement is N/A (full-pool or unavailable selection), not
an artificial 100%. N1/N3/N6/N8 have fewer than five eligible candidates and N2
has exactly five: Top-5 selection agreement is uninformative for all five. For
N3/N6/N8 the same full-pool issue applies to Top-3. N4/N5/N7 have larger pools,
but any boundary tie still makes the relevant Top-k agreement N/A. No Top-k list
is selected in this checkpoint.

### Aggregation, interpretation and baseline

Compute each metric per Need first in a separately authorized P6-B2. The default
macro mean is `sum(applicable per-Need metric)/number of applicable Needs`, with
that denominator and all N/A reasons reported. For pairwise agreement an optional
micro mean is `sum(correct pairs)/sum(comparable pairs)` over applicable Needs;
label it separately because pool sizes weight it differently. No applicable Needs
means aggregate N/A. Never substitute N/A with zero or one. Report proxies
separately from catalog-supported Needs and identify non-discriminating pools.

Human labels represent professional relevance, while production Ranking V2 also
contains a separately approved FSP contribution. A disagreement may reflect that
policy rather than a professional-scoring implementation defect; report both
layers without changing labels after seeing outputs. Do not label an FSP-favored
candidate professionally superior solely to improve a metric.

No improvement over V1 is established. A valid future baseline needs the same
frozen population, independently reviewed labels, candidate-admission convention,
cutoffs and tie/small-pool policies. Any V1 eligibility difference needs an
explicit comparable-pool design, not a comparison across disjoint populations.
Eight purpose-built Needs are not a representative labor-market sample; avoid
population claims, significance claims or unverifiable headline percentages.

## Human review and P6-B2 authorization gate

1. Keep this PROPOSED checkpoint and its commit/byte hash immutable as evidence of
   pre-evaluation authoring. Any revision needs a new identifiable commit/hash.
2. Give professional reviewers the frozen Needs and professional candidate fields,
   excluding FSP evidence, prior grades/rankings, production output and irrelevant
   declared grade. Request independent grades/rationales before showing proposals.
   Randomized display may reduce ID-order anchoring; retain stable IDs for audit.
3. Review all 38 pairs, rubric, proxy scope/cap and uncertainty. Prefer two separate
   knowledgeable reviewers, then documented reconciliation; if only one is
   available disclose it. Review must not invent missing technology evidence.
4. Review FSP business-rule expectations and negative/controlled cases separately.
   Agreement on deterministic rules does not validate professional labels.
5. Record reviewer identity/role, date, per-pair changes, unresolved disagreements
   and approval in an appropriately controlled review record. Do not publish real
   personal details in these synthetic public artifacts. No review is claimed now.
6. Freeze the reviewed label version/hash, applicability rules and metric design
   before observing production outputs. Revisions after observation need explicit
   disclosure and a new version; do not silently retrofit golden labels.
7. Obtain separate authorization for P6-B2. Only then implement an isolated offline
   adapter, deterministic oracles and an evaluator; run completeness/hard filters
   first, regression second, relevance metrics third, with an approved comparable
   baseline if improvement is being claimed. Do not seed production or tune
   weights without a distinct approved task.

## Reproduction and quality gate

From the repository root, with the existing Python environment and dependencies:

```powershell
Get-FileHash -Algorithm SHA256 docs/validation/matching-v2-dataset-v1.json
cd backend
.\.venv\Scripts\python.exe -X utf8 validate_matching_v2_golden.py
.\.venv\Scripts\python.exe -X utf8 -m pytest --noconftest --basetemp=../.cache/p6b1-integrity -q tests/test_matching_v2_golden.py tests/test_matching_v2_dataset.py
.\.venv\Scripts\python.exe -X utf8 -m ruff check validate_matching_v2_golden.py tests/test_matching_v2_golden.py
.\.venv\Scripts\python.exe -X utf8 -m ruff format --check validate_matching_v2_golden.py tests/test_matching_v2_golden.py
.\.venv\Scripts\python.exe -X utf8 -m mypy validate_matching_v2_golden.py
cd ..
git diff --check
git status --short
```

`--dataset` and `--golden` allow explicit read-only artifact paths; the CLI always
checks the exact frozen byte hash before parsing. The programmatic `validate()`
interface assumes the caller has verified input bytes; it validates structural
reference counts and the new artifact, not a replacement for P6-A schema checks.
Run the CLI twice and compare output for determinism. Tests independently assert
literal eligible ID sets, scenario scores, controls, negative coverage, rejection
of missing/duplicate/excluded pairs, malformed grades, missing proxy limitations,
inconsistent evidence, wrong FSP aggregates, extra output/private fields and
false human-review claims. Changed dataset bytes are rejected even if valid JSON.

Only the two new documents, standalone golden validator and its tests are staged.
Inspect the full proposed file and patch, confirm original dataset bytes and all
protected paths unchanged, perform read-only review, then create the Draft PR.
Integrity tests prove coverage/contracts, not expert correctness or live behavior.

**STOP FOR INDEPENDENT LABEL REVIEW. P6-B2 NOT STARTED. DO NOT MERGE.**
