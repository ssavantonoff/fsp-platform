from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import FspResultLevel, Grade, InvitationStatus, Specialization
from app.need_schemas import MatchBreakdown
from app.schemas import InputModel, SkillOut


class InvitationSend(InputModel):
    # Preserve the optional plain-text message, including significant whitespace.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    candidate_id: Annotated[str, Field(min_length=1, max_length=36)]
    message: Annotated[str | None, Field(max_length=2000)] = None


class NeedSnapshot(BaseModel):
    need_id: str
    position_title: str
    specialization: Specialization
    required_grade: Grade
    target_experience_years: float | None
    salary_from: str
    salary_to: str
    description: str
    additional_requirements: str | None
    must_have_skills: list[SkillOut]
    nice_to_have_skills: list[SkillOut]
    company_name: str


class StoredNeedSnapshot(NeedSnapshot):
    contact_person_name: str
    website: str | None


class CandidateSnapshot(BaseModel):
    # Historical V1 evidence has no P4 explanation: never fabricate it on read.
    ranking_score: float | None = None
    fsp_verified: bool | None = None
    fsp_achievement_score: float | None = None
    fsp_bonus: float | None = None
    competition_count: int | None = None
    best_result_level: FspResultLevel | None = None
    candidate_id: str
    display_name: str
    specialization: Specialization
    verified_grade: Grade
    normalized_assessment_score: int
    assessment_verified_at: datetime | None
    professional_fit_score: float
    breakdown: MatchBreakdown

    @field_validator("assessment_verified_at")
    @classmethod
    def utc_dates(cls, value: datetime | None) -> datetime | None:
        return value.replace(tzinfo=UTC) if value and value.tzinfo is None else value


class CandidateContact(BaseModel):
    first_name: str
    last_name: str
    email: str


class EmployerContact(BaseModel):
    company_name: str
    contact_person_name: str
    email: str
    website: str | None


class InvitationOut(BaseModel):
    id: str
    need_id: str
    status: InvitationStatus
    message: str | None
    need_snapshot: NeedSnapshot
    sent_at: datetime
    viewed_at: datetime | None
    responded_at: datetime | None
    withdrawn_at: datetime | None

    @field_validator("sent_at", "viewed_at", "responded_at", "withdrawn_at")
    @classmethod
    def utc_dates(cls, value: datetime | None) -> datetime | None:
        return value.replace(tzinfo=UTC) if value and value.tzinfo is None else value


class EmployerInvitationOut(InvitationOut):
    candidate_snapshot: CandidateSnapshot
    candidate_contact: CandidateContact | None = None


class CandidateInvitationOut(InvitationOut):
    employer_contact: EmployerContact | None = None


class EmployerInvitationPage(BaseModel):
    items: list[EmployerInvitationOut]
    total: int
    limit: int
    offset: int


class CandidateInvitationPage(BaseModel):
    items: list[CandidateInvitationOut]
    total: int
    limit: int
    offset: int
