from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models import FspResultLevel, FspScope
from app.schemas import InputModel


class FspAction(InputModel):
    """No client evidence, identity, score or provider fields are accepted."""


class FspAchievementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    competition_name: str
    discipline: str
    year: int | None
    event_date: datetime | None
    result_level: FspResultLevel
    placement: int | None
    scope: FspScope | None

    @field_validator("event_date")
    @classmethod
    def utc_date(cls, value: datetime | None) -> datetime | None:
        return value.replace(tzinfo=UTC) if value and value.tzinfo is None else value


class FspStatus(BaseModel):
    provider: str = "MOCK"
    fsp_id: str | None
    fsp_verified: bool
    fsp_verified_at: datetime | None
    fsp_synced_at: datetime | None
    fsp_achievement_score: float
    fsp_bonus: float
    competition_count: int
    best_result_level: FspResultLevel | None
    achievements: list[FspAchievementOut]

    @field_validator("fsp_verified_at", "fsp_synced_at")
    @classmethod
    def utc_dates(cls, value: datetime | None) -> datetime | None:
        return value.replace(tzinfo=UTC) if value and value.tzinfo is None else value
