from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import func, inspect, select

from alembic import command
from app.models import CandidateProfile, EmployerProfile, Skill, User
from app.seed import SKILLS, seed


def test_migration_upgrade_downgrade_and_schema_matches_models(database):
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    with database.begin() as connection:
        config.attributes["connection"] = connection
        assert set(inspect(connection).get_table_names()) == {
            "alembic_version",
            "users",
            "auth_sessions",
            "email_verifications",
            "candidate_profiles",
            "employer_profiles",
            "skills",
            "candidate_skills",
        }
        command.check(config)
        command.downgrade(config, "base")
        assert inspect(connection).get_table_names() == ["alembic_version"]
        command.upgrade(config, "head")
        assert "candidate_skills" in inspect(connection).get_table_names()


def test_seed_is_idempotent_and_preserves_accounts(db_factory):
    with db_factory() as db:
        seed(db, demo=True, demo_password="demo-password-one")
    with db_factory() as db:
        user = db.scalar(select(User).where(User.email == "candidate@example.com"))
        original_hash = user.password_hash
    with db_factory() as db:
        seed(db, demo=True, demo_password="demo-password-two")
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(Skill)) == len(SKILLS)
        assert db.scalar(select(func.count()).select_from(User)) == 2
        assert db.scalar(select(func.count()).select_from(EmployerProfile)) == 1
        candidate = db.scalar(select(CandidateProfile))
        assert candidate.declared_grade == "MIDDLE"
        assert candidate.verified_grade is None
        assert {s.name for s in candidate.skills} == {"Python", "Django", "PostgreSQL"}
        user = db.scalar(select(User).where(User.email == "candidate@example.com"))
        assert user.password_hash == original_hash


def test_seed_skills_without_demo(db_factory):
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 0
        assert db.scalar(select(func.count()).select_from(Skill)) == len(SKILLS)


def test_seed_invalid_password_rolls_back(db_factory):
    with db_factory() as db, pytest.raises(ValueError):
        seed(db, demo=True, demo_password="short")
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(Skill)) == 0


def test_health_and_openapi(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert "/auth/me" in schema["paths"]
    assert (
        "verified_grade"
        not in schema["components"]["schemas"]["CandidateWrite"]["properties"]
    )
