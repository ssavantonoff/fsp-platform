"""Fixture-only registry prototype. No network or real identity authentication."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.models import FspResultLevel, FspScope


class RegistryAchievement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    external_id: str = Field(min_length=1, max_length=200)
    competition_id: str = Field(min_length=1, max_length=200)
    competition_name: str = Field(min_length=1, max_length=500)
    discipline: str = Field(min_length=1, max_length=200)
    year: int | None = Field(default=None, ge=1, le=9999)
    event_date: datetime | None = None
    result_level: FspResultLevel
    placement: int | None = Field(default=None, gt=0)
    scope: FspScope | None = None


@dataclass(frozen=True)
class RegistryProfile:
    achievements: tuple[RegistryAchievement, ...]


class FspRegistryProvider(Protocol):
    def lookup(self, fsp_id: str) -> RegistryProfile | None: ...


class RegistryUnavailable(Exception):
    """Provider boundary failure, translated without private payloads."""


class RegistryFixture(BaseModel):
    profiles: dict[str, tuple[RegistryAchievement, ...]]


class MockFspRegistryProvider:
    def __init__(self) -> None:
        path = Path(__file__).parents[1] / "content" / "fsp_registry_mock.json"
        self._profiles = RegistryFixture.model_validate_json(
            path.read_text(encoding="utf-8")
        ).profiles

    def lookup(self, fsp_id: str) -> RegistryProfile | None:
        values = self._profiles.get(fsp_id)
        return RegistryProfile(values) if values is not None else None
