# Blind Matching Holdout v1

**Status: DRAFT_FOR_HUMAN_FREEZE**

Baseline origin/main: `9892400d57b57fe3104d1871fa3513e56e24c4b5`. Branch: `docs/matching-holdout-v1`.

Создан: 2026-10-05 14:32:03 UTC. Все 12 профилей и 4 Need вымышленные.

## Purpose

Набор фиксирует предварительное экспертное ожидание до review Employer Matching Engine. После реализации будут отдельно проверены hard eligibility и qualitative ranking. Он не доказывает универсальное качество найма и не предназначен для выбора реальных людей.

Данные и ожидания вручную заданы одновременно в JSON; Markdown отображает те же значения. Никакие Matching scores или outputs для выбора профилей и порядка не использовались.

## Independence rules

- Перед созданием выполнены git fetch origin, git status и git rev-parse origin/main; рабочее дерево чистое. Зафиксирован `9892400d57b57fe3104d1871fa3513e56e24c4b5`.
- В baseline есть фундамент и Candidate Assessment; production Employer Needs/Matching отсутствует.
- Ветка Олега feat/employer-needs-matching, её PR/diff, implementation plan O1 и Matching-файлы не читались и не checkout.
- Demo ranking и вычисленные scores не просматривались. Professional Fit не вычислялся; производственные коэффициенты не использовались.
- Для данных использованы только этот baseline main, его Skill catalog и ТЗ P1. Предыдущая работа исполнителя относилась к Candidate Assessment, а не Matching.

## Interpretation and compatibility

Для этого черновика higher grade считается compatible overqualification. Это буквальная трактовка требования P1 о compatible overqualified candidate, а не вывод из будущей реализации:

| Required grade | Compatible verified grades |
|---|---|
| JUNIOR | JUNIOR, MIDDLE, SENIOR |
| MIDDLE | MIDDLE, SENIOR |
| SENIOR | SENIOR |

Hard eligibility: consent=true, совпадающая specialization, непустой compatible verified_grade, все must-have skills и непустой assessment score. Optional skills и target experience — мягкие предпочтения. Опыт ниже ориентира не исключает кандидата.

Assessment score — сигнал результата своего grade/blueprint. Middle 90 и Senior 90 не являются психометрически эквивалентными; универсальная шкала силы из них не строится. В rationale сравнения scores одного grade возможны, а межуровневые решения используют qualitative соответствие Need. Достаточный стаж и точное попадание в ориентир не превращены в математический коэффициент или автоматический штраф за больший стаж.

Каталог baseline: `backend/app/seed.py`, skills: Python, Django, FastAPI, PostgreSQL, React, TypeScript, SQL. В наборе используется его подмножество Python/FastAPI/Django/PostgreSQL/SQL, только names, без UUID.

## Need definitions

| Need | Position | Specialization | Grade | Must-have | Nice-to-have | Target years |
|---|---|---|---|---|---|---|
| H1 | Middle Backend Developer — API-сервисы | BACKEND | MIDDLE | Python, FastAPI | PostgreSQL, SQL, Django | 3 |
| H2 | Junior Python Backend Developer | BACKEND | JUNIOR | Python | Django, SQL | 1 |
| H3 | Senior Backend Developer — платформа данных | BACKEND | SENIOR | Python, PostgreSQL | SQL, Django, FastAPI | 7 |
| H4 | Middle Django Backend Developer — сервисы обработки данных | BACKEND | MIDDLE | Python, Django, PostgreSQL | SQL, FastAPI | 6 |

### H1 rationale

Нужен разработчик для самостоятельной повседневной работы с Python API. Важны подходящий Middle grade и практический опыт около трёх лет; работа с PostgreSQL/SQL полезна, Django помогает интеграции с соседним сервисом.

### H2 rationale

Базовые backend-задачи под наставничеством. Приоритет — Junior либо близкий по уровню профиль, опыт около года и фундамент Django/SQL. Дополнительные API-framework навыки не обязательны.

### H3 rationale

Нужен подтверждённый Senior для архитектурно самостоятельной работы с реляционными данными. Явный SQL важен для глубины работы с данными; Django полезен для существующих приложений, FastAPI — для API-интеграций. Опыт около семи лет — ориентир, а не hard minimum. Специфический архитектурный опыт не приписывается кандидату из общего стажа.

### H4 rationale

Нужна самостоятельная работа с существующим Django/PostgreSQL backend. Желательны опыт около шести лет и явный SQL; FastAPI помогает смежным интеграциям. Это более опытный и ориентированный на данные профиль, чем H1; target experience остаётся мягким предпочтением.

## Candidate definitions

Один и тот же набор C01–C12 используется для всех четырёх Need. Score — только normalized_assessment_score; имена, контакты, зарплата, declared_grade, даты, FSP/recency signals отсутствуют.

| Candidate | Specialization | Verified grade | Assessment | Consent | Skills | Years |
|---|---|---|---|---|---|---|
| C01 | BACKEND | MIDDLE | 85 | true | Python, FastAPI, Django, PostgreSQL | 3 |
| C02 | BACKEND | SENIOR | 90 | true | Python, FastAPI, Django, PostgreSQL, SQL | 7 |
| C03 | BACKEND | SENIOR | 100 | true | Python, FastAPI, PostgreSQL | 3 |
| C04 | BACKEND | MIDDLE | 95 | true | Python, FastAPI, Django, PostgreSQL, SQL | 1 |
| C05 | BACKEND | SENIOR | 70 | true | Python, FastAPI, Django, PostgreSQL, SQL | 12 |
| C06 | BACKEND | SENIOR | 80 | true | Python, FastAPI, PostgreSQL, SQL | 5 |
| C07 | BACKEND | JUNIOR | 85 | true | Python, Django, SQL | 1 |
| C08 | BACKEND | SENIOR | 85 | true | Python, Django, PostgreSQL, SQL | 6 |
| C09 | FRONTEND | MIDDLE | 90 | true | Python, FastAPI, Django, PostgreSQL, SQL | 3 |
| C10 | BACKEND | MIDDLE | 95 | false | Python, FastAPI, Django, PostgreSQL, SQL | 4 |
| C11 | BACKEND | null | null | true | Python, FastAPI, Django, PostgreSQL, SQL | 4 |
| C12 | BACKEND | SENIOR | null | true | Python, FastAPI, Django, PostgreSQL, SQL | 8 |

- **C01:** Сильный exact Middle для H1: подходящий стаж и полезный stack; SQL отсутствует.
- **C02:** Полный stack и достаточный стаж; overqualified для Middle/Junior, exact Senior для H3.
- **C03:** Очень высокий результат Senior assessment; отсутствуют Django и SQL, стаж ниже ориентира H3.
- **C04:** Exact Middle с полным stack и сильным результатом своего уровня; всего один год опыта.
- **C05:** Большой опыт и полный stack; результат Senior assessment на нижней границе PASS.
- **C06:** Опыт пять лет, SQL и API-stack; отсутствует Django — optional для H1/H3 и must-have для H4.
- **C07:** Exact Junior для H2; несовместим с Middle/Senior Need, нет FastAPI и PostgreSQL.
- **C08:** Senior с data/Django stack и шестью годами опыта; нет FastAPI — must-have H1 и optional H3/H4.
- **C09:** Wrong-specialization case с привлекательными остальными полями; только синтетический snapshot.
- **C10:** Consent=false при остальных привлекательных полях.
- **C11:** Unverified: grade и score отсутствуют, остальные поля не должны заменять verification.
- **C12:** Некорректный входной snapshot: grade указан, score отсутствует; отдельный defensive exclusion case.

### Research fixture boundaries

- C12 — намеренно некорректный snapshot с grade без score. Он не представим в current main БД из-за consistent_verification; будущая проверка должна использовать реальную input/validation boundary без ослабления constraint и без заполнения score.
- C09 — синтетический wrong-specialization snapshot; он не утверждает наличие production Frontend assessment bank.
- Поля являются проекцией для research; контактов, declared_grade, дат, FSP bonus и profile recency нет.

C12 не следует исправлять до запуска, добавляя score или понижая grade: это удалит missing-score case. Нельзя отключать constraints ради вставки. После появления реализации заранее выбрать проверяемую реальную input/validation boundary для такого snapshot. Если она недоступна, отметить C12 как NOT_EXECUTABLE, а не PASS: dataset-level вывод о нулевых violations нельзя заявить без проверки всех отрицательных случаев. Это ограничение исполнения fixture не меняет заранее зафиксированный EXCLUDED.

Остальные профили — синтетические research projections. Для будущего изолированного окружения mapping UUID и необходимых служебных полей должен быть описан отдельно, с сохранением заданных ranking/eligibility полей. Никаких production profiles или canonical verification через клиентский API создавать не требуется.

## Eligibility expectations

Ниже явно перечислены все C01–C12 для каждой Need. EXCLUDED не может входить в Expected Top-5. Missing assessment у C11 и C12 фиксируется отдельно от отсутствия grade. В случаях нескольких нарушений приведены все известные причины.

### H1

| Candidate | Expected eligibility | Reason |
|---|---|---|
| C01 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, score указан. |
| C02 | ELIGIBLE | BACKEND, consent=true, compatible higher grade, все must-have, score указан. |
| C03 | ELIGIBLE | BACKEND, consent=true, compatible higher grade, все must-have, score указан. |
| C04 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, score указан. |
| C05 | ELIGIBLE | BACKEND, consent=true, compatible higher grade, все must-have, score указан. |
| C06 | ELIGIBLE | BACKEND, consent=true, compatible higher grade, все must-have, score указан. |
| C07 | EXCLUDED | JUNIOR ниже требуемого MIDDLE. Отсутствует must-have FastAPI. |
| C08 | EXCLUDED | Отсутствует must-have FastAPI. |
| C09 | EXCLUDED | FRONTEND не совпадает с BACKEND Need. |
| C10 | EXCLUDED | personal_data_consent=false. |
| C11 | EXCLUDED | verified_grade=null: нет подтверждённой квалификации. normalized_assessment_score=null. |
| C12 | EXCLUDED | normalized_assessment_score=null, несмотря на указанный SENIOR grade. |

### H2

| Candidate | Expected eligibility | Reason |
|---|---|---|
| C01 | ELIGIBLE | BACKEND, consent=true, compatible higher grade, все must-have, score указан. |
| C02 | ELIGIBLE | BACKEND, consent=true, compatible higher grade, все must-have, score указан. |
| C03 | ELIGIBLE | BACKEND, consent=true, compatible higher grade, все must-have, score указан. |
| C04 | ELIGIBLE | BACKEND, consent=true, compatible higher grade, все must-have, score указан. |
| C05 | ELIGIBLE | BACKEND, consent=true, compatible higher grade, все must-have, score указан. |
| C06 | ELIGIBLE | BACKEND, consent=true, compatible higher grade, все must-have, score указан. |
| C07 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, score указан. |
| C08 | ELIGIBLE | BACKEND, consent=true, compatible higher grade, все must-have, score указан. |
| C09 | EXCLUDED | FRONTEND не совпадает с BACKEND Need. |
| C10 | EXCLUDED | personal_data_consent=false. |
| C11 | EXCLUDED | verified_grade=null: нет подтверждённой квалификации. normalized_assessment_score=null. |
| C12 | EXCLUDED | normalized_assessment_score=null, несмотря на указанный SENIOR grade. |

### H3

| Candidate | Expected eligibility | Reason |
|---|---|---|
| C01 | EXCLUDED | MIDDLE ниже требуемого SENIOR. |
| C02 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, score указан. |
| C03 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, score указан. |
| C04 | EXCLUDED | MIDDLE ниже требуемого SENIOR. |
| C05 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, score указан. |
| C06 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, score указан. |
| C07 | EXCLUDED | JUNIOR ниже требуемого SENIOR. Отсутствует must-have PostgreSQL. |
| C08 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, score указан. |
| C09 | EXCLUDED | FRONTEND не совпадает с BACKEND Need. MIDDLE ниже требуемого SENIOR. |
| C10 | EXCLUDED | personal_data_consent=false. MIDDLE ниже требуемого SENIOR. |
| C11 | EXCLUDED | verified_grade=null: нет подтверждённой квалификации. normalized_assessment_score=null. |
| C12 | EXCLUDED | normalized_assessment_score=null, несмотря на указанный SENIOR grade. |

### H4

| Candidate | Expected eligibility | Reason |
|---|---|---|
| C01 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, score указан. |
| C02 | ELIGIBLE | BACKEND, consent=true, compatible higher grade, все must-have, score указан. |
| C03 | EXCLUDED | Отсутствует must-have Django. |
| C04 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, score указан. |
| C05 | ELIGIBLE | BACKEND, consent=true, compatible higher grade, все must-have, score указан. |
| C06 | EXCLUDED | Отсутствует must-have Django. |
| C07 | EXCLUDED | JUNIOR ниже требуемого MIDDLE. Отсутствует must-have PostgreSQL. |
| C08 | ELIGIBLE | BACKEND, consent=true, compatible higher grade, все must-have, score указан. |
| C09 | EXCLUDED | FRONTEND не совпадает с BACKEND Need. |
| C10 | EXCLUDED | personal_data_consent=false. |
| C11 | EXCLUDED | verified_grade=null: нет подтверждённой квалификации. normalized_assessment_score=null. |
| C12 | EXCLUDED | normalized_assessment_score=null, несмотря на указанный SENIOR grade. |

## Expected Top-5

Позиции начинаются с 1. Это фиксированный qualitative ordering, без вычисленного Fit. Close call означает неопределённость экспертного предпочтения; единый порядок всё равно задан. Он не будет меняться после просмотра production output.

### H1

1. **C01** — Exact Middle, опыт ровно около целевого и полезные PostgreSQL/Django. Выше C04: дополнительный опыт перевешивает более высокий Middle assessment и SQL у C04; close call.
2. **C04** — Exact Middle с полным optional stack и сильным результатом Middle assessment. Выше C02 выбрана точность grade для API-роли; один год опыта против семи у C02 делает сравнение спорным (close call).
3. **C02** — Полный stack и достаточный опыт. Выше C03: SQL/Django и более широкий опыт предпочтены более высокому Senior assessment и стажу ближе к ориентиру у C03; close call.
4. **C03** — Высокий результат Senior assessment и три года опыта соответствуют API-контексту. Выше C06: этот сигнал качества предпочтён наличию SQL и большему опыту у C06; close call, Django нет у обоих.
5. **C06** — SQL/PostgreSQL и достаточный опыт для API-роли. Выше C05: более сильный результат в том же Senior assessment предпочтён полному optional stack и двенадцати годам опыта C05; отсутствие Django — уступка.

### H2

1. **C07** — Exact Junior, один год опыта, оба optional skill Django/SQL. Профиль наиболее точно соответствует базовым задачам под наставничеством.
2. **C04** — Совместимый Middle, один год опыта и полный полезный Django/SQL stack. Выше C01: более сильный результат внутри Middle и SQL предпочтены дополнительным двум годам опыта C01.
3. **C01** — Middle ближе к требуемому Junior, чем Senior-профили; три года опыта и Django полезны. Выше C02: близость grade/стажа предпочтена SQL и семи годам опыта C02; close call, баллы разных grades напрямую не сравниваются.
4. **C02** — Оба optional skill и сильный результат Senior assessment. Выше C08: при одинаковом полезном H2 stack выбран более высокий результат внутри Senior; стаж C08 на год ближе к ориентиру — встречный аргумент.
5. **C08** — Оба optional skill Django/SQL. Выше C06: полнота фундаментального stack и более сильный результат в том же Senior assessment предпочтены стажу C06 на год ближе к ориентиру; close call. FastAPI не нужен H2.

### H3

1. **C02** — Exact Senior, семь лет опыта, полный optional stack. Сбалансированное совпадение с данными, существующими приложениями и API-интеграциями.
2. **C08** — SQL/Django и шесть лет опыта подходят data-контексту. Выше C06: Django, более сильный Senior assessment и опыт ближе к ориентиру предпочтены FastAPI у C06; close call.
3. **C06** — SQL/FastAPI и пять лет опыта; оценка Senior выше C05. Выше C05: этот результат и опыт ближе к ориентиру предпочтены Django и большему стажу C05; close call, пять лет не являются hard rejection.
4. **C05** — Полный optional stack, включая SQL/Django, и большой опыт. Выше C03: data-fit и достаточный опыт предпочтены высокому Senior assessment C03; close call из-за результата 70 против 100 в одном grade.
5. **C03** — Exact Senior с высоким результатом своего assessment. Стаж три года и отсутствие SQL/Django ограничивают qualitative data-fit; высокий score сам по себе не заменяет совпадение с Need.

### H4

1. **C02** — Полный Django/PostgreSQL/SQL stack и семь лет опыта близки ориентиру шесть. Совместимый Senior здесь предпочтён менее опытным exact Middle.
2. **C08** — Шесть лет опыта, Django/PostgreSQL/SQL. Ниже C02: отсутствует FastAPI и результат Senior немного ниже, хотя стаж точнее совпадает. Выше C01: data-fit и опыт предпочтены exact Middle и FastAPI у C01; close call.
3. **C01** — Exact Middle, Django/PostgreSQL и три года опыта. Выше C04: больший опыт предпочтён SQL и более сильному результату в том же Middle assessment у C04; close call для data-роли.
4. **C04** — Exact Middle с полным optional stack и сильным результатом своего уровня. Выше C05: точность grade и этот сигнал качества предпочтены двенадцати годам опыта C05; close call, Senior 70 не трактуется как психометрически эквивалентный Middle score.
5. **C05** — Полный stack и большой опыт обеспечивают допустимость. Профиль поставлен после C04 в спорном сравнении подходящего grade/результата и опыта. Это не утверждение, что меньший стаж всегда лучше.

## Ambiguous trade-offs

Для каждой Need зафиксированы три неоднозначных сравнения. Они содержат встречные преимущества; простая абсолютная доминация всех профилей одним кандидатом отсутствует.

| Need | Pair | Fixed preference | Why it is a close call |
|---|---|---|---|
| H1 | C01 vs C04 | C01 | Middle 85, опыт 3, без SQL против Middle 95, опыт 1, полный stack; выбран опыт для самостоятельной API-работы. |
| H1 | C04 vs C02 | C04 | Exact Middle с опытом 1 против полного Senior с опытом 7; зафиксировано предпочтение точности grade. |
| H1 | C02 vs C03 | C02 | Senior 90 и полный optional stack против Senior 100, опыта ближе к цели и отсутствия SQL/Django. |
| H2 | C04 vs C01 | C04 | Middle 95, Django/SQL и опыт 1 против Middle 85, без SQL и опыта 3; выбран профиль ближе к базовым задачам. |
| H2 | C01 vs C02 | C01 | Более близкий к Junior Middle против более опытного Senior с полным optional stack; scores разных grades не уравниваются. |
| H2 | C08 vs C06 | C08 | Оба optional skill и Senior 85 при опыте 6 против отсутствия Django, Senior 80 и опыта 5; стаж C06 ближе к цели. |
| H3 | C08 vs C06 | C08 | Django против FastAPI при общем SQL; выбран Django/data-fit, хотя отсутствие FastAPI является уступкой. |
| H3 | C06 vs C05 | C06 | Senior 80 и опыт 5 без Django против Senior 70 и опыта 12 с полным stack; более высокий assessment против полноты и опыта. |
| H3 | C05 vs C03 | C05 | Senior 70, опыт 12, полный stack против Senior 100, опыта 3 и отсутствия SQL/Django; высокий assessment против data-fit. |
| H4 | C08 vs C01 | C08 | Senior с SQL и опытом 6 без FastAPI против exact Middle с опытом 3 и FastAPI без SQL; data-fit против grade-fit. |
| H4 | C01 vs C04 | C01 | Middle 85, опыт 3, без SQL против Middle 95, опыта 1 и полного stack; больший опыт против assessment/SQL. |
| H4 | C04 vs C05 | C04 | Exact Middle, сильный результат своего уровня и опыт 1 против Senior с полным stack и опытом 12; спорная точность grade против опыта. |

## Future evaluation

1. Получить human approval и зафиксировать LOCKED_BEFORE_MATCHING_EVALUATION отдельным commit **до** Matching evaluation. При текущем DRAFT результаты не считать locked blind benchmark.
2. Зафиксировать dataset commit, SHA реализации Matching, версию окружения и adapter. Применять один набор 12 snapshots ко всем четырём Needs в изолированном окружении.
3. Проверить отрицательные случаи, включая C12, на реальной границе ввода/validation; не ослаблять production constraints. Невыполнимый case явно пометить, не выдавать его за успешную проверку.
4. Сохранить полный actual eligible set и его порядок, исключения, actual Top-3/Top-5 и сведения об ошибках отдельно от этих двух файлов. Не заменять actual ranking экспертным и не отбрасывать ошибки без отчёта.
5. Использовать документированный tie-break реализации без добавления своего удобного порядка. При неизвестном tie-break фиксировать неоднозначность; duplicate candidate IDs и сбой Need делают evaluation невалидной, их нельзя молча убирать. Меньшее число возвращённых кандидатов учитывается с фиксированными знаменателями.
6. Посчитать заранее заданные метрики ниже. Итог — diagnostic report; расхождение не даёт автоматического разрешения изменять coefficients или expectations.

### Metric definitions fixed before output

- **Hard-filter violations:** число пар (Need, candidate), заранее EXCLUDED, но возвращённых production как eligible. Считать по полному eligible set, включая кандидатов ниже Top-5. Цель: **0**.
- **Top-3 Set Agreement:** для каждой Need `100 × |ActualTop3 ∩ ExpectedTop3| / 3`; ExpectedTop3 — первые три Expected Top-5. Затем среднее по четырём Need. Цель: **≥90%**. Если actual короче трёх, знаменатель остаётся 3.
- **Top-5 Set Agreement:** для каждой Need `100 × |ActualTop5 ∩ ExpectedTop5| / 5`, затем среднее по четырём Need. Цель: **≥90%**. Если actual короче пяти, знаменатель остаётся 5.
- **Mean Rank Error@5:** для каждого из пяти Expected Top-5 candidates `abs(expected_position - actual_position)`. Позиции от 1. Если кандидат отсутствует в Actual Top-5, **actual_position=6**, даже при наличии ниже пятого места. Усреднить по пяти кандидатам, затем по четырём Need. Цель: **≤1.0**.

Actual Top-k берётся непосредственно из порядка production output. Нарушивший hard filter кандидат не удаляется из него задним числом: его попадание одновременно фиксируется как violation и может ухудшать ranking agreement. Незавершённый прогон любой Need не разрешает заявлять общий PASS или считать среднее лишь по удобным Need.

Знаменатели дискретны: по четырём Needs mean Top-3 меняется шагами 1/12, поэтому ориентир ≥90% означает минимум 11 совпадений из 12; mean Top-5 — минимум 18 из 20. Это свойства заранее заданных метрик, не рассчитанный Matching результат.

Targets — предварительные validation ориентиры, не гарантия качества. Нельзя автоматически тюнить алгоритм ради этих цифр. Нельзя менять metric definitions после появления output.

## Freeze policy

**Текущий статус: DRAFT_FOR_HUMAN_FREEZE.** Codex самостоятельно не переводит его в LOCKED.

Human review проверяет реалистичность Need, grade compatibility, профили, спорные Top-5 и отсутствие скрытой подгонки. После approval статус меняется на **LOCKED_BEFORE_MATCHING_EVALUATION** отдельным commit с подтверждением команды и временем freeze.

После LOCKED не меняются candidates, Needs, exclusion expectations, Expected Top-5, rationale и определения/targets метрик. Ranking coefficients не тюнятся по holdout. Обнаруженную ошибку фиксируют отдельно; согласованное исправление требует новой версии и независимого набора, а не правки этого benchmark после просмотра результата.

Push этого draft не является human approval. PR в P1 не создаётся, merge не выполняется.

## Self-review

- Ровно 4 Needs BACKEND и 12 вымышленных candidates, общий пул для всех Needs.
- Skills входят в каталог baseline; UUID и реальные персональные данные отсутствуют.
- Все шесть hard-filter типов покрыты; у H1/H2/H3/H4 есть минимум пять eligible candidates.
- По три meaningful trade-off на Need; Top-5 заданы до production output, исключённых в них нет.
- Содержимое JSON и Markdown согласовано; числовой Fit и production formula отсутствуют.
- Только два validation-файла; production, README, seed, CI, migrations и frontend не изменены.
