# Assessment bank audit — draft

Status: ASSESSMENT PREWORK READY FOR HUMAN REVIEW. Review date: 2026-10-06 (Europe/Moscow).

Baseline origin/main: `9892400d57b57fe3104d1871fa3513e56e24c4b5`. Branch: `docs/assessment-validation-prework`.

## Scope

Полный ручной content review всех 75 Backend source questions из [backend/app/content/backend_questions.json](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/content/backend_questions.json). Файл не редактировался. Source SHA256: `7d2c7f2db8a7986d3027e250ac47786e700e4babf0c80e7c46ce6fce34442096`.

Просмотрены stem и все четыре alternatives каждого question. В отчёте публикуются только codes, metadata и безопасные reasons; нет answer texts, option positions, key или пояснений, позволяющих восстановить правильный вариант. Matching branch/implementation и locked holdout/output не использовались. Production не менялся.

## Structural Summary

| Срез | Count |
|---|---:|
| Total source questions | 75 |
| JUNIOR | 25 |
| MIDDLE | 25 |
| SENIOR | 25 |
| PROGRAMMING, все grades | 15 |
| HTTP_API, все grades | 15 |
| DATABASES, все grades | 15 |
| ARCHITECTURE, все grades | 15 |
| TESTING_SECURITY_DEBUGGING, все grades | 15 |
| BASIC, все grades | 15 |
| APPLIED, все grades | 45 |
| ADVANCED, все grades | 15 |

В каждой строке следующей таблицы counts проверены по реальному JSON, без production validator:

| Grade | Competency | BASIC | APPLIED source | ADVANCED | Total |
|---|---|---:|---:|---:|---:|
| JUNIOR | PROGRAMMING | 1 | 3 | 1 | 5 |
| JUNIOR | HTTP_API | 1 | 3 | 1 | 5 |
| JUNIOR | DATABASES | 1 | 3 | 1 | 5 |
| JUNIOR | ARCHITECTURE | 1 | 3 | 1 | 5 |
| JUNIOR | TESTING_SECURITY_DEBUGGING | 1 | 3 | 1 | 5 |
| MIDDLE | PROGRAMMING | 1 | 3 | 1 | 5 |
| MIDDLE | HTTP_API | 1 | 3 | 1 | 5 |
| MIDDLE | DATABASES | 1 | 3 | 1 | 5 |
| MIDDLE | ARCHITECTURE | 1 | 3 | 1 | 5 |
| MIDDLE | TESTING_SECURITY_DEBUGGING | 1 | 3 | 1 | 5 |
| SENIOR | PROGRAMMING | 1 | 3 | 1 | 5 |
| SENIOR | HTTP_API | 1 | 3 | 1 | 5 |
| SENIOR | DATABASES | 1 | 3 | 1 | 5 |
| SENIOR | ARCHITECTURE | 1 | 3 | 1 | 5 |
| SENIOR | TESTING_SECURITY_DEBUGGING | 1 | 3 | 1 | 5 |

Каждый grade имеет 5 BASIC / 15 APPLIED / 5 ADVANCED. Все 75 codes и все 75 stems уникальны по точному тексту. У всех вопросов четыре разные непустые alternatives; blank stems не найдены. Structural source blueprint выполнен. Это не доказательство content/psychometric validity.

73 records version=1, два version=2. Replacements: backend-junior-architecture-1-v2 и backend-senior-architecture-4-v2. Их supersedes ссылаются на предыдущие v1 codes, которых в текущем source JSON нет. Seed допускает отсутствие predecessor при первом запуске, при наличии деактивирует его и сохраняет историю. Source counts не являются инвентаризацией конкретной live DB: там могут оставаться inactive прежние версии.

Source specialization field отсутствует; [backend/app/question_bank.py:47](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/question_bank.py#L47) закрепляет Backend при seed. В runtime [backend/app/services/assessments.py:187](https://github.com/ssavantonoff/fsp-platform/blob/9892400d57b57fe3104d1871fa3513e56e24c4b5/backend/app/services/assessments.py#L187) проверяется возможность собрать blueprint, не полное равенство source counts. Уже существующие checks и недостающие structural validation перечислены в [Task 3 map](assessment-task3-implementation-map.md).

## Review Method

Каждый из 75 вопросов рассмотрен по 16 критериям P2: Backend specialization; grade; difficulty; competency; единственный наиболее корректный ответ; наличие двух разумных ответов; неоднозначность wording; скрытый контекст; trivia; случайная зависимость от версии; engineering knowledge против угадывания wording; answer leakage; качество distractors; near-duplicates; сложность внутри grade; соответствие rubric.

| Grade | Что измеряется | Ограничение для audit |
|---|---|---|
| JUNIOR | Фундамент, стандартные практические ситуации, локальные задачи одного компонента, базовые инструменты и типовые ошибки | Не требуется системный архитектурный опыт. |
| MIDDLE | Применение знаний, выбор решения и trade-offs, API/transactions, debugging/performance, взаимодействие компонентов | Для APPLIED/ADVANCED недостаточно узнавания одного термина или очевидно безопасной формулировки. |
| SENIOR | Архитектурные trade-offs, concurrency/consistency, failure modes, scaling, security/observability, системные решения | Нужна проверка инженерного суждения; редкое слово или тема распределённых систем сами по себе не доказывают Senior demand. |

### Severity и consistency rules

- BLOCKER: нет обоснованно однозначной оценки либо отсутствующий контекст способен менять корректный ответ и результат.
- IMPORTANT: вопрос имеет наиболее корректный ответ, но серьёзно ослабляет измерение заявленного grade/difficulty/competency.
- MINOR: локальная редакционная или менее существенная measurement проблема без установленной ошибочной оценки.

Короткий BASIC сам по себе не дефект; сложная тема сама по себе не достаточное подтверждение Senior. Junior fundamentals с облегчёнными distractors получают MINOR, когда содержательная задача остаётся соответствующей Junior; систематически облегчённый выбор в Middle/Senior APPLIED/ADVANCED — IMPORTANT. Для важных grade/difficulty findings проверяется требуемое действие, а не только терминология темы. Простое повторение темы между grades не объявляется duplicate без близкого когнитивного требования.

Технические предпосылки сверялись с первичными справочниками: [RFC 9110](https://datatracker.ietf.org/doc/html/rfc9110), [Python 3.13 asyncio](https://docs.python.org/3.13/library/asyncio-task.html), [PostgreSQL 17 isolation](https://www.postgresql.org/docs/17/transaction-iso.html). References служат проверке общего контекста, не публикуют solutions и не калибруют grades. Rubric/severity — экспертные judgments.

У всех заданий найден один наиболее обоснованный ответ при заявленном контексте; доказанного неверного scoring key, двух равноправных ответов или answer leakage в candidate API не обнаружено. Этот вывод не является формальным доказательством полноты возможных интерпретаций. Source key не публикуется. Вопрос с потенциальным контекстным уточнением ниже отмечен MINOR: он спрашивает о риске, не гарантирует его наступление.

## Findings Summary

Одна строка — один flagged question с максимальной severity; несколько categories в строке не увеличивают finding count.

| Severity | Flagged questions |
|---|---:|
| BLOCKER | 0 |
| IMPORTANT | 27 |
| MINOR | 6 |
| Total flagged | 33 |
| Reviewed without findings | 42 |
| Total reviewed | 75 |

| Grade | BLOCKER | IMPORTANT | MINOR | Without findings |
|---|---:|---:|---:|---:|
| JUNIOR | 0 | 1 | 5 | 19 |
| MIDDLE | 0 | 11 | 0 | 14 |
| SENIOR | 0 | 15 | 1 | 9 |

AMBIGUOUS, MULTIPLE_REASONABLE_ANSWERS, GRADE_TOO_HARD, COMPETENCY_MISMATCH, VERSION_SPECIFIC, ANSWER_LEAKAGE и OTHER не присваивались без достаточных оснований. CONTEXT_DEPENDENT не означает доказанную невозможность единственной оценки. Отсутствие flag — положительный результат этого ограниченного экспертного review, не сертификат качества.

## Findings

| Question code | Grade | Competency | Difficulty | Severity | Finding categories | Reason |
|---|---|---|---|---|---|---|
| backend-junior-http_api-2-v1 | JUNIOR | HTTP_API | APPLIED | MINOR | WEAK_DISTRACTORS | Несколько альтернатив не похожи на типичные ошибки начинающего при проверке входа. Тема и уровень подходят, но выбор слишком облегчён. |
| backend-junior-architecture-2-v1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR | WEAK_DISTRACTORS | Альтернативы слабо отражают реальные стратегии работы с нестабильной зависимостью; две не связаны с ограничением ожидания. Junior scenario валиден. |
| backend-junior-architecture-3-v1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR | WEAK_DISTRACTORS | Варианты почти не сравнивают правдоподобные способы изоляции теста. Локальная задача подходит Junior, различительная способность ограничена. |
| backend-junior-testing_security_debugging-3-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | WEAK_DISTRACTORS | Альтернативные проверки в основном не проверяют описанное поведение. Для Junior это допустимая основа, но набор отвлекающих вариантов стоит усилить. |
| backend-junior-testing_security_debugging-4-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | WEAK_DISTRACTORS | Почти весь набор отвлекающих вариантов содержит очевидные нарушения обработки ошибки. Содержательная тема подходит Junior. |
| backend-junior-testing_security_debugging-5-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | ADVANCED | IMPORTANT | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | ADVANCED требует только распознавания стандартного начала диагностики без анализа фактов или гипотез; три альтернативы явно не помогают исследовать сбой. |
| backend-middle-programming-2-v1 | MIDDLE | PROGRAMMING | APPLIED | IMPORTANT | WEAK_DISTRACTORS | Тема взаимодействия async handler и I/O соответствует Middle, но альтернативы не предлагают реалистичного выбора реализации с ограничениями. Трудность выбора существенно ниже темы. |
| backend-middle-programming-3-v1 | MIDDLE | PROGRAMMING | APPLIED | IMPORTANT | GRADE_TOO_EASY, DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | APPLIED сводится к базовой локальной обработке файла без взаимодействия компонентов или trade-off. Альтернативы слишком явно противоречат ограничению из stem. |
| backend-middle-programming-5-v1 | MIDDLE | PROGRAMMING | ADVANCED | IMPORTANT | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | ADVANCED обозначен у выбора базового ограничения нагрузки без оценки очереди, ошибок или нескольких разумных подходов. Неверные альтернативы почти не конкурируют между собой. |
| backend-middle-http_api-2-v1 | MIDDLE | HTTP_API | APPLIED | IMPORTANT | WEAK_DISTRACTORS | Сценарий конкурентного редактирования содержательно релевантен; альтернативы не создают выбора между правдоподобными контрактами обновления. |
| backend-middle-http_api-3-v1 | MIDDLE | HTTP_API | APPLIED | IMPORTANT | WEAK_DISTRACTORS | Тема защиты персональных ответов уместна, но альтернативы не сравнивают разумные стратегии кэширования и контекста авторизации. |
| backend-middle-http_api-4-v1 | MIDDLE | HTTP_API | APPLIED | IMPORTANT | GRADE_TOO_EASY, NEAR_DUPLICATE | Когнитивная задача почти повторяет backend-junior-architecture-5-v1: распознавание безопасного повтора операции, без новых ограничений, требующих Middle judgement. |
| backend-middle-databases-2-v1 | MIDDLE | DATABASES | APPLIED | IMPORTANT | WEAK_DISTRACTORS | APPLIED предлагает узнать стандартную ORM-проблему, но не сравнивает правдоподобные варианты загрузки. Сложность выбора низка для заявленного уровня. |
| backend-middle-databases-4-v1 | MIDDLE | DATABASES | APPLIED | IMPORTANT | GRADE_TOO_EASY, DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | Нужен базовый факт о жизненном цикле транзакции; нет применения знания к нескольким допустимым решениям. APPLIED измеряет узнавание правила. |
| backend-middle-architecture-3-v1 | MIDDLE | ARCHITECTURE | APPLIED | IMPORTANT | WEAK_DISTRACTORS | Тема cascading failures соответствует rubric, но все distractors представлены явно неразумной реакцией на отказ. Заявленное инженерное суждение слабо проверяется. |
| backend-middle-testing_security_debugging-3-v1 | MIDDLE | TESTING_SECURITY_DEBUGGING | APPLIED | IMPORTANT | ARTIFICIAL_WORDING, WEAK_DISTRACTORS | Исходная тестовая практика намеренно гиперболизирована, а альтернативы не отражают обычный инженерный выбор. APPLIED можно пройти по правдоподобию wording. |
| backend-middle-testing_security_debugging-4-v1 | MIDDLE | TESTING_SECURITY_DEBUGGING | APPLIED | IMPORTANT | WEAK_DISTRACTORS | Не требуется интерпретировать диагностические данные; альтернативы в основном нерелевантны описанной регрессии. Тема performance подходит, качество измерения ограничено. |
| backend-senior-programming-2-v1 | SENIOR | PROGRAMMING | APPLIED | IMPORTANT | GRADE_TOO_EASY, WEAK_DISTRACTORS | Senior APPLIED сводит отмену операции к общему требованию корректного завершения работы с ресурсом. Условия не требуют выбора системной стратегии или анализа failure modes. |
| backend-senior-programming-3-v1 | SENIOR | PROGRAMMING | APPLIED | IMPORTANT | GRADE_TOO_EASY, WEAK_DISTRACTORS | APPLIED проверяет знакомство с типовой характеристикой runtime, не выбор по измерениям и ограничениям workload. Условия о CPython с GIL явно заданы; VERSION_SPECIFIC defect не заявляется. |
| backend-senior-programming-5-v1 | SENIOR | PROGRAMMING | ADVANCED | IMPORTANT | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | ADVANCED остаётся распознаванием подхода к одному локальному concurrency case; не проверяет анализ его компромиссов или отказов на содержательных альтернативных решениях. |
| backend-senior-http_api-1-v1 | SENIOR | HTTP_API | BASIC | IMPORTANT | GRADE_TOO_EASY, NEAR_DUPLICATE | Требуемое суждение существенно перекрывается с backend-middle-http_api-4-v1 и backend-junior-architecture-5-v1. Новый grade не добавляет содержательного ограничения. |
| backend-senior-http_api-2-v1 | SENIOR | HTTP_API | APPLIED | IMPORTANT | GRADE_TOO_EASY, WEAK_DISTRACTORS | Тема эволюции контракта системная, но вопрос предлагает лишь общую декларацию перехода, без ограничений rollout и выбора между жизнеспособными стратегиями. |
| backend-senior-http_api-3-v1 | SENIOR | HTTP_API | APPLIED | IMPORTANT | WEAK_DISTRACTORS | Сценарий гонки соответствует Senior concurrency. Альтернативы не дают содержательного сравнения корректных архитектурных способов работы с конфликтом. |
| backend-senior-http_api-4-v1 | SENIOR | HTTP_API | APPLIED | IMPORTANT | WEAK_DISTRACTORS | Тема trust boundary релевантна, однако distractors состоят из явно несостоятельных оснований доверия; Senior judgement почти не требуется для выбора. |
| backend-senior-http_api-5-v1 | SENIOR | HTTP_API | ADVANCED | IMPORTANT | DIFFICULTY_MISMATCH, WEAK_DISTRACTORS | ADVANCED требует распознать базовую согласованность API contract, без сложного случая границ намерения или жизненного цикла операции. Альтернативы слишком облегчены. |
| backend-senior-databases-1-v1 | SENIOR | DATABASES | BASIC | IMPORTANT | TRIVIA, WEAK_DISTRACTORS | Запрашивается название явления, а не инженерное решение. Конкурирующие термины в основном не относятся к сценарию; знание vocabulary не доказывает Senior judgement. |
| backend-senior-databases-3-v1 | SENIOR | DATABASES | APPLIED | IMPORTANT | WEAK_DISTRACTORS | Тема безопасной миграции подходит Senior, но альтернативы не сравнивают жизнеспособные rollout с различными ограничениями. Одна общая стратегия не проверяет системный trade-off. |
| backend-senior-databases-5-v1 | SENIOR | DATABASES | ADVANCED | IMPORTANT | GRADE_TOO_EASY, DIFFICULTY_MISMATCH, NEAR_DUPLICATE | ADVANCED близок по требуемому суждению к backend-middle-databases-1-v1: локальный конфликт обновления. Нет дополнительной системной сложности, объясняющей Senior demand. |
| backend-senior-architecture-4-v2 | SENIOR | ARCHITECTURE | APPLIED | IMPORTANT | GRADE_TOO_EASY, WEAK_DISTRACTORS | APPLIED решается выбором локального data contract одного заказа; нет системных trade-offs или failure modes, соответствующих Senior rubric. |
| backend-senior-testing_security_debugging-1-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | BASIC | IMPORTANT | GRADE_TOO_EASY, WEAK_DISTRACTORS | Даже для Senior BASIC требуется лишь фундаментальное правило обращения с чувствительной информацией. Альтернативы не проверяют observability trade-offs или инженерное суждение. |
| backend-senior-testing_security_debugging-3-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR | CONTEXT_DEPENDENT | Для оценки возможности описанного риска не указан порядок access check относительно cache lookup и контекст ответа. Stem спрашивает о потенциальном риске, поэтому доказанного scoring BLOCKER нет; контекст стоит уточнить. |
| backend-senior-testing_security_debugging-4-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | APPLIED | IMPORTANT | WEAK_DISTRACTORS | Observability topic соответствует Senior, но отсутствие конкретных измерений и правдоподобных альтернатив делает ответ выбором общей категории диагностики. |
| backend-senior-testing_security_debugging-5-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | ADVANCED | IMPORTANT | WEAK_DISTRACTORS | Failure-injection topic подходит Senior; distractors не представляют сравнимых стратегий проверки и явно обходят поставленную задачу. Системное суждение проверяется слабо. |

## Grade-Level Observations

### JUNIOR

Большинство вопросов соответствует fundamentals и локальным стандартным ситуациям. Более содержательные вопросы внутри Junior требуют практического понимания, не системной архитектуры. Основные замечания относятся к distractors; один ADVANCED diagnostic question не демонстрирует ожидаемую дополнительную сложность. Оснований повышать вопросы до более высокого grade или требовать архитектурного опыта не выявлено.

### MIDDLE

Покрыты API, транзакции, ORM, concurrency, кэш, диагностика и тестовые границы. Несколько APPLIED требуют лишь локального факта; часть вариантов не создаёт инженерного выбора. Тематическое покрытие не равно доказанному применению/trade-off навыку. Транзакционные и pagination вопросы не были объявлены неоднозначными только из-за существования других решений, отсутствующих в options.

### SENIOR

Есть релевантные distributed/concurrency/failure/observability темы. Однако значительная часть APPLIED/ADVANCED ограничивается узнаванием общей практики, а alternatives не моделируют жизнеспособные стратегии. Один BASIC спрашивает vocabulary; один APPLIED data scenario остаётся локальным. Это основной риск соответствия frozen Senior rubric. Корректный выбор в таких заданиях не даёт достаточного evidence Senior judgement.

## Competency-Level Observations

| Competency | Observation |
|---|---|
| PROGRAMMING | Все grades тематически релевантны; у отдельных Middle/Senior заданий требуемое применение слишком облегчено. Senior runtime context указан явно, поэтому произвольная version dependency не приписывается. |
| HTTP_API | Переход от фундаментальных задач к контрактам и trust boundaries просматривается; повтор когнитивной задачи между grades и слабые alternatives ограничивают различение уровня. |
| DATABASES | Хорошее тематическое покрытие transactions/concurrency и rollout; отдельные задачи измеряют узнавание vocabulary/локального приёма вместо требуемого judgement. |
| ARCHITECTURE | Есть межкомпонентные и distributed failure темы; несколько задач слабо различают инженерный уровень. Перекрытие с HTTP/DB не означает автоматически competency mismatch. |
| TESTING_SECURITY_DEBUGGING | Все три аспекта представлены, но объединённая competency даёт только четыре измерения в attempt. Много очевидных alternatives; у одной Senior risk-formulation недостаёт контекста pipeline. |

## Duplicate / overlap observations

Точных повторов stem нет. Near-duplicate findings относятся к близкому когнитивному требованию, не к буквальному совпадению:

- backend-junior-architecture-5-v1 ↔ backend-middle-http_api-4-v1 ↔ backend-senior-http_api-1-v1: смена grade/competency не добавляет достаточно нового требования к суждению. Junior вопрос не flagged сам по себе; повышенные grades flagged из-за недостаточной progression.
- backend-middle-databases-1-v1 ↔ backend-senior-databases-5-v1: второе задание имеет ADVANCED label, но остаётся близким локальному конфликту. Это qualitative near-duplicate, не утверждение, что их difficulty математически равна.

Общие темы concurrency/security/testing между competencies естественны для Backend. Не доказана независимость всех вопросов или scores между блоками. BASIC/ADVANCED того же grade повторяются при retake; это ожидаемое поведение source blueprint, не случайно найденный textual duplicate.

## Review Coverage

Регистр ниже фиксирует просмотр всех 75 codes без повторения содержимого или answers. OK означает «в этом review не найден finding». Метаданные grade/competency/difficulty взяты из исходного JSON.

| Question code | Grade | Competency | Difficulty | Review outcome |
|---|---|---|---|---|
| backend-junior-programming-1-v1 | JUNIOR | PROGRAMMING | BASIC | OK |
| backend-junior-programming-2-v1 | JUNIOR | PROGRAMMING | APPLIED | OK |
| backend-junior-programming-3-v1 | JUNIOR | PROGRAMMING | APPLIED | OK |
| backend-junior-programming-4-v1 | JUNIOR | PROGRAMMING | APPLIED | OK |
| backend-junior-programming-5-v1 | JUNIOR | PROGRAMMING | ADVANCED | OK |
| backend-junior-http_api-1-v1 | JUNIOR | HTTP_API | BASIC | OK |
| backend-junior-http_api-2-v1 | JUNIOR | HTTP_API | APPLIED | MINOR |
| backend-junior-http_api-3-v1 | JUNIOR | HTTP_API | APPLIED | OK |
| backend-junior-http_api-4-v1 | JUNIOR | HTTP_API | APPLIED | OK |
| backend-junior-http_api-5-v1 | JUNIOR | HTTP_API | ADVANCED | OK |
| backend-junior-databases-1-v1 | JUNIOR | DATABASES | BASIC | OK |
| backend-junior-databases-2-v1 | JUNIOR | DATABASES | APPLIED | OK |
| backend-junior-databases-3-v1 | JUNIOR | DATABASES | APPLIED | OK |
| backend-junior-databases-4-v1 | JUNIOR | DATABASES | APPLIED | OK |
| backend-junior-databases-5-v1 | JUNIOR | DATABASES | ADVANCED | OK |
| backend-junior-architecture-1-v2 | JUNIOR | ARCHITECTURE | BASIC | OK |
| backend-junior-architecture-2-v1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR |
| backend-junior-architecture-3-v1 | JUNIOR | ARCHITECTURE | APPLIED | MINOR |
| backend-junior-architecture-4-v1 | JUNIOR | ARCHITECTURE | APPLIED | OK |
| backend-junior-architecture-5-v1 | JUNIOR | ARCHITECTURE | ADVANCED | OK |
| backend-junior-testing_security_debugging-1-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | BASIC | OK |
| backend-junior-testing_security_debugging-2-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | OK |
| backend-junior-testing_security_debugging-3-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR |
| backend-junior-testing_security_debugging-4-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR |
| backend-junior-testing_security_debugging-5-v1 | JUNIOR | TESTING_SECURITY_DEBUGGING | ADVANCED | IMPORTANT |
| backend-middle-programming-1-v1 | MIDDLE | PROGRAMMING | BASIC | OK |
| backend-middle-programming-2-v1 | MIDDLE | PROGRAMMING | APPLIED | IMPORTANT |
| backend-middle-programming-3-v1 | MIDDLE | PROGRAMMING | APPLIED | IMPORTANT |
| backend-middle-programming-4-v1 | MIDDLE | PROGRAMMING | APPLIED | OK |
| backend-middle-programming-5-v1 | MIDDLE | PROGRAMMING | ADVANCED | IMPORTANT |
| backend-middle-http_api-1-v1 | MIDDLE | HTTP_API | BASIC | OK |
| backend-middle-http_api-2-v1 | MIDDLE | HTTP_API | APPLIED | IMPORTANT |
| backend-middle-http_api-3-v1 | MIDDLE | HTTP_API | APPLIED | IMPORTANT |
| backend-middle-http_api-4-v1 | MIDDLE | HTTP_API | APPLIED | IMPORTANT |
| backend-middle-http_api-5-v1 | MIDDLE | HTTP_API | ADVANCED | OK |
| backend-middle-databases-1-v1 | MIDDLE | DATABASES | BASIC | OK |
| backend-middle-databases-2-v1 | MIDDLE | DATABASES | APPLIED | IMPORTANT |
| backend-middle-databases-3-v1 | MIDDLE | DATABASES | APPLIED | OK |
| backend-middle-databases-4-v1 | MIDDLE | DATABASES | APPLIED | IMPORTANT |
| backend-middle-databases-5-v1 | MIDDLE | DATABASES | ADVANCED | OK |
| backend-middle-architecture-1-v1 | MIDDLE | ARCHITECTURE | BASIC | OK |
| backend-middle-architecture-2-v1 | MIDDLE | ARCHITECTURE | APPLIED | OK |
| backend-middle-architecture-3-v1 | MIDDLE | ARCHITECTURE | APPLIED | IMPORTANT |
| backend-middle-architecture-4-v1 | MIDDLE | ARCHITECTURE | APPLIED | OK |
| backend-middle-architecture-5-v1 | MIDDLE | ARCHITECTURE | ADVANCED | OK |
| backend-middle-testing_security_debugging-1-v1 | MIDDLE | TESTING_SECURITY_DEBUGGING | BASIC | OK |
| backend-middle-testing_security_debugging-2-v1 | MIDDLE | TESTING_SECURITY_DEBUGGING | APPLIED | OK |
| backend-middle-testing_security_debugging-3-v1 | MIDDLE | TESTING_SECURITY_DEBUGGING | APPLIED | IMPORTANT |
| backend-middle-testing_security_debugging-4-v1 | MIDDLE | TESTING_SECURITY_DEBUGGING | APPLIED | IMPORTANT |
| backend-middle-testing_security_debugging-5-v1 | MIDDLE | TESTING_SECURITY_DEBUGGING | ADVANCED | OK |
| backend-senior-programming-1-v1 | SENIOR | PROGRAMMING | BASIC | OK |
| backend-senior-programming-2-v1 | SENIOR | PROGRAMMING | APPLIED | IMPORTANT |
| backend-senior-programming-3-v1 | SENIOR | PROGRAMMING | APPLIED | IMPORTANT |
| backend-senior-programming-4-v1 | SENIOR | PROGRAMMING | APPLIED | OK |
| backend-senior-programming-5-v1 | SENIOR | PROGRAMMING | ADVANCED | IMPORTANT |
| backend-senior-http_api-1-v1 | SENIOR | HTTP_API | BASIC | IMPORTANT |
| backend-senior-http_api-2-v1 | SENIOR | HTTP_API | APPLIED | IMPORTANT |
| backend-senior-http_api-3-v1 | SENIOR | HTTP_API | APPLIED | IMPORTANT |
| backend-senior-http_api-4-v1 | SENIOR | HTTP_API | APPLIED | IMPORTANT |
| backend-senior-http_api-5-v1 | SENIOR | HTTP_API | ADVANCED | IMPORTANT |
| backend-senior-databases-1-v1 | SENIOR | DATABASES | BASIC | IMPORTANT |
| backend-senior-databases-2-v1 | SENIOR | DATABASES | APPLIED | OK |
| backend-senior-databases-3-v1 | SENIOR | DATABASES | APPLIED | IMPORTANT |
| backend-senior-databases-4-v1 | SENIOR | DATABASES | APPLIED | OK |
| backend-senior-databases-5-v1 | SENIOR | DATABASES | ADVANCED | IMPORTANT |
| backend-senior-architecture-1-v1 | SENIOR | ARCHITECTURE | BASIC | OK |
| backend-senior-architecture-2-v1 | SENIOR | ARCHITECTURE | APPLIED | OK |
| backend-senior-architecture-3-v1 | SENIOR | ARCHITECTURE | APPLIED | OK |
| backend-senior-architecture-4-v2 | SENIOR | ARCHITECTURE | APPLIED | IMPORTANT |
| backend-senior-architecture-5-v1 | SENIOR | ARCHITECTURE | ADVANCED | OK |
| backend-senior-testing_security_debugging-1-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | BASIC | IMPORTANT |
| backend-senior-testing_security_debugging-2-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | APPLIED | OK |
| backend-senior-testing_security_debugging-3-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | APPLIED | MINOR |
| backend-senior-testing_security_debugging-4-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | APPLIED | IMPORTANT |
| backend-senior-testing_security_debugging-5-v1 | SENIOR | TESTING_SECURITY_DEBUGGING | ADVANCED | IMPORTANT |

## Limitations

Это полный expert content review данного source snapshot, не psychometric validation и не pilot study. Нет данных о candidate response distributions, item discrimination, difficulty estimates, reliability или hiring outcomes. Counts/semantic plausibility не доказывают такую валидность. Severity и grade fit требуют human content review; это рекомендации, не product decisions.

DB active bank отдельно не инвентаризировался. UI review выполнен по source current main, без утверждения о runtime/browser visual QA. Scoring/API contract прочитан; связанные production файлы не изменялись. Matching и locked holdout не являлись источниками audit.

## Recommendation

**NOT_READY** для MVP, который должен подтверждать выбранный grade по frozen rubric P2.

Структура и scoring contract выполнены, scoring BLOCKER не найден. Рекомендация основана на 27 IMPORTANT measurement findings, особенно в Senior: содержание пока недостаточно проверяет требуемое инженерное суждение. Это экспертный вывод по rubric, не эмпирическое доказательство ошибочной классификации кандидатов.

Команде следует review flagged questions и отдельно принять решение о content revisions и границах claims. Автоматического изменения банка, thresholds, grades или API из этой рекомендации не следует. Существующий исполняемый demo flow сохраняется. Content исправления потребуют отдельных version/code с сохранением истории; в P2 они не сделаны. TASK №3 не начат.
