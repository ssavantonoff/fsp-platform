# Assessment bank — full content audit v2

## Decision and frozen source

Content readiness: **NOT_READY**. **STOP FOR HUMAN REVIEW**: the full re-audit found IMPORTANT content findings. P3-D final gate and PR creation are not authorized by this result. No second content pass has been performed.

- Branch: `feat/assessment-bank-remediation`.
- Original main/base: `f6ac399bd84f7379cb957d2c8f4b4c1fc31d5193`.
- Starting approved P3-A HEAD: `1d8e01b7a6c21138075bda3cbb3e49f6b2899198`.
- Exact reviewed source/test HEAD: `8b6ceb5c6df2e9043c5263ef3ff8355eac4b292e`.
- Audit snapshot UTC: `2026-10-07T19:47:02.502588Z`.
- Current source SHA256: `079e40829c0ac41e8c893971f0b0d586ae7a071bf14d9d2a486466159ad4b30a`.
- Current source: `backend/app/content/backend_questions.json`.
- Baseline source SHA256: `7d2c7f2db8a7986d3027e250ac47786e700e4babf0c80e7c46ce6fce34442096`.
- Provenance: [original audit](assessment-bank-audit-draft.md), [approved P3-A design](assessment-bank-remediation-plan.md). Both documents are unchanged.

The reviewed source was frozen before the independent audit. This report records that snapshot; no bank content was changed after review began. The coverage register below identifies every current code and version. It describes current JSON records, not physical historical DB rows.

## Method and rubric

Сначала прочитаны все 75 stems и все 300 альтернатив текущего source и зафиксированы первичные суждения без authoring reasoning. Затем прочитан baseline для сравнения и согласования явных severity rules. Authoring plan/reasoning и утверждения автора не использовались как доказательство.

Reviewed **75 stems and all 300 alternatives** privately. The independent reviewer used a separate context. The implementation author checked artifact/source identity, metadata, counts, coverage and safe reporting; the author did not replace the reviewer’s classifications with target counts.

Each question was reviewed against the same 16 criteria: Backend specialization, grade fit, difficulty fit, competency fit, single most defensible answer, multiple reasonable answers, wording ambiguity, missing decisive context, trivia, version specificity, engineering reasoning versus wording guess, answer leakage, distractor quality, near-duplicates, difficulty within grade, and cross-grade rubric progression. All 15 buckets and five same-competency cross-grade sets were reviewed, including unaffected source buckets and all 25 Senior questions.

| Grade | Frozen review expectation |
| --- | --- |
| JUNIOR | Фундамент и стандартные локальные задачи без architecture ownership. |
| MIDDLE | Применение, компоненты, контракты, транзакции, debugging/performance и trade-offs; APPLIED требует конкретных ограничений и правдоподобных стратегий. |
| SENIOR | Системное суждение об authority, ownership, failure, concurrency, consistency, rollout, compatibility, security, observability и operations. |

BASIC относительно grade; короткий BASIC не является самостоятельным дефектом. ADVANCED включает несколько interacting constraints. Сложная тема не доказывает Senior demand; математический межуровневый порядок difficulty не предполагается.

- **BLOCKER:** no defensible unique scoring, or missing decisive context can change the correct answer.
- **IMPORTANT:** a likely best answer exists, but the item materially weakens measurement of its grade/difficulty/competency.
- **MINOR:** a localized issue without established scoring failure or major measurement weakness.
- **OK:** this qualitative pass found no finding; it is not certification.
- One question is counted once at its highest severity. Categories do not add to the count.

При прочитанном контексте у всех вопросов различим один наиболее защищаемый выбор. Равноправных разумных альтернатив или доказанного неверного ключа не выявлено. Оговорка одного concurrency-сценария не доказывает scoring BLOCKER, но требует human review как IMPORTANT.

Primary sources used for factual context: [RFC 9111 HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111.html), [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html), [PostgreSQL 17 Transaction Isolation](https://www.postgresql.org/docs/17/transaction-iso.html), [PostgreSQL 17 SELECT](https://www.postgresql.org/docs/17/sql-select.html), [Python 3.13 asyncio tasks](https://docs.python.org/3.13/library/asyncio-task.html). These references validate technical premises and do not define product rules, calibrate grades or publish solutions. The PostgreSQL concurrency qualification is based on the declared PostgreSQL 17 isolation context.

This report contains codes, metadata, categories and safe reasons. It contains no question/alternative texts, answer keys, correct positions, source ordering convention or solutions. API privacy/runtime verification is outside this content-only pass; APIs were not changed.

## Inventory and actual audit counts

P3-B applied exactly **27** approved replacements: **1 JUNIOR / 11 MIDDLE / 15 SENIOR**; **26 v1→v2 / 1 v2→v3**. Current JSON has **75 records**, **25 per grade**, and versions **47 v1 / 27 v2 / 1 v3**. All 48 non-target records, including the six original MINOR records, remain content-equivalent to the fixed baseline. All replacement grade/competency/difficulty metadata is preserved.

| Outcome | Baseline | Post-remediation |
| --- | --- | --- |
| BLOCKER | 0 | 0 |
| IMPORTANT | 27 | 10 |
| MINOR | 6 | 13 |
| OK | 42 | 52 |

Total reviewed: **75** in each audit. Current flagged count: **23**. Target 0 IMPORTANT was not achieved; it was not used as a predetermined result.

| Grade | BLOCKER | IMPORTANT | MINOR | OK | Reviewed |
| --- | --- | --- | --- | --- | --- |
| JUNIOR | 0 | 0 | 5 | 20 | 25 |
| MIDDLE | 0 | 3 | 7 | 15 | 25 |
| SENIOR | 0 | 7 | 1 | 17 | 25 |

## Baseline dispositions

The slot comparison partitions all 75 current questions: **26 resolved flagged slots / 7 still-flagged baseline slots / 16 newly flagged prior-OK slots / 26 unchanged OK slots**. “Still flagged” tracks the current slot, not an assertion that every old category persists.

- Among the 27 approved replacement slots, **26 are OK**. `backend-middle-databases-4-v2` remains IMPORTANT at slot level: the original recognition/weak-distractor measurement reasons were resolved, but a **new CONTEXT_DEPENDENT** reason was found. It is not counted as a clean remediation.
- All six original MINOR records were re-reviewed. Five remain MINOR; `backend-senior-testing_security_debugging-3-v1` is now IMPORTANT. Its old context qualification persists and new grade/distractor reasons were found.
- Among the 42 original OK records, **8 are now IMPORTANT, 8 are now MINOR, and 26 remain OK**. These are new audit findings on untouched content, not newly introduced source changes.
- `backend-junior-testing_security_debugging-4-v1` retains MINOR and also has a new localized `OTHER` qualification. It remains one flagged question, not an additional count.
- No original audit finding was edited retrospectively. The fresh final bank review, including within-grade and cross-grade comparisons, supports the changed classifications below under the same severity rubric.

| Baseline replacement code | Current code | Current outcome |
| --- | --- | --- |
| backend-junior-testing_security_debugging-5-v1 | backend-junior-testing_security_debugging-5-v2 | OK |
| backend-middle-programming-2-v1 | backend-middle-programming-2-v2 | OK |
| backend-middle-programming-3-v1 | backend-middle-programming-3-v2 | OK |
| backend-middle-programming-5-v1 | backend-middle-programming-5-v2 | OK |
| backend-middle-http_api-2-v1 | backend-middle-http_api-2-v2 | OK |
| backend-middle-http_api-3-v1 | backend-middle-http_api-3-v2 | OK |
| backend-middle-http_api-4-v1 | backend-middle-http_api-4-v2 | OK |
| backend-middle-databases-2-v1 | backend-middle-databases-2-v2 | OK |
| backend-middle-databases-4-v1 | backend-middle-databases-4-v2 | IMPORTANT |
| backend-middle-architecture-3-v1 | backend-middle-architecture-3-v2 | OK |
| backend-middle-testing_security_debugging-3-v1 | backend-middle-testing_security_debugging-3-v2 | OK |
| backend-middle-testing_security_debugging-4-v1 | backend-middle-testing_security_debugging-4-v2 | OK |
| backend-senior-programming-2-v1 | backend-senior-programming-2-v2 | OK |
| backend-senior-programming-3-v1 | backend-senior-programming-3-v2 | OK |
| backend-senior-programming-5-v1 | backend-senior-programming-5-v2 | OK |
| backend-senior-http_api-1-v1 | backend-senior-http_api-1-v2 | OK |
| backend-senior-http_api-2-v1 | backend-senior-http_api-2-v2 | OK |
| backend-senior-http_api-3-v1 | backend-senior-http_api-3-v2 | OK |
| backend-senior-http_api-4-v1 | backend-senior-http_api-4-v2 | OK |
| backend-senior-http_api-5-v1 | backend-senior-http_api-5-v2 | OK |
| backend-senior-databases-1-v1 | backend-senior-databases-1-v2 | OK |
| backend-senior-databases-3-v1 | backend-senior-databases-3-v2 | OK |
| backend-senior-databases-5-v1 | backend-senior-databases-5-v2 | OK |
| backend-senior-architecture-4-v2 | backend-senior-architecture-4-v3 | OK |
| backend-senior-testing_security_debugging-1-v1 | backend-senior-testing_security_debugging-1-v2 | OK |
| backend-senior-testing_security_debugging-4-v1 | backend-senior-testing_security_debugging-4-v2 | OK |
| backend-senior-testing_security_debugging-5-v1 | backend-senior-testing_security_debugging-5-v2 | OK |

## Current IMPORTANT findings — STOP gate

| Code | Grade | Competency | Difficulty | Severity | Source change | Disposition | Categories | Safe reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| backend-middle-http_api-5-v1 | MIDDLE | HTTP_API | ADVANCED | IMPORTANT | untouched | new; baseline OK | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | ADVANCED: сценарий сводится к распознаванию стандартного способа пагинации. Альтернативы не предлагают правдоподобных стратегий работы с меняющимся списком; взаимодействующие ограничения и их последствия практически не проверяются. |
| backend-middle-databases-4-v2 | MIDDLE | DATABASES | APPLIED | IMPORTANT | replacement | persisting slot; new context reason | CONTEXT_DEPENDENT | При заявленном уровне изоляции конкурентная запись возможна между чтением версии и сохранением; общая транзакция сама это окно не исключает. Формулировка оставляет связь проверки с мутацией неявной. Наиболее вероятный замысел различим и допускает корректную реализацию, поэтому scoring BLOCKER не доказан, но существенная concurrency-гарантия требует неоговорённого допущения. |
| backend-middle-testing_security_debugging-5-v1 | MIDDLE | TESTING_SECURITY_DEBUGGING | ADVANCED | IMPORTANT | untouched | new; baseline OK | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | ADVANCED Middle сводится к распознаванию того, что конкурентный инвариант надо проверять конкурентным сценарием. Три альтернативы фактически не воспроизводят поставленную конкуренцию; выбор между правдоподобными стратегиями проверки и взаимодействующими условиями отсутствует. |
| backend-senior-programming-4-v1 | SENIOR | PROGRAMMING | APPLIED | IMPORTANT | untouched | new; baseline OK | GRADE_TOO_EASY, DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | APPLIED Senior сводится к одному универсальному правилу управления временем. Другие варианты не являются правдоподобными инженерными стратегиями, а системные последствия и взаимодействующие ограничения отсутствуют; текущие Middle-вопросы по этой теме требуют существенно большего анализа. |
| backend-senior-databases-2-v1 | SENIOR | DATABASES | APPLIED | IMPORTANT | untouched | new; baseline OK | GRADE_TOO_EASY, WEAK_DISTRACTORS | APPLIED Senior проверяет стандартную реакцию на известную ошибку транзакции. Три альтернативы заведомо неработоспособны, а конкретного выбора по внешним эффектам, конфликтам или восстановлению нет; названия уровня изоляции недостаточно для Senior demand. |
| backend-senior-databases-4-v1 | SENIOR | DATABASES | APPLIED | IMPORTANT | untouched | new; baseline OK | GRADE_TOO_EASY, DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | APPLIED Senior фактически просит определить назначение одной SQL-конструкции. Альтернативы содержат очевидно чрезмерные гарантии, а реальные ограничения владения заданиями, повторов и восстановления не входят в выбор. |
| backend-senior-architecture-3-v1 | SENIOR | ARCHITECTURE | APPLIED | IMPORTANT | untouched | new; baseline OK | GRADE_TOO_EASY, WEAK_DISTRACTORS | В сценарии названы две проблемы доставки, но альтернативы сводят выбор к общей осторожной формулировке без конкретной стратегии обработки. Контекст и варианты не позволяют проверить заявленное системное суждение APPLIED Senior. |
| backend-senior-architecture-5-v1 | SENIOR | ARCHITECTURE | ADVANCED | IMPORTANT | untouched | new; baseline OK | GRADE_TOO_EASY, DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | ADVANCED Senior проверяет узнавание стандартной политики согласованного чтения. Варианты почти устраняют содержательный выбор; отсутствуют взаимодействующие требования, по которым нужно было бы оценить системные последствия стратегии. |
| backend-senior-testing_security_debugging-2-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | APPLIED | IMPORTANT | untouched | new; baseline OK | GRADE_TOO_EASY, WEAK_DISTRACTORS | APPLIED Senior проверяет базовый сценарий тестирования локальной транзакционной атомарности. Остальные варианты не дают содержательных доказательств вообще; нет системных условий отказа, из-за которых инженер должен выбирать между правдоподобными проверками. |
| backend-senior-testing_security_debugging-3-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | APPLIED | IMPORTANT | untouched | persisting context; new grade/distractor reasons; MINOR→IMPORTANT | GRADE_TOO_EASY, WEAK_DISTRACTORS, CONTEXT_DEPENDENT | APPLIED Senior сводится к распознаванию общеизвестного риска общего кеша. Конкретная граница проверки доступа и выдачи данных не задана, а альтернативы не представляют правдоподобных вариантов оценки системного риска. |

The concurrency finding describes an underspecified guarantee, not a proven equal alternative or incorrect scoring key. Its highest supported severity in this review is IMPORTANT. The primary-source premise is that the stated isolation does not by itself make all reads and later writes observe an unchanged state; see [PostgreSQL 17 transaction isolation](https://www.postgresql.org/docs/17/transaction-iso.html). Human review must decide whether and how to authorize a new versioned pass.

## Current MINOR findings

| Code | Grade | Competency | Difficulty | Severity | Disposition | Categories | Safe reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| backend-junior-http_api-2-v1 | JUNIOR | HTTP_API | APPLIED | MINOR | persisting MINOR | WEAK_DISTRACTORS | Контекст входной валидации достаточно определён и подходит Junior APPLIED, но несколько альтернатив слабо отражают реальные ошибки начинающего. Это локальное ослабление дистракторов без неоднозначного скоринга. |
| backend-junior-architecture-2-v1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR | persisting MINOR | WEAK_DISTRACTORS | Локальная задача ограничения ожидания подходит Junior APPLIED. Часть альтернатив не связана с причиной зависания и почти не конкурирует с защищаемым подходом; слабость ограничена качеством дистракторов. |
| backend-junior-architecture-3-v1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR | persisting MINOR | WEAK_DISTRACTORS | Задача изоляции расчёта от внешнего сервиса соответствует Junior. Несколько альтернатив почти не исследуют эту связь, поэтому локально облегчают выбор без нарушения уникальности оценки. |
| backend-junior-testing_security_debugging-3-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | persisting MINOR | WEAK_DISTRACTORS | Junior-сценарий регрессии и отсутствия побочной мутации корректен. Часть альтернатив вообще не проверяет описанное поведение и слабо различает знание тестовой практики. |
| backend-junior-testing_security_debugging-4-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | persisting MINOR | WEAK_DISTRACTORS, OTHER | Junior-сценарий обращения с ошибкой сохраняет однозначный защищаемый выбор, но несколько альтернатив содержат очевидные нарушения. Есть локальная оговорка о диагностических подробностях: в условии они могут включать секреты, а требования к их обезличиванию не сформулированы. |
| backend-middle-programming-4-v1 | MIDDLE | PROGRAMMING | APPLIED | MINOR | new; baseline OK | WEAK_DISTRACTORS | Сценарий применения контракта коллекции соответствует Middle, но несколько альтернатив слишком слабы и облегчают исключение вариантов. Содержательная ошибка скоринга не выявлена. |
| backend-middle-databases-3-v1 | MIDDLE | DATABASES | APPLIED | MINOR | new; baseline OK | WEAK_DISTRACTORS | Фильтр и порядок достаточно определены для выбора, но часть альтернатив не связана с запросом и слабо различает компетенцию. Это локальное ослабление дистракторов. |
| backend-middle-databases-5-v1 | MIDDLE | DATABASES | ADVANCED | MINOR | new; baseline OK | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | Типовой практический deadlock-сценарий корректен, но для ADVANCED варианты дают ограниченную проверку выбора стратегии. Основное взаимодействие блокировок и повторного исполнения сохраняется. |
| backend-middle-architecture-2-v1 | MIDDLE | ARCHITECTURE | APPLIED | MINOR | new; baseline OK | WEAK_DISTRACTORS | Практический разрыв между сохранением и публикацией измеряется, но часть альтернатив заведомо противоречит исходной проблеме. Выбор остаётся однозначным; качество отдельных дистракторов ограничено. |
| backend-middle-architecture-4-v1 | MIDDLE | ARCHITECTURE | APPLIED | MINOR | new; baseline OK | WEAK_DISTRACTORS | Практическая задача соответствует компетенции, но конкурентная часть обозначена общей оговоркой и не раскрывается в вариантах. Это локальное ослабление APPLIED-сценария без доказанного scoring failure. |
| backend-middle-architecture-5-v1 | MIDDLE | ARCHITECTURE | ADVANCED | MINOR | new; baseline OK | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | Практическая атомарность обработки дубля измеряется, но альтернативы дают ограниченную проверку ADVANCED-выбора и почти не различают правдоподобные варианты реализации. |
| backend-middle-testing_security_debugging-2-v1 | MIDDLE | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | new; baseline OK | WEAK_DISTRACTORS | Сценарий входящего URL соответствует Backend/Middle; часть неверных альтернатив слишком явно недостаточна. Локальное качество дистракторов слабее, чем конкретность проверяемой задачи. |
| backend-senior-architecture-2-v1 | SENIOR | ARCHITECTURE | APPLIED | MINOR | new; baseline OK | WEAK_DISTRACTORS | Сценарий действительно затрагивает смену владельца и границу хранилища, поэтому соответствует Senior APPLIED. Некоторые альтернативы заметно слабее наиболее серьёзной ошибки границы доверия. |

## Full 75-question coverage register

All current stems and all four alternatives were inspected. This register reports maximum severity only; OK does not imply psychometric or hiring validity.

| Current code | Version | Grade | Competency | Difficulty | Outcome | Source change | Baseline slot outcome |
| --- | --- | --- | --- | --- | --- | --- | --- |
| backend-junior-programming-1-v1 | 1 | JUNIOR | PROGRAMMING | BASIC | OK | untouched | OK |
| backend-junior-programming-2-v1 | 1 | JUNIOR | PROGRAMMING | APPLIED | OK | untouched | OK |
| backend-junior-programming-3-v1 | 1 | JUNIOR | PROGRAMMING | APPLIED | OK | untouched | OK |
| backend-junior-programming-4-v1 | 1 | JUNIOR | PROGRAMMING | APPLIED | OK | untouched | OK |
| backend-junior-programming-5-v1 | 1 | JUNIOR | PROGRAMMING | ADVANCED | OK | untouched | OK |
| backend-junior-http_api-1-v1 | 1 | JUNIOR | HTTP_API | BASIC | OK | untouched | OK |
| backend-junior-http_api-2-v1 | 1 | JUNIOR | HTTP_API | APPLIED | MINOR | untouched | MINOR |
| backend-junior-http_api-3-v1 | 1 | JUNIOR | HTTP_API | APPLIED | OK | untouched | OK |
| backend-junior-http_api-4-v1 | 1 | JUNIOR | HTTP_API | APPLIED | OK | untouched | OK |
| backend-junior-http_api-5-v1 | 1 | JUNIOR | HTTP_API | ADVANCED | OK | untouched | OK |
| backend-junior-databases-1-v1 | 1 | JUNIOR | DATABASES | BASIC | OK | untouched | OK |
| backend-junior-databases-2-v1 | 1 | JUNIOR | DATABASES | APPLIED | OK | untouched | OK |
| backend-junior-databases-3-v1 | 1 | JUNIOR | DATABASES | APPLIED | OK | untouched | OK |
| backend-junior-databases-4-v1 | 1 | JUNIOR | DATABASES | APPLIED | OK | untouched | OK |
| backend-junior-databases-5-v1 | 1 | JUNIOR | DATABASES | ADVANCED | OK | untouched | OK |
| backend-junior-architecture-1-v2 | 2 | JUNIOR | ARCHITECTURE | BASIC | OK | untouched | OK |
| backend-junior-architecture-2-v1 | 1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR | untouched | MINOR |
| backend-junior-architecture-3-v1 | 1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR | untouched | MINOR |
| backend-junior-architecture-4-v1 | 1 | JUNIOR | ARCHITECTURE | APPLIED | OK | untouched | OK |
| backend-junior-architecture-5-v1 | 1 | JUNIOR | ARCHITECTURE | ADVANCED | OK | untouched | OK |
| backend-junior-testing_security_debugging-1-v1 | 1 | JUNIOR | TESTING_SECURITY_DEBUGGING | BASIC | OK | untouched | OK |
| backend-junior-testing_security_debugging-2-v1 | 1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | OK | untouched | OK |
| backend-junior-testing_security_debugging-3-v1 | 1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | untouched | MINOR |
| backend-junior-testing_security_debugging-4-v1 | 1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | untouched | MINOR |
| backend-junior-testing_security_debugging-5-v2 | 2 | JUNIOR | TESTING_SECURITY_DEBUGGING | ADVANCED | OK | replacement | IMPORTANT |
| backend-middle-programming-1-v1 | 1 | MIDDLE | PROGRAMMING | BASIC | OK | untouched | OK |
| backend-middle-programming-2-v2 | 2 | MIDDLE | PROGRAMMING | APPLIED | OK | replacement | IMPORTANT |
| backend-middle-programming-3-v2 | 2 | MIDDLE | PROGRAMMING | APPLIED | OK | replacement | IMPORTANT |
| backend-middle-programming-4-v1 | 1 | MIDDLE | PROGRAMMING | APPLIED | MINOR | untouched | OK |
| backend-middle-programming-5-v2 | 2 | MIDDLE | PROGRAMMING | ADVANCED | OK | replacement | IMPORTANT |
| backend-middle-http_api-1-v1 | 1 | MIDDLE | HTTP_API | BASIC | OK | untouched | OK |
| backend-middle-http_api-2-v2 | 2 | MIDDLE | HTTP_API | APPLIED | OK | replacement | IMPORTANT |
| backend-middle-http_api-3-v2 | 2 | MIDDLE | HTTP_API | APPLIED | OK | replacement | IMPORTANT |
| backend-middle-http_api-4-v2 | 2 | MIDDLE | HTTP_API | APPLIED | OK | replacement | IMPORTANT |
| backend-middle-http_api-5-v1 | 1 | MIDDLE | HTTP_API | ADVANCED | IMPORTANT | untouched | OK |
| backend-middle-databases-1-v1 | 1 | MIDDLE | DATABASES | BASIC | OK | untouched | OK |
| backend-middle-databases-2-v2 | 2 | MIDDLE | DATABASES | APPLIED | OK | replacement | IMPORTANT |
| backend-middle-databases-3-v1 | 1 | MIDDLE | DATABASES | APPLIED | MINOR | untouched | OK |
| backend-middle-databases-4-v2 | 2 | MIDDLE | DATABASES | APPLIED | IMPORTANT | replacement | IMPORTANT |
| backend-middle-databases-5-v1 | 1 | MIDDLE | DATABASES | ADVANCED | MINOR | untouched | OK |
| backend-middle-architecture-1-v1 | 1 | MIDDLE | ARCHITECTURE | BASIC | OK | untouched | OK |
| backend-middle-architecture-2-v1 | 1 | MIDDLE | ARCHITECTURE | APPLIED | MINOR | untouched | OK |
| backend-middle-architecture-3-v2 | 2 | MIDDLE | ARCHITECTURE | APPLIED | OK | replacement | IMPORTANT |
| backend-middle-architecture-4-v1 | 1 | MIDDLE | ARCHITECTURE | APPLIED | MINOR | untouched | OK |
| backend-middle-architecture-5-v1 | 1 | MIDDLE | ARCHITECTURE | ADVANCED | MINOR | untouched | OK |
| backend-middle-testing_security_debugging-1-v1 | 1 | MIDDLE | TESTING_SECURITY_DEBUGGING | BASIC | OK | untouched | OK |
| backend-middle-testing_security_debugging-2-v1 | 1 | MIDDLE | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | untouched | OK |
| backend-middle-testing_security_debugging-3-v2 | 2 | MIDDLE | TESTING_SECURITY_DEBUGGING | APPLIED | OK | replacement | IMPORTANT |
| backend-middle-testing_security_debugging-4-v2 | 2 | MIDDLE | TESTING_SECURITY_DEBUGGING | APPLIED | OK | replacement | IMPORTANT |
| backend-middle-testing_security_debugging-5-v1 | 1 | MIDDLE | TESTING_SECURITY_DEBUGGING | ADVANCED | IMPORTANT | untouched | OK |
| backend-senior-programming-1-v1 | 1 | SENIOR | PROGRAMMING | BASIC | OK | untouched | OK |
| backend-senior-programming-2-v2 | 2 | SENIOR | PROGRAMMING | APPLIED | OK | replacement | IMPORTANT |
| backend-senior-programming-3-v2 | 2 | SENIOR | PROGRAMMING | APPLIED | OK | replacement | IMPORTANT |
| backend-senior-programming-4-v1 | 1 | SENIOR | PROGRAMMING | APPLIED | IMPORTANT | untouched | OK |
| backend-senior-programming-5-v2 | 2 | SENIOR | PROGRAMMING | ADVANCED | OK | replacement | IMPORTANT |
| backend-senior-http_api-1-v2 | 2 | SENIOR | HTTP_API | BASIC | OK | replacement | IMPORTANT |
| backend-senior-http_api-2-v2 | 2 | SENIOR | HTTP_API | APPLIED | OK | replacement | IMPORTANT |
| backend-senior-http_api-3-v2 | 2 | SENIOR | HTTP_API | APPLIED | OK | replacement | IMPORTANT |
| backend-senior-http_api-4-v2 | 2 | SENIOR | HTTP_API | APPLIED | OK | replacement | IMPORTANT |
| backend-senior-http_api-5-v2 | 2 | SENIOR | HTTP_API | ADVANCED | OK | replacement | IMPORTANT |
| backend-senior-databases-1-v2 | 2 | SENIOR | DATABASES | BASIC | OK | replacement | IMPORTANT |
| backend-senior-databases-2-v1 | 1 | SENIOR | DATABASES | APPLIED | IMPORTANT | untouched | OK |
| backend-senior-databases-3-v2 | 2 | SENIOR | DATABASES | APPLIED | OK | replacement | IMPORTANT |
| backend-senior-databases-4-v1 | 1 | SENIOR | DATABASES | APPLIED | IMPORTANT | untouched | OK |
| backend-senior-databases-5-v2 | 2 | SENIOR | DATABASES | ADVANCED | OK | replacement | IMPORTANT |
| backend-senior-architecture-1-v1 | 1 | SENIOR | ARCHITECTURE | BASIC | OK | untouched | OK |
| backend-senior-architecture-2-v1 | 1 | SENIOR | ARCHITECTURE | APPLIED | MINOR | untouched | OK |
| backend-senior-architecture-3-v1 | 1 | SENIOR | ARCHITECTURE | APPLIED | IMPORTANT | untouched | OK |
| backend-senior-architecture-4-v3 | 3 | SENIOR | ARCHITECTURE | APPLIED | OK | replacement | IMPORTANT |
| backend-senior-architecture-5-v1 | 1 | SENIOR | ARCHITECTURE | ADVANCED | IMPORTANT | untouched | OK |
| backend-senior-testing_security_debugging-1-v2 | 2 | SENIOR | TESTING_SECURITY_DEBUGGING | BASIC | OK | replacement | IMPORTANT |
| backend-senior-testing_security_debugging-2-v1 | 1 | SENIOR | TESTING_SECURITY_DEBUGGING | APPLIED | IMPORTANT | untouched | OK |
| backend-senior-testing_security_debugging-3-v1 | 1 | SENIOR | TESTING_SECURITY_DEBUGGING | APPLIED | IMPORTANT | untouched | MINOR |
| backend-senior-testing_security_debugging-4-v2 | 2 | SENIOR | TESTING_SECURITY_DEBUGGING | APPLIED | OK | replacement | IMPORTANT |
| backend-senior-testing_security_debugging-5-v2 | 2 | SENIOR | TESTING_SECURITY_DEBUGGING | ADVANCED | OK | replacement | IMPORTANT |

## All 15 bucket reviews

Every bucket retains the source blueprint **1 BASIC / 3 APPLIED / 1 ADVANCED = 5**. Review of cognitive spread is separate from that structural count.

| Grade | Competency | BASIC/APPLIED/ADVANCED | IMPORTANT | MINOR | OK | Within-grade review |
| --- | --- | --- | --- | --- | --- | --- |
| JUNIOR | PROGRAMMING | 1/3/1 | 0 | 0 | 5 | Локальные фундаментальные и практические задачи; дополнительное взаимодействие приоритетов в ADVANCED не требует архитектурного владения. Существенной инверсии сложности не найдено. |
| JUNIOR | HTTP_API | 1/3/1 | 0 | 1 | 4 | Fundamentals, локальная валидация и доверие к запросу развиваются до cookie-сценария. Есть одна локальная слабость дистракторов, grade demand сохраняется. |
| JUNIOR | DATABASES | 1/3/1 | 0 | 0 | 5 | Инварианты, связи, атомарность и поиск развиваются до семантики внешнего соединения. Контекст достаточно определён; scoring-проблемы не выявлены. |
| JUNIOR | ARCHITECTURE | 1/3/1 | 0 | 2 | 3 | Задачи остаются стандартными локальными boundaries. Два APPLIED набора имеют слабые дистракторы; требование системного владения Junior не добавлено. |
| JUNIOR | TESTING_SECURITY_DEBUGGING | 1/3/1 | 0 | 2 | 3 | Все три части компетенции представлены. Новый ADVANCED требует различить гипотезы по фактам; два APPLIED имеют локальные слабости вариантов. |
| MIDDLE | PROGRAMMING | 1/3/1 | 0 | 1 | 4 | Бюджеты, порядок, отмена и admission усложняют применение по сравнению с Junior. ADVANCED добавляет несколько независимых ограничений к теме APPLIED; один локальный набор вариантов слабее. |
| MIDDLE | HTTP_API | 1/3/1 | 1 | 0 | 4 | Контракты, угрозы и состояния создают содержательные APPLIED задачи. Неизменённый ADVANCED заметно слабее остальных по глубине выбора и не демонстрирует сопоставимые взаимодействующие требования. |
| MIDDLE | DATABASES | 1/3/1 | 1 | 2 | 2 | Измерения и конкурентные ограничения усилили APPLIED. У одной новой версии неявна существенная concurrency-гарантия; остальные слабости локальны. |
| MIDDLE | ARCHITECTURE | 1/3/1 | 0 | 3 | 2 | Межкомпонентные атомарность, кеш и деградация соответствуют Middle. Новый APPLIED содержит реальные политики; несколько неизменённых вопросов имеют ограниченное разнообразие вариантов. |
| MIDDLE | TESTING_SECURITY_DEBUGGING | 1/3/1 | 1 | 1 | 3 | Новые APPLIED требуют различить доказательство enforcement и диагностическую гипотезу. Неизменённый ADVANCED практически исключает конкуренцию из всех отвлекающих стратегий и существенно ослабляет измерение слота. |
| SENIOR | PROGRAMMING | 1/3/1 | 1 | 0 | 4 | Новые вопросы измеряют владение внешним результатом, allocation и координацию поколений. Неизменённый APPLIED остаётся одним общим правилом и нарушает содержательную progression относительно Middle. |
| SENIOR | HTTP_API | 1/3/1 | 0 | 0 | 5 | Все пять вопросов получили содержательные authority, routing, rollout либо lifecycle constraints. BASIC допустим как фундаментальная системная граница; строгого численного порядка между labels не предполагается. |
| SENIOR | DATABASES | 1/3/1 | 2 | 0 | 3 | Новые вопросы системно проверяют агрегатный инвариант, совместимый rollout и конкурирующие terminal переходы. Два неизменённых APPLIED сводятся к стандартной реакции или определению. |
| SENIOR | ARCHITECTURE | 1/3/1 | 2 | 1 | 2 | Новая canonical-задача содержит replay, ownership и historical consistency. Один APPLIED и ADVANCED остаются существенно облегчёнными; другая APPLIED boundary-задача имеет локально слабые варианты. |
| SENIOR | TESTING_SECURITY_DEBUGGING | 1/3/1 | 2 | 0 | 3 | Новые security, observability и failure-evidence сценарии имеют системный demand. Два неизменённых APPLIED его существенно не подтверждают; у одного также сохраняется контекстная оговорка. |

## Cross-grade progression and overlap

| Competency | Reviewed | Safe review |
| --- | --- | --- |
| PROGRAMMING | 15 | Junior измеряет локальное поведение языка и ресурсов; новые Middle вопросы — управление потоками и ограничениями компонентов; новые Senior — восстановимое владение, runtime allocation и межпроцессную координацию. backend-senior-programming-4-v1 остаётся ниже этого demand; это отдельный IMPORTANT. Пересечение Middle APPLIED и ADVANCED по SDK не объявлено near-duplicate: дополнительные ограничения materially меняют выбор. |
| HTTP_API | 15 | Переход от фундаментальной HTTP-семантики и доверия к контрактам обновления, threat model и операциям, затем к authority, региональным мутациям, proxy trust и rollout прослеживается. Слабость backend-middle-http_api-5-v1 относится к его ADVANCED demand. Старый тройной overlap Junior architecture / Middle HTTP / Senior HTTP устранён. |
| DATABASES | 15 | Junior локальные инварианты и запросы переходят к измеренному выбору загрузки и транзакционным ограничениям Middle, затем к агрегатам, миграции и конкурирующим terminal переходам Senior. Старый Middle BASIC / Senior ADVANCED overlap устранён. Два неизменённых Senior APPLIED остаются общими стандартными правилами и ослабляют progression; concurrency-оговорка нового Middle рассматривается отдельно. |
| ARCHITECTURE | 15 | Junior стандартные boundaries и retry переходят к Middle межкомпонентной согласованности и деградации, затем к Senior authority и восстановлению исторических условий. Общая тема повторов сама по себе не duplicate. backend-senior-architecture-3-v1 и backend-senior-architecture-5-v1 не демонстрируют необходимое повышение demand. |
| TESTING_SECURITY_DEBUGGING | 15 | Junior проверяет фундаментальную защиту и локальную регрессию; новые Middle требуют доказательства серверного enforcement и интерпретации диагностики; новые Senior учитывают путь чувствительных данных, качество наблюдений и неопределённый внешний исход. Неизменённые Middle ADVANCED и два Senior APPLIED существенно слабее этой progression. Не предполагается, что короткий BASIC или одинаковый общий термин автоматически является дефектом. |

- **RESOLVED**: `backend-junior-architecture-5-v1` ↔ `backend-middle-http_api-4-v2` ↔ `backend-senior-http_api-1-v2`. Проверены все три текущих сценария. Junior остаётся стандартным повтором намерения; Middle добавляет контракт состояний клиента, Senior требует оценить authority принятия и завершения. Когнитивное совпадение baseline не сохраняется.
- **RESOLVED**: `backend-middle-databases-1-v1` ↔ `backend-senior-databases-5-v2`. Проверены оба текущих сценария. Senior теперь включает разные terminal команды, повторы, crash и согласованность нескольких записей; это иной demand относительно локального lost-update Middle BASIC.

No exact duplicates were found in this review. Shared Backend topics alone were not classified as near-duplicates; cognitive requirements and actual alternatives were compared. The old two overlap groups are resolved. New weak grade/difficulty findings remain listed above. This is a qualitative judgment, not an empirical claim of equal score scales across grades.

Extra human-review cautions D06, D11 and D25 were inspected in the final stems and all alternatives. These current replacements are OK in this pass: the tasks require discrimination among technical properties/evidence/control boundaries. Passing those three cautions does not override findings elsewhere.

## P3-B regression evidence and scope

Before P3-C began, the P3-B checkpoint ran the following targeted tests on SQLite, with working directory `backend/`:

```text
../.venv/bin/python -m pytest -q tests/test_assessment_bank_remediation.py tests/test_assessment_validation.py tests/test_assessments.py
192 passed, 1 skipped, 0 failed, 5 warnings
```

Breakdown: remediation 42 passed; validation 85 passed; assessments 65 passed and one PostgreSQL-only row-locking case skipped on SQLite. Warnings were the existing Starlette/httpx notice and four SQLite datetime-adapter deprecation notices. Targeted Ruff check passed; Ruff formatted the new test file, and the existing validation test file was unchanged by formatting. `git diff --check` passed at the P3-B checkpoint. These results are not the P3-D full gate.

The remediation tests cover the exact mapping and metadata, 48 unchanged records, six untouched original MINORs, zero structural findings, fresh/repeated seed, baseline→P3 seed with stable historical question/option IDs and content, the explicit v2→v3 case, rejected same-code mutations, and historical/active attempts spanning seed for all three grades. The baseline fixture is byte-equivalent to the fixed pre-P3 source and has a literal hash guard.

The runtime seed only deactivates the explicitly named immediate predecessor. A persistent DB must not skip an already-published intermediate version when applying later versioned source. A fresh DB may contain only the current v3. This operational constraint is documented without changing seed behavior.

P3 production diff is limited to the question-bank JSON. Assessment scoring, thresholds, timing, cooldowns, qualification/canonical profile rules, lifecycle/API, selection/shuffle, seed implementation, Matching, Invitations, FSP, frontend, migrations, CI and dependencies are unchanged. The approved design and old audit remain provenance. No O2 branch integration occurred.

## Readiness, limitations and required human decision

**NOT_READY**: actual IMPORTANT findings prevent P3-D and PR creation. Full SQLite/PostgreSQL 17 suites, full Ruff/format/mypy, Alembic and Docker/seed-mode gates were not started as P3-D. No technical-gate pass or MVP readiness is claimed. Targeted P3-B evidence above is preserved separately.

- Это qualitative content review по frozen rubric, не psychometric calibration, не pilot study и не сертификат уровня.
- Не получены распределения ответов кандидатов, эмпирическая сложность, discrimination, reliability или hiring outcomes.
- Во время независимого content review достаточность технической структуры не использовалась как evidence качества содержания; reviewer не менял production/tests и не запускал проверки.
- Live DB, candidate API и визуальный runtime отдельно не аудировались; вывод answer leakage ограничен содержанием текущего source и безопасностью данного артефакта.
- Классификации grade/difficulty/severity требуют human content review. Обнаруженные IMPORTANT не исправлялись; решение о second pass остаётся за пользователем.

The independent reviewer’s read-only audit did not run tests or inspect a live DB/API. The targeted P3-B implementation tests are separately reported above. Human review must decide whether to authorize a second versioned remediation pass for the listed findings. No further questions were rewritten after the audit, no PR was created, and no merge was performed.

- P3-B REMEDIATION IMPLEMENTED
- P3-C AUDIT FOUND BLOCKING CONTENT FINDINGS
- P3-D FINAL GATE NOT AUTHORIZED
- PR NOT CREATED
- STOP FOR HUMAN REVIEW
