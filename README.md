# FSP Platform

Технический фундамент хакатон-платформы: аккаунты кандидатов и работодателей,
подтверждение email, серверная авторизация, профили и справочник навыков.

## Стек и структура

Next.js 16.3.8 / React 19.3 / TypeScript / App Router / CSS;
Python 3.13+ / FastAPI / Pydantic 2 / SQLAlchemy 2 / Alembic;
PostgreSQL 17; Docker Compose.

```text
backend/
  app/routes/       HTTP endpoints и зависимости авторизации
  app/services/     операции авторизации и сохранения профилей
  app/models.py     SQLAlchemy-модели
  app/schemas.py    Pydantic-контракты чтения и записи
  app/mail.py       adapters: локальный журнал / SMTP
  app/seed.py       skills и необязательные demo-аккаунты
  alembic/          миграции схемы БД
  tests/            API, роли, владение, миграции и seed
frontend/
  src/app/          страницы и серверный /api proxy
  src/components/   формы и отображение профилей
  src/api.ts        единый клиентский API
  src/backend-proxy.ts      передача cookie и Origin в FastAPI
  tests/            Node tests API-клиента и proxy
compose.yaml
.env.example
.github/workflows/checks.yml
```

## Запуск через Docker Compose

Требуется работающий Docker Engine и Compose v2+. Порты 3000, 8000, 5432 должны
быть свободны. Команды выполняются из корня репозитория:

```sh
cp .env.example .env
# Перед запуском настройте пароли в .env для своей среды.
docker compose up --build -d --wait
# Skills и два demo-аккаунта:
docker compose exec backend python -m app.seed --demo
```

Backend применяет `alembic upgrade head` перед запуском API. Для создания только
skills используйте `docker compose exec backend python -m app.seed`.

- UI: <http://localhost:3000>
- API: <http://localhost:8000>
- Swagger: <http://localhost:8000/docs>
- OpenAPI: <http://localhost:8000/openapi.json>
- API/DB health: <http://localhost:8000/health>

Demo candidate: `candidate@example.com`; demo employer: `employer@example.com`.
Пароль — `DEMO_PASSWORD` в `.env` (в примере `local-demo-password`). Demo email
подтверждены. Candidate: Backend / заявленный Middle / Python, Django,
PostgreSQL / `verified_grade = null`. Seed можно повторять: существующие
аккаунты, профили и пароли сохраняются. Demo запрещены в production.

```sh
docker compose ps
docker compose logs -f backend
docker compose down
```

`down` сохраняет БД в volume. `docker compose down -v` **удаляет локальные данные**;
используйте только когда действительно нужна пустая БД.

## Подтверждение email

Development по умолчанию использует `MAIL_BACKEND=log`. После регистрации найдите
ссылку в приватном журнале backend:

```sh
docker compose logs backend
```

Откройте `http://localhost:3000/verify-email#token=...` и нажмите «Подтвердить».
Фрагмент удаляется из адресной строки после открытия формы; подтверждение
выполняется POST body, не GET. Токен хранится в БД только как SHA-256 hash,
истекает через час по умолчанию и атомарно используется только один раз.
API регистрации не возвращает токен. Истёкший, неверный и повторный token — HTTP 400.

Вход и профили доступны до подтверждения; UI показывает статус ожидания.
ТЗ первого этапа не требует блокировать эти действия до подтверждения email.

SMTP adapter подключается через `MAIL_BACKEND=smtp`, `SMTP_HOST`, `SMTP_FROM` и
остальные SMTP variables. Ошибка отправки откатывает регистрацию (HTTP 503),
запрос можно повторить. Другой mail provider может реализовать тот же
`VerificationMailer.send(email, token)` без изменения API.
Production-конфигурация требует HTTPS, `COOKIE_SECURE=true` и SMTP.
Очередь email и endpoint повторной отправки истёкшей ссылки пока не реализованы.

## Environment variables

Backend читает корневой `.env`, затем `.env` рабочей директории; environment
variables имеют приоритет. Frontend локально читает `frontend/.env.local`.
Compose передаёт переменные контейнерам явно.

| Переменная | Назначение / пример |
| --- | --- |
| `APP_ENV` | `development`, `test`, `production` |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | БД и credentials |
| `POSTGRES_PORT`, `BACKEND_PORT`, `FRONTEND_PORT` | `5432`, `8000`, `3000` |
| `DATABASE_URL` | SQLAlchemy URL; Compose использует host `postgres` |
| `FRONTEND_URL` | Публичный URL UI для verification links |
| `ALLOWED_ORIGINS` | JSON array: `["http://localhost:3000"]` |
| `COOKIE_SECURE` | `false` локально; `true` для HTTPS production |
| `SESSION_TTL_SECONDS` | `604800` (7 дней) |
| `VERIFICATION_TTL_SECONDS` | `3600` (час) |
| `MAIL_BACKEND` | `log` или `smtp` |
| `SMTP_HOST`, `SMTP_PORT` | SMTP host и порт (`587`) |
| `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` | SMTP credentials и отправитель |
| `SMTP_STARTTLS` | `true` для SMTP с STARTTLS |
| `DEMO_PASSWORD` | Пароль новых demo users, 10–128 символов |
| `API_INTERNAL_URL` | Server frontend → backend: локально `http://localhost:8000`, Compose `http://backend:8000` |
| `TEST_DATABASE_URL` | PostgreSQL для backend tests; без него временная SQLite |

При смене порта UI также измените `FRONTEND_URL` и `ALLOWED_ORIGINS`. Спецсимволы
пароля в SQLAlchemy URL нужно URL-encode; для локальной Compose-среды используйте
URL-safe пароль. `.env` не коммитится.

## Локальная разработка

Требуется Python 3.13+, Node.js 22+ и PostgreSQL. Можно запускать только БД в Docker:

```sh
cp .env.example .env
docker compose up -d postgres
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/python -m app.seed --demo
../.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Другой терминал, из корня:

```sh
cd frontend
cp .env.example .env.local
npm ci
npm run dev
```

Production frontend локально: `npm run build && npm start` из `frontend/`.

## Миграции

Ревизия `0001` создаёт `users`, `auth_sessions`, `email_verifications`,
`candidate_profiles`, `employer_profiles`, `skills`, `candidate_skills`.
Email и user_id профилей уникальны. Skills связаны many-to-many с составным PK.
Есть foreign keys с cascade delete, enum checks, ограничения опыта и
согласованности consent/timestamp. Для новой специализации расширяется enum и
check constraint отдельной миграцией. `create_all()` не используется.

```sh
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
docker compose exec backend alembic check
```

## API и права

| Метод | Путь | Назначение |
| --- | --- | --- |
| POST | `/auth/register` | email, password, role → User, HTTP 201 |
| POST | `/auth/verify-email` | token → HTTP 204 |
| POST | `/auth/login` | User + HttpOnly session cookie |
| POST | `/auth/logout` | Отзыв сессии и удаление cookie, HTTP 204 |
| GET | `/auth/me` | Текущий User |
| GET / POST / PUT | `/candidate/profile` | Свой профиль: read / create / replace |
| GET / POST / PUT | `/employer/profile` | Свой профиль компании |
| GET | `/skills` | Справочник skills |

PUT требует полный набор обязательных полей, nullable-поля очищаются `null`.
`skill_ids` заменяет список навыков; `[]` удаляет все связи.
Роль берётся из User в БД, а профиль выбирается по авторизованному user_id.
Endpoints для произвольного profile ID отсутствуют. Входные схемы запрещают
`verified_grade`, `user_id`, `role`, `personal_data_consent_at` (HTTP 422).
Заявленный уровень не копируется в подтверждённый. Consent timestamp задаётся
сервером при false→true, сохраняется при повторном true и очищается при отзыве.

Пароли — Argon2id. Random session tokens хранятся в БД только как hashes;
cookie — HttpOnly / SameSite=Lax, Secure в production. Сессии переживают restart
и отзываются при logout. LocalStorage не содержит authentication secrets.
Cookie-authenticated mutations требуют доверенный Origin; proxy сохраняет
исходный Origin. CLI с cookie тоже должен передавать Origin из `ALLOWED_ORIGINS`.
Без cookie CLI может не отправлять Origin; любой переданный недоверенный Origin
отклоняется. Для интерактивных mutation из Swagger локально добавьте
`http://localhost:8000` в `ALLOWED_ORIGINS` (по умолчанию разрешён только UI).

Ошибки: 400 token, 401 credentials/session, 403 role/Origin, 404 profile,
409 duplicate, 422 validation, 503 registration/delivery. Формат:

```json
{"error":{"code":"validation_error","message":"Проверьте заполнение полей.","fields":[{"field":"first_name","message":"Field required"}]}}
```

В ответах ошибок нет паролей, токенов и внутренних исключений. Для публичного
production deployment нужны HTTPS и отдельное решение по rate limiting.

## Проверки

В контейнере на PostgreSQL:

```sh
docker compose exec backend sh -c 'TEST_DATABASE_URL="$DATABASE_URL" pytest -q'
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .
docker compose exec backend mypy app
docker compose exec backend alembic check
```

Локально:

```sh
cd backend
../.venv/bin/pytest -q
TEST_DATABASE_URL=postgresql+psycopg://fsp:local-dev-change-me@localhost:5432/fsp ../.venv/bin/pytest -q
../.venv/bin/ruff check .
../.venv/bin/ruff format --check .
../.venv/bin/mypy app
cd ../frontend
npm run lint
npm run typecheck
npm test
npm run build
cd ..
git diff --check
```

PostgreSQL tests создают и удаляют собственные временные schemas `fsp_test_*`;
тестовый пользователь должен иметь CREATE SCHEMA. SQLite — быстрый вариант:
тест конкурентного token consumption выполняется только на PostgreSQL.
Каждый тест использует миграции; проверяются upgrade→downgrade→upgrade и
соответствие моделей схеме. Frontend tests используют встроенный Node test
runner через `tsx`, без отдельной тяжёлой инфраструктуры.

## Ручная проверка

1. Зарегистрируйте Candidate, повторите тот же email: появится ошибка.
2. Войдите, проверьте уведомление о неподтверждённом email. Подтвердите ссылку
   из backend log; повторное подтверждение той же ссылки должно дать ошибку.
3. Создайте профиль Backend / Middle со skills, FSP ID и consent. Профиль показывает
   отдельно заявленный Middle и «Подтверждённый уровень: не подтверждён».
4. Измените профиль и skills, перезагрузите страницу. `/employer` возвращает
   кандидата к своему профилю; `/employer/profile` API возвращает 403.
5. Выйдите, создайте Employer, заполните и измените компанию; candidate API даёт
   403. После logout профиль требует нового входа.
6. Проверьте узкий экран, required fields, disabled submit и ошибку с повтором
   при недоступном backend.

В scope фундамента (ТЗ №1) не входили тестирование кандидатов, matching, вакансии, invitations,
рейтинг, реальная ФСП-интеграция и административная панель.

## Candidate Assessment Engine

Доступно в `/candidate/assessment`; история — `/candidate/assessment/history`.
Тест запускается только явным POST после подтверждения правил. Нужны профиль
кандидата, подтверждённый email и согласие на обработку данных. Согласие проверяется
при старте: его отзыв не блокирует завершение уже начатой попытки или историю.

### Правила

- 20 вопросов `SINGLE_CHOICE`, 4 варианта, 1 правильный; 30 минут по серверному UTC.
- Пять компетенций Backend: программирование, HTTP/API, базы данных, архитектура,
  тестирование/безопасность/отладка.
- В каждой компетенции выбираются 1 BASIC + 2 APPLIED + 1 ADVANCED.
- Правильный ответ = 5 баллов; без ответа = 0; общая оценка 0–100.
- PASS: минимум 70/100 **и** минимум 50% (2 из 4 ответов) в каждом блоке.
- Неуспех: повтор через 7 дней; успех: через 90 дней для той же пары
  specialization + grade. Более высокий уровень доступен независимо от этого cooldown.
- Уровни ниже подтверждённого запрещены. Declared grade не влияет на баллы и допуск.
- Только одна активная попытка на кандидата. Паузы и продления таймера нет.
- Истёкшая попытка лениво финализируется при чтении, сохранении, submit,
  проверке доступности или новом старте. `finished_at = expires_at` для TIMEOUT;
  cooldown отсчитывается от этого срока, даже если тест был открыт позднее.
- Статусы: IN_PROGRESS / PASSED / FAILED; итоговая причина: SUBMITTED / TIMEOUT.
  Timeout может дать PASS при достаточном числе уже сохранённых верных ответов.
- Ответы сохраняются PUT сразу после выбора, их можно менять до завершения.
  При ошибке показан явный повтор; учитывается последний успешный серверный ответ.
- Submit идемпотентен, результат и verification сохраняются одной транзакцией.
  Мутации сначала блокируют профиль, затем попытку; partial unique index
  `uq_assessment_active_candidate` дополнительно запрещает второй IN_PROGRESS.

### Canonical verification и Matching

`CandidateProfile.verified_grade`, `normalized_assessment_score` (nullable int 0–100)
и `assessment_verified_at` (nullable UTC timestamp) — единый серверный контракт.
Либо все три поля NULL, либо все заполнены. CandidateWrite их не принимает.
Matching должен читать эти поля, не добавляя второй источник score или grade.

PASS на более высоком уровне повышает verification. Неуспех сохраняет её.
Успешная пересдача того же уровня заменяет score последним успешным результатом,
даже если он ниже прежнего. При смене specialization сервис берёт самый высокий
успешный grade по новой specialization и последнюю успешную попытку этого grade;
при отсутствии истории очищает три поля. Возврат к прежней specialization
восстанавливает её verification. История сохраняется; срок действия verification
не ограничен. Во время IN_PROGRESS смена specialization запрещена; остальные
поля профиля доступны для редактирования.

### Модели и API

`AssessmentQuestion` хранит код, specialization, grade, competency, difficulty,
текст, version и is_active. `AssessmentOption` содержит текст и закрытый is_correct.
`AssessmentAttempt` фиксирует specialization/grade, сроки и итоговый breakdown.
`AssessmentAttemptQuestion` фиксирует 20 вопросов, позиции, перемешанный порядок
вариантов и сохранённый ответ. Набор и порядок не регенерируются при reload.
Связи загружаются пакетно через selectin; цикла запросов по каждому вопросу нет.

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/candidate/assessments/availability` | Карточки уровней, причина отказа, available_at, active_attempt_id, verification и server_now |
| POST | `/candidate/assessments` | Только `{ "target_grade": "MIDDLE" }`, возвращает новую попытку |
| GET | `/candidate/assessments/current` | Активная попытка; 404, если её нет |
| GET | `/candidate/assessments/{attempt_id}` | Только собственная попытка |
| PUT | `/candidate/assessments/{attempt_id}/answers/{attempt_question_id}` | Только `{ "selected_option_id": "…" }` |
| POST | `/candidate/assessments/{attempt_id}/submit` | Завершение или существующий результат |
| GET | `/candidate/assessments/history` | Попытки по started_at DESC, включая итог и breakdown |

Ответ попытки содержит server_now/expires_at для таймера и текущую verification.
История использует поле `id` как attempt ID. Завершённая попытка возвращает пустой
массив questions: только агрегаты без разбора правильных вариантов.
Правильные ответы, is_correct, solution и explanations не выдаются кандидату.
Чужая попытка — 404; employer — 403; без сессии — 401.
Все мутации используют существующую проверку доверенного Origin.

Стабильные error codes: `email_not_verified`, `consent_required`,
`assessment_unavailable`, `assessment_in_progress`, `assessment_grade_not_allowed`,
`assessment_cooldown`, `assessment_finished`, `question_not_in_attempt`,
`option_not_in_question`, `assessment_not_found`, `profile_not_found`.
Ошибки используют общий `{ "error": { "code", "message", "fields" } }` формат.
Availability reasons: EMAIL_NOT_VERIFIED, CONSENT_REQUIRED, IN_PROGRESS,
LOWER_THAN_VERIFIED, UNAVAILABLE, COOLDOWN; null означает доступный уровень.

### Банк и seed

`backend/app/content/backend_questions.json`: 75 русских demo-вопросов BACKEND —
25 Junior, 25 Middle, 25 Senior. По каждой компетенции/grade: 1 BASIC + 3 APPLIED +
1 ADVANCED. FRONTEND и DATA_ML поддержаны в моделях и конфигурации компетенций,
но пока без банка: старт возвращает `assessment_unavailable`.

Обе существующие команды теперь заполняют вопросы:

```bash
docker compose exec backend python -m app.seed
docker compose exec backend python -m app.seed --demo
```

Seed идемпотентен и проверяет четыре разных непустых варианта и один правильный.
Он не изменяет вопросы с прежним code и сохраняет ручное is_active=false.
Несовпадение содержания вызывает ошибку с требованием нового version/code;
исторические вопросы нельзя удалять или изменять. Контент хранит явные
code/version; supersedes деактивирует прежний вопрос, сохраняя его и историю. Новая версия добавляется новым
кодом, прежнюю можно деактивировать. Demo candidate автоматически не получает
verification: локальное подтверждение появляется только после успешного теста.

При проверке технических формулировок использованы первичные справочники:
[HTTP Semantics (RFC 9110)](https://www.rfc-editor.org/rfc/rfc9110.html),
[PostgreSQL Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html),
[Python asyncio tasks](https://docs.python.org/3/library/asyncio-task.html).
Банк является demo-контентом; runtime LLM отсутствует.

### Миграция 0002

`0001` не изменена. `0002_assessment_engine` добавляет четыре таблицы, два поля
профиля, ограничения consistency/score и partial unique index активных попыток.
При upgrade старый `verified_grade` без score/assessment date сбрасывается в NULL:
его невозможно считать подтверждённым assessment без доказательства. Остальные
поля и сами профили сохранены. Score/date для прежних профилей остаются NULL.
Downgrade удаляет assessment-таблицы и новые поля; история будет потеряна при
явном downgrade, а прежний grade остаётся колонкой схемы 0001. Re-upgrade снова
сбрасывает grade без assessment evidence. Перед downgrade нужен обычный backup БД.

Автотесты проходят переходы 0001→0002→0001→0002, сохранение профиля, сброс
неполного legacy verification и `alembic check`.

### Ручная проверка assessment

1. Выполнить миграции и seed; войти demo candidate либо новым candidate.
2. Для нового candidate проверить запрет старта без профиля/email/consent;
   подтвердить email существующим потоком и дать согласие в профиле.
3. Открыть `/candidate/assessment`, выбрать Backend / Middle и прочитать правила.
4. Нажать «Начать тест»: 20 вопросов, 30:00; второй старт запрещён.
5. Выбрать ответ, увидеть «Ответ сохранён», перейти назад/вперёд и через номера.
6. Reload: те же вопросы, порядок вариантов и ответы, таймер продолжает идти.
7. Во время теста сменить declared grade: разрешено. Смена specialization: отказ.
8. Отключить backend, выбрать ответ: ошибка сохранения, успешный статус не показан.
   Включить backend и нажать «Повторить сохранение».
9. На последнем вопросе проверить подтверждение и предупреждение о пропусках.
10. Завершить PASS: проверить score, пять процентов, профиль и историю; Junior
    запрещён, Middle на cooldown, Senior доступен. FAILED не понижает verification.
11. На ширине 375 px проверить перенос вариантов/номеров, читаемый timer и кнопки.
12. Для проверки timeout в отдельной тестовой БД дождаться срока или изменить
    expires_at на прошедшее: GET/PUT/submit финализируют сохранённые ответы,
    последующие ответы запрещены. Смена specialization очищает/восстанавливает
    verification согласно истории.
