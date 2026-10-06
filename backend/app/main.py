from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.middleware.base import RequestResponseEndpoint

from app.config import get_settings
from app.dependencies import Db
from app.errors import install_error_handlers
from app.mail import create_mailer
from app.routes import assessments, auth, employer_needs, profiles, skills
from app.schemas import ErrorOut


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="FSP Platform",
        version="0.1.0",
        responses={
            status: {"model": ErrorOut}
            for status in (400, 401, 403, 404, 409, 422, 500, 503)
        },
    )
    app.state.mailer = create_mailer(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response: Response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    install_error_handlers(app)
    app.include_router(auth.router)
    app.include_router(assessments.router)
    app.include_router(profiles.candidate)
    app.include_router(profiles.employer)
    app.include_router(employer_needs.router)
    app.include_router(skills.router)

    @app.get("/health", tags=["health"])
    def health(db: Db) -> dict[str, str]:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()
