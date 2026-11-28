# P9-B0 — Final Backend Audit & Matching Validation

Дата: 10 октября 2026 (Europe/Moscow). Дедлайн: 11 октября 2026.
**Backend: PASS в проверенном scope. Release recommendation: CONDITIONAL.**
Новых подтверждённых P0/P1/P2/P3 дефектов не обнаружено в выполненных проверках.
Human Review: NOT STARTED — awaiting actual human reviewers. Stage 2: NOT STARTED.

## 1. Baseline / SHA

Репозиторий: `ssavantonoff/fsp-platform`. Фактический GitHub/main:
`bce395a8c102491f4cf9ac26106b7263d08ad515`, совпадает с ТЗ.
[PR #18](https://github.com/ssavantonoff/fsp-platform/pull/18) merged в этот SHA.
Ветка аудита: `audit/p9-b0-release-readiness`; новый managed worktree
`C:/Users/olego/.codex/worktrees/p9-b0-release-readiness/fsp-platform`.

Прочитаны [P8-B0 / Draft PR #16](https://github.com/ssavantonoff/fsp-platform/pull/16)
на старом baseline `acead7a5ea8eb93c1344107440ddb6c16b42173f` и
[P8-B1 remediation report](p8-b1-backend-remediation.md).
Финальный P8-B1 SHA `f8d869b6440edbb7279390f96e573fcff738ba4a` и текущий main
имеют одинаковый backend; diff содержит только `frontend/Dockerfile` и
`.github/workflows/checks.yml`. Поэтому полный локальный suite заново не запускался.

GitHub подтверждает [Checks run 38048994399](https://github.com/ssavantonoff/fsp-platform/actions/runs/38048994399)
на **точном baseline SHA**, событие push, status completed / conclusion success.
Jobs backend/frontend/docker — success. Backend job log подтверждает
1073 passed / 1 warning; frontend — 184 tests / 184 pass / 0 fail / 0 skipped.
Ruff check/format (79 files), mypy (39 source files), Alembic upgrade/check,
frontend lint/typecheck/build и Docker startup/seed/health/logo checks — success.
Это **повторно прочитанные результаты CI**, а не новые локальные запуски P9-B0.
Первичный wrapper возвращал пустой список из-за фильтра PR-event;
push run затем найден через authenticated GitHub GET. Ограничение снято.

## 2. Scope

P9-B0 проверяет стабильность существующей системы после PR #18. Ни production-код,
ни frontend, бизнес-правила, миграции/схема, frozen datasets/labels/CSV, вопросы,
формулы, grading, cooldown или git attributes не изменялись. PR #16 не изменён.
Нет deployment, merge, Ready-for-review transition или Stage 2.

Архитектура: FastAPI REST routes и Pydantic DTO; business services для Assessment,
Matching, Needs, Invitations, profiles, FSP и auth; SQLAlchemy 2 / psycopg к PostgreSQL 17;
Alembic migrations; Docker Compose с PostgreSQL, backend и frontend.
Authentication — серверные DB sessions с хешем opaque cookie token, сроком действия
и отзывом при logout/rotation; пароли хешируются Argon2. Роли CANDIDATE/EMPLOYER,
ownership predicates и проверка trusted Origin защищают соответствующие API.
Эта архитектура подтверждена исходниками и обозначенными тестами, не deployment-аудитом.

Superpowers: план, изоляция, inline execution, evidence-before-completion и один
ограниченный независимый review доказательств без повторных тестов.
GitHub: main, PR16/18, CI и Draft PR. Context7 не потребовался — неопределённого
поведения библиотек не осталось. Новый Codex Security scan не запускался:
backend совпадает с проверенным PR18, нового security trigger нет.
Исторический P8-B1 targeted static scan не считается новым P9 scan.

## 3. Backend Verification

**Новые локальные тесты: 365 passed, 0 failed, 0 errors, 0 skipped.**

| Новый запуск | Cases | PASS | FAIL / ERROR / SKIP |
| --- | ---: | ---: | --- |
| Шесть обязательных файлов | 47 | 47 | 0 / 0 / 0 |
| Целевые scoring/API/Assessment/FSP/auth/concurrency controls | 306 | 306 | 0 / 0 / 0 |
| PR15 publication/history controls | 12 | 12 | 0 / 0 / 0 |
| Итого, непересекающиеся node IDs | 365 | 365 | 0 / 0 / 0 |

Required: P8 Matching 11, atomic profile 8, response snapshot 9,
Invitation privacy 8, Invitation evaluator 1, FSP Matching 10.
Controls: Matching rules112, Matching API16, Assessment66, FSP API20, FSP rules11,
Invitation API68, Invitation concurrency7, auth5, seed idempotency1.
Publication:12. Полный список выбранных node selectors находится в
[evidence/commands.json](evidence/p9-b0/commands.json); independent JUnit readback —
[test-summary.json](evidence/p9-b0/test-summary.json).
Каждый запуск сохраняет существующее предупреждение Starlette/httpx deprecation.

Среда: собственный native PostgreSQL **17.11**, новый пустой data directory в
audit cache, выделенные role/database `p9audit`, loopback `127.0.0.1:55441`, UTC.
Перед тестами SQL readback подтверждает version, host/port, database, role,
data_directory и timezone: [database-proof.json](evidence/p9-b0/database-proof.json).
`TEST_DATABASE_URL` задан явно только этому процессу и указывает туда же.
Fixtures создают UUID schemas, применяют существующий Alembic head и удаляют
только собственные schemas. Существующие DB и Docker volumes не использовались.

Python 3.13.7 / существующие backend dependencies переиспользованы read-only.
Тестирование выполнено только в собственном canonical LF export exact baseline,
побайтово из Git archive; P8 worktrees/manual copy не использовались для запуска.
Из P8-B1 cache скопированы только PG17 executable binaries в собственный cache,
без data directory. Docker engine локально недоступен; containers/volumes не тронуты.
Чужие ветки, файлы и checkout не переключались и не изменялись.

Setup не выдаётся за тестовый результат: первоначальный fetch отказал sandbox,
после разрешённой узкой escalation выполнен; первая native worktree попытка не нашла
ещё не fetched SHA; retry после fetch создал worktree. DB preflight уточнён до запуска
pytest: PostgreSQL `inet::text` возвращает `127.0.0.1/32`, а не строку без маски.

## 4. Matching Verification

**Eligibility: PASS.** Точное specialization, canonical verified grade/score,
grade compatibility, все must-have tags и consent=true обязательны.
Declared grade, высокий score, опыт, nice-to-have и FSP не компенсируют hard-filter failure.
Persisted qualification trio защищён DB consistency constraints; timestamp не является
ranking/tie factor. Матрица и filters сохранены:

| Required | Допущенные verified grades / Grade Fit |
| --- | --- |
| JUNIOR | JUNIOR 1.0; MIDDLE 0.75 |
| MIDDLE | MIDDLE 1.0; SENIOR 0.75 |
| SENIOR | SENIOR 1.0 |

**Ranking: PASS.** Professional Fit использует веса Assessment45%, Grade25%,
Nice-to-have15%, Experience15%. Assessment score нормализуется через /100;
nice factor — matched/total; experience — capped ratio к target.
При отсутствии nice requirements или experience target фактор выключается,
оставшиеся веса пропорционально нормализуются до100. Отсутствующий опыт кандидата
при активном target даёт0; target=0 даёт full experience fit.

`Ranking Score = 0.95 × Professional Fit + FSP Bonus`, bonus0–5.
Сортировка серверная по неокруглённым ranking desc → Professional Fit desc →
Assessment desc → candidate ID asc; применяется перед offset/limit.
Determinism/ties, sub-display precision, пагинация, breakdown contributions,
matched/missing skills, read-only behavior и batch-query controls проверены.
Детерминированность относится к неизменным входам; между отдельными запросами
при изменении БД порядок/total могут измениться.

**Regressions после PR18: 28/28 PASS.**

| Исправление | Новые выполненные regression cases | Доказательство |
| --- | ---: | --- |
| P8-B0-001 Coherent Matching | 11 | Controlled PostgreSQL races; consent/skills/spec/canonical/FSP в одном statement snapshot; coherent ranking/page, stale ORM и provider cleanup |
| P8-B0-002 Atomic Profile Update | 8 | Все4 исходных consent×FSP verification комбинации успешны;4 injected failures сохраняют полный rollback |
| P8-B0-003 Coherent API Responses | 9 | Candidate/Need PUT при обоих expire_on_commit; GET/list scalar+relations; commit-failure controls |

Тесты не переписывались. Matching читает scalar candidate streams одним UNION ALL;
Need criteria сохраняется immutable внутри invocation. Candidate/Need mutations
готовят detached DTO под lock до commit и возвращают успех после него; GET joined
reads согласуют scalar/relations. Не заявляется общий snapshot для NeedPage count/items
или всех последовательных пользовательских запросов.

## 5. Invitations & Privacy

Десять правил рассмотрены; существующие product policies не изменены.

| Правило | Основание / фактический метод |
| --- | --- |
| 1 Employer-only send | Новый selected auth-role matrix + role dependencies |
| 2 Собственная ACTIVE Need | Новый active-state и foreign-resource matrix; owner predicate/Need lock |
| 3 Eligible candidate | Новый unavailable-candidate/evaluator controls + FSP hard-filter tests |
| 4 Candidate видит только своё | Static `_owned` + `list_candidate` owner-filter для count/items; full baseline CI. Отдельный adversarial foreign-list test в P9 локально не запускался |
| 5 До ACCEPTED контактов нет | Новый recursive exact allowlist для SENT/VIEWED/DECLINED/WITHDRAWN |
| 6 ACCEPTED раскрывает разрешённым сторонам | Новый ACCEPTED allowlist + foreign-resource tests |
| 7 DECLINED не раскрывает | Новый DECLINED allowlist |
| 8 Чужие invitation недоступны | Новый missing/foreign detail/action matrix, одинаковый404 |
| 9 Неверные state transitions отклоняются | Новый API transition matrix |
| 10 Повторы/concurrency сохраняют DB guards | Новый reinvite matrix и7 PostgreSQL concurrency cases, one-winner/conflict/source-lock checks |

Новый Matching preview exact-allowlist test исключает email, phone/contact fields,
полную фамилию, private FSP ID, user IDs и приватные profile fields.
Display name использует имя и одну букву фамилии. Invitation read tests проверяют
вложенные allowlists на обеих сторонах, list/detail и все5 статусов.
Отсутствие утечек установлено в этих тестовых условиях, не как абсолютная гарантия
для всех deployment paths.

**Product Decision Required:** acceptance существующего приглашения после Need close/
изменения eligibility; сохранение accepted-contact доступа после отзыва consent;
reinvite после DECLINED/WITHDRAWN без отдельного cadence limit.
Current behavior сохранено; отсутствие согласованного другого правила не превращено
в новый дефект. Остальные P8 auth/recovery/in-flight read decisions также не исправлялись.

## 6. Assessment

Новый targeted runtime suite:66 Assessment cases плюс seed1 и publication12 — PASS.
Проверены email/profile/consent prerequisites, допустимость target grade, запрет
клиентской canonical mass-assignment, persist/reload ответов и фиксированного порядка,
owner/option/question binding, submit/idempotency/rollback, server deadline/timeout,
canonical verification, история, cooldown и concurrent start/submit.
API возвращает question/options и saved selection без `is_correct`/правильных ключей;
после завершения доступны агрегаты, не разбор правильных вариантов.

Фактический published source: **Backend120 вопросов,40 на каждый JUNIOR/MIDDLE/SENIOR**.
Legacy published bank использует пять компетенций и mix2 BASIC/4 APPLIED/2 ADVANCED
на каждую grade×competency bucket. Попытка:20 вопросов, четыре варианта с одним
правильным,30 минут; selection1 BASIC/2 APPLIED/1 ADVANCED на компетенцию,
history-aware exposure и SystemRandom; выбранные вопросы/order сохраняются.
Каждый правильный ответ даёт5 overall points и25 в своей компетенции.
PASS требует overall>=70 и каждую competency>=50.
Canonical grade/score/time восстанавливается из подходящей успешной истории;
неудача не обнуляет прежнюю квалификацию.
Cooldown для той же specialization/target grade:7 дней после FAIL,90 после PASS.

PR15 source review/hash gate, отсутствие публикации draft/manual persisted банка,
block partial/changed bank и сохранение существующей истории после unpublication
проверены отдельными12 cases в temporary synthetic fixtures.
Это тесты инфраструктуры; production Frontend/DataML банки не создавались/не публиковались.
**Опубликован только Backend**; остальные registry entries draft. Психометрическая
эквивалентность score разных grades/directions и качество профессиональной диагностики
этими тестами не доказаны. В README осталось75 вопросов — использовать120 из source/tests.

## 7. FSP Integration

**PASS в mock scope.** API link/verify/read/refresh/unlink; mock lookup errors;
achievements; bonus; ID-change verification/evidence reset; rollback;
unverified/empty achievements; privacy-safe aggregates и hard-filter precedence проверены.
Mock registry читает `fsp_registry_mock.json`; реальный официальный API ФСП отсутствует
и не интегрирован. Успешный lookup не является доказательством реальной личности/владения.

Achievement score:
`min(distinct competitions,3)/3 ×30 + best quality ×70`, capped0–100.
Quality: participant0, finalist0.5, prize-winner0.8, winner1.
Verified bonus=`achievement score/100 ×5`; unverified bonus0;
verified без achievements также score/bonus0. FSP не меняет Professional Fit/
Assessment и не обходит eligibility. Private registry identifiers отсутствуют в Matching DTO.

## 8. Human Review Status

**Human Review: NOT STARTED — awaiting actual human reviewers.**
Подтверждённых reviewers:0. Подлинных бланков:0. Completed pairs:0/38 на reviewer.
Личности, квалификация, independence declarations не предоставлены.
Олег не назначен автоматически; если участвует, потребуется раскрыть developer role/
возможное знакомство с алгоритмом. AI/subagent review этого отчёта не является human review.

Прочитаны dataset, methodology, human guide/input/template. AI-proposed file только
проверен по hash, grades/rationales не использованы для reviewer package.
Первый `--check` на Windows checkout: **FAIL — Proposed labels SHA256 mismatch: STOP**.
Эта копия не отправляется; frozen originals/config/hashes не исправлялись.
[Byte evidence](evidence/p9-b0/byte-comparison.json) показывает canonical Git blobs
и CRLF-only отличие checkout (проверено в памяти).
Exact canonical export: **PASS**, 8 Needs /36 Candidates /288 structural pairs,
38 eligible /250 excluded, N1..N8=4,5,3,7,6,3,7,3, neutral ID order,
allowed input fields и все reviewer fields blank. [Check log](evidence/p9-b0/human-package-check.log).

Подготовлены два отдельных local blind ZIP copies из exact canonical bytes:
только guide/input/blank template. [Manifest](evidence/p9-b0/reviewer-package-manifest.json).
Координатор должен реально выбрать и связать двух IT reviewers;
передача сообщений агентом не выполнялась.
[Короткая инструкция пользователю](p9-b0-human-review-handoff.md) описывает файлы,
0–3/rationale/uncertainty, запрет AI/Ranking/FSP hints, возврат оригиналов,
SHA256 и разногласия без автоматического среднего.
N3 Java/N5 Next.js CATALOG_PROXY; N7/N8 specialized ML/platform не подтверждены.
Общие Python/SQL tags не доказывают эти компетенции. Dataset synthetic, skills/stаж self-declared.

**Stage 2: NOT STARTED.** NDCG@3/@5, итоговые Pairwise/Top-k metrics не вычислялись.
Synthetic rule/API tests не являются evaluation ranking against human labels.
Human labels не генерировались; AI_PROPOSED не объявлены HUMAN_REVIEWED.

## 9. Findings

**Новые подтверждённые дефекты: P0=0, P1=0, P2=0, P3=0 в проверенном scope.**
Новых defect records/reproducers нет, production fixes не выполнялись.
Проходящий regression воспроизводит защиту от исправленного дефекта, а не доказывает
универсальное отсутствие всех конкурирующих проблем.

Inherited dispositions:

| ID | Историческая severity | Текущий статус |
| --- | --- | --- |
| P8-B0-001 | P1 | Исправлен PR18;11 новых PASS |
| P8-B0-002 | P2 | Исправлен PR18;8 новых PASS |
| P8-B0-003 | P2 | Исправлен PR18;9 новых PASS |
| P8-B0-004 | P3 | Current loader использует bytes/JSON вместо locale read_text; UTF8 validation PASS. Отдельный non-UTF8 process здесь не запускался |
| P8-B0-005 | P3 | Сохраняется: README75 против source120; не release blocker |
| P8-B0-014 | P3 | Сохраняется Windows newline portability; reproduced package/source mismatch, canonical PASS; не release blocker для canonical/Linux path |

Для сохранённых P3 affected SHA=`bce395a8c102491f4cf9ac26106b7263d08ad515`.
005 reproduction: README bank paragraph vs source loader/inventory; expected120/40,
actual README75; suggested fix — отдельное разрешённое documentation correction.
014 reproduction: `core.autocrlf=true` checkout + `--check`; expected frozen byte hash,
actual STOP; canonical proposed hash111e1a06… vs checkout3209c67b… в evidence.
Suggested fix — отдельная задача с exact-byte Windows checkout strategy,
без ослабления hash gates/изменения frozen данных. Release blocker: NO при использовании
проверенного канонического пакета; ошибочную checkout-копию передавать нельзя.
Это ранее зарегистрированные проблемы, не два новых P9 дефекта.
Potential Need payload/login budget risks остаются Potential, не confirmed DoS/compromise.

## 10. Remaining Risks

- Human relevance ещё не оценена; Stage2 не разрешён. Структурные38/250 не доказывают ranking quality, hiring precision/recall или market representativeness.
- Frontend/DataML qualification в offline dataset — synthetic fixtures; runtime Assessment опубликован только для Backend. Java/Next.js/ML skill catalog proxies и self-declared tags ограничивают выводы.
- FSP mock не подтверждает real organizer integration или ownership.
- Deployment/browser/TLS/SMTP/effective gateway limits и sustained load не проверялись P9 локально. CI Docker success подтверждает CI environment, не production deployment.
- Matching materializes pool до pagination; память/latency широкого snapshot query и lock-duration при DTO preparation не измерялись. Нет гарантии page stability через изменения БД.
- Product decisions для invitation acceptance/consent/resend и auth recovery/email gates остаются открыты. Не заявлять иной privacy contract без решения команды.
- Windows CRLF prerequisites и устаревший README сохраняются; deprecation warning видим.
- Тесты используют request-scoped sessions и supported writers/locks; privileged direct DB writers и произвольные shared providers не покрыты.
- По правилу own candidate inbox локально сохранено статическое доказательство owner filtering и общий CI, без нового отдельного adversarial list теста.

## 11. Evidence

Все новые logs/JUnit сохранены в PR как документационные evidence, не только cache:

- [Summary](evidence/p9-b0/test-summary.json), [commands/timestamps/exit codes](evidence/p9-b0/commands.json), [database identity](evidence/p9-b0/database-proof.json).
- [Required JUnit](evidence/p9-b0/required.xml) / [log](evidence/p9-b0/required.log).
- [Controls JUnit](evidence/p9-b0/controls.xml) / [log](evidence/p9-b0/controls.log).
- [Publication JUnit](evidence/p9-b0/publication.xml) / [log](evidence/p9-b0/publication.log).
- [Independent evidence review](evidence/p9-b0/independent-review.md).
- [Exact baseline CI receipt/jobs/log excerpts](evidence/p9-b0/ci-baseline.json).
- [Canonical package check](evidence/p9-b0/human-package-check.log), [checkout failure](evidence/p9-b0/human-package-checkout-failure.log), [hash comparison](evidence/p9-b0/byte-comparison.json), [blind manifest](evidence/p9-b0/reviewer-package-manifest.json).
- [Execution plan](../superpowers/plans/2026-10-10-p9-b0-verification.md); [handoff](p9-b0-human-review-handoff.md).

Reproduction: собственная disposable PostgreSQL17/UTC; явно направить
`TEST_DATABASE_URL` на её выделенную DB. Использовать exact LF Git export baseline
(`git -c core.autocrlf=false archive`), UTF8 process, repository dependencies.
Из backend выполнить шесть обязательных pytest files с `-q`;
остальные точные selectors — commands.json. Из export root — review `--check`.
Не исправлять hash mismatch в frozen checkout автоматически.
Fixtures применяют реальные существующие миграции, не альтернативную схему.

Исторические P8-B1 local1073/SQLite1034+39 skips/frontend184, lint/mypy/Alembic
не суммируются с новыми365. CI1073/184 подтверждены exact baseline log readback,
но тоже не суммируются с local cases как уникальная coverage.
Source/privacy review и независимый report review — статические методы, не runtime gates.

## 12. Release Recommendation

**CONDITIONAL — допускается конкурсная demo-сдача существующего backend с раскрытыми
ограничениями и независимым review Савы.** Подтверждённых backend P0/P1 блокеров,
требующих production fix перед сдачей, в проверенном scope нет.
P9 не удостоверяет deployment readiness или полную профессиональную валидность ranking.

Допустимые конкурсные утверждения: реализованы и проверены hard filters/grade matrix,
Professional Fit45/25/15/15 и optional normalization; Ranking0.95×Fit+bonus0–5,
deterministic server sort/page, privacy preview и PR18 coherent/atomic regressions.
365 новых targeted PostgreSQL17 tests PASS и exact-main CI success можно указать
с отдельными denominators. Frozen synthetic dataset:8/36/288,38 eligible/250 excluded.
Сказать «Human-reviewed ranking quality подтверждено», привести NDCG/Top-k/Pairwise
или объявить AI proposals human labels нельзя.

Приоритет до дедлайна: независимый technical review Савы; реально передать blind packages
двум людям; раскрыть Backend-only Assessment, FSP mock, synthetic/proxy/independence
ограничения. Если подлинные бланки не поступили, сдавать с честным NOT STARTED.
После них только intake/hash/disagreement record и отдельный запрос Stage2 permission.

Публикация: documentation/evidence-only **Draft PR в main**, без merge/Ready transition.
Baseline freshness, staged allowlist, protected paths, git diff --check и status
проверяются до публикации; финальный head/PR URL подтверждаются в итоговом сообщении.
