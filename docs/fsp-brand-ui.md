# P7-A — FSP branded platform UI

Status: **STOP FOR HUMAN VISUAL REVIEW**. P7-B is not started. No merge is authorized.

## Scope and base

Branch: `feat/fsp-brand-ui`.
Base: `f5d460f9888b8bfe94a90e495254974a0d2043e7` (latest origin/main verified at bootstrap and again before publication).

Presentation changes reuse the existing global CSS and React components. No UI framework or dependency was added.

- Global header: official Cyrillic logos, existing role navigation, current-page indication.
- Local typography, page headings, cards, controls, feedback, loading text and keyboard focus.
- Candidate: identity, canonical qualification and assessment score, independently declared skills, profile information and explicitly marked MOCK FSP evidence.
- Matching: masked identity, separately styled Professional Fit and Ranking Score, FSP contribution, skills and existing factor disclosure/invitation action.
- Responsive layouts at 375, 768 and 1440 CSS pixels.

Backend, assessment engine/content, ranking/eligibility rules, API contracts and permissions are unchanged. The existing AuthProvider, RoleGate, CandidateEditor, InvitationForm, InviteCandidate, MatchesContent and FspProfile functions were compared against origin/main and are unchanged. Header logout behavior is unchanged. Matching items keep server order; the displayed position uses page offset plus item index only. Scores and evidence come from server responses.

## Brand source

Primary source: the 78-page `Брендбук ФСП.pdf` in the official supplied bundle `фирменный стиль фсп`. The conflicting AI materials on pages 74, 76 and 77 were not used.

Only two used logos, three used font files and their three license/copyright files are included. Brandbook, archives, presentations and print patterns are not copied.

| Repository asset | Original bundle path |
| --- | --- |
| `frontend/public/brand/fsp-full-dark.svg` | `ЛОГО ФСП/Кирилица/Полноцвет/Для темного фона/SVG/Логотип полная верция цвет.svg` |
| `frontend/public/brand/fsp-compact-dark.svg` | `ЛОГО ФСП/Кирилица/Полноцвет/Для темного фона/SVG/Сокращенный лого ФСП цвет.svg` |
| `frontend/src/fonts/JetBrainsMono-Regular.ttf` | `ФИРМЕНЫЕ ШРИФТЫ ФСП/ОСНОВНОЙ JetBrains_Mono.zip → JetBrains_Mono/static/JetBrainsMono-Regular.ttf` |
| `frontend/src/fonts/JetBrainsMono-Bold.ttf` | Same archive, `JetBrains_Mono/static/JetBrainsMono-Bold.ttf` |
| `frontend/src/fonts/TDAText.ttf` | `ФИРМЕНЫЕ ШРИФТЫ ФСП/АКЦЕНТНЫЙ TDAText.zip → TDAText/TDAText.ttf` |
| `frontend/public/brand/licenses/JetBrainsMono-OFL.txt` | JetBrains archive, `JetBrains_Mono/OFL.txt` |
| `frontend/public/brand/licenses/TDAText-LICENSE.txt` | TDA archive, `TDAText/LICENSE.TXT` |
| `frontend/public/brand/licenses/TDAText-COPYRIGHT.txt` | TDA archive, `TDAText/COPYRIGHT.txt` |

The SVG and font bytes are unchanged. License copies normalize CRLF/trailing whitespace only; all legal text and the original bundle remain unchanged. Regression tests verify five original asset SHA-256 hashes and three normalized license-text hashes. Logo aspect ratios are preserved by automatic height. The full logo is used above 600px, the compact official variant at smaller widths, both on the dark header. No SVG color overrides or redrawing.

Both font families retain their supplied SIL Open Font License 1.1 and copyright. JetBrains Mono Regular/Bold is used for interface text/data; TDAText Regular only for h1. Fonts are bundled through `next/font/local`, with no font CDN or OS font installation.

## Tokens

### Official palette

| CSS token | HEX | Role |
| --- | --- | --- |
| `--brand-blue` | #402FFF | Primary actions, links, focus, accents |
| `--brand-digital` | #0A006B | Action hover, Ranking Score, initials |
| `--brand-red` | #EC1D35 | Retained official token and original logo color |
| `--brand-black` | #1B1C21 | Main text and header |
| `--brand-dark` | #2D2E37 | Official additional dark token |
| `--brand-secondary` | #3A3C46 | Secondary text and active navigation |
| `--brand-neutral` | #9B9C9E | Control borders |
| `--brand-gray` | #D9D9D9 | Card borders and header caption |
| `--brand-light` | #EDEDED | Background and neutral chips |

Semantic aliases: `--color-background/surface/text/muted/border/primary/primary-hover`. White surfaces: #FFFFFF. Primary soft background: #F0EEFF.

### Functional feedback colors

These are interface state colors, not additional official brand colors.

| State | Text | Background |
| --- | --- | --- |
| Success | #166534 | #EEF8F0 |
| Error | #A81427 | #FFF1F3 |
| Warning | #854D0E | #FFF8E6 |

Normal text contrast for these pairs and primary/secondary text is tested at >=4.5:1. States also have text and semantic status/alert feedback; color alone is not used to communicate the result.

Spacing scale: 4/8/12/16/24/32px. Control radius: 6px; card radius: 12px. Buttons have a 44px minimum height. Keyboard focus uses a 3px outline, plus a visible skip-to-content link. Optional transitions respect reduced motion.

## Verification

All required frontend commands passed:

- `npm ci` — unchanged lockfile/dependency versions.
- `npm run lint`.
- `npm run typecheck`.
- `npm test` — **126 passed, 0 failed**.
- `npm run build`.
- `git diff --check`.

Six regression tests were added: verified vs declared qualification/skills, canonical unverified and empty values, zero values and escaped content, official asset byte integrity/local fonts, feedback contrast, independent display of server Professional Fit/Ranking/FSP values. Existing privacy, invitation state, stale response, unmount and duplicate action regressions passed.

### Real browser smoke

A separate local SQLite demo database was migrated and populated by existing `--demo --matching-demo` seeds. No production database was used or reset.

- Candidate and Matching inspected at 375, 768 and 1440px: document scroll width equals viewport width; inspected controls/cards/nav stay within the viewport.
- Local fonts and original SVGs loaded. Keyboard skip link/focus tested.
- Candidate login/logout, profile save, assessment navigation.
- FSP ID saved using the existing editor; verify/refresh/unlink/reverify through the real API and supplied MOCK-MULTI registry entry.
- Need navigation and saving the existing ACTIVE Need on mobile.
- Factor disclosure opens and displays server breakdown.
- Invitation sent through the real form, success and disabled repeat action confirmed.
- ACCEPTED confirmed on both sides; contacts absent before acceptance and visible mutually afterwards.
- Unlink did not change persisted invitation snapshots: both candidate/need snapshot SHA-256 hashes are identical before/after unlink.
- Actual API outage produced error feedback without horizontal overflow; explicit retry recovered after restarting the local API.

Four full-page JPEG screenshots were captured from the working application and supplied with the task report: candidate desktop 1440/mobile 375; Matching desktop 1440/mobile 375. Matching screenshots show the first factor disclosure expanded. They use the existing demo data and real server responses, without fabricated DOM/API state.

## Remaining review

Human visual approval is pending. P7-B is not started. Merge requires an explicit user instruction.

Existing dependency audit warning, outside this UI scope: `npm audit` reports five high findings in the eslint-config-next → fast-glob → micromatch → braces development dependency chain. `npm audit --omit=dev` reports zero production dependency vulnerabilities. No dependency upgrade/downgrade was applied; remediation needs a separate task.

The local browser smoke used SQLite, not a separate Docker/PostgreSQL gate. The P7-A specification requires frontend checks; backend/CI configuration is unchanged.
