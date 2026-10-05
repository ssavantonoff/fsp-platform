import argparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.models import (
    CandidateProfile,
    EmployerProfile,
    Grade,
    Role,
    Skill,
    User,
    utcnow,
)
from app.security import password_hasher

SKILLS = ["Python", "Django", "FastAPI", "PostgreSQL", "React", "TypeScript", "SQL"]


def seed(db: Session, *, demo: bool = False, demo_password: str | None = None) -> None:
    # Repeated runs preserve existing accounts and commit all seed data together.
    with db.begin():
        for name in SKILLS:
            if db.scalar(select(Skill).where(Skill.name == name)) is None:
                db.add(Skill(name=name))
        db.flush()
        if not demo:
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed skills and optional demo accounts"
    )
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo and get_settings().app_env == "production":
        parser.error("Demo accounts are disabled in production")
    with SessionLocal() as db:
        seed(db, demo=args.demo, demo_password=get_settings().demo_password)
    print("Seed completed.")


if __name__ == "__main__":
    main()
