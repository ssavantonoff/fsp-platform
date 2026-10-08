# Verified FSP profile and Ranking V2

P4 uses a **MOCK registry / integration prototype**, not a live FSP API or
Keycloak connection. It has no runtime network dependency. The fixture proves
adapter, storage and ranking behavior; it does **not** authenticate ownership of
a real FSP identity. Real integration requires a registry contract and an
identity/ownership authentication mechanism before production use.

## Entered identifiers and verified evidence

`CandidateProfile.fsp_id` remains candidate-entered. Entering it alone gives no
bonus. Candidate profile editing, including ID changes, uses the existing owner
and parent-row lock. Changing the ID atomically clears `fsp_verified_id`,
`fsp_verified_at`, `fsp_synced_at` and removes synced achievements.

`FspRegistryProvider.lookup(fsp_id)` returns immutable normalized records.
`MockFspRegistryProvider` loads `backend/app/content/fsp_registry_mock.json`.
A future real adapter implements the same boundary, normalizes result levels,
validates records and translates provider failures to `RegistryUnavailable`.
The application accepts no client achievements, scores, provider payloads or
verification timestamps.

Successful verify/refresh atomically replaces achievement rows, updates sync
time and preserves the first verification time for the unchanged link. A
provider failure leaves the old snapshot intact. A unique nullable verified-ID
index protects cross-account races; entered IDs need not be unique. The DB
checks identity/timestamp consistency and achievement uniqueness, result level,
scope, year and placement. Each mutation locks the candidate profile; invitation
send uses the same lock to capture coherent send-time FSP evidence.

Candidate-owned endpoints:

- `GET /candidate/fsp`: current entered ID, verification, public achievements,
  sync timestamps and summary. Read-only.
- `POST /candidate/fsp/verify`: verify the current saved ID. Empty JSON `{}`.
- `POST /candidate/fsp/refresh`: replace evidence for a currently verified link.
  Empty JSON `{}`.
- `DELETE /candidate/fsp/verification`: clear verified evidence, preserving the
  entered identifier. Repeating it is safe; the bonus becomes zero.

All mutations use the existing trusted-Origin protection. Missing profile,
wrong role and anonymous behavior follow existing API conventions. Missing or
unknown registry ID returns `404 fsp_not_available`; duplicate verification
returns a generic `409 fsp_verification_conflict` without another account's
identity; provider failure returns `503 fsp_provider_unavailable`.

## Deterministic prototype IDs

Save the ID in the candidate profile, then use **Проверить FSP ID**:

| ID | Evidence | Achievement score | Bonus |
| --- | --- | ---: | ---: |
| `MOCK-EMPTY` | Verified, no achievements | 0 | 0 |
| `MOCK-PARTICIPANT` | One participation | 10 | 0.5 |
| `MOCK-FINALIST` | One finalist result | 45 | 2.25 |
| `MOCK-PRIZE` | One prize winner result | 66 | 3.3 |
| `MOCK-WINNER` | One individual win | 80 | 4 |
| `MOCK-MULTI` | Three competitions including a win | 100 | 5 |
| `MOCK-TEAM` | One team win | 80 | 4 |

Any other ID is missing. Three distinct participant competitions score 30 even
though the fixture table need not contain every possible combination. Fixture
IDs are case-sensitive and are not real personal identifiers.

## Exact formulas and ordering

```text
participation_component = min(distinct_competitions, 3) / 3 * 30

best_result_quality:
  PARTICIPANT = 0
  FINALIST = 0.50
  PRIZE_WINNER = 0.80
  WINNER = 1.00

fsp_achievement_score = clamp(participation_component + best_result_quality * 70, 0, 100)
fsp_bonus = fsp_achievement_score / 100 * 5  # only verified evidence; otherwise 0
ranking_score = 0.95 * professional_fit_unrounded + fsp_bonus
```

Examples: one participant = 10; three participants = 30; one winner = 80;
three or more competitions including a winner = 100. The FSP contribution is
bounded to 5 points in a 100-point final score. Without FSP, final ranking is
95% of Professional Fit; those candidates still match. A sufficiently stronger
Professional Fit still wins against an achievement bonus.

Sort by unrounded ranking descending, unrounded Professional Fit descending,
normalized assessment score descending, candidate ID ascending. Display rounding
does not participate in sorting. Multiple achievements in one competition count
as one participation; the best normalized result supplies quality. Discipline,
recency and team/individual scope do not affect score. Team placements do not
imply individual contribution.

## Assessment independence and privacy

The existing `evaluate_candidate()` calls the original eligibility and
Professional Fit functions; P4 adds a separate ranking signal afterward.
Professional Fit's 45/25/15/15 weights, optional-factor renormalization, grade
compatibility and hard filters are unchanged. FSP never sets verified grade,
assessment score or assessment verification time, changes Assessment history,
bypasses must-have skills, or makes an ineligible candidate eligible.

The employer pool intentionally remains assessment-verified to preserve the
platform's verified qualification promise, as permitted by the organizer Q&A.
Profile skills remain self-declared; the UI does not label them verified.

Employer preview exposes only `fsp_verified`, `fsp_achievement_score`,
`fsp_bonus`, `competition_count`, `best_result_level`, `ranking_score` in addition
to the existing masked preview. Raw FSP IDs, external achievement/competition
IDs and provider payloads never enter employer representations. Candidate-owned
achievement responses also omit external/provider IDs.

New invitation candidate snapshots store these six aggregate fields at send
time. Later refresh, unlink and profile edits do not rewrite history. Old V1
snapshots remain readable without inventing a V2 score. Invitation lifecycle,
ownership and mutual contact unlock only after ACCEPTED are unchanged.

## UI, salary and limitations

Candidate profile separates entered ID from provider verification and displays
achievements, last sync and verify/refresh/unlink controls. Employer cards show
Professional Fit, FSP evidence and Ranking Score separately. Both clearly
label the mock prototype. Salary remains the same server-provided decimal
strings in RUB gross, **до вычета налогов**; no net salary mode is introduced.

No production FSP connection, discipline/recency weighting, notifications,
chat, phone/Telegram, ranking cache or persisted ranking is added. Existing
Matching V1 holdout material is historical evidence and is unchanged; it does
not validate Ranking V2. P4 regression tests prove the specified formulas and
contracts; independent judge-level evaluation belongs to P6.
