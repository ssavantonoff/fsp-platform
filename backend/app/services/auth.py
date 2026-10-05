import logging
from datetime import timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import ApiError
from app.mail import VerificationMailer
from app.models import AuthSession, EmailVerification, User, utcnow
from app.schemas import Login, Register
from app.security import DUMMY_HASH, new_token, password_hasher, token_hash


def register(
    db: Session, data: Register, settings: Settings, mailer: VerificationMailer
) -> User:
    user = User(
        email=str(data.email),
        password_hash=password_hasher.hash(data.password),
        role=data.role,
    )
    token = new_token()
    try:
        db.add(user)
        db.flush()
        db.add(
            EmailVerification(
                token_hash=token_hash(token),
                user_id=user.id,
                expires_at=utcnow()
                + timedelta(seconds=settings.verification_ttl_seconds),
            )
        )
        # Delivery failure rolls back the account so registration can be retried.
        mailer.send(user.email, token)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(409, "email_exists", "Этот email уже зарегистрирован.") from exc
    except Exception as exc:
        db.rollback()
        logging.getLogger("uvicorn.error").error(
            "Registration delivery/commit failed (%s)", type(exc).__name__
        )
        raise ApiError(
            503,
            "registration_unavailable",
            "Регистрация временно недоступна. Повторите.",
        ) from exc
    return user


def verify_email(db: Session, token: str) -> None:
    now = utcnow()
    # One conditional UPDATE atomically consumes a token, including concurrent requests.
    user_id = db.scalar(
        update(EmailVerification)
        .where(
            EmailVerification.token_hash == token_hash(token),
            EmailVerification.consumed_at.is_(None),
            EmailVerification.expires_at > now,
        )
        .values(consumed_at=now)
        .returning(EmailVerification.user_id)
    )
    if user_id is None:
        raise ApiError(400, "invalid_token", "Ссылка недействительна или срок истёк.")
    db.execute(update(User).where(User.id == user_id).values(email_verified=True))
    db.commit()


def login(
    db: Session, data: Login, settings: Settings, previous_token: str | None
) -> tuple[User, str]:
    user = db.scalar(select(User).where(User.email == str(data.email)))
    valid = password_hasher.verify(
        data.password, user.password_hash if user else DUMMY_HASH
    )
    if user is None or not valid:
        raise ApiError(401, "invalid_credentials", "Неверный email или пароль.")
    if previous_token:
        db.execute(
            delete(AuthSession).where(
                AuthSession.token_hash == token_hash(previous_token)
            )
        )
    token = new_token()
    db.add(
        AuthSession(
            token_hash=token_hash(token),
            user_id=user.id,
            expires_at=utcnow() + timedelta(seconds=settings.session_ttl_seconds),
        )
    )
    db.commit()
    return user, token


def logout(db: Session, token: str | None) -> None:
    if token:
        db.execute(
            delete(AuthSession).where(AuthSession.token_hash == token_hash(token))
        )
        db.commit()
