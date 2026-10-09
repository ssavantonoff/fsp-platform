"""P6-A read-only input validation. No DB, Matching, FSP scoring or ranking."""

import argparse
import ast
import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models import Grade, Specialization
from app.services.candidate_assessments import CandidateAssessment
from app.services.fsp_registry import MockFspRegistryProvider, RegistryAchievement

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = ROOT / "docs/validation/matching-v2-dataset-v1.json"


def catalog() -> list[str]:
    """Read the literal production seed catalog without importing seed/DB setup."""
    tree = ast.parse((ROOT / "backend/app/seed.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "SKILLS"
            for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if isinstance(value, list) and all(isinstance(s, str) for s in value):
                return value
    raise ValueError("Production catalog is no longer a literal string list")


def utc_instant(value: datetime) -> datetime:
    if value.utcoffset() != timedelta(0):
        raise ValueError("Timestamp must be timezone-aware UTC")
    return value


UTCInstant = Annotated[datetime, AfterValidator(utc_instant)]
Years = Annotated[float, Field(ge=0, le=80, allow_inf_nan=False)]
Skills = Annotated[list[str], Field(max_length=100)]
Salary = Annotated[str, Field(pattern=r"^(0|[1-9][0-9]{0,9})\.[0-9]{2}$")]


def valid_skills(values: list[str]) -> list[str]:
    if len(values) != len(set(values)) or not set(values) <= set(catalog()):
        raise ValueError("Skills must be unique names from the production catalog")
    return values


class StrictRecord(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class Evidence(RegistryAchievement):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class FspRecord(StrictRecord):
    state: Literal["NONE", "ENTERED_UNVERIFIED", "VERIFIED"]
    fsp_id: Annotated[str, Field(pattern=r"^MOCK-[A-Z]+$", max_length=200)] | None
    verified_at: UTCInstant | None
    synced_at: UTCInstant | None
    achievements: list[Evidence]

    @model_validator(mode="after")
    def coherent_evidence(self) -> Self:
        if self.state == "NONE":
            if self.fsp_id is not None:
                raise ValueError("NONE cannot contain an entered FSP ID")
        elif self.fsp_id is None:
            raise ValueError("Entered/verified state requires a mock FSP ID")
        if self.state != "VERIFIED":
            if self.verified_at or self.synced_at or self.achievements:
                raise ValueError("Unverified states cannot contain verified evidence")
        else:
            if not self.verified_at or not self.synced_at:
                raise ValueError("Verified evidence requires both timestamps")
            if self.synced_at < self.verified_at:
                raise ValueError("Sync cannot precede verification")
            record = MockFspRegistryProvider().lookup(self.fsp_id or "")
            if record is None or [
                a.model_dump(mode="json") for a in self.achievements
            ] != [a.model_dump(mode="json") for a in record.achievements]:
                raise ValueError(
                    "Evidence must exactly match the trusted mock provider"
                )
        return self


class NeedRecord(StrictRecord):
    id: Annotated[str, Field(pattern=r"^N[1-8]$")]
    position_title: Annotated[str, Field(min_length=1, max_length=200)]
    specialization: Specialization
    required_grade: Grade
    status: Literal["ACTIVE"]
    must_have_skills: Annotated[Skills, Field(min_length=1)]
    nice_to_have_skills: Skills
    target_experience_years: Years | None
    salary_from: Salary
    salary_to: Salary
    salary_currency: Literal["RUB"]
    salary_basis: Literal["GROSS"]
    description: Annotated[str, Field(min_length=1)]
    rationale: Annotated[str, Field(min_length=1)]
    catalog_limited: bool
    limitation: Annotated[str, Field(min_length=1)] | None

    _skills = field_validator("must_have_skills", "nice_to_have_skills")(valid_skills)

    @model_validator(mode="after")
    def coherent_need(self) -> Self:
        if set(self.must_have_skills) & set(self.nice_to_have_skills):
            raise ValueError("Must-have and nice-to-have must be disjoint")
        if Decimal(self.salary_from) > Decimal(self.salary_to):
            raise ValueError("Salary interval must be ordered")
        if self.catalog_limited != (self.limitation is not None):
            raise ValueError("Catalog limitation must be explicitly documented")
        return self


class CandidateRecord(StrictRecord):
    id: Annotated[str, Field(pattern=r"^C(0[1-9]|[12][0-9]|3[0-6])$")]
    specialization: Specialization
    declared_grade: Grade
    verified_grade: Grade | None
    normalized_assessment_score: Annotated[int, Field(ge=0, le=100)] | None
    assessment_verified_at: UTCInstant | None
    self_declared_skills: Skills
    years_of_experience: Years | None
    personal_data_consent: bool
    personal_data_consent_at: UTCInstant | None
    fsp: FspRecord
    design_note: Annotated[str, Field(min_length=1)]

    _skills = field_validator("self_declared_skills")(valid_skills)

    @model_validator(mode="after")
    def coherent_candidate(self) -> Self:
        trio = (
            self.verified_grade,
            self.normalized_assessment_score,
            self.assessment_verified_at,
        )
        if sum(value is not None for value in trio) not in (0, 3):
            raise ValueError("Canonical Assessment trio must be all-null or complete")
        if self.personal_data_consent != (self.personal_data_consent_at is not None):
            raise ValueError("Consent timestamp must agree with consent")
        return self


def exclusion_reasons(need: NeedRecord, candidate: CandidateRecord) -> list[str]:
    """Independent product requirements, not a call to production eligibility."""
    allowed = {
        Grade.JUNIOR: {Grade.JUNIOR, Grade.MIDDLE},
        Grade.MIDDLE: {Grade.MIDDLE, Grade.SENIOR},
        Grade.SENIOR: {Grade.SENIOR},
    }
    reasons = []
    if not candidate.personal_data_consent:
        reasons.append("consent")
    if candidate.specialization != need.specialization:
        reasons.append("specialization")
    if candidate.verified_grade is None:
        reasons.append("unverified_assessment")
    elif candidate.verified_grade not in allowed[need.required_grade]:
        reasons.append("grade")
    if not set(need.must_have_skills) <= set(candidate.self_declared_skills):
        reasons.append("must_have")
    return reasons


class Dataset(StrictRecord):
    name: Literal["matching-v2-validation-v1"]
    version: Annotated[int, Field(strict=True, ge=1, le=1)]
    status: Literal["P6A_REVIEW_CHECKPOINT"]
    synthetic: Literal[True]
    source_base: Literal["f5d460f9888b8bfe94a90e495254974a0d2043e7"]
    skill_catalog: list[str]
    fsp_provider: Literal["MockFspRegistryProvider"]
    needs: Annotated[list[NeedRecord], Field(min_length=8, max_length=8)]
    candidates: Annotated[list[CandidateRecord], Field(min_length=36, max_length=36)]

    @field_validator("synthetic", mode="before")
    @classmethod
    def explicitly_synthetic(cls, value: object) -> bool:
        if value is not True:
            raise ValueError("Synthetic flag must be the boolean true")
        return True

    @model_validator(mode="after")
    def valid_coverage(self) -> Self:
        if self.skill_catalog != catalog():
            raise ValueError("Catalog snapshot must exactly match production")
        if [n.id for n in self.needs] != [f"N{i}" for i in range(1, 9)]:
            raise ValueError("Need IDs must be unique and ordered N1..N8")
        if [c.id for c in self.candidates] != [f"C{i:02}" for i in range(1, 37)]:
            raise ValueError("Candidate IDs must be unique and ordered C01..C36")
        required_needs = [
            ("Python API / Junior", Specialization.BACKEND, Grade.JUNIOR),
            ("Python Django / Middle", Specialization.BACKEND, Grade.MIDDLE),
            ("Java / Senior", Specialization.BACKEND, Grade.SENIOR),
            ("React / Junior", Specialization.FRONTEND, Grade.JUNIOR),
            ("Next.js / Middle", Specialization.FRONTEND, Grade.MIDDLE),
            ("Frontend / Senior", Specialization.FRONTEND, Grade.SENIOR),
            ("ML Engineer / Middle", Specialization.DATA_ML, Grade.MIDDLE),
            ("ML Platform / Senior", Specialization.DATA_ML, Grade.SENIOR),
        ]
        if [
            (n.position_title, n.specialization, n.required_grade) for n in self.needs
        ] != required_needs:
            raise ValueError(
                "The eight approved Need names/directions/grades must remain"
            )
        if {n.id for n in self.needs if n.catalog_limited} != {"N3", "N5", "N7", "N8"}:
            raise ValueError("Four catalog-limited Needs must remain explicit")
        verified = [c.fsp for c in self.candidates if c.fsp.state == "VERIFIED"]
        if len({f.fsp_id for f in verified}) != len(verified):
            raise ValueError("Verified FSP identities must be globally unique")
        by_id = {c.id: c for c in self.candidates}
        ordinal = {Grade.JUNIOR: 0, Grade.MIDDLE: 1, Grade.SENIOR: 2}
        for key in ("C03", "C18", "C21"):
            c = by_id[key]
            if (
                c.verified_grade is None
                or ordinal[c.declared_grade] <= ordinal[c.verified_grade]
            ):
                raise ValueError(
                    "Required declared-above-verified scenarios are missing"
                )
        for cid, nid in (("C15", "N4"), ("C27", "N7")):
            c = by_id[cid]
            n = next(n for n in self.needs if n.id == nid)
            if (
                c.normalized_assessment_score or 0
            ) < 95 or "must_have" not in exclusion_reasons(n, c):
                raise ValueError("Required high-score missing-must cases are missing")
        if by_id["C36"].verified_grade is not None:
            raise ValueError("C36 must have no canonical verification")
        if {c.fsp.state for c in self.candidates} != {
            "NONE",
            "ENTERED_UNVERIFIED",
            "VERIFIED",
        }:
            raise ValueError("All FSP states must be covered")
        levels = {a.result_level.value for f in verified for a in f.achievements}
        if levels != {"PARTICIPANT", "FINALIST", "PRIZE_WINNER", "WINNER"}:
            raise ValueError("All four FSP result levels must be covered")
        if not any(a.scope == "TEAM" for f in verified for a in f.achievements):
            raise ValueError("Team evidence must be covered")
        if not any(
            len({a.competition_id for a in f.achievements}) >= 3 for f in verified
        ):
            raise ValueError("Multiple competitions must be covered")
        if not any(not f.achievements for f in verified):
            raise ValueError("Verified-empty evidence must be covered")
        for spec in Specialization:
            if sum(c.specialization == spec for c in self.candidates) != 12:
                raise ValueError("Dataset must contain twelve candidates per direction")
        for need in self.needs:
            count = sum(not exclusion_reasons(need, c) for c in self.candidates)
            if not 2 <= count < 12:
                raise ValueError("Each Need requires a nontrivial mixed eligible pool")
        return self


class OfflineAssessmentProvider:
    """Read-only CandidateAssessmentProvider-compatible synthetic evidence."""

    def __init__(self, dataset: Dataset):
        self._assessments = {
            c.id: CandidateAssessment(
                c.id,
                c.verified_grade,
                c.normalized_assessment_score,
                c.assessment_verified_at,
            )
            for c in dataset.candidates
        }

    def get_assessments(
        self, candidate_ids: Sequence[str]
    ) -> Mapping[str, CandidateAssessment]:
        return {
            key: self._assessments[key]
            for key in candidate_ids
            if key in self._assessments
        }


def load_dataset(path: Path = DEFAULT_DATASET) -> Dataset:
    return Dataset.model_validate_json(path.read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--schema", action="store_true", help="Print the JSON Schema")
    args = parser.parse_args()
    if args.schema:
        print(json.dumps(Dataset.model_json_schema(), ensure_ascii=False, indent=2))
        return
    dataset = load_dataset(args.dataset)
    print("8 Needs; 36 Candidates; 288 structural pairs")
    for need in dataset.needs:
        eligible = [c.id for c in dataset.candidates if not exclusion_reasons(need, c)]
        print(
            f"{need.id}: {len(eligible)} eligible (ID order only): "
            f"{', '.join(eligible)}"
        )
    print(f"SHA256: {hashlib.sha256(args.dataset.read_bytes()).hexdigest()}")
    print("Ranking/evaluation not executed")


if __name__ == "__main__":
    main()
