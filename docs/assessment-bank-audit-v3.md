# Assessment bank — full content audit v3

## Decision and frozen source

P3-C2 content gate: **PASS — 0 BLOCKER / 0 IMPORTANT**. Actual result: **25 MINOR / 50 OK**. Recommendation after the technical evidence below: **MVP_READY_WITH_MINOR_FINDINGS**. P3-D local mandatory gates passed. Actual PR CI must be checked separately after creation; no merge is authorized.

- Branch: `feat/assessment-bank-remediation`.
- Original main/base: `f6ac399bd84f7379cb957d2c8f4b4c1fc31d5193`.
- Starting B2 HEAD: `6346546b22eef55ad3ef6185d23cd167a2561a0d`.
- Starting source SHA256: `079e40829c0ac41e8c893971f0b0d586ae7a071bf14d9d2a486466159ad4b30a`.
- Exact reviewed source/test HEAD: `71be88f61e0fccc5b5df4f231b572bdea151414b`.
- Audit snapshot UTC: `2026-10-07T20:43:01.372433Z`.
- Frozen current source SHA256: `11fba035b866475b588f62a142bc97f47e7fe94898afdbba3ecd263b5b7fae56`.
- Current source: `backend/app/content/backend_questions.json`.
- B2 content commit: `b67e02887160da2a6bd652194ec0ea279285ff62`; B2 regression commit: `71be88f61e0fccc5b5df4f231b572bdea151414b`.
- Provenance: [original audit](assessment-bank-audit-draft.md), [approved P3-A design](assessment-bank-remediation-plan.md), [first remediation audit v2](assessment-bank-audit-v2.md). All remain unchanged.

The source was committed before the fresh independent review and remained identical before/after review. This register covers current JSON records, not every physical historical database row. No third remediation pass or MINOR cleanup was performed.

## Independent method and rubric

Все 75 stems и 300 alternatives прочитаны до v2/draft; первичный безопасный реестр сохранён. Затем прочитаны только два прежних аудита для disposition и согласования явной rubric; авторские rationale и scripts не читались.

Reviewed **all 75 stems / all 300 alternatives**, all **15 grade × competency buckets**, and all **five same-competency cross-grade sets**, in a separate reviewer context. The implementation author checked source identity, metadata, actual counts, coverage and safe reporting; classifications were not replaced with target counts.

Every question was assessed for Backend specialization, grade, difficulty and competency fit; a single defensible best choice; multiple reasonable choices; ambiguity; missing decisive context; trivia; version dependence; knowledge versus wording; leakage; distractor quality; near-duplicates; within-grade progression; and cross-grade rubric progression.

| Grade | Frozen expectation |
| --- | --- |
| JUNIOR | Фундамент и стандартные локальные ситуации. |
| MIDDLE | Применение, ограничения компонентов и предметные компромиссы. |
| SENIOR | Системное владение, отказы, concurrency/consistency, rollout, security и observability. |

- BASIC относительно grade; короткая формулировка сама по себе не дефект.
- Сложный термин сам по себе не доказывает Senior demand.
- ADVANCED рассматривается по взаимодействию существенных ограничений.
- Один вопрос учитывается один раз по максимальной severity.
- Новые решения вне имеющихся альтернатив и нерелевантные более строгие стандарты не требуются.
- Тематическое совпадение не объявляется near-duplicate без совпадения когнитивного требования.

| Severity | Unchanged rubric |
| --- | --- |
| BLOCKER | Нет защищаемой однозначной оценки либо отсутствующий решающий контекст меняет ответ. |
| IMPORTANT | Лучший выбор вероятен, но существенно ослаблено измерение grade, difficulty или competency. |
| MINOR | Локальный недостаток без установленного scoring failure или значимого ослабления измерения. |
| OK | В этом качественном review finding не найден; это не сертификат. |

The full primary independent register contained **0 BLOCKER / 0 IMPORTANT / 22 MINOR / 53 OK**. Rechecking actual content against the same explicit v2/draft rubric restored three previously under-assessed local MINOR reasons; two other category labels were narrowed without severity changes. Final counts are **0 / 0 / 25 / 50**. No harder quality threshold or target count was introduced.

| Code | Initial | Final | Initial categories | Final categories |
| --- | --- | --- | --- | --- |
| backend-junior-programming-5-v1 | MINOR | MINOR | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | WEAK_DISTRACTORS |
| backend-junior-http_api-2-v1 | OK | MINOR | — | WEAK_DISTRACTORS |
| backend-junior-testing_security_debugging-3-v1 | OK | MINOR | — | WEAK_DISTRACTORS |
| backend-junior-testing_security_debugging-4-v1 | OK | MINOR | — | WEAK_DISTRACTORS, OTHER |
| backend-middle-programming-4-v1 | MINOR | MINOR | GRADE_TOO_EASY, WEAK_DISTRACTORS | WEAK_DISTRACTORS |

Independence qualification: После сохранения первичного полного реестра вызов list_agents непреднамеренно вернул краткую финальную заметку pre-freeze reviewer по трём уточнениям. Эта заметка не была доступна при первичном чтении и первичных классификациях; последующая сверка имеет это ограничение. Отдельные authoring reasoning/scripts или pre-freeze файлы не читались.

Primary sources used only for factual premises: [PostgreSQL 17 Transaction Isolation](https://www.postgresql.org/docs/17/transaction-iso.html), [PostgreSQL 17 Explicit Locking](https://www.postgresql.org/docs/17/explicit-locking.html), [PostgreSQL 17 SELECT](https://www.postgresql.org/docs/17/sql-select.html), [PostgreSQL 17 Index Uniqueness Checks](https://www.postgresql.org/docs/17/index-unique-checks.html), [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html), [RFC 9111 HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111.html), [Python 3.13 asyncio tasks](https://docs.python.org/3.13/library/asyncio-task.html), [Python 3.13 threading](https://docs.python.org/3.13/library/threading.html), [Python 3.13 Data Model](https://docs.python.org/3.13/reference/datamodel.html), [Python 3.13 Sorting Techniques](https://docs.python.org/3.13/howto/sorting.html). References do not calibrate grades or publish solutions.

This document contains no question text, alternatives, keys, positions or solutions. Content review does not establish candidate API privacy or live database safety; those are separately checked in P3-D.

## Inventory and actual counts

The approved first pass applied **27 replacements: 26 v1→v2 / 1 v2→v3**. B2 applies exactly **10 more versioned replacements: 3 MIDDLE / 7 SENIOR; 9 v1→v2 / 1 v2→v3**. All other **65** B1 records are content-equivalent, including **26 previously clean first-pass replacements** and all **13 prior MINOR records**. Replacement grade/competency/difficulty metadata remains exact. Only code, version, immediate supersedes, prompt and alternatives changed.

Final source remains **75 records / 25 per grade / 300 alternatives**, with **38 v1 / 35 v2 / 2 v3**. Every one of the 15 buckets retains **1 BASIC / 3 APPLIED / 1 ADVANCED**.

| Outcome | Baseline | First remediation v2 | Second remediation v3 |
| --- | --- | --- | --- |
| BLOCKER | 0 | 0 | 0 |
| IMPORTANT | 27 | 10 | 0 |
| MINOR | 6 | 13 | 25 |
| OK | 42 | 52 | 50 |

| Grade | BLOCKER | IMPORTANT | MINOR | OK | Reviewed |
| --- | --- | --- | --- | --- | --- |
| JUNIOR | 0 | 0 | 11 | 14 | 25 |
| MIDDLE | 0 | 0 | 11 | 14 | 25 |
| SENIOR | 0 | 0 | 3 | 22 | 25 |

## Disposition versus audit v2

The 75 slot dispositions are **10 resolved IMPORTANT / 13 persisting MINOR / 12 new MINOR / 40 unchanged OK**. All 10 B2 replacements are OK. All 13 previous MINOR remain MINOR after actual re-review. Every new finding concerns untouched content; no new content regression is claimed. The original audits were not retroactively edited.

| Previous code | B2 current code | Version | Current outcome | Resolved categories |
| --- | --- | --- | --- | --- |
| backend-middle-http_api-5-v1 | backend-middle-http_api-5-v2 | 2 | OK | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS |
| backend-middle-databases-4-v2 | backend-middle-databases-4-v3 | 3 | OK | CONTEXT_DEPENDENT |
| backend-middle-testing_security_debugging-5-v1 | backend-middle-testing_security_debugging-5-v2 | 2 | OK | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS |
| backend-senior-programming-4-v1 | backend-senior-programming-4-v2 | 2 | OK | DIFFICULTY_MISMATCH, GRADE_TOO_EASY, WEAK_DISTRACTORS |
| backend-senior-databases-2-v1 | backend-senior-databases-2-v2 | 2 | OK | GRADE_TOO_EASY, WEAK_DISTRACTORS |
| backend-senior-databases-4-v1 | backend-senior-databases-4-v2 | 2 | OK | DIFFICULTY_MISMATCH, GRADE_TOO_EASY, WEAK_DISTRACTORS |
| backend-senior-architecture-3-v1 | backend-senior-architecture-3-v2 | 2 | OK | GRADE_TOO_EASY, WEAK_DISTRACTORS |
| backend-senior-architecture-5-v1 | backend-senior-architecture-5-v2 | 2 | OK | DIFFICULTY_MISMATCH, GRADE_TOO_EASY, WEAK_DISTRACTORS |
| backend-senior-testing_security_debugging-2-v1 | backend-senior-testing_security_debugging-2-v2 | 2 | OK | GRADE_TOO_EASY, WEAK_DISTRACTORS |
| backend-senior-testing_security_debugging-3-v1 | backend-senior-testing_security_debugging-3-v2 | 2 | OK | CONTEXT_DEPENDENT, GRADE_TOO_EASY, WEAK_DISTRACTORS |

## Current BLOCKER / IMPORTANT findings

**None found in this full qualitative content audit.** This satisfies the conditional content prerequisite for P3-D; it is not a psychometric or hiring-validity claim.

## All current MINOR findings

All 25 are intentionally retained. Neither the 13 existing nor the 12 newly identified local findings were remediated in B2.

| Code | Grade | Competency | Difficulty | Severity | Source change | V2 disposition | Categories | Safe reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| backend-junior-programming-5-v1 | JUNIOR | PROGRAMMING | ADVANCED | MINOR | untouched | new | WEAK_DISTRACTORS | Взаимодействие локальных приоритетов допустимо для Junior ADVANCED; часть отвлекающих подходов малоправдоподобна. Это локальная слабость вариантов без доказанной инверсии сложности. |
| backend-junior-http_api-2-v1 | JUNIOR | HTTP_API | APPLIED | MINOR | untouched | persisting | WEAK_DISTRACTORS | Локальная задача входной валидации соответствует Junior; несколько отвлекающих подходов не отражают реалистичные ошибки и облегчают выбор без неоднозначного оценивания. |
| backend-junior-http_api-3-v1 | JUNIOR | HTTP_API | APPLIED | MINOR | untouched | new | WEAK_DISTRACTORS | Пояснения в отвлекающих вариантах и чрезмерные обобщения облегчают исключение по формулировке. Предметное различие сохраняется; существенного нарушения оценивания нет. |
| backend-junior-http_api-5-v1 | JUNIOR | HTTP_API | ADVANCED | MINOR | untouched | new | WEAK_DISTRACTORS | Сценарий защиты браузерной мутации соответствует Junior ADVANCED, но ошибочные подходы слишком легко исключить. Слабость ограничена качеством вариантов. |
| backend-junior-databases-5-v1 | JUNIOR | DATABASES | ADVANCED | MINOR | untouched | new | WEAK_DISTRACTORS | Есть локально слабые отвлекающие подходы; сам предметный выбор соответствует Junior и однозначен. |
| backend-junior-architecture-2-v1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR | untouched | persisting | WEAK_DISTRACTORS | Часть отвлекающих подходов явно не отвечает описанной проблеме. Локальная прикладная компетенция сохраняется. |
| backend-junior-architecture-3-v1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR | untouched | persisting | WEAK_DISTRACTORS | Некоторые отвлекающие подходы не выглядят реалистичным инженерным выбором; однозначность и предметная связь сохранены. |
| backend-junior-architecture-4-v1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR | untouched | new | WEAK_DISTRACTORS | Стандартная локальная граница соответствует Junior; отвлекающие подходы слишком явно нарушают условие доступности между экземплярами. Значимого сбоя оценивания нет. |
| backend-junior-architecture-5-v1 | JUNIOR | ARCHITECTURE | ADVANCED | MINOR | untouched | new | WEAK_DISTRACTORS | Повтор намерения и устойчивый результат образуют допустимую Junior ADVANCED задачу, однако несколько альтернатив малоправдоподобны. Содержательный дефект уровня не доказан. |
| backend-junior-testing_security_debugging-3-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | untouched | persisting | WEAK_DISTRACTORS | Предметный локальный сценарий регрессии соответствует Junior, но несколько отвлекающих проверок почти не исследуют поставленную задачу. |
| backend-junior-testing_security_debugging-4-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | untouched | persisting | WEAK_DISTRACTORS, OTHER | Задача обработки ошибки соответствует Junior и однозначна; отвлекающие подходы очевидны. Для диагностических подробностей не уточнено обезличивание потенциальных секретов, что остаётся локальной оговоркой. |
| backend-middle-programming-1-v1 | MIDDLE | PROGRAMMING | BASIC | MINOR | untouched | new | WEAK_DISTRACTORS | Несколько отвлекающих объяснений технически малоправдоподобны. Базовый вопрос относительно Middle допустим. |
| backend-middle-programming-4-v1 | MIDDLE | PROGRAMMING | APPLIED | MINOR | untouched | persisting | WEAK_DISTRACTORS | Применение контракта коллекции допустимо для Middle; несколько отвлекающих подходов слишком слабы. Не установлено существенного нарушения уровня или однозначности оценивания. |
| backend-middle-databases-1-v1 | MIDDLE | DATABASES | BASIC | MINOR | untouched | new | WEAK_DISTRACTORS | Отвлекающие подходы слабо конкурируют с технически осмысленным выбором; базовая конкурентная проблема соответствует блоку. |
| backend-middle-databases-3-v1 | MIDDLE | DATABASES | APPLIED | MINOR | untouched | persisting | WEAK_DISTRACTORS | Есть явно нерелевантный отвлекающий подход; прикладной выбор по структуре запроса сохраняет предметную ценность. |
| backend-middle-databases-5-v1 | MIDDLE | DATABASES | ADVANCED | MINOR | untouched | persisting | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | Верхняя ступень блока компактна и облегчена отвлекающими подходами; сценарий конкуренции и восстановления всё же требует предметного знания. |
| backend-middle-architecture-1-v1 | MIDDLE | ARCHITECTURE | BASIC | MINOR | untouched | new | WEAK_DISTRACTORS | Ошибочные источники состояния слишком легко исключить; базовая архитектурная граница в блоке при этом допустима. |
| backend-middle-architecture-2-v1 | MIDDLE | ARCHITECTURE | APPLIED | MINOR | untouched | persisting | WEAK_DISTRACTORS | Некоторые отвлекающие подходы очевидно нарушают надёжность. Прикладная граница между устойчивыми компонентами остаётся предметно значимой. |
| backend-middle-architecture-4-v1 | MIDDLE | ARCHITECTURE | APPLIED | MINOR | untouched | persisting | WEAK_DISTRACTORS | Есть явно неполные отвлекающие подходы, поэтому выбор облегчается; вопрос не доказывает существенного нарушения измерения. |
| backend-middle-architecture-5-v1 | MIDDLE | ARCHITECTURE | ADVANCED | MINOR | untouched | persisting | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | Верхняя ступень блока имеет ограниченное взаимодействие условий и слабые альтернативы; устойчивый конкурентный инвариант остаётся проверяемым. |
| backend-middle-testing_security_debugging-1-v1 | MIDDLE | TESTING_SECURITY_DEBUGGING | BASIC | MINOR | untouched | new | WEAK_DISTRACTORS | Несколько отвлекающих подходов не являются достаточными проверками безопасности. Для BASIC относительно Middle это локальный недостаток. |
| backend-middle-testing_security_debugging-2-v1 | MIDDLE | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | untouched | persisting | WEAK_DISTRACTORS | Отвлекающие подходы упрощены и ограничивают различимость ответа; прикладная тема и единственный защищаемый выбор сохранены. |
| backend-senior-programming-1-v1 | SENIOR | PROGRAMMING | BASIC | MINOR | untouched | new | WEAK_DISTRACTORS | Альтернативы мало конкурируют с обоснованной политикой. Короткий BASIC проверяет допустимый фундамент системной перегрузки. |
| backend-senior-architecture-1-v1 | SENIOR | ARCHITECTURE | BASIC | MINOR | untouched | new | WEAK_DISTRACTORS | Отвлекающие обещания чрезмерны и облегчают выбор. Базовая системная граница соответствует Senior без требования сложного сценария. |
| backend-senior-architecture-2-v1 | SENIOR | ARCHITECTURE | APPLIED | MINOR | untouched | persisting | WEAK_DISTRACTORS | Прикладная проблема владения системно уместна, но отвлекающие подходы облегчают узнавание одного механизма. Это локальный недостаток, не доказанный провал уровня. |

## Full 75-question coverage register

| Current code | Version | Grade | Competency | Difficulty | Outcome | B2 source change | V2 slot outcome | V2 disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| backend-junior-programming-1-v1 | 1 | JUNIOR | PROGRAMMING | BASIC | OK | untouched | OK | unchangedOK |
| backend-junior-programming-2-v1 | 1 | JUNIOR | PROGRAMMING | APPLIED | OK | untouched | OK | unchangedOK |
| backend-junior-programming-3-v1 | 1 | JUNIOR | PROGRAMMING | APPLIED | OK | untouched | OK | unchangedOK |
| backend-junior-programming-4-v1 | 1 | JUNIOR | PROGRAMMING | APPLIED | OK | untouched | OK | unchangedOK |
| backend-junior-programming-5-v1 | 1 | JUNIOR | PROGRAMMING | ADVANCED | MINOR | untouched | OK | new |
| backend-junior-http_api-1-v1 | 1 | JUNIOR | HTTP_API | BASIC | OK | untouched | OK | unchangedOK |
| backend-junior-http_api-2-v1 | 1 | JUNIOR | HTTP_API | APPLIED | MINOR | untouched | MINOR | persisting |
| backend-junior-http_api-3-v1 | 1 | JUNIOR | HTTP_API | APPLIED | MINOR | untouched | OK | new |
| backend-junior-http_api-4-v1 | 1 | JUNIOR | HTTP_API | APPLIED | OK | untouched | OK | unchangedOK |
| backend-junior-http_api-5-v1 | 1 | JUNIOR | HTTP_API | ADVANCED | MINOR | untouched | OK | new |
| backend-junior-databases-1-v1 | 1 | JUNIOR | DATABASES | BASIC | OK | untouched | OK | unchangedOK |
| backend-junior-databases-2-v1 | 1 | JUNIOR | DATABASES | APPLIED | OK | untouched | OK | unchangedOK |
| backend-junior-databases-3-v1 | 1 | JUNIOR | DATABASES | APPLIED | OK | untouched | OK | unchangedOK |
| backend-junior-databases-4-v1 | 1 | JUNIOR | DATABASES | APPLIED | OK | untouched | OK | unchangedOK |
| backend-junior-databases-5-v1 | 1 | JUNIOR | DATABASES | ADVANCED | MINOR | untouched | OK | new |
| backend-junior-architecture-1-v2 | 2 | JUNIOR | ARCHITECTURE | BASIC | OK | untouched | OK | unchangedOK |
| backend-junior-architecture-2-v1 | 1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR | untouched | MINOR | persisting |
| backend-junior-architecture-3-v1 | 1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR | untouched | MINOR | persisting |
| backend-junior-architecture-4-v1 | 1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR | untouched | OK | new |
| backend-junior-architecture-5-v1 | 1 | JUNIOR | ARCHITECTURE | ADVANCED | MINOR | untouched | OK | new |
| backend-junior-testing_security_debugging-1-v1 | 1 | JUNIOR | TESTING_SECURITY_DEBUGGING | BASIC | OK | untouched | OK | unchangedOK |
| backend-junior-testing_security_debugging-2-v1 | 1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | OK | untouched | OK | unchangedOK |
| backend-junior-testing_security_debugging-3-v1 | 1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | untouched | MINOR | persisting |
| backend-junior-testing_security_debugging-4-v1 | 1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | untouched | MINOR | persisting |
| backend-junior-testing_security_debugging-5-v2 | 2 | JUNIOR | TESTING_SECURITY_DEBUGGING | ADVANCED | OK | untouched | OK | unchangedOK |
| backend-middle-programming-1-v1 | 1 | MIDDLE | PROGRAMMING | BASIC | MINOR | untouched | OK | new |
| backend-middle-programming-2-v2 | 2 | MIDDLE | PROGRAMMING | APPLIED | OK | untouched | OK | unchangedOK |
| backend-middle-programming-3-v2 | 2 | MIDDLE | PROGRAMMING | APPLIED | OK | untouched | OK | unchangedOK |
| backend-middle-programming-4-v1 | 1 | MIDDLE | PROGRAMMING | APPLIED | MINOR | untouched | MINOR | persisting |
| backend-middle-programming-5-v2 | 2 | MIDDLE | PROGRAMMING | ADVANCED | OK | untouched | OK | unchangedOK |
| backend-middle-http_api-1-v1 | 1 | MIDDLE | HTTP_API | BASIC | OK | untouched | OK | unchangedOK |
| backend-middle-http_api-2-v2 | 2 | MIDDLE | HTTP_API | APPLIED | OK | untouched | OK | unchangedOK |
| backend-middle-http_api-3-v2 | 2 | MIDDLE | HTTP_API | APPLIED | OK | untouched | OK | unchangedOK |
| backend-middle-http_api-4-v2 | 2 | MIDDLE | HTTP_API | APPLIED | OK | untouched | OK | unchangedOK |
| backend-middle-http_api-5-v2 | 2 | MIDDLE | HTTP_API | ADVANCED | OK | replacement | IMPORTANT | resolved |
| backend-middle-databases-1-v1 | 1 | MIDDLE | DATABASES | BASIC | MINOR | untouched | OK | new |
| backend-middle-databases-2-v2 | 2 | MIDDLE | DATABASES | APPLIED | OK | untouched | OK | unchangedOK |
| backend-middle-databases-3-v1 | 1 | MIDDLE | DATABASES | APPLIED | MINOR | untouched | MINOR | persisting |
| backend-middle-databases-4-v3 | 3 | MIDDLE | DATABASES | APPLIED | OK | replacement | IMPORTANT | resolved |
| backend-middle-databases-5-v1 | 1 | MIDDLE | DATABASES | ADVANCED | MINOR | untouched | MINOR | persisting |
| backend-middle-architecture-1-v1 | 1 | MIDDLE | ARCHITECTURE | BASIC | MINOR | untouched | OK | new |
| backend-middle-architecture-2-v1 | 1 | MIDDLE | ARCHITECTURE | APPLIED | MINOR | untouched | MINOR | persisting |
| backend-middle-architecture-3-v2 | 2 | MIDDLE | ARCHITECTURE | APPLIED | OK | untouched | OK | unchangedOK |
| backend-middle-architecture-4-v1 | 1 | MIDDLE | ARCHITECTURE | APPLIED | MINOR | untouched | MINOR | persisting |
| backend-middle-architecture-5-v1 | 1 | MIDDLE | ARCHITECTURE | ADVANCED | MINOR | untouched | MINOR | persisting |
| backend-middle-testing_security_debugging-1-v1 | 1 | MIDDLE | TESTING_SECURITY_DEBUGGING | BASIC | MINOR | untouched | OK | new |
| backend-middle-testing_security_debugging-2-v1 | 1 | MIDDLE | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | untouched | MINOR | persisting |
| backend-middle-testing_security_debugging-3-v2 | 2 | MIDDLE | TESTING_SECURITY_DEBUGGING | APPLIED | OK | untouched | OK | unchangedOK |
| backend-middle-testing_security_debugging-4-v2 | 2 | MIDDLE | TESTING_SECURITY_DEBUGGING | APPLIED | OK | untouched | OK | unchangedOK |
| backend-middle-testing_security_debugging-5-v2 | 2 | MIDDLE | TESTING_SECURITY_DEBUGGING | ADVANCED | OK | replacement | IMPORTANT | resolved |
| backend-senior-programming-1-v1 | 1 | SENIOR | PROGRAMMING | BASIC | MINOR | untouched | OK | new |
| backend-senior-programming-2-v2 | 2 | SENIOR | PROGRAMMING | APPLIED | OK | untouched | OK | unchangedOK |
| backend-senior-programming-3-v2 | 2 | SENIOR | PROGRAMMING | APPLIED | OK | untouched | OK | unchangedOK |
| backend-senior-programming-4-v2 | 2 | SENIOR | PROGRAMMING | APPLIED | OK | replacement | IMPORTANT | resolved |
| backend-senior-programming-5-v2 | 2 | SENIOR | PROGRAMMING | ADVANCED | OK | untouched | OK | unchangedOK |
| backend-senior-http_api-1-v2 | 2 | SENIOR | HTTP_API | BASIC | OK | untouched | OK | unchangedOK |
| backend-senior-http_api-2-v2 | 2 | SENIOR | HTTP_API | APPLIED | OK | untouched | OK | unchangedOK |
| backend-senior-http_api-3-v2 | 2 | SENIOR | HTTP_API | APPLIED | OK | untouched | OK | unchangedOK |
| backend-senior-http_api-4-v2 | 2 | SENIOR | HTTP_API | APPLIED | OK | untouched | OK | unchangedOK |
| backend-senior-http_api-5-v2 | 2 | SENIOR | HTTP_API | ADVANCED | OK | untouched | OK | unchangedOK |
| backend-senior-databases-1-v2 | 2 | SENIOR | DATABASES | BASIC | OK | untouched | OK | unchangedOK |
| backend-senior-databases-2-v2 | 2 | SENIOR | DATABASES | APPLIED | OK | replacement | IMPORTANT | resolved |
| backend-senior-databases-3-v2 | 2 | SENIOR | DATABASES | APPLIED | OK | untouched | OK | unchangedOK |
| backend-senior-databases-4-v2 | 2 | SENIOR | DATABASES | APPLIED | OK | replacement | IMPORTANT | resolved |
| backend-senior-databases-5-v2 | 2 | SENIOR | DATABASES | ADVANCED | OK | untouched | OK | unchangedOK |
| backend-senior-architecture-1-v1 | 1 | SENIOR | ARCHITECTURE | BASIC | MINOR | untouched | OK | new |
| backend-senior-architecture-2-v1 | 1 | SENIOR | ARCHITECTURE | APPLIED | MINOR | untouched | MINOR | persisting |
| backend-senior-architecture-3-v2 | 2 | SENIOR | ARCHITECTURE | APPLIED | OK | replacement | IMPORTANT | resolved |
| backend-senior-architecture-4-v3 | 3 | SENIOR | ARCHITECTURE | APPLIED | OK | untouched | OK | unchangedOK |
| backend-senior-architecture-5-v2 | 2 | SENIOR | ARCHITECTURE | ADVANCED | OK | replacement | IMPORTANT | resolved |
| backend-senior-testing_security_debugging-1-v2 | 2 | SENIOR | TESTING_SECURITY_DEBUGGING | BASIC | OK | untouched | OK | unchangedOK |
| backend-senior-testing_security_debugging-2-v2 | 2 | SENIOR | TESTING_SECURITY_DEBUGGING | APPLIED | OK | replacement | IMPORTANT | resolved |
| backend-senior-testing_security_debugging-3-v2 | 2 | SENIOR | TESTING_SECURITY_DEBUGGING | APPLIED | OK | replacement | IMPORTANT | resolved |
| backend-senior-testing_security_debugging-4-v2 | 2 | SENIOR | TESTING_SECURITY_DEBUGGING | APPLIED | OK | untouched | OK | unchangedOK |
| backend-senior-testing_security_debugging-5-v2 | 2 | SENIOR | TESTING_SECURITY_DEBUGGING | ADVANCED | OK | untouched | OK | unchangedOK |

## All 15 bucket reviews

| Grade | Competency | BASIC/APPLIED/ADVANCED | BLOCKER | IMPORTANT | MINOR | OK | Within-grade review |
| --- | --- | --- | --- | --- | --- | --- | --- |
| JUNIOR | PROGRAMMING | 1/3/1 | 0 | 0 | 1 | 4 | Стандартные локальные fundamentals развиваются до нескольких приоритетов; существенной инверсии сложности нет. Есть локальная слабость вариантов верхнего слота. |
| JUNIOR | HTTP_API | 1/3/1 | 0 | 0 | 3 | 2 | Fundamentals, локальная валидация и доверие к запросу переходят к браузерной security границе. Несколько наборов вариантов облегчены, grade сохраняется. |
| JUNIOR | DATABASES | 1/3/1 | 0 | 0 | 1 | 4 | Локальные инварианты, атомарность и поиск переходят к семантике соединения. Один набор вариантов локально ослаблен; равноправных ответов нет. |
| JUNIOR | ARCHITECTURE | 1/3/1 | 0 | 0 | 4 | 1 | Стандартные локальные boundaries и устойчивый повтор соответствуют Junior; четыре набора вариантов локально облегчены без требования системного ownership. |
| JUNIOR | TESTING_SECURITY_DEBUGGING | 1/3/1 | 0 | 0 | 2 | 3 | Защита, локальная регрессия и ошибки переходят к разбору диагностических фактов. Сохраняются два локальных замечания, ADVANCED содержательно отличается. |
| MIDDLE | PROGRAMMING | 1/3/1 | 0 | 0 | 2 | 3 | От базовой конкурентной семантики до управления потоками с конкретными лимитами. APPLIED/ADVANCED имеют компонентный demand; локальные слабости двух старых наборов не определяют весь блок. |
| MIDDLE | HTTP_API | 1/3/1 | 0 | 0 | 0 | 5 | Контракты, модель угроз и состояния дополнены содержательным взаимодействием условий в ADVANCED. Существенного нарушения progression не найдено. |
| MIDDLE | DATABASES | 1/3/1 | 0 | 0 | 3 | 2 | Применение измерений и конкурентных условий соответствует Middle. Уточнённый сценарий даёт достаточную concurrency границу; три старых набора имеют локальные слабости. |
| MIDDLE | ARCHITECTURE | 1/3/1 | 0 | 0 | 4 | 1 | Межкомпонентная согласованность, кеш и деградация соответствуют Middle. ADVANCED сохраняет ограниченный охват; слабости вариантов локальны. |
| MIDDLE | TESTING_SECURITY_DEBUGGING | 1/3/1 | 0 | 0 | 2 | 3 | От базового enforcement к выбору доказательств и диагностике; ADVANCED добавляет детерминированную конкуренцию и persisted evidence. Две локальные слабости старых вариантов. |
| SENIOR | PROGRAMMING | 1/3/1 | 0 | 0 | 1 | 4 | Системная перегрузка, владение, ресурсы, время и поколения создают содержательный Senior demand. Один BASIC набор локально слаб по альтернативам. |
| SENIOR | HTTP_API | 1/3/1 | 0 | 0 | 0 | 5 | Во всех слотах есть системные authority, routing, compatibility, trust либо lifecycle условия. BASIC допустим относительно Senior; строгая численная монотонность не предполагается. |
| SENIOR | DATABASES | 1/3/1 | 0 | 0 | 0 | 5 | Системные агрегатные инварианты, повторы, rollout, владение длительной работой и terminal конкуренция дают содержательную progression; значимых дефектов нет. |
| SENIOR | ARCHITECTURE | 1/3/1 | 0 | 0 | 2 | 3 | Границы компонентов, ownership, восстановление, история и согласованность развиваются до нескольких условий ADVANCED. Два локальных слабых набора сохраняют уместную предметную задачу. |
| SENIOR | TESTING_SECURITY_DEBUGGING | 1/3/1 | 0 | 0 | 0 | 5 | Security, observability и evidence отказов имеют системный demand во всех слотах. Новые APPLIED не ограничиваются локальной реакцией на rollback или общий риск. |

## Cross-grade progression and overlap

| Competency | Questions / alternatives | Safe review |
| --- | --- | --- |
| PROGRAMMING | 15 / 60 | Junior проверяет локальную семантику и ресурсы; Middle — ограниченные компоненты и потоки; Senior — восстановимое владение, операционные ресурсы, общий временной контракт и межпроцессные поколения. Общая SDK-тема не является near-duplicate при разных существенных ограничениях. |
| HTTP_API | 15 / 60 | Junior fundamentals и локальное доверие переходят к Middle контрактам и threat model, затем к Senior системным authority, региональным мутациям, rollout и trust. Новый Middle ADVANCED содержательно соответствует своему месту; старое тройное когнитивное перекрытие не сохраняется. |
| DATABASES | 15 / 60 | Junior локальные инварианты и запросы переходят к Middle измеренному и конкурентному применению, затем к Senior агрегатам, rollout, внешним последствиям и terminal конкуренции. Старое перекрытие Middle BASIC и Senior ADVANCED устранено; локальные слабости отдельно отмечены. |
| ARCHITECTURE | 15 / 60 | Junior стандартные локальные boundaries переходят к Middle межкомпонентной надёжности, затем к Senior владению, автономному восстановлению и согласованности исторических условий. Общая тема повтора не доказывает duplicate. |
| TESTING_SECURITY_DEBUGGING | 15 / 60 | Junior защищает локальное поведение; Middle выбирает доказательства enforcement, диагностики и воспроизводимой конкуренции; Senior оценивает системные trust, наблюдения и неопределённые интервалы отказов. BASIC относительно grade и не требует той же длины, что ADVANCED. |

- **resolved_previous_overlap**: `backend-junior-architecture-5-v1` ↔ `backend-middle-http_api-4-v2` ↔ `backend-senior-http_api-1-v2`. Проверены все текущие вопросы и альтернативы. Различаются локальный повтор, контракт действий клиента и оценка достоверности системного результата; прежнее когнитивное совпадение не сохраняется.
- **resolved_previous_overlap**: `backend-middle-databases-1-v1` ↔ `backend-senior-databases-5-v2`. Локальный конкурентный конфликт и системный terminal инвариант с разными намерениями, повторами и отказом требуют различного суждения.
- **acceptable_thematic_overlap**: `backend-middle-programming-2-v2` ↔ `backend-middle-programming-5-v2` ↔ `backend-senior-programming-4-v2`. Общие темы ёмкости, отмены и времени не создают near-duplicate: состав существенных ограничений, компонентный контекст и системный временной контракт различаются.
- **acceptable_cross_competency_overlap**: `backend-junior-databases-3-v1` ↔ `backend-senior-testing_security_debugging-2-v2` ↔ `backend-senior-databases-2-v2`. Общая тема атомарности и повторов различает локальный инвариант, систему доказательств и границу повторного исполнения. Совпадение терминов не объявляется duplicate.
- **acceptable_thematic_overlap**: `backend-middle-architecture-2-v1` ↔ `backend-middle-architecture-5-v1` ↔ `backend-senior-architecture-3-v2`. При общей event-теме различаются межкомпонентный разрыв, отдельный устойчивый инвариант и восстановление упорядоченной проекции. Локальные слабости старых вопросов учтены отдельно.

No exact duplicate or new near-duplicate finding was established. Shared technical topics alone were not classified as duplicates. This qualitative comparison does not assert empirically equal scales across grades.

## P3-B2 regression checkpoint

Before C2, targeted SQLite verification ran from `backend/`:

```text
../.venv/bin/python -m pytest -q tests/test_assessment_bank_remediation.py tests/test_assessment_validation.py tests/test_assessments.py tests/test_candidate_assessments.py
216 passed / 0 failed / 1 skipped / 5 warnings
```

At the pre-C2 checkpoint the remediation module contained **59 cases**; the later diagnostic regression brings the final module to **60**. The skip is the PostgreSQL-only concurrent row-locking case; warnings are the existing Starlette/httpx notice and four SQLite datetime-adapter deprecations. Targeted Ruff check/format and `git diff --check` passed. These focused results do not substitute for the full P3-D gate.

Tests preserve first-pass guarantees, assert the exact B2 map, 65 unchanged records, literal fixture hashes, metadata, versions, source shape and zero structural findings. They cover fresh/repeated final seed; persisted B1→B2 and pre-P3→B1→B2 paths; old question/option IDs and content; both v2→v3 chains; rejected same-code changes; and ten completed/IN_PROGRESS API attempt cases spanning both seed phases. All three Middle and all seven Senior B2 predecessors are selected explicitly in the second-phase historical cases.

Physical history expectations are **75→102→112 questions / 300→408→448 options** for the complete persisted path, and **75→85 questions / 300→340 options** for B1→B2. The final active current set is always 75. Runtime seed behavior remains immediate-predecessor only: persistent deployments must apply the published B1 source before B2; a fresh database may contain only current v3 records. No transitive supersedes behavior is introduced.

## Technical verification and final readiness

**P3-D TECHNICAL GATE PASSED.** Content was not edited after C2. Final test-only diagnostic protection is committed separately as `8cec60fc796ccb93a497ff38e0fcc690c000adfa`; this adds one regression case and changes test representations/assertion diagnostics without changing loader, question data or assessment behavior. Full backend checks below ran against that exact test content in the built Python 3.13 image.

Technical evidence checkpoint UTC: **2026-10-07T21:01:09Z**. This is separate from the frozen content-review timestamp above.

The dedicated Docker project `fsp-p3-remediation` uses synthetic development configuration outside the repository and ports 55449/18049/13049. It was reset with the scoped equivalent of `docker compose down -v`, then started using `docker compose up --build -d --wait --wait-timeout 240`. PostgreSQL was **17.11**; PostgreSQL/backend/frontend were all healthy. The actual migrations ran before backend startup. After the diagnostic test change the backend image was rebuilt; all final backend checks were rerun.

| Check | Actual result |
| --- | --- |
| Full SQLite `python -m pytest -q -rs` | **569 passed / 0 failed / 7 skipped / 5 warnings**, 53.29 s |
| Full PostgreSQL 17.11 `python -m pytest -q -rs` | **576 passed / 0 failed / 0 skipped / 1 warning**, 67.70 s |
| Explicit persistent upgrade/history rerun | **13 passed / 0 failed / 47 deselected / 1 warning**, 2.76 s |
| Structural validator in runtime | **0 findings**, 75 records / 300 alternatives / versions 38/35/2 |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS, 46 files |
| `python -m mypy app` | PASS, 29 source files |
| `python -m alembic heads` | `fbce7259afda` — single head |
| `python -m alembic current` | `fbce7259afda` — head |
| `python -m alembic check` | PASS, no new upgrade operations; repeated after runtime seed |
| Host frontend `npm run lint` / `npm run typecheck` / `npm run build` | PASS, no warnings; Node 26.5.1, existing dependencies |
| Host frontend `npm test` | **93 passed / 0 failed / 0 skipped**, no warnings |
| Docker frontend build/runtime | Existing Node 22 build image, healthy; frontend API proxy returned HTTP 200 |
| `git diff --check` | PASS |

Test processes used `APP_ENV=test`, `FRONTEND_URL=http://localhost:3000` and `ALLOWED_ORIGINS=["http://localhost:3000"]`, matching fixture/CI origins. SQLite used an empty `TEST_DATABASE_URL`; PostgreSQL used the dedicated PostgreSQL URL and existing per-test UUID schemas. No test schema touched the runtime public seed data.

Initial full-suite commands incorrectly inherited the isolated runtime origin 13049: SQLite reported 300 passed / 168 failed / 104 errors / 3 skipped / 5 warnings; PostgreSQL reported 301 passed / 170 failed / 104 errors / 0 skipped / 1 warning. The failed setup requests returned `403 untrusted_origin`. Existing settings consume the inherited origin environment; resetting only test-command origins to the CI values made the auth smoke pass (21 passed / 1 SQLite-only skip), then both full suites passed. No application change was made for this invocation/configuration error. The final counts above supersede those initial runs and are not inferred from them.

The seven SQLite skips require PostgreSQL concurrency/row locks or its NaN constraint behavior: one assessment-start case, one token-consumption case, one employer-need concurrency case, one infrastructure NaN case, and three Matching concurrency cases. All ran on PostgreSQL. SQLite warnings are the existing Starlette/httpx notice plus four datetime-adapter deprecations; PostgreSQL has only the existing Starlette/httpx notice. Dependencies were not changed to silence warnings.

All five literal golden cases and the canonical/lifecycle tests passed in the full matrix:

| Case | Frozen outcome verified |
| --- | --- |
| G1 — 14/20, all competencies ≥50% | PASS, 70 |
| G2 — 16/20, one competency 25% | FAIL, 80 |
| G3 — 13/20, all competencies ≥50% | FAIL, 65 |
| G4 — 20/20 | PASS, 100 |
| G5 — 0/20 | FAIL, 0 |

Existing tests also passed for failed higher-grade preservation, successful/failed same-grade retakes, specialization restoration, exact timeouts, cooldowns, immutable attempts and candidate API privacy. No scoring, threshold or lifecycle contract was altered.

### Persistent version/history evidence

The explicit PostgreSQL rerun used `tests/test_assessment_bank_remediation.py -k 'baseline_upgrade_keeps or second_upgrade_preserves or attempt_keeps_historical'`. It includes pre-P3→B1, B1→B2, complete pre-P3→B1→B2, and ten completed/active API cases. Each path uses the actual existing runtime seed across committed DB sessions, fixed original/B1 fixtures and final runtime B2 source. It proves retained IDs/content/options/membership/order, inactive immediate predecessors, active final versions, 75 current active questions, and repeated seed stability. Physical counts are 75→102→112 questions and 300→408→448 options for the full path, and 75→85 / 300→340 for B1→B2.

Both required chains passed explicitly: `backend-senior-architecture-4-v2→v3` and `backend-middle-databases-4-v2→v3`. Historical Middle v1 and v2 remain intact; seed only changes the explicit immediate predecessor's active flag. Ten API cases retain completed and IN_PROGRESS attempts across the upgrades; all ten B2 predecessors are deliberately selected across the Middle/Senior cases. Old saved option order and scoring remain stable. This is a faithful persistent PostgreSQL path, not an assertion of unsupported transitive upgrades.

### Fresh Docker seed modes

Existing `python -m app.seed`, `python -m app.seed --demo`, and `python -m app.seed --matching-demo` each ran twice. READ ONLY snapshots of every column/row in every public table were compared through opaque SHA256 values; each complete snapshot was identical on repeat. No keys/options/PII were printed by the evidence collection.

| Mode | Questions / options | Active versions v1/v2/v3 | Users / candidate profiles / employer profiles / Needs | Repeat |
| --- | --- | --- | --- | --- |
| base | 75 / 300, all 75 active | 38/35/2 | 0 / 0 / 0 / 0 | identical all-table snapshot |
| --demo | 75 / 300, all 75 active | 38/35/2 | 2 / 1 / 1 / 0 | identical all-table snapshot |
| --matching-demo | 75 / 300, all 75 active | 38/35/2 | 11 / 10 / 1 / 3 | identical all-table snapshot |

This preserves existing seed modes; no P3-only seed mode or transitive deactivation was introduced. Fresh mode data and persisted upgrade data are deliberately distinct evidence: a fresh database has only current question versions, while the upgrade tests retain published historical rows.

### Final diff and diagnostic review

The entire branch was reviewed against `f6ac399bd84f7379cb957d2c8f4b4c1fc31d5193`; freshly fetched `origin/main` still equals that SHA. Production scope is the question JSON only. Expected accompanying files are the remediation test module, its exact pre-P3/B1 fixtures, the validation inventory assertions, and P3-A/v2/v3 documents. The previous design and audit documents remain byte-identical. All 65 B1 non-target records remain exact, including the 13 previous MINOR and 26 clean B1 replacements. No O2 branch was integrated.

The new remediation assertions compare precomputed digests, including fixture-byte hashes and historical API comparisons. A temporary test-only `SeedQuestion.__repr__` contains only safe code/version metadata and is restored after each test. A regression checks actual B1/current-bank list/dict representations for private text; separate synthetic pytest rewritten failures verified metadata, membership and digest diagnostics with default argument rendering. Source/model/loader behavior is unchanged.

A separate pre-existing limitation remains in `test_assessment_validation.py`: nested fingerprint assertions and raw fixture representations can expose fixture content if those tests fail. This P3 change does not claim general backend failure-output sanitization; those old diagnostics were not broadened or cleaned outside this local remediation scope. The full suites passed, so no such output occurred in the final evidence. No production API leak or runtime engine defect was found.

The content/technical prerequisites authorize PR creation and checking actual CI; this document does not predeclare CI success or authorize merge.

## Scope and limitations

Production changes remain limited to `backend/app/content/backend_questions.json`. Tests/fixtures and the three P3 provenance documents accompany it. Assessment Engine, scoring, thresholds, cooldowns, qualification/canonical state, timeouts, selection/shuffle, seed implementation, APIs, frontend, Matching, Invitations, FSP, migrations, dependencies and CI are unchanged. No O2 integration, direct main mutation or merge occurred.

The following limits describe the independent content review at its frozen timestamp. The implementation author's separate P3-D results are recorded above; the auditor did not claim or run those technical checks.

- Качественный экспертный content review; нет эмпирических данных о сложности, discrimination, reliability или результатах найма.
- В рамках независимого content audit live DB, candidate API и визуальное runtime поведение не проверялись. Отдельные DB/API privacy и полный P3-D проверки затем прошли, как зафиксировано выше; visual browser smoke в этой задаче не выполнялся.
- Все 75 current records и 300 alternatives просмотрены; текущий source не является инвентарём физических исторических DB rows.
- Первичный независимый реестр был 22 MINOR; сверка той же rubric добавила три сохраняющихся локальных причины и уточнила две категории без повышения severity.
- Ограничение последующей независимости: краткая pre-freeze заметка непреднамеренно получена через list_agents после полного первичного реестра.
- Независимый аудитор не изменял production, tests или документацию репозитория, не запускал tests и не делал commit/push/PR. Реализация и отдельный P3-D evidence принадлежат implementation phase.

The auditor performed a read-only content review; implementation/technical evidence is separately identified. Expert content review provides no empirical discrimination, reliability, psychometric calibration or hiring-success evidence.
