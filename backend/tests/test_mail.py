import ssl

import pytest

from app.config import Settings
from app.mail import LogMailer, SmtpMailer, create_mailer


def test_smtp_adapter_uses_verified_tls_and_sends_fragment_link(monkeypatch):
    calls = []

    class Server:
        def __init__(self, host, port, timeout):
            calls.append((host, port, timeout))

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def starttls(self, *, context):
            assert context.verify_mode == ssl.CERT_REQUIRED
            assert context.check_hostname
            calls.append("tls")

        def login(self, username, password):
            calls.append((username, password))

        def send_message(self, message):
            calls.append(message)

    monkeypatch.setattr("app.mail.smtplib.SMTP", Server)
    settings = Settings(
        app_env="test",
        mail_backend="smtp",
        smtp_host="smtp.example.com",
        smtp_from="platform@example.com",
        smtp_username="sender",
        smtp_password="test-smtp-password",
    )
    mailer = create_mailer(settings)
    assert isinstance(mailer, SmtpMailer)
    mailer.send("candidate@example.com", "test-verification-token")
    assert calls[:3] == [
        ("smtp.example.com", 587, 10),
        "tls",
        ("sender", "test-smtp-password"),
    ]
    message = calls[-1]
    assert message["To"] == "candidate@example.com"
    assert message["From"] == "platform@example.com"
    assert "/verify-email#token=test-verification-token" in message.get_content()


def test_dev_mailer_cannot_log_tokens_in_production():
    settings = Settings(
        app_env="production",
        cookie_secure=True,
        frontend_url="https://platform.example.com",
        mail_backend="smtp",
        smtp_host="smtp.example.com",
        smtp_from="platform@example.com",
    )
    with pytest.raises(RuntimeError):
        LogMailer(settings).send("candidate@example.com", "secret-token")


def test_smtp_configuration_requires_host_and_sender():
    with pytest.raises(ValueError):
        Settings(mail_backend="smtp", smtp_host="", smtp_from="")
