import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select

from app import seed as seed_module
from app.models import (
    AssessmentAttempt,
    AssessmentAttemptQuestion,
    AssessmentQuestion,
    CandidateProfile,
    EmployerNeed,
    EmployerNeedSkill,
    EmployerProfile,
    Grade,
    NeedSkillKind,
    NeedStatus,
    Role,
    Skill,
    Specialization,
    User,
    candidate_skills,
)
from app.seed import SKILLS, seed
from app.services import assessments, matching
from app.services.candidate_assessments import ProfileAssessmentProvider

ACTIVE_ID = "demo-need-backend-middle-active"
NEED_IDS = {
    ACTIVE_ID,
    "demo-need-backend-junior-draft",
    "demo-need-backend-senior-closed",
}
VERIFIED_AT = datetime(2026, 10, 5, 12, tzinfo=UTC)
FULL_STACK = {"Python", "FastAPI", "PostgreSQL", "Django"}
BASE_EMAILS = {"candidate@example.com", "employer@example.com"}
MATCH_EMAILS = {
    f"match-{case}@example.com"
    for case in (
        "exact",
        "senior",
        "optional",
        "no-experience",
        "junior",
        "missing-must",
        "unverified",
        "no-consent",
        "frontend",
    )
}


def rows(db, table):
    return db.execute(select(table).order_by(*table.primary_key)).all()


def snapshot(db):
    return {
        model.__tablename__: rows(db, model.__table__)
        for model in (
            User,
            CandidateProfile,
            EmployerProfile,
            EmployerNeed,
            EmployerNeedSkill,
            AssessmentAttempt,
            AssessmentAttemptQuestion,
        )
    } | {"candidate_skills": rows(db, candidate_skills)}


def candidate(db, email):
    profile = db.scalar(select(CandidateProfile).join(User).where(User.email == email))
    assert profile is not None
    return profile


def test_matching_demo_is_explicit_and_preserves_base_demo(db_factory):
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 0
        assert {s.name for s in db.scalars(select(Skill))} == set(SKILLS)
        assert db.scalar(select(func.count()).select_from(AssessmentQuestion)) == 120
    with db_factory() as db:
        seed(db, demo=True, demo_password=uuid4().hex)
    with db_factory() as db:
        assert set(db.scalars(select(User.email))) == BASE_EMAILS
        assert db.scalar(select(func.count()).select_from(EmployerNeed)) == 0
        profile = candidate(db, "candidate@example.com")
        assert profile.specialization == Specialization.BACKEND
        assert profile.declared_grade == Grade.MIDDLE
        assert (
            profile.verified_grade,
            profile.normalized_assessment_score,
            profile.assessment_verified_at,
        ) == (None, None, None)
        assert {s.name for s in profile.skills} == {"Python", "Django", "PostgreSQL"}
        before = snapshot(db)
    with db_factory() as db:
        seed(db, matching_demo=True, demo_password=uuid4().hex)
    with db_factory() as db:
        after = snapshot(db)
        for table in (
            "users",
            "candidate_profiles",
            "employer_profiles",
            "candidate_skills",
        ):
            assert all(row in after[table] for row in before[table])
        assert set(db.scalars(select(User.email))) == BASE_EMAILS | MATCH_EMAILS
        assert set(db.scalars(select(EmployerNeed.id))) == NEED_IDS
        assert db.scalar(select(func.count()).select_from(CandidateProfile)) == 10
        assert (
            after["assessment_attempts"] == after["assessment_attempt_questions"] == []
        )


def test_matching_demo_is_idempotent_and_preserves_edits(db_factory, database):
    with db_factory() as db:
        seed(db, matching_demo=True, demo_password=uuid4().hex)
    # Use the real Assessment Engine to leave nonempty history to preserve.
    with db_factory() as db:
        base_user = db.scalar(select(User).where(User.email == "candidate@example.com"))
        assessments.start(db, base_user, Grade.MIDDLE)
    with db_factory() as db:
        exact = candidate(db, "match-exact@example.com")
        user = db.get(User, exact.user_id)
        user.password_hash = "preserved-fixture-hash"
        user.email_verified = False
        exact.first_name = "Изменено"
        exact.last_name = "Редактором"
        exact.specialization = Specialization.DATA_ML
        exact.declared_grade = Grade.JUNIOR
        exact.verified_grade = Grade.SENIOR
        exact.normalized_assessment_score = 75
        exact.assessment_verified_at = datetime(2026, 9, 2, 12, tzinfo=UTC)
        exact.years_of_experience = 79  # Existing DB bound is 80, not 99.
        exact.personal_data_consent = False
        exact.personal_data_consent_at = None
        exact.city = "Изменённый город"
        exact.about = "Изменённое описание"
        exact.fsp_id = "synthetic-edited-fsp"
        skills = {s.name: s for s in db.scalars(select(Skill))}
        exact.skills = [skills["Python"], skills["FastAPI"]]
        base = candidate(db, "candidate@example.com")
        base.about = "Base edit retained"
        employer = db.scalar(select(EmployerProfile))
        employer.company_name = "Edited demo company"
        need = db.get(EmployerNeed, ACTIVE_ID)
        need.position_title = "Edited need"
        need.specialization = Specialization.DATA_ML
        need.required_grade = Grade.SENIOR
        need.target_experience_years = 8
        need.salary_from = Decimal("10.25")
        need.salary_to = Decimal("20.50")
        need.description = "Edited description"
        need.additional_requirements = "Edited requirements"
        need.status = NeedStatus.CLOSED
        # Reuse two links, swap kinds and remove the remaining links.
        retained = []
        for link in need.skill_requirements:
            if link.skill.name in {"Python", "PostgreSQL"}:
                link.kind = (
                    NeedSkillKind.NICE_TO_HAVE
                    if link.skill.name == "Python"
                    else NeedSkillKind.MUST_HAVE
                )
                retained.append(link)
        need.skill_requirements = retained
        db.commit()
    with db_factory() as db:
        before = snapshot(db)
        assert len(before["assessment_attempts"]) == 1
        assert len(before["assessment_attempt_questions"]) == 20
    statements = []

    def capture(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower().strip())

    event.listen(database, "before_cursor_execute", capture)
    try:
        with db_factory() as db:
            seed(db, demo=True, matching_demo=True, demo_password=uuid4().hex)
        with db_factory() as db:
            seed(db, matching_demo=True, demo_password=uuid4().hex)
    finally:
        event.remove(database, "before_cursor_execute", capture)
    with db_factory() as db:
        assert snapshot(db) == before  # Includes all scalars, timestamps and relations.
        assert db.scalar(select(func.count()).select_from(Skill)) == 7
    assert not any(
        sql.startswith(("insert", "update", "delete")) and "assessment_attempt" in sql
        for sql in statements
    )


def test_matching_demo_ranking_and_adversarial_cases(db_factory):
    with db_factory() as db:
        seed(db, matching_demo=True, demo_password=uuid4().hex)
    with db_factory() as db:
        users = {u.email: u for u in db.scalars(select(User))}
        profiles = {email: candidate(db, email) for email in MATCH_EMAILS}
        employer = users["employer@example.com"]
        employer_profile = db.scalar(select(EmployerProfile))
        expected_needs = {
            ACTIVE_ID: (
                "Backend Python Engineer",
                Grade.MIDDLE,
                NeedStatus.ACTIVE,
                3,
                Decimal("180000"),
                Decimal("260000"),
                "Разработка backend-сервисов и API на Python/FastAPI.",
                "Опыт проектирования REST API и работы с PostgreSQL "
                "будет преимуществом.",
                {"Python", "FastAPI"},
                {"PostgreSQL", "Django"},
            ),
            "demo-need-backend-junior-draft": (
                "Junior Python Backend Developer",
                Grade.JUNIOR,
                NeedStatus.DRAFT,
                1,
                Decimal("100000"),
                Decimal("150000"),
                "Разработка и поддержка backend-функциональности на Python.",
                None,
                {"Python"},
                {"FastAPI", "PostgreSQL"},
            ),
            "demo-need-backend-senior-closed": (
                "Senior Backend Architect",
                Grade.SENIOR,
                NeedStatus.CLOSED,
                7,
                Decimal("280000"),
                Decimal("420000"),
                "Проектирование backend-архитектуры и критичных сервисов.",
                "Опыт проектирования отказоустойчивых систем.",
                {"Python", "PostgreSQL"},
                {"FastAPI", "Django"},
            ),
        }
        for need in db.scalars(select(EmployerNeed)):
            assert need.employer_id == employer_profile.id
            assert need.specialization == Specialization.BACKEND
            assert (
                need.position_title,
                need.required_grade,
                need.status,
                need.target_experience_years,
                need.salary_from,
                need.salary_to,
                need.description,
                need.additional_requirements,
                {
                    r.skill.name
                    for r in need.skill_requirements
                    if r.kind == NeedSkillKind.MUST_HAVE
                },
                {
                    r.skill.name
                    for r in need.skill_requirements
                    if r.kind == NeedSkillKind.NICE_TO_HAVE
                },
            ) == expected_needs[need.id]
            assert len({r.skill_id for r in need.skill_requirements}) == len(
                need.skill_requirements
            )
        assert set(db.scalars(select(EmployerNeed.id))) == NEED_IDS
        expected_candidates = {
            "exact": ("Мария", "Смирнова", Grade.MIDDLE, 90, 3, FULL_STACK),
            "senior": ("Алексей", "Волков", Grade.SENIOR, 100, 3, FULL_STACK),
            "optional": (
                "Ирина",
                "Орлова",
                Grade.MIDDLE,
                90,
                1.5,
                FULL_STACK - {"Django"},
            ),
            "no-experience": ("Павел", "Морозов", Grade.MIDDLE, 90, None, FULL_STACK),
            "junior": ("Денис", "Соколов", Grade.JUNIOR, 100, 3, FULL_STACK),
            "missing-must": (
                "Ольга",
                "Кузнецова",
                Grade.MIDDLE,
                100,
                3,
                FULL_STACK - {"FastAPI"},
            ),
            "unverified": ("Никита", "Лебедев", None, None, 3, FULL_STACK),
            "no-consent": ("Анна", "Фёдорова", Grade.MIDDLE, 100, 3, FULL_STACK),
            "frontend": ("Елена", "Новикова", Grade.MIDDLE, 100, 3, FULL_STACK),
        }
        for case, expected in expected_candidates.items():
            email = f"match-{case}@example.com"
            profile = profiles[email]
            assert users[email].role == Role.CANDIDATE
            assert users[email].email_verified is True
            assert (
                profile.first_name,
                profile.last_name,
                profile.verified_grade,
                profile.normalized_assessment_score,
                profile.years_of_experience,
                {s.name for s in profile.skills},
            ) == expected
            assert profile.declared_grade == (profile.verified_grade or Grade.MIDDLE)
            assert profile.specialization == (
                Specialization.FRONTEND
                if case == "frontend"
                else Specialization.BACKEND
            )
            assert profile.personal_data_consent is (case != "no-consent")
            assert (profile.personal_data_consent_at is None) is (case == "no-consent")
            verified_at = profile.assessment_verified_at
            assert (verified_at.replace(tzinfo=UTC) if verified_at else None) == (
                None if case == "unverified" else VERIFIED_AT
            )
        result = matching.match_need(
            db, employer, ACTIVE_ID, ProfileAssessmentProvider(db), limit=100, offset=0
        )
        exact_id = profiles["match-exact@example.com"].id
        senior_id = profiles["match-senior@example.com"].id
        optional_id = profiles["match-optional@example.com"].id
        no_exp_id = profiles["match-no-experience@example.com"].id
        assert result.total == 4
        assert [r.candidate_id for r in result.items[:2]] == [exact_id, senior_id]
        assert [r.professional_fit_score for r in result.items[:2]] == [95.5, 93.75]
        by_id = {item.candidate_id: item for item in result.items}
        assert set(by_id) == {exact_id, senior_id, optional_id, no_exp_id}
        assert by_id[exact_id].normalized_assessment_score == 90
        assert by_id[senior_id].normalized_assessment_score == 100
        for profile_id, expected in (
            (exact_id, [40.5, 25, 15, 15]),
            (senior_id, [45, 18.75, 15, 15]),
        ):
            breakdown = by_id[profile_id].breakdown
            assert [
                getattr(breakdown, key).score
                for key in ("assessment", "grade", "nice_to_have", "experience")
            ] == expected
        optional = by_id[optional_id]
        assert optional.professional_fit_score == 80.5
        assert optional.breakdown.nice_to_have.matched == 1
        assert optional.breakdown.nice_to_have.total == 2
        assert optional.breakdown.nice_to_have.score == 7.5
        assert optional.breakdown.experience.score == 7.5
        no_exp = by_id[no_exp_id]
        assert no_exp.professional_fit_score == 80.5
        assert no_exp.breakdown.experience.active is True
        assert no_exp.breakdown.experience.max == 15
        assert no_exp.breakdown.experience.score == 0
        assert candidate(db, "candidate@example.com").id not in by_id
        assert all(
            profiles[email].id not in by_id
            for email in MATCH_EMAILS
            - {
                "match-exact@example.com",
                "match-senior@example.com",
                "match-optional@example.com",
                "match-no-experience@example.com",
            }
        )
        for case in ("junior", "missing-must", "no-consent"):
            assert (
                profiles[f"match-{case}@example.com"].normalized_assessment_score == 100
            )
        # Real previews contain masked names and no fixture contacts/private fields.
        assert by_id[exact_id].display_name == "Мария С."
        serialized = result.model_dump_json()
        for forbidden in (
            "@example.com",
            "Смирнова",
            '"user_id"',
            '"personal_data_consent"',
            '"declared_grade"',
        ):
            assert forbidden not in serialized


@pytest.mark.parametrize(
    "flags", [["--matching-demo"], ["--demo"], ["--demo", "--matching-demo"]]
)
def test_matching_demo_rejected_in_production(monkeypatch, capsys, flags):
    monkeypatch.setattr(sys, "argv", ["app.seed", *flags])
    monkeypatch.setattr(
        seed_module, "get_settings", lambda: SimpleNamespace(app_env="production")
    )

    def reject_session():
        pytest.fail("Production demo must be rejected before opening a seed session")

    monkeypatch.setattr(seed_module, "SessionLocal", reject_session)
    with pytest.raises(SystemExit) as exc:
        seed_module.main()
    assert exc.value.code == 2
    assert "Demo accounts are disabled in production" in capsys.readouterr().err


@pytest.mark.parametrize("password", [None, "", "x" * 9, "x" * 129])
def test_matching_demo_invalid_password_rolls_back(db_factory, password):
    with db_factory() as db, pytest.raises(ValueError, match="DEMO_PASSWORD"):
        seed(db, matching_demo=True, demo_password=password)
    with db_factory() as db:
        for model in (
            User,
            CandidateProfile,
            EmployerProfile,
            EmployerNeed,
            Skill,
            AssessmentQuestion,
        ):
            assert db.scalar(select(func.count()).select_from(model)) == 0


def test_matching_demo_role_conflict_rolls_back(db_factory):
    with db_factory() as db:
        seed(db)
        db.add(
            User(
                email="match-senior@example.com",
                role=Role.EMPLOYER,
                password_hash="existing-fixture-hash",
                email_verified=False,
            )
        )
        db.commit()
    with db_factory() as db:
        before = snapshot(db)
    with (
        db_factory() as db,
        pytest.raises(ValueError, match="match-senior@example.com"),
    ):
        seed(db, matching_demo=True, demo_password=uuid4().hex)
    with db_factory() as db:
        assert snapshot(db) == before


def test_matching_demo_missing_catalog_skill_rolls_back(db_factory, monkeypatch):
    monkeypatch.setattr(seed_module, "SKILLS", [s for s in SKILLS if s != "FastAPI"])
    with db_factory() as db, pytest.raises(ValueError, match="Missing.*FastAPI"):
        seed(db, matching_demo=True, demo_password=uuid4().hex)
    with db_factory() as db:
        assert all(not table_rows for table_rows in snapshot(db).values())
        assert db.scalar(select(func.count()).select_from(Skill)) == 0
        assert db.scalar(select(func.count()).select_from(AssessmentQuestion)) == 0


@pytest.mark.parametrize("length", [10, 128])
def test_matching_demo_creates_missing_candidate_profile(db_factory, length):
    with db_factory() as db:
        db.add(
            User(
                email="match-exact@example.com",
                role=Role.CANDIDATE,
                password_hash="existing-fixture-hash",
                email_verified=False,
            )
        )
        db.commit()
    with db_factory() as db:
        seed(db, matching_demo=True, demo_password=(uuid4().hex * 4)[:length])
    with db_factory() as db:
        profile = candidate(db, "match-exact@example.com")
        user = db.get(User, profile.user_id)
        assert user.password_hash == "existing-fixture-hash"
        assert user.email_verified is False
        assert user.role == Role.CANDIDATE
        assert profile.normalized_assessment_score == 90


@pytest.mark.parametrize(
    "flags", [[], ["--demo"], ["--matching-demo"], ["--demo", "--matching-demo"]]
)
def test_seed_cli_forwards_explicit_modes(monkeypatch, db_factory, flags):
    calls = []
    settings = SimpleNamespace(app_env="test", demo_password=uuid4().hex)
    monkeypatch.setattr(sys, "argv", ["app.seed", *flags])
    monkeypatch.setattr(seed_module, "get_settings", lambda: settings)
    monkeypatch.setattr(seed_module, "SessionLocal", db_factory)
    monkeypatch.setattr(seed_module, "seed", lambda db, **kwargs: calls.append(kwargs))
    seed_module.main()
    assert calls == [
        {
            "demo": bool(flags),
            "matching_demo": "--matching-demo" in flags,
            "demo_password": settings.demo_password,
        }
    ]
