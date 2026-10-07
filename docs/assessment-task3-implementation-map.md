# Assessment TASK 3 — implementation evidence

Branch: `feat/assessment-validation-qualification`. Production base: `671ad354658ec9c092b00e6811e6a5a73f66f5af`.
Task 8 evidence snapshot: `ecc29e9b700149485612d2fd707e4634f6c1327e`, 2026-10-07.

**FINAL FULL GATE: PENDING**

Tasks 1–7 completed; this section records actual implementation and checks already run. PostgreSQL full suite, final migrations, Docker, browser desktop/375px and final-head PR CI are not yet claimed. Task 9 actual results will replace the final-gate status only after every mandatory local gate passes. Original P2 provenance and historical gap map are preserved below and describe the old audit baseline, not open implementation gaps at this feature snapshot.

## Completed tasks and commits

| Task | Commit | Actual result |
|---|---|---|
| 1: pure validator | `ea8ce4ba95b5529396c88631f4cf06afe9dcbf1a` | Created validator and tests; 63 tests passed. |
| 1 review fix | `0334f382b230c061f506ff88ea0544218cd63c27` | Grade/Difficulty require actual enum instances; raw strings rejected, enums valid; 66 tests passed. |
| 2: loader | `6e69f9103dd431d4c85ff0995edd78999ed7f3aa` | One read/JSON parse/record parser pass/validator call; safe format and structural errors; 85 validator/loader tests, 1 immutable bank test, 3 seed tests passed. |
| 3: G1–G5 | `1f770e35ca8d54f2a91b824eb57dd5a6c4df9634` | Literal full score dictionaries, five keys/allowed values; wrong/unanswered/overwrite and declared-grade independence. Targeted 12 passed; assessment 64 passed/1 skipped; default full 508 passed/7 skipped. |
| 4: qualification | `1b8c26eb9967fdd7d42b16be9abd239882398823` | Fixed UTC Middle80/T1 → Senior65/T2 FAIL, complete canonical preservation across API and DB; history separate, same-grade FAIL, PASS100→70 and restoration. Targeted 2 passed; assessment 65 passed/1 skipped. |
| 5: dates | `8578f9554168f17d0b358b012988741d09db9585` | Explicit ru-RU UTC 24-hour dates with seconds; null em dash. 15 tests passed in TZ=UTC and TZ=Europe/Moscow; typecheck passed. |
| 6: qualification UI | `68a30e24ca3e26f4342f83e8d1bef848a9609b39` | Reused pure CurrentQualification; dashboard declared/current, result attempt/current, both explanatory thresholds, missing/unverified distinction, server status/privacy. 28 assessment tests and 87 frontend tests passed; lint/typecheck passed. |
| 7: history | `ecc29e9b700149485612d2fd707e4634f6c1327e` | Pure attempt-only history list; exact explanation, empty/PASS/FAIL/IN_PROGRESS, UTC dates/navigation; no fabricated profile. 34 assessment tests and 93 frontend tests passed; lint/typecheck passed. |

## Actual implementation files

| File | Change |
|---|---|
| `backend/app/assessment_validation.py` | Added pure source validation and immutable safe findings; no DB/read/mutation/scoring. |
| `backend/app/question_bank.py` | Integrated validator into load_bank; removed superseded manual checks; SeedQuestion and seed_questions unchanged. |
| `backend/tests/test_assessment_validation.py` | Added 85 core/loader/privacy/order/metadata/graph cases. Temporary sources use scoped module path monkeypatch; repo JSON never edited. |
| `backend/tests/test_assessments.py` | Strengthened original scoring/canonical tests and added focused regressions; production services unchanged. |
| `frontend/src/assessment.ts` | dateLabel only; timer/API/availability/late-save behavior unchanged. |
| `frontend/src/components/assessment-dashboard.tsx` | Pure summary and canonical block using already loaded profile. |
| `frontend/src/components/assessment-result.tsx` | Pure shared qualification view, attempt fields, threshold explanations, cooldown label. |
| `frontend/src/components/assessment-history.tsx` | Pure list inside existing file; hooks/fetch/error/retry remain. |
| `frontend/tests/assessment.test.ts` | Literal UTC, semantic-section, server-status, privacy and history fixtures. |
| `docs/assessment-methodology-draft.md` | Actual platform rubric, structural/qualification/UI evidence and limits. |
| `docs/assessment-bank-audit-draft.md` | Separate technical evidence; original content audit not reclassified. |
| `docs/assessment-task3-implementation-map.md` | This evidence map with original audit provenance retained. |

Approved design/plan were added in documentation commits `253a0724d40271e0890f7b9ba85d80be2cf694dc` and `281217bb9a78e65b0763cb9b1a4e3cc6abf62346`; approved prework was imported unchanged as `fd4d51f251a3418fa666b1358946266fb85573e3` from `39bd567b11497c7d0121cd1c675d7a3f57068a0e`.

## Latest obtained checks before Task 9

Tested implementation SHA: `ecc29e9b700149485612d2fd707e4634f6c1327e`.

| Command | Observed result |
|---|---|
| `python -m pytest -q tests/test_assessments.py` | 65 passed, 0 failed, 1 skipped. |
| `env -u TEST_DATABASE_URL python -m pytest -q -ra` | SQLite: 509 passed, 0 failed, 7 skipped, 5 warnings. |
| `python -m ruff check .` | PASS. |
| `python -m ruff format --check .` | PASS, 45 files formatted. |
| `python -m mypy app` | PASS, 29 source files. |
| `TZ=UTC node --import tsx --test tests/assessment.test.ts` | 34 passed, 0 failed/skipped. |
| `TZ=Europe/Moscow node --import tsx --test tests/assessment.test.ts` | Same 34 passed and literal UTC output. |
| `npm test` | 93 passed, 0 failed/skipped. |
| `npm run lint` / `npm run typecheck` / `npm run build` | PASS. |
| Full Block B diff/scope check | Exactly six authorized files/four commits; frozen backend, assessment-attempt, docs, seed, Matching/Needs, migrations, CI and dependencies unchanged. |

SQLite skips are real exclusions, not PostgreSQL passes: assessment row locks, concurrent email-token consumption, Need row locks/pg_blocking_pids, PostgreSQL NaN handling and three Matching concurrency cases. Existing warnings: Starlette/httpx deprecation and Python sqlite datetime adapter deprecation. No PostgreSQL run or browser screenshot evidence was obtained in Tasks 1–7. Static React HTML tests do not prove browser layout/hooks/loading/retry.

## Canonical and presentation evidence

Middle 4/3/3/3/3: literal80/PASSED at T1=2026-10-07T09:10:00Z; Senior G3: literal65/FAILED at T2=09:25:00Z. Submit verification, profile, availability, detail, repeated submit and DB retain Backend/Middle80/T1. History retains its own Senior score/date/competencies without verification. Same-grade FAIL keeps the full canonical state; PASS70 replaces PASS100 and date. Returning specialization restores highest successful grade/latest success at that grade.

Dashboard separates declared Senior from current Middle; result sections distinguish Senior65/T2 from Middle80/T1. Both thresholds are explanatory aggregate labels, never frontend scoring authority. Missing verification is unavailable data; provided all-null canonical triple is explicitly unverified. History displays attempts only. Finished detail/UI are aggregate-only; no answer review. UTC formatter is host-timezone independent.

## Content readiness and frozen contracts

Content audit remains **75 reviewed / 0 BLOCKER / 27 IMPORTANT / 6 MINOR / 42 without findings**, **NOT_READY** under the reviewed rubric. All 27 IMPORTANT findings remain unresolved. Structural validation is separate from content quality and active live DB availability; inactive historical DB rows are allowed. Only Backend has a production source bank. There is no psychometric validity, scientific grade calibration, cross-grade score equivalence, industry certification, hiring probability or universal developer-grade claim.

Scoring, thresholds, question/option selection, cooldown, canonical synchronization, API/schema/migrations, question JSON, Matching/Needs, seed modes, CI and dependency contracts remain unchanged. No new qualification storage/fetch or endpoint was introduced.

## Final full gate evidence

PENDING — record actual Task 9 PostgreSQL, SQLite, static/Alembic, frontend, Docker/seed, browser desktop/375px, privacy and full feature-integrity evidence here after execution. PR is not yet created; CI is not yet claimed.

---

# Historical P2 gap map — original audit provenance

The following original text is retained as an audit record of baseline `9892400d57b57fe3104d1871fa3513e56e24c4b5`; its future-tense gaps are superseded by the completed-task evidence above.

# Assessment TASK №3 — read-only gap map

Status: ASSESSMENT PREWORK READY FOR HUMAN REVIEW. Baseline origin/main: `9892400d57b57fe3104d1871fa3513e56e24c4b5`. Branch: `docs/assessment-validation-prework`. Review date: 2026-10-06 (Europe/Moscow).

Это inventory текущей реализации и gaps для будущего отдельного ТЗ. Это не implementation plan, запуск TASK №3, разрешение на production changes или решение по содержанию банка. Matching branch и locked holdout не использовались; readiness интеграционного TASK №3 здесь не устанавливается.

## Current backend

| Область | Реальное состояние / source |
|---|---|
| Source bank | 75 Backend records, explicit code/version/supersedes, 4 options; [backend/app/question_bank.py:18](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/question_bank.py#L18). |
| Existing loading checks | Pydantic grade/difficulty enums, version ≥1, prompt min length, exactly four options, unique codes, valid Backend competencies, непустые и разные options; [backend/app/question_bank.py:30](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/question_bank.py#L30). |
| Seed immutability | Повторный seed сохраняет content существующего code и deliberate is_active=false; mismatch отклоняется, replacement деактивирует predecessor без удаления истории; [backend/app/question_bank.py:47](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/question_bank.py#L47). |
| Runtime availability | Active specialization/grade pool; exactly four options и единственная marked choice в каждом active question, minima 1 BASIC/2 APPLIED/1 ADVANCED по пяти competencies; [backend/app/services/assessments.py:187](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/assessments.py#L187). |
| Attempt | SystemRandom selection/shuffle, persisted membership/positions/options, серверный 30-min deadline, одна active attempt; [backend/app/services/assessments.py:280](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/assessments.py#L280). |
| Scoring | 5 points/correct, fixed 20 questions; block percent по четырём; overall ≥70 AND each ≥50; [backend/app/services/assessments.py:125](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/assessments.py#L125). |
| Lifecycle | Lazy timeout, SUBMITTED/TIMEOUT, idempotent submit и atomic verification/result transaction, failed attempt preservation. |
| Canonical verification | Existing CandidateProfile triple; highest grade/latest PASS текущей specialization; constraints и запрет client writes; [backend/app/models.py:138](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/models.py#L138). |
| Specialization restoration | В existing profile service с blocking active attempt и восстановлением/очисткой из истории; [backend/app/services/profiles.py:29](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/profiles.py#L29). |
| API contracts | AttemptOut содержит current CandidateOut verification; history отдаёт AttemptSummary; finished detail без questions/key; [backend/app/assessment_schemas.py:40](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/assessment_schemas.py#L40). |

Фундаментальные IMPLEMENTATION / PRODUCT CONTRACT MISMATCH по правилам P2 не обнаружены. Source schema явно Backend через seed, specialization не является дополнительным start input. Результат FAIL Senior не квалифицируется как Middle; backend сохраняет прежний canonical qualification.

## Current frontend

| Область | Реальное состояние |
|---|---|
| Dashboard | Текущая specialization, declared/verified grades раздельно, canonical score и date; карточки grades, availability/cooldown, explicit start и правила обоих порогов. |
| Result | Attempt specialization/target grade, PASSED/FAILED, score, five competency scores, timeout notice, следующая попытка. Для FAIL: thresholds и список слабых блоков. |
| Current qualification on result | При переданном verification prop выводится отдельный current verified grade. В реальном attempt screen prop передаётся. Полный canonical specialization/score/date не выводится. |
| History | Heading «История попыток», specialization/target grade каждой строки, status/score, started/finished dates, completion reason и competency scores. |
| State/API | Existing assessment.ts API helpers, серверный deadline с monotonic countdown, autosave retry и защита от late saved response; сохранение canonical state через backend. |

Sources: [frontend/src/assessment.ts](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/frontend/src/assessment.ts), [frontend/src/components/assessment-dashboard.tsx:81](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/frontend/src/components/assessment-dashboard.tsx#L81), [frontend/src/components/assessment-result.tsx:7](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/frontend/src/components/assessment-result.tsx#L7), [frontend/src/components/assessment-history.tsx:35](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/frontend/src/components/assessment-history.tsx#L35), [frontend/src/components/assessment-attempt.tsx:128](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/frontend/src/components/assessment-attempt.tsx#L128).

## Already covered

TASK №3 не должен переписывать question selection, scoring, cooldown/progression, lazy timeout, persisted attempt order, role/ownership checks, idempotent completion, atomic canonical update, verification constraints, source versioning или specialization restoration.

Существующие backend tests покрывают blueprint для всех grades, stable reload, output без key, A–E score/status, cooldown boundaries, failed higher/same grade preservation, lower-grade restriction, latest successful retake, specialization restoration, atomic rollback и PostgreSQL concurrency. Банк integrity/version immutability уже проверяется. Тесты не доказывают content quality.

Existing frontend tests покрывают API helpers, clock/timeout, availability labels, четырёхвариантный question view, FAIL thresholds/weak competency, PASS aggregate, retry и late autosave handling. Это не browser end-to-end coverage Dashboard/History и полного qualification snapshot.

Sources: [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/tests/test_assessments.py), [frontend/tests/assessment.test.ts](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/frontend/tests/assessment.test.ts).

## Missing structural validation

Будущий assessment_validation.py, если будет задан TASK №3, должен дополнять existing loader/runtime checks, с одним reuse boundary и без второго scoring/state слоя. Сейчас такой модуль не создаётся.

| Gap | Что требуется позднее / что уже есть |
|---|---|
| Полный source inventory | Явно проверить expected 75 total / 25 per grade и каждый grade×competency bucket 1/3/1. Existing regression проверяет эти counts; load_bank не делает полной source-count проверки. Runtime minima 1/2/1 не подменяют source contract. |
| Identity / metadata | Проверять непустой code, корректность связи code/version/grade/competency и existing Backend identity. Не добавлять specialization field в JSON или новый API contract без отдельного требования. |
| Whitespace / distinctness | Отклонять blank-after-strip stems и визуально одинаковые options после нормализации для сравнения. Existing prompt min_length и raw option distinctness не полностью покрывают это. Нормализация для validation не должна молча менять исторический content. |
| Version / supersedes graph | Проверять self-reference, cycles и конфликтующие replacements. Отсутствующий predecessor допустим для baseline v2 source после удаления прежней записи из source inventory; не объявлять текущий seed fixture невалидным. |
| Diagnostic output | Findings должны иметь code/category/context, не key или answer text в публичных errors/logs/docs. Структурная проверка не решает grade quality и ambiguity автоматически. |
| Source vs active DB | Отдельно описать source validation и runtime eligibility. История сохраняет inactive versions; runtime bank может отличаться от source JSON. Не заставлять любую live DB иметь ровно 75 физически существующих rows. |

Сейчас counts и проблемы loader описаны read-only; production validator, новые schemas, migrations или CI не написаны. Все content corrections требуют human product decision и version/code policy.

## Missing tests

Будущие areas для проверки, не новые tests P2:

1. **Literal A–E:** score/status уже есть в test_scoring_and_initial_verification. Усилить exact five competency expectations независимыми literal числами из methodology; не копировать production formula в expected helper и не создавать дубль пяти существующих cases.
2. **Scoring shape:** зафиксировать exactly five named keys, значения 0/25/50/75/100, wrong и unanswered как zero, отсутствие влияния declared grade. Это усиление oracle, не изменение scoring.
3. **Validator negative fixtures:** неверные totals/bucket mixes, пустой code/blank stem, визуальные duplicates, invalid replacement relations; reuse existing seed/schema fixtures. Structural errors не должны раскрывать key.
4. **Qualification regression:** existing backend higher-grade FAIL сохраняет Middle verification; дополнить проверкой всех трёх canonical полей и current specialization в одном результате. Same-grade FAIL и lower successful score retake уже проверяются; не переписывать механизм.
5. **Frontend FAIL + current:** отдельный literal scenario current Backend/Middle/82 и failed Senior/65. Проверить отдельные specialization/grade/score/date двух сущностей и отсутствие claim о Senior current. 82 — UI illustration из P2; backend-generated totals кратны пяти. UI использует canonical score из API, не пересчитывает его.
6. **Frontend PASS:** coherently passing fixture с пятью literal competency values, датой завершения и обеими threshold conditions. Existing passed-result test меняет status/overall у базового FAIL fixture, сохраняя один competency ниже порога; это test fixture gap, не обнаруженный backend bug. Не переносить эту противоречивую fixture в новые qualification assertions.
7. **Dashboard / history:** render/interaction coverage declared vs verified, unverified/null fields, отсутствующий банк и empty/error/loading; history rows обозначают attempt, не current qualification. Также old successful attempt при иной current qualification.
8. **Randomization:** existing deterministic RNG test показывает возможность полного повторения; future assertions overlap/stability не должны требовать уникальности каждой попытки. Не проверять качество SystemRandom нестабильным вероятностным assertion.

Новые tests сейчас запрещены scope P2 и не добавлены.

## UI gaps

| Area | Уже есть | Gap будущего TASK №3 |
|---|---|---|
| Dashboard: declared/current | Раздельные declared/verified, specialization, canonical score/date. | Нет отдельного полного summary с явной семантикой «подтверждённая квалификация по выбранной специализации». Данные уже присутствуют; не создавать второй state слой. |
| PASS result | Attempt specialization/grade, score, пять блоков, PASSED. | finished_at не выводится на detail result; оба PASS conditions там явно не показаны. Дата available_at — дата следующей попытки, не verification date. |
| FAIL result: overall | Numeric attempt score и текст порогов. | Нет явного состояния overall condition «выполнено/не выполнено», приходится сравнивать числа вручную. |
| FAIL result: blocks | Показываются пять scores и список блоков <50. | Нет отдельного явного итогового состояния второго условия, особенно когда все блоки проходят, а overall FAIL. |
| Current canonical after attempt | Отдельная строка current verified grade, prop приходит из backend. | Отсутствуют current specialization/score/date, поэтому невозможно увидеть сохранённый Middle/82 snapshot целиком рядом с failed Senior/65. Необходимо явно назвать данные attempt и current; canonical остаётся из API. |
| History | Явный heading «История попыток», даты, status и target_grade каждой строки. | Нет пояснения различия с current qualification; historical PASSED detail имеет формулировку в настоящем времени. Нужна ясная семантика исторического результата без подмены current snapshot. |

Observations основаны на source baseline, не runtime screenshots. Dashboard соответствует большинству требований; это уточнение presentation, не утверждение о полном отсутствии declared/verified разделения.

### Manual acceptance scenarios для будущей UI работы

- Открыть Dashboard с declared Senior и current Middle: убедиться, что два уровня, specialization, canonical score/date не смешаны с выбранной карточкой.
- Показать PASS: видны attempt specialization/grade, score, finished date, пять блоков и оба условия.
- Показать FAIL Senior/65 при current Middle/82: attempt помечен FAILED, current specialization/grade/score/date сохранены и отдельно подписаны. Аналогично overall 80 при одном блоке 25: общий score не должен приводить к PASS.
- Открыть старую successful Middle attempt при current Senior: history остаётся историей, current не понижается; проверить empty/error/loading и узкую ширину.
- Проверить unverified current с null triple: не заменять его attempt score/grade; никаких правильных options/solutions на finished screen.

Это acceptance map, проверки нового UI в P2 не выполнялись.

## Documentation gaps

P2 закрывает описание actual blueprint/counts, relative grade/difficulty semantics, exact randomization и повторов, coarse scores/двух PASS conditions, canonical vs attempts, timeout/retakes/restoration, пяти independent literal golden oracles, полного content review и source-based UI gaps.

Остаются human review rubric/readiness, отдельное решение по bank content, empirical validation/pilot evidence и конкретное ТЗ №3 после снятия его интеграционных зависимостей. P2 не доказывает psychometric validity, grading accuracy или hiring probability и не тюнит правила по Matching/holdout.

## Do not change

- Assessment API и выбранную specialization/target-grade semantics.
- Overall/block thresholds, points/question и cooldown/progression.
- Canonical CandidateProfile model, verification writer и database schema.
- Matching formula или её реализацию; они не читались в P2.
- Existing attempt/version history; не редактировать вопрос in-place и не раскрывать key.
- Не добавлять VerifiedQualification persistent entity или параллельный UI storage/business logic.
- Не добавлять Frontend/DataML bank из этой gap map.

## Expected files for future TASK №3

Предварительные areas, подлежащие подтверждению будущим ТЗ; файлы сейчас не меняются:

| File / area | Возможная будущая роль |
|---|---|
| backend/app/assessment_validation.py | Дополнительная source structural validation; файла в baseline нет. |
| backend/app/question_bank.py | Reuse/integration existing loader, если потребуется будущим ТЗ. |
| backend/tests/test_assessments.py | Усиление existing literal/regression assertions. |
| backend/tests/test_assessment_validation.py | Возможные structural validator cases; сейчас не создаётся. |
| frontend/src/components/assessment-dashboard.tsx | Ясность current qualification summary при existing data. |
| frontend/src/components/assessment-result.tsx | Attempt/current labels, даты, оба conditions. |
| frontend/src/components/assessment-history.tsx | Historical semantics и current context. |
| frontend/tests/assessment.test.ts | Literal result/qualification fixtures и regression rendering. |
| frontend/src/assessment.ts | Только reuse existing types/helpers; изменения при подтверждённой необходимости. |
| docs/assessment-*.md | Review/finalization утверждённых документов. |

backend/app/services/assessments.py, assessment_schemas.py и models.py уже содержат рабочий core; эта gap map не требует их переписывания. Question JSON меняется только по отдельному product decision с version/code policy. README/CI/migrations в P2 не меняются; будущие изменения не авторизованы этой картой.
