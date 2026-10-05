from fastapi import APIRouter, Depends, Request, Response

from app.dependencies import Config, CurrentUser, Db, require_trusted_origin
from app.schemas import Login, Register, UserOut, Verification
from app.security import COOKIE_NAME
from app.services import auth

router = APIRouter(prefix="/auth", tags=["auth"])
mutations = [Depends(require_trusted_origin)]


@router.post(
    "/register", response_model=UserOut, status_code=201, dependencies=mutations
)
def register(data: Register, request: Request, db: Db, settings: Config) -> object:
    return auth.register(db, data, settings, request.app.state.mailer)


@router.post("/verify-email", status_code=204, dependencies=mutations)
def verify_email(data: Verification, db: Db) -> Response:
    auth.verify_email(db, data.token)
    return Response(status_code=204)


@router.post("/login", response_model=UserOut, dependencies=mutations)
def login(
    data: Login, request: Request, response: Response, db: Db, settings: Config
) -> object:
    user, token = auth.login(db, data, settings, request.cookies.get(COOKIE_NAME))
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return user


@router.post("/logout", status_code=204, dependencies=mutations)
def logout(request: Request, db: Db, settings: Config) -> Response:
    auth.logout(db, request.cookies.get(COOKIE_NAME))
    response = Response(status_code=204)
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> object:
    return user
