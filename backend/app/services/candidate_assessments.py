from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CandidateProfile, Grade


@dataclass(frozen=True)
class CandidateAssessment:
    candidate_id: str
    verified_grade: Grade | None
    normalized_assessment_score: int | None
    assessment_verified_at: datetime | None


class CandidateAssessmentProvider(Protocol):
    def get_assessments(
        self, candidate_ids: Sequence[str]
    ) -> Mapping[str, CandidateAssessment]: ...


class ProfileAssessmentProvider:
    def __init__(self, db: Session):
        self.db = db

    def get_assessments(
        self, candidate_ids: Sequence[str]
    ) -> Mapping[str, CandidateAssessment]:
        unique_ids = list(dict.fromkeys(candidate_ids))
        assessments = {}
        with self.db.no_autoflush:
            for start in range(0, len(unique_ids), 500):
                rows = self.db.execute(
                    select(
                        CandidateProfile.id,
                        CandidateProfile.verified_grade,
                        CandidateProfile.normalized_assessment_score,
                        CandidateProfile.assessment_verified_at,
                    ).where(CandidateProfile.id.in_(unique_ids[start : start + 500]))
                )
                for candidate_id, grade, score, verified_at in rows:
                    assessments[candidate_id] = CandidateAssessment(
                        candidate_id, grade, score, verified_at
                    )
        return assessments
