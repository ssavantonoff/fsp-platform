from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, Field, model_validator

from app.models import Grade, NeedStatus, Specialization
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
