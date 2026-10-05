from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import (
    AssessmentStatus,
    CompletionReason,
    Difficulty,
    Grade,
    Specialization,
)
from app.schemas import CandidateOut, InputModel


class AssessmentStart(InputModel):
    target_grade: Grade


class AnswerWrite(InputModel):
    selected_option_id: Annotated[str, Field(min_length=1, max_length=36)]


class OptionOut(BaseModel):
    id: str
    text: str


class QuestionOut(BaseModel):
    attempt_question_id: str
    question_id: str
    position: int
    competency: str
    difficulty: Difficulty
    prompt: str
    options: list[OptionOut]
    selected_option_id: str | None


class AttemptSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    specialization: Specialization
    target_grade: Grade
    status: AssessmentStatus
    completion_reason: CompletionReason | None
    started_at: datetime
    expires_at: datetime
    finished_at: datetime | None
    normalized_assessment_score: int | None
    competency_scores: dict[str, int] | None
    available_at: datetime | None

    @field_validator("started_at", "expires_at", "finished_at", "available_at")
    @classmethod
    def utc_dates(cls, value: datetime | None) -> datetime | None:
        return value.replace(tzinfo=UTC) if value and value.tzinfo is None else value


class AttemptOut(AttemptSummary):
    server_now: datetime
    questions: list[QuestionOut]
    verification: CandidateOut


class GradeAvailability(BaseModel):
    grade: Grade
    available: bool
    reason: str | None
    available_at: datetime | None


class AvailabilityOut(BaseModel):
    specialization: Specialization
    grades: list[GradeAvailability]
    active_attempt_id: str | None
    server_now: datetime
    verification: CandidateOut
