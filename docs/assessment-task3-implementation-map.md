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
