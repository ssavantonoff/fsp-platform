# Blind Matching Holdout — frozen v2 (имена файлов v1 сохранены)

**Status: LOCKED_BEFORE_MATCHING_EVALUATION**

Freeze timestamp (UTC): `2026-10-05T19:40:16Z`. Holdout v2 прошёл human review; approval получен от пользователя.

Baseline origin/main: `9892400d57b57fe3104d1871fa3513e56e24c4b5`. Branch: `docs/matching-holdout-v1`.

Создан: 2026-10-05 14:32:03 UTC. Пересмотрен до freeze: 2026-10-05 18:31:11 UTC, JSON version=2. Все 15 профилей и 4 Need вымышленные.

Первый draft не прошёл human freeze. Исправления основаны на frozen product matrix из review; original baseline сохранён, Matching output не просматривался.

## Purpose

Набор фиксирует предварительное экспертное ожидание до review Employer Matching Engine. После реализации будут отдельно проверены hard eligibility и qualitative ranking. Он не доказывает универсальное качество найма и не предназначен для выбора реальных людей.

Данные и ожидания вручную заданы одновременно в JSON; Markdown отображает те же значения. Никакие Matching scores или outputs для выбора профилей и порядка не использовались.

## Independence rules

- Перед созданием выполнены git fetch origin, git status и git rev-parse origin/main; рабочее дерево чистое. Зафиксирован `9892400d57b57fe3104d1871fa3513e56e24c4b5`.
- В baseline есть фундамент и Candidate Assessment; production Employer Needs/Matching отсутствует.
- Ветка Олега feat/employer-needs-matching, её PR/diff, implementation plan O1 и Matching-файлы не читались и не checkout.
- Demo ranking и вычисленные scores не просматривались. Professional Fit не вычислялся; производственные коэффициенты не использовались.
- Для данных использованы только этот baseline main, его Skill catalog, ТЗ P1 и human review v2. Предыдущая работа исполнителя относилась к Candidate Assessment, а не Matching.

## Interpretation and compatibility

Используется строго frozen product matrix из human review. Required JUNIOR допускает JUNIOR/MIDDLE и исключает SENIOR. Правило «любой higher grade compatible» не применяется.

| Required grade | Verified JUNIOR | Verified MIDDLE | Verified SENIOR |
|---|---|---|---|
| JUNIOR | ELIGIBLE | ELIGIBLE | EXCLUDED |
| MIDDLE | EXCLUDED | ELIGIBLE | ELIGIBLE |
| SENIOR | EXCLUDED | EXCLUDED | ELIGIBLE |

Матрица определяет только grade compatibility; остальные hard filters проверяются отдельно. Нужны consent=true, совпадающая specialization, непустой compatible verified_grade, все must-have skills и непустой assessment score. Verification triple canonical: grade/score/assessment_verified_at либо все заполнены, либо все null. Optional skills и target experience — мягкие предпочтения, опыт ниже ориентира не исключает кандидата.

Assessment score — сигнал результата своего grade/blueprint. Middle 90 и Senior 90 не являются психометрически эквивалентными; универсальная шкала силы из них не строится. Межуровневые решения учитывают qualitative соответствие Need. Стаж не превращён в математический коэффициент или автоматический штраф за больший опыт. Одинаковая verification date всех verified profiles не участвует в ranking.

Каталог baseline: `backend/app/seed.py`, skills: Python, Django, FastAPI, PostgreSQL, React, TypeScript, SQL. Используется его подмножество Python/FastAPI/Django/PostgreSQL/SQL, только names, без UUID.

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

Один и тот же пул C01–C15 используется для всех четырёх Need. Score — только normalized_assessment_score. Единственная дата — canonical assessment_verified_at, не ranking signal.

| Candidate | Specialization | Verified grade | Assessment | Consent | Skills | Years | Assessment verified at |
|---|---|---|---|---|---|---|---|
| C01 | BACKEND | MIDDLE | 85 | true | Python, FastAPI, Django, PostgreSQL | 3 | 2026-10-01T12:00:00Z |
| C02 | BACKEND | SENIOR | 90 | true | Python, FastAPI, Django, PostgreSQL, SQL | 7 | 2026-10-01T12:00:00Z |
| C03 | BACKEND | SENIOR | 100 | true | Python, FastAPI, PostgreSQL | 3 | 2026-10-01T12:00:00Z |
| C04 | BACKEND | MIDDLE | 95 | true | Python, FastAPI, Django, PostgreSQL, SQL | 1 | 2026-10-01T12:00:00Z |
| C05 | BACKEND | SENIOR | 70 | true | Python, FastAPI, Django, PostgreSQL, SQL | 12 | 2026-10-01T12:00:00Z |
| C06 | BACKEND | SENIOR | 80 | true | Python, FastAPI, PostgreSQL, SQL | 5 | 2026-10-01T12:00:00Z |
| C07 | BACKEND | JUNIOR | 85 | true | Python, Django, SQL | 1 | 2026-10-01T12:00:00Z |
| C08 | BACKEND | SENIOR | 85 | true | Python, Django, PostgreSQL, SQL | 6 | 2026-10-01T12:00:00Z |
| C09 | FRONTEND | MIDDLE | 90 | true | Python, FastAPI, Django, PostgreSQL, SQL | 3 | 2026-10-01T12:00:00Z |
| C10 | BACKEND | MIDDLE | 95 | false | Python, FastAPI, Django, PostgreSQL, SQL | 4 | 2026-10-01T12:00:00Z |
| C11 | BACKEND | null | null | true | Python, FastAPI, Django, PostgreSQL, SQL | 4 | null |
| C12 | BACKEND | SENIOR | 80 | true | Python, Django, PostgreSQL | 4 | 2026-10-01T12:00:00Z |
| C13 | BACKEND | JUNIOR | 95 | true | Python, SQL | 0.5 | 2026-10-01T12:00:00Z |
| C14 | BACKEND | JUNIOR | 75 | true | Python, Django | 2 | 2026-10-01T12:00:00Z |
| C15 | BACKEND | MIDDLE | 90 | true | Python, SQL | 2 | 2026-10-01T12:00:00Z |

- **C01:** Сильный exact Middle для H1: подходящий стаж и PostgreSQL/Django; SQL отсутствует. В H2 остаётся шестым eligible после close call с C15.
- **C02:** Полный stack и достаточный стаж; compatible Senior для Middle, exact Senior для H3, incompatible для Junior H2.
- **C03:** Очень высокий результат Senior assessment; нет Django/SQL, стаж ниже ориентира H3.
- **C04:** Exact Middle, полный stack и сильный результат своего уровня; один год опыта.
- **C05:** Большой опыт и полный stack; Senior assessment на нижней границе PASS.
- **C06:** Пять лет опыта, SQL и API-stack; нет Django — optional H1/H3, must-have H4.
- **C07:** Exact Junior для H2 с Django/SQL; несовместим с Middle/Senior Need, нет FastAPI/PostgreSQL.
- **C08:** Senior с SQL/Django и шестью годами опыта; нет FastAPI, incompatible с Junior H2.
- **C09:** Отдельный wrong-specialization case с canonical verification triple; FRONTEND вместо BACKEND.
- **C10:** Отдельный consent=false case при остальных привлекательных полях.
- **C11:** Отдельный canonical unverified case: grade=null, score=null, assessment_verified_at=null.
- **C12:** Замена невозможного snapshot: verified Senior 80, Django/PostgreSQL, четыре года опыта, без SQL/FastAPI. Шестой eligible для H3/H4.
- **C13:** Новый Junior 95, SQL, опыт 0.5 года; высокий assessment против отсутствия Django и малого стажа.
- **C14:** Новый Junior 75, Django, два года опыта; более низкий assessment против большего стажа и точного grade.
- **C15:** Новый Middle 90, SQL, два года опыта, без Django/FastAPI/PostgreSQL; assessment/SQL против Django и дополнительного опыта C01.

### Research fixture boundaries

- Все verification triples canonical: grade, score и assessment_verified_at либо одновременно заполнены, либо одновременно null. C11 — отдельный BACKEND unverified case, одновременно покрывающий отсутствие verification и assessment score.
- C09 — отдельный FRONTEND wrong-specialization case с согласованной verification triple. Это допустимое состояние CandidateProfile в БД; fixture не утверждает наличие текущего Frontend assessment bank. Подготовка через доверенный isolated fixture adapter, а не через CandidateWrite и не через несуществующий Frontend assessment flow.
- У всех verified profiles одинаковый assessment_verified_at; дата не участвует в ranking. Контактов, declared_grade, FSP bonus и profile recency signals нет.
- Invalid-provider snapshot с grade без score удалён из end-to-end holdout. Defensive invalid-provider cases остаются обязанностью Matching unit/provider tests; в P1 такие tests не создаются.

Все 15 проекций могут быть сохранены в CandidateProfile с действующими constraints. Будущий доверенный adapter изолированного окружения добавляет только служебные поля: User/UUID, синтетические имена, consent timestamp по consent и связи существующих skills по name. Он сохраняет все заданные canonical поля, не заполняет C11 verification и не отключает constraints. Подготовка fixtures не является клиентской записью verification или отдельным источником canonical state. Здесь не создаются production profiles и не выполняется Matching.

## Eligibility expectations

Все 60 пар C01–C15 × H1–H4 перечислены явно. EXCLUDED не может входить в Expected Top-5. C11 одновременно покрывает no verified qualification и missing assessment score. При нескольких нарушениях перечислены все причины.

| Need | Eligible count | Excluded count |
|---|---|---|
| H1 | 6 | 9 |
| H2 | 6 | 9 |
| H3 | 6 | 9 |
| H4 | 6 | 9 |

### H1

| Candidate | Expected eligibility | Reason |
|---|---|---|
| C01 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, canonical verification указана. |
| C02 | ELIGIBLE | BACKEND, consent=true, compatible grade по frozen matrix, все must-have, canonical verification указана. |
| C03 | ELIGIBLE | BACKEND, consent=true, compatible grade по frozen matrix, все must-have, canonical verification указана. |
| C04 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, canonical verification указана. |
| C05 | ELIGIBLE | BACKEND, consent=true, compatible grade по frozen matrix, все must-have, canonical verification указана. |
| C06 | ELIGIBLE | BACKEND, consent=true, compatible grade по frozen matrix, все must-have, canonical verification указана. |
| C07 | EXCLUDED | JUNIOR несовместим с required MIDDLE по frozen product matrix. Отсутствует must-have FastAPI. |
| C08 | EXCLUDED | Отсутствует must-have FastAPI. |
| C09 | EXCLUDED | FRONTEND не совпадает с BACKEND Need. |
| C10 | EXCLUDED | personal_data_consent=false. |
| C11 | EXCLUDED | verified_grade=null: нет подтверждённой квалификации. normalized_assessment_score=null; assessment_verified_at=null: canonical unverified profile. |
| C12 | EXCLUDED | Отсутствует must-have FastAPI. |
| C13 | EXCLUDED | JUNIOR несовместим с required MIDDLE по frozen product matrix. Отсутствует must-have FastAPI. |
| C14 | EXCLUDED | JUNIOR несовместим с required MIDDLE по frozen product matrix. Отсутствует must-have FastAPI. |
| C15 | EXCLUDED | Отсутствует must-have FastAPI. |

### H2

| Candidate | Expected eligibility | Reason |
|---|---|---|
| C01 | ELIGIBLE | BACKEND, consent=true, compatible grade по frozen matrix, все must-have, canonical verification указана. |
| C02 | EXCLUDED | SENIOR несовместим с required JUNIOR по frozen product matrix. |
| C03 | EXCLUDED | SENIOR несовместим с required JUNIOR по frozen product matrix. |
| C04 | ELIGIBLE | BACKEND, consent=true, compatible grade по frozen matrix, все must-have, canonical verification указана. |
| C05 | EXCLUDED | SENIOR несовместим с required JUNIOR по frozen product matrix. |
| C06 | EXCLUDED | SENIOR несовместим с required JUNIOR по frozen product matrix. |
| C07 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, canonical verification указана. |
| C08 | EXCLUDED | SENIOR несовместим с required JUNIOR по frozen product matrix. |
| C09 | EXCLUDED | FRONTEND не совпадает с BACKEND Need. |
| C10 | EXCLUDED | personal_data_consent=false. |
| C11 | EXCLUDED | verified_grade=null: нет подтверждённой квалификации. normalized_assessment_score=null; assessment_verified_at=null: canonical unverified profile. |
| C12 | EXCLUDED | SENIOR несовместим с required JUNIOR по frozen product matrix. |
| C13 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, canonical verification указана. |
| C14 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, canonical verification указана. |
| C15 | ELIGIBLE | BACKEND, consent=true, compatible grade по frozen matrix, все must-have, canonical verification указана. |

### H3

| Candidate | Expected eligibility | Reason |
|---|---|---|
| C01 | EXCLUDED | MIDDLE несовместим с required SENIOR по frozen product matrix. |
| C02 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, canonical verification указана. |
| C03 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, canonical verification указана. |
| C04 | EXCLUDED | MIDDLE несовместим с required SENIOR по frozen product matrix. |
| C05 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, canonical verification указана. |
| C06 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, canonical verification указана. |
| C07 | EXCLUDED | JUNIOR несовместим с required SENIOR по frozen product matrix. Отсутствует must-have PostgreSQL. |
| C08 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, canonical verification указана. |
| C09 | EXCLUDED | FRONTEND не совпадает с BACKEND Need. MIDDLE несовместим с required SENIOR по frozen product matrix. |
| C10 | EXCLUDED | personal_data_consent=false. MIDDLE несовместим с required SENIOR по frozen product matrix. |
| C11 | EXCLUDED | verified_grade=null: нет подтверждённой квалификации. normalized_assessment_score=null; assessment_verified_at=null: canonical unverified profile. |
| C12 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, canonical verification указана. |
| C13 | EXCLUDED | JUNIOR несовместим с required SENIOR по frozen product matrix. Отсутствует must-have PostgreSQL. |
| C14 | EXCLUDED | JUNIOR несовместим с required SENIOR по frozen product matrix. Отсутствует must-have PostgreSQL. |
| C15 | EXCLUDED | MIDDLE несовместим с required SENIOR по frozen product matrix. Отсутствует must-have PostgreSQL. |

### H4

| Candidate | Expected eligibility | Reason |
|---|---|---|
| C01 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, canonical verification указана. |
| C02 | ELIGIBLE | BACKEND, consent=true, compatible grade по frozen matrix, все must-have, canonical verification указана. |
| C03 | EXCLUDED | Отсутствует must-have Django. |
| C04 | ELIGIBLE | BACKEND, consent=true, exact grade, все must-have, canonical verification указана. |
| C05 | ELIGIBLE | BACKEND, consent=true, compatible grade по frozen matrix, все must-have, canonical verification указана. |
| C06 | EXCLUDED | Отсутствует must-have Django. |
| C07 | EXCLUDED | JUNIOR несовместим с required MIDDLE по frozen product matrix. Отсутствует must-have PostgreSQL. |
| C08 | ELIGIBLE | BACKEND, consent=true, compatible grade по frozen matrix, все must-have, canonical verification указана. |
| C09 | EXCLUDED | FRONTEND не совпадает с BACKEND Need. |
| C10 | EXCLUDED | personal_data_consent=false. |
| C11 | EXCLUDED | verified_grade=null: нет подтверждённой квалификации. normalized_assessment_score=null; assessment_verified_at=null: canonical unverified profile. |
| C12 | ELIGIBLE | BACKEND, consent=true, compatible grade по frozen matrix, все must-have, canonical verification указана. |
| C13 | EXCLUDED | JUNIOR несовместим с required MIDDLE по frozen product matrix. Отсутствует must-have Django, PostgreSQL. |
| C14 | EXCLUDED | JUNIOR несовместим с required MIDDLE по frozen product matrix. Отсутствует must-have PostgreSQL. |
| C15 | EXCLUDED | Отсутствует must-have Django, PostgreSQL. |

## Expected Top-5

Позиции начинаются с 1. Порядок задан вручную до output, без вычисленного Fit. Close call отмечает спорное предпочтение; единый ordering всё равно фиксируется.

H2 составлен заново. H1/H3/H4 сохранены после ручной оценки нового пула; причины выбора и cutoff comparisons приведены ниже.

### H1

Top-5 сохранён: C12 и C13–C15 не проходят must-have/grade. Старые полезные eligible profiles не менялись.

1. **C01** — Exact Middle, опыт ровно около целевого и полезные PostgreSQL/Django. Выше C04: дополнительный опыт перевешивает более высокий Middle assessment и SQL у C04; close call.
2. **C04** — Exact Middle с полным optional stack и сильным результатом Middle assessment. Выше C02 выбрана точность grade для API-роли; один год опыта против семи у C02 делает сравнение спорным (close call).
3. **C02** — Полный stack и достаточный опыт. Выше C03: SQL/Django и более широкий опыт предпочтены более высокому Senior assessment и стажу ближе к ориентиру у C03; close call.
4. **C03** — Высокий результат Senior assessment и три года опыта соответствуют API-контексту. Выше C06: этот сигнал качества предпочтён наличию SQL и большему опыту у C06; close call, Django нет у обоих.
5. **C06** — SQL/PostgreSQL и достаточный опыт для API-роли. Выше C05: более сильный результат в том же Senior assessment предпочтён полному optional stack и двенадцати годам опыта C05; отсутствие Django — уступка.

### H2

Top-5 составлен заново: все Senior исключены frozen matrix; среди шести eligible C01 остаётся вне Top-5 после close call с C15.

1. **C07** — Exact Junior, год опыта и оба optional skill Django/SQL. Выше C04: при одинаковых полезных skills и стаже выбрана точность Junior grade для задач под наставничеством; сильный результат Middle assessment C04 не уравнивается с Junior score. Выше C13: полнота stack и готовность к базовой работе предпочтены Junior assessment 95 и меньшему стажу; close call, сравнение score только внутри Junior.
2. **C04** — Compatible Middle с годом опыта и полным Django/SQL stack. Выше C13: готовность к задачам в существующем Django backend предпочтена exact Junior и его сильному результату; close call, одинаковые баллы разных grades не считаются эквивалентными.
3. **C13** — Exact Junior с сильным результатом своего assessment и SQL, но без Django и с половиной года опыта. Выше C14: assessment внутри Junior и SQL предпочтены Django и большему опыту C14; close call.
4. **C14** — Exact Junior, Django и два года опыта; SQL отсутствует. Выше C15: соответствие уровню задач под наставничеством и Django предпочтены более высокому verified grade и SQL у C15; close call, scores разных grades напрямую не сравниваются.
5. **C15** — Compatible Middle, SQL и два года опыта. Выше C01 (шестого eligible): более высокий assessment внутри Middle и SQL предпочтены Django и дополнительному году опыта C01; close call. FastAPI/PostgreSQL не являются требованиями H2.

### H3

C12 становится шестым eligible. Вручную оставлен после C03: Django/дополнительный год против сильного Senior assessment и FastAPI. Старый Top-5 сохранён.

1. **C02** — Exact Senior, семь лет опыта, полный optional stack. Сбалансированное совпадение с данными, существующими приложениями и API-интеграциями.
2. **C08** — SQL/Django и шесть лет опыта подходят data-контексту. Выше C06: Django, более сильный Senior assessment и опыт ближе к ориентиру предпочтены FastAPI у C06; close call.
3. **C06** — SQL/FastAPI и пять лет опыта; оценка Senior выше C05. Выше C05: этот результат и опыт ближе к ориентиру предпочтены Django и большему стажу C05; close call, пять лет не являются hard rejection.
4. **C05** — Полный optional stack, включая SQL/Django, и большой опыт. Выше C03: data-fit и достаточный опыт предпочтены высокому Senior assessment C03; close call из-за результата 70 против 100 в одном grade.
5. **C03** — Exact Senior с высоким результатом своего assessment. Стаж три года и отсутствие SQL/Django ограничивают qualitative data-fit; высокий score сам по себе не заменяет совпадение с Need. Выше нового C12: Senior assessment 100 и FastAPI предпочтены Django и дополнительному году опыта C12 (Senior 80); close call, SQL отсутствует у обоих.

### H4

C12 становится шестым eligible. Вручную оставлен после C05: более сильный Senior assessment и стаж ближе к цели против полного SQL/FastAPI stack и достаточного опыта. Старый Top-5 сохранён.

1. **C02** — Полный Django/PostgreSQL/SQL stack и семь лет опыта близки ориентиру шесть. Совместимый Senior здесь предпочтён менее опытным exact Middle.
2. **C08** — Шесть лет опыта, Django/PostgreSQL/SQL. Ниже C02: отсутствует FastAPI и результат Senior немного ниже, хотя стаж точнее совпадает. Выше C01: data-fit и опыт предпочтены exact Middle и FastAPI у C01; close call.
3. **C01** — Exact Middle, Django/PostgreSQL и три года опыта. Выше C04: больший опыт предпочтён SQL и более сильному результату в том же Middle assessment у C04; close call для data-роли.
4. **C04** — Exact Middle с полным optional stack и сильным результатом своего уровня. Выше C05: точность grade и этот сигнал качества предпочтены двенадцати годам опыта C05; close call, Senior 70 не трактуется как психометрически эквивалентный Middle score.
5. **C05** — Полный stack и большой опыт обеспечивают допустимость. Профиль поставлен после C04 в спорном сравнении подходящего grade/результата и опыта. Это не утверждение, что меньший стаж всегда лучше. Выше нового C12: явный SQL, FastAPI и достаточный стаж предпочтены более высокому Senior assessment и опыту ближе к ориентиру у C12; close call.

## Ambiguous trade-offs

Для каждой Need есть минимум три спорных сравнения; H2 содержит пять, H3/H4 — четыре, включая границу Top-5. Новые profiles дают встречные преимущества и не доминируют по всем ranking signals.

| Need | Pair | Fixed preference | Why it is a close call |
|---|---|---|---|
| H1 | C01 vs C04 | C01 | Middle 85, опыт 3, без SQL против Middle 95, опыт 1, полный stack; выбран опыт для самостоятельной API-работы. |
| H1 | C04 vs C02 | C04 | Exact Middle с опытом 1 против полного Senior с опытом 7; зафиксировано предпочтение точности grade. |
| H1 | C02 vs C03 | C02 | Senior 90 и полный optional stack против Senior 100, опыта ближе к цели и отсутствия SQL/Django. |
| H2 | C07 vs C13 | C07 | Junior 85, Django/SQL и год опыта против Junior 95, только SQL и половины года; готовность и полный optional stack против assessment. |
| H2 | C04 vs C13 | C04 | Compatible Middle с Django/SQL и годом опыта против exact Junior с SQL и половиной года; stack/готовность против точности grade, без уравнивания scores разных уровней. |
| H2 | C13 vs C14 | C13 | Junior 95, SQL и опыт 0.5 против Junior 75, Django и опыта 2; assessment/SQL против Django и практического стажа. |
| H2 | C14 vs C15 | C14 | Exact Junior с Django против compatible Middle с SQL при одинаковом опыте 2; точность grade и Django против более высокого grade и SQL. |
| H2 | C15 vs C01 | C15 | Middle 90, SQL и опыт 2 против Middle 85, Django и опыта 3; assessment/SQL против Django и дополнительного опыта на границе Top-5. |
| H3 | C08 vs C06 | C08 | Django против FastAPI при общем SQL; выбран Django/data-fit, хотя отсутствие FastAPI является уступкой. |
| H3 | C06 vs C05 | C06 | Senior 80 и опыт 5 без Django против Senior 70 и опыта 12 с полным stack; более высокий assessment против полноты и опыта. |
| H3 | C05 vs C03 | C05 | Senior 70, опыт 12, полный stack против Senior 100, опыта 3 и отсутствия SQL/Django; высокий assessment против data-fit. |
| H3 | C03 vs C12 | C03 | Senior 100, FastAPI и опыт 3 против Senior 80, Django и опыта 4; сильный assessment/API против Django и дополнительного опыта на границе Top-5. |
| H4 | C08 vs C01 | C08 | Senior с SQL и опытом 6 без FastAPI против exact Middle с опытом 3 и FastAPI без SQL; data-fit против grade-fit. |
| H4 | C01 vs C04 | C01 | Middle 85, опыт 3, без SQL против Middle 95, опыта 1 и полного stack; больший опыт против assessment/SQL. |
| H4 | C04 vs C05 | C04 | Exact Middle, сильный результат своего уровня и опыт 1 против Senior с полным stack и опытом 12; спорная точность grade против опыта. |
| H4 | C05 vs C12 | C05 | Senior 70 с SQL/FastAPI и опытом 12 против Senior 80 без обоих optional skills и опыта 4; полный data stack/стаж против assessment и близости к целевому опыту. |

## Future evaluation

1. Human approval holdout v2 получен. Статус LOCKED_BEFORE_MATCHING_EVALUATION и UTC-время freeze зафиксированы отдельным commit **до** Matching evaluation.
2. Зафиксировать dataset commit, SHA реализации Matching, версию окружения и adapter. Применять один набор 15 canonical profiles ко всем четырём Needs в изолированном окружении.
3. Сохранить все 15 profiles с действующими production constraints через доверенный isolated fixture adapter. Проверить отрицательные случаи, в том числе C11 с canonical null triple. Invalid-provider cases проверяются отдельно Matching unit/provider tests и в этот holdout не входят. При невозможности подготовки fixture явно остановить evaluation, а не засчитать пропущенный case как PASS.
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

**Текущий статус: LOCKED_BEFORE_MATCHING_EVALUATION.** Codex самостоятельно не переводит его в LOCKED.

Human review проверяет реалистичность Need, grade compatibility, профили, спорные Top-5 и отсутствие скрытой подгонки. После approval статус меняется на **LOCKED_BEFORE_MATCHING_EVALUATION** отдельным commit с подтверждением команды и временем freeze.

После LOCKED не меняются candidates, Needs, exclusion expectations, Expected Top-5, rationale и определения/targets метрик. Ranking coefficients не тюнятся по holdout. Обнаруженную ошибку фиксируют отдельно; согласованное исправление требует новой версии и независимого набора, а не правки этого benchmark после просмотра результата.

Push этого draft не является human approval. PR в P1 не создаётся, merge не выполняется.

## Self-review

- Ровно 4 BACKEND Needs, 15 вымышленных candidates и 60 eligibility expectations; общий пул для всех Needs.
- Frozen matrix точна: Senior исключён из H2 JUNIOR; compatible grades не выводятся из общего higher-grade правила.
- Skills из baseline catalog; все canonical verification triples согласованы. C11 имеет три null; invalid-provider case отсутствует.
- Все шесть hard-filter причин покрыты сохраняемыми CandidateProfile fixtures. Wrong specialization, consent=false и unverified — отдельные profiles.
- Eligible count: H1=6, H2=6, H3=6, H4=6; Top-5 не равен всему eligible set у H2/H3.
- Все Expected Top-5 содержат только ELIGIBLE; новые candidates и cutoff comparisons вручную рассмотрены до output.
- JSON и Markdown совпадают по данным, датам, eligibility, ordering, rationale и trade-offs; Fit/formula/output не использовались.
- Только два holdout-файла; production/README/seed/CI/migrations/frontend не изменены. Status — LOCKED_BEFORE_MATCHING_EVALUATION, version=2; freeze выполнен по human approval.
