from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from conftest import ORIGIN, PASSWORD
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.config import Settings
from app.main import create_app
from app.models import AuthSession, EmailVerification, User, utcnow
from app.security import COOKIE_NAME, password_hasher, token_hash


def test_registration_hashes_password_and_stores_only_token_hash(
    client, app, db_factory
):
    result = client.post(
        "/auth/register",
        json={
            "email": "Candidate@EXAMPLE.COM",
            "password": PASSWORD,
            "role": "CANDIDATE",
        },
    )
    assert result.status_code == 201
    assert result.json()["email"] == "candidate@example.com"
    assert result.json()["email_verified"] is False
    assert "password_hash" not in result.json()
    assert "token" not in result.text
    token = app.state.mailer.tokens["candidate@example.com"]
    with db_factory() as db:
        user = db.get(User, result.json()["id"])
        assert user.password_hash != PASSWORD
        assert user.password_hash.startswith("$argon2id$")
        assert password_hasher.verify(PASSWORD, user.password_hash)
        assert db.get(EmailVerification, token_hash(token)) is not None
        assert db.get(EmailVerification, token) is None


def test_duplicate_email_case_insensitive(client, account):
    account()
    result = client.post(
        "/auth/register",
        json={
            "email": "CANDIDATE@example.com",
            "password": PASSWORD,
            "role": "EMPLOYER",
        },
    )
    assert result.status_code == 409
    assert result.json()["error"]["code"] == "email_exists"


@pytest.mark.parametrize(
    "body",
    [
        {"email": "invalid", "password": PASSWORD, "role": "CANDIDATE"},
        {"email": "a@example.com", "password": "short", "role": "CANDIDATE"},
        {"email": "a@example.com", "password": "x" * 129, "role": "CANDIDATE"},
        {"email": "a@example.com", "password": PASSWORD, "role": "ADMIN"},
        {
            "email": "a@example.com",
            "password": PASSWORD,
            "role": "CANDIDATE",
            "email_verified": True,
        },
    ],
)
def test_registration_validation_does_not_echo_password(client, body):
    result = client.post("/auth/register", json=body)
    assert result.status_code == 422
    assert body["password"] not in result.text


def test_login_cookie_and_current_user(client, account, db_factory):
    user = account()
    result = client.post(
        "/auth/login", json={"email": "CANDIDATE@example.com", "password": PASSWORD}
    )
    assert result.status_code == 200
    assert "HttpOnly" in result.headers["set-cookie"]
    assert "SameSite=lax" in result.headers["set-cookie"]
    assert client.get("/auth/me").json()["id"] == user["id"]
    with db_factory() as db:
        session = db.get(AuthSession, token_hash(client.cookies[COOKIE_NAME]))
        assert session is not None
        assert session.token_hash != client.cookies[COOKIE_NAME]
        assert db.scalar(select(func.count()).select_from(AuthSession)) == 1


@pytest.mark.parametrize("email", ["candidate@example.com", "missing@example.com"])
def test_wrong_credentials_are_generic(client, account, email):
    account()
    result = client.post(
        "/auth/login", json={"email": email, "password": "wrong-password"}
    )
    assert result.status_code == 401
    assert result.json()["error"]["code"] == "invalid_credentials"


def test_logout_revokes_session_and_is_repeatable(client, account, app):
    account()
    cookie = client.cookies[COOKIE_NAME]
    assert client.post("/auth/logout").status_code == 204
    assert COOKIE_NAME not in client.cookies
    assert client.get("/auth/me").status_code == 401
    with TestClient(app, headers={"Cookie": f"{COOKIE_NAME}={cookie}"}) as copied:
        assert copied.get("/auth/me").status_code == 401
    assert client.post("/auth/logout").status_code == 204


def test_session_survives_app_restart(client, account, app):
    user = account()
    restarted = create_app()
    restarted.dependency_overrides = app.dependency_overrides.copy()
    with TestClient(restarted, cookies=dict(client.cookies)) as restarted_client:
        assert restarted_client.get("/auth/me").json()["id"] == user["id"]


def test_expired_session_rejected(client, account, db_factory):
    account()
    with db_factory() as db:
        session = db.get(AuthSession, token_hash(client.cookies[COOKIE_NAME]))
        session.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.get("/auth/me").status_code == 401


def test_email_verification_is_one_time(client, account, app, db_factory):
    user = account()
    token = app.state.mailer.tokens[user["email"]]
    assert client.post("/auth/verify-email", json={"token": token}).status_code == 204
    assert client.get("/auth/me").json()["email_verified"] is True
    assert client.post("/auth/verify-email", json={"token": token}).status_code == 400
    with db_factory() as db:
        assert db.get(EmailVerification, token_hash(token)).consumed_at is not None


def test_expired_verification_rejected(client, account, app, db_factory):
    user = account()
    token = app.state.mailer.tokens[user["email"]]
    with db_factory() as db:
        verification = db.get(EmailVerification, token_hash(token))
        verification.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.post("/auth/verify-email", json={"token": token}).status_code == 400
    assert client.get("/auth/me").json()["email_verified"] is False


def test_unknown_verification_rejected(client):
    assert (
        client.post("/auth/verify-email", json={"token": "x" * 43}).status_code == 400
    )


def test_concurrent_verification_has_one_winner(client, account, app, database):
    if database.dialect.name != "postgresql":
        pytest.skip("Concurrent token consumption is checked on PostgreSQL")
    user = account()
    token = app.state.mailer.tokens[user["email"]]

    def confirm(_):
        with TestClient(app, headers={"Origin": ORIGIN}) as peer:
            return peer.post("/auth/verify-email", json={"token": token}).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(confirm, range(2))) == [204, 400]


def test_untrusted_origin_rejected(client, account):
    account()
    result = client.post("/auth/logout", headers={"Origin": "https://attacker.example"})
    assert result.status_code == 403
    assert client.get("/auth/me").status_code == 200


def test_missing_origin_rejected_for_cookie_mutation(client, account, app):
    account()
    with TestClient(app, cookies=dict(client.cookies)) as no_origin:
        assert no_origin.post("/auth/logout").status_code == 403


def test_production_settings_reject_dev_mail_and_insecure_cookies():
    with pytest.raises(ValueError):
        Settings(app_env="production")


def test_secure_cookie_enabled(client, account, app):
    from app.config import get_settings

    account()
    app.dependency_overrides[get_settings] = lambda: Settings(cookie_secure=True)
    result = client.post(
        "/auth/login", json={"email": "candidate@example.com", "password": PASSWORD}
    )
    assert "Secure" in result.headers["set-cookie"]


def test_mail_failure_rolls_back_registration(client, app, db_factory):
    class FailingMailer:
        def send(self, email, token):
            raise OSError("Provider unavailable")

    capture = app.state.mailer
    app.state.mailer = FailingMailer()
    body = {"email": "a@example.com", "password": PASSWORD, "role": "CANDIDATE"}
    assert client.post("/auth/register", json=body).status_code == 503
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 0
        assert db.scalar(select(func.count()).select_from(EmailVerification)) == 0
    app.state.mailer = capture
    assert client.post("/auth/register", json=body).status_code == 201
