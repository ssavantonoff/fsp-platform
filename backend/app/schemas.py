from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator

from app.models import Grade, Role, Specialization


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(InputModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=1, max_length=128)]

    # Password whitespace is significant; do not apply global string stripping.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class Register(Login):
    password: Annotated[str, Field(min_length=10, max_length=128)]
    role: Role


class Verification(InputModel):
    token: Annotated[str, Field(min_length=32, max_length=128)]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    role: Role
    email_verified: bool
    created_at: datetime
    updated_at: datetime


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str


class CandidateWrite(InputModel):
    first_name: Annotated[str, Field(min_length=1, max_length=100)]
    last_name: Annotated[str, Field(min_length=1, max_length=100)]
    city: Annotated[str | None, Field(max_length=200)] = None
    about: Annotated[str | None, Field(max_length=5000)] = None
    specialization: Specialization
    declared_grade: Grade
    years_of_experience: Annotated[float | None, Field(ge=0, le=80)] = None
    fsp_id: Annotated[str | None, Field(max_length=200)] = None
    personal_data_consent: bool
    skill_ids: Annotated[list[str], Field(max_length=100)] = []

    @field_validator("skill_ids")
    @classmethod
    def unique_skills(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("Skill IDs must be unique")
        return value


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    first_name: str
    last_name: str
    city: str | None
    about: str | None
    specialization: Specialization
    declared_grade: Grade
    verified_grade: Grade | None
    normalized_assessment_score: int | None
    assessment_verified_at: datetime | None
    years_of_experience: float | None
    fsp_id: str | None
    personal_data_consent: bool
    personal_data_consent_at: datetime | None
    skills: list[SkillOut]
    created_at: datetime
    updated_at: datetime

    @field_validator(
        "assessment_verified_at", "personal_data_consent_at", "created_at", "updated_at"
    )
    @classmethod
    def utc_dates(cls, value: datetime | None) -> datetime | None:
        return value.replace(tzinfo=UTC) if value and value.tzinfo is None else value


class EmployerWrite(InputModel):
    company_name: Annotated[str, Field(min_length=1, max_length=200)]
    company_description: Annotated[str | None, Field(max_length=5000)] = None
    website: HttpUrl | None = None
    contact_person_name: Annotated[str, Field(min_length=1, max_length=200)]


class EmployerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    company_name: str
    company_description: str | None
    website: str | None
    contact_person_name: str
    created_at: datetime
    updated_at: datetime


class ErrorDetail(BaseModel):
    code: str
    message: str
    fields: list[dict[str, str]] = []


class ErrorOut(BaseModel):
    error: ErrorDetail
