# Assessment methodology — draft

Status: TASK 3 IMPLEMENTATION EVIDENCE. Task 8 snapshot: 2026-10-07; latest final-gate status is recorded in the implementation map.

Original audit baseline origin/main: `9892400d57b57fe3104d1871fa3513e56e24c4b5`. Original branch: `docs/assessment-validation-prework`; review: 2026-10-06 (Europe/Moscow). Ссылки с этим SHA сохраняют provenance первоначального audit, а не обозначают текущую feature branch.

Implementation evidence: `ecc29e9b700149485612d2fd707e4634f6c1327e`, branch `feat/assessment-validation-qualification`, production base `671ad354658ec9c092b00e6811e6a5a73f66f5af`. Tasks 1–7 реализованы и проверены targeted/default tests. На этом Task 8 snapshot полный PostgreSQL/Docker/browser gate PENDING; последующие результаты, commands, commits и ограничения — в [implementation map](assessment-task3-implementation-map.md). Content audit остаётся **NOT_READY**: 75 reviewed / 0 BLOCKER / 27 IMPORTANT / 6 MINOR / 42 without findings; content remediation не выполнялась.

## What the assessment verifies

Подтверждается выбранная кандидатом пара specialization + target grade. Specialization выбирается в профиле: [backend/app/schemas.py:52](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/schemas.py#L52). При старте backend берёт её из CandidateProfile, а POST принимает только target_grade: [backend/app/assessment_schemas.py:16](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/assessment_schemas.py#L16), [backend/app/services/assessments.py:280](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/assessments.py#L280).

Кандидат не выбирает specialization внутри start payload. Dashboard показывает текущую specialization профиля и отдельные карточки grade. Declared grade — самодекларация, отдельная от target grade и canonical verified grade; она не участвует в выборе вопросов, подсчёте баллов или решении PASS.

## What it does not verify

Assessment не определяет specialization автоматически и не переводит Senior FAIL в Middle PASS. Он не является универсальной сертификацией инженера, доказательством опыта или гарантией hiring success. Один score — один сигнал относительно blueprint выбранного уровня, не вероятность найма.

## Blueprint

Backend MVP: 20 SINGLE_CHOICE вопросов, 30 минут, 4 варианта на вопрос. Пять competencies:

- PROGRAMMING;
- HTTP_API;
- DATABASES;
- ARCHITECTURE;
- TESTING_SECURITY_DEBUGGING.

На каждую competency в attempt: 1 BASIC + 2 APPLIED + 1 ADVANCED. Из исходного пула 3 APPLIED выбираются 2. В source bank каждой пары grade/competency: 1 BASIC + 3 APPLIED + 1 ADVANCED = 5 вопросов. Всего: 75, по 25 Junior/Middle/Senior; по 15 BASIC, 45 APPLIED, 15 ADVANCED. Сам JSON не содержит specialization field; Backend identity задаётся existing seed contract.

Источник: [backend/app/services/assessments.py:33](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/assessments.py#L33), [backend/app/question_bank.py:30](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/question_bank.py#L30). Подробные counts и content findings: [assessment-bank-audit-draft.md](assessment-bank-audit-draft.md).

## Scoring

Корректный сохранённый ответ — 5 points, неправильный или отсутствующий — 0. Overall normalized_assessment_score находится в диапазоне 0–100 с шагом 5. Competency score — процент из четырёх вопросов, значения 0/25/50/75/100. Отдельных весов grades/difficulties нет; штрафа за ошибку нет. Знаменатель не уменьшается из-за пропуска ответа.

Источники: [backend/app/services/assessments.py:125](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/assessments.py#L125), [backend/app/models.py:138](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/models.py#L138). Этот документ не содержит scoring implementation и не вычисляет oracles через production function.

## Passing

PASS требует одновременно overall ≥70 и каждой из пяти competencies ≥50%. Это минимум 14 корректных ответов overall и минимум 2 в каждом блоке. Невыполнение любого условия даёт FAILED. Оценка результата относится к выбранному grade; fallback qualification на более низкий grade не создаётся.

### Implemented independent literal golden cases G1–G5

Вектор указан строго в порядке PROGRAMMING / HTTP_API / DATABASES / ARCHITECTURE / TESTING_SECURITY_DEBUGGING. Он обозначает агрегаты, не вопросы или варианты ответа. Expectations зафиксированы непосредственно из продуктовых порогов, не вызовом finalize.

| Case | Корректно из 20 | Количество по блокам | Literal competency percentages | Literal score | Literal status | Почему |
|---|---:|---|---|---:|---|---|
| G1 | 14 | 3 / 3 / 3 / 3 / 2 | 75 / 75 / 75 / 75 / 50 | 70 | PASSED | Оба порога выполнены, включая границы. |
| G2 | 16 | 4 / 4 / 1 / 4 / 3 | 100 / 100 / 25 / 100 / 75 | 80 | FAILED | Один блок ниже 50%, несмотря на overall. |
| G3 | 13 | 3 / 3 / 3 / 2 / 2 | 75 / 75 / 75 / 50 / 50 | 65 | FAILED | Все блоки проходят, overall ниже 70. |
| G4 | 20 | 4 / 4 / 4 / 4 / 4 | 100 / 100 / 100 / 100 / 100 | 100 | PASSED | Все ответы корректны. |
| G5 | 0 | 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 | 0 | FAILED | Оба условия не выполнены. |

`test_scoring_and_initial_verification` теперь использует literal overall/status и полный literal словарь пяти competency scores с IDs G1–G5. Проверяются точные ключи и допустимые значения. Oracles не вычисляются формулой из counts и не вызывают production finalize. `test_wrong_and_unanswered_score_zero` проходит actual save/submit path, включая correct→wrong overwrite. `test_declared_grade_does_not_affect_result` сохраняет Backend/Middle G1 при каждом declared grade. Это техническая regression evidence, не научная калибровка уровней.

## Source structural validation

[assessment_validation.py](../backend/app/assessment_validation.py) содержит pure `validate_source_bank`: exact 75 source records, 25 per grade, 1 BASIC / 3 APPLIED / 1 ADVANCED для каждой пары grade/competency; blank/duplicate codes, blank prompts, четыре непустых options и whitespace-equivalent duplicates. Grade/Difficulty требуют actual enum instances, competency — Backend string membership, version — strict integer >=1. Self-reference, conflicting supersedes ownership и cycles отвергаются; отсутствующий historical predecessor допустим. Новой naming regex или inferred version order нет.

Findings deterministic и содержат только category/code/safe context. Validator не читает файлы/DB и не мутирует записи. Loader читает JSON один раз, проверяет list root, использует existing SeedQuestion parser и один вызов validator. JSON/root/Pydantic errors дают фиксированное `Invalid assessment source format` с подавленным raw exception chaining; structural ValueError сериализует только safe findings, без prompt/options/key/index/solution.

SOURCE inventory и ACTIVE LIVE DB availability различны. Runtime собирает attempt по active DB rows и minima 1/2/1; physical DB может хранить inactive historical predecessors и не обязана содержать ровно 75 rows. Seed сохраняет immutable published content, deliberate inactive state и historical links; вопросник и business logic не изменены. Эти проверки не классифицируют distractors, grade fit или psychometric validity.

## Grade rubric

| Grade | Что измеряется | Ограничение для audit |
|---|---|---|
| JUNIOR | Фундамент, стандартные практические ситуации, локальные задачи одного компонента, базовые инструменты и типовые ошибки | Не требуется системный архитектурный опыт. |
| MIDDLE | Применение знаний, выбор решения и trade-offs, API/transactions, debugging/performance, взаимодействие компонентов | Для APPLIED/ADVANCED недостаточно узнавания одного термина или очевидно безопасной формулировки. |
| SENIOR | Архитектурные trade-offs, concurrency/consistency, failure modes, scaling, security/observability, системные решения | Нужна проверка инженерного суждения; редкое слово или тема распределённых систем сами по себе не доказывают Senior demand. |

Rubric применяется ко всему stem + альтернативам, не только к названию темы. BASIC может быть фундаментальным входным вопросом уровня; не каждый короткий BASIC считается дефектом. IMPORTANT фиксируется, когда требуемое суждение явно ниже grade/difficulty или альтернативы практически устраняют содержательный выбор. Это экспертная классификация, не эмпирическая difficulty estimate.

## Difficulty interpretation

BASIC / APPLIED / ADVANCED относительны к конкретному grade. Нельзя выводить математический порядок Senior BASIC > Middle ADVANCED. Scores 90 Senior и 90 Middle не являются одинаковой абсолютной мерой профессиональной силы: отличаются blueprint и содержание. Difficulty labels не меняют стоимость ответа.

## Randomization

Фактический алгоритм в [backend/app/services/assessments.py:171](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/assessments.py#L171) и [backend/app/services/assessments.py:280](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/assessments.py#L280):

1. Берутся active вопросы текущих specialization и grade, упорядоченные по code.
2. Для каждой competency/difficulty выбирается sample без возвращения в пределах этого bucket; обычный источник — SystemRandom, в tests возможен детерминированный RNG.
3. BASIC/ADVANCED в исходном baseline pool имеют по одному вопросу, поэтому они повторяются в каждой попытке того же grade при неизменном active bank.
4. Два APPLIED выбираются из трёх независимо для каждой новой попытки; история показов не используется. Две такие выборки одной competency обязательно пересекаются хотя бы одним вопросом.
5. После выбора shuffle применяется к общему списку questions и отдельно к options каждого question.
6. Membership, question positions и option order сохраняются в AssessmentAttemptQuestion. Reload использует сохранённый набор и порядок, не генерирует новый.

При неизменном baseline bank две попытки одного grade имеют не менее 15 общих question IDs: десять BASIC/ADVANCED и не менее пяти APPLIED. Верхняя граница — все 20. Полное совпадение возможных наборов и порядков не запрещено. «Каждый тест уникален» не утверждается. При расширении/деактивации active DB bank эти source-specific числа могут измениться.

Набор attempt устойчив через API. Вопросы/варианты читаются по сохранённым ссылкам; content immutable обеспечивается seed/version contract, а не копированием всего текста в attempt или запретом любого ручного SQL UPDATE. Изменение содержания существующего code отвергается seed; новая версия получает новый code, predecessor может деактивироваться без удаления истории. Сам seed не является shuffle engine: [backend/app/question_bank.py:47](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/question_bank.py#L47).

## Verification semantics

Единственный canonical current qualification — поля CandidateProfile для его текущей specialization: verified_grade, normalized_assessment_score, assessment_verified_at. DB consistent_verification требует либо три null, либо три заполненных значения. CandidateWrite их не принимает. Второй VerifiedQualification/state слой не требуется.

После PASS synchronize_verification выбирает самый высокий успешно пройденный grade в текущей specialization, внутри grade — последний PASS по finished_at. Поэтому same-grade успешная пересдача может заменить более высокий предыдущий score более низким успешным; это не best-ever score. FAIL сохраняет canonical qualification.

Смена specialization вне активной попытки восстанавливает highest/latest PASS для новой specialization либо очищает triple. Возврат восстанавливает прежнюю qualification из истории. История не удаляется. В baseline нет срока действия verification. Источники: [backend/app/services/assessments.py:96](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/assessments.py#L96), [backend/app/services/profiles.py:29](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/profiles.py#L29), [backend/app/models.py:138](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/models.py#L138).

Attempt history — отдельные исторические результаты с собственной specialization, target_grade, score, status и датами. Detail endpoint отдаёт актуальный CandidateProfile в verification даже при просмотре старой попытки. Исторический PASS не обязан совпадать с текущей qualification; failed higher-grade attempt не повышает и не стирает её.

### Implemented qualification regression evidence

Fixed aware UTC times: Backend/Middle starts 2026-10-07T09:00:00Z, finishes T1=2026-10-07T09:10:00Z; 4/3/3/3/3 gives literal 80/PASSED and 100/75/75/75/75. Backend/Senior starts 09:20:00Z, finishes T2=09:25:00Z; G3 gives literal 65/FAILED and 75/75/75/50/50. Current canonical state остаётся Backend/Middle/80/T1 через Senior submit verification, profile, availability, detail, repeated submit и persisted CandidateProfile. History отдельно сохраняет Middle PASSED80/T1 и Senior FAILED65/T2, без current verification.

Same-grade FAIL сравнивает всю canonical четверку specialization/grade/score/date. Последующий same-grade PASS70 заменяет прежний PASS100 и дату новым successful finished_at; highest-score-wins не используется. Switch без успешной истории очищает triple, возврат восстанавливает highest successful grade/latest PASS внутри grade. Tests не меняют synchronization/service.

## Retakes / progression

- На один CandidateProfile разрешена одна IN_PROGRESS попытка; profile lock и partial unique index защищают повторный/concurrent start.
- Нужны profile, verified email и consent при старте. Отзыв consent после старта не блокирует завершение или историю.
- После последней завершённой попытки той же пары specialization/grade: FAILED → 7 дней, PASSED → 90 дней. На точной границе cooldown новый start допускается.
- Более высокий grade может быть доступен независимо от cooldown другого grade. Grade ниже canonical verified_grade недоступен.
- Во время неистёкшей активной попытки specialization switch запрещён; declared grade и остальные разрешённые поля профиля можно редактировать.
- Таймер серверный, не останавливается от закрытия страницы. Паузы/продления не предусмотрены.

### Completion / timeout

completion_reason имеет SUBMITTED либо TIMEOUT, отдельно от PASSED/FAILED. Submit идемпотентен; attempt result и canonical update коммитятся вместе. Повтор submit не создаёт новый результат.

На deadline expires_at ≤ server now попытка завершается по уже сохранённым ответам. Timeout может дать PASSED. TIMEOUT finished_at равен deadline, даже если обнаружен позже; cooldown считается от deadline. SUBMITTED finished_at — время финализации.

Lazy timeout вызывается чтением attempt/current, availability/history, answer mutation, submit, новым start и specialization switch. Это существующее поведение: часть read endpoints может финализировать истёкшую попытку. После завершения ответы не меняются, questions в detail пусты; key/solutions/explanations кандидату не выдаются.

Источники: [backend/app/services/assessments.py:125](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/assessments.py#L125), [backend/app/services/assessments.py:159](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/assessments.py#L159), [backend/app/services/assessments.py:396](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/assessments.py#L396), [backend/app/services/assessments.py:444](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/assessments.py#L444).

## Product contract comparison

IMPLEMENTATION / PRODUCT CONTRACT MISMATCH по перечисленным в P2 scoring, blueprint, progression и canonical rules не обнаружен. Выбор specialization реализован через профиль, target grade — через assessment start; это соответствует выбранной паре. Технические presentation gaps закрыты Tasks 5–7; content quality findings сохранены. Это не разрешение менять contracts.

## Limitations

- Полный source bank сейчас только Backend. Frontend/DataML enum и competencies существуют, source bank отсутствует; start недоступен.
- Четыре вопроса на competency дают coarse resolution: 25 percentage points за ответ. Общие 20 вопросов не измеряют весь спектр практического опыта.
- BASIC/ADVANCED повторяются; retakes имеют гарантированные пересечения baseline pool, что создаёт риск familiarity/memorization.
- Это не psychometric certification: нет pilot calibration, empirical difficulty/discrimination, reliability evidence или связи с hiring outcomes.
- Scores разных grades строго не эквивалентны. Один assessment score — лишь один сигнал, не hiring probability.
- Фактические snapshots теста стабильны, но seed correctness и content quality — разные проверки; структура и PASS thresholds не доказывают соответствие grade rubric.
- Audit имеет IMPORTANT content findings; критерии продукта и thresholds в P2 не изменены.

## UI interpretation boundary

Dashboard отдельно показывает `Заявленный уровень` и `Текущая подтверждённая квалификация`. Reused pure CurrentQualification использует только CandidateProfile specialization/verified grade/canonical score/date. All-null triple: `Подтверждённой квалификации пока нет.` Omitted verification prop: данные недоступны, а не доказанная unverified qualification; fallback из declared/target/latest attempt нет.

Result heading `Результат попытки` относится к attempt specialization/target/server status/score/finished_at и пяти competency rows. Отдельно поясняются overall >=70 и every competency >=50 с состояниями `Выполнено` / `Не выполнено`; missing Backend keys/null/empty scores не проходят второе условие. Эти labels не переопределяют server status. Senior FAILED65/T2 и current Middle80/T1 проверяются в разных semantic sections.

History говорит `История попыток не заменяет текущую подтверждённую квалификацию.` Rows обозначены как `Попытка`, PASSED относится к historical attempt, IN_PROGRESS остаётся отдельным состоянием. Profile не запрашивается и qualification не фабрикуется. Dates explicit ru-RU UTC, 24h, включая секунды; completed/verification/cooldown dates различаются. `Следующая попытка на этом уровне — не ранее` — cooldown boundary, не guaranteed availability. Finished response questions=[]; UI не показывает options/answer review/solutions.

Static render/API tests подтверждают эти semantics, не browser layout/hooks. На Task 8 snapshot browser desktop/375px и final PostgreSQL gate PENDING; фактический Task 9 итог фиксируется отдельно в implementation map. Нет claims о scientific grade calibration, cross-grade score equivalence, industry certification, hiring probability или universal objective developer grade. Platform-verified qualification означает результат по документированной platform rubric; 27 IMPORTANT human content findings не исправлены.
