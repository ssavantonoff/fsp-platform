# Assessment methodology — draft

Status: ASSESSMENT PREWORK READY FOR HUMAN REVIEW. Дата review: 2026-10-06 (Europe/Moscow).

Baseline origin/main: `9892400d57b57fe3104d1871fa3513e56e24c4b5`. Branch: `docs/assessment-validation-prework`. Документ описывает фактический baseline и frozen product semantics; TASK №3 не выполняется.

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

### Independent literal golden cases для TASK №3

Вектор указан строго в порядке PROGRAMMING / HTTP_API / DATABASES / ARCHITECTURE / TESTING_SECURITY_DEBUGGING. Он обозначает агрегаты, не вопросы или варианты ответа. Expectations зафиксированы непосредственно из продуктовых порогов, не вызовом finalize.

| Case | Корректно из 20 | Количество по блокам | Literal competency percentages | Literal score | Literal status | Почему |
|---|---:|---|---|---:|---|---|
| A | 14 | 3 / 3 / 3 / 3 / 2 | 75 / 75 / 75 / 75 / 50 | 70 | PASSED | Оба порога выполнены, включая границы. |
| B | 16 | 4 / 4 / 1 / 4 / 3 | 100 / 100 / 25 / 100 / 75 | 80 | FAILED | Один блок ниже 50%, несмотря на overall. |
| C | 13 | 3 / 3 / 3 / 2 / 2 | 75 / 75 / 75 / 50 / 50 | 65 | FAILED | Все блоки проходят, overall ниже 70. |
| D | 20 | 4 / 4 / 4 / 4 / 4 | 100 / 100 / 100 / 100 / 100 | 100 | PASSED | Все ответы корректны. |
| E | 0 | 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 | 0 | FAILED | Оба условия не выполнены. |

Baseline `test_scoring_and_initial_verification` уже содержит эти пять сочетаний counts/score/status. Competency expectations там получаются выражением из counts. TASK №3 следует усилить независимыми literal competency assertions; новые tests в P2 не написаны.

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

IMPLEMENTATION / PRODUCT CONTRACT MISMATCH по перечисленным в P2 scoring, blueprint, progression и canonical rules не обнаружен. Выбор specialization реализован через профиль, target grade — через assessment start; это соответствует выбранной паре. UI gaps и content quality findings отдельно перечислены в двух соседних документах. Это не разрешение менять contracts.

## Limitations

- Полный source bank сейчас только Backend. Frontend/DataML enum и competencies существуют, source bank отсутствует; start недоступен.
- Четыре вопроса на competency дают coarse resolution: 25 percentage points за ответ. Общие 20 вопросов не измеряют весь спектр практического опыта.
- BASIC/ADVANCED повторяются; retakes имеют гарантированные пересечения baseline pool, что создаёт риск familiarity/memorization.
- Это не psychometric certification: нет pilot calibration, empirical difficulty/discrimination, reliability evidence или связи с hiring outcomes.
- Scores разных grades строго не эквивалентны. Один assessment score — лишь один сигнал, не hiring probability.
- Фактические snapshots теста стабильны, но seed correctness и content quality — разные проверки; структура и PASS thresholds не доказывают соответствие grade rubric.
- Audit имеет IMPORTANT content findings; критерии продукта и thresholds в P2 не изменены.

## UI interpretation boundary

Product illustration: current Backend/Middle/82, attempt Backend/Senior/65/FAILED. UI должен показывать отдельные current qualification и attempt result; Senior FAIL не превращает current в Senior и не обнуляет её. Score 82 в illustration — literal UI input из P2, допустимый integer в read contract. Фактический текущий scoring engine выдаёт кратные пяти значения; для backend-generated regression используется сохраняемый score 80/85 либо existing 100. UI не должен самостоятельно пересчитывать canonical score.

Точное read-only UI gap map: [assessment-task3-implementation-map.md](assessment-task3-implementation-map.md). Исправления и новый TASK №3 требуют отдельной постановки после review.
