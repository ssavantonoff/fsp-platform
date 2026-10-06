import argparse
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.models import (
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
    utcnow,
)
from app.question_bank import seed_questions
from app.security import password_hasher

SKILLS = ["Python", "Django", "FastAPI", "PostgreSQL", "React", "TypeScript", "SQL"]
DEMO_VERIFIED_AT = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)
MATCHING_STACK = ("Python", "FastAPI", "PostgreSQL", "Django")


def _demo_skills(catalog: dict[str, Skill], names: tuple[str, ...]) -> list[Skill]:
    try:
        return [catalog[name] for name in names]
    except KeyError as exc:
        raise ValueError(f"Missing matching demo skill: {exc.args[0]}") from exc


def _matching_candidate(
    db: Session,
    catalog: dict[str, Skill],
    password: str,
    email: str,
    first_name: str,
    last_name: str,
    *,
    grade: Grade | None = Grade.MIDDLE,
    score: int | None = 90,
    experience: float | None = 3,
    consent: bool = True,
    specialization: Specialization = Specialization.BACKEND,
    skills: tuple[str, ...] = MATCHING_STACK,
) -> None:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            password_hash=password_hasher.hash(password),
            role=Role.CANDIDATE,
            email_verified=True,
        )
        db.add(user)
        db.flush()
    elif user.role != Role.CANDIDATE:
        raise ValueError(f"Matching demo fixture conflict: {email} is not a CANDIDATE")
    if db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id)):
        return
    # Explicit synthetic verification; never create or synchronize assessment history.
    db.add(
        CandidateProfile(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            specialization=specialization,
            declared_grade=grade or Grade.MIDDLE,
            verified_grade=grade,
            normalized_assessment_score=score if grade is not None else None,
            assessment_verified_at=DEMO_VERIFIED_AT if grade is not None else None,
            years_of_experience=experience,
            personal_data_consent=consent,
            personal_data_consent_at=DEMO_VERIFIED_AT if consent else None,
            skills=_demo_skills(catalog, skills),
        )
    )


def _matching_need(
    db: Session,
    catalog: dict[str, Skill],
    employer_id: str,
    need_id: str,
    *,
    title: str,
    grade: Grade,
    experience: float,
    salary_from: int,
    salary_to: int,
    description: str,
    requirements: str | None,
    status: NeedStatus,
    must: tuple[str, ...],
    nice: tuple[str, ...],
) -> None:
    if db.get(EmployerNeed, need_id) is not None:
        return
    db.add(
        EmployerNeed(
            id=need_id,
            employer_id=employer_id,
            position_title=title,
            specialization=Specialization.BACKEND,
            required_grade=grade,
            target_experience_years=experience,
            salary_from=Decimal(salary_from),
            salary_to=Decimal(salary_to),
            description=description,
            additional_requirements=requirements,
            status=status,
            skill_requirements=[
                EmployerNeedSkill(skill=skill, kind=kind)
                for names, kind in (
                    (must, NeedSkillKind.MUST_HAVE),
                    (nice, NeedSkillKind.NICE_TO_HAVE),
                )
                for skill in _demo_skills(catalog, names)
            ],
        )
    )


def _seed_matching_demo(db: Session, password: str) -> None:
    catalog = {skill.name: skill for skill in db.scalars(select(Skill))}
    owner = db.scalar(
        select(EmployerProfile)
        .join(User)
        .where(User.email == "employer@example.com", User.role == Role.EMPLOYER)
    )
    if owner is None:
        raise ValueError(
            "Matching demo requires employer@example.com with an employer profile"
        )
    _matching_need(
        db,
        catalog,
        owner.id,
        "demo-need-backend-middle-active",
        title="Backend Python Engineer",
        grade=Grade.MIDDLE,
        experience=3,
        salary_from=180000,
        salary_to=260000,
        description="Разработка backend-сервисов и API на Python/FastAPI.",
        requirements=(
            "Опыт проектирования REST API и работы с PostgreSQL будет преимуществом."
        ),
        status=NeedStatus.ACTIVE,
        must=("Python", "FastAPI"),
        nice=("PostgreSQL", "Django"),
    )
    _matching_need(
        db,
        catalog,
        owner.id,
        "demo-need-backend-junior-draft",
        title="Junior Python Backend Developer",
        grade=Grade.JUNIOR,
        experience=1,
        salary_from=100000,
        salary_to=150000,
        description="Разработка и поддержка backend-функциональности на Python.",
        requirements=None,
        status=NeedStatus.DRAFT,
        must=("Python",),
        nice=("FastAPI", "PostgreSQL"),
    )
    _matching_need(
        db,
        catalog,
        owner.id,
        "demo-need-backend-senior-closed",
        title="Senior Backend Architect",
        grade=Grade.SENIOR,
        experience=7,
        salary_from=280000,
        salary_to=420000,
        description="Проектирование backend-архитектуры и критичных сервисов.",
        requirements="Опыт проектирования отказоустойчивых систем.",
        status=NeedStatus.CLOSED,
        must=("Python", "PostgreSQL"),
        nice=("FastAPI", "Django"),
    )
    _matching_candidate(
        db, catalog, password, "match-exact@example.com", "Мария", "Смирнова"
    )
    _matching_candidate(
        db,
        catalog,
        password,
        "match-senior@example.com",
        "Алексей",
        "Волков",
        grade=Grade.SENIOR,
        score=100,
    )
    _matching_candidate(
        db,
        catalog,
        password,
        "match-optional@example.com",
        "Ирина",
        "Орлова",
        experience=1.5,
        skills=("Python", "FastAPI", "PostgreSQL"),
    )
    _matching_candidate(
        db,
        catalog,
        password,
        "match-no-experience@example.com",
        "Павел",
        "Морозов",
        experience=None,
    )
    _matching_candidate(
        db,
        catalog,
        password,
        "match-junior@example.com",
        "Денис",
        "Соколов",
        grade=Grade.JUNIOR,
        score=100,
    )
    _matching_candidate(
        db,
        catalog,
        password,
        "match-missing-must@example.com",
        "Ольга",
        "Кузнецова",
        score=100,
        skills=("Python", "PostgreSQL", "Django"),
    )
    _matching_candidate(
        db,
        catalog,
        password,
        "match-unverified@example.com",
        "Никита",
        "Лебедев",
        grade=None,
        score=None,
    )
    _matching_candidate(
        db,
        catalog,
        password,
        "match-no-consent@example.com",
        "Анна",
        "Фёдорова",
        score=100,
        consent=False,
    )
    _matching_candidate(
        db,
        catalog,
        password,
        "match-frontend@example.com",
        "Елена",
        "Новикова",
        score=100,
        specialization=Specialization.FRONTEND,
    )


def seed(
    db: Session,
    *,
    demo: bool = False,
    matching_demo: bool = False,
    demo_password: str | None = None,
) -> None:
    # Repeated runs preserve existing accounts and commit all seed data together.
    with db.begin():
        seed_questions(db)
        for name in SKILLS:
            if db.scalar(select(Skill).where(Skill.name == name)) is None:
                db.add(Skill(name=name))
        db.flush()
        if not (demo or matching_demo):
            return
        if not demo_password or not 10 <= len(demo_password) <= 128:
            raise ValueError("DEMO_PASSWORD must be between 10 and 128 characters")
        for email, role in (
            ("candidate@example.com", Role.CANDIDATE),
            ("employer@example.com", Role.EMPLOYER),
        ):
            user = db.scalar(select(User).where(User.email == email))
            if user is not None:
                continue
            user = User(
                email=email,
                password_hash=password_hasher.hash(demo_password),
                role=role,
                email_verified=True,
            )
            db.add(user)
            db.flush()
            if role == Role.CANDIDATE:
                db.add(
                    CandidateProfile(
                        user_id=user.id,
                        first_name="Алексей",
                        last_name="Иванов",
                        city="Москва",
                        about="Backend-разработчик",
                        specialization="BACKEND",
                        declared_grade=Grade.MIDDLE,
                        verified_grade=None,
                        years_of_experience=3,
                        personal_data_consent=True,
                        personal_data_consent_at=utcnow(),
                        skills=list(
                            db.scalars(
                                select(Skill).where(
                                    Skill.name.in_(["Python", "Django", "PostgreSQL"])
                                )
                            )
                        ),
                    )
                )
            else:
                db.add(
                    EmployerProfile(
                        user_id=user.id,
                        company_name="Demo Tech",
                        company_description="Тестовая компания",
                        website="https://example.com",
                        contact_person_name="Мария Петрова",
                    )
                )
        if matching_demo:
            _seed_matching_demo(db, demo_password)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed skills and optional demo accounts"
    )
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--matching-demo", action="store_true")
    args = parser.parse_args()
    if (args.demo or args.matching_demo) and get_settings().app_env == "production":
        parser.error("Demo accounts are disabled in production")
    with SessionLocal() as db:
        seed(
            db,
            demo=args.demo or args.matching_demo,
            matching_demo=args.matching_demo,
            demo_password=get_settings().demo_password,
        )
    print("Seed completed.")


if __name__ == "__main__":
    main()
