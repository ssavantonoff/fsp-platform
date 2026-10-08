# Assessment bank diversity — P5 frozen implementation and review

> **Current execution: P5-B — CONTENT AND FINAL TECHNICAL GATES PASSED.** The first P5 audit below is preserved as historical evidence (0 / 7 / 21 / 17). The user authorized exactly seven unpublished v1 content edits in P5-B. The current source freeze and results are recorded in the P5-B section at the end; prior STOP/prohibition statements describe the completed first execution. Both gates below have passed; branch publication and a PR for human review are authorized. No merge is authorized.

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

## P5-B — authorized seven-item remediation and new source freeze

- Starting P5-B HEAD: `61d1a28d9e3fad7e51bcc4af73dbe6a468d96edb`.
- Current origin/main verified at pre-flight: `f4fc87ccad953979be82cbe8118142d74be50c1d`.
- Same branch: `feat/assessment-bank-diversity`.
- New content freeze commit: `41c3c37db5aa2aa695218a8943607403de5ee288`.
- New freeze UTC: `2026-10-08T16:34:00Z`.
- New source SHA256: `76cda12d6358f14da84cce0ac584035ab189ae7a2f43e18d1e3cfed41276023c`.
- Previous source freeze/hash and failed register above remain historical evidence.

The P5-B task explicitly permits in-place edits to these unpublished v1 records: they are not in main, a PR or a production release. No v2 records, supersedes relationships or additional questions were created. All grade/competency/difficulty/version/code metadata and record ordering remain unchanged. No MINOR cleanup was performed.

### Exact seven authorized targets

| Code | Grade | Competency | Difficulty | Previous IMPORTANT categories |
| --- | --- | --- | --- | --- |
| backend-junior-testing_security_debugging-8-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | ADVANCED | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS |
| backend-middle-programming-7-v1 | MIDDLE | PROGRAMMING | APPLIED | GRADE_TOO_EASY, DIFFICULTY_MISMATCH, WEAK_DISTRACTORS |
| backend-middle-programming-8-v1 | MIDDLE | PROGRAMMING | ADVANCED | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS |
| backend-middle-databases-8-v1 | MIDDLE | DATABASES | ADVANCED | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS, COGNITIVE_OVERLAP |
| backend-middle-architecture-8-v1 | MIDDLE | ARCHITECTURE | ADVANCED | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS |
| backend-senior-architecture-8-v1 | SENIOR | ARCHITECTURE | ADVANCED | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS |
| backend-senior-testing_security_debugging-8-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | ADVANCED | GRADE_TOO_EASY, DIFFICULTY_MISMATCH, WEAK_DISTRACTORS |

### Scope and structural proof

Comparison against `a0e5d399fe443ef7bc0796fa9b5dde3eee97e0f9` establishes exactly seven changed content records. The original 75 P3 records and the other 38 P5 records are content-equivalent; their existing JSON serialization is retained. The 45 P5 additions remain unique v1 records without supersedes. Current source remains **120 / 40 per grade / 2 BASIC + 4 APPLIED + 2 ADVANCED per bucket**. Immediate structural validation after editing gives **0 findings**.

One new regression in `backend/tests/test_assessment_diversity.py` freezes opaque model-content hashes for all 45 records of the failed first source. It requires exactly the seven authorized records to differ, preserves the other 38 and checks the unchanged v1 metadata. Existing frozen original-75 checks and all selection/lineage/option-persistence regressions remain. No source selection, history, scoring, cooldown, API, Matching, Invitations, FSP or migration implementation changes occur in P5-B.

### New independent audit

**P5 CONTENT GATE PASSED: 0 BLOCKER / 0 IMPORTANT / 28 MINOR / 17 OK.**

Independent review completed UTC: `2026-10-08T16:49:58.366642Z`. A new reviewer independently read all **45 P5 stems / 180 alternatives** and all **75 P3 stems / 300 alternatives**. No authoring rationale, author scripts or technical test success was used as content-quality evidence. The full primary register was saved at `2026-10-08T16:41:01.636484Z` before reading the previous P5 register. Its primary result was 0 / 0 / 25 / 20; all subsequent refinements are recorded below.

| Grade | BLOCKER | IMPORTANT | MINOR | OK |
| --- | ---: | ---: | ---: | ---: |
| JUNIOR | 0 | 0 | 8 | 7 |
| MIDDLE | 0 | 0 | 9 | 6 |
| SENIOR | 0 | 0 | 11 | 4 |

### Final independent register — all 45 P5 items

One item is counted once by maximum severity. Previous classifications remain above as provenance. This safe register contains no marking positions, alternatives, keys or solutions.

| Code | Grade | Competency | Difficulty | Previous → current | Categories | Safe audit finding |
| --- | --- | --- | --- | --- | --- | --- |
| backend-junior-programming-6-v1 | JUNIOR | PROGRAMMING | BASIC | OK → OK | — | Фундаментальное поведение объекта рассмотрено в конкретной последовательности действий; отвлекающие объяснения отражают локальные ошибочные модели. Уровень BASIC уместен, неоднозначности не найдено. |
| backend-junior-programming-7-v1 | JUNIOR | PROGRAMMING | APPLIED | MINOR → MINOR | COGNITIVE_OVERLAP | Самостоятельное локальное рассуждение о входном контракте уместно для Junior APPLIED и однозначно. Есть заметное когнитивное перекрытие с новым вопросом того же grade другой компетенции; отдельные языковой и HTTP контексты ограничивают finding уровнем MINOR. |
| backend-junior-programming-8-v1 | JUNIOR | PROGRAMMING | ADVANCED | MINOR → MINOR | WEAK_DISTRACTORS | Отвлекающие подходы мало различаются по типу локальной ошибки. Задача проверяет допустимое для Junior взаимодействие вложенного состояния и отдельного изменения; неоднозначного оценивания не установлено. |
| backend-junior-http_api-6-v1 | JUNIOR | HTTP_API | BASIC | OK → OK | — | Проверяется стандартное разграничение частей HTTP-контракта с предметно связанными альтернативами. BASIC относительно Junior уместен. |
| backend-junior-http_api-7-v1 | JUNIOR | HTTP_API | APPLIED | MINOR → MINOR | WEAK_DISTRACTORS, COGNITIVE_OVERLAP | Прикладная частичная мутация по явному контракту для Junior уместна. Одна альтернатива искусственна; дополнительно есть локальное когнитивное перекрытие с языковым вопросом того же grade. Лучшая оценка остаётся защищаемой. |
| backend-junior-http_api-8-v1 | JUNIOR | HTTP_API | ADVANCED | MINOR → MINOR | WEAK_DISTRACTORS | Условное чтение и граница HTTP-представления дают допустимое для Junior локальное взаимодействие ADVANCED. Часть пояснений альтернатив чрезмерно произвольна и облегчает исключение; существенного ослабления grade/difficulty либо scoring failure не установлено. |
| backend-junior-databases-6-v1 | JUNIOR | DATABASES | BASIC | OK → OK | — | Конкретный небольшой набор требует применить фундаментальную семантику запроса. Связанные ошибочные модели правдоподобны для Junior BASIC. |
| backend-junior-databases-7-v1 | JUNIOR | DATABASES | APPLIED | OK → OK | — | Стандартный локальный SQL-сценарий имеет защищаемый однозначный выбор и предметно связанные ошибки. Связь с Junior APPLIED сохранена. |
| backend-junior-databases-8-v1 | JUNIOR | DATABASES | ADVANCED | OK → OK | — | Требуется рассуждение о взаимодействии кратностей, агрегирования и отсутствующих дочерних данных. Альтернативы отражают распространённые локальные ошибочные сокращения; Junior ADVANCED уместен. |
| backend-junior-architecture-6-v1 | JUNIOR | ARCHITECTURE | BASIC | MINOR → MINOR | WEAK_DISTRACTORS | Локальная граница публичного ответа уместна для Junior BASIC и имеет однозначную оценку. Несколько отвлекающих стратегий не конкурируют реалистично с явным требованием ограничения данных; это локальная слабость. |
| backend-junior-architecture-7-v1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR → MINOR | WEAK_DISTRACTORS | Несколько альтернатив слишком явно расходятся с заданными ограничениями готовности и допустимой конфигурации. Прикладная локальная граница остаётся проверяемой. |
| backend-junior-architecture-8-v1 | JUNIOR | ARCHITECTURE | ADVANCED | MINOR → MINOR | WEAK_DISTRACTORS | Часть альтернатив вводит данные вне установленного входного контракта и облегчает исключение. Взаимодействие авторитетных данных и исторических условий уместно для Junior ADVANCED; scoring failure не установлен. |
| backend-junior-testing_security_debugging-6-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | BASIC | MINOR → MINOR | WEAK_DISTRACTORS | Несколько отвлекающих действий не выглядят достаточными способами изоляции исходных данных. Фундаментальный BASIC сценарий относительно Junior уместен и однозначен. |
| backend-junior-testing_security_debugging-7-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | OK → OK | — | Локальная модель вывода и недоверенного входа достаточна для однозначной предметной оценки. Связь с Junior APPLIED и данной компетенцией сохранена. |
| backend-junior-testing_security_debugging-8-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | ADVANCED | IMPORTANT → OK | — | Проверяются различимость двух локальных дефектов, момент наблюдения и успешный путь. Альтернативы отличаются содержательным покрытием; взаимодействие условий соответствует Junior ADVANCED. |
| backend-middle-programming-6-v1 | MIDDLE | PROGRAMMING | BASIC | MINOR → MINOR | WEAK_DISTRACTORS | Один отвлекающий способ содержит явную утрату информации, несколько других объединяются одной ошибкой представления. Базовое предметное различие для Middle сохраняется. |
| backend-middle-programming-7-v1 | MIDDLE | PROGRAMMING | APPLIED | IMPORTANT → OK | — | Взаимодействуют границы входных частей, ограничение памяти, сохранность данных и завершение потока. Ошибочные способы содержательно конкурируют, APPLIED измеряет применение при компонентных ограничениях. |
| backend-middle-programming-8-v1 | MIDDLE | PROGRAMMING | ADVANCED | IMPORTANT → OK | — | Одновременно рассматриваются независимые ожидания, общий жизненный цикл и конкурентная очистка. Альтернативы отличаются существенными локальными протоколами; ADVANCED соответствует Middle. |
| backend-middle-http_api-6-v1 | MIDDLE | HTTP_API | BASIC | OK → OK | — | Короткий BASIC проверяет конкретное протокольное различие, а предметно связанные альтернативы сохраняют однозначность. Терминология сама по себе не использована для требования более высокого уровня. |
| backend-middle-http_api-7-v1 | MIDDLE | HTTP_API | APPLIED | OK → OK | — | Прикладной контракт включает поведение последующего запроса и повторного пользовательского действия. Альтернативы требуют предметного различения HTTP-семантики; контекст достаточен. |
| backend-middle-http_api-8-v1 | MIDDLE | HTTP_API | ADVANCED | MINOR → MINOR | WEAK_DISTRACTORS | Часть альтернатив объединяет явную несогласованность версии с недостаточностью данных и облегчает исключение; два подхода близки по ошибке. Протокольное и клиентское ограничения взаимодействуют, существенный дефект ADVANCED не доказан. |
| backend-middle-databases-6-v1 | MIDDLE | DATABASES | BASIC | MINOR → MINOR | WEAK_DISTRACTORS | Некоторые отвлекающие объяснения технически малоправдоподобны. Базовая для Middle семантика транзакций проверяется; отсутствующего решающего контекста не найдено. |
| backend-middle-databases-7-v1 | MIDDLE | DATABASES | APPLIED | MINOR → MINOR | WEAK_DISTRACTORS | Один отвлекающий подход почти не воздействует на описанную проблему, поэтому выбор облегчается. Прикладная гарантия запроса отличается от задачи выбора индекса; оценивание однозначно. |
| backend-middle-databases-8-v1 | MIDDLE | DATABASES | ADVANCED | IMPORTANT → OK | — | Ограничения длительности владения snapshot, изменяемых значений, публикации и дальнейшей выдачи взаимодействуют. Альтернативы содержательно различают границы согласованности; ADVANCED уместен. |
| backend-middle-architecture-6-v1 | MIDDLE | ARCHITECTURE | BASIC | MINOR → MINOR | WEAK_DISTRACTORS | Некоторые отвлекающие выводы чрезмерны относительно доступных наблюдений. Короткий BASIC проверяет допустимую компонентную границу, длина сама по себе недостатком не считается. |
| backend-middle-architecture-7-v1 | MIDDLE | ARCHITECTURE | APPLIED | OK → MINOR | WEAK_DISTRACTORS | Отвлекающие планы слишком мало учитывают одновременную работу несовместимых экземпляров. Предметное применение при rollout и rollback сохранено; значимое ослабление Middle не установлено. |
| backend-middle-architecture-8-v1 | MIDDLE | ARCHITECTURE | ADVANCED | IMPORTANT → OK | — | Версионная согласованность, кеш и общий срок ответа взаимодействуют. Правдоподобные локальные отклонения проверяют компромисс доступности и согласованности; ADVANCED соответствует Middle. |
| backend-middle-testing_security_debugging-6-v1 | MIDDLE | TESTING_SECURITY_DEBUGGING | BASIC | MINOR → MINOR | WEAK_DISTRACTORS | Несколько отвлекающих проверок почти не исследует заданную privacy-границу. BASIC относительно Middle допустим; безопасное однозначное оценивание сохранено. |
| backend-middle-testing_security_debugging-7-v1 | MIDDLE | TESTING_SECURITY_DEBUGGING | APPLIED | OK → MINOR | WEAK_DISTRACTORS | Часть альтернатив ограничивается проверками, слабо связанными с фактической границей доступа. Явная модель неизменности файлов снимает конкурентную неоднозначность; прикладной предметный выбор остаётся. |
| backend-middle-testing_security_debugging-8-v1 | MIDDLE | TESTING_SECURITY_DEBUGGING | ADVANCED | OK → MINOR | WEAK_DISTRACTORS | Локализованные наблюдения о стадии, размере входа и промежуточном состоянии требуют совместного диагностического применения и допустимы для Middle ADVANCED. Несколько отвлекающих экспериментов плохо адресуют наблюдаемые границы и облегчают выбор; существенного нарушения difficulty/grade не установлено. |
| backend-senior-programming-6-v1 | SENIOR | PROGRAMMING | BASIC | OK → MINOR | WEAK_DISTRACTORS | Все отвлекающие модели чтения упрощены и облегчают исключение по заявленной согласованности. Базовое системное требование единой версии для запроса уместно относительно Senior. |
| backend-senior-programming-7-v1 | SENIOR | PROGRAMMING | APPLIED | MINOR → MINOR | WEAK_DISTRACTORS | Несколько отвлекающих политик явно нарушает заданные условия завершения и подтверждения. Прикладная операционная граница между жизнью экземпляра и устойчивым результатом сохраняет Senior связь; существенного провала уровня не доказано. |
| backend-senior-programming-8-v1 | SENIOR | PROGRAMMING | ADVANCED | OK → MINOR | WEAK_DISTRACTORS | Некоторые отвлекающие способы откладывают контроль до очевидно позднего этапа. Ограничения отдельной обработки и общей конкурентной ёмкости взаимодействуют и поддерживают Senior ADVANCED demand. |
| backend-senior-http_api-6-v1 | SENIOR | HTTP_API | BASIC | OK → MINOR | WEAK_DISTRACTORS | Некоторые альтернативы явно разрывают заданную общую границу квоты. Короткий BASIC про владение и многократные экземпляры допустим относительно Senior. |
| backend-senior-http_api-7-v1 | SENIOR | HTTP_API | APPLIED | OK → MINOR | WEAK_DISTRACTORS | Один отвлекающий подход одновременно нарушает несколько явно указанных требований. Остальные различия и взаимодействие trust, повторов и устойчивости сохраняют прикладное Senior измерение. |
| backend-senior-http_api-8-v1 | SENIOR | HTTP_API | ADVANCED | OK → OK | — | Есть взаимодействие распространения доверенного материала, срока существующих credentials и mixed rollout. Альтернативы задают разные этапы жизненного цикла; системное ADVANCED суждение сохраняется. |
| backend-senior-databases-6-v1 | SENIOR | DATABASES | BASIC | MINOR → MINOR | WEAK_DISTRACTORS | Отвлекающие свидетельства очевидно недостаточны для указанного восстановительного требования. Базовая операционная задача для Senior однозначна, её системная предметная связь сохраняется. |
| backend-senior-databases-7-v1 | SENIOR | DATABASES | APPLIED | MINOR → MINOR | WEAK_DISTRACTORS | Несколько отвлекающих операций плохо адресует описанную удерживаемую границу. Предметная связь между транзакционной видимостью и операционными последствиями для Senior сохраняется. |
| backend-senior-databases-8-v1 | SENIOR | DATABASES | ADVANCED | MINOR → MINOR | WEAK_DISTRACTORS, CONTEXT_SCOPE | Отвлекающие планы заметно нарушают необходимость учитывать независимое устойчивое состояние. Дополнительно слабо описана полнота восстанавливаемого набора принятых операций и данных для сверки. Системное взаимодействие остаётся уместным для Senior ADVANCED; среди имеющихся вариантов scoring failure не установлен. |
| backend-senior-architecture-6-v1 | SENIOR | ARCHITECTURE | BASIC | OK → OK | — | Проверяется операционное решение при измеренном влиянии локального релиза на общую зависимость. Системные границы и допустимое восстановление поведения поддерживают BASIC относительно Senior. |
| backend-senior-architecture-7-v1 | SENIOR | ARCHITECTURE | APPLIED | MINOR → MINOR | WEAK_DISTRACTORS, CONTEXT_SCOPE | Один отвлекающий подход практически не влияет на конкурентную ёмкость. Количественное обещание ожидания также опирается на слабо раскрытую достаточность выделенной доли; пиковые поступления и длительность обслуживания не детализированы. Системная задача Senior APPLIED и лучшая относительная стратегия сохраняются. |
| backend-senior-architecture-8-v1 | SENIOR | ARCHITECTURE | ADVANCED | IMPORTANT → OK | — | Сочетаются mixed readers, задержанные команды, конкурентное отключение и сохранность смысла данных при rollback. Альтернативы различают существенные архитектурные границы; Senior ADVANCED обоснован. |
| backend-senior-testing_security_debugging-6-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | BASIC | MINOR → MINOR | WEAK_DISTRACTORS | Некоторые альтернативы повторяют очевидную несопоставимость наблюдений. BASIC про оценку системного релиза уместен относительно Senior, однозначность сохраняется. |
| backend-senior-testing_security_debugging-7-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR → MINOR | WEAK_DISTRACTORS | Часть отвлекающих подходов слишком явно расходится с требованием актуальности разрешения. Прикладная trust-граница отложенного системного исполнения остаётся проверяемой; значимого ослабления Senior не доказано. |
| backend-senior-testing_security_debugging-8-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | ADVANCED | IMPORTANT → OK | — | Измеряется достаточность evidence для двух различных системных границ и совместимости изменений. Альтернативы сохраняют реалистичные неполные наборы проверок; Senior ADVANCED уместен. |

### Comparison with the failed first audit

Новый полный audit заново оценивает весь frozen content. Сохранены все 21 прежних MINOR; все 7 прежних IMPORTANT устранены содержательными изменениями и оценены OK. Дополнительно установлены 7 локальных MINOR на неизменённых записях: это уточнения качественного review, а не новая контентная регрессия. Первичный независимый реестр и последующие изменения классификации сохранены отдельно; counts не заменялись целевыми.

- **7 resolved IMPORTANT → OK**: exactly the seven authorized content edits.
- **21 persisting MINOR**: not remediated in this pass.
- **7 new MINOR on unchanged content**: additional qualitative findings, without a content change to those records.
- **10 unchanged OK**.

The increase from 21 to 28 MINOR reflects the fresh review of all 45 items. It is not a silent expansion of remediation scope. All seven edited records are now OK; no BLOCKER or IMPORTANT remains.

Primary-register refinements after reading the previous safe audit and rechecking actual content:

| Code | Primary → final | Final categories | Safe recheck reason |
| --- | --- | --- | --- |
| backend-junior-programming-7-v1 | OK → MINOR | COGNITIVE_OVERLAP | Первичное чтение отметило общую тему, но недооценило одинаковое различение двух случаев входа. После сопоставления actual content локальное перекрытие сохранено, без повышения до near-duplicate существенного уровня. |
| backend-junior-http_api-7-v1 | OK → MINOR | WEAK_DISTRACTORS, COGNITIVE_OVERLAP | При первичном чтении недооценены искусственный отвлекающий подход и одинаковое различение двух случаев входа в соседней компетенции. Оба недостатка локальные. |
| backend-junior-architecture-6-v1 | OK → MINOR | WEAK_DISTRACTORS | Сам предметный BASIC demand сохраняется; при повторном чтении по той же rubric слабость нескольких альтернатив достаточно явна для MINOR. Первичное OK недооценивало этот локальный недостаток. |
| backend-junior-http_api-8-v1 | MINOR → MINOR | WEAK_DISTRACTORS | Категория DIFFICULTY_MISMATCH сужена: по final P3 rubric взаимодействие локальных протокольных условий для Junior допустимо. Сохраняется только установленная слабость вариантов, severity не меняется. |
| backend-senior-databases-8-v1 | MINOR → MINOR | WEAK_DISTRACTORS, CONTEXT_SCOPE | Контекстная оговорка была замечена при первичном чтении, но не включена в реестр. Отдельный поиск по известной identity не доказывает полноту восстановительного набора; это ограничение общей гарантии, а не равноправная альтернатива или BLOCKER. |
| backend-senior-architecture-7-v1 | MINOR → MINOR | WEAK_DISTRACTORS, CONTEXT_SCOPE | Повторное чтение сохраняет локальную оговорку количественного контекста. Из заявленной достаточности доли нельзя выводить универсальную гарантию для любых неописанных нагрузок; выбор среди данных альтернатив остаётся однозначным. |
| backend-middle-testing_security_debugging-8-v1 | MINOR → MINOR | WEAK_DISTRACTORS | При сверке final P3 rubric диагностическое взаимодействие признано достаточным для ADVANCED; прежняя первичная категория DIFFICULTY_MISMATCH снята. Независимое локальное замечание к нескольким экспериментам сохранено, severity остаётся MINOR. |

### Renewed full-bank comparison

All 120 stems and 480 alternatives were read by competency and across grades. A reviewer-created supplementary lexical screen covered 3375 P5-to-P3 pairs and 990 P5-to-P5 pairs after the primary manual register. It only supported renewed comparisons; it did not set severity or replace reading.

**0 established P5-to-P3 near-duplicates; 0 established new material near-duplicates.** One local Junior P5-to-P5 cognitive overlap group remains MINOR. The previous material Middle DATABASES overlap is resolved. Existing P3 severity provenance is preserved, not rewritten.

| Codes compared | Scope | Classification | Safe comparison finding |
| --- | --- | --- | --- |
| backend-junior-programming-8-v1, backend-junior-programming-1-v1, backend-junior-programming-3-v1 | P5_TO_P3 | OK — acceptable_thematic_overlap | Связь вложенных объектов, мутация аргумента и жизнь значения по умолчанию относятся к общей теме изменяемости, но требуют разных локальных выводов. Новый вопрос не повторяет когнитивную задачу P3. |
| backend-junior-testing_security_debugging-6-v1, backend-junior-programming-1-v1, backend-junior-programming-3-v1 | P5_TO_P3 | OK — acceptable_cross_competency_overlap | Общая фундаментальная изменяемость применяется к изоляции независимых тестовых сценариев, а не к определению результата вызова функции или её входной модели. Локальная слабость альтернатив учтена в индивидуальном P5 реестре. |
| backend-junior-architecture-6-v1, backend-senior-testing_security_debugging-1-v2 | P5_TO_P3 | OK — acceptable_cross_grade_competency_overlap | Граница публичного ответа одной модели и системная граница меняющихся producers до независимого контура хранения имеют общую тему ограничения данных, но разные ownership, последствия и grade demand. |
| backend-junior-testing_security_debugging-7-v1, backend-junior-testing_security_debugging-2-v1 | P5_TO_P3 | OK — acceptable_security_overlap | Обработка недоверенного входа рассматривается в разных интерпретирующих контекстах. Общая security-тема не означает один и тот же предметный механизм или когнитивный вывод. |
| backend-junior-http_api-8-v1, backend-junior-http_api-1-v1, backend-middle-http_api-2-v2 | P5_TO_P3 | OK — acceptable_protocol_overlap | Результат создания, условная выдача представления и конкурентная мутация требуют разных протокольных выводов. Локальная слабость P5 вариантов отдельно сохранена; новая P5 запись не повторяет P3 demand. |
| backend-junior-databases-8-v1, backend-junior-databases-5-v1, backend-middle-databases-2-v2 | P5_TO_P3 | OK — acceptable_thematic_overlap | Сохранность родителей при фильтрации, взаимодействие кратностей агрегатов и измеренный выбор стратегии загрузки рассматривают разные границы данных и ограничений. |
| backend-junior-architecture-8-v1, backend-senior-architecture-4-v3 | P5_TO_P3 | OK — acceptable_cross_grade_overlap | Локальная авторитетная коммерческая граница отличается от системных replay, срока доверенного решения, исторических условий и восстановления между владельцами. Выраженное одинаковое когнитивное требование не установлено. |
| backend-junior-testing_security_debugging-8-v1, backend-junior-programming-4-v1, backend-junior-testing_security_debugging-3-v1 | P5_TO_P3 | OK — acceptable_cross_competency_overlap | Выбор реализации локального ресурса и выбор достаточного evidence для двух дефектов отличаются по предметному действию. Новый ADVANCED добавляет взаимодействие исходов и момента наблюдения, а не пересказывает один P3 механизм. |
| backend-middle-programming-7-v1, backend-middle-programming-3-v2, backend-middle-programming-5-v2 | P5_TO_P3 | OK — acceptable_thematic_overlap | Общий streaming и ресурсные бюджеты не задают duplicate: новый разбор границ входа и завершения отличается от согласования sink throughput, очереди и исполнения пакета. Новое APPLIED требование больше не исчерпывается одной локальной ленивостью. |
| backend-middle-programming-8-v1, backend-middle-programming-1-v1, backend-middle-programming-5-v2, backend-senior-programming-2-v2, backend-senior-programming-5-v2 | P5_TO_P3 | OK — acceptable_cross_grade_overlap | Локальный registry общих ожиданий с cleanup отличается от потери обновления, ограниченного пакетного исполнения, внешнего восстановимого резерва и устойчивого распределённого job с поколениями. Новые конкурирующие жизненные циклы поддерживают Middle ADVANCED. |
| backend-middle-http_api-6-v1, backend-junior-http_api-1-v1 | P5_TO_P3 | OK — acceptable_protocol_overlap | Общая форма выбора HTTP-статуса не означает одинаковое знание: разные условия операции и представления дают разные предметные протокольные границы. Короткий Middle BASIC относительно grade допустим. |
| backend-middle-http_api-8-v1, backend-middle-http_api-2-v2 | P5_TO_P3 | OK — acceptable_thematic_overlap | Продолжение частичного чтения и смена версии отличаются от конфликтующего обновления с атомарной проверкой. Похожая протокольная терминология не задаёт near-duplicate. |
| backend-middle-databases-7-v1, backend-middle-databases-3-v1, backend-middle-http_api-5-v2 | P5_TO_P3 | OK — acceptable_cross_competency_overlap | Устойчивое ограниченное чтение, соответствие индекса и полный обход фиксированной публикационной границы требуют разных выводов. Новый вопрос не повторяет более широкий контракт P3. |
| backend-middle-databases-8-v1, backend-middle-databases-4-v3, backend-senior-databases-1-v2 | P5_TO_P3 | OK — acceptable_consistency_overlap | Материализация и публикация отчёта отличаются от конкурентной актуальности расчёта перед мутацией и агрегатного инварианта бронирований. Взаимодействующие ограничения нового ADVANCED не сводятся к общему слову snapshot. |
| backend-middle-architecture-7-v1, backend-senior-http_api-2-v2, backend-senior-databases-3-v2 | P5_TO_P3 | OK — acceptable_cross_grade_rollout_overlap | Совместимость производного кеша, routing контрактов и согласованность writers при backfill имеют разные границы владения и rollback. Локальная слабость P5 альтернатив не превращает их в повтор P3. |
| backend-middle-architecture-8-v1, backend-middle-architecture-3-v2, backend-senior-architecture-5-v2, backend-senior-programming-5-v2 | P5_TO_P3 | OK — acceptable_cross_grade_overlap | Согласованность необязательного результата с версией и сроком ответа отличается от изоляции отказной зависимости, доказуемой системной свежести и распределённого поколенческого job. Наборы существенных ограничений и архитектурные роли различаются. |
| backend-middle-testing_security_debugging-8-v1, backend-junior-testing_security_debugging-5-v2, backend-middle-testing_security_debugging-4-v2 | P5_TO_P3 | OK — acceptable_diagnostic_overlap | Размер промежуточных объектов, различие отсутствующего поля и стоимость SQL-плана дают разные диагностические проверки. Общая работа с наблюдениями не делает вопросы одним заданием; новое локальное замечание к альтернативам учтено отдельно. |
| backend-senior-http_api-7-v1, backend-middle-architecture-5-v1, backend-senior-databases-2-v2 | P5_TO_P3 | OK — acceptable_cross_competency_overlap | Граница доверия входящей доставки с временным контекстом отличается от локального атомарного consumer и согласования transaction retry с внешними последствиями. Повторы — общая тема, но предметные требования различны. |
| backend-senior-databases-8-v1, backend-senior-databases-2-v2, backend-senior-testing_security_debugging-2-v2, backend-senior-testing_security_debugging-5-v2 | P5_TO_P3 | OK — acceptable_recovery_overlap | Возврат после отката DB во времени отличается от транзакционного retry и доказательств отдельного неопределённого интервала процесса. Системные источники состояния и масштаб восстановления различаются; ограничение полноты нового сценария отражено как MINOR. |
| backend-senior-architecture-6-v1, backend-middle-architecture-3-v2, backend-senior-testing_security_debugging-4-v2 | P5_TO_P3 | OK — acceptable_cross_grade_operations_overlap | Первое решение при влиянии релиза на общую зависимость отличается от политики деградации компонента и плана диагностики полноты telemetry. Общая тема повторов не повторяет когнитивный выбор P3. |
| backend-senior-architecture-7-v1, backend-senior-programming-1-v1, backend-middle-programming-5-v2 | P5_TO_P3 | OK — acceptable_thematic_overlap | Межпользовательская гарантия доступа при невытесняемой работе отличается от общей перегрузки и бюджета пакетной операции. Сохраняются локальные замечания к контексту и альтернативам, существенный cross-grade overlap не установлен. |
| backend-senior-testing_security_debugging-6-v1, backend-senior-testing_security_debugging-4-v2 | P5_TO_P3 | OK — acceptable_observability_overlap | Сопоставимость компонентов одного показателя и репрезентативность связанной latency-выборки проверяют разные основания системного наблюдения. BASIC первого не требует такого же диагностического охвата, как APPLIED второго. |
| backend-senior-testing_security_debugging-7-v1, backend-senior-testing_security_debugging-3-v2, backend-middle-testing_security_debugging-1-v1 | P5_TO_P3 | OK — acceptable_cross_grade_security_overlap | Актуальность разрешения при отложенном опасном действии, актуальная выдача кешированных данных и локальная проверка владения имеют разные временные и системные trust-границы. |
| backend-senior-testing_security_debugging-8-v1, backend-senior-testing_security_debugging-2-v2, backend-senior-testing_security_debugging-5-v2 | P5_TO_P3 | OK — acceptable_evidence_overlap | Достаточность evidence для криптографического контекста и конкурентной перешифровки отличается от согласованности транзакционных последствий и повторного внешнего эффекта. Общий тестовый язык не задаёт near-duplicate. |
| backend-junior-programming-7-v1, backend-junior-http_api-7-v1 | P5_TO_P5 | MINOR — persisting_local_cognitive_overlap | Оба новых вопроса одного grade требуют одинакового различения двух случаев входного контракта. Языковой и HTTP контексты различаются, поэтому локальное когнитивное перекрытие остаётся MINOR и учтено один раз в severity каждого затронутого item. |
| backend-middle-databases-6-v1, backend-middle-databases-8-v1 | P5_TO_P5 | OK — resolved_previous_material_cognitive_overlap | Новый ADVANCED включает дальнейшую выдачу, изменяемые значения, короткую границу создания и атомарную публикацию. Прежнее повторение одной базовой семантики snapshot устранено; BASIC остаётся самостоятельным. |
| backend-middle-http_api-6-v1, backend-middle-http_api-8-v1, backend-junior-http_api-8-v1 | P5_TO_P5 | OK — acceptable_new_cross_grade_protocol_overlap | Статус частичного ответа, условное чтение и согласованное продолжение разных версий требуют разных протокольных выводов. Различаются BASIC, локальный Junior ADVANCED и применение взаимодействующих Middle ограничений. |
| backend-senior-architecture-6-v1, backend-senior-testing_security_debugging-6-v1 | P5_TO_P5 | OK — acceptable_new_cross_competency_operations_overlap | Одинаковый canary контекст используется для решения о системном воздействии и для проверки корректности измерения. Когнитивные требования относятся к разным компетенциям и не совпадают. |
| backend-senior-databases-6-v1, backend-senior-databases-8-v1 | P5_TO_P5 | OK — acceptable_new_within_grade_progression | Базовая достаточность восстановительного evidence отличается от возврата согласованного исполнения при независимых последствиях после точки backup. ADVANCED добавляет системные границы отказа. |
| backend-senior-architecture-8-v1, backend-senior-testing_security_debugging-7-v1 | P5_TO_P5 | OK — acceptable_new_cross_competency_overlap | Актуальность отложенного разрешения участвует в обоих сценариях, но новый ADVANCED одновременно включает mixed readers, поколения команд, смысл данных и поддерживаемый rollback. Поставленные инженерные задачи различаются. |

### Independent method and limitations

Same rubric as the final P3 audit (`docs/assessment-bank-audit-v3.md`):

| Severity | Meaning |
| --- | --- |
| BLOCKER | Нет защищаемой однозначной оценки либо отсутствующий решающий контекст меняет ответ. |
| IMPORTANT | Лучший выбор вероятен, но существенно ослаблено измерение grade, difficulty или competency. |
| MINOR | Локальный недостаток без установленного scoring failure или значимого ослабления измерения. |
| OK | В качественном review finding не найден; это не сертификат. |

BASIC is relative to grade. Technical terminology alone does not establish Senior demand. ADVANCED requires interaction between material constraints. Themes shared across questions are distinguished from the same cognitive requirement. Grade/difficulty/competency fit, alternative realism, a defensible single best choice, decisive context and grade overlap were reviewed across all five competency sets.

- Качественный экспертный аудит без эмпирической difficulty/discrimination/reliability или hiring-validity калибровки.
- Контент прочитан целиком; API privacy, live DB и пользовательский runtime сценарий этим review не доказываются.
- Аудитор не запускал технические тесты и не менял production, tests или документацию repo.
- Контентные оценки не основаны на авторских scripts, rationale или успешности технических проверок.
- Аудит сравнивает текущие source records; не является инвентарём физических исторических DB rows.
- Семантическое сравнение качественное, а не математическое доказательство отсутствия всех возможных near-duplicates; 3375/990 lexical comparisons не заменяют полного ручного чтения.
- Количественная гарантия ожидания и полнота восстановительного набора в двух Senior сценариях имеют локальные CONTEXT_SCOPE оговорки; общие гарантии за пределами описанной модели не утверждаются.
- После сохранения первичного полного независимого реестра прочитан прежний безопасный P5 audit для disposition и согласования той же rubric. Все изменения оценок после этой сверки явно сохранены; первичная оценка не заменена задним числом.

Primary sources were used only to verify factual premises: [Python 3.13 asyncio tasks](https://docs.python.org/3.13/library/asyncio-task.html), [Python 3.13 codecs](https://docs.python.org/3.13/library/codecs.html), [PostgreSQL 17 Transaction Isolation](https://www.postgresql.org/docs/17/transaction-iso.html), [PostgreSQL 17 Routine Vacuuming](https://www.postgresql.org/docs/17/routine-vacuuming.html), [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html).

### P5-B final technical gate

Final gate ran only after the complete new independent content gate passed. All results below are from P5-B on the frozen source hash, including full reruns after the test-literal formatting correction.

| Check | P5-B actual result |
| --- | --- |
| Immediate structural validator | 0 findings; 120 / 40 per grade / 2-4-2 in all 15 buckets |
| Full SQLite, Python 3.13.16 | **806 passed / 20 PostgreSQL-only skips** |
| Full PostgreSQL 17.11, Python 3.13.16 | **826 passed / no skips** |
| Targeted `tests/test_assessment_diversity.py`, PostgreSQL 17 | **26 passed** |
| Ruff `check .` | PASS |
| Ruff `format --check .` | PASS, 56 files |
| mypy `app` | PASS, 32 source files |
| Alembic heads | Single unchanged `a812e4c79b60` |
| Alembic check | No new upgrade operations detected |
| Frontend Node 22.23.3 `npm ci` | PASS |
| Frontend lint / typecheck / build | PASS |
| Frontend tests | **106 passed / 0 failures / 0 skips** |
| Fresh Docker build / healthy startup | PASS, isolated `fsp-p5-b-diversity` project and fresh volume |
| PostgreSQL runtime | 17.11 |
| Backend `/health` and frontend `/api/skills` | HTTP 200 |
| Base / demo / matching-demo seeds, each twice | PASS; all 15 public table snapshots identical across every repeat, 120 questions / 480 alternatives |
| `git diff --check` | PASS |

Executed backend commands: `python -m pytest -q --tb=short` with empty `TEST_DATABASE_URL` (SQLite) and with the isolated PostgreSQL URL; `python -m pytest -q tests/test_assessment_diversity.py --tb=short` on PostgreSQL; `python -m ruff check .`; `python -m ruff format --check .`; `python -m mypy app`; `alembic heads`; `alembic check`. Existing literal G1 PASS 70 / G2 FAIL 80 by competency / G3 FAIL 65 / G4 PASS 100 / G5 FAIL 0 remain unchanged and pass in both full suites.

Executed frontend commands inside the existing Node 22 build stage: `npm ci`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`. No frontend source, dependency or lockfile was changed.

Docker commands used a separate `fsp-p5-b-diversity` project: fresh `down -v` / `up --build -d --wait`, followed by a rebuild after the test-only formatting correction. Seeds invoked `python -m app.seed`, `python -m app.seed --demo` and `python -m app.seed --matching-demo` twice each and compared all persisted public rows using content hashes. The earlier disposable P5 database already contained the unpublished old v1 records; it was not patched in place, and production immutable seed behavior was retained.

The first P5-B Ruff run caught long lines in the new opaque hash registry. Only those Python literals were reformatted; the complete test AST remained identical. The final Ruff/format/mypy/Alembic checks, full SQLite/PostgreSQL suites and targeted regressions were rerun against the rebuilt exact current runtime and passed. Frozen question content did not change after `41c3c37db5aa2aa695218a8943607403de5ee288`.

All 26 diversity regressions cover inventory, 2/4/2, the original frozen 75, the exact seven P5-B changes with 38 unchanged, disjoint first two forms at every grade, later exposure balance, persisted predecessor-family exposure, secure runtime tie selection and option-order persistence. The existing first P5 browser smoke above is retained; P5-B does not expand its scenario. No selection, history, scoring, cooldown, API or UI implementation changed in P5-B, and no regression was found in the final suites.

### P5-B disposition

**P5 CONTENT GATE PASSED — 0 BLOCKER / 0 IMPORTANT. Final technical gate PASS.** The exact seven authorized unpublished v1 records are remediated. All 75 original P3 records and the other 38 P5 records remain byte/content-equivalent. The source still contains 120 current questions and 45 P5 additions. The 28 local MINOR findings remain documented without cleanup; no psychometric validity claim is made.

Both gates authorize normal branch push and a PR titled `feat: diversify assessment question bank` targeting `main`, for human review. The actual PR/head/CI identity is reported in the execution result rather than predeclaring CI success in this frozen local gate report. **PR NOT MERGED. STOP after publication and verification.**
