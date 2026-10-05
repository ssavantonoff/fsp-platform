from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.errors import ApiError
from app.models import AuthSession, Role, User, utcnow
from app.security import COOKIE_NAME, token_hash

Db = Annotated[Session, Depends(get_db)]
Config = Annotated[Settings, Depends(get_settings)]


def require_trusted_origin(request: Request, settings: Config) -> None:
    origin = request.headers.get("origin")
    # Cookie-authenticated mutations require Origin; CLI clients must supply it too.
    if origin not in settings.allowed_origins and (
        origin is not None or request.cookies.get(COOKIE_NAME)
    ):
        raise ApiError(403, "untrusted_origin", "Запрос из недоверенного источника.")


def current_user(request: Request, db: Db) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise ApiError(401, "unauthorized", "Войдите в аккаунт.")
    user = db.scalar(
        select(User)
        .join(AuthSession, AuthSession.user_id == User.id)
        .where(
            AuthSession.token_hash == token_hash(token),
            AuthSession.expires_at > utcnow(),
        )
    )
    if user is None:
        raise ApiError(401, "unauthorized", "Сессия завершена. Войдите снова.")
    return user


def candidate_user(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role != Role.CANDIDATE:
        raise ApiError(403, "forbidden", "Доступно только кандидатам.")
    return user


def employer_user(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role != Role.EMPLOYER:
        raise ApiError(403, "forbidden", "Доступно только работодателям.")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
CandidateUser = Annotated[User, Depends(candidate_user)]
EmployerUser = Annotated[User, Depends(employer_user)]
