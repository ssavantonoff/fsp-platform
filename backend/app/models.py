from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid4())


class Role(StrEnum):
    CANDIDATE = "CANDIDATE"
    EMPLOYER = "EMPLOYER"


class Specialization(StrEnum):
    BACKEND = "BACKEND"
    FRONTEND = "FRONTEND"
    DATA_ML = "DATA_ML"


class Grade(StrEnum):
    JUNIOR = "JUNIOR"
    MIDDLE = "MIDDLE"
    SENIOR = "SENIOR"


class Difficulty(StrEnum):
    BASIC = "BASIC"
    APPLIED = "APPLIED"
    ADVANCED = "ADVANCED"


class AssessmentStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    PASSED = "PASSED"
    FAILED = "FAILED"


class CompletionReason(StrEnum):
    SUBMITTED = "SUBMITTED"
    TIMEOUT = "TIMEOUT"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(
        Enum(Role, native_enum=False, create_constraint=True)
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


candidate_skills = Table(
    "candidate_skills",
    Base.metadata,
    Column(
        "candidate_id",
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class CandidateProfile(TimestampMixin, Base):
    __tablename__ = "candidate_profiles"
    __table_args__ = (
        CheckConstraint(
            "years_of_experience IS NULL OR years_of_experience BETWEEN 0 AND 80",
            name="valid_experience",
        ),
        CheckConstraint(
            "(personal_data_consent = true "
            "AND personal_data_consent_at IS NOT NULL) OR "
            "(personal_data_consent = false AND personal_data_consent_at IS NULL)",
            name="consistent_consent",
        ),
        CheckConstraint(
            "normalized_assessment_score BETWEEN 0 AND 100",
            name="valid_assessment_score",
        ),
        CheckConstraint(
            "(verified_grade IS NULL AND normalized_assessment_score IS NULL "
            "AND assessment_verified_at IS NULL) OR "
            "(verified_grade IS NOT NULL AND normalized_assessment_score IS NOT NULL "
            "AND assessment_verified_at IS NOT NULL)",
            name="consistent_verification",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(200))
    about: Mapped[str | None] = mapped_column(Text)
    specialization: Mapped[Specialization] = mapped_column(
        Enum(Specialization, native_enum=False, create_constraint=True)
    )
    declared_grade: Mapped[Grade] = mapped_column(
        Enum(Grade, native_enum=False, create_constraint=True, name="declared_grade")
    )
    verified_grade: Mapped[Grade | None] = mapped_column(
        Enum(Grade, native_enum=False, create_constraint=True, name="verified_grade")
    )
    normalized_assessment_score: Mapped[int | None] = mapped_column(Integer)
    assessment_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    years_of_experience: Mapped[float | None] = mapped_column(Float)
    fsp_id: Mapped[str | None] = mapped_column(String(200))
    personal_data_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    personal_data_consent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    skills: Mapped[list[Skill]] = relationship(
        secondary=candidate_skills, lazy="selectin", order_by="Skill.name"
    )


class EmployerProfile(TimestampMixin, Base):
    __tablename__ = "employer_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    company_name: Mapped[str] = mapped_column(String(200))
    company_description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(2048))
    contact_person_name: Mapped[str] = mapped_column(String(200))


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(120), unique=True)
    specialization: Mapped[Specialization] = mapped_column(
        Enum(Specialization, native_enum=False, create_constraint=True)
    )
    grade: Mapped[Grade] = mapped_column(
        Enum(Grade, native_enum=False, create_constraint=True)
    )
    competency: Mapped[str] = mapped_column(String(60))
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty, native_enum=False, create_constraint=True)
    )
    prompt: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    options: Mapped[list[AssessmentOption]] = relationship(lazy="selectin")
    __table_args__ = (
        Index("ix_assessment_question_bank", "specialization", "grade", "is_active"),
    )


class AssessmentOption(Base):
    __tablename__ = "assessment_options"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    question_id: Mapped[str] = mapped_column(
        ForeignKey("assessment_questions.id"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidate_profiles.id"), index=True
    )
    specialization: Mapped[Specialization] = mapped_column(
        Enum(Specialization, native_enum=False, create_constraint=True)
    )
    target_grade: Mapped[Grade] = mapped_column(
        Enum(Grade, native_enum=False, create_constraint=True)
    )
    status: Mapped[AssessmentStatus] = mapped_column(
        Enum(AssessmentStatus, native_enum=False, create_constraint=True),
        default=AssessmentStatus.IN_PROGRESS,
    )
    completion_reason: Mapped[CompletionReason | None] = mapped_column(
        Enum(CompletionReason, native_enum=False, create_constraint=True)
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    normalized_assessment_score: Mapped[int | None] = mapped_column(Integer)
    competency_scores: Mapped[dict[str, int] | None] = mapped_column(JSON)
    questions: Mapped[list[AssessmentAttemptQuestion]] = relationship(
        lazy="selectin", order_by="AssessmentAttemptQuestion.position"
    )
    __table_args__ = (
        Index(
            "uq_assessment_active_candidate",
            "candidate_id",
            unique=True,
            postgresql_where=text("status = 'IN_PROGRESS'"),
            sqlite_where=text("status = 'IN_PROGRESS'"),
        ),
        CheckConstraint(
            "normalized_assessment_score BETWEEN 0 AND 100", name="valid_attempt_score"
        ),
        CheckConstraint(
            "(status = 'IN_PROGRESS' AND completion_reason IS NULL AND "
            "finished_at IS NULL "
            "AND normalized_assessment_score IS NULL AND competency_scores IS NULL) OR "
            "(status <> 'IN_PROGRESS' AND completion_reason IS NOT NULL AND "
            "finished_at IS NOT NULL "
            "AND normalized_assessment_score IS NOT NULL AND "
            "competency_scores IS NOT NULL)",
            name="consistent_attempt_result",
        ),
    )


class AssessmentAttemptQuestion(Base):
    __tablename__ = "assessment_attempt_questions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    attempt_id: Mapped[str] = mapped_column(
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[str] = mapped_column(ForeignKey("assessment_questions.id"))
    position: Mapped[int] = mapped_column(Integer)
    option_order: Mapped[list[str]] = mapped_column(JSON)
    selected_option_id: Mapped[str | None] = mapped_column(
        ForeignKey("assessment_options.id")
    )
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    question: Mapped[AssessmentQuestion] = relationship(lazy="selectin")
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),
        UniqueConstraint("attempt_id", "position", name="uq_attempt_position"),
        CheckConstraint("position BETWEEN 1 AND 20", name="valid_attempt_position"),
    )
