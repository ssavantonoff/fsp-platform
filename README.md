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

## Employer Needs & Matching

Backend API для собственных потребностей работодателя и текущего подбора кандидатов.
Employer UI доступен в `/employer/needs`; Invitations пока не реализованы.
Используются существующие session cookies и справочник `/skills`; отдельного auth
или skill catalog нет.

### Endpoints, права и контракт

| Метод | Endpoint | Результат |
|---|---|---|
| GET | `/employer/needs` | Свои Needs, `{items, total, limit, offset}` |
| POST | `/employer/needs` | Создать DRAFT, HTTP 201 |
| GET | `/employer/needs/{need_id}` | Свой Need, HTTP 200 |
| PUT | `/employer/needs/{need_id}` | Полностью заменить editable fields, HTTP 200 |
| POST | `/employer/needs/{need_id}/activate` | DRAFT → ACTIVE, HTTP 200 |
| POST | `/employer/needs/{need_id}/close` | ACTIVE → CLOSED, HTTP 200 |
| GET | `/employer/needs/{need_id}/matches` | Текущий matching, `{items, total, limit, offset}` |

Все семь endpoints требуют роль EMPLOYER. Без session — 401, Candidate — 403.
Работодатель работает только со своими Needs: чужой и отсутствующий ID одинаково
возвращают `404 need_not_found`; без employer profile — `404 profile_not_found`.
Четыре mutation endpoints (create, PUT, activate, close) требуют trusted Origin
через существующую cookie-auth CSRF protection. GET endpoints read-only; matching
не меняет БД и не финализирует assessment attempts. Ответы имеют `Cache-Control: no-store`.

Create/PUT принимают `position_title`, `specialization`, `required_grade`,
`target_experience_years` (nullable), `salary_from`, `salary_to`, `description`,
`additional_requirements` (nullable), `must_have_skill_ids`, `nice_to_have_skill_ids`.
Owner и status определяются сервером; передавать их или calculated fields нельзя.
Заголовок/описание непустые; salary — конечные неотрицательные Decimal с максимум
12 цифрами и 2 знаками после точки, from ≤ to. В JSON ответа salary — строки.
Target experience конечный и неотрицательный либо null. Требуется хотя бы один
must-have; IDs из существующего каталога, без duplicates и пересечения must/nice.
PUT заменяет и scalar fields, и обе skill lists атомарно.

NeedOut содержит `id`, `employer_id`, scalar fields, `status`, `created_at`,
`updated_at`, `must_have_skills` и `nice_to_have_skills` в формате `{id, name}`.
Неизвестный skill — `422 unknown_skill`, неверный input/query — `422 validation_error`,
недопустимое состояние — `409 need_state_conflict`, ошибка сохранения — `409 need_conflict`.
Ошибки используют существующий `{error: {code, message, fields}}` envelope.
Для list/matches: limit по умолчанию 20, диапазон 1–100, offset ≥0.
List сортируется по created_at DESC, затем id ASC; total не равен размеру страницы.

### Lifecycle и live recalculation

| Status | Edit | Activate | Close | Matching |
|---|---|---|---|---|
| DRAFT | Да | Да | Нет | Недоступен, 409 |
| ACTIVE | Да | Нет | Да | Доступен |
| CLOSED | Нет, 409 | Нет | Нет | Недоступен, 409 |

Единственная цепочка: DRAFT → ACTIVE → CLOSED. Reopen нет; повтор неподходящего
transition возвращает 409. После закрытия сохраняются прежние поля и связи.

ACTIVE Need можно редактировать. Следующий GET `/employer/needs/{need_id}/matches`
после успешного commit читает актуальные committed criteria и заново вычисляет
eligibility, score и ranking. Ranking не сохраняется в таблице или cache.
Каждый invocation захватывает immutable criteria одним согласованным чтением;
matching A, уже захвативший criteria, может завершиться по прежним значениям,
пока update успешно коммитится. Следующий invocation видит новые criteria;
rollback сохраняет прежние. Это in-memory input одной операции, не persisted snapshot.
Matching GET не берёт mutation row lock; update/activate/close сохраняют свои locks.

### Hard filters и grade matrix

Перед scoring обязательны consent=true, exact specialization, canonical verified
grade, совместимость grade, все must-have skills и валидный normalized assessment
score (integer 0–100). Высокий score не компенсирует отказ hard filter.
Declared grade, FSP и recency verification date не участвуют в eligibility или rank.

| Required grade | Verified JUNIOR | Verified MIDDLE | Verified SENIOR |
|---|---|---|---|
| JUNIOR | GradeFit 1.0 | GradeFit 0.75 | Excluded |
| MIDDLE | Excluded | GradeFit 1.0 | GradeFit 0.75 |
| SENIOR | Excluded | Excluded | GradeFit 1.0 |

### Professional Fit

«Соответствие / Professional Fit» — детерминированный score 0–100 с объяснимыми
вкладами, не probability или шанс найма. Frozen base weights:

| Factor | Weight | Fit |
|---|---|---|
| Assessment | 45% | normalized_assessment_score / 100 |
| Grade | 25% | 1.0 exact, 0.75 allowed overqualified |
| Nice-to-have | 15% | matched nice / total nice |
| Experience | 15% | min(candidate experience / target, 1) для positive target |

Если nice list пуст, Nice factor исключается. Если target experience=null,
Experience factor исключается. Оставшиеся active weights пропорционально
renormalized до 100%; breakdown возвращает фактические `score`, `max`, `active`.
Target=0 даёт ExperienceFit=1 даже при candidate experience=null. При positive
target и отсутствующем опыте factor **активен**, Fit=0 и contribution=0.

Сортировка серверная: unrounded Professional Fit DESC, normalized assessment score
DESC, stable candidate_id ASC. Pagination применяется после полного ranking.
Frontend должен сохранять серверный порядок; округление для отображения не меняет rank.

### Privacy-safe preview

Matching отдаёт только dedicated preview: `candidate_id`, masked `display_name`
(имя и инициал фамилии), specialization, verified grade, **self-declared skills**
(навыки, указанные кандидатом), years of experience, normalized assessment score,
assessment verification date, Professional Fit, factor breakdown и списки
matched must-have, matched nice-to-have, missing nice-to-have. Skills не объявляются
verified. Grade breakdown также содержит `exact_match`, Nice — `matched` и `total`.

Preview не раскрывает email, phone, Telegram, полную фамилию, user_id, personal
consent fields, FSP ID, city/address, about, declared grade, assessment history
или контакты. Verification date только отображается, не влияет на score/rank.
Контакты в O1 не разблокируются; будущий accepted Invitation не реализован здесь.

### Explicit matching demo

```sh
docker compose exec backend python -m app.seed --matching-demo
```

Команда включает base identities `candidate@example.com` / `employer@example.com`,
три Needs с фиксированными IDs и девять synthetic Matching candidates. Используется
тот же `DEMO_PASSWORD` (10–128 символов); оба demo modes запрещены в production
до открытия seed session. Обычный `--demo` по-прежнему создаёт только base identities
и сохраняет base candidate unverified; он не создаёт Needs или Matching candidates.
Комбинация `--demo --matching-demo` также допустима.

Matching demo **create-if-absent**: повторные запуски не сбрасывают existing users,
password hashes, verification, profiles, skills или Need edits/status/relations.
Identity key кандидата — фиксированный email, Need — фиксированный ID. Несовместимая
роль existing matching user вызывает fixture conflict вместо смены роли.
Для полного локального reset удаляют DB volume отдельной командой, описанной выше;
matching seed не является reset command.

Matching candidates — synthetic fixtures. Их canonical verification trio заполнено
напрямую для проверки Matching boundary с фиксированной датой `2026-10-05T12:00:00Z`.
Они не созданы из AssessmentAttempt history; seed не создаёт и не меняет attempts.
Полный production question bank сейчас только Backend. Frontend fixture существует
только как negative specialization case; она не проходила настоящий Frontend assessment.

| Fixed Need ID | Setup | Status |
|---|---|---|
| demo-need-backend-middle-active | Backend/Middle, must Python + FastAPI, nice PostgreSQL + Django, target 3 | ACTIVE |
| demo-need-backend-junior-draft | Backend/Junior, must Python, nice FastAPI + PostgreSQL, target 1 | DRAFT |
| demo-need-backend-senior-closed | Backend/Senior, must Python + PostgreSQL, nice FastAPI + Django, target 7 | CLOSED |

На чистом demo ACTIVE Need имеет ровно четыре eligible candidates:

| Case | Assessment | Outcome / Professional Fit |
|---|---:|---|
| Exact Middle, оба nice, experience 3 | 90 | #1, **95.5** |
| Overqualified Senior, оба nice, experience 3 | 100 | #2, **93.75** |
| Middle, без Django, experience 1.5 | 90 | Eligible, 80.5 |
| Middle, оба nice, experience=null | 90 | Eligible, 80.5; Experience contribution=0 |
| Junior для Middle Need | 100 | Excluded: grade |
| Middle без FastAPI | 100 | Excluded: must-have |
| Unverified, canonical trio all-null | — | Excluded: verification/score |
| Middle без consent | 100 | Excluded: consent |
| Frontend Middle | 100 | Excluded: specialization |

Exact Middle/90 выше Senior/100 из-за соответствия requested grade; высокий
assessment score сам по себе не гарантирует первое место. Два результата 80.5
упорядочиваются по candidate_id, их взаимный порядок не является demo oracle.
Base candidate также исключён. После пользовательских edits результаты могут
измениться; повторный seed сохраняет эти edits.


### Employer UI manual flow

1. В запущенной локальной среде выполните
   `docker compose exec backend python -m app.seed --matching-demo`.
   Повторный seed сохраняет существующие edits и статусы.
2. Войдите как `employer@example.com` с настроенным `DEMO_PASSWORD` и откройте
   `/employer/needs`. При отсутствии профиля сначала заполните `/employer/edit`.
3. У ACTIVE «Backend Python Engineer» нажмите «Подбор кандидатов».
   В чистом demo total равен 4: первая Мария С. (Middle, оценка 90, соответствие
   95.5), второй Алексей В. (Senior, оценка 100, точный backend score 93.75,
   в UI **93.8**). Два оставшихся результата имеют 80.5; их взаимный порядок
   не является продуктовым oracle. Пагинация использует серверные limit/offset.
4. Раскройте «Почему такой результат». Для Марии отображаются 40.5 / 45.0,
   25.0 / 25.0, 15.0 / 15.0, 15.0 / 15.0. Проверьте дату подтверждения,
   совпавшие обязательные/желательные навыки и отсутствующий Django у кандидата
   с неполным nice-набором. Неактивные факторы исключены; активный нулевой
   вклад опыта отображается как 0.0 / 15.0.
5. Для проверки создания/редактирования используйте отдельную временную
   потребность: «Новая потребность», заполните обязательные поля и навыки,
   сохраните DRAFT, отредактируйте и активируйте в списке. Откройте подбор,
   запомните результаты, перейдите в «Редактировать потребность», измените
   желательные навыки или целевой опыт и сохраните ACTIVE. Вернитесь через
   список к подбору: новый GET отражает сохранённые требования.
6. Закрывайте только временную потребность: CLOSED нельзя редактировать,
   а прямые `/employer/needs/{id}/matches` для DRAFT/CLOSED показывают блокировку.
   Не закрывайте canonical ACTIVE demo: seed его не переоткроет.
7. На ширине 375px проверьте перенос заголовков/навыков и раскрытый breakdown
   без горизонтальной прокрутки. При ошибке отображается «Повторить», повторная
   загрузка проверяет актуальный Need. Для пустого pool показывается отдельное
   сообщение; переходы страниц не показывают старый ranking как текущий.
8. Без авторизации страница перенаправляет на `/login`, Candidate — на
   `/candidate`. В карточках и `/matches` response нет контактов, полной фамилии,
   FSP ID и invitation actions: используются только разрешённые preview fields.

Frontend не вычисляет и не переупорядочивает matching: Professional Fit —
серверный детерминированный показатель соответствия требованиям, не вероятность
найма. Округление до одной цифры применяется только при отображении. Навыки и
опыт указаны кандидатом; дата подтверждения компетенции носит информационный
характер. Контакты в O1 не раскрываются. Ranking хранится только в состоянии
страницы и заново запрашивается при возвращении после редактирования.
