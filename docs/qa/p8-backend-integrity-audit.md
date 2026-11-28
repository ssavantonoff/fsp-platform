# P8-B0 — Independent Backend Integrity & Business Logic Audit

## 1. Executive Summary

Аудит фиксированного main выявил **6 Confirmed findings: P0=0, P1=1, P2=2, P3=3**. Два дополнительных security-риска имеют статус **Potential / P2**. Шесть вопросов требуют **Product Decision Required**: пять P2, один P3. Ни один дефект не исправлен.

Приоритетный дефект — несогласованные SQL snapshots Matching: старое consent=true объединяется с новой квалификацией, и работодателю показывается кандидат, который **никогда не удовлетворял eligibility в одном committed состоянии**. Это подтверждённое нарушение consent/hard-filter инварианта; утечки email или контактов этим сценарием не установлено. Другие подтверждённые дефекты: HTTP500 при совместной смене consent/FSP ID, смешанный ответ конкурентного PUT, локальная Windows-кодировка seed, устаревшее описание банка в README и воспроизводимый сбой byte-gates из-за Windows newline conversion.

До ACCEPTED скрытые контактные поля в выполненной матрице API не раскрылись. Принятие после CLOSED, сохранение доступа после отзыва consent и повторные приглашения после DECLINED воспроизведены, но не объявлены ошибками при отсутствии утверждённого правила. Их нельзя незаметно разрешить техническим исправлением.

**Покрытие: 102 строки; Verified=75, Failed=13, Potential=10, Not Tested=4; фактически проверено 86.27%**. Разрешённый этап аудита оформлен; полное покрытие не достигнуто. Статус Verified относится только к обозначенному методу и условиям проверки.

## 2. Baseline commit SHA and scope

- Repository: [ssavantonoff/fsp-platform](https://github.com/ssavantonoff/fsp-platform).
- Baseline: `acead7a5ea8eb93c1344107440ddb6c16b42173f`. `git fetch origin main` выполнен; `git ls-remote origin refs/heads/main` вернул тот же SHA. На момент фиксации remote audit-ветка отсутствовала.
- Audit branch: `audit/p8-backend-integrity`; managed worktree: `C:/Users/olego/.codex/worktrees/p8-backend-integrity/fsp-platform`.
- Исходный checkout `C:/Users/olego/Documents/ChatGPT/hackathon/fsp-platform` остался на `feat/matching-v2-review-gate`; его существующие файлы и ветка не изменялись. Новый worktree имеет отдельный Git index и был создан/прикреплён к этому чату. До начала работы он был чистым; другие доступные чаты не имели его cwd. Это не утверждение об отсутствии неизвестных процессов на всей машине.
- Область: backend/runtime, миграции, тесты, профиль/Assessment/Matching/Needs/Invitations/FSP взаимодействия; frontend API contracts и repository docs как supporting context. Незавершённый P8-A0 вне baseline исключён.
- Запрещённые Matching validation dataset/golden/review тесты, P6-B2 Stage2 и изменение frozen labels не выполнялись. Stage1 уже присутствует в baseline; это не разрешение вычислять метрики38 пар.
- Оригинальное независимо утверждённое ТЗ отдельно не приложено к baseline. README — наблюдаемый текущий контракт; specs с пометкой draft и implementation plans — supporting evidence. Исторические Assessment-документы не используются как безусловная текущая норма. Отдельный `O2_SPEC.md` отсутствует в зафиксированном main и не используется для выводов. Тестовые прогоны выполнялись 9–10 октября 2026 (Europe/Moscow); документационное ревью завершено 10 октября.

## 3. Tools and environment

Superpowers использован для изоляции, перечня проверок, параллельного анализа и проверки перед завершением. Context7 предоставил официальную документацию [SQLAlchemy identity map / refresh](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#expiring-refreshing) и [populate_existing](https://docs.sqlalchemy.org/en/20/orm/queryguide/api.html#populate-existing): row lock сам по себе не заменяет свежесть ORM-объекта или согласованность нескольких SELECT. Доказательства findings получены из baseline и экспериментов, а не из документации библиотеки.

GitHub используется для remote baseline и Draft PR. Codex Security Standard scan: `3a4c1440-d255-46cf-b5d9-a14b415c7728`, scope backend. Read-only preflight ready, capacity4 включая родителя (3 рабочих места); предупреждение о рекомендуемых6 slots не блокировало работу. Daybreak not_granted — advisory, аудит продолжен. Самостоятельный static baseline auditor и отдельный architecture reviewer не получали родительских гипотез; их кандидаты перепроверены и не автоматически повышены до Confirmed.


The existing Codex Security scan was finalized on10 October2026 after read-only validation of its saved canonical draft; no new scan or broad review was launched. Completion returned `status=complete`, `reportAvailable=true`, one High security finding corresponding to P8-B0-001, and generated `report.md`. Its canonical coverage remains **partial** (eight reviewed surfaces, unresolved resource/rate-limit/deployment questions); completed artifact generation is not a claim of full security coverage. Other business/environment findings and product questions belong to this P8 report and are not duplicated into security severity totals.

Canonical artifacts are retained locally under `C:/Users/olego/.codex/state/plugins/codex-security/scans/fsp-platform/acead7a5ea8eb93c1344107440ddb6c16b42173f_20261009T202831Z_og97oqbd/`: `scan-manifest.json`, `findings.json`, `coverage.json`, `threatmodel.md`, `report.md`, and supplemental architecture/runtime evidence. The completion warning states that working-tree contents changed during the scan and results were saved for the original snapshot. The new untracked audit report is the only review-tree change; production source/migrations/frozen assets are verified against the pinned baseline before commit. No real deployment or Daybreak guarantees are inferred.

Windows; Python3.13.7; Node24.1.0; Docker29.4.3; PostgreSQL17.11. Установленные Python/Node библиотеки использованы только как runtime: application source импортировался из audit-worktree. `PYTHONUTF8=1`, `APP_ENV=test`, `DATABASE_URL` и `TEST_DATABASE_URL` явно задавались только для собственных тестовых процессов. Существующие .env и environment dumps не читались.

Тестовая БД: новый `fsp-p8-b0-postgres-01a12258`, loopback55438, tmpfs, synthetic principal/database; UUID schemas создаются/удаляются fixture. Для outage/restart — **вторая** новая БД `fsp-p8-b0-infra-db-01a12258`, отдельная сеть `fsp-p8-b0-net-01a12258`, новый volume `fsp-p8-b0-infra-data-01a12258`, API `fsp-p8-b0-infra-api-01a12258`, loopback58438. Backend image собран из baseline: `fsp-p8-b0-backend:01a12258`, manifest digest `sha256:cbf46e3cac5fcc3fc315bcb023ff7f6adaf6cf558e87f51d971de1d957020ef8`. Общие контейнеры/volumes не останавливались; `docker compose down -v` не использовался.

## 4. Audit methodology

Перечень73 обязательных сценариев A–G/DB был зафиксирован до выполнения scenario probes. Затем: требования → инварианты → позитивные/негативные/конкурентные случаи → source/migration/contract review → реальные тесты на PostgreSQL → parent reproduction → матрица. Независимые субаудиты: A/C; B/D/E/G; security baseline. Приглашения и инфраструктура дополнительно проверены родителем. Первый независимый reviewer подтвердил73 IDs, исходные счётчики и серьёзные evidence, выявил неточные имена тестов и fixture recipe; узкий reviewer продолжения подтвердил необходимость разделить observed byte failure и incomplete suites. Замечания обработаны, финальные подсчёты выполнены по обновлённой матрице.

Failed означает наблюдаемое нарушение, не только подозрительный код. Passing **reproducer** фиксирует ошибочное поведение и не означает исправления. Несколько Failed rows могут ссылаться на один root cause. Product Decision Required представлен Potential, поскольку поведение установлено, а норма ещё нет. Конкурентные эксперименты используют Events/Barriers/SQL checkpoints и отдельные Sessions; это проверенные расписания, а не формальное доказательство всех interleavings. Старые captured Need criteria при ACTIVE edits разрешены; невозможная смесь consent/qualification этим разрешением не оправдывается.

## 5. Audit Coverage Matrix

Ссылки на исходники закреплены за baseline SHA. Имена existing tests относятся к реально выполненным case families и junit, не к одному названию теста. Полные синтетические воспроизводители приведены в Appendix B, execution commands/results — Appendix A/C. Повторяющиеся source anchors обозначают общий контракт, но evidence различается по проверяемому сценарию.

| Check ID | Module | Scenario | Expected invariant | Verification method | Status | Evidence | Finding ID | Limitation |
|---|---|---|---|---|---|---|---|---|
| AUTH-01 | Auth | Protected API rejects anonymous requests | 401 for auth/me, both profiles, assessment availability/current/history/details/start/save/submit, candidate FSP/invitations and employer needs. Sources: [README.md:335-339](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L335-L339) | Test / Integration | Verified | [backend/tests/test_profiles.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_profiles.py) → `test_anonymous_has_no_profile_access[/candidate/profile]`<br>[backend/tests/test_profiles.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_profiles.py) → `test_anonymous_has_no_profile_access[/employer/profile]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_authorization[get-/availability-None]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_authorization[get-/current-None]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_authorization[get-/history-None]`<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| AUTH-02 | Auth | Server-owned role cannot be spoofed | Other-role profile and assessment APIs403; role update405; header/query role spoof403; stored CANDIDATE unchanged. ADMIN/email_verified registration extras422. Sources: [README.md:188-191](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L191), [README.md:337](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L337) | Test / Integration | Verified | [backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_registration_validation_does_not_echo_password[body0]`<br>[backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_registration_validation_does_not_echo_password[body1]`<br>[backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_registration_validation_does_not_echo_password[body2]`<br>[backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_registration_validation_does_not_echo_password[body3]`<br>[backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_registration_validation_does_not_echo_password[body4]`<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| AUTH-03 | Auth | Foreign profiles/resources cannot be accessed | Foreign profile path/read/update404; user_id mass assignment422; owner profile unchanged. Foreign assessment detail/save/submit404, intruder history empty. Sources: [README.md:188-191](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L191), [README.md:337](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L337) | Test / Integration | Verified | [backend/tests/test_profiles.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_profiles.py) → `test_cannot_read_or_mutate_foreign_profile[candidate]`<br>[backend/tests/test_profiles.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_profiles.py) → `test_cannot_read_or_mutate_foreign_profile[employer]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_foreign_attempt_privacy`<br>Executed: Appendix A (126 existing + 18 adversarial). | — | Executed profile/assessment ownership; needs and invitations are audited by other audit areas. |
| AUTH-04 | Auth | Expired and revoked sessions reject reuse | Session at expiry401; microsecond before200; replaced login token401; logged-out copied token401; new application uses persisted valid session. Sources: [README.md:194-197](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L194-L197) | Test / Integration / Concurrency | Verified | [backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_logout_revokes_session_and_is_repeatable`<br>[backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_session_survives_app_restart`<br>[backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_expired_session_rejected`<br>`test_p8_session_rotation_revoked_token_cannot_replay` (Appendix B)<br>`test_p8_session_and_email_exact_expiry_boundary` (Appendix B)<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| AUTH-05 | Auth | Consumed verification and revoked session token cannot be reused | Consumed verification204 then400; old/revoked session401. Active session tokens are intentionally reusable until expiry/revocation, not one-time access tokens. Sources: [README.md:89-92](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L89-L92), [README.md:194-197](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L194-L197) | Test / Integration / Concurrency | Verified | [backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_email_verification_is_one_time`<br>[backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_concurrent_verification_has_one_winner`<br>`test_p8_session_rotation_revoked_token_cannot_replay` (Appendix B)<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| AUTH-06 | Auth | Duplicate normalized email registration | Existing normalized email409; four concurrent case variants yield201/409/409/409, exactly one user and one verification. Sources: [README.md:182-184](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L182-L184), [README.md:202](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L202) | Test / Integration | Verified | [backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_duplicate_email_case_insensitive`<br>`test_p8_four_way_register_and_verify_have_single_winners` (Appendix B)<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| AUTH-07 | Auth | Expired email link cannot verify account | Expired, exact-expiry and unknown verification400; expired account remains unverified. Recovery path absence separately recorded as product decision. Sources: [README.md:89-92](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L89-L92), [README.md:102](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L102) | Test / Integration | Verified | [backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_expired_verification_rejected`<br>[backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_unknown_verification_rejected`<br>`test_p8_session_and_email_exact_expiry_boundary` (Appendix B)<br>`test_p8_unverified_email_action_contract` (Appendix B)<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| AUTH-08 | Auth | Action-specific email verification policy | Unverified login200/profile create201 conform to README; assessment start403 email_not_verified. General verification policy for other protected actions is not assumed. Sources: [README.md:94-95](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L94-L95), [README.md:271-273](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L271-L273) | Test / Integration | Verified | [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_prerequisites_and_missing_profile`<br>`test_p8_unverified_email_action_contract` (Appendix B)<br>Executed: Appendix A (126 existing + 18 adversarial). | — | Global restriction beyond assessment is Product Decision Required; no authority to invent a blanket verified-email rule. |
| AUTH-09 | Auth | Cookie-authenticated CSRF defense | Actual session cookie, hostile/null/empty/missing Origin: logout, profile PUT, answer PUT, submit POST all403; answer and attempt unchanged. Sources: [README.md:198-201](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L198-L201), [README.md:338](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L338) | Test / Integration | Verified | [backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_untrusted_origin_rejected`<br>[backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_missing_origin_rejected_for_cookie_mutation`<br>`test_p8_cookie_csrf_rejection_matrix[https://attacker.example]` (Appendix B)<br>`test_p8_cookie_csrf_rejection_matrix[null]` (Appendix B)<br>`test_p8_cookie_csrf_rejection_matrix[]` (Appendix B)<br>Executed: Appendix A (126 existing + 18 adversarial). | — | API-side cookie check executed; proxy preservation inspected statically here; no browser cross-site scenario executed by this subaudit. |
| AUTH-10 | Auth | Concurrent register and verification single winners | Four-way concurrent normalized-email register201/409/409/409; verify204/400/400/400; persisted user count1, verification count1, verified true. Sources: [README.md:89-92](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L89-L92), [README.md:182-184](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L182-L184) | Test / Integration / Concurrency | Verified | [backend/tests/test_auth.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_auth.py) → `test_concurrent_verification_has_one_winner`<br>`test_p8_four_way_register_and_verify_have_single_winners` (Appendix B)<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| ASM-01 | Assessment | Concurrent starts allow one active attempt | Concurrent starts201/409; one AssessmentAttempt; DB rejects second IN_PROGRESS directly. Sources: [README.md:286](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L286), [README.md:294-296](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L294-L296) | Test / Integration | Verified | [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_database_verification_consistency_and_single_active`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_concurrent_start_and_submit_postgres`<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| ASM-02 | Assessment | Answers cannot change attempt at/after deadline | Save at exact deadline and+1 microsecond409 assessment_finished; attempted answer remains null, FAILED0/TIMEOUT; finished_at equals deadline. Lazy timeout may PASS based on saved answers. Sources: [README.md:287-293](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L287-L293) | Test / Integration | Verified | [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_lazy_timeout_and_cooldown[True-get]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_lazy_timeout_and_cooldown[True-current]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_lazy_timeout_and_cooldown[True-availability]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_lazy_timeout_and_cooldown[True-history]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_lazy_timeout_and_cooldown[True-answer]`<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| ASM-03 | Assessment | Repeat submit is idempotent and atomic | Repeated submit returns identical stable result; injected synchronization failure rolls back status and qualification; concurrent submits both200 PASSED, same finished_at, single attempt. Sources: [README.md:294-296](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L294-L296) | Test / Integration | Verified | [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_submit_idempotent_and_atomic_rollback`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_concurrent_start_and_submit_postgres`<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| ASM-04 | Assessment | Question/option substitution rejected | Other-question option422 option_not_in_question; bank question_id in place of assigned attempt_question_id422 question_not_in_attempt; zero altered saved answers. Sources: [README.md:330-331](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L330-L331), [README.md:342-343](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L342-L343) | Test / Integration / Concurrency | Verified | [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_answers_validation_change_and_finalized`<br>`test_p8_swapped_question_and_option_identifiers_rejected` (Appendix B)<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| ASM-05 | Assessment | Foreign attempt private across all actions | Other candidate GET/PUT answer/POST submit404 and history[]; no foreign identifier effect. Sources: [README.md:337](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L337) | Test / Integration / Concurrency | Verified | [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_foreign_attempt_privacy`<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| ASM-06 | Assessment | Cooldown and grade restrictions resist bypass | FAILED7/PASSED90 days exact boundary allowed; more advanced level independent; lower verified grade denied; specialization switch-and-back retains cooldown; submitted specialization/score/timer/candidate_id extras422. Sources: [README.md:283-286](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L283-L286), [README.md:305-312](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L305-L312) | Test / Integration | Verified | [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_start_forbids_client_canonical_data[extra0]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_start_forbids_client_canonical_data[extra1]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_start_forbids_client_canonical_data[extra2]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_start_forbids_client_canonical_data[extra3]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_start_forbids_client_canonical_data[extra4]`<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| ASM-07 | Assessment | FAIL preserves previous canonical qualification | Middle PASS80/dateT1 then Senior FAIL65/T2 leaves Middle80/T1 in profile/detail/availability/repeat submit and DB; same-grade FAIL preserves triple; successful retake can lower previous score as documented. Sources: [README.md:300-312](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L300-L312) | Test / Integration | Verified | [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_failed_higher_grade_preserves_current_qualification`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_grade_upgrade_fail_preservation_same_grade_and_specialization`<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| ASM-08 | Assessment | Specialization change during active attempt | Live specialization change409 assessment_in_progress; declared grade and consent edits200, finish/history still work. Expired attempt finalized then switch clears new-specialization qualification; return restores prior PASS. Concurrent specialization edit/submit409/200 with correct Backend PASS and profile state. Sources: [README.md:272-273](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L272-L273), [README.md:305-312](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L305-L312) | Test / Integration | Verified | [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_active_attempt_and_profile_edits`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_specialization_change_finalizes_expired_attempt_and_restores_history`<br>`test_p8_specialization_edit_races_submit_consistently` (Appendix B)<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| ASM-09 | Assessment | History and next availability match canonical rules | History preserves independent historical attempt results and descending starts; detail carries current canonical verification. Timeout finished_at=expires_at, next availability=deadline+7/90 days; availability shows live block reason and active id. Sources: [README.md:287-290](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L287-L290), [README.md:324-339](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L324-L339) | Test / Integration | Verified | [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_lazy_timeout_and_cooldown[True-get]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_lazy_timeout_and_cooldown[True-current]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_lazy_timeout_and_cooldown[True-availability]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_lazy_timeout_and_cooldown[True-history]`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_lazy_timeout_and_cooldown[True-answer]`<br>Executed: Appendix A (126 existing + 18 adversarial). | — | FastAPI TestClient plus real isolated PostgreSQL, not a browser or live deployment. |
| ASM-10 | Assessment | Concurrent finish/grading and deadline races | Two submitters same PASSED100+finished_at. Last-answer/submit3 schedules: save-first PASSED70/save200 and submit-first FAILED65/save409; canonical values always coherent. Exact-deadline save/submit/availability race409/200/200, one PASSED70 TIMEOUT, equal result/canonical timestamp. Sources: [README.md:286-296](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L286-L296) | Test / Integration / Concurrency | Verified | [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_concurrent_start_and_submit_postgres`<br>`test_p8_last_answer_races_submit_linearizably[0]` (Appendix B)<br>`test_p8_last_answer_races_submit_linearizably[1]` (Appendix B)<br>`test_p8_last_answer_races_submit_linearizably[2]` (Appendix B)<br>`test_p8_deadline_save_submit_and_read_race_agree` (Appendix B)<br>Executed: Appendix A (126 existing + 18 adversarial). | — | Sampled real concurrent schedules, not an exhaustive concurrency proof; uses PostgreSQL row locks, no SQLite skip. |
| PROF-01 | Candidate profiles | Specialization after assessment | Changing specialization after completion clears/restores qualification from that specialization history; active attempt blocks change. Sources: [README.md:188-193](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L193) | Test / Integration | Verified | `test_profile_edits_after_real_assessment_propagate_to_fresh_matching` (Appendix B)<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_active_attempt_and_profile_edits`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_grade_upgrade_fail_preservation_same_grade_and_specialization`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_specialization_change_finalizes_expired_attempt_and_restores_history`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/profiles.py:48-56](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L48-L56), [backend/app/services/assessments.py:97-123](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/assessments.py#L97-L123) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| PROF-02 | Candidate profiles | Declared grade edit | Declared grade is editable and never overwrites server-qualified grade/score/date or enters Matching eligibility. Sources: [README.md:188-193](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L193) | Test / Integration | Verified | `test_profile_edits_after_real_assessment_propagate_to_fresh_matching` (Appendix B)<br>[backend/tests/test_profiles.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_profiles.py) → `test_existing_verified_grade_is_preserved`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_ignores_declared_grade_fsp_and_recency`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/profiles.py:63-67](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L63-L67), [backend/app/services/matching.py:170-175](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L170-L175), [backend/app/schemas.py:51-68](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/schemas.py#L51-L68) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| PROF-03 | Candidate profiles | Remove must-have skills | Removing a mandatory skill excludes the candidate from fresh Matching without inventing verified skills. Sources: [README.md:188-193](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L193) | Test / Integration | Verified | `test_profile_edits_after_real_assessment_propagate_to_fresh_matching` (Appendix B)<br>[backend/tests/test_matching_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching_rules.py) → `test_eligibility_hard_filters`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/profiles.py:42-44](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L42-L44), [backend/app/services/profiles.py:65](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L65), [backend/app/services/matching_rules.py:194-195](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching_rules.py#L194-L195) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| PROF-04 | Candidate profiles | Withdraw consent with unchanged FSP ID; next Matching excludes candidate | Successful same-ID consent withdrawal clears consent timestamp and excludes the candidate from new Matching/send operations. Sources: [README.md:188-193](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L193) | Test / Integration | Verified | `test_profile_edits_after_real_assessment_propagate_to_fresh_matching` (Appendix B)<br>`test_reproduce_impossible_consent_qualification_mix` (Appendix B)<br>`test_reproduce_combined_consent_id_edit_autoflush_failure` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/profiles.py:57-64](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L57-L64), [backend/app/services/matching.py:138-156](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L138-L156), [backend/app/services/matching_rules.py:183-184](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching_rules.py#L183-L184) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| PROF-04b | Candidate profiles | Withdraw consent while changing FSP ID | All required fields must describe one coherent committed state; valid multi-field updates succeed atomically. [README.md:188-193](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L193) | Integration / Concurrency | Failed | `test_profile_edits_after_real_assessment_propagate_to_fresh_matching` (Appendix B)<br>`test_reproduce_impossible_consent_qualification_mix` (Appendix B)<br>`test_reproduce_combined_consent_id_edit_autoflush_failure` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/profiles.py:57-64](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L57-L64), [backend/app/services/matching.py:138-156](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L138-L156), [backend/app/services/matching_rules.py:183-184](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching_rules.py#L183-L184)<br>Parent independent reproduction: Appendix B1–B3. | P8-B0-002 | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| PROF-05 | Candidate profiles | Change FSP ID alone; evidence resets, qualification unchanged | An ID-only change atomically clears FSP evidence/bonus while preserving independent Assessment qualification. Sources: [README.md:188-193](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L193) | Test / Integration | Verified | `test_profile_edits_after_real_assessment_propagate_to_fresh_matching` (Appendix B)<br>`test_reproduce_combined_consent_id_edit_autoflush_failure` (Appendix B)<br>[backend/tests/test_fsp.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp.py) → `test_changing_identifier_invalidates_evidence_atomically`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/profiles.py:57-64](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L57-L64), [backend/app/services/fsp.py:24-29](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/fsp.py#L24-L29) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| PROF-05b | Candidate profiles | Change FSP ID and consent together | All required fields must describe one coherent committed state; valid multi-field updates succeed atomically. [README.md:188-193](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L193) | Integration / Concurrency | Failed | `test_profile_edits_after_real_assessment_propagate_to_fresh_matching` (Appendix B)<br>`test_reproduce_combined_consent_id_edit_autoflush_failure` (Appendix B)<br>[backend/tests/test_fsp.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp.py) → `test_changing_identifier_invalidates_evidence_atomically`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/profiles.py:57-64](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L57-L64), [backend/app/services/fsp.py:24-29](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/fsp.py#L24-L29)<br>Parent independent reproduction: Appendix B1–B3. | P8-B0-002 | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| PROF-06 | Candidate profiles | Concurrent writes persist a coherent final full profile | Concurrent full-profile writes serialize and persist one complete payload with its own skill relations. Sources: [README.md:188-193](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L193) | Test / Integration | Verified | `test_two_concurrent_full_edits_remain_coherent[candidate]` (Appendix B)<br>`test_reproduce_mutation_response_scalar_relation_mix[candidate]` (Appendix B)<br>[backend/tests/test_fsp_concurrency.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_concurrency.py) → `test_verify_and_identifier_edit_use_same_parent_lock`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/profiles.py:32-37](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L32-L37), [backend/app/services/profiles.py:67-68](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L67-L68), [backend/app/models.py:237-239](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/models.py#L237-L239) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| PROF-06b | Candidate profiles | Concurrent mutation response combines different versions | All required fields must describe one coherent committed state; valid multi-field updates succeed atomically. [README.md:188-193](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L193) | Integration / Concurrency | Failed | `test_two_concurrent_full_edits_remain_coherent[candidate]` (Appendix B)<br>`test_reproduce_mutation_response_scalar_relation_mix[candidate]` (Appendix B)<br>[backend/tests/test_fsp_concurrency.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_concurrency.py) → `test_verify_and_identifier_edit_use_same_parent_lock`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/profiles.py:32-37](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L32-L37), [backend/app/services/profiles.py:67-68](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L67-L68), [backend/app/models.py:237-239](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/models.py#L237-L239)<br>Parent independent reproduction: Appendix B1–B3. | P8-B0-003 | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| PROF-07 | Candidate profiles | Canonical verification trio and specialization/history stay consistent | Canonical grade/score/date form a consistent server-owned trio for the current specialization. Sources: [README.md:188-193](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L193) | Test / Integration | Verified | [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_database_verification_consistency_and_single_active`<br>`test_reproduce_impossible_consent_qualification_mix` (Appendix B)<br>`test_reproduce_mutation_response_scalar_relation_mix[candidate]` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/models.py:189-203](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/models.py#L189-L203), [backend/app/services/matching.py:138-156](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L138-L156), [backend/app/services/profiles.py:67-68](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L67-L68) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| PROF-07b | Candidate profiles | Matching combines consent and qualification never committed together | All required fields must describe one coherent committed state; valid multi-field updates succeed atomically. [README.md:188-193](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L193) | Integration / Concurrency | Failed | [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_database_verification_consistency_and_single_active`<br>`test_reproduce_impossible_consent_qualification_mix` (Appendix B)<br>`test_reproduce_mutation_response_scalar_relation_mix[candidate]` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/models.py:189-203](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/models.py#L189-L203), [backend/app/services/matching.py:138-156](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L138-L156), [backend/app/services/profiles.py:67-68](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L67-L68)<br>Parent independent reproduction: Appendix B1–B3. | P8-B0-001 | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-01 | Matching V2 | All six hard filters on coherent stable inputs | All six hard filters must hold together in a coherent candidate state before any scoring. Sources: [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Test / Integration | Verified | [backend/tests/test_matching_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching_rules.py) → `test_eligibility_hard_filters`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_excludes_failed_hard_filters`<br>`test_reproduce_impossible_consent_qualification_mix` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/matching_rules.py:178-205](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching_rules.py#L178-L205), [backend/app/services/matching.py:138-156](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L138-L156) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-01b | Matching V2 | Hard-filter conjunction across concurrent consent and qualification writes | All required fields must describe one coherent committed state; valid multi-field updates succeed atomically. [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Integration / Concurrency | Failed | [backend/tests/test_matching_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching_rules.py) → `test_eligibility_hard_filters`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_excludes_failed_hard_filters`<br>`test_reproduce_impossible_consent_qualification_mix` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/matching_rules.py:178-205](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching_rules.py#L178-L205), [backend/app/services/matching.py:138-156](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L138-L156)<br>Parent independent reproduction: Appendix B1–B3. | P8-B0-001 | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-02 | Matching V2 | Grade compatibility | Only the documented nine-cell grade matrix determines eligibility and GradeFit. Sources: [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Test / Integration | Verified | [backend/tests/test_matching_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching_rules.py) → `test_grade_compatibility`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_active_grade_edit_changes_eligibility_and_fit`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/matching_rules.py:167-175](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching_rules.py#L167-L175) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-03 | Matching V2 | Must-have skills | Every must-have skill is required; missing one fails eligibility before scoring. Sources: [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Test / Integration | Verified | [backend/tests/test_matching_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching_rules.py) → `test_eligibility_hard_filters`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_active_must_have_edit_changes_eligibility`<br>`test_profile_edits_after_real_assessment_propagate_to_fresh_matching` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/matching_rules.py:194-195](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching_rules.py#L194-L195), [backend/app/services/matching.py:118-120](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L118-L120) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-04 | Matching V2 | Nice-to-have skills | Nice-to-have skills affect fit/ordering but not hard eligibility; absent optional factor is excluded and renormalized. Sources: [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Test / Integration | Verified | [backend/tests/test_matching_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching_rules.py) → `test_eligibility_does_not_require_optional_skills_or_experience`<br>[backend/tests/test_matching_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching_rules.py) → `test_no_nice_factor_renormalization`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_active_nice_to_have_edit_changes_score_and_order`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/matching_rules.py:107-153](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching_rules.py#L107-L153), [backend/app/services/matching.py:218-222](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L218-L222) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-05 | Matching V2 | Canonical assessment provider and valid score boundaries | The canonical current Assessment provider supplies a valid integer score0–100 and compatible verified grade; no declared fallback or writes. Sources: [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Test / Integration | Verified | [backend/tests/test_candidate_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_candidate_assessments.py)<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_rejects_invalid_provider_state`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_is_read_only`<br>`test_reproduce_impossible_consent_qualification_mix` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/candidate_assessments.py:30-49](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/candidate_assessments.py#L30-L49), [backend/app/services/matching_rules.py:187-198](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching_rules.py#L187-L198), [backend/app/services/matching.py:155](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L155) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-05b | Matching V2 | New Assessment PASS combined with stale pool consent | All required fields must describe one coherent committed state; valid multi-field updates succeed atomically. [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Integration / Concurrency | Failed | [backend/tests/test_candidate_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_candidate_assessments.py)<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_rejects_invalid_provider_state`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_is_read_only`<br>`test_reproduce_impossible_consent_qualification_mix` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/candidate_assessments.py:30-49](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/candidate_assessments.py#L30-L49), [backend/app/services/matching_rules.py:187-198](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching_rules.py#L187-L198), [backend/app/services/matching.py:155](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L155)<br>Parent independent reproduction: Appendix B1–B3. | P8-B0-001 | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-06 | Matching V2 | Professional Fit weights and bounds | Professional Fit uses45/25/15/15 base weights, optional normalization, zero-target rule and bounded finite factors. Sources: [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Test / Integration | Verified | [backend/tests/test_matching_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching_rules.py) → `test_score_contributions`<br>[backend/tests/test_matching_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching_rules.py) → `test_both_optional_factors_absent`<br>[backend/tests/test_matching_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching_rules.py) → `test_scoring_bounds_and_component_endpoints`<br>[backend/tests/test_matching_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching_rules.py) → `test_scoring_bounds_reject_invalid_inputs`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/matching_rules.py:72-153](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching_rules.py#L72-L153) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-07 | Matching V2 | FSP bonus and final ranking | Ranking=.95×unrounded Professional Fit+verified FSP bonus; bonus remains0–5 and never sets eligibility. Sources: [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Test / Integration | Verified | [backend/tests/test_fsp_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_rules.py) → `test_exact_score_examples_and_bonus_cap`<br>[backend/tests/test_fsp_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_matching.py) → `test_fsp_bonus_reorders_without_changing_fit_or_assessment`<br>[backend/tests/test_fsp_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_matching.py) → `test_stronger_fit_can_win_and_ties_use_all_unrounded_keys`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/fsp_rules.py:17-38](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/fsp_rules.py#L17-L38), [backend/app/services/matching.py:46-63](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L46-L63) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-08 | Matching V2 | Deterministic ordering | Sort uses unrounded ranking, Professional Fit, Assessment score and candidate ID in documented order. Sources: [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Test / Integration | Verified | [backend/tests/test_fsp_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_matching.py) → `test_v2_uses_sub_display_precision_and_assessment_tertiary_key`<br>[backend/tests/test_matching_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching_rules.py) → `test_deterministic_ties`<br>[backend/tests/test_matching_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching_rules.py) → `test_deterministic_ties_ignore_assessment_dates`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/matching.py:55-63](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L55-L63) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-09 | Matching V2 | Pagination and stability | For unchanged committed inputs, rank before slicing and return deterministic pages with validated limit/offset. Sources: [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Test / Integration | Verified | [backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_ranks_before_pagination`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_pagination_validation`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_batches_queries`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/matching.py:187-201](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L187-L201), [backend/app/routes/employer_needs.py:70-81](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/routes/employer_needs.py#L70-L81) | — | Passed for unchanged committed inputs. Stable pagination across intervening candidate/Need edits is not specified; offset pagination can legitimately move items. |
| MATCH-10 | Matching V2 | Fresh Matching after committed profile edits | A fresh Matching request reflects committed current profile fields and canonical qualification. Sources: [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Test / Integration | Verified | `test_profile_edits_after_real_assessment_propagate_to_fresh_matching` (Appendix B)<br>`test_reproduce_impossible_consent_qualification_mix` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/matching.py:138-181](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L138-L181), [backend/app/services/profiles.py:48-67](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L48-L67) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-10b | Matching V2 | In-flight Matching during profile consent withdrawal and Assessment completion | All required fields must describe one coherent committed state; valid multi-field updates succeed atomically. [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Integration / Concurrency | Failed | `test_profile_edits_after_real_assessment_propagate_to_fresh_matching` (Appendix B)<br>`test_reproduce_impossible_consent_qualification_mix` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/matching.py:138-181](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L138-L181), [backend/app/services/profiles.py:48-67](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L48-L67)<br>Parent independent reproduction: Appendix B1–B3. | P8-B0-001 | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-11 | Matching V2 | Concurrent ACTIVE edit uses captured old criteria; fresh request uses new criteria | [README.md:456-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L456-L474); coherent immutable criteria and terminal CLOSED. | Integration / Concurrency | Verified | [backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_snapshot_survives_concurrent_active_update`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_failed_active_transaction_keeps_committed_snapshot`<br>`test_matching_close_after_criteria_snapshot_is_old_result_then_fresh_conflict` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [README.md:467-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L467-L474), [backend/app/services/matching.py:88-124](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L88-L124) | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| MATCH-11b | Matching V2 | Close Need after Matching captures ACTIVE criteria: old request200, next409 | Whether in-flight reads should finish after close is not specified. [README.md:462-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L462-L474) | Integration / Concurrency | Potential | [backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_snapshot_survives_concurrent_active_update`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_failed_active_transaction_keeps_committed_snapshot`<br>`test_matching_close_after_criteria_snapshot_is_old_result_then_fresh_conflict` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [README.md:467-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L467-L474), [backend/app/services/matching.py:88-124](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L88-L124) | P8-B0-013 | Product Decision Required: cancellation semantics after close undefined. |
| MATCH-12 | Matching V2 | Exact preview allowlist excludes contacts/private fields | Employer preview uses only allowed masked fields; it excludes contacts and private profile attributes. Sources: [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Test / Integration | Verified | [backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_preview_exact_allowlist`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_allows_assessment_verified_at`<br>`test_reproduce_impossible_consent_qualification_mix` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/need_schemas.py:91-110](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/need_schemas.py#L91-L110), [backend/app/services/matching.py:266-299](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L266-L299), [backend/app/services/matching.py:138-156](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L138-L156) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-12b | Matching V2 | Masked personal qualification preview without any eligible committed state | All required fields must describe one coherent committed state; valid multi-field updates succeed atomically. [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Integration / Concurrency | Failed | [backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_preview_exact_allowlist`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_allows_assessment_verified_at`<br>`test_reproduce_impossible_consent_qualification_mix` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/need_schemas.py:91-110](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/need_schemas.py#L91-L110), [backend/app/services/matching.py:266-299](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L266-L299), [backend/app/services/matching.py:138-156](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L138-L156)<br>Parent independent reproduction: Appendix B1–B3. | P8-B0-001 | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| MATCH-13 | Matching V2 | FSP cannot bypass eligibility | Verified FSP achievements cannot override any hard filter or create qualified eligibility. Sources: [README.md:476-524](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L476-L524) | Test / Integration | Verified | [backend/tests/test_fsp_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_matching.py) → `test_verified_fsp_cannot_override_hard_filters`<br>[backend/tests/test_fsp_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_matching.py) → `test_winner_without_must_have_is_not_invitable`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/matching.py:204-226](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L204-L226) | — | Consistent-input predicate passes; mixed-snapshot defect MPF-01 exists independently of FSP. |
| NEED-01 | Employer Needs | Need creation | Create an own DRAFT with server-derived owner/status, validated salary/experience and known nonoverlapping skills. Sources: [README.md:419-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L419-L474) | Test / Integration | Verified | [backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_employer_creates_own_draft`<br>[backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_need_input_validation`<br>[backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_need_rejects_mass_assignment`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/employer_needs.py:44-57](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/employer_needs.py#L44-L57), [backend/app/need_schemas.py:15-41](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/need_schemas.py#L15-L41) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| NEED-02 | Employer Needs | Need editing | Allowed Need scalar/skill replacement commits atomically; rejected validation/persistence leaves the previous full state. Sources: [README.md:419-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L419-L474) | Test / Integration | Verified | [backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_need_lifecycle_and_editing`<br>[backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_need_skill_kind_reassignment`<br>[backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_invalid_active_update_is_atomic`<br>[backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_active_update_persistence_failure_rolls_back`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/employer_needs.py:78-106](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/employer_needs.py#L78-L106) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| NEED-03 | Employer Needs | DRAFT to ACTIVE to CLOSED | Only DRAFT→ACTIVE→CLOSED transitions are allowed; CLOSED is terminal. Sources: [README.md:419-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L419-L474) | Test / Integration | Verified | [backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_need_lifecycle_and_editing`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/employer_needs.py:109-127](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/employer_needs.py#L109-L127) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| NEED-04 | Employer Needs | ACTIVE requirement changes | ACTIVE requirements are editable by contract; subsequent fresh Matching uses successful changes and rejected edits preserve prior inputs. Sources: [README.md:419-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L419-L474) | Test / Integration | Verified | [backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_active_must_have_edit_changes_eligibility`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_active_nice_to_have_edit_changes_score_and_order`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_active_grade_edit_changes_eligibility_and_fit`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_active_experience_edit_changes_score`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_failed_active_edit_preserves_matching`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [README.md:467-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L467-L474), [backend/app/services/employer_needs.py:78-106](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/employer_needs.py#L78-L106) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| NEED-05 | Employer Needs | Foreign Needs | Foreign and missing Need IDs give equivalent404 without owner/resource disclosure. Sources: [README.md:419-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L419-L474) | Test / Integration | Verified | [backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_need_routes_hide_foreign_and_missing_ids`<br>[backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_permissions_and_status`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/employer_needs.py:60-75](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/employer_needs.py#L60-L75), [backend/app/services/matching.py:88-111](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L88-L111) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| NEED-06 | Employer Needs | Concurrent writes preserve complete last Need payload | Concurrent full-Need writes serialize and preserve coherent scalar/skill associations. Sources: [README.md:419-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L419-L474) | Test / Integration | Verified | `test_two_concurrent_full_edits_remain_coherent[need]` (Appendix B)<br>`test_reproduce_mutation_response_scalar_relation_mix[need]` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/employer_needs.py:32-41](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/employer_needs.py#L32-L41), [backend/app/services/employer_needs.py:67-71](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/employer_needs.py#L67-L71), [backend/app/models.py:320-337](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/models.py#L320-L337) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| NEED-06b | Employer Needs | Need mutation response mixes old scalars with new skills | All required fields must describe one coherent committed state; valid multi-field updates succeed atomically. [README.md:419-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L419-L474) | Integration / Concurrency | Failed | `test_two_concurrent_full_edits_remain_coherent[need]` (Appendix B)<br>`test_reproduce_mutation_response_scalar_relation_mix[need]` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/employer_needs.py:32-41](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/employer_needs.py#L32-L41), [backend/app/services/employer_needs.py:67-71](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/employer_needs.py#L67-L71), [backend/app/models.py:320-337](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/models.py#L320-L337)<br>Parent independent reproduction: Appendix B1–B3. | P8-B0-003 | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| NEED-07 | Employer Needs | Close racing a pending edit preserves CLOSED and rejects later edit | [README.md:456-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L456-L474); coherent immutable criteria and terminal CLOSED. | Integration / Concurrency | Verified | [backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_close_racing_update_preserves_closed_state`<br>`test_matching_close_after_criteria_snapshot_is_old_result_then_fresh_conflict` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/employer_needs.py:78-83](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/employer_needs.py#L78-L83), [backend/app/services/matching.py:88-124](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L88-L124) | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| NEED-07b | Employer Needs | Close Need after Matching captures ACTIVE criteria: old request200, next409 | Whether in-flight reads should finish after close is not specified. [README.md:462-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L462-L474) | Integration / Concurrency | Potential | [backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_close_racing_update_preserves_closed_state`<br>`test_matching_close_after_criteria_snapshot_is_old_result_then_fresh_conflict` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/employer_needs.py:78-83](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/employer_needs.py#L78-L83), [backend/app/services/matching.py:88-124](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L88-L124) | P8-B0-013 | Product Decision Required: cancellation semantics after close undefined. |
| NEED-08 | Employer Needs | Closed immutability | CLOSED Need cannot be edited/reopened; rejection preserves scalars and skill relations. Sources: [README.md:419-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L419-L474) | Test / Integration | Verified | [backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_closed_need_update_is_immutable`<br>[backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_need_lifecycle_and_editing`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/employer_needs.py:78-83](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/employer_needs.py#L78-L83), [backend/app/services/employer_needs.py:109-127](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/employer_needs.py#L109-L127) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| FSP-01 | FSP/privacy | Link an ID already verified by another account in mock registry | [docs/fsp-integration-and-ranking.md:3-29](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/fsp-integration-and-ranking.md#L3-L29); generic conflict and one verified-ID owner. | Test / Concurrency | Verified | [backend/tests/test_fsp.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp.py) → `test_duplicate_verified_id_is_conflict_without_foreign_identity_leak`<br>[backend/tests/test_fsp_concurrency.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_concurrency.py) → `test_same_verified_id_cross_account_race`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [docs/fsp-integration-and-ranking.md:3-9](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/fsp-integration-and-ranking.md#L3-L9), [backend/app/services/fsp_registry.py:43-52](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/fsp_registry.py#L43-L52), [backend/app/services/fsp.py:78-125](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/fsp.py#L78-L125) | — | Mock exclusivity only. An unclaimed known fixture ID is linkable by design. |
| FSP-01b | FSP/privacy | Authenticate ownership of a real external FSP identity | Explicitly outside current mock guarantee. [docs/fsp-integration-and-ranking.md:3-9](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/fsp-integration-and-ranking.md#L3-L9) | External integration | Not Tested | No real provider/ownership contract is implemented. | — | External service absent; no mock claim extrapolated to real identity. |
| FSP-02 | FSP/privacy | Repeated verification | Repeated verify/refresh replaces evidence without duplicates, preserves first verification time, and failure preserves old snapshot. Sources: [docs/fsp-integration-and-ranking.md:11-127](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/fsp-integration-and-ranking.md#L11-L127) | Test / Integration | Verified | [backend/tests/test_fsp.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp.py) → `test_verify_read_refresh_unlink_preserve_entered_id`<br>[backend/tests/test_fsp.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp.py) → `test_failed_refresh_rolls_back_and_changed_provider_results_replace`<br>[backend/tests/test_fsp.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp.py) → `test_failure_during_replacement_restores_complete_snapshot`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/fsp.py:78-147](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/fsp.py#L78-L147) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| FSP-03 | FSP/privacy | ID-only edit clears verified evidence; parent-lock race | A successful ID-only change clears verified identity/timestamps/achievements atomically, including races with verify. Sources: [docs/fsp-integration-and-ranking.md:11-127](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/fsp-integration-and-ranking.md#L11-L127) | Test / Integration | Verified | [backend/tests/test_fsp.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp.py) → `test_changing_identifier_invalidates_evidence_atomically`<br>[backend/tests/test_fsp_concurrency.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_concurrency.py) → `test_verify_and_identifier_edit_use_same_parent_lock`<br>`test_reproduce_combined_consent_id_edit_autoflush_failure` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/profiles.py:57-64](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L57-L64), [backend/app/services/fsp.py:24-29](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/fsp.py#L24-L29) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| FSP-03b | FSP/privacy | Simultaneous FSP ID and consent edit returns 500 | All required fields must describe one coherent committed state; valid multi-field updates succeed atomically. [docs/fsp-integration-and-ranking.md:11-127](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/fsp-integration-and-ranking.md#L11-L127) | Integration / Concurrency | Failed | [backend/tests/test_fsp.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp.py) → `test_changing_identifier_invalidates_evidence_atomically`<br>[backend/tests/test_fsp_concurrency.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_concurrency.py) → `test_verify_and_identifier_edit_use_same_parent_lock`<br>`test_reproduce_combined_consent_id_edit_autoflush_failure` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/profiles.py:57-64](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L57-L64), [backend/app/services/fsp.py:24-29](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/fsp.py#L24-L29)<br>Parent independent reproduction: Appendix B1–B3. | P8-B0-002 | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| FSP-04 | FSP/privacy | Achievement formula and bonus | Achievement score uses distinct-event breadth and best normalized result; score0–100 and bonus0–5 follow the exact formula. Sources: [docs/fsp-integration-and-ranking.md:11-127](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/fsp-integration-and-ranking.md#L11-L127) | Test / Integration | Verified | [backend/tests/test_fsp_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_rules.py) → `test_exact_score_examples_and_bonus_cap`<br>[backend/tests/test_fsp_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_rules.py) → `test_competition_breadth_counts_distinct_events_not_achievements`<br>[backend/tests/test_fsp_rules.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_rules.py) → `test_team_discipline_and_recency_do_not_affect_score`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/fsp_rules.py:8-38](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/fsp_rules.py#L8-L38) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| FSP-05 | FSP/privacy | Ranking behavior | Only verified achievement aggregates affect ranking; entered-only ID contributes zero and Professional Fit stays independent. Sources: [docs/fsp-integration-and-ranking.md:11-127](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/fsp-integration-and-ranking.md#L11-L127) | Test / Integration | Verified | [backend/tests/test_fsp_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_matching.py) → `test_fsp_bonus_reorders_without_changing_fit_or_assessment`<br>[backend/tests/test_fsp_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_matching.py) → `test_stronger_fit_can_win_and_ties_use_all_unrounded_keys`<br>`test_profile_edits_after_real_assessment_propagate_to_fresh_matching` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/matching.py:46-63](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L46-L63), [backend/app/services/fsp.py:150-177](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/fsp.py#L150-L177) | — | FastAPI TestClient and synthetic PostgreSQL only; no browser or production evidence. |
| FSP-06 | FSP/privacy | Public FSP privacy | Public employer representations contain FSP aggregates only, without raw IDs/provider data or foreign identity leaks. Sources: [docs/fsp-integration-and-ranking.md:11-127](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/fsp-integration-and-ranking.md#L11-L127) | Test / Integration | Verified | [backend/tests/test_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching.py) → `test_matching_preview_exact_allowlist`<br>[backend/tests/test_fsp.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp.py) → `test_duplicate_verified_id_is_conflict_without_foreign_identity_leak`<br>[backend/tests/test_fsp_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_matching.py) → `test_invitation_snapshots_keep_fsp_at_send_after_unlink`<br>[backend/tests/test_fsp_concurrency.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_concurrency.py) → `test_invitation_send_and_unlink_keep_coherent_locked_evidence`<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/fsp_schemas.py:13-39](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/fsp_schemas.py#L13-L39), [backend/app/need_schemas.py:91-110](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/need_schemas.py#L91-L110), [backend/app/services/fsp.py:150-177](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/fsp.py#L150-L177) | — | Field minimization passes. General consent-disclosure race is reported MATCH12, independently of FSP. |
| FSP-07 | FSP/privacy | FSP cannot override eligibility or qualification | FSP never bypasses eligibility or changes Assessment history/qualification. Sources: [docs/fsp-integration-and-ranking.md:11-127](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/fsp-integration-and-ranking.md#L11-L127) | Test / Integration | Verified | [backend/tests/test_fsp_matching.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_matching.py) → `test_verified_fsp_cannot_override_hard_filters`<br>[backend/tests/test_fsp.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp.py) → `test_fsp_actions_never_call_assessment_write_paths`<br>`test_profile_edits_after_real_assessment_propagate_to_fresh_matching` (Appendix B)<br>Executed: Appendix A (357 existing; 13 synthetic cases plus 4 existing Assessment cases).<br>Source: [backend/app/services/matching.py:204-226](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L204-L226), [backend/app/services/fsp.py:78-147](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/fsp.py#L78-L147) | — | No real FSP source and no production proof. General mixed-snapshot defect exists independently of FSP. |
| INV-01 | Invitations | Send to missing/ineligible candidate (consent, specialization, skills, qualification, invalid score) | Re-evaluate current eligibility; same generic404; no invitation persisted. [backend/app/services/invitations.py:52-114](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/invitations.py#L52-L114) | Test / Integration | Verified | [backend/tests/test_invitations.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitations.py) → `test_unavailable_candidates_have_identical_external_error`<br>[backend/tests/test_invitation_privacy.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_privacy.py) → `test_send_and_matches_use_same_evaluator`<br>Executed in full PostgreSQL gate, Appendix A. | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| INV-02 | Invitations | Repeat send for SENT/VIEWED/ACCEPTED; concurrent send | One blocking pair;409 and exactly one stored invitation. [backend/tests/test_invitation_persistence.py:170-185](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_persistence.py#L170-L185) | Test / Concurrency | Verified | [backend/tests/test_invitations.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitations.py) → `test_reinvite_rules`<br>[backend/tests/test_invitation_concurrency.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_concurrency.py) → `test_concurrent_duplicate_send_one_winner`<br>[backend/tests/test_invitation_persistence.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_persistence.py) → `test_invitation_concurrent_send_database_guard`<br>Executed in full PostgreSQL gate, Appendix A. | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| INV-03 | Invitations | Accept an invitation already WITHDRAWN | Terminal withdrawal cannot reopen;409 with no contact unlock. [backend/app/services/invitations.py:334-343](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/invitations.py#L334-L343) | Test / Integration | Verified | [backend/tests/test_invitations.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitations.py) → `test_api_transition_matrix`<br>[backend/tests/test_invitation_persistence.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_persistence.py) → `test_invitation_terminal_cannot_reopen_or_be_deleted`<br>Executed in full PostgreSQL gate, Appendix A. | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| INV-04 | Invitations | Accept after Need CLOSED | Acceptance policy after closure is not established in an independently approved Invitations spec; baseline tests intentionally allow it. [backend/tests/test_invitation_privacy.py:152-180](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_privacy.py#L152-L180) | Integration | Potential | Appendix B4 `test_closed_need_accept_observation`: close200 → accept200 and employer_contact present. | P8-B0-008 | Product Decision Required; observed behavior is certain, defect classification is not. |
| INV-05 | Invitations | Concurrent accept and withdraw in both lock orders | One terminal winner, loser409; timestamps consistent; no terminal rewrite. [backend/app/services/invitations.py:317-361](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/invitations.py#L317-L361) | Concurrency | Verified | [backend/tests/test_invitation_concurrency.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_concurrency.py) → `test_accept_withdraw_race_stable_conflict`<br>[backend/tests/test_invitation_persistence.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_persistence.py) → `test_invitation_concurrent_terminal_updates_have_one_winner`<br>Executed in full PostgreSQL gate, Appendix A. | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| INV-06 | Invitations | Change profile after send: specialization, skills, qualification, name | Immutable send-time snapshots; acceptance reads current allowed contacts. [docs/fsp-integration-and-ranking.md:123-127](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/fsp-integration-and-ranking.md#L123-L127) | Test / Integration | Verified | [backend/tests/test_invitation_privacy.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_privacy.py) → `test_snapshots_survive_all_edits_and_accept_does_not_reevaluate`<br>Executed in full PostgreSQL gate, Appendix A.<br>Appendix B4 `test_profile_edit_snapshot_and_contacts_observation`. | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| INV-06b | Invitations | Accept after candidate becomes ineligible | Product must choose historical-offer vs revalidated-offer semantics. [backend/tests/test_invitation_privacy.py:152-180](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_privacy.py#L152-L180) | Integration | Potential | Appendix B4: changed specialization and cleared skills, accept200; send-time snapshot unchanged. | P8-B0-008 | No approved post-send eligibility rule supplied. |
| INV-07 | Invitations | Withdraw consent after send: fresh Matching and new send | Future eligibility fails consent; existing snapshot remains historical. [README.md:478-483](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L478-L483) | Test / Integration | Verified | [backend/tests/test_invitations.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitations.py) → `test_unavailable_candidates_have_identical_external_error`<br>Executed in full PostgreSQL gate, Appendix A.<br>Appendix B4: unchanged-ID consent PUT200 → fresh Matching total0. | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| INV-07b | Invitations | Consent=false before accept or after ACCEPTED: subsequent contact reads | Clarify independent contact-sharing consent and revocation semantics. [README.md:9-11](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L9-L11) | Integration | Potential | Appendix B4 `test_consent_withdrawal_contact_observation[before_accept/after_accept]`: candidate_contact still returned after consent=false. | P8-B0-009 | ACCEPTED is enforced; whether later personal-data withdrawal should revoke contact access is undefined. |
| INV-08 | Invitations | Snapshot correctness, immutability and concurrent source edits/FSP unlink | One coherent send-time snapshot; history unchanged by later source edits. [docs/fsp-integration-and-ranking.md:123-127](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/fsp-integration-and-ranking.md#L123-L127) | Test / Concurrency | Verified | [backend/tests/test_invitation_concurrency.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_concurrency.py) → `test_send_snapshot_holds_source_locks`<br>[backend/tests/test_invitation_concurrency.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_concurrency.py) → `test_send_refreshes_stale_session_objects`<br>[backend/tests/test_invitation_persistence.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_persistence.py) → `test_invitation_send_time_data_is_immutable`<br>[backend/tests/test_fsp_concurrency.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_concurrency.py) → `test_invitation_send_and_unlink_keep_coherent_locked_evidence`<br>Executed in full PostgreSQL gate, Appendix A. | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| INV-09 | Invitations | Contacts on list/detail/actions in SENT/VIEWED/DECLINED/WITHDRAWN | No candidate or employer contact object/private fields before ACCEPTED. [README.md:9-11](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L9-L11) | Test / Integration | Verified | [backend/tests/test_invitation_privacy.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_privacy.py) → `test_recursive_privacy_allowlists_on_every_read_surface`<br>[backend/tests/test_invitations.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitations.py) → `test_mutual_contact_unlock`<br>Executed in full PostgreSQL gate, Appendix A. | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| INV-09b | Invitations | ACCEPTED mutual contact access remains owner-scoped | Only corresponding parties receive current counterpart contacts. [backend/app/services/invitations.py:196-251](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/invitations.py#L196-L251) | Test / Integration | Verified | [backend/tests/test_invitations.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitations.py) → `test_mutual_contact_unlock`<br>[backend/tests/test_invitations.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitations.py) → `test_foreign_and_missing_resources_are_identical`<br>Executed in full PostgreSQL gate, Appendix A. | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| INV-10 | Invitations | New send after DECLINED/WITHDRAWN | Baseline permits re-send; approved cooldown/retry/anti-harassment policy is missing. [backend/tests/test_invitations.py:258-289](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitations.py#L258-L289) | Test / Integration | Potential | [backend/tests/test_invitations.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitations.py) → `test_reinvite_rules`<br>Executed in full PostgreSQL gate, Appendix A.<br>Appendix B4: three successive DECLINED → new send201; history3 rows. | P8-B0-010 | Product Decision Required: allowed cadence/limits/new Need behavior unspecified. |
| INV-11 | Invitations | All role/owner and CSRF checks across nine endpoints | Anonymous401, wrong role403, foreign/missing404, missing/untrusted Origin403; no mutation. [backend/app/routes/invitations.py:16-179](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/routes/invitations.py#L16-L179) | Test / Integration | Verified | [backend/tests/test_invitations.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitations.py) → `test_invitation_auth_roles`<br>[backend/tests/test_invitations.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitations.py) → `test_foreign_and_missing_resources_are_identical`<br>[backend/tests/test_invitations.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitations.py) → `test_all_invitation_mutations_require_origin`<br>Executed in full PostgreSQL gate, Appendix A. | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| INV-12 | Invitations | Repeated actions and complete API/DB transition matrix | Same action idempotent including timestamps; terminal cross-transition409; GET read-only. [backend/app/services/invitations.py:333-361](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/invitations.py#L333-L361) | Test / Concurrency | Verified | [backend/tests/test_invitations.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitations.py) → `test_candidate_actions_and_get_are_read_only`<br>[backend/tests/test_invitations.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitations.py) → `test_api_transition_matrix`<br>[backend/tests/test_invitation_persistence.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_persistence.py) → `test_invitation_database_transition_matrix`<br>[backend/tests/test_invitation_privacy.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_privacy.py) → `test_invitation_operations_do_not_write_or_finalize_assessment`<br>Executed in full PostgreSQL gate, Appendix A. | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| DB-01 | Infrastructure | Run real PostgreSQL17 with separate synthetic schemas | PostgreSQL17 compatibility under migrated schema. [compose.yaml:4](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/compose.yaml#L4) | Integration | Verified | PostgreSQL17.11, Alembic head c3d9b7e21a40; all PostgreSQL test gates in Appendix A. | — | Dedicated audit container, loopback55438, tmpfs; no shared data. |
| DB-02 | Infrastructure | Alembic upgrade/downgrade/upgrade and model/schema check | All five revisions apply; downgrade/re-upgrade preserves unaffected tables. [README.md:159-172](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L159-L172) | Integration | Verified | [backend/tests/test_infrastructure.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_infrastructure.py) → `test_migration_upgrade_downgrade_and_schema_matches_models`<br>[backend/tests/test_infrastructure.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_infrastructure.py) → `test_need_migration_round_trip_preserves_assessment_state`<br>[backend/tests/test_invitation_persistence.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_persistence.py) → `test_invitation_migration_round_trip_preserves_existing_tables`<br>[backend/tests/test_fsp_persistence.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_persistence.py)<br>Fresh container startup completed0001→0002→fbce7259afda→a812e4c79b60→c3d9b7e21a40. | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| DB-03 | Infrastructure | Repeat seed and demo seed preservation | Seed is transactional/idempotent and preserves existing identity/profile/qualification. [README.md:535-546](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L535-L546) | Test / Integration | Verified | [backend/tests/test_infrastructure.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_infrastructure.py) → `test_seed_is_idempotent_and_preserves_accounts`<br>[backend/tests/test_matching_seed.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_matching_seed.py)<br>Separate infra container: app.seed executed twice; skills GET200. | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| DB-04 | Infrastructure | Restart audit API and PostgreSQL containers | Persistent state survives restart; API recovers after DB restart. [compose.yaml:12-13](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/compose.yaml#L12-L13) | Integration | Verified | Appendix C: after API and private-volume DB restart, health200/users1 both times. | — | Only explicitly named P8-B0 infra containers/private volume; no common compose project used. |
| DB-05 | Infrastructure | DB stopped: health/register then recovery | Sanitized failure; no successful partial account; recovery when DB restored. [backend/app/errors.py:56-67](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/errors.py#L56-L67) | Integration | Verified | Appendix C: health500 internal_error; register503 registration_unavailable; recovered health200 and users1 unchanged. | — | Bounded outage on second audit DB, while per-test DB stayed running. |
| DB-06 | Infrastructure | Transactional finalization, Need/FSP replacement and rollback | All related writes commit together or rollback; qualification matches result. [README.md:294-312](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L294-L312) | Test / Integration | Verified | [backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_submit_idempotent_and_atomic_rollback`<br>[backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_active_update_persistence_failure_rolls_back`<br>[backend/tests/test_fsp.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp.py) → `test_failure_during_replacement_restores_complete_snapshot` | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| DB-07 | Infrastructure | Rejected mutations must not leave partially persisted operations | Validate/flush atomically; failed request leaves prior committed values. [README.md:467-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L467-L474) | Test / Integration | Verified | [backend/tests/test_infrastructure.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_infrastructure.py) → `test_seed_invalid_password_rolls_back`<br>[backend/tests/test_profiles.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_profiles.py) → `test_unknown_skills_do_not_partially_update_profile`<br>[backend/tests/test_employer_needs.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_employer_needs.py) → `test_invalid_active_update_is_atomic`<br>Combined profile500 probe independently proves rollback/unchanged profile+FSP (Appendix B2). | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| DB-08 | Infrastructure | Concurrent writes and DB uniqueness/check/lifecycle guards | Enforce one active attempt, reservation identity, legal states and coherent FSP evidence. [backend/app/models.py:175-203](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/models.py#L175-L203) | Test / Concurrency | Verified | [backend/tests/test_invitation_persistence.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_persistence.py) → `test_invitation_concurrent_send_database_guard`<br>[backend/tests/test_invitation_persistence.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_persistence.py) → `test_invitation_concurrent_terminal_updates_have_one_winner`<br>[backend/tests/test_fsp_concurrency.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_fsp_concurrency.py) → `test_same_verified_id_cross_account_race`<br>[backend/tests/test_assessments.py](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py) → `test_database_verification_consistency_and_single_active` | — | Synthetic PostgreSQL 17 / TestClient; no live deployment proof. |
| DB-09 | API contracts | Frontend callers/types vs FastAPI/Pydantic/OpenAPI | Routes, roles, enums, decimal-string salary, error envelope, optional V1/V2 FSP fields and cookie/Origin forwarding agree. [README.md:419-454](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L419-L454) | Code review / Test | Verified | Frontend runner183/184 pass; API/proxy/Assessment/Need/Matching/FSP/Invitation contract tests pass. Only source-byte brand-assets test failed (ENV-02). OpenAPI test executed. See Appendix A and [frontend/src/invitations.ts](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/frontend/src/invitations.ts), [frontend/src/backend-proxy.ts](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/frontend/src/backend-proxy.ts). | — | Unit/contract evidence, not browser-to-live-stack proof or TS compile/build gate. |
| AUTH-07b | Auth | Recovery after the only verification link expires | Recovery policy/endpoint not currently promised. [README.md:89-102](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L89-L102) | Integration | Potential | Appendix A auth events: verify400, duplicate register409, resend404, Assessment start403. | P8-B0-012 | Product Decision Required; existing README explicitly defers resend. |
| AUTH-08b | Auth | Unverified employer Need/send and candidate FSP/invitation actions | Define exactly which actions beyond Assessment require verified email. [README.md:94-95](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L94-L95) [README.md:271-273](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L271-L273) | Code review / Integration | Potential | Unverified employer fixtures create/activate/send successfully; auth role checks contain no global email gate. Assessment start403; login200/profile201. | P8-B0-011 | Current action-specific rules are verified; a blanket new policy is not an existing defect. |
| SEC-01 | Input/resource limits | Oversized Need text persisted into immutable inbox snapshot | Cross-user persistent response resource budget should be bounded; no declared byte budget exists. [backend/app/need_schemas.py:24-25](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/need_schemas.py#L24-L25) | Code review / Integration | Potential | Appendix B4: 262164-character synthetic description accepted, candidate inbox262974 bytes; static source follows input→Need→snapshot→list. | P8-B0-006 | No denial-of-service/load/stress test; effective external ingress limits and failure threshold not measured. |
| SEC-02 | Authentication abuse | Repeated bad logins and sustained guessing | Bound effective auth attempts per account/client before public exposure. [README.md:211-212](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L211-L212) | Code review / Integration | Potential | Appendix C bounded8 wrong-password HTTP requests each401; no429. [backend/app/services/auth.py:77-82](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/auth.py#L77-L82) contains no failure budget/backoff. | P8-B0-007 | Application omission certain; gateway configuration/public exposure and actual brute-force success untested. |
| ENV-01 | Local infrastructure | Default Windows encoding loads UTF-8 question bank | Documented local source should load independently of host code page. [README.md:133-144](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L133-L144) | Test | Failed | Initial targeted69 passed/1 failed/56 errors; UnicodeDecodeError cp1252 byte0x8f position214. Same unchanged source+PYTHONUTF8=1:126 pass. [backend/app/question_bank.py:30-40](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/question_bank.py#L30-L40) | P8-B0-004 | Local Windows failure; Docker Linux unaffected; UTF8 environment workaround used. |
| ENV-02 | Windows byte-gates | Observed Assessment fixture/raw SVG hash mismatches in Windows checkout | Raw-byte freeze checks require canonical bytes; sampled baseline Git blobs match their expected hashes. | Test / read-only byte comparison | Failed | Frontend completed184/183pass/1fail; observed fixture gate expected079e408… vs checkoute77d937…; full SVG expected3e38c148… vs checkout5e5b1560…. Saved Git comparison proves equality after CRLF reversal (Appendix D). | P8-B0-014 | Confirmed local checkout/test reproducibility failure; no committed fixture or logo corruption. Only two sampled byte comparisons, no assertion about all assets. |
| ENV-02b | Assessment excluded suites | Complete test_assessment_bank_remediation.py and test_assessment_diversity.py after failed byte prerequisite | Completion requires the whole suite to run; failed setup does not establish downstream behavior. | Test | Not Tested | First prerequisite failures retained; both files excluded from the completed793-case filtered gate. | — | Neither suite completed. Frozen-file rewrite rejected; no normalization or bypass performed. |
| DOC-01 | Requirements consistency | Current README bank inventory vs executed source validator | Top-level current description should agree with current bank; historical docs remain labelled. [README.md:351-353](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L351-L353) | Code review / Test | Failed | [backend/tests/test_assessments.py:212-234](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py#L212-L234) `test_bank_integrity_and_immutable_seed` executed:120; [docs/assessment-bank-diversity.md:27-37](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/assessment-bank-diversity.md#L27-L37) documents120/40/2-4-2; README says75/25/1-3-1. | P8-B0-005 | Documentation only, not an Assessment scoring defect. |
| AUTH-09b | Browser/CSRF | Actual cross-site browser cookie behavior through deployed proxy | Browser cookie/origin rules must enforce request policy at deployment. [backend/app/routes/auth.py:30-39](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/routes/auth.py#L30-L39) | Browser integration | Not Tested | HTTP-level cookie+Origin attack matrix and proxy forwarding unit tests executed; no real cross-site browser run. | — | No authorized deployed/browser cross-site infrastructure prepared; secure/SameSite behavior not extrapolated from TestClient. |
| DB-09b | Full-stack runtime | Browser→Next proxy→API→data for every workflow | Full user workflows must preserve runtime cookies/contracts. [frontend/src/backend-proxy.ts:5-38](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/frontend/src/backend-proxy.ts#L5-L38) | Browser integration | Not Tested | Backend live HTTP infra checks and frontend contract tests are separate evidence. | — | Frontend full production build/browser stack was not launched; contract tests do not establish complete runtime flow. |

## 6. Coverage Summary

| Metric | Value |
|---|---:|
| Total scenarios, including distinct branches and extra checks | 102 |
| Verified | 75 |
| Failed | 13 |
| Potential | 10 |
| Not Tested | 4 |
| Factually checked `(Verified+Failed)/Total×100%` | 86.27% |
| Scenarios with confirmed violations | 13 |
| Unique Confirmed findings | 6 |
| Required base scenarios represented | 73 / 73 |

Не закрыты: реальные FSP ownership guarantees (FSP-01b; внешняя интеграция отсутствует по дизайну), completion of byte-dependent Assessment suites (ENV-02b), настоящий browser CSRF (AUTH-09b), полные browser→proxy→API workflows (DB-09b). Риски повышенного приоритета, не доведённые до наблюдаемого вреда: persistent oversized inbox / sustained login abuse (SEC-01/02). Product semantics остаются Potential до решения владельца продукта. Поэтому называть аудит полностью завершённым по покрытию нельзя.

## 7. Confirmed Findings

### P8-B0-001 — Matching combines a candidate state that never satisfied eligibility

- **Severity / module / status:** P1 / Matching / consent / Assessment / Confirmed.
- **Condition:** Matching is paused after pool/skills SELECT but before assessment batch SELECT; candidate revokes consent, then completes an already active successful Assessment.
- **Reproduction:** Create synthetic verified-email candidate with consent=true and no qualification; start/fill MIDDLE attempt through API. Employer creates ACTIVE eligible Need; first Matching total0. Pause provider entry, PUT consent=false (same FSP ID)200, submit PASS200 MIDDLE100, release read. Parent independently repeated all3 cases.
- **Expected:** All hard filters must hold together in a coherent committed candidate state: [README.md:478-483](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L478-L483).
- **Actual:** States `[true,null,null] → [false,null,null] → [false,MIDDLE,100]`; resumed read200/total1/score100; next read total0. No committed eligible state existed.
- **Evidence:** [backend/app/services/matching.py:138-156](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching.py#L138-L156); [backend/app/services/candidate_assessments.py:35-43](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/candidate_assessments.py#L35-L43); [backend/app/services/matching_rules.py:178-205](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/matching_rules.py#L178-L205); Appendix B1; parent independent-race.xml3/3,18.32s.
- **Root cause:** READ COMMITTED supplies separate statement snapshots for pool/relationships/assessment/FSP; pure eligibility combines stale consent with newer verification.
- **Impact:** Consent hard-filter/privacy promise fails; employer receives masked name/skills and newly verified score without a valid combined state. No pre-ACCEPTED email/contact leak or persisted qualification corruption demonstrated. P1 follows a core stated invariant, not a claim of critical account compromise.
- **Proposed technical approach, not implemented:** Use a coherent transaction snapshot (e.g. read-only REPEATABLE READ established before first read) or unified consistent input query for profile, canonical qualification, skills and FSP; preserve legitimate old immutable Need criteria. Regression must assert exclusion under forced interleaving.
- **Related Check IDs:** PROF-07b, MATCH-01b, MATCH-05b, MATCH-10b, MATCH-12b.

### P8-B0-002 — Changing consent and FSP ID together returns HTTP500

- **Severity / module / status:** P2 / Candidate profiles / FSP / Confirmed.
- **Condition:** A valid full CandidateWrite flips consent and changes fsp_id in the same PUT, whether FSP link is verified or unverified.
- **Reproduction:** Create profile with MOCK-WINNER; optionally verify. PUT same payload with consent flipped and MOCK-TEAM using raise_server_exceptions=false. All4 initial consent true/false × verified/unverified branches return500. Independent parent repetition4/4. Same-ID consent-only control returns200.
- **Expected:** Allowed fields update atomically; timestamp follows consent and changed ID clears FSP evidence. [README.md:188-193](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L193) [docs/fsp-integration-and-ranking.md:11-16](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/fsp-integration-and-ranking.md#L11-L16).
- **Actual:** 500 internal_error; old profile and FSP evidence survive unchanged. With initial consent=true, attempted withdrawal does not take effect.
- **Evidence:** [backend/app/services/profiles.py:57-64](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L57-L64); [backend/app/services/fsp.py:24-29](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/fsp.py#L24-L29); [backend/app/models.py:189-193](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/models.py#L189-L193); Appendix B2; combined parent gate with B3:6 passed11.89s.
- **Root cause:** Consent timestamp changes before consent boolean assignment. FSP DELETE triggers query autoflush while row is temporarily inconsistent, before commit_profile IntegrityError handling.
- **Impact:** Valid profile update/withdrawal fails. Separate consent and ID updates provide a workaround, so P2; no partial persisted operation or data loss demonstrated.
- **Proposed technical approach, not implemented:** Stage the complete consistent bool/timestamp/ID state before autoflush, or use no_autoflush around preparation; one explicit flush/commit under current parent lock, rollback/error mapping. Cover both consent directions and verified/unverified links.
- **Related Check IDs:** PROF-04b, PROF-05b, FSP-03b; rollback corroborated DB-07.

### P8-B0-003 — Post-commit refresh can return scalars and skills from different versions

- **Severity / module / status:** P2 / Candidate profiles / Employer Needs responses / Confirmed.
- **Condition:** A commits then starts scalar refresh; B commits a new legitimate full edit before A selectin relationship refresh.
- **Reproduction:** A writes response-0/skill-0. SQL after_cursor_execute checkpoint pauses A refresh after scalar SELECT. B normal service+DTO path commits response-1/skill-1. Release A relationship SELECT. Candidate and Need branches independently repeated by parent.
- **Expected:** A returned DTO describes one coherent committed version; fields and skills are not an impossible mixture. [README.md:467-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L467-L474); coherent profile contract [README.md:188-193](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L188-L193).
- **Actual:** A response is response-0/skill-1; final DB response-1/skill-1. The response combination never existed in committed DB.
- **Evidence:** [backend/app/services/profiles.py:67-68](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/profiles.py#L67-L68); [backend/app/services/employer_needs.py:32-41](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/employer_needs.py#L32-L41); [backend/app/models.py:237-239](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/models.py#L237-L239) and [backend/app/models.py:320-337](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/models.py#L320-L337); Appendix B3; parent2/2 in same6-case11.89s gate.
- **Root cause:** commit releases write lock; refresh scalars and eager selectin relations use different READ COMMITTED snapshots. Locks protect the writes but not later response reconstruction.
- **Impact:** Client can display/retain a profile or Need combination never saved. Stored final state stays coherent; reload is a workaround. Demonstrated at production service + normal DTO constructors, not a network-level response-race capture.
- **Proposed technical approach, not implemented:** Build immutable DTO after flush while still holding write lock and return it only after successful commit, or refresh/serialize in one coherent snapshot. Preserve ownership and atomic write protections; test returned response as well as final DB.
- **Related Check IDs:** PROF-06b, NEED-06b.

### P8-B0-004 — Question-bank loader depends on host default text encoding

- **Severity / module / status:** P3 / Local Windows seed/tests / Confirmed.
- **Condition:** Windows Python3.13 process chooses cp1252 with PYTHONUTF8 unset; UTF-8 Cyrillic question-bank JSON is loaded.
- **Reproduction:** Run scoped auth/profile/Assessment tests in unmodified audit checkout without UTF8 mode. Captured load_bank UnicodeDecodeError cp1252 byte0x8f position214. Repeat same files with PYTHONUTF8=1.
- **Expected:** The bundled UTF-8 source loads consistently in documented local Python setup. [README.md:133-144](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L133-L144).
- **Actual:** Initial69 pass/1 fail/56 errors; corrected126 pass. Docker Linux run unaffected. A separate frozen raw-byte-hash issue is recorded as ENV-02, not silently repaired.
- **Evidence:** [backend/app/question_bank.py:30-40](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/question_bank.py#L30-L40); initial existing-output.txt lines26-44 retained locally; corrected existing-utf8-junit.xml and Appendix A.
- **Root cause:** Path.read_text omits encoding; its default follows host locale and UnicodeDecodeError escapes loader error mapping.
- **Impact:** Local setup/seed and affected test fixtures fail; explicit UTF8 environment mode is a workaround. P3 because isolated local portability and primary Docker path works.
- **Proposed technical approach, not implemented:** Separately specify encoding=UTF-8 and exercise a non-UTF8 Windows locale; preserve source bytes and question content.
- **Related Check IDs:** ENV-01.

### P8-B0-005 — README bank inventory is stale

- **Severity / module / status:** P3 / Assessment documentation / Confirmed.
- **Condition:** A reader uses current README bank/seed subsection as the baseline inventory.
- **Reproduction:** Compare README351–353 (75 records/25 per grade/1-3-1 buckets) with executed test_bank_integrity_and_immutable_seed and current diversity documentation (120/40/2-4-2).
- **Expected:** Current top-level runtime description agrees with current bank, while historical draft provenance remains explicit.
- **Actual:** README still describes prior bank size/distribution; current validator and test load120 questions. No question contents published in evidence.
- **Evidence:** [README.md:351-353](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L351-L353); [docs/assessment-bank-diversity.md:27-37](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/docs/assessment-bank-diversity.md#L27-L37); [backend/tests/test_assessments.py:212-234](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_assessments.py#L212-L234) executed in126-case gate.
- **Root cause:** P5 expansion documented in dedicated file without updating top-level subsection.
- **Impact:** Misleads future validation and spec interpretation. P3 documentation only; not evidence that live scoring fails.
- **Proposed technical approach, not implemented:** Separate documentation change to current inventory and links marking old drafts as historical; no automatic rule/content edits during audit.
- **Related Check IDs:** DOC-01.

### P8-B0-014 — Windows checkout newline conversion breaks sampled raw-byte freeze gates

- **Severity / module / status:** P3 / Local Windows test reproducibility / Confirmed.
- **Condition:** `core.autocrlf=true` produces CRLF checkout bytes for text files whose existing tests compare raw SHA-256 against canonical LF bytes.
- **Reproduction:** Read the saved frontend184-case run and Assessment raw-hash prerequisite error. Compare the two sampled current checkout hashes with `git show HEAD:<path>` in the saved `budget-byte-evidence.log`; the canonical Git blob hashes equal expected values, and reversing CRLF only in memory yields equality. No source file is rewritten.
- **Expected:** Existing raw-byte freeze checks preserve canonical source bytes through checkout, or documented tooling establishes that prerequisite explicitly. Sources: `.gitattributes`, `backend/tests/test_assessment_bank_remediation.py:150-152`, `frontend/tests/brand-ui.test.ts:72-83` at the baseline.
- **Actual:** The completed frontend run fails at the first SVG hash assertion; the Assessment fixture hash prerequisite fails. This establishes the two observed byte mismatches, not later assertions in that combined brand test or the rest of either Assessment suite.
- **Evidence:** Appendix D gives the exact expected/Git/check-out SHA-256 values. Saved `frontend-url.log:185,198` records184 tests/183 pass/1 fail; `budget-byte-evidence.log:2-3` proves canonical blobs and in-memory CRLF reversal equality. Earlier raw fixture gate error is retained in the local Assessment evidence.
- **Root cause:** Git newline conversion changes working bytes while canonical hashes/tests remain byte-dependent; baseline `.gitattributes` protects the Matching dataset but does not cover these sampled Assessment fixture/SVG paths.
- **Impact:** Clean Windows checkout cannot reproduce these byte gates with current settings. P3 local reproducibility only; canonical committed assets are intact. The two excluded Assessment suites remain Not Tested in ENV-02b.
- **Proposed technical approach, not implemented:** In a separate approved task, define LF-preserving attributes or an explicitly canonical-byte verification workflow for the relevant frozen text assets. Test a clean Windows checkout; preserve content/golden labels and do not weaken or rewrite frozen hashes merely to make tests green.
- **Related Check IDs:** ENV-02; incomplete downstream suites remain ENV-02b.

## 8. Potential Findings

### P8-B0-006 — Unbounded Need text becomes persistent candidate inbox payload

- **Severity / module / status:** P2 / Needs / Invitations resource use / Potential.
- **Condition:** Authenticated matching employer supplies very large description/additional_requirements; invitation copies both to immutable snapshot.
- **Reproduction:** Bounded synthetic description262164 characters was accepted by active Need PUT; send201; candidate inbox200 with262974-byte response. No stress/flood performed.
- **Expected:** Cross-user persistent resources have a defined safe text/body/response budget; current product has not specified a concrete size limit.
- **Actual:** No max_length on two fields; snapshot/list carries full text. Actual service exhaustion threshold and ingress limits unknown.
- **Evidence:** [backend/app/need_schemas.py:24-25](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/need_schemas.py#L24-L25); [backend/app/services/invitations.py:133-134](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/invitations.py#L133-L134) and [backend/app/services/invitations.py:300-310](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/invitations.py#L300-L310); Appendix B4; independent security baseline SB-01.
- **Root cause:** No text/body budget at this application boundary; page size bounds item count, not bytes.
- **Impact:** Plausible persistent memory/bandwidth/inbox availability pressure. Acceptance and propagation confirmed; denial of service was not reproduced, so remains Potential.
- **Proposed technical approach, not implemented:** Define backend field caps plus independent ingress body limit; return summaries on list where appropriate; test multi-worker budgets and design historical oversized data handling separately.
- **Related Check IDs:** SEC-01.

### P8-B0-007 — No backend login attempt throttling

- **Severity / module / status:** P2 / Authentication / deployment controls / Potential.
- **Condition:** Endpoint publicly reachable without effective external account/client limiter.
- **Reproduction:** Eight bounded incorrect-password HTTP requests on isolated audit API each401, no429; independently read all auth path/guards. No password guessing success or load attack performed.
- **Expected:** Public deployment must add an effective rate-limiting solution: [README.md:211-212](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L211-L212).
- **Actual:** Every attempt runs Argon2/dummy verification; application stores no failure budget/backoff. Existing documentation already acknowledges an external production requirement.
- **Evidence:** [backend/app/routes/auth.py:25-29](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/routes/auth.py#L25-L29); [backend/app/services/auth.py:77-82](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/app/services/auth.py#L77-L82); Appendix C; independent security SB-02.
- **Root cause:** Throttling delegated to deployment but no configured production gateway was supplied or verified.
- **Impact:** Credential-stuffing/guessing and CPU pressure remain conditional risks; no current public deployment compromise or effective external-control absence established.
- **Proposed technical approach, not implemented:** Before public exposure provide reviewed distributed per-account/client budgets and clear retry responses, including nonexistent accounts without permanent-lockout abuse. Validate gateway/application behavior across workers.
- **Related Check IDs:** SEC-02.

## 9. Product Decisions Required

Все следующие наблюдения воспроизведены. Статус относится к отсутствию нормативного решения, а не к неопределённости результата. Приоритет — порядок принятия решения, не заявленная тяжесть подтверждённой уязвимости.

### P8-B0-008 — Should an existing offer remain accept-able after Need close or candidate eligibility change?

- **Severity / module / status:** P2 / Invitations / Product Decision Required.
- **Condition:** Existing behavior meets code/test convention, but independently approved rule is unavailable.
- **Reproduction:** Need close200 or changed specialization/skills → accept200; immutable snapshot retained. Baseline test intentionally permits this.
- **Expected:** An explicit product rule resolving this branch; no invented requirement.
- **Actual:** Need close200 or changed specialization/skills → accept200; immutable snapshot retained. Baseline test intentionally permits this.
- **Evidence:** Appendix B4 and [backend/tests/test_invitation_privacy.py:152-180](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_privacy.py#L152-L180)
- **Root cause:** Missing normative product decision; no unreviewed state-machine change authorized.
- **Impact:** Ambiguous user/privacy/availability promise; severity not counted as a Confirmed defect.
- **Proposed technical approach, not implemented:** Choose historical offer or current revalidation; define lock order/status checks and contact disclosure semantics atomically if revalidation is selected.
- **Related Check IDs:** INV-04, INV-06b.

### P8-B0-009 — Does personal-data consent withdrawal revoke accepted-contact access?

- **Severity / module / status:** P2 / Consent/privacy / Product Decision Required.
- **Condition:** Existing behavior meets code/test convention, but independently approved rule is unavailable.
- **Reproduction:** Consent=false before or after acceptance → employer candidate_contact still returned, fresh Matching excludes candidate.
- **Expected:** An explicit product rule resolving this branch; no invented requirement.
- **Actual:** Consent=false before or after acceptance → employer candidate_contact still returned, fresh Matching excludes candidate.
- **Evidence:** Appendix B4 and [backend/tests/test_invitation_privacy.py:152-180](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_privacy.py#L152-L180)
- **Root cause:** Missing normative product decision; no unreviewed state-machine change authorized.
- **Impact:** Ambiguous user/privacy/availability promise; severity not counted as a Confirmed defect.
- **Proposed technical approach, not implemented:** Define separate contact-sharing consent or explicit revocation behavior, retention/history and reciprocal access; server policy then needs race tests.
- **Related Check IDs:** INV-07b.

### P8-B0-010 — What cadence/retry limit applies after DECLINED/WITHDRAWN?

- **Severity / module / status:** P2 / Invitations / Product Decision Required.
- **Condition:** Existing behavior meets code/test convention, but independently approved rule is unavailable.
- **Reproduction:** Three consecutive declined invitations to same Need/candidate each allow next send201; active/accepted pairs blocked.
- **Expected:** An explicit product rule resolving this branch; no invented requirement.
- **Actual:** Three consecutive declined invitations to same Need/candidate each allow next send201; active/accepted pairs blocked.
- **Evidence:** Appendix B4 and [backend/tests/test_invitation_privacy.py:152-180](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/backend/tests/test_invitation_privacy.py#L152-L180)
- **Root cause:** Missing normative product decision; no unreviewed state-machine change authorized.
- **Impact:** Ambiguous user/privacy/availability promise; severity not counted as a Confirmed defect.
- **Proposed technical approach, not implemented:** Specify cooldown/cap/abuse policy and scope across Needs; preserve history and DB reservation constraints.
- **Related Check IDs:** INV-10.

### P8-B0-011 — Which actions beyond Assessment require verified email?

- **Severity / module / status:** P2 / Auth / Product Decision Required.
- **Condition:** Existing behavior meets code/test convention, but independently approved rule is unavailable.
- **Reproduction:** Unverified login/profile/Need/send allowed; Assessment start403. Current README permits first-stage login/profile.
- **Expected:** An explicit product rule resolving this branch; no invented requirement.
- **Actual:** Unverified login/profile/Need/send allowed; Assessment start403. Current README permits first-stage login/profile.
- **Evidence:** Appendix A auth events; [README.md:94-102](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L94-L102)
- **Root cause:** Missing normative product decision; no unreviewed state-machine change authorized.
- **Impact:** Ambiguous user/privacy/availability promise; severity not counted as a Confirmed defect.
- **Proposed technical approach, not implemented:** List gated operations explicitly before implementing guards; balance recovery and verified employer contact authenticity.
- **Related Check IDs:** AUTH-08b.

### P8-B0-012 — Is expired verification-link recovery required in MVP?

- **Severity / module / status:** P2 / Auth recovery / Product Decision Required.
- **Condition:** Existing behavior meets code/test convention, but independently approved rule is unavailable.
- **Reproduction:** verify400, duplicate register409, missing resend404, start403; README explicitly defers resend.
- **Expected:** An explicit product rule resolving this branch; no invented requirement.
- **Actual:** verify400, duplicate register409, missing resend404, start403; README explicitly defers resend.
- **Evidence:** Appendix A auth events; [README.md:94-102](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L94-L102)
- **Root cause:** Missing normative product decision; no unreviewed state-machine change authorized.
- **Impact:** Ambiguous user/privacy/availability promise; severity not counted as a Confirmed defect.
- **Proposed technical approach, not implemented:** Approve self-service resend/recovery, mailbox proof, token replacement/TTL/rate limits and concurrency semantics.
- **Related Check IDs:** AUTH-07b.

### P8-B0-013 — Should close cancel in-flight reads that already captured ACTIVE criteria?

- **Severity / module / status:** P3 / Matching/Needs / Product Decision Required.
- **Condition:** Existing behavior meets code/test convention, but independently approved rule is unavailable.
- **Reproduction:** Already captured read returns200; fresh read409. Old captured criteria for ACTIVE edits are explicitly allowed.
- **Expected:** An explicit product rule resolving this branch; no invented requirement.
- **Actual:** Already captured read returns200; fresh read409. Old captured criteria for ACTIVE edits are explicitly allowed.
- **Evidence:** Appendix B1 close probe; [README.md:462-474](https://github.com/ssavantonoff/fsp-platform/blob/acead7a5ea8eb93c1344107440ddb6c16b42173f/README.md#L462-L474)
- **Root cause:** Missing normative product decision; no unreviewed state-machine change authorized.
- **Impact:** Ambiguous user/privacy/availability promise; severity not counted as a Confirmed defect.
- **Proposed technical approach, not implemented:** Define completion/cancellation semantics. Preserve consistent immutable criteria and nonblocking reads if old invocation completion is allowed.
- **Related Check IDs:** MATCH-11b, NEED-07b.

## 10. Severity / status summary

| Status | P0 | P1 | P2 | P3 | Total |
|---|---:|---:|---:|---:|---:|
| Confirmed | 0 | 1 | 2 | 3 | 6 |
| Potential | 0 | 0 | 2 | 0 | 2 |
| Product Decision Required | 0 | 0 | 5 | 1 | 6 |
| Total | 0 | 1 | 9 | 4 | 14 |

Findings and matrix rows have different denominators. One defect can fail several cross-module checks; those rows do not multiply findings. P0 not found in inspected/executed scope, not a universal absence guarantee.

## 11. Successful checks

Anonymous/role/owner controls, session rotation/logout/expiry and one-use verification withstand tested inputs/races. Assessment enforces owner/question/option binding, server deadline and one active attempt; cooldown7/90 days and prior qualification survive failure. Finalization/profile verification is transactional; sampled save/submit/timeout races produce one consistent result. Ordinary specialization/declared-grade/skill/consent/FSP changes propagate correctly to fresh Matching.

Scoring/grade matrix/optional-weight normalization/zero target/FSP bonus cap and unrounded ordering pass synthetic existing tests. Offset pagination is deterministic on unchanged committed inputs; stable paging across mutations is not claimed. Active Need edits are allowed; CLOSED edits and foreign Needs are rejected. Invitations enforce current send eligibility, blocking-pair uniqueness, terminal transitions, idempotent repeats, owner/role boundaries and pre-ACCEPTED allowlists. Send-time snapshots/FSP aggregates survive source edits/unlink. No real FSP ownership claims are made.

## 12. Untested scenarios and limitations

See explicit Not Tested/Potential matrix rows. No production, official FSP, live SMTP, deployment TLS/gateway limiter, cross-site browser cookie trial, complete browser stack, full frontend build/typecheck or sustained performance attack was exercised. Provider failure behavior is tested with controlled doubles; not an external service outage. PostgreSQL17 and API outage/restart were exercised locally on new audit resources.

Two existing Assessment suites (`test_assessment_bank_remediation.py`, `test_assessment_diversity.py`) could not complete their raw-byte freeze gates in Windows CRLF checkout; excluded from corrected general gate and preserved as visible limitations. `test_matching_v2_dataset.py`, `test_matching_v2_golden.py`, `test_matching_v2_review.py` deliberately not executed/read for evaluation. The first general run was interrupted after encoding/hash setup failures, not presented as completed. Three-fixture baseline-byte rewrite was rejected by automatic approval review because frozen writes violate user scope; no rewrite occurred and no bypass was attempted. Frontend had one brand source-byte test failure, explicitly retained.

The existing local Python/Node runtimes were reused read-only; baseline source remained the tested source. Initial loader command error for Windows `--import C:` was corrected to a file URL; frontend runner then actually executed184 tests. None of these environment failures is converted into fabricated product-runtime evidence.

## 13. Infrastructure results

Fresh audit backend image build succeeded. PostgreSQL17.11 applies0001→0002→fbce7259afda→a812e4c79b60→c3d9b7e21a40. Migration round trips/model comparison and DB constraints were exercised in disposable schemas. Dedicated API and DB restart retained one synthetic account; DB stop produced health500 and registration503 with safe envelopes; restart restored200 and account count stayed1. No failed registration row persisted. Source Dockerfile CMD alone does not apply migrations; Compose/documented local commands do. Audit startup supplied migration explicitly.

Continuation runtime limitation (10 October2026): read-only Docker status inspection failed because the Docker Desktop Linux-engine named pipe was unavailable. Current container state was not reverified; prior restart/outage conclusions remain tied to the saved9–10 October evidence. No engine restart, container deletion, volume cleanup or other Docker mutation was performed during continuation.

Audit resources are separately named/labelled P8-B0 and are the only resources eligible for cleanup. No common Docker volume, production database or other agent's testing database was used. No existing compose project reset/down-v.

## 14. Recommended remediation priority

1. P8-B0-001: make all eligibility/scoring inputs one coherent snapshot; reproduce consent/new-PASS race as a failing regression before implementation.
2. P8-B0-002: eliminate intermediate inconsistent consent autoflush; preserve single transaction and add4 combined-edit branches.
3. P8-B0-003: return coherent DTO under a defined snapshot; test both response and persisted state.
4. Resolve post-send eligibility/contact-consent/resend/email-recovery policies before changing Invitations/Auth guards. Audit observations are not authorization to choose these product rules.
5. Before public exposure verify effective login/resource budgets and external controls; Potential cases require bounded targeted validation, not an uncontrolled stress run.
6. Separate low-impact UTF8 and README fixes from Assessment P8-A0. No changes performed here.

## 15. Appendix: reproducible evidence

### Appendix A — executed commands and outcomes

The disposable PostgreSQL fixture uses migrations and UUID schemas; run only against a database you created specifically for this audit. Credentials below are synthetic audit-only values, not production secrets. There are no private dumps or real tokens in this report.

```powershell
$env:PYTHONUTF8='1'
$env:APP_ENV='test'
$env:DATABASE_URL='postgresql+psycopg://p8audit:p8-synthetic-only@127.0.0.1:55438/p8audit'
$env:TEST_DATABASE_URL=$env:DATABASE_URL
# cwd isolated backend, no .env present
python -m pytest tests --ignore=tests/test_matching_v2_dataset.py --ignore=tests/test_matching_v2_golden.py --ignore=tests/test_matching_v2_review.py --ignore=tests/test_assessment_bank_remediation.py --ignore=tests/test_assessment_diversity.py -q -ra --junitxml=../.cache/p8-root/baseline-utf8.xml
```

Completed filtered baseline backend gate: **793 cases; failures=0, errors=0, skipped=0; time=908.982s**.

Independent overlapping gates (do not add totals as distinct test coverage): A/C126 existing passed293.48s and18 additional passed; B/D/E/G357 existing passed320.84s; final B/D/E/G17 passed58.76s =13 synthetic cases +4 existing Assessment cases. Parent repeats3 race cases18.32s; parent combined consent/response6 cases11.89s; parent Invitation/policy/resource observations6 passed14.73s. Reproducer passes assert the **bad behavior**, not a fix. All used PostgreSQL; no fake concurrency skips.

Frontend: Node24.1.0 using installed tsx loader as `file:///.../tsx/dist/loader.mjs`, cwd isolated frontend,184 tests/183 pass/1 fail,15.636s. Only failed test: `official logos and fonts keep source bytes and licenses retain normalized source text` at brand-ui.test.ts83. API/proxy and module contract tests passed; build/typecheck/browser gates were not run.

Auth adversarial event excerpts, containing statuses only:

```text
register4 [201,409,409,409]; verify4 [204,400,400,400]; users1/verifications1
session before deadline200; at deadline401; verify at deadline400
rotated token replay401; logout token replay401
hostile/null/empty/missing Origin: four tested cookie mutations each403, answer unchanged
answer deadline/+1us:409, TIMEOUT finalized, rejected answer absent
last answer vs submit: save-first PASSED70/save200; submit-first FAILED65/save409
timeout save/submit/availability [409,200,200], one PASSED70/TIMEOUT result
```

### Appendix B — temporary probe sources, preserved in this documentation

Save probe files in a new ignored audit-only directory. Create a small wrapper `conftest.py` there containing `from tests.conftest import *`; imported fixture functions retain the original baseline `__file__` and Alembic path. Do not copy the baseline fixture implementation into that directory: its relative Alembic configuration path would change. From isolated `backend`, use `-o pythonpath=". tests"` so both application modules and auth helper imports resolve. Alternatively load `-p tests.conftest` with the same pythonpath, without copying fixture source. Never change production files or existing frozen assets. Test input/ground-truth preparation reads correct option IDs only inside the disposable synthetic attempt setup; question contents and correct-answer keys are not emitted.

#### B1–B3: Matching race, combined consent/FSP PUT, coherent concurrent writes and response snapshots

```python
"""P8-B0 synthetic read/write audit probes. All fixtures use disposable schemas."""
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app.models import AssessmentAttempt, CandidateProfile, EmployerNeed, User
from app.question_bank import seed_questions
from app.schemas import CandidateWrite
from app.need_schemas import NeedWrite
from app.services import profiles, employer_needs, matching
from app.services.candidate_assessments import ProfileAssessmentProvider
from conftest import ORIGIN, PASSWORD


@pytest.fixture
def active_need(client, employer_account, need_data):
    user, _ = employer_account()
    response = client.post('/employer/needs', json=need_data)
    assert response.status_code == 201, response.text
    need_id = response.json()['id']
    assert client.post(f'/employer/needs/{need_id}/activate').status_code == 200
    return user['id'], need_id


def state(db_factory, candidate_id):
    with db_factory() as db:
        p = db.get(CandidateProfile, candidate_id)
        return (p.personal_data_consent, p.verified_grade, p.normalized_assessment_score)


@pytest.mark.parametrize('run', range(3))
def test_reproduce_impossible_consent_qualification_mix(
    client, account, candidate_data, db_factory, employer_account, need_data, app,
    monkeypatch, run
):
    user = account(email=f'p8-race-candidate-{run}@example.com')
    response = client.post('/candidate/profile', json=candidate_data)
    assert response.status_code == 201, response.text
    candidate_id = response.json()['id']
    with db_factory() as db:
        seed_questions(db)
        db.get(User, user['id']).email_verified = True
        db.commit()
    response = client.post('/candidate/assessments', json={'target_grade': 'MIDDLE'})
    assert response.status_code == 201, response.text
    attempt_id = response.json()['id']
    with db_factory() as db:
        attempt = db.get(AssessmentAttempt, attempt_id)
        answers = [(q.id, next(o.id for o in q.question.options if o.is_correct))
                   for q in attempt.questions]
    for question_id, option_id in answers:
        response = client.put(
            f'/candidate/assessments/{attempt_id}/answers/{question_id}',
            json={'selected_option_id': option_id},
        )
        assert response.status_code == 200, response.text
    with TestClient(app, headers={'Origin': ORIGIN}) as candidate_client:
        candidate_client.cookies.clear()
        employer_account(f'p8-race-employer-{run}@example.com')
        response = client.post('/employer/needs', json=need_data)
        assert response.status_code == 201, response.text
        need_id = response.json()['id']
        assert client.post(f'/employer/needs/{need_id}/activate').status_code == 200
        response = candidate_client.post('/auth/login', json={'email': user['email'], 'password': PASSWORD})
        assert response.status_code == 200, response.text
        path = f'/employer/needs/{need_id}/matches'
        assert client.get(path).json()['total'] == 0
        assert state(db_factory, candidate_id) == (True, None, None)
        captured, release = Event(), Event()
        original = ProfileAssessmentProvider.get_assessments
        paused = False
        def checkpoint(provider, ids):
            nonlocal paused
            if not paused:
                paused = True
                captured.set()
                assert release.wait(20), 'matching checkpoint not released'
            return original(provider, ids)
        monkeypatch.setattr(ProfileAssessmentProvider, 'get_assessments', checkpoint)
        with ThreadPoolExecutor(1) as pool:
            read = pool.submit(client.get, path)
            try:
                assert captured.wait(20), 'matching did not capture profile pool'
                response = candidate_client.put('/candidate/profile', json={
                    **candidate_data, 'personal_data_consent': False,
                })
                assert response.status_code == 200, response.text
                assert state(db_factory, candidate_id) == (False, None, None)
                response = candidate_client.post(f'/candidate/assessments/{attempt_id}/submit')
                assert response.status_code == 200, response.text
                assert response.json()['status'] == 'PASSED'
                assert state(db_factory, candidate_id) == (False, 'MIDDLE', 100)
            finally:
                release.set()
            response = read.result(20)
        assert response.status_code == 200, response.text
        stale = response.json()
        fresh = client.get(path).json()
        # Observed bug assertion: no committed state ever satisfied both conditions.
        assert stale['total'] == 1 and stale['items'][0]['candidate_id'] == candidate_id
        assert stale['items'][0]['normalized_assessment_score'] == 100
        assert fresh['total'] == 0
        print(json.dumps({'probe': 'impossible_consent_qualification_mix', 'run': run,
            'committed_states': [[True, None, None], [False, None, None], [False, 'MIDDLE', 100]],
            'paused_matching_total': stale['total'], 'fresh_matching_total': fresh['total'],
            'public_score': stale['items'][0]['normalized_assessment_score']}))


@pytest.mark.parametrize('kind', ['candidate', 'need'])
def test_two_concurrent_full_edits_remain_coherent(
    kind, client, account, candidate_data, matching_candidate, active_need, need_data,
    db_factory, database, monkeypatch, skill_ids
):
    captured, release, attempting = Event(), Event(), Event()
    if kind == 'candidate':
        entity_id = matching_candidate()
        with db_factory() as db:
            owner_id = db.get(CandidateProfile, entity_id).user_id
        payloads = [CandidateWrite(**{**candidate_data, 'first_name': f'writer-{i}',
                    'skill_ids': skill_ids[i:i+1]}) for i in range(2)]
        original = profiles.commit_profile
        def commit(db):
            if db.info.get('writer') == 0:
                db.flush(); captured.set(); assert release.wait(20)
            return original(db)
        monkeypatch.setattr(profiles, 'commit_profile', commit)
        def mutate(db, owner, payload):
            return profiles.save_candidate(db, owner, payload, create=False)
    else:
        owner_id, entity_id = active_need
        payloads = [NeedWrite(**{**need_data, 'position_title': f'writer-{i}',
                    'must_have_skill_ids': skill_ids[i:i+1], 'nice_to_have_skill_ids': []})
                    for i in range(2)]
        original = employer_needs._commit
        def commit(db, need):
            if db.info.get('writer') == 0:
                db.flush(); captured.set(); assert release.wait(20)
            return original(db, need)
        monkeypatch.setattr(employer_needs, '_commit', commit)
        def mutate(db, owner, payload):
            return employer_needs.update_need(db, owner, entity_id, payload)
    def worker(index):
        with db_factory() as db:
            db.execute(text("SET LOCAL lock_timeout = '15s'"))
            db.info['writer'] = index
            owner = db.get(User, owner_id)
            entity = db.get(CandidateProfile if kind == 'candidate' else EmployerNeed, entity_id)
            # Hold stale relationship references across the second lock acquisition.
            retained = list(entity.skills if kind == 'candidate' else entity.skill_requirements)
            if index == 1:
                assert captured.wait(20); attempting.set()
            result = mutate(db, owner, payloads[index])
            return result.id, retained
    with ThreadPoolExecutor(2) as pool:
        first = pool.submit(worker, 0)
        assert captured.wait(20)
        second = pool.submit(worker, 1)
        try:
            assert attempting.wait(20)
            assert not second.done()
        finally:
            release.set()
        assert first.result(20)[0] == entity_id
        assert second.result(20)[0] == entity_id
    with db_factory() as db:
        if kind == 'candidate':
            p = db.get(CandidateProfile, entity_id)
            assert p.first_name == 'writer-1'
            assert [s.id for s in p.skills] == skill_ids[1:2]
            assert (p.verified_grade, p.normalized_assessment_score) == ('MIDDLE', 80)
        else:
            n = db.get(EmployerNeed, entity_id)
            assert n.position_title == 'writer-1'
            assert [s.skill_id for s in n.skill_requirements] == skill_ids[1:2]
            assert n.status == 'ACTIVE'
    print(json.dumps({'probe': 'concurrent_full_edits', 'kind': kind,
        'outcome': 'serialized_last_full_edit_consistent', 'optimistic_versioning': False}))


def test_matching_close_after_criteria_snapshot_is_old_result_then_fresh_conflict(
    client, active_need, matching_candidate, db_factory, monkeypatch
):
    candidate_id = matching_candidate()
    owner_id, need_id = active_need
    path = f'/employer/needs/{need_id}/matches'
    original = matching.load_need_criteria
    captured, release = Event(), Event()
    paused = False
    def checkpoint(db, owner, target):
        nonlocal paused
        result = original(db, owner, target)
        if not paused:
            paused = True; captured.set(); assert release.wait(20)
        return result
    monkeypatch.setattr(matching, 'load_need_criteria', checkpoint)
    with ThreadPoolExecutor(1) as pool:
        read = pool.submit(client.get, path)
        try:
            assert captured.wait(20)
            with db_factory() as db:
                need = employer_needs.close_need(db, db.get(User, owner_id), need_id)
                assert need.status == 'CLOSED'
        finally:
            release.set()
        response = read.result(20)
    assert response.status_code == 200, response.text
    assert response.json()['items'][0]['candidate_id'] == candidate_id
    assert client.get(path).status_code == 409
    print(json.dumps({'probe': 'matching_close_snapshot', 'in_flight_status': 200,
        'fresh_status': 409, 'requirement': 'in_flight_close_not_explicitly_defined'}))


@pytest.mark.parametrize('kind', ['candidate', 'need'])
def test_reproduce_mutation_response_scalar_relation_mix(
    kind, client, account, candidate_data, matching_candidate, active_need,
    need_data, db_factory, database, monkeypatch, skill_ids
):
    from sqlalchemy import event
    from app.schemas import CandidateOut
    if kind == 'candidate':
        entity_id = matching_candidate()
        with db_factory() as db:
            owner_id = db.get(CandidateProfile, entity_id).user_id
        model = CandidateProfile
        payloads = [CandidateWrite(**{**candidate_data, 'first_name': f'response-{i}',
            'skill_ids': skill_ids[i:i+1]}) for i in range(2)]
        def mutate(db, user, payload):
            return profiles.save_candidate(db, user, payload, create=False)
        def result_out(entity):
            value = CandidateOut.model_validate(entity)
            return value.first_name, [s.id for s in value.skills]
    else:
        owner_id, entity_id = active_need
        model = EmployerNeed
        payloads = [NeedWrite(**{**need_data, 'position_title': f'response-{i}',
            'must_have_skill_ids': skill_ids[i:i+1], 'nice_to_have_skill_ids': []})
            for i in range(2)]
        def mutate(db, user, payload):
            return employer_needs.update_need(db, user, entity_id, payload)
        def result_out(entity):
            value = employer_needs.need_out(entity)
            return value.position_title, [s.id for s in value.must_have_skills]
    scalar_fetched, release = Event(), Event()
    first_session = None
    original_refresh = db_factory.class_.refresh
    def refresh(db, entity, *args, **kwargs):
        if db is first_session and isinstance(entity, model):
            db.info['inside_target_refresh'] = True
        try:
            return original_refresh(db, entity, *args, **kwargs)
        finally:
            db.info.pop('inside_target_refresh', None)
    monkeypatch.setattr(db_factory.class_, 'refresh', refresh)
    def after_query(connection, cursor, statement, parameters, context, executemany):
        if first_session is None or not first_session.info.get('inside_target_refresh'):
            return
        if connection is not first_session.connection():
            return
        lowered = statement.lower()
        if 'from ' + model.__tablename__ in lowered and ' join ' not in lowered:
            scalar_fetched.set()
            assert release.wait(20), 'scalar refresh checkpoint not released'
    event.listen(database, 'after_cursor_execute', after_query)
    def first_worker():
        nonlocal first_session
        with db_factory() as db:
            first_session = db
            return result_out(mutate(db, db.get(User, owner_id), payloads[0]))
    try:
        with ThreadPoolExecutor(1) as pool:
            first = pool.submit(first_worker)
            try:
                assert scalar_fetched.wait(20), 'response refresh not captured'
                with db_factory() as db:
                    second = result_out(mutate(db, db.get(User, owner_id), payloads[1]))
                    assert second == ('response-1', skill_ids[1:2])
            finally:
                release.set()
            mixed = first.result(20)
        assert mixed == ('response-0', skill_ids[1:2]), mixed
        with db_factory() as db:
            final = result_out(db.get(model, entity_id))
        assert final == ('response-1', skill_ids[1:2])
        print(json.dumps({'probe': 'mutation_response_scalar_relation_mix', 'kind': kind,
            'first_written_state': ['response-0', 'skill-0'],
            'second_written_state': ['response-1', 'skill-1'],
            'first_returned_state': ['response-0', 'skill-1'],
            'persisted_final_state': ['response-1', 'skill-1']}))
    finally:
        release.set()
        event.remove(database, 'after_cursor_execute', after_query)

@pytest.mark.parametrize('initial_consent', [True, False])
@pytest.mark.parametrize('verified', [True, False])
def test_reproduce_combined_consent_id_edit_autoflush_failure(
    client, app, account, candidate_data, initial_consent, verified
):
    account()
    data = {**candidate_data, 'personal_data_consent': initial_consent,
            'fsp_id': 'MOCK-WINNER'}
    response = client.post('/candidate/profile', json=data)
    assert response.status_code == 201, response.text
    if verified:
        response = client.post('/candidate/fsp/verify', json={})
        assert response.status_code == 200, response.text
    before = client.get('/candidate/profile').json()
    fsp_before = client.get('/candidate/fsp').json()
    with TestClient(app, headers={'Origin': ORIGIN}, raise_server_exceptions=False) as safe:
        safe.cookies.update(client.cookies)
        response = safe.put('/candidate/profile', json={**data,
            'personal_data_consent': not initial_consent, 'fsp_id': 'MOCK-TEAM'})
    assert response.status_code == 500, response.text
    assert client.get('/candidate/profile').json() == before
    assert client.get('/candidate/fsp').json() == fsp_before
    # Positive control: changing only consent succeeds using identical profile/id.
    response = client.put('/candidate/profile', json={**data,
        'personal_data_consent': not initial_consent})
    assert response.status_code == 200, response.text
    assert response.json()['personal_data_consent'] is (not initial_consent)
    assert client.get('/candidate/fsp').json()['fsp_verified'] is verified
    print(json.dumps({'probe': 'combined_consent_id_edit_autoflush_failure',
        'initial_consent': initial_consent, 'verified': verified,
        'combined_edit_status': 500, 'same_id_consent_control_status': 200,
        'failed_edit_preserves_db': True}))


def test_profile_edits_after_real_assessment_propagate_to_fresh_matching(
    client, app, account, candidate_data, db_factory, employer_account, need_data,
):
    user = account()
    response = client.post('/candidate/profile', json=candidate_data)
    assert response.status_code == 201, response.text
    with db_factory() as db:
        seed_questions(db)
        db.get(User, user['id']).email_verified = True
        db.commit()
    response = client.post('/candidate/assessments', json={'target_grade': 'MIDDLE'})
    assert response.status_code == 201, response.text
    attempt_id = response.json()['id']
    with db_factory() as db:
        attempt = db.get(AssessmentAttempt, attempt_id)
        answers = [(q.id, next(o.id for o in q.question.options if o.is_correct))
            for q in attempt.questions]
    for qid, oid in answers:
        assert client.put(f'/candidate/assessments/{attempt_id}/answers/{qid}',
            json={'selected_option_id': oid}).status_code == 200
    assert client.post(f'/candidate/assessments/{attempt_id}/submit').json()['status'] == 'PASSED'
    employer_account()
    response = client.post('/employer/needs', json=need_data)
    assert response.status_code == 201, response.text
    need_id = response.json()['id']
    assert client.post(f'/employer/needs/{need_id}/activate').status_code == 200
    path = f'/employer/needs/{need_id}/matches'
    with TestClient(app, headers={'Origin': ORIGIN}) as owner:
        assert owner.post('/auth/login', json={'email': user['email'], 'password': PASSWORD}).status_code == 200
        def update(**changes):
            response = owner.put('/candidate/profile', json={**candidate_data, **changes})
            assert response.status_code == 200, response.text
            return response.json()
        original = client.get(path).json()
        assert original['total'] == 1
        changed = update(declared_grade='SENIOR')
        assert changed['verified_grade'] == 'MIDDLE'
        assert client.get(path).json() == original
        update(skill_ids=candidate_data['skill_ids'][:1])
        assert client.get(path).json()['total'] == 0
        update()
        assert client.get(path).json() == original
        update(personal_data_consent=False)
        assert client.get(path).json()['total'] == 0
        update()
        assert client.get(path).json() == original
        update(fsp_id='MOCK-WINNER')
        assert owner.post('/candidate/fsp/verify', json={}).json()['fsp_verified'] is True
        winner = client.get(path).json()
        assert winner['items'][0]['fsp_bonus'] == 4
        assert winner['items'][0]['professional_fit_score'] == original['items'][0]['professional_fit_score']
        changed = update(fsp_id='MOCK-TEAM')
        assert changed['verified_grade'] == 'MIDDLE'
        assert owner.get('/candidate/fsp').json()['fsp_verified'] is False
        assert client.get(path).json() == original
        changed = update(specialization='FRONTEND')
        assert [changed[f] for f in ['verified_grade', 'normalized_assessment_score',
            'assessment_verified_at']] == [None, None, None]
        assert client.get(path).json()['total'] == 0
        changed = update()
        assert changed['verified_grade'] == 'MIDDLE' and changed['normalized_assessment_score'] == 100
        assert client.get(path).json() == original
    print(json.dumps({'probe': 'fresh_matching_after_real_assessment_profile_edits',
        'declared_grade_independent': True, 'missing_must_excluded': True,
        'withdrawn_consent_excluded': True, 'fsp_id_change_resets': True,
        'specialization_clear_restore': True}))

```

Commands (after saving the above as `.cache/p8-repro/test_p8_profiles_matching.py` and creating only the fixture wrapper beside it):

```powershell
# from isolated backend; synthetic database settings from Appendix A
python -m pytest -o pythonpath=". tests" ../.cache/p8-repro/test_p8_profiles_matching.py -q -s
# Parent independent focused repeat:
python -m pytest -o pythonpath=". tests" ../.cache/p8-repro/test_p8_profiles_matching.py -k impossible -q -s
python -m pytest -o pythonpath=". tests" ../.cache/p8-repro/test_p8_profiles_matching.py -k 'scalar_relation_mix or combined_consent_id' -q -s
```

Observed deterministic traces:

```text
Matching3/3: [true,null,null]→[false,null,null]→[false,MIDDLE,100]; old total1/score100; fresh total0
Consent+ID4/4: combinedPUT500; same-ID consentPUT200; DB/profile/FSP unchanged after500
Response2/2: A0/skill0→B1/skill1; Areturned0/skill1; finalDB1/skill1
Close after captured criteria: in-flight200, fresh409
```

#### B4: Invitation policy observations and bounded oversized payload

```python
import pytest
from sqlalchemy import select
from app.models import Invitation
from tests.test_invitations import as_user, send

def test_closed_need_accept_observation(client, app, invitation_setup, db_factory):
    s = invitation_setup
    invitation = send(client, s).json()
    assert client.post(f"/employer/needs/{s['need_id']}/close").status_code == 200
    as_user(app, db_factory, s['candidate_user_id'])
    response = client.post(f"/candidate/invitations/{invitation['id']}/accept")
    assert response.status_code == 200
    assert response.json()['status'] == 'ACCEPTED'
    print('OBS closed Need accepts and unlocks employer_contact:', 'employer_contact' in response.json())

@pytest.mark.parametrize('when', ['before_accept', 'after_accept'])
def test_consent_withdrawal_contact_observation(client, app, invitation_setup, db_factory, candidate_data, when):
    s = invitation_setup
    invitation = send(client, s).json()
    as_user(app, db_factory, s['candidate_user_id'])
    if when == 'after_accept':
        assert client.post(f"/candidate/invitations/{invitation['id']}/accept").status_code == 200
    assert client.put('/candidate/profile', json=candidate_data | {'personal_data_consent': False, 'fsp_id': 'PRIVATE_FSP'}).status_code == 200
    if when == 'before_accept':
        assert client.post(f"/candidate/invitations/{invitation['id']}/accept").status_code == 200
    as_user(app, db_factory, s['employer_user_id'])
    detail = client.get(f"/employer/invitations/{invitation['id']}")
    assert detail.status_code == 200
    assert detail.json()['candidate_contact']['email'] == 'private-candidate@example.com'
    assert client.get(f"/employer/needs/{s['need_id']}/matches").json()['total'] == 0
    print('OBS consent=false, mode=', when, ', Matching excluded, accepted contact still returned')

def test_repeated_declines_no_limit_observation(client, app, invitation_setup, db_factory):
    s = invitation_setup
    for i in range(3):
        as_user(app, db_factory, s['employer_user_id'])
        response = send(client, s)
        assert response.status_code == 201
        as_user(app, db_factory, s['candidate_user_id'])
        assert client.post(f"/candidate/invitations/{response.json()['id']}/decline").status_code == 200
    with db_factory() as db:
        assert len(list(db.scalars(select(Invitation)))) == 3
    print('OBS three successive DECLINED invitations permit new send')

def test_profile_edit_snapshot_and_contacts_observation(client, app, invitation_setup, db_factory, candidate_data):
    s = invitation_setup
    sent = send(client, s).json()
    as_user(app, db_factory, s['candidate_user_id'])
    assert client.put('/candidate/profile', json=candidate_data | {'specialization': 'FRONTEND', 'skill_ids': [], 'first_name': 'SyntheticChanged'}).status_code == 200
    assert 'employer_contact' not in client.get(f"/candidate/invitations/{sent['id']}").json()
    assert client.post(f"/candidate/invitations/{sent['id']}/accept").status_code == 200
    as_user(app, db_factory, s['employer_user_id'])
    accepted = client.get(f"/employer/invitations/{sent['id']}").json()
    assert accepted['candidate_snapshot'] == sent['candidate_snapshot']
    assert accepted['candidate_contact']['first_name'] == 'SyntheticChanged'
    print('OBS historical candidate snapshot unchanged, accepted contacts use current profile')

def test_bounded_oversized_need_reaches_inbox(client, app, invitation_setup, db_factory, need_data):
    s = invitation_setup
    marker = 'synthetic-description-' + 'x' * 262144
    response = client.put(f"/employer/needs/{s['need_id']}", json=need_data | {'description': marker})
    assert response.status_code == 200
    sent = send(client, s)
    assert sent.status_code == 201
    as_user(app, db_factory, s['candidate_user_id'])
    inbox = client.get('/candidate/invitations')
    assert inbox.status_code == 200
    assert inbox.json()['items'][0]['need_snapshot']['description'] == marker
    print('OBS bounded oversized Need description accepted; inbox response bytes=', len(inbox.content))

```

This6-case file ran with baseline conftest loaded as `-p tests.conftest`. To reproduce from isolated backend after saving it as `.cache/p8-repro/test_probes.py`: `python -m pytest -o pythonpath=". tests" -p tests.conftest ../.cache/p8-repro/test_probes.py -q -s`. Observed: closed Need accept200/contact; consent=false before/after ACCEPTED still contact returned while Matching total0; three DECLINED allow next send201; profile edits preserve snapshot and return current accepted name; bounded description accepted/inbox262974 bytes. These assert established behavior, not the missing product decision.

#### B5: Auth/Assessment boundary and concurrency probes

Save as `.cache/p8-repro/test_p8_probes.py` with the same fixture wrapper; from isolated backend run `python -m pytest -o pythonpath=". tests" ../.cache/p8-repro/test_p8_probes.py -q -s`. This only describes reproduction; tests were not rerun during final report review.

```python
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from conftest import ORIGIN, PASSWORD
from app import dependencies
from app.models import AuthSession, EmailVerification, User, AssessmentAttempt, CandidateProfile
from app.security import COOKIE_NAME, token_hash
from app.services import auth, assessments
from test_assessments import ready, start, finish, answer_counts, BASE


def record(check, data):
    with (Path(__file__).parent / 'events.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'check': check, 'observed': data}, ensure_ascii=False) + '\n')


def parallel(app, cookies, actions):
    barrier = Barrier(len(actions))
    def request(action):
        method, path, body = action
        with TestClient(app, headers={'Origin': ORIGIN}, cookies=cookies) as peer:
            barrier.wait(timeout=15)
            return peer.request(method, path, json=body)
    with ThreadPoolExecutor(len(actions)) as pool:
        return list(pool.map(request, actions))


def test_p8_anonymous_protected_matrix(client):
    paths = ['/auth/me', '/candidate/profile', '/employer/profile', BASE + '/availability', BASE + '/current', BASE + '/history', '/candidate/fsp', '/candidate/invitations', '/employer/needs']
    actual = {path: client.get(path).status_code for path in paths}
    record('AUTH-01', actual)
    assert set(actual.values()) == {401}


def test_p8_role_spoof_headers_and_query_are_ignored(client, account, candidate_data):
    account(role='CANDIDATE')
    original = client.post('/candidate/profile', json=candidate_data).json()
    result = client.get('/employer/profile?role=EMPLOYER', headers={'X-Role': 'EMPLOYER', 'X-User-ID': original['user_id']})
    mutate = client.put('/auth/me', json={'role': 'EMPLOYER'})
    me = client.get('/auth/me').json()
    record('AUTH-02', {'spoofed_employer_read': result.status_code, 'role_write': mutate.status_code, 'persisted_role': me['role']})
    assert result.status_code == 403 and mutate.status_code == 405 and me['role'] == 'CANDIDATE'


def test_p8_session_rotation_revoked_token_cannot_replay(client, account, app):
    account()
    old = client.cookies[COOKIE_NAME]
    assert client.post('/auth/login', json={'email':'candidate@example.com','password':PASSWORD}).status_code == 200
    new = client.cookies[COOKIE_NAME]
    with TestClient(app, headers={'Origin':ORIGIN}, cookies={COOKIE_NAME:old}) as peer:
        old_status = peer.get('/auth/me').status_code
    assert old != new
    assert client.post('/auth/logout').status_code == 204
    with TestClient(app, headers={'Origin':ORIGIN}, cookies={COOKIE_NAME:new}) as peer:
        new_status = peer.get('/auth/me').status_code
    record('AUTH-04/05', {'replaced_token_replay':old_status,'logged_out_token_replay':new_status})
    assert old_status == new_status == 401


def test_p8_session_and_email_exact_expiry_boundary(client, account, app, db_factory, monkeypatch):
    user = account()
    token = app.state.mailer.tokens[user['email']]
    with db_factory() as db:
        session_deadline = db.get(AuthSession,token_hash(client.cookies[COOKIE_NAME])).expires_at
        verification_deadline = db.get(EmailVerification,token_hash(token)).expires_at
    monkeypatch.setattr(dependencies,'utcnow',lambda:session_deadline-timedelta(microseconds=1))
    before = client.get('/auth/me').status_code
    monkeypatch.setattr(dependencies,'utcnow',lambda:session_deadline)
    at = client.get('/auth/me').status_code
    monkeypatch.setattr(auth,'utcnow',lambda:verification_deadline)
    verify = client.post('/auth/verify-email',json={'token':token})
    with db_factory() as db:
        persisted = db.get(User,user['id']).email_verified
    record('AUTH-04/07',{'session_before_deadline':before,'session_at_deadline':at,'verify_at_deadline':verify.status_code,'email_verified':persisted})
    assert before == 200 and at == 401 and verify.status_code == 400 and persisted is False


def test_p8_four_way_register_and_verify_have_single_winners(client, app, db_factory):
    emails = ['Concurrent@EXAMPLE.COM','concurrent@example.com','CONCURRENT@example.com','concurrent@EXAMPLE.com']
    actions = [('POST','/auth/register',{'email': email,'password':PASSWORD,'role':'CANDIDATE'}) for email in emails]
    registrations = parallel(app,{},actions)
    statuses = sorted(r.status_code for r in registrations)
    token = app.state.mailer.tokens['concurrent@example.com']
    confirmations = parallel(app,{},[('POST','/auth/verify-email',{'token':token})]*4)
    confirmed = sorted(r.status_code for r in confirmations)
    with db_factory() as db:
        counts = {'users':db.scalar(select(func.count()).select_from(User)), 'verifications':db.scalar(select(func.count()).select_from(EmailVerification)), 'email_verified':db.scalar(select(User.email_verified))}
    record('AUTH-06/10',{'register_statuses':statuses,'verify_statuses':confirmed,'persisted':counts})
    assert statuses == [201,409,409,409] and confirmed == [204,400,400,400]
    assert counts == {'users':1,'verifications':1,'email_verified':True}


def test_p8_unverified_email_action_contract(client, account, app, candidate_data, db_factory):
    user = account()
    profile = client.post('/candidate/profile',json=candidate_data)
    start_result = client.post(BASE,json={'target_grade':'MIDDLE'})
    token = app.state.mailer.tokens[user['email']]
    with db_factory() as db:
        row=db.get(EmailVerification,token_hash(token))
        row.expires_at=auth.utcnow()-timedelta(seconds=1)
        db.commit()
    expired = client.post('/auth/verify-email',json={'token':token})
    resend = client.post('/auth/resend-verification',json={'email':user['email']})
    duplicate = client.post('/auth/register',json={'email':user['email'],'password':PASSWORD,'role':'CANDIDATE'})
    record('AUTH-08/PDP-expired-link-recovery',{'login':200,'profile_create':profile.status_code,'start':start_result.status_code,'start_code':start_result.json()['error']['code'],'expired_verify':expired.status_code,'resend_probe':resend.status_code,'register_same_email':duplicate.status_code})
    assert profile.status_code == 201 and start_result.status_code == 403 and start_result.json()['error']['code'] == 'email_not_verified'
    assert expired.status_code==400 and resend.status_code==404 and duplicate.status_code==409


@pytest.mark.parametrize('origin',['https://attacker.example','null','',None])
def test_p8_cookie_csrf_rejection_matrix(client, ready, app, candidate_data, origin):
    attempt=start(client)
    q=attempt['questions'][0]
    mutations=[('POST','/auth/logout',None),('PUT','/candidate/profile',dict(candidate_data,first_name='Forbidden')),('POST',f'{BASE}/{attempt["id"]}/submit',None),('PUT',f'{BASE}/{attempt["id"]}/answers/{q["attempt_question_id"]}',{'selected_option_id':q['options'][0]['id']})]
    actual=[]
    with TestClient(app,cookies=dict(client.cookies),headers={} if origin is None else {'Origin':origin}) as peer:
        for method,path,body in mutations:
            actual.append(peer.request(method,path,json=body).status_code)
    current=client.get(f'{BASE}/{attempt["id"]}').json()
    record('AUTH-09',{'origin':origin,'mutation_statuses':actual,'attempt_status':current['status'],'selection':current['questions'][0]['selected_option_id']})
    assert actual==[403]*4 and current['status']=='IN_PROGRESS' and current['questions'][0]['selected_option_id'] is None


@pytest.mark.parametrize('delta',[0,1])
def test_p8_answer_at_or_after_deadline_cannot_change_state(client,ready,db_factory,monkeypatch,delta):
    attempt=start(client)
    q=attempt['questions'][0]
    deadline=datetime.fromisoformat(attempt['expires_at'])
    monkeypatch.setattr(assessments,'utcnow',lambda:deadline+timedelta(microseconds=delta))
    result=client.put(f'{BASE}/{attempt["id"]}/answers/{q["attempt_question_id"]}',json={'selected_option_id':q['options'][0]['id']})
    with db_factory() as db:
        row=db.get(AssessmentAttempt,attempt['id'])
        observed={'http':result.status_code,'error':result.json()['error']['code'],'status':str(row.status),'reason':str(row.completion_reason),'score':row.normalized_assessment_score,'answer':next(i.selected_option_id for i in row.questions if i.id==q['attempt_question_id']),'finished_at':row.finished_at.isoformat()}
    record('ASM-02',{'microseconds_after_deadline':delta,**observed})
    assert observed['http']==409 and observed['error']=='assessment_finished' and observed['answer'] is None
    assert observed['status']=='FAILED' and observed['reason']=='TIMEOUT' and observed['score']==0 and row.finished_at==deadline


def test_p8_swapped_question_and_option_identifiers_rejected(client,ready):
    attempt=start(client)
    q,other=attempt['questions'][:2]
    wrong_question=client.put(f'{BASE}/{attempt["id"]}/answers/{q["question_id"]}',json={'selected_option_id':q['options'][0]['id']})
    wrong_option=client.put(f'{BASE}/{attempt["id"]}/answers/{q["attempt_question_id"]}',json={'selected_option_id':other['options'][0]['id']})
    current=client.get(f'{BASE}/{attempt["id"]}').json()
    record('ASM-04',{'bank_question_id_as_attempt_question':wrong_question.status_code,'foreign_option':wrong_option.status_code,'saved_answers':sum(q['selected_option_id'] is not None for q in current['questions'])})
    assert wrong_question.status_code==wrong_option.status_code==422 and all(q['selected_option_id'] is None for q in current['questions'])


@pytest.mark.parametrize('repeat',range(3))
def test_p8_last_answer_races_submit_linearizably(client,ready,app,db_factory,repeat):
    attempt=start(client)
    answer_counts(db_factory,attempt,(3,3,3,3,1))
    with db_factory() as db:
        row=db.get(AssessmentAttempt,attempt['id'])
        item=next(i for i in row.questions if i.question.competency=='TESTING_SECURITY_DEBUGGING' and i.selected_option_id is None)
        item_id=item.id
        correct=next(o.id for o in item.question.options if o.is_correct)
    responses=parallel(app,dict(client.cookies),[('PUT',f'{BASE}/{attempt["id"]}/answers/{item_id}',{'selected_option_id':correct}),('POST',f'{BASE}/{attempt["id"]}/submit',None)])
    saved,submitted=responses
    with db_factory() as db:
        row=db.get(AssessmentAttempt,attempt['id'])
        profile=db.get(CandidateProfile,ready['id'])
        observed={'answer_http':saved.status_code,'submit_http':submitted.status_code,'status':str(row.status),'score':row.normalized_assessment_score,'verified_grade':str(profile.verified_grade) if profile.verified_grade else None,'profile_score':profile.normalized_assessment_score,'selected':next(i.selected_option_id for i in row.questions if i.id==item_id) is not None}
    record('ASM-10-last-answer-submit',{'repeat':repeat,**observed})
    assert submitted.status_code==200
    if saved.status_code==200:
        assert observed['status']=='PASSED' and observed['score']==70 and observed['profile_score']==70 and observed['verified_grade']=='MIDDLE' and observed['selected']
    else:
        assert saved.status_code==409 and observed['status']=='FAILED' and observed['score']==65 and observed['profile_score'] is None and observed['verified_grade'] is None and not observed['selected']


def test_p8_deadline_save_submit_and_read_race_agree(client,ready,app,db_factory,monkeypatch):
    attempt=start(client)
    answer_counts(db_factory,attempt,(3,3,3,3,2))
    deadline=datetime.fromisoformat(attempt['expires_at'])
    monkeypatch.setattr(assessments,'utcnow',lambda:deadline)
    q=attempt['questions'][0]
    responses=parallel(app,dict(client.cookies),[('PUT',f'{BASE}/{attempt["id"]}/answers/{q["attempt_question_id"]}',{'selected_option_id':q['options'][0]['id']}),('POST',f'{BASE}/{attempt["id"]}/submit',None),('GET',BASE+'/availability',None)])
    with db_factory() as db:
        row=db.get(AssessmentAttempt,attempt['id'])
        profile=db.get(CandidateProfile,ready['id'])
        observed={'http':[r.status_code for r in responses],'status':str(row.status),'reason':str(row.completion_reason),'score':row.normalized_assessment_score,'profile_score':profile.normalized_assessment_score,'finished_at':row.finished_at.isoformat(),'verified_at':profile.assessment_verified_at.isoformat(),'attempt_count':db.scalar(select(func.count()).select_from(AssessmentAttempt))}
    record('ASM-10-timeout-save-submit-availability',observed)
    assert observed['http']==[409,200,200] and observed['status']=='PASSED' and observed['reason']=='TIMEOUT' and observed['score']==observed['profile_score']==70
    assert row.finished_at==profile.assessment_verified_at==deadline and observed['attempt_count']==1


def test_p8_specialization_edit_races_submit_consistently(client,ready,app,db_factory,candidate_data):
    attempt=start(client)
    answer_counts(db_factory,attempt)
    responses=parallel(app,dict(client.cookies),[('PUT','/candidate/profile',dict(candidate_data,specialization='FRONTEND')),('POST',f'{BASE}/{attempt["id"]}/submit',None)])
    edit,submitted=responses
    profile=client.get('/candidate/profile').json()
    history=client.get(BASE+'/history').json()
    record('ASM-08/10',{'edit_http':edit.status_code,'submit_http':submitted.status_code,'current_specialization':profile['specialization'],'current_verified_grade':profile['verified_grade'],'current_score':profile['normalized_assessment_score'],'attempt_status':history[0]['status'],'attempt_specialization':history[0]['specialization']})
    assert submitted.status_code==200 and history[0]['status']=='PASSED' and history[0]['specialization']=='BACKEND'
    if edit.status_code==409:
        assert profile['specialization']=='BACKEND' and profile['verified_grade']=='MIDDLE' and profile['normalized_assessment_score']==100
    else:
        assert edit.status_code==200 and profile['specialization']=='FRONTEND' and profile['verified_grade'] is None and profile['normalized_assessment_score'] is None
    restored=client.put('/candidate/profile',json=candidate_data).json()
    assert restored['verified_grade']=='MIDDLE' and restored['normalized_assessment_score']==100

```

### Appendix C — bounded live HTTP infrastructure observations

```text
baseline health200
seed twice; skills200
synthetic registration201; users1
API restart: health200/users1
PostgreSQL private-volume restart: health200/users1
DB stopped: health500/internal_error; registration503/registration_unavailable
DB started: health200/users1
failed outage registration absent; no partial account
bounded wrong-password attempts8:401 each, no429 (no stress or successful guess)
```

Infrastructure script used only named newly created resources:

```python
import json, urllib.request, urllib.error, subprocess, time
from pathlib import Path
db='fsp-p8-b0-infra-db-01a12258'
api='fsp-p8-b0-infra-api-01a12258'
out=Path.cwd()/'.cache/p8-root/infra-events.json'
events=[]
def record(**values):
    events.append(values); out.write_text(json.dumps(events,indent=2),encoding='utf-8'); print(json.dumps(values))
def req(path,body=None):
    headers={'Origin':'http://localhost:3000'}
    data=json.dumps(body).encode() if body is not None else None
    if data: headers['Content-Type']='application/json'
    try:
        with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:58438'+path,data=data,headers=headers),timeout=8) as r:
            return r.status,json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code,json.loads(e.read())
def healthy():
    for _ in range(40):
        try:
            status,body=req('/health')
            if status==200: return status,body
        except (OSError,ValueError): pass
        time.sleep(.25)
    raise AssertionError('audit API did not become healthy')
record(stage='baseline_health',result=healthy())
subprocess.run(['docker','exec',api,'python','-m','app.seed'],check=True,capture_output=True)
subprocess.run(['docker','exec',api,'python','-m','app.seed'],check=True,capture_output=True)
record(stage='repeat_seed',skills=req('/skills')[0])
status,body=req('/auth/register',{'email':'p8-infra-only@example.com','password':'p8-infra-synthetic-password','role':'CANDIDATE'})
assert status==201
record(stage='synthetic_register',status=status)
def count():
    return subprocess.check_output(['docker','exec',db,'psql','-U','p8audit','-d','p8infra','-Atc','SELECT count(*) FROM users;'],text=True).strip()
assert count()=='1'
subprocess.run(['docker','restart',api],check=True,capture_output=True)
record(stage='api_restart',health=healthy(),users=count())
subprocess.run(['docker','restart',db],check=True,capture_output=True)
record(stage='db_restart_private_volume',health=healthy(),users=count())
subprocess.run(['docker','stop',db],check=True,capture_output=True)
try:
    status,body=req('/health'); assert status==500 and body['error']['code']=='internal_error'
    record(stage='db_unavailable_health',status=status,code=body['error']['code'])
    status,body=req('/auth/register',{'email':'p8-outage-only@example.com','password':'p8-infra-synthetic-password','role':'CANDIDATE'})
    assert status==503 and body['error']['code']=='registration_unavailable'
    record(stage='db_unavailable_register',status=status,code=body['error']['code'])
finally:
    subprocess.run(['docker','start',db],check=True,capture_output=True)
record(stage='db_recovered',health=healthy(),users=count())
assert count()=='1'
record(stage='outage_no_partial_account',users=count(),passed=True)

```

### Appendix D — source identity / byte-gate limitations / final review

Baseline source review is pinned by SHA links above. Git diff/staged/commit checks restrict this PR to this report; production, migrations, frozen datasets and Assessment files must remain absent from changed-file lists. Original workspace branch/HEAD/status are compared without switching it. Remote main changes after capture do not change this immutable audit target.

Raw-byte mismatch examples: Assessment fixture expected `079e40829c0ac41e8c893971f0b0d586ae7a071bf14d9d2a486466159ad4b30a`, Windows checkout `e77d9375e159defd0ed3c7d5613934f3bf20560fa271a18edca8c9a217ada172`; frontend full logo expected `3e38c1488ec8345eb37bcaa0c807695e9446c881aaa7ceb6a693761493dd3045`, checkout `5e5b15605afdd8f240c8343a8943a6760b4cc4d1760f99d29b9f48d93c7a0c06`. Read-only Git-blob comparison distinguishes checkout transformation from repository content; files were not restored/normalized.

Independent final review: prior reviewer verified mandatory coverage, JUnit and serious evidence, and identified two test-name/fixture-recipe corrections. Continuation reviewer independently classified the sampled byte-gate failure as Confirmed P3 and incomplete Assessment suites as Not Tested; these branches are now separate. Parent corrected cited names/commands, made Expected invariant cells normative, verified102 rows/73 mandatory IDs, every Failed link, severity/status totals, saved test evidence and documentation-only scope. `p8_generate_report.py` remains an uncommitted local generator; it was inspected but not rerun because it would overwrite the reviewed report and old matrix. All original logs/JUnit/probe sources are preserved; the pre-review report is backed up locally. No tests or full security scan were repeated on continuation. Draft PR stays draft/unmerged for Sava review.
