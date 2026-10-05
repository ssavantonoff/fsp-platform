import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import Protocol
from urllib.parse import urlencode

from app.config import Settings

logger = logging.getLogger("uvicorn.error")


class VerificationMailer(Protocol):
    def send(self, email: str, token: str) -> None: ...


class LogMailer:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send(self, email: str, token: str) -> None:
        if self.settings.app_env not in {"development", "test"}:
            raise RuntimeError("Development mail logging is disabled")
        # URL fragments avoid leaking the token into HTTP request/access logs.
        url = f"{self.settings.frontend_url}/verify-email#{urlencode({'token': token})}"
        logger.warning("DEV email verification for %s: %s", email, url)


class SmtpMailer:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send(self, email: str, token: str) -> None:
        message = EmailMessage()
        message["Subject"] = "Подтверждение email — FSP Platform"
        message["From"] = self.settings.smtp_from
        message["To"] = email
        url = f"{self.settings.frontend_url}/verify-email#{urlencode({'token': token})}"
        message.set_content(f"Подтвердите email: {url}")
        with smtplib.SMTP(
            self.settings.smtp_host, self.settings.smtp_port, timeout=10
        ) as server:
            if self.settings.smtp_starttls:
                server.starttls(context=ssl.create_default_context())
            if self.settings.smtp_username:
                server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.send_message(message)


def create_mailer(settings: Settings) -> VerificationMailer:
    return (
        SmtpMailer(settings) if settings.mail_backend == "smtp" else LogMailer(settings)
    )
