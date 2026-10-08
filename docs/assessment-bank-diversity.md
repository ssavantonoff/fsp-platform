# Assessment bank diversity — P5 frozen implementation and review

## Decision

**STOP_FOR_HUMAN_REVIEW.** The independent reviewer has identified IMPORTANT findings in the new content. P5 has not passed the content gate. No post-audit remediation, PR creation or merge is authorized in this execution. The final independent register below records actual classifications, without replacing them with target counts.

## Frozen source and provenance

- Exact starting main: `f4fc87ccad953979be82cbe8118142d74be50c1d`.
- Branch: `feat/assessment-bank-diversity`.
- Source freeze commit: `a0e5d399fe443ef7bc0796fa9b5dde3eee97e0f9`.
- Freeze recorded UTC: `2026-10-08T15:57:23Z`.
- Source: `backend/app/content/backend_questions.json`.
- Source SHA256: `deaab5428aca5ba2a4f67d0026f0f644fbe942a00b6cdbe79272ca08e8582b8b`.
- Frozen base source SHA256: `11fba035b866475b588f62a142bc97f47e7fe94898afdbba3ecd263b5b7fae56`.
- `backend/tests/fixtures/assessment-bank-pre-p5.json` is byte-identical to the exact base source. All 75 existing records remain content-equivalent, with unchanged metadata, versions, ordering and alternatives. The 45 additions follow them in source order.
- Historical provenance remains unchanged: [P3 design](assessment-bank-remediation-plan.md), [P3 audit v2](assessment-bank-audit-v2.md), [P3 final audit v3](assessment-bank-audit-v3.md). The old audit describes its historical 75-record source and its 25 MINOR findings; it is not rewritten as a 120-record audit.

This document contains no question text, alternatives, marking positions, keys or solutions. After source freeze only this report may change; question content is not silently remediated.

## Inventory

Current source: **120 records / 480 alternatives**, **40 per grade**, **45 new unique v1 codes**, **75 existing unchanged**. New records have no `supersedes`. Versions: **83 v1 / 35 v2 / 2 v3**. Slot 6 adds BASIC, slot 7 APPLIED and slot 8 ADVANCED in every grade × competency bucket.

Each cell below is **BASIC / APPLIED / ADVANCED = 2 / 4 / 2**. Each bucket contains 8 records and exactly 3 additions.

| Grade | PROGRAMMING | HTTP_API | DATABASES | ARCHITECTURE | TESTING_SECURITY_DEBUGGING | Total / additions |
| --- | --- | --- | --- | --- | --- | --- |
| JUNIOR | 2 / 4 / 2 | 2 / 4 / 2 | 2 / 4 / 2 | 2 / 4 / 2 | 2 / 4 / 2 | 40 / 15 |
| MIDDLE | 2 / 4 / 2 | 2 / 4 / 2 | 2 / 4 / 2 | 2 / 4 / 2 | 2 / 4 / 2 | 40 / 15 |
| SENIOR | 2 / 4 / 2 | 2 / 4 / 2 | 2 / 4 / 2 | 2 / 4 / 2 | 2 / 4 / 2 | 40 / 15 |

The validator now requires exactly 120 / 40 / 2-4-2. Typed enums, strict versions, code uniqueness, four distinct alternatives, supersedes graph checks and safe diagnostics remain intact. Frozen historical 75-record fixtures are checked for exactly the expected inventory findings; production validation is not weakened to accept them.

## Selection and exposure methodology

Exposure is calculated from persisted attempt membership, restricted to the same candidate, specialization and target grade. Every assigned question counts, including unanswered questions and attempts completed by submission or timeout, irrespective of pass/fail. Counting does not mutate history.

For each competency/difficulty bucket, selection visits exposure levels in ascending order. It samples randomly among ties, then visits the next level only when the lower level cannot supply the required number of distinct questions. APPLIED selects two distinct questions. Runtime retains `random.SystemRandom()` without public or candidate-derived seeds. Selected membership, question position and randomized option IDs are persisted once and read unchanged on reload.

The published code convention uses a stable slot followed by `-vN`. Exposure sums all versions of that slot, including inactive predecessors. All 37 current supersedes relationships obey this convention. A real persisted v1 → v2 → v3 regression checks inherited exposure for PASSED, FAILED and timeout completion, while retaining historical content and membership. There is no new schema, predecessor column or historical-row rewrite. Arbitrary future successor codes that do not retain this stable slot naming would require an explicit lineage decision; this implementation does not infer an unrelated code's predecessor from its text.

For a candidate with no history, one attempt consumes half of each pool: 1/2 BASIC, 2/4 APPLIED and 1/2 ADVANCED. The second attempt chooses the zero-exposure complement in every bucket. Therefore the first two same-grade forms have **20 families each and zero overlap**, independent of the random tie choice. After that, least-exposed selection balances reuse. Eight generated attempts for each grade keep `max exposure - min exposure <= 1` in every bucket after every attempt, and end with exposure 4 for all 40 families. That balance property is tested for the stated initially uniform pool; it does not promise to erase arbitrary historical skew in one attempt.

The guarantee concerns these current pools and the same candidate/grade scope. Different candidates sample independently. It is **reduced repeated exposure / a diversified bank**, not a globally unique exam or protection against memorizing the entire finite bank.

### Expected independent cross-candidate overlap

For two fresh candidates at the same grade, sampling independently and uniformly within each bucket:

- BASIC expected intersection: `1 × 1 / 2 = 0.5` families.
- APPLIED expected intersection: `2 × 2 / 4 = 1` family.
- ADVANCED expected intersection: `1 × 1 / 2 = 0.5` families.
- Five competencies: `5 × (0.5 + 1 + 0.5) = 10` families out of 20 (**50% expected overlap**).

There are `2 × C(4,2) × 2 = 24` family sets per competency and `24^5 = 7,962,624` per grade, ignoring ordering and option permutations. Exact enumeration tests the expectation; it is not a claim that collisions cannot occur. Different-grade slot families are scoped by grade.

## Technical evidence completed before the content STOP

| Check | Actual result |
| --- | --- |
| Targeted assessment suite | 235 passed / 1 PostgreSQL-only skip |
| Full SQLite, Python 3.13.16 | 805 passed / 20 PostgreSQL-only skips |
| Full PostgreSQL 17.11, Python 3.13.16 | 825 passed / no skips |
| Additional local SQLite, Python 3.14 | 805 passed / 20 skips |
| Ruff `check .` | PASS |
| Ruff `format --check .` | PASS, 56 files |
| mypy `app` | PASS, 32 source files |
| Alembic heads | Single unchanged `a812e4c79b60` |
| Alembic check on PostgreSQL | No new upgrade operations detected |
| Frontend tests | 106 passed |
| Frontend lint / typecheck / build | PASS; local Node 26.5.1 |
| Fresh Docker build / healthy startup | PASS; frontend build/runtime Node 22, backend Python 3.13, PostgreSQL 17.11 |
| Base / demo / matching-demo seed, each run twice | PASS; snapshots of all 15 public tables identical across each repeat |
| `git diff --check` | PASS |

Backend commands: `python -m pytest -q` once with empty `TEST_DATABASE_URL` and once with the isolated PostgreSQL URL; `python -m ruff check .`; `python -m ruff format --check .`; `python -m mypy app`; `alembic heads`; `alembic check`. Frontend commands: `npm test`, `npm run lint`, `npm run typecheck`, `npm run build`. Docker used a new `fsp-p5-diversity` project and volume. The initial `down -v` could not connect while Docker Desktop was stopped; Desktop was started and the fresh project was built and reached healthy state via `up --build -d --wait`.

Existing literal G1 PASS 70, G2 FAIL 80 by competency, G3 FAIL 65, G4 PASS 100 and G5 FAIL 0 remain unchanged and pass in both database suites. The suites also retain cooldowns, timeout, higher-grade failure, specialization restoration, canonical verification, answer privacy and a single global IN_PROGRESS attempt.

`backend/tests/test_assessment_diversity.py` adds 25 regressions: exact frozen source/content inventory; all-grade disjoint attempts; all-grade eight-attempt balance; lowest-pool expansion; unseeded secure runtime RNG; candidate independence and persisted option shuffle; actual predecessor history; immutable 75→120 upgrade for active/finished attempts; exact cross-candidate overlap. The pre-P5 byte fixture freezes the previous source. Existing assessment inventory tests are adjusted to 120. One existing `test_matching_seed.py` assertion changes only the shared assessment-bank count from 75 to 120; no Matching production behavior, fixture, ranking or API changes.

### Browser smoke

A real in-app browser used the isolated seeded candidate at `http://localhost:13055`:

1. Started Backend/Middle; UI and persisted membership contained 20 questions with the 30-minute timer.
2. Selected an answer, reloaded, and saw the same selection, question and option order with the saved status.
3. Submitted the scenario with 19 unanswered questions; result was FAILED / 0 with no canonical verification. The Middle selector was disabled until the unchanged seven-day cooldown date.
4. A test-only setup outside the repository shifted timestamps of that one synthetic terminal attempt and its selected answer back eight days in the isolated development database. No production clock, cooldown, grading or selection code was bypassed or changed. This fixture operation is not a production/history migration.
5. Reloaded availability and started a second Middle attempt through the UI. It contained 20 families. Comparing the two actual persisted memberships gave **zero overlapping families**; the first membership, positions, option order and selected answer were unchanged.
6. Finished the second empty attempt through the UI; result was again FAILED / 0. No active synthetic attempt was left behind.

This browser check exercises controlled test time rather than waiting seven real days. Automated tests separately use a patched test clock and verify real cooldown boundaries and restoration semantics. The browser was not used to extract or publish answers.

## Independent content audit

**Final new-content result: 0 BLOCKER / 7 IMPORTANT / 21 MINOR / 17 OK.** Content gate: **FAIL — STOP_FOR_HUMAN_REVIEW**.

Audit completed UTC: `2026-10-08T16:12:31.321886+00:00`. The separate reviewer context did not author the questions or use authoring scripts/rationales. It manually read all **45 new stems / 180 alternatives** and all **75 baseline stems / 300 alternatives** for comparison. All 15 buckets and same-competency cross-grade groups were reviewed. Technical gates and desired counts were not evidence of item quality. Classifications below are retained as returned by the independent reviewer.

The rubric is the final P3 rubric: BASIC is relative to grade; complex terminology alone does not establish Senior demand; ADVANCED considers interacting material constraints. BLOCKER means no defensible unique evaluation; IMPORTANT means materially weakened grade/difficulty/competency measurement; MINOR means a local weakness without established scoring failure or material measurement failure; OK means no finding in this review, not certification. One item is counted once at its maximum severity.

| Grade | BLOCKER | IMPORTANT | MINOR | OK | Reviewed |
| --- | --- | --- | --- | --- | --- |
| JUNIOR | 0 | 1 | 8 | 6 | 15 |
| MIDDLE | 0 | 4 | 6 | 5 | 15 |
| SENIOR | 0 | 2 | 7 | 6 | 15 |

### Full register of 45 new items

| Code | Grade | Difficulty | Severity | Categories | Independent safe rationale |
| --- | --- | --- | --- | --- | --- |
| backend-junior-programming-6-v1 | JUNIOR | BASIC | OK | — | Проверяется фундаментальная семантика жизненного цикла итератора. Заблуждения в вариантах относятся к тому же предмету; локальный BASIC Junior и однозначность сохранены. |
| backend-junior-programming-7-v1 | JUNIOR | APPLIED | MINOR | COGNITIVE_OVERLAP | Самостоятельно это однозначная локальная APPLIED-задача Junior с правдоподобными ошибками. Есть заметное когнитивное перекрытие с новым backend-junior-http_api-7-v1: оба различают отсутствие значения и допустимое ложное значение; это локальное перекрытие разных компетенций. |
| backend-junior-programming-8-v1 | JUNIOR | ADVANCED | MINOR | WEAK_DISTRACTORS | Локальная работа с вложенной изменяемой структурой соответствует Junior ADVANCED и имеет защищаемый выбор. Несколько альтернатив повторяют одну и ту же ошибку владения вложенным объектом, ограничивая разнообразие отвлечений. |
| backend-junior-http_api-6-v1 | JUNIOR | BASIC | OK | — | Фундаментальное различение назначения HTTP-заголовков соответствует BASIC Junior; конкурирующие варианты отражают типичные смешения метаданных. Неоднозначность не установлена. |
| backend-junior-http_api-7-v1 | JUNIOR | APPLIED | MINOR | WEAK_DISTRACTORS, COGNITIVE_OVERLAP | Частичная мутация по явно заданному контракту подходит Junior APPLIED. Одна альтернатива искусственна; дополнительно есть локальное когнитивное перекрытие с backend-junior-programming-7-v1. Лучший выбор при этом защищаем. |
| backend-junior-http_api-8-v1 | JUNIOR | ADVANCED | MINOR | WEAK_DISTRACTORS | Условное чтение и граница HTTP-представления дают допустимую локальную ADVANCED-задачу Junior. Часть пояснений альтернатив чрезмерно произвольна и облегчает исключение; значимого ослабления измерения или scoring failure не установлено. |
| backend-junior-databases-6-v1 | JUNIOR | BASIC | OK | — | Проверяется стандартная агрегатная семантика SQL в явном локальном наборе данных. Варианты представляют разные распространённые ошибочные трактовки; BASIC Junior и единственность сохранены. |
| backend-junior-databases-7-v1 | JUNIOR | APPLIED | OK | — | Локальное применение SQL-семантики отсутствующего значения подходит Junior APPLIED. Альтернативы содержательно различимы и отражают обычные ошибки сравнения; неоднозначности нет. |
| backend-junior-databases-8-v1 | JUNIOR | ADVANCED | OK | — | Взаимодействуют кардинальность двух связей, агрегаты и сохранение родителей без детей. Это содержательная локальная Junior ADVANCED-задача; альтернативы отражают распространённые ошибки агрегации и не дают второго защищаемого выбора. |
| backend-junior-architecture-6-v1 | JUNIOR | BASIC | MINOR | WEAK_DISTRACTORS | Локальная граница публичного ответа соответствует BASIC Junior и однозначна. Несколько отвлекающих подходов слабо конкурируют с осмысленной границей данных; это локальная слабость без доказанного нарушения grade. |
| backend-junior-architecture-7-v1 | JUNIOR | APPLIED | MINOR | WEAK_DISTRACTORS | Обязательная конфигурация и готовность сервиса образуют допустимую Junior APPLIED-ситуацию. Несколько альтернатив прямо расходятся с запретами сценария и мало похожи на реальный инженерный выбор; уровень в целом сохраняется. |
| backend-junior-architecture-8-v1 | JUNIOR | ADVANCED | MINOR | WEAK_DISTRACTORS | Авторитет данных и сохранение принятых условий дают допустимое локальное взаимодействие для Junior ADVANCED. Часть альтернатив предполагает входные данные, которых описанный контракт не предоставляет; выбор облегчается, но остаётся однозначным. |
| backend-junior-testing_security_debugging-6-v1 | JUNIOR | BASIC | MINOR | WEAK_DISTRACTORS | Семантика изоляции тестовых данных соответствует BASIC Junior. Несколько альтернатив не решают даже заявленную зависимость от порядка; это локальный недостаток качества отвлечений. |
| backend-junior-testing_security_debugging-7-v1 | JUNIOR | APPLIED | OK | — | Локальная защита вывода данных соответствует Junior APPLIED. Альтернативы отражают распространённые ошибки выбора контекста обработки, а указанный контракт не оставляет равноправного выбора. |
| backend-junior-testing_security_debugging-8-v1 | JUNIOR | ADVANCED | IMPORTANT | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | ADVANCED сводится к распознаванию того, что проверка отказа должна воспроизводить отказ и проверять требуемое поведение. Три альтернативы почти не исследуют заявленный отрицательный сценарий; нет анализа конкурирующих диагностических фактов или взаимодействующих границ. Это существенно слабее требуемого ADVANCED demand, хотя лучший выбор однозначен. |
| backend-middle-programming-6-v1 | MIDDLE | BASIC | MINOR | WEAK_DISTRACTORS | Базовая числовая граница относительно Middle допустима и оценивание защищаемо. Одна альтернатива искусственно отбрасывает информацию, явно необходимую контракту, и слабо конкурирует с другими; значимого дефекта grade не установлено. |
| backend-middle-programming-7-v1 | MIDDLE | APPLIED | IMPORTANT | GRADE_TOO_EASY, DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | APPLIED Middle фактически сводится к локальному различению ленивого и полного накопления. Поведение вызывающего компонента уже решено условием; очередь, пакетирование, порядок и конфликт ограничений не требуют выбора. Все отвлекающие подходы повторяют полное накопление и явно нарушают единственный лимит. Реалистичный размер входа сам по себе не создаёт Middle judgement. |
| backend-middle-programming-8-v1 | MIDDLE | ADVANCED | IMPORTANT | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | Локальная семантика завершения отменяемой задачи уместна для Middle, но ADVANCED сводится к одному правилу завершения перед ответом. Все альтернативы снимают прямо указанное требование завершения или владения ресурсом; отсутствует содержательный выбор при взаимодействии времени, отказов и ресурсов. Недостаток касается demand сложности, а не технической правильности. |
| backend-middle-http_api-6-v1 | MIDDLE | BASIC | OK | — | Базовая семантика успешного ответа на запрос диапазона допустима относительно Middle. Альтернативы различают успех, принятие, отсутствие содержимого и ошибку диапазона; это HTTP-семантика без framework trivia. |
| backend-middle-http_api-7-v1 | MIDDLE | APPLIED | OK | — | Задан конкретный практический контракт перехода после мутации. Альтернативы отражают типичные ошибки сохранения метода и смешения ответа с перенаправлением; прикладная HTTP-задача Middle однозначна. |
| backend-middle-http_api-8-v1 | MIDDLE | ADVANCED | MINOR | WEAK_DISTRACTORS | Взаимодействуют условный диапазон, изменение версии и обработка локального фрагмента, что сохраняет Middle ADVANCED demand. Две отвлекающие альтернативы повторяют практически один дефект и ограничивают их разнообразие; scoring failure не установлен. |
| backend-middle-databases-6-v1 | MIDDLE | BASIC | MINOR | WEAK_DISTRACTORS | Базовая граница snapshot в явно указанном PostgreSQL 17 соответствует Middle BASIC. Некоторые отвлекающие обещания технически чрезмерны и слишком легко исключаются; однозначность сохраняется. |
| backend-middle-databases-7-v1 | MIDDLE | APPLIED | MINOR | WEAK_DISTRACTORS | Применение устойчивого порядка к ограниченной выборке подходит Middle APPLIED. Несколько альтернатив почти не решают проблему порядка; одна практическая ошибочная стратегия остаётся содержательной. Нарушение grade или равноправный ответ не установлены. |
| backend-middle-databases-8-v1 | MIDDLE | ADVANCED | IMPORTANT | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS, COGNITIVE_OVERLAP | ADVANCED фактически проверяет базовое свойство snapshot уровня изоляции. Другие варианты снимают общий транзакционный контекст либо используют противоположное базовое свойство; взаимодействующие требования не меняют предметного выбора. Есть сильное когнитивное перекрытие с новым BASIC backend-middle-databases-6-v1, а повышение difficulty не добавляет достаточного demand. |
| backend-middle-architecture-6-v1 | MIDDLE | BASIC | MINOR | WEAK_DISTRACTORS | Различение сигналов эксплуатационного контракта допустимо для Middle BASIC. Одна альтернатива вводит необоснованное постоянное последствие, облегчая исключение; это локальная слабость без значимого нарушения измерения. |
| backend-middle-architecture-7-v1 | MIDDLE | APPLIED | OK | — | Прикладное суждение включает совместимость двух форматов, смешанный rollout, восстановимость производных данных и rollback. Альтернативы представляют типичные несовместимые стратегии; Middle APPLIED и однозначность защищаемы. |
| backend-middle-architecture-8-v1 | MIDDLE | ADVANCED | IMPORTANT | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | ADVANCED сводится к распознаванию необходимости отличать недоступное значение от фактически пустого или актуального. Три альтернативы прямо нарушают эту явно заданную смысловую границу; поведение обязательного компонента уже фиксировано, конфликт ресурсов, времени или восстановления не входит в выбор. Измерение ADVANCED существенно ослаблено. |
| backend-middle-testing_security_debugging-6-v1 | MIDDLE | BASIC | MINOR | WEAK_DISTRACTORS | Проверка границы раскрытия ошибок допустима для Middle BASIC и имеет единственный защищаемый выбор. Несколько альтернатив фактически не проверяют эту границу вообще; это локальный дефект вариантов, без установленного провала grade. |
| backend-middle-testing_security_debugging-7-v1 | MIDDLE | APPLIED | OK | — | Явно ограничена модель файловой системы, поэтому отсутствующая защита от изменения между проверкой и использованием не является скрытым требованием. Проверяется прикладная граница разрешённого ресурса; варианты отражают распространённые неправильные проверки. |
| backend-middle-testing_security_debugging-8-v1 | MIDDLE | ADVANCED | OK | — | Выбор эксперимента требует связать локализованные наблюдения, размер входа и рост промежуточного состояния. Конкурирующие измерения теряют одну из существенных диагностических границ; Middle ADVANCED и единственность сохранены. |
| backend-senior-programming-6-v1 | SENIOR | BASIC | OK | — | Базовый системный инвариант чтения одной версии при параллельной публикации соответствует Senior BASIC. Разные альтернативы нарушают различимые границы согласованности; сложность не основана на названии runtime. |
| backend-senior-programming-7-v1 | SENIOR | APPLIED | MINOR | WEAK_DISTRACTORS | Системная жизнь worker, устойчивое подтверждение и ограниченный shutdown дают содержательный Senior APPLIED demand. Некоторые альтернативы слишком явно снимают указанные гарантии; недостаток локальный, поскольку несколько существенных границ сохраняются. |
| backend-senior-programming-8-v1 | SENIOR | ADVANCED | OK | — | ADVANCED включает недоверенную структуру, скрытые затраты после преобразования и общий бюджет нескольких обработчиков. Альтернативы правдоподобно теряют разные уровни ограничения; это системное ресурсное суждение Senior. |
| backend-senior-http_api-6-v1 | SENIOR | BASIC | OK | — | Базовая identity и общая квота при нескольких credentials и экземплярах создают системную границу Senior BASIC. Альтернативы отражают реальные обходы или ошибки локальности состояния; единственный выбор защищаем. |
| backend-senior-http_api-7-v1 | SENIOR | APPLIED | OK | — | Взаимодействуют целостность доставки, допустимое время, устойчивость повторов и scope идентичности после restart. Эти границы создают содержательную Senior APPLIED-задачу; варианты отражают распространённые ошибки интеграции. |
| backend-senior-http_api-8-v1 | SENIOR | ADVANCED | OK | — | Взаимодействуют распространение материала проверки, смешанные версии, жизнь ранее выданных credentials и временная погрешность. Плановая модель без компрометации задана явно; Senior ADVANCED и единственность защищаемы. |
| backend-senior-databases-6-v1 | SENIOR | BASIC | MINOR | WEAK_DISTRACTORS | Базовое эксплуатационное evidence восстановления допустимо относительно Senior BASIC. Несколько вариантов почти не проверяют восстановительный сценарий и чрезмерно облегчают исключение; значимого провала системной темы не установлено. |
| backend-senior-databases-7-v1 | SENIOR | APPLIED | MINOR | WEAK_DISTRACTORS | Связь длительного snapshot, фонового обслуживания и эксплуатационного влияния создаёт Senior APPLIED demand. Одна отвлекающая мера явно не относится к указанной причине; часть выбора остаётся содержательной, поэтому severity локальная. |
| backend-senior-databases-8-v1 | SENIOR | ADVANCED | MINOR | CONTEXT_SCOPE | Системное восстановление при независимых последствиях соответствует Senior ADVANCED. Полнота восстанавливаемого набора ранее принятых операций и данных для их сверки описана слабо: доступ к отдельному известному идентификатору не равен доказанной полноте набора. Среди имеющихся альтернатив лучший выбор остаётся защищаемым; scoring failure не установлен. |
| backend-senior-architecture-6-v1 | SENIOR | BASIC | OK | — | Базовое системное решение требует связать частичный rollout с общей внешней ёмкостью и безопасным оперативным действием при ещё неполной диагностике. Это Senior BASIC, а не локальная оценка процесса. |
| backend-senior-architecture-7-v1 | SENIOR | APPLIED | MINOR | CONTEXT_SCOPE | Невытесняемая работа, распределение ёмкости и изоляция очередей дают содержательное Senior APPLIED-суждение. Количественное обещание максимального ожидания опирается на слабо раскрытую формулировку достаточности доли B; границы пикового поступления и времени обслуживания не детализированы. Лучшая из имеющихся стратегий остаётся однозначной. |
| backend-senior-architecture-8-v1 | SENIOR | ADVANCED | IMPORTANT | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | Тема rollout системная и уместна для Senior, но ADVANCED фактически сводится к одному правилу совместимости чтения и появления новой записи. Все три альтернативы включают несовместимую запись немедленно, а rollback служит повтором того же запрета вместо отдельного взаимодействующего ограничения. Содержательный выбор между правдоподобными стратегиями существенно ослаблен. |
| backend-senior-testing_security_debugging-6-v1 | SENIOR | BASIC | MINOR | WEAK_DISTRACTORS | Базовая граница cohort в измерении частичного rollout допустима для Senior BASIC. Одна альтернатива представляет слишком очевидное обратное смешение знаменателя и числителя; неоднозначности или существенного провала grade не установлено. |
| backend-senior-testing_security_debugging-7-v1 | SENIOR | APPLIED | MINOR | WEAK_DISTRACTORS | Системная жизнь разрешения между постановкой и исполнением и атомарная граница действия дают Senior APPLIED demand. Некоторые отвлекающие подходы слишком очевидно нарушают security-границу; сохраняется одна содержательная конкурирующая ошибка доверия. |
| backend-senior-testing_security_debugging-8-v1 | SENIOR | ADVANCED | IMPORTANT | GRADE_TOO_EASY, DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | ADVANCED Senior фактически проверяет узнавание одного базового свойства криптографической аутентификации контекста. Сложные термины не добавляют системного judgement: rotation упомянута, но не влияет на альтернативы; три отвлечения либо сохраняют описанный дефект, либо меняют нерелевантный параметр. Инженерного выбора по взаимодействующим границам недостаточно. |

### Cross-bank comparison

All **3,375 new-to-existing pairs** were considered through manual bucket/cross-grade review, with lexical similarity only assisting re-reading. **0 exact duplicates / 0 established new-to-existing near-duplicates**. Shared themes were not classified as duplicate without the same cognitive requirement. The baseline severity register was not re-audited or rewritten.

| Compared codes | Disposition | Safe rationale |
| --- | --- | --- |
| backend-junior-programming-8-v1, backend-junior-programming-1-v1, backend-junior-programming-3-v1 | acceptable_thematic_overlap | Общая тема изменяемости; новые вложенные связи объектов отличаются от мутации аргумента и жизни значения по умолчанию. |
| backend-junior-architecture-8-v1, backend-senior-architecture-4-v3 | acceptable_cross_grade_overlap | Локальная коммерческая граница отличается от системного replay, срока доверенного решения и восстановления между владельцами. |
| backend-middle-programming-7-v1, backend-middle-programming-3-v2 | theme_overlap_with_separate_grade_finding | Локальная ленивость отличается от согласования ограниченной очереди, скорости подтверждаемого sink и порядка. IMPORTANT нового вопроса относится к слабому Middle demand, не к буквальному повтору старого. |
| backend-middle-http_api-8-v1, backend-middle-http_api-2-v2 | acceptable_thematic_overlap | Продолжение частичного чтения и смена версии отличается от конкурентной условной мутации и атомарной проверки версии. |
| backend-middle-databases-7-v1, backend-middle-databases-3-v1, backend-middle-http_api-5-v2 | acceptable_cross_competency_overlap | Устойчивый порядок одного ограниченного чтения отличается от структуры индекса и контракта полного обхода фиксированной публикационной границы. |
| backend-middle-architecture-7-v1, backend-senior-architecture-8-v1, backend-senior-http_api-2-v2, backend-senior-databases-3-v2 | theme_overlap_with_separate_difficulty_finding | Совместимость кеша, появление значения в общей БД, маршрутизация API-контракта и совместимость writers при backfill имеют разные границы. IMPORTANT нового Senior ADVANCED относится к упрощённым альтернативам и demand. |
| backend-middle-testing_security_debugging-8-v1, backend-junior-testing_security_debugging-5-v2, backend-middle-testing_security_debugging-4-v2 | acceptable_diagnostic_overlap | Разные диагностические действия касаются размеров промежуточных объектов, отсутствующего поля и оценок SQL-плана; общая работа с evidence не делает их одним заданием. |
| backend-senior-http_api-7-v1, backend-middle-architecture-5-v1, backend-senior-databases-2-v2 | acceptable_cross_competency_overlap | Граница доверия входящей доставки отличается от атомарной локальной обработки и согласования transaction retry с внешним эффектом. |
| backend-senior-architecture-7-v1, backend-senior-programming-1-v1, backend-middle-programming-5-v2 | acceptable_thematic_overlap | Изоляция арендаторов и невытесняемой занятой ёмкости отличается от глобальной перегрузки и общего дедлайна пакетной операции. |
| backend-senior-testing_security_debugging-7-v1, backend-senior-testing_security_debugging-8-v1, backend-senior-testing_security_debugging-3-v2 | acceptable_security_overlap | Жизнь разрешения от постановки до исполнения, криптографическая связь объекта и актуальная выдача кешированных данных требуют разных предметных границ. |

New-to-new local overlap findings (already counted once in the 45-item register):

- **MINOR** — `backend-junior-programming-7-v1`, `backend-junior-http_api-7-v1`: Два новых вопроса того же grade сильно перекрываются по различению отсутствия и допустимого ложного значения. Языковой и HTTP контексты различаются, поэтому finding локальный.
- **IMPORTANT** — `backend-middle-databases-6-v1`, `backend-middle-databases-8-v1`: Базовая граница snapshot между statements повторно проверяется в ADVANCED без достаточного дополнительного взаимодействия требований. Severity закреплена за ADVANCED записью; BASIC сам по себе уместен.

### Independent audit limitations

- Качественный экспертный review одного независимого reviewer. Не выполнялись пилотирование, психометрическая калибровка, измерение discrimination/reliability или эмпирическая эквивалентность grades.
- 75 baseline записей прочитаны для near-duplicate сравнения; их прежние severity не пересматривались и этот файл не заменяет P3 provenance.
- Семантическое сопоставление не является математическим доказательством отсутствия всех возможных смысловых повторов. Само число 3375 лексических сравнений не заменяет ручного чтения.
- Не проверялись runtime marking, выбор, option ordering, seed/DB immutability, история попыток или технические gates; их доказательства должны быть отдельными от content review.
- Наличие уникального лучшего выбора не означает, что item измеряет заявленный уровень. Все IMPORTANT здесь относятся к качеству измерения grade/difficulty, а не к установленному неверному scoring.
- Оговорки полноты восстановительного набора и количественной нагрузки классифицированы MINOR: по имеющимся вариантам не установлен scoring failure. Не следует выводить из этих вопросов строгие общие гарантии за пределами явно заданной модели.

Primary sources were used for factual premises only, without publishing solutions or calibrating grades: [Python 3.13 Built-in Types](https://docs.python.org/3.13/library/stdtypes.html), [Python 3.13 Coroutines and Tasks](https://docs.python.org/3.13/library/asyncio-task.html), [Python 3.13 decimal](https://docs.python.org/3.13/library/decimal.html), [Python 3.13 pathlib](https://docs.python.org/3.13/library/pathlib.html), [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html), [PostgreSQL 17 Transaction Isolation](https://www.postgresql.org/docs/17/transaction-iso.html), [PostgreSQL 17 Aggregate Functions](https://www.postgresql.org/docs/17/functions-aggregate.html), [PostgreSQL 17 LIMIT and OFFSET](https://www.postgresql.org/docs/17/queries-limit.html), [PostgreSQL 17 Routine Vacuuming](https://www.postgresql.org/docs/17/routine-vacuuming.html), [RFC 5116 AEAD](https://www.rfc-editor.org/rfc/rfc5116.html), [RFC 7517 JSON Web Key](https://www.rfc-editor.org/rfc/rfc7517.html).

## Disposition

**P5 is not complete and is not PR-ready.** The seven IMPORTANT items require a separate human decision and an explicitly authorized remediation scope. No post-freeze content edits, silent remediation, push, PR or merge are performed in this execution. The frozen implementation and this audit report are retained locally for review. CI for a new PR has not run because no PR was created.
