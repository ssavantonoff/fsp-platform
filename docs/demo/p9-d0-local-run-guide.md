# P9-D0 — Воспроизводимый локальный запуск

Repository: [ssavantonoff/fsp-platform](https://github.com/ssavantonoff/fsp-platform) (private).
Baseline: `bce395a8c102491f4cf9ac26106b7263d08ad515`.
Дата: 10 октября 2026 (Europe/Moscow).

**Commands verified:** исходники и ограниченный Docker/HTTP запуск P9-D0 — VERIFIED
на каноническом LF-экспорте exact baseline. Обычный Windows checkout с CRLF — seed FAILED,
описан ниже. **Запуск на MacBook, его preflight и настоящий результат теста капитана — NOT VERIFIED.**
Видео: **VIDEO STATUS: PENDING RECORDING BY TEAM CAPTAIN**.

## 1. Зависимости и изоляция

- Git с разрешённым чтением приватного репозитория, терминал и браузер.
- Работающий Docker Engine и Docker Compose v2 с поддержкой `up --wait`.
  На MacBook можно использовать установленный Docker Desktop; контейнеры Linux.
- Для первичной сборки нужен интернет к Docker/package registries. Первая сборка может
  занять 5–15 минут или дольше в зависимости от сети. Это оценка, не обещание.
- Порты 3000/8000/5432 свободны. Приложение привязано к loopback в Compose, это локальный запуск.
- Python/Node/PostgreSQL на хост устанавливать для Docker-пути не требуется:
  Dockerfile использует Python 3.13-slim и Node 22-alpine, Compose — PostgreSQL 17-alpine.
  Native development из README требует Python 3.13+, Node 22+, PostgreSQL.

```sh
git --version
docker --version
docker compose version
docker info
```

Команды ниже для macOS shell. Выполнять последовательно; если команда завершилась с ошибкой,
не считать следующие этапы готовыми. Не использовать существующие QA/manual directories,
их контейнеры, пароли или volumes. Compose project `fsp-p9-d0-demo` должен быть новым:

```sh
docker compose ls
```

Если имя занято другой средой, выбрать другое уникальное имя и заменить его **во всех командах**.
Существующую среду не останавливать. Без флага `-p` Compose может выбрать другое имя проекта.

## 2. Клонирование и точный baseline

В каталоге, где ещё нет `fsp-platform-demo`:

```sh
git clone https://github.com/ssavantonoff/fsp-platform.git fsp-platform-demo
cd fsp-platform-demo
git checkout bce395a8c102491f4cf9ac26106b7263d08ad515
git rev-parse HEAD
git status --short
```

HEAD должен совпасть с SHA выше, tracked working tree — чистый. Detached HEAD здесь ожидаем:
эксперт запускает конкретную версию, не разрабатывает изменения. GitHub/main проверен
в P9-D0 через `git ls-remote origin refs/heads/main` и совпадал с этим SHA.
Если main позже изменится, этот сценарий остаётся проверенным для закреплённого baseline;
не заменять SHA без оценки влияния изменений.

## 3. Настройка `.env` только из шаблона

В новой копии, где `.env` ещё нет:

```sh
cp .env.example .env
```

Открыть **свой новый** `.env` локально в редакторе и настроить:

| Переменная существующего шаблона | Локальное значение / действие |
|---|---|
| `APP_ENV` | `development`; demo seed запрещён при `production` |
| `POSTGRES_DB`, `POSTGRES_USER` | `fsp`, `fsp` для новой БД |
| `POSTGRES_PASSWORD` | Собственный URL-safe пароль для новой БД; не публиковать |
| `DATABASE_URL` | Сохранить формат шаблона, согласовать пароль и host-порт для native запуска; Docker backend получает URL от Compose с host `postgres` и внутренним портом 5432 |
| `DEMO_PASSWORD` | Собственный пароль новых demo accounts, 10–128 символов; не публиковать |
| `POSTGRES_PORT`, `BACKEND_PORT`, `FRONTEND_PORT` | 5432, 8000, 3000, если свободны |
| `FRONTEND_URL` | `http://localhost:3000` |
| `ALLOWED_ORIGINS` | `["http://localhost:3000"]`, корректный JSON array |
| `COOKIE_SECURE` | `false` для локального HTTP |
| `MAIL_BACKEND` | `log` для локальных синтетических регистраций |

`API_INTERNAL_URL=http://backend:8000` уже задаётся frontend в Compose.
Не менять его на host-порт. SMTP-поля для `MAIL_BACKEND=log` не нужны.
Оставить остальные значения шаблона. Не показывать `.env`, `docker compose config`
или полный environment в записи: они могут раскрыть пароли.

Если порты заняты, выбрать свободные, например:

| Переменная | Пример отдельной среды |
|---|---|
| `FRONTEND_PORT` | 13010 |
| `BACKEND_PORT` | 18080 |
| `POSTGRES_PORT` | 55442 |
| `FRONTEND_URL` | `http://localhost:13010` |
| `ALLOWED_ORIGINS` | `["http://localhost:13010"]` |

Тогда все UI URL/Origin в сценарии используют 13010, health — 18080; для native
`DATABASE_URL` согласовать 55442. Пример проверен P9-D0; доступность этих портов на MacBook
нужно проверить отдельно. Вход по `127.0.0.1` вместо `localhost` меняет Origin — использовать
ровно настроенный адрес. Не отключать Origin protection ради Swagger/демо.

## 4. Запуск, миграции и demo seed

Из корня новой копии, после настройки `.env`:

```sh
docker compose -p fsp-p9-d0-demo up --build -d --wait
```

Compose ждёт healthy PostgreSQL/backend/frontend. Backend автоматически выполняет
`alembic upgrade head` перед uvicorn. Явная команда повторно применяет только необходимые
существующие миграции и позволяет проверить ревизию:

```sh
docker compose -p fsp-p9-d0-demo exec backend alembic upgrade head
docker compose -p fsp-p9-d0-demo exec backend alembic current
```

Ожидаемый head для этого baseline: `c3d9b7e21a40 (head)`.

```sh
docker compose -p fsp-p9-d0-demo exec backend python -m app.seed --demo
docker compose -p fsp-p9-d0-demo exec backend python -m app.seed --matching-demo
```

Обе должны закончиться `Seed completed.`. Используется один существующий module `app.seed`;
отдельного `seed_matching_demo.py` нет. Seed также публикует зарегистрированный банк вопросов
и навыки. Повторный seed сохраняет существующие аккаунты, профили и пароли: изменение
`DEMO_PASSWORD` в `.env` не меняет пароль уже созданного аккаунта. Это не сброс данных.

### Если seed отказал из-за перевода строк

P9-D0 воспроизвёл на Windows с `core.autocrlf=true`:
`ValueError: Assessment source differs from reviewed content`. Контейнеры могли оставаться
healthy, но skills/accounts отсутствовали. Это **не успешный demo startup**.
`backend_questions.json` в checkout SHA256
`146904321bc170382bfc3c22a6d4345ca7d8d657c76323f4c4cc6f02d8e206d4`;
проверенный Git LF content SHA256
`76cda12d6358f14da84cce0ac584035ab189ae7a2f43e18d1e3cfed41276023c`.
Причина установлена сравнением bytes и publication registry; не менять reviewed hash.

Безопасный обход: экспортировать **тот же SHA** в новый собственный каталог с LF,
не меняя tracked checkout, постоянный Git config или frozen-файлы. Даже `git archive`
при включённом autocrlf может менять bytes, поэтому override обязателен для этой команды.

macOS shell, из корня своей новой копии, если путь `.cache/p9-d0-lf` ещё не существует:

```sh
mkdir -p .cache
mkdir .cache/p9-d0-lf
git -c core.autocrlf=false archive --format=tar --output=.cache/p9-d0-lf.tar bce395a8c102491f4cf9ac26106b7263d08ad515
tar -xf .cache/p9-d0-lf.tar -C .cache/p9-d0-lf
cp .env .cache/p9-d0-lf/.env
cd .cache/p9-d0-lf
docker compose -p fsp-p9-d0-demo up --build -d --wait
docker compose -p fsp-p9-d0-demo exec backend alembic current
docker compose -p fsp-p9-d0-demo exec backend python -m app.seed --demo
docker compose -p fsp-p9-d0-demo exec backend python -m app.seed --matching-demo
```

Продолжать команды Compose из этого LF-каталога с тем же `-p`; volume сохраняется.
Если каталог уже существует, выбрать новый собственный путь, не перезаписывать чужой.
В P9-D0 проверен эквивалент с явным `-f <LF-export>/compose.yaml` и приватным `--env-file`:
обе seed-команды PASS. macOS native clone без преобразования строк отдельно не запускался.
Если ошибка сохраняется или отличается, остановиться и передать точный текст техническому
участнику; не нормализовать JSON вручную и не обходить publication gate.

## 5. Health и адреса

```sh
docker compose -p fsp-p9-d0-demo ps
docker compose -p fsp-p9-d0-demo exec postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
curl --fail http://localhost:8000/health
curl --fail http://localhost:3000/api/skills
```

Ожидаются три healthy services, accepting connections, `{"status":"ok"}` и 7 seed skills.
SQL-проверка работает **в своём** postgres container и не выводит пароль.
API health выполняет DB query; сам healthy не доказывает успешность seed или полноценного демо.

| Назначение | URL при стандартных портах |
|---|---|
| Frontend | http://localhost:3000/ |
| Вход / регистрация | http://localhost:3000/login / http://localhost:3000/register |
| Backend API | http://localhost:8000 |
| Swagger / OpenAPI | http://localhost:8000/docs / http://localhost:8000/openapi.json |
| Проверка API + БД | http://localhost:8000/health |
| Same-origin proxy | http://localhost:3000/api/skills |

Из Swagger по умолчанию не выполнять cookie-authenticated mutations: разрешён UI Origin,
а Swagger расположен на backend Origin. Для демонстрации использовать UI.

## 6. Вход и состояние демонстрационных данных

| Аккаунт после seed | Роль / профиль | Важное ограничение |
|---|---|---|
| `candidate@example.com` | Candidate, Алексей Иванов, Backend, declared Middle, 3 года | verified grade/score/date NULL; навыки Python/Django/PostgreSQL; добавить FastAPI и пройти настоящий тест для связного видео |
| `employer@example.com` | Employer, Demo Tech | Владелец трёх matching-demo заявок |
| `match-exact@example.com` | Candidate, Мария Смирнова, Middle/90, 3 года, полный stack | Квалификация задана синтетически; реальной Assessment history нет |
| `match-senior@example.com` | Candidate, Алексей Волков, Senior/100 | Синтетическая квалификация |
| `match-optional@example.com` | Candidate, Ирина Орлова, Middle/90, 1.5 года, без Django | Синтетическая квалификация |
| `match-no-experience@example.com` | Candidate, Павел Морозов, Middle/90, без опыта | Синтетическая квалификация |

Пароль каждого нового seed user — свой `DEMO_PASSWORD`. Demo email уже подтверждены.
Никакой реальный пароль в документации не приведён. Если seed повторялся поверх старых
данных, приведённые свойства нельзя считать текущими без UI проверки: seed их сохраняет.

Seed не создаёт реальные завершённые попытки, FSP verification или приглашения.
Обычный `candidate@example.com` на свежем seed не участвует в подборе из-за отсутствия
подтверждения и FastAPI. См. [подготовку капитана](p9-d0-demo-script.md).

## 7. Подбор подходящих кандидатов

1. Войти Employer на `/login` → открыть `/employer/needs`.
2. У **Backend Python Engineer** / «Активна» нажать «Подбор кандидатов».
3. Точный seed URL: http://localhost:3000/employer/needs/demo-need-backend-middle-active/matches.
4. На свежем seed допущены четыре синтетических кандидата из таблицы выше. Это наблюдалось
   в P9-D0; после настоящего теста/правок профилей количество может измениться.
5. Показать Professional Fit / Ranking Score → «Почему такой результат».
6. Не искать отдельную кнопку «Запустить Matching V2»: получение списка выполняется при
   открытии `/matches`. При изменении данных заново открыть/перезагрузить страницу.

Другие seed заявки: `demo-need-backend-junior-draft` (DRAFT) и
`demo-need-backend-senior-closed` (CLOSED). Для них активный подбор недоступен.
Не закрывать основной demo Need и не менять его ради репетиции; создать свою отдельную заявку.

## 8. Приглашения и достижения

**Техническая репетиция на синтетической fixture**, не заменяющая настоящее тестирование:

1. В отдельном профиле браузера войти `match-exact@example.com`.
2. `/candidate/edit`: сохранить FSP ID `MOCK-MULTI`, не менять specialization, consent и skills.
3. `/candidate`: «Проверить FSP ID» → три достижения, тестовый реестр / MOCK.
4. Employer: `/employer/needs/new` создать отдельную заявку по рецепту раздела A сценария:
   «Позиция» = `Демонстрация CodexTeam — репетиция`, Backend/Middle, обязательные Python/FastAPI,
   описание `Ищем специалиста для демонстрационного проекта на Python и FastAPI.`,
   зарплата от 100000 до 150000 → «Создать потребность»; в `/employer/needs` «Активировать».
5. Открыть её «Подбор кандидатов», найти **Мария С.**, раскрыть «Почему такой результат».
6. «Пригласить» → сообщение → «Отправить приглашение»; ждать «Приглашение отправлено».
7. `/employer/needs/<needId>/invitations`: статус «Отправлено», контакта нет.
8. Candidate `/candidate/invitations`: «Обновить» → «Открыть» → «Принять».
9. Появляется контакт работодателя. Employer: «Обновить» → «Принято» и контакт кандидата.

Для **видеозаписи** использовать подготовленный `candidate@example.com` с настоящим
успешным тестом и новую/неиспользованную заявку согласно сценарию. В репетиции выше score
Марии синтетический — не произносить, что она прошла тест.
Для повтора записи создавать новую заявку через UI: ACCEPTED той же пары блокирует новую отправку.

Точная реализация API, сверенная по routes (UI использует `/api` proxy):
`GET /employer/needs/{need_id}/matches`, `POST /employer/needs/{need_id}/invitations`,
`GET /candidate/invitations`, `POST /candidate/invitations/{invitation_id}/view`,
`POST /candidate/invitations/{invitation_id}/accept`,
`GET /employer/needs/{need_id}/invitations`, `POST /candidate/fsp/verify`.
Роли/ownership/ACTIVE/eligibility не обходить; SQL mutations для подготовки не нужны.

## 9. Завершение и восстановление

Из каталога, которым запускали свой Compose project:

```sh
docker compose -p fsp-p9-d0-demo down
```

Это останавливает свои контейнеры/сеть, volume с данными сохраняется. При следующем
`up --build -d --wait` существующие данные останутся. Не использовать удаление volumes,
Docker prune, drop/reset БД или остановку проектов QA/manual.

При временной недоступности:

```sh
docker compose -p fsp-p9-d0-demo ps
docker compose -p fsp-p9-d0-demo logs --tail=80 backend
```

Журнал смотреть приватно: при регистрациях он содержит verification links.
После восстановления нажать «Повторить»/«Обновить» в UI. Если пароль старого аккаунта
не совпадает, повторный seed его не меняет; не удалять БД для восстановления.

## 10. Доказательства P9-D0 и пределы проверки

Новые проверки 10 октября 2026, без повторения P9-A0/P9-B0:

| Проверка | Результат и среда |
|---|---|
| GitHub main | `git ls-remote`: exact baseline; diff с известным baseline отсутствует |
| Docker | Server 29.4.3; проект `fsp-p9-d0-check`, свои контейнеры/volume; UI 13010, API 18080, DB 55442 |
| Build / up | VERIFIED: frontend/backend build, три healthy services на LF-экспорте |
| Alembic | VERIFIED: upgrade; `c3d9b7e21a40 (head)` |
| Seed checkout | FAILED: обе команды отклонены hash gate при CRLF; это не успешный запуск |
| Seed LF | VERIFIED: `--demo` и `--matching-demo` → `Seed completed.` |
| Health / DB / proxy | VERIFIED: pg_isready accepting connections; health 200 `{"status":"ok"}`; `/api/skills` — 7 |
| Аккаунты | VERIFIED через HTTP frontend proxy: candidate/employer/match-exact login, email_verified=true |
| Реальный Assessment результат | NOT VERIFIED в P9-D0. Original candidate grade=NULL/history=0; match-exact Middle/90/history=0 — seed fixture |
| Ограниченный demo HTTP | VERIFIED: ACTIVE seed Need, 4 matches, breakdown; UI/API FSP flow → 3 achievements / bonus5; новая собственная репетиционная Need → SENT → VIEWED → ACCEPTED; взаимный GET readback контактов |
| Browser / MacBook | NOT VERIFIED в P9-D0. Историческое P9-A0 E2E относится к тому же baseline, но не к MacBook капитана |
| Завершение | Свой Compose project остановлен без удаления volume; чужие среды не затронуты |

HTTP smoke завершён **2026-10-10 14:54:07 UTC (17:54:07 Europe/Moscow)**.
Использовал `match-exact@example.com` с явно синтетической qualification и новую репетиционную
Need, без прямых SQL edits, без настоящего прохождения Assessment, без новых regression suites.
Это доказывает технический путь приглашения/ФСП, а не наличие результата теста для видео.
Записи диагностики и helper находятся в игнорируемой собственной `.cache/p9-d0`, не в PR.
Секреты/сырые auth responses/logs в документацию не копировались.

Команды сверены с `README.md`, `compose.yaml`, `.env.example`, Dockerfiles,
`backend/app/seed.py`, `question_bank.py`, API routes и frontend components.
README inventory 75 устарел: фактически опубликован Backend120 (40 на grade);
это историческое замечание P9-A0/P9-B0, README в P9-D0 не меняется.

Необходимые проверки капитана: десять пунктов preflight в сценарии, настоящая успешная
попытка, раздельные роли браузера, новая пара приглашения, читаемый кадр/звук и итоговая
проверка файла. До их выполнения запуск/демо на MacBook остаются NOT VERIFIED.
