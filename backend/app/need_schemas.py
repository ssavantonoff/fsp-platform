from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models import FspResultLevel, Grade, NeedStatus, Specialization
from app.schemas import InputModel, SkillOut

Salary = Annotated[
    Decimal, Field(ge=0, max_digits=12, decimal_places=2, allow_inf_nan=False)
]


class NeedWrite(InputModel):
    position_title: Annotated[str, Field(min_length=1, max_length=200)]
    specialization: Specialization
    required_grade: Grade
    target_experience_years: Annotated[
        float | None, Field(ge=0, allow_inf_nan=False)
    ] = None
    salary_from: Salary
    salary_to: Salary
    description: Annotated[str, Field(min_length=1)]
    additional_requirements: str | None = None
    must_have_skill_ids: Annotated[list[str], Field(min_length=1)]
    nice_to_have_skill_ids: list[str] = []

    @model_validator(mode="after")
    def valid_requirements(self) -> Self:
        if self.salary_from > self.salary_to:
            raise ValueError("Salary range must be ordered")
        must = set(self.must_have_skill_ids)
        nice = set(self.nice_to_have_skill_ids)
        if len(must) != len(self.must_have_skill_ids) or len(nice) != len(
            self.nice_to_have_skill_ids
        ):
            raise ValueError("Skill IDs must be unique within each list")
        if must & nice:
            raise ValueError("Must-have and nice-to-have skills must be disjoint")
        return self


class NeedOut(BaseModel):
    id: str
    employer_id: str
    position_title: str
    specialization: Specialization
    required_grade: Grade
    target_experience_years: float | None
    salary_from: Decimal
    salary_to: Decimal
    description: str
    additional_requirements: str | None
    status: NeedStatus
    created_at: datetime
    updated_at: datetime
    must_have_skills: list[SkillOut]
    nice_to_have_skills: list[SkillOut]


class NeedPage(BaseModel):
    items: list[NeedOut]
    total: int
    limit: int
    offset: int


class FactorBreakdown(BaseModel):
    score: float
    max: float
    active: bool


class GradeBreakdown(FactorBreakdown):
    exact_match: bool


class NiceToHaveBreakdown(FactorBreakdown):
    matched: int
    total: int


class MatchBreakdown(BaseModel):
    assessment: FactorBreakdown
    grade: GradeBreakdown
    nice_to_have: NiceToHaveBreakdown
    experience: FactorBreakdown


class EmployerCandidatePreview(BaseModel):
    ranking_score: float
    fsp_verified: bool
    fsp_achievement_score: float
    fsp_bonus: float
    competition_count: int
    best_result_level: FspResultLevel | None
    candidate_id: str
    display_name: str
    specialization: Specialization
    verified_grade: Grade
    skills: list[SkillOut]
    years_of_experience: float | None
    normalized_assessment_score: int
    assessment_verified_at: datetime | None
    professional_fit_score: float
    breakdown: MatchBreakdown
    matched_must_have_skills: list[SkillOut]
    matched_nice_to_have_skills: list[SkillOut]
    missing_nice_to_have_skills: list[SkillOut]

    @field_validator("assessment_verified_at")
    @classmethod
    def utc_dates(cls, value: datetime | None) -> datetime | None:
        return value.replace(tzinfo=UTC) if value and value.tzinfo is None else value


class MatchesPage(BaseModel):
    items: list[EmployerCandidatePreview]
    total: int
    limit: int
    offset: int
