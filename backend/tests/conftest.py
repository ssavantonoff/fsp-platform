import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import sessionmaker

from alembic import command
from app.config import Settings, get_settings
from app.db import get_db
from app.main import create_app
from app.models import CandidateProfile, Grade, Role, Skill, Specialization, User

ORIGIN = "http://localhost:3000"
PASSWORD = "valid-test-password"


class CaptureMailer:
    def __init__(self):
        self.tokens = {}

    def send(self, email: str, token: str) -> None:
        self.tokens[email] = token


@pytest.fixture
def database(tmp_path):
    url = os.environ.get("TEST_DATABASE_URL")
    schema = f"fsp_test_{uuid4().hex}"
    admin = None
    if url:
        if not url.startswith("postgresql"):
            raise ValueError("TEST_DATABASE_URL must be a PostgreSQL URL")
        admin = create_engine(url)
        with admin.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    else:
        engine = create_engine(f"sqlite:///{tmp_path}/test.db")

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    try:
        yield engine
    finally:
        engine.dispose()
        if admin is not None:
            with admin.begin() as connection:
                connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin.dispose()


@pytest.fixture
def db_factory(database):
    return sessionmaker(bind=database, expire_on_commit=False)


@pytest.fixture
def app(db_factory):
    application = create_app()
    application.state.mailer = CaptureMailer()

    def db_override():
        with db_factory() as session:
            yield session

    application.dependency_overrides[get_db] = db_override
    application.dependency_overrides[get_settings] = lambda: Settings(app_env="test")
    return application


@pytest.fixture
def client(app):
    with TestClient(app, headers={"Origin": ORIGIN}) as test_client:
        yield test_client


@pytest.fixture
def account(client):
    def create(role="CANDIDATE", email="candidate@example.com"):
        response = client.post(
            "/auth/register", json={"email": email, "password": PASSWORD, "role": role}
        )
        assert response.status_code == 201, response.text
        response = client.post(
            "/auth/login", json={"email": email, "password": PASSWORD}
        )
        assert response.status_code == 200, response.text
        return response.json()

    return create


@pytest.fixture
def skill_ids(db_factory):
    with db_factory() as db:
        skills = [Skill(name=name) for name in ("Python", "Django", "PostgreSQL")]
        db.add_all(skills)
        db.commit()
        return [skill.id for skill in skills]


@pytest.fixture
def candidate_data(skill_ids):
    return {
        "first_name": "Анна",
        "last_name": "Иванова",
        "specialization": "BACKEND",
        "declared_grade": "MIDDLE",
        "personal_data_consent": True,
        "years_of_experience": 2.5,
        "skill_ids": skill_ids,
    }


@pytest.fixture
def employer_data():
    return {"company_name": "Tech", "contact_person_name": "Иван Петров"}


@pytest.fixture
def employer_account(client, account, employer_data):
    def create(email="employer@example.com"):
        user = account(role="EMPLOYER", email=email)
        response = client.post("/employer/profile", json=employer_data)
        assert response.status_code == 201, response.text
        return user, response.json()

    return create


@pytest.fixture
def need_data(skill_ids):
    return {
        "position_title": "Backend developer",
        "specialization": "BACKEND",
        "required_grade": "MIDDLE",
        "target_experience_years": 3,
        "salary_from": "100000.00",
        "salary_to": "200000.00",
        "description": "Build platform services.",
        "additional_requirements": None,
        "must_have_skill_ids": skill_ids[:2],
        "nice_to_have_skill_ids": skill_ids[2:],
    }


@pytest.fixture
def matching_candidate(db_factory, skill_ids):
    def create(**changes):
        with db_factory() as db:
            user = User(
                email=f"private-{uuid4().hex}@example.com",
                password_hash="unused-fixture-hash",
                role=Role.CANDIDATE,
            )
            db.add(user)
            db.flush()
            verified = changes.pop("verified", True)
            consent = changes.pop("personal_data_consent", True)
            selected_skills = changes.pop("skill_ids", skill_ids)
            profile = CandidateProfile(
                user_id=user.id,
                **{
                    "first_name": "Анна",
                    "last_name": "Иванова",
                    "city": "PRIVATE_CITY_ADDRESS",
                    "about": "PRIVATE_PHONE_+79991234567 PRIVATE_TELEGRAM_@anna",
                    "fsp_id": "PRIVATE_FSP",
                    "specialization": Specialization.BACKEND,
                    "declared_grade": Grade.JUNIOR,
                    "years_of_experience": 2,
                    "personal_data_consent": consent,
                    "personal_data_consent_at": datetime(2026, 9, 1, tzinfo=UTC)
                    if consent
                    else None,
                    "verified_grade": Grade.MIDDLE if verified else None,
                    "normalized_assessment_score": 80 if verified else None,
                    "assessment_verified_at": datetime(2026, 9, 18, tzinfo=UTC)
                    if verified
                    else None,
                    **changes,
                },
            )
            profile.skills = list(
                db.scalars(select(Skill).where(Skill.id.in_(selected_skills)))
            )
            db.add(profile)
            db.commit()
            return profile.id

    return create
