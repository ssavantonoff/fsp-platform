from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
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
        self._snapshot: Mapping[str, CandidateAssessment] | None = None

    @contextmanager
    def matching_snapshot(
        self, values: Mapping[str, CandidateAssessment]
    ) -> Iterator[None]:
        """Bind canonical values to Matching's statement snapshot for this call only."""
        previous = self._snapshot
        self._snapshot = dict(values)
        try:
            yield
        finally:
            self._snapshot = previous

    def get_assessments(
        self, candidate_ids: Sequence[str]
    ) -> Mapping[str, CandidateAssessment]:
        unique_ids = list(dict.fromkeys(candidate_ids))
        if self._snapshot is not None:
            return {
                candidate_id: self._snapshot[candidate_id]
                for candidate_id in unique_ids
                if candidate_id in self._snapshot
            }
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
