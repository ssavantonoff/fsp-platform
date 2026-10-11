# P9-A0 — Final E2E & UI Audit

## 1. Baseline

| Поле | Значение |
|---|---|
| Repository | ssavantonoff/fsp-platform |
| Проверенный main SHA | `bce395a8c102491f4cf9ac26106b7263d08ad515` |
| Ветка аудита | `audit/p9-a0-final-e2e-ui` |
| Дата | 10 октября 2026, UTC; локальный часовой пояс Europe/Moscow |
| Environment | Изолированный Docker Compose project `fsp-p9-a0`, собственный PostgreSQL volume |
| Frontend / Backend | http://localhost:13200 / http://localhost:13201 |
| Browser | Настоящий Codex In-app Browser, управление через Computer Use; отдельный запуск Chromium не выполнялся |
| Viewports | 1440×1000, 768×1024, 375×812 |

Перед началом выполнены проверка чистоты, fetch и выделение отдельного worktree от origin/main. Основной checkout пользователя не переключался и не изменялся. Повторный fetch перед подготовкой отчёта подтвердил тот же main SHA.

Охват: реальные браузерные действия Candidate/Employer, frontend→backend интеграция, UI, приватность и демонстрация. Backend regression gate, профессиональная валидация Matching, human review и ranking metrics относятся к P9-B0 и здесь не выполнялись.

**PASS** ниже означает наблюдавшийся браузерный результат. Дополнительные API/SQL/source проверки обозначены отдельно. **FAIL** — воспроизведённый дефект; **GAP** — отсутствующая функция; **NOT TESTED** — непроверенная граница. Итог: **CONDITIONAL**, основной путь успешно пройден; P0/P1 в проверенных сценариях не обнаружены.

## 2. Environment Health

| Проверка | Результат / основание |
|---|---|
| Docker build / up | Успешно собраны frontend/backend и запущен отдельный Compose project |
| Frontend | Страницы доступны в браузере; контейнер healthy |
| Backend | `/health` возвращает 200 / `{"status":"ok"}`; контейнер healthy |
| PostgreSQL | 17.11, aarch64 alpine; контейнер healthy |
| Миграции | `c3d9b7e21a40 (head)` после автоматического Alembic upgrade |
| API proxy | `/api/skills` 200; все основные формы работали через same-origin proxy |
| Runtime | Docker Server 29.8.1; frontend Next.js 16.3.8 / React 19.3.0 по package.json |
| Outage / recovery | Остановлен только QA backend; браузер показал ошибку и «Повторить»; после start эта кнопка восстановила Needs и сессию |

Использована существующая `compose.yaml` с отдельными локальными портами и приватным env вне Git. `APP_ENV=test`, mail log backend; это не production deployment. SMTP доставка писем **NOT TESTED**: реальные тестовые verification links ведущий получил из приватного dev/test лога.

Существующий matching-demo seed выполнен один раз как подготовка синтетического пула. Seed qualification отделена от настоящих попыток. Volumes не удалялись, общая инфраструктура не отключалась.

Подготовительные действия вне браузера ограничены отдельным helper account для истёкшего email token и изменением expiry собственных QA auth sessions. Qualification, scoring, question bank и приглашения напрямую в БД не изменялись.

### Тестовые записи

- Новый Candidate: Алексей Тестовый / `p9.candidate@example.com`, masked name Алексей Т.; создан в UI.
- Новый Employer: P9 Audit Tech / `p9.employer@example.com`; создан в UI.
- Основная собственная Need: `9933fe48-6754-465e-a439-62838438d365`, Junior Backend Engineer — P9 ACCEPT; оставлена ACTIVE.
- Временная Need: `16f1ee33-4c8d-486e-90f7-1681a2f8e9e6`, Junior Backend Engineer — P9 DECLINE; после lifecycle оставлена CLOSED.
- Seed demo Need не закрывалась. Пароли, .env, cookies, session/verification tokens не включены в материалы.

## 3. Candidate E2E

| Сценарий | Status | Наблюдение |
|---|---|---|
| A1: главная → регистрация Candidate | PASS | Новый аккаунт создан через форму, навигация завершилась |
| Неверный email / короткий пароль | PASS | Реальный ввод блокируется browser validation |
| Повторная регистрация | PASS | Видно «Этот email уже зарегистрирован»; введённые данные не пропадают |
| Неверный пароль / последующий верный вход | PASS | Понятная ошибка; корректный вход после исправления |
| A2: новая verification link | PASS | Email подтверждён, URL fragment удалён, unverified banner исчез |
| Неверный / использованный / истёкший код | PASS | Понятное сообщение «Ссылка недействительна или срок истёк» |
| Новый fragment в уже открытой verify-email странице | FAIL | Код не загружается до reload; F01, P2 |
| SMTP доставка | NOT TESTED | Использован явно разрешённый dev log flow |
| A3: create / edit / reload profile | PASS | Имя, город, Backend, Senior declared, 2 года, навыки и consent сохраняются |
| Declared / verified distinction | PASS | Declared Senior показывается отдельно; реальный verified Junior появился только после PASS |
| Consent отсутствует | PASS | Assessment start недоступен, причина видна |
| Нет профиля | PASS | Assessment предлагает создать профиль, приложение не падает |
| FSP verify / unlink / повторный verify | PASS | MOCK-MULTI проверен UI; 3 достижения, bonus 5; unlink убрал текущий бонус, Junior сохранился; затем FSP восстановлен UI |
| A4: реальный Junior Assessment | PASS | 20 ответов отправлены через UI, результат 100/100, пять компетенций по 100% |
| Reload / timer / resume | PASS | Сохранённый ответ и выбор сохранились; время уменьшилось; активная попытка доступна через «Продолжить тест» |
| Active attempt start restriction | PASS | Новый запуск блокируется при активной попытке |
| Finish повторным нажатием | PASS | Double-click не создал повторное завершение; в истории одна Junior попытка |
| Успешный cooldown | PASS | Junior disabled до 08.01.2027 12:21:19 UTC, 90 дней |
| Неуспешная отдельная Middle попытка | PASS | Завершение без ответов через UI: 0/100; прежние Junior 100 и дата подтверждения сохранились |
| Неуспешный cooldown / итоговая history | PASS | Middle disabled до 17.10.2026 12:41:45 UTC, 7 дней; history содержит ровно две выполненные попытки |
| Ответные ключи в видимом quiz | PASS | Не показывались при прохождении; исходные answer keys не использовались и не экспортировались |
| Фактическое истечение 30 минут / auto-submit | NOT TESTED | Наблюдалось уменьшение timer; полного 30-минутного timeout не ожидали |
| Save ответа при outage / повторное сохранение | NOT TESTED | Outage проверялся на Needs/Account, не во время активного Assessment |
| A5: inbox / view / accept / separate decline | PASS | Оба предложения отображаются, зарплата доступна до ответа, terminal statuses сохраняются |
| A6: role / logout / reload / expired session | PASS | Candidate Employer-only route возвращает в Candidate; logout/expiry возвращает на login; reload сохраняет валидную сессию |
| Другой собственный synthetic Candidate | PASS | У Марии С. inbox пустой; два приглашения Алексея отсутствуют |
| Отдельная Candidate Category | GAP | Есть grade/score/specialization, отдельная category отсутствует |

Настоящая Junior попытка: `b36cf705-f67a-4a71-a5bf-269f50e3404a`, 12:17:49–12:21:19 UTC. Ответы выбирались по видимым заданиям и инженерному рассуждению; квалификация в БД вручную не присваивалась. Время этого технического прохождения не является обещанием длительности теста для нового пользователя.

Отдельная Middle попытка: `7bdafc47-9dea-4780-8b17-57275d93cbf5`, 12:41:06–12:41:45 UTC, намеренно без ответов для проверки failure boundary.

Доказательства: [Junior PASS](p9-a0-evidence/assessment-result.jpg), [Middle failure / сохранённый Junior](p9-a0-evidence/assessment-failed.jpg), [mobile profile](p9-a0-evidence/candidate-375.jpg), [browser journal](p9-a0-evidence/browser-checks.json).

## 4. Employer E2E

| Сценарий | Status | Наблюдение |
|---|---|---|
| B1: registration / email / login | PASS | Новый Employer зарегистрирован на 375px, email подтверждён |
| Company create / edit / reload | PASS | P9 Audit Tech, contact/site/описание сохранены; правка видна после reload |
| Пустой Needs list | PASS | Понятная кнопка создания, total 0 |
| B2: создание DRAFT | PASS | Position, specialization, grade, must/nice, experience, salary, description сохранены |
| Double-click create | PASS | Одна primary Need; всего создано две намеренные записи, два POST 201 по access log |
| Валидация Need | PASS | Пустые обязательные поля/skills, обратный диапазон, отрицательная зарплата/опыт блокируют submit; сообщения рядом с полями |
| B3: DRAFT edit / activate | PASS | Python must сохранён, статус ACTIVE, Matching link доступна |
| ACTIVE edit / refreshed results | PASS | Временный React must дал 0, после изменения на Python — 6 |
| ACTIVE → CLOSED | PASS | Закрыта только временная запись; native confirm подтверждён пользователем, результат проверен браузером |
| CLOSED edit / Matching | PASS | Read-only summary, нет сохранения; «Для закрытой потребности подбор недоступен» |
| Несуществующий ID | FAIL | Boundary защищена и есть возврат к списку, но heading/повтор ошибки неверны: F02, P3 |
| B4/B5 Matching / explanation | PASS | Карточки/порядок/score согласованы с API, раскрываются детали |
| B6/B7 invitations / contacts | PASS | SENT → VIEWED → ACCEPTED; отдельный DECLINED, unlock только после ACCEPTED |
| Employer Candidate-only route | PASS | Возврат на Employer profile |
| Истёкшая собственная session | PASS | После QA expiry + reload login; новый вход успешен |
| API временно недоступен | PASS | Ошибка без infinite loading; восстановление кнопкой «Повторить» |
| Пагинация на вторую страницу | NOT TESTED | Две Needs и шесть matches; disabled boundary проверена, второй страницы нет |

[Need form mobile](p9-a0-evidence/need-form-mobile.jpg), [not-found presentation](p9-a0-evidence/need-not-found.jpg), [API outage](p9-a0-evidence/api-outage.jpg).

## 5. Matching UI

Браузер и дополнительный proxy GET сравнивались на одном состоянии primary Need до unlink. При reload на 1440/768/375 порядок и отображаемые значения сохранились.

| # | Synthetic masked name | Professional Fit | Ranking Score | FSP Bonus |
|---|---|---|---|---|
| 1 | Алексей Т. | 100.0 | 100.0 | 5.0 |
| 2 | Денис С. | 92.5 | 87.9 | 0.0 |
| 3 | Ольга К. | 86.3 | 81.9 | 0.0 |
| 4 | Мария С. | 81.8 | 77.7 | 0.0 |
| 5 | Ирина О. | 78.0 | 74.1 | 0.0 |
| 6 | Павел М. | 66.8 | 63.4 | 0.0 |

Это серверные отображаемые числа, округлённые UI, без независимого пересчёта формулы и без оценки качества ranking. Seed кандидаты имеют synthetic qualification; только Алексей получил grade в реальной попытке этого аудита.

- **PASS:** specialization, verified grade, matched must/nice skills, total 6, masked names, Professional Fit, Ranking Score.
- **PASS:** общее объяснение Ranking V2 один раз над выдачей; индивидуальный вклад FSP у каждой карточки.
- **PASS:** открыты breakdown первой и Middle карточки; видны assessment/grade/skills/experience, отсутствующий SQL и «Допустимый более высокий уровень».
- **PASS:** после unlink следующий подбор временной Need показывал у Алексея FSP 0 / Ranking 95 при PF 100. Исторический snapshot первой invitation остался 5/100. После повторного UI verify primary выдача снова показала 5/100.
- **PASS:** отдельная пустая выдача 0 с советом проверить требования; после ACTIVE edit выдача 6.
- **PASS:** prev/next disabled при total 6 и limit 20.
- **NOT TESTED:** реальный переход между страницами при total > 20; не создавался дополнительный пул с искусственно выданной qualification.

Доказательства: [desktop](p9-a0-evidence/matching-1440.jpg), [mobile card](p9-a0-evidence/matching-mobile-card.jpg), [empty](p9-a0-evidence/matching-empty.jpg), [API/UI comparison](p9-a0-evidence/api-ui-comparison.json).

## 6. Invitations

| Проверка | Status | Результат |
|---|---|---|
| Send | PASS | Double-click отправки дал одну invitation; 201, «Приглашение отправлено» |
| SENT | PASS | Employer history и Candidate inbox показывают SENT, salary/message доступны |
| VIEWED | PASS | Открытие Candidate details обновило статус; Employer увидел «Просмотрено» |
| ACCEPTED | PASS | Double-click accept дал один успешный переход; повторных кнопок нет |
| DECLINED | PASS | Другой Need / другая invitation: double-click decline, статус сохранён и у Employer |
| Contacts SENT / VIEWED | PASS | Контактных секций нет в обеих проверенных ролях |
| Mutual unlock ACCEPTED | PASS | Candidate видит Employer contact/email/site; Employer — полное synthetic имя/email Candidate |
| Contacts DECLINED | PASS | В соответствующей карточке Candidate и Employer contacts отсутствуют |
| Historical FSP snapshot | PASS | После UI unlink Employer ACCEPTED history по-прежнему показывает FSP 5 / Ranking 100 / 3 участия |
| Reload / refresh | PASS | Статусы и contacts согласованы после роли/страницы/refresh |
| Withdrawal / third terminal action | NOT TESTED | Не относится к основному accept/decline gate, отдельно не проверялось |

IDs: ACCEPTED `44ea767b-9651-435d-889a-fe4dd77f3260`; DECLINED `3a53527d-2fa9-4df3-9cde-d30ab9571932`.

Приватность проверялась **внутри конкретной карточки**. Общая inbox страница может законно содержать контакты старой ACCEPTED invitation одновременно с закрытой DECLINED карточкой.

[Candidate ACCEPTED](p9-a0-evidence/candidate-accepted.jpg), [Employer contact + snapshot после unlink](p9-a0-evidence/employer-accepted-snapshot.jpg), [Employer DECLINED без контактов](p9-a0-evidence/employer-declined.jpg).

## 7. UI/UX

| Экран | 1440 | 768 | 375 | Наблюдение |
|---|---|---|---|---|
| Candidate profile | PASS | PASS | PASS | Grade/score/declared/skills раздельны, FSP MOCK notice виден |
| Needs list | PASS | PASS | PASS | Статусы/действия доступны, закрытая запись без edit/matches |
| Need form | PASS | PASS | PASS | Поля/validation доступны, min button height 49–51px |
| Matching / cards / breakdown | PASS | PASS | PASS | Нет горизонтального overflow, min button height 49–51px |
| Assessment attempt | PASS | PASS | PASS | Desktop отдельная Middle attempt, tablet/mobile Junior; question navigation buttons 44px |
| Candidate invitations | PASS | PASS | PASS | Salary/status/contacts читаемы, кнопки 49–51px |
| Employer invitations | PASS | PASS | PASS | Historical breakdown раскрывается; contacts доступны |

DOM `scrollWidth` равнялся ширине viewport в измеренных состояниях. Проверялись видимые страницы/карточки и сохранённые screenshots; это не exhaustive screenshot diff всего приложения.

Логотипы: официальный full вариант на desktop/tablet, compact на 375px. Оба SVG загружены; оригинальные материалы не менялись. В мобильных приглашениях основной текст15px, metadata14px; в desktop/tablet metadata местами12px.

Навигация основного пути выполнялась через существующие ссылки. Прямые URL использовались только для role/unknown-ID/error checks и повторного открытия известных страниц. Empty states позволяют продолжить, формы показывают success/error и блокируют повторную отправку.

Accessibility observations: семантические headings/labels, доступные названия question navigation, видимый focus outline при клавиатурной навигации; skip link меняет hash на main-content. Полный WCAG/контраст/screen-reader audit **NOT TESTED**. Mobile skill checkbox label около24.75px высоты: это наблюдение для улучшения удобства, не подтверждённый blocker.

UX observations, не новые функциональные дефекты:
- Главная предлагает создать профиль, но слабо объясняет механику «работодатель сам приглашает». Для новичка потребуется короткое объяснение ведущего.
- Mobile Matching имеет длинный блок требований до первой карточки; можно обсудить уменьшение высоты/сворачивание при отдельной UI задаче.
- Термины Professional Fit / Ranking V2 раскрыты, но более простое русское пояснение помогло бы первому визиту.
- Критических overlap, обрезанных кнопок, missing logo или horizontal overflow в проверенных состояниях не обнаружено.

## 8. Browser Console & Network

[Console capture](p9-a0-evidence/browser-console.json): доступный browser API вернул0 warn/error entries для audit tab. Это ограниченная запись инструмента, не доказательство отсутствия любых ошибок во всех браузерах.

[Sanitized access summary](p9-a0-evidence/network-summary.json) содержит методы, пути и статусы из изолированного Compose; включает health checks, setup и отдельное API/UI сравнение. Request/response bodies, cookies, tokens и raw logs не публикуются.

В снимке журнала: 200×568, 201×11, 204×10; ожидаемые 400×4,401×18,404×8,409×1,422×1.
- 400: неверные/использованные/истёкшие verification codes.
- 401: отсутствующая/истёкшая session и неверный login; часть retries связана с автоматизацией ввода до готовности формы.
- 404: ещё не созданный profile и заведомо несуществующая Need.
- 409: duplicate email.
- 422: helper fixture input validation при подготовке.
- Backend 5xx в этом access snapshot отсутствуют. Остановленный backend не пишет access log; UI outage соответствует proxy fallback 502 по read-only source, отдельный browser network waterfall для этого ответа не записан.

Во всех ожидаемых error boundaries пользователь увидел понятное состояние, без unhandled crash. F01 возникает до отправки нового кода: серверный token flow не сломан. F02 — presentation при корректном 404.

**NOT TESTED:** полный DevTools Network waterfall/HAR и response-body privacy audit, отдельная проверка каждого font request, Safari/Firefox/Android/iOS. Логотипы проверены фактической загрузкой и screenshots. CUA native confirm не управлялся автоматически: потребовалось нажатие пользователя; это ограничение инструмента, не дефект приложения.

## 9. Findings

### P0 / P1

Подтверждённых P0/P1 в проверенном браузерном охвате нет. Это не заменяет P9-B0 security/backend verification и не гарантирует отсутствие дефектов вне охвата.

### F01 — P2: новая verification link не обрабатывается на уже открытой странице

- SHA: `bce395a8c102491f4cf9ac26106b7263d08ad515`.
- Роль: Candidate/Employer; route `/verify-email`.
- Preconditions: страница уже смонтирована; есть свежая synthetic verification link.
- Repro: открыть verify-email без fragment → перейти в этой же вкладке на такую же страницу с новым verification fragment → проверить поле и URL → reload.
- Expected: новый код прочитан, поле обновлено и token fragment удалён.
- Actual: поле остаётся пустым/старым, fragment остаётся в URL; reload заполняет поле и удаляет fragment. Во время Candidate/Employer verification понадобился reload.
- Повторное безопасное воспроизведение выполнено с заведомо невалидным literal; screenshot не содержит действующего кода.
- Evidence: [empty form](p9-a0-evidence/verification-hash-navigation.jpg), journal `F01` / `F01-safe-reproduction`. Network: новый код не отправляется, console exception не наблюдалось.
- Read-only cause: `frontend/src/app/verify-email/page.tsx:14` читает hash только в mount effect.
- Минимальное предложение: обработать смену hash на смонтированной странице, очистить прежнюю ошибку/результат и удалить fragment; добавить regression для same-document navigation. Не менялись ни компонент, ни token contract.
- Workaround для показа: открыть ссылку в новой вкладке либо reload verify-email перед submit. Это P2 edge, нормальный fresh-load путь прошёл.

### F02 — P3: неверный heading и повтор ошибки для неизвестного Need

- SHA: тот же; роль Employer.
- URL: http://localhost:13200/employer/needs/00000000-0000-4000-8000-000000000000/edit
- Repro: войти Employer → открыть этот edit URL.
- Expected: однозначный not-found heading и одно сообщение, ссылка к списку.
- Actual: heading «Новая потребность» и два «Потребность не найдена». Form/save отсутствуют, возврат работает.
- Evidence: [screenshot](p9-a0-evidence/need-not-found.jpg), GET 404 × 2 в access summary; console exception не наблюдалось.
- Read-only cause: generic editor heading fallback + общий error и специальное сообщение, `employer-needs-screen.tsx:49,169`.
- Минимальное предложение: отдельный not-found heading и один error block. Без изменения backend 404/API.

Отдельное документационное наблюдение: README всё ещё упоминает 75 вопросов и прежний порядок Professional Fit, тогда как текущий Backend 120 и UI Ranking V2. Это не браузерная регрессия; исправление документации требует отдельного согласования.

## 10. Known MVP Gaps

| Возможность | Status | Фактическое состояние / риск демонстрации |
|---|---|---|
| Candidate Category | GAP | Отдельная category отсутствует; verified grade не следует выдавать за неё |
| Глобальный каталог кандидатов | GAP | Есть подбор по собственной ACTIVE Need |
| Прямое приглашение без Need | GAP | Отправка привязана к Need |
| Публикация вакансий / самостоятельные отклики | GAP | Не реализованы; не показывать job board механику |
| Регулярные задания работодателей | GAP | Не реализованы |
| Полные Frontend / DataML Assessment banks | GAP | JSON/approved publication отсутствуют; реальный показ только Backend 120, 40 на grade |
| Live FSP API / подтверждение владения настоящим ID | GAP | Только явно подписанный MOCK registry |
| Расширенная приватность | GAP | Есть consent и contact unlock после ACCEPTED; дополнительных настроек нет |
| PDF standardized profile | GAP | Экспорта нет |
| Chat / invitation email notifications | GAP | Inbox + ручное обновление, не messaging platform |
| Resend verification | GAP | Отдельного resend flow нет |
| SMTP delivery в QA | NOT TESTED | Adapter существует, но использован log backend |

Последние утверждения дополнены read-only проверкой текущих routes/models/question bank registry/docs. Им не присвоен browser PASS. Эти GAPs должны быть раскрыты жюри; соответствие официальному конкурсному scope требует продуктового решения.

## 11. Demonstration Readiness

### A. Полный показ — 25–50 минут

**Подготовка:** healthy изолированное окружение, свежие synthetic Candidate/Employer, приватный dev verification log у ведущего, свободный MOCK ID. Не показывать пароль или verification URL аудитории.

| Шаг / страница | Действие | Ожидаемый результат |
|---|---|---|
| Home → Register | Candidate registration, dev email link | Новый verified email account |
| Candidate → Edit | Backend, skills, experience, consent | Сохранённый профиль |
| Assessment | Junior, 20 вопросов, 30 минут; реальный submit | Настоящий score/history; grade только при PASS |
| Candidate | Показать qualification отдельно от declared | Подтверждённый уровень понятен |
| Candidate FSP | Сохранить свободный MOCK ID, проверить | Явно synthetic evidence, bonus |
| Register → Employer | Новый employer, verification, company | Собственный company profile |
| Needs → New | Junior, Python must, salary, description → DRAFT → ACTIVE | Собственная активная Need |
| Matching | Cards → «Почему такой результат» | Professional Fit / Ranking / FSP / навыки |
| Invite | Отправить сообщение, показать salary | SENT, contacts скрыты |
| Candidate inbox | Открыть → принять | VIEWED → ACCEPTED, employer contact |
| Employer invitations | Обновить / details | Candidate contact unlocked |

Этот путь фактически пройден на новых аккаунтах аудита с реальным Junior 100. Не гарантировать будущий PASS: нужны ≥70 в целом и ≥50% каждой компетенции. Если кандидат не проходит, показывать реальный failure/cooldown и переходить к явно обозначенному short fixture demo. Отдельного Candidate Category шага нет.

### B. Короткий показ — 6–9 минут (+1–2 для DECLINED)

Рекомендуемые подготовленные accounts этого аудита: Алексей / P9 Audit Tech. У Алексея **настоящая** Junior attempt/history этого аудита; MOCK-MULTI после unlink/snapshot проверки повторно verified через UI. Можно показывать текущую qualification/history, Matching primary Need, затем уже сохранённые SENT/VIEWED → ACCEPTED результаты и mutual contacts.

Для **повторного живого** send/accept нужна новая собственная ACTIVE Need: существующая primary invitation уже ACCEPTED, повторная отправка той же пары не является сбросом. Подготовить новую Need заранее или включить её создание в показ. Не закрывать canonical demo Need.

1. Candidate profile → настоящий Junior result/history → MOCK FSP notice.
2. Employer Needs → Matching → карточка / detailed explanation.
3. Новая demo Need → invitation: salary видна, контакты скрыты.
4. Candidate inbox → открыть → принять.
5. Employer history → contact unlock.
6. При наличии времени: отдельное предложение DECLINED и locked contacts; historical snapshot после unlink.

Альтернатива: existing matching-demo Employer `employer@example.com` / Мария С. `match-exact@example.com`, Middle Need. **Её qualification подготовлена seed и не является реальным Assessment прохождением.** Не подменять ею шаг настоящего тестирования.

### Риски / подготовка перед выходом к жюри

- Показ не полностью self-service в log-mail окружении; ведущий получает dev link. SMTP production delivery этим аудитом не подтверждена.
- F01: открывать verification ссылку новой вкладкой или reload.
- Истёкшие ссылки/cookies, занятый MOCK ID, уже terminal invitation могут нарушить повторяемость; перед показом проверить accounts и свежую Need.
- Re-seed не сбрасывает terminal invitations/Need edits/статусы/FSP. Не рассчитывать на него как на reset.
- Full Assessment занимает время и может FAILED; короткий заранее пройденный реальный путь надёжнее для ограниченного слота.
- Нет реального FSP, Category, Frontend/DataML banks, PDF и ряда официальных требований.
- Межстраничная pagination и 30 минут timeout не покрыты этим браузерным прогоном.
- Это оценка локального healthy окружения; deployed публичный endpoint не проверялся.

## 12. Evidence

Все материалы созданы на synthetic QA accounts. JPEG — реальные browser captures без изменения изображений. Никаких действующих verification links, password, cookies, ответных ключей или .env.

| Материал | Путь |
|---|---|
| Журнал браузерных действий, viewport measurements | [browser-checks.json](p9-a0-evidence/browser-checks.json) |
| Console capture (ограниченный) | [browser-console.json](p9-a0-evidence/browser-console.json) |
| HTTP methods/statuses, без raw logs/bodies | [network-summary.json](p9-a0-evidence/network-summary.json) |
| API сравнение с six browser cards | [api-ui-comparison.json](p9-a0-evidence/api-ui-comparison.json) |
| Реальная успешная attempt | [assessment-result.jpg](p9-a0-evidence/assessment-result.jpg) |
| Реальная неуспешная attempt, сохранённый Junior | [assessment-failed.jpg](p9-a0-evidence/assessment-failed.jpg) |
| Candidate mobile / официальное logo | [candidate-375.jpg](p9-a0-evidence/candidate-375.jpg) |
| Need form mobile | [need-form-mobile.jpg](p9-a0-evidence/need-form-mobile.jpg) |
| Matching desktop / mobile | [desktop](p9-a0-evidence/matching-1440.jpg), [mobile card](p9-a0-evidence/matching-mobile-card.jpg) |
| Empty Matching | [matching-empty.jpg](p9-a0-evidence/matching-empty.jpg) |
| Accepted mutual contacts / historical snapshot | [Candidate](p9-a0-evidence/candidate-accepted.jpg), [Employer](p9-a0-evidence/employer-accepted-snapshot.jpg) |
| Declined locked contacts | [employer-declined.jpg](p9-a0-evidence/employer-declined.jpg) |
| F01 safe empty verification form | [verification-hash-navigation.jpg](p9-a0-evidence/verification-hash-navigation.jpg) |
| F02 not-found presentation | [need-not-found.jpg](p9-a0-evidence/need-not-found.jpg) |
| Isolated API outage | [api-outage.jpg](p9-a0-evidence/api-outage.jpg) |

Git материалы только в `docs/qa/`. Production-код, SVG, цвета, frozen datasets, CI, миграции и вопросные банки не менялись. Implementation unit tests не добавлялись. Полный backend/frontend automated gate не повторялся: P9-B0 выделен отдельно. Для этой docs-only ветки проверены diff/scope, JSON parse, evidence links, отсутствие приватных значений и `git diff --check`.

## 13. Final Recommendation

**CONDITIONAL — основной локальный браузерный путь работает.**

Регистрация→qualification→Need→Matching→Invitation→ACCEPTED → mutual unlock подтверждены; отдельный DECLINED сохраняет приватность. В проверенном охвате нет подтверждённых P0/P1. Для подготовленного короткого показа есть рабочие accounts и настоящий Assessment результат.

Условия: раскрыть MOCK/MVP GAPs, подготовить свежую Need и ссылки, использовать workaround F01 или отдельно исправить его, получить P9-B0 результат. «Без риска сорвать» гарантировать нельзя: SMTP/deployment/timeout/pagination/другие браузеры не покрыты.

### Обязательная сводная матрица

| Scenario | Status | Evidence | Severity |
|----------|--------|----------|----------|
| Candidate Registration | PASS | A1 journal; реальная новая UI registration | — |
| Email Verification | FAIL | Fresh-load PASS; same-document F01; safe screenshot/journal | P2 |
| Candidate Profile | PASS | A3 journal; candidate-375.jpg | — |
| Assessment | PASS | Настоящие Junior 100 и Middle 0; history/cooldowns; timeout NOT TESTED | — |
| Verified Grade | PASS | После Junior PASS; сохранён после Middle FAIL | — |
| Employer Registration | PASS | B1 journal; UI registration/email | — |
| Employer Profile | PASS | B1 create/edit/reload journal | — |
| Create Need | PASS | B2 journal; form mobile; два намеренных POST 201 | — |
| Activate Need | PASS | B3 journal; ACTIVE card/matches | — |
| Matching | PASS | Six browser cards vs API; empty/edit refresh; page 2 NOT TESTED | — |
| Ranking Explanation | PASS | Browser first/Middle breakdown, missing SQL / higher grade | — |
| FSP Evidence | PASS | MOCK verify/unlink/reverify; historical snapshot | — |
| Send Invitation | PASS | Один POST 201 каждой пары; SENT/viewed journal | — |
| Candidate Invitation Inbox | PASS | Два собственных предложения, другой account empty | — |
| Accept Invitation | PASS | candidate-accepted.jpg; двойное нажатие | — |
| Decline Invitation | PASS | employer-declined.jpg; Candidate/Employer statuses | — |
| Contact Unlock | PASS | Mutual contacts ACCEPTED; absent SENT/VIEWED/DECLINED | — |
| Privacy | PASS | Role/logout/expiry/own inbox segregation; не полный security audit | — |
| Mobile UI | PASS | 375px measured/screenshots; полный device/WCAG audit NOT TESTED | — |
| Demo Readiness | PASS | Основные шаги браузером пройдены; рекомендация CONDITIONAL с указанными условиями | — |

### Ответы владельцу проекта

1. **Можно показывать подготовленный короткий путь**, но абсолютное отсутствие риска не подтверждено. Свежая Need, working accounts, healthy окружение и честные пояснения MOCK/dev email необходимы. Показ «без объяснений разработчика» сейчас ограничен email log flow и GAPs.
2. **Подтверждённых срочных P0/P1 исправлений нет.** До 11 октября желательно отдельно согласовать F01 (P2) как auth-flow edge. F02 (P3) можно отложить. Не внедрять fixes внутри этого аудита.
3. Стоит времени: F01 regression/fix, короткое объяснение employer-led механики и проверка demo rehearsal на целевом deployment. Небольшое упрощение mobile header можно обсуждать после этого. Отложить redesign, новые банки/category/FSPAPI/PDF/каталог/чат и изменения ranking: это отдельные продуктовые задачи.

**STOP FOR HUMAN REVIEW. Исправления не начаты, PR должен оставаться Draft, merge не выполняется.**
