from datetime import UTC, datetime
from decimal import Decimal
from math import isnan
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import MetaData, Table, func, inspect, select
from sqlalchemy.exc import IntegrityError

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
            "assessment_questions",
            "assessment_options",
            "assessment_attempts",
            "assessment_attempt_questions",
            "employer_needs",
            "employer_need_skills",
        }
        command.check(config)
        command.downgrade(config, "base")
        assert inspect(connection).get_table_names() == ["alembic_version"]
        command.upgrade(config, "head")
        assert "candidate_skills" in inspect(connection).get_table_names()


def test_need_migration_round_trip_preserves_assessment_state(database, db_factory):
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    with database.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "0002")
    with db_factory() as db:
        seed(db, demo=True, demo_password="migration-test-password")
        candidate = db.scalar(select(CandidateProfile))
        candidate.verified_grade = "MIDDLE"
        candidate.normalized_assessment_score = 73
        candidate.assessment_verified_at = datetime(2026, 10, 5, tzinfo=UTC)
        db.commit()
    with database.begin() as connection:
        config.attributes["connection"] = connection
        original_tables = set(inspect(connection).get_table_names())
        assert "employer_needs" not in original_tables
        assert "employer_need_skills" not in original_tables
        metadata = MetaData()
        metadata.reflect(bind=connection)
        preserved = {
            name: connection.execute(
                select(metadata.tables[name]).order_by(
                    *metadata.tables[name].primary_key
                )
            ).all()
            for name in original_tables - {"alembic_version"}
        }
        for revision in ("head", "0002", "head"):
            if revision == "head":
                command.upgrade(config, revision)
            else:
                command.downgrade(config, revision)
            expected_tables = original_tables | (
                {"employer_needs", "employer_need_skills"}
                if revision == "head"
                else set()
            )
            assert set(inspect(connection).get_table_names()) == expected_tables
            for name, rows in preserved.items():
                assert (
                    connection.execute(
                        select(metadata.tables[name]).order_by(
                            *metadata.tables[name].primary_key
                        )
                    ).all()
                    == rows
                )
        command.check(config)


@pytest.mark.parametrize(
    "changes",
    [
        {"salary_from": -1},
        {"salary_to": -1},
        {"salary_from": 101, "salary_to": 100},
        {"status": "BOGUS"},
        {"specialization": "INVALID"},
        {"required_grade": "BOGUS"},
        {"target_experience_years": -0.1},
        {"employer_id": "unknown-employer"},
    ],
)
def test_need_database_integrity(database, db_factory, changes):
    with db_factory() as db:
        seed(db, demo=True, demo_password="integrity-test-password")
        employer_id = db.scalar(select(EmployerProfile.id))
    with database.begin() as connection:
        needs = Table("employer_needs", MetaData(), autoload_with=connection)
        values = {
            "id": "invalid-need",
            "employer_id": employer_id,
            "position_title": "Backend Engineer",
            "specialization": "BACKEND",
            "required_grade": "MIDDLE",
            "target_experience_years": 2.5,
            "salary_from": 50,
            "salary_to": 100,
            "description": "Build backend services",
            "status": "DRAFT",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(needs.insert().values(values | changes))


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_need_database_integrity_nonfinite_target(database, db_factory, value):
    if database.dialect.name != "postgresql" and isnan(value):
        pytest.skip("SQLite converts NaN to NULL; the NaN check requires PostgreSQL")
    test_need_database_integrity(
        database, db_factory, {"target_experience_years": value}
    )


def test_need_database_integrity_skill_associations(database, db_factory):
    from app.models import EmployerNeed, EmployerNeedSkill, NeedSkillKind, NeedStatus

    with db_factory() as db:
        seed(db, demo=True, demo_password="association-test-password")
        employer_id = db.scalar(select(EmployerProfile.id))
        skill_ids = db.scalars(select(Skill.id).order_by(Skill.id)).all()[:3]
        need = EmployerNeed(
            employer_id=employer_id,
            position_title="Backend Engineer",
            specialization="BACKEND",
            required_grade="MIDDLE",
            target_experience_years=None,
            salary_from=Decimal("50.25"),
            salary_to=Decimal("100.50"),
            description="Build backend services",
            skill_requirements=[
                EmployerNeedSkill(
                    skill_id=skill_ids[1], kind=NeedSkillKind.NICE_TO_HAVE
                ),
                EmployerNeedSkill(skill_id=skill_ids[0], kind=NeedSkillKind.MUST_HAVE),
            ],
        )
        db.add(need)
        db.commit()
        need_id = need.id
    with database.begin() as connection:
        associations = Table(
            "employer_need_skills", MetaData(), autoload_with=connection
        )
        for changes in (
            {"need_id": "unknown-need"},
            {"skill_id": "unknown-skill"},
            {"skill_id": skill_ids[2], "kind": "INVALID"},
            {"kind": "MUST_HAVE"},
            {"kind": "NICE_TO_HAVE"},
        ):
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(
                    associations.insert().values(
                        {
                            "need_id": need_id,
                            "skill_id": skill_ids[0],
                            "kind": "MUST_HAVE",
                        }
                        | changes
                    )
                )
    with db_factory() as db:
        persisted = db.get(EmployerNeed, need_id)
        db.expunge_all()
        assert persisted.status == NeedStatus.DRAFT
        assert persisted.salary_from == Decimal("50.25")
        assert persisted.salary_to == Decimal("100.50")
        assert [item.skill_id for item in persisted.skill_requirements] == skill_ids[:2]
        assert all(item.skill.name for item in persisted.skill_requirements)
    with db_factory() as db:
        persisted = db.get(EmployerNeed, need_id)
        persisted.skill_requirements.pop()
        db.commit()
        assert db.scalar(select(func.count()).select_from(EmployerNeedSkill)) == 1
        db.delete(persisted)
        db.commit()
        assert db.scalar(select(func.count()).select_from(EmployerNeedSkill)) == 0
        assert db.scalar(select(func.count()).select_from(Skill)) == len(SKILLS)
        cascading_need = EmployerNeed(
            employer_id=employer_id,
            position_title="Junior Engineer",
            specialization="BACKEND",
            required_grade="JUNIOR",
            target_experience_years=0,
            salary_from=Decimal("0"),
            salary_to=Decimal("0"),
            description="Learn backend development",
            skill_requirements=[
                EmployerNeedSkill(skill_id=skill_ids[0], kind=NeedSkillKind.MUST_HAVE)
            ],
        )
        db.add(cascading_need)
        db.commit()
        cascading_id = cascading_need.id
    with database.begin() as connection:
        needs = Table("employer_needs", MetaData(), autoload_with=connection)
        associations = Table(
            "employer_need_skills", MetaData(), autoload_with=connection
        )
        connection.execute(needs.delete().where(needs.c.id == cascading_id))
        assert connection.scalar(select(func.count()).select_from(associations)) == 0


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
