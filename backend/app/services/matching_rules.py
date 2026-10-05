from dataclasses import dataclass
from datetime import datetime

from app.models import Grade, Specialization
from app.services.candidate_assessments import CandidateAssessment


@dataclass(frozen=True)
class NeedCriteria:
    need_id: str
    employer_id: str
    specialization: Specialization
    required_grade: Grade
    must_have_skill_ids: frozenset[str]
    nice_to_have_skill_ids: frozenset[str]
    target_experience_years: float | None


@dataclass(frozen=True)
class CandidateMatchInput:
    candidate_id: str
    specialization: Specialization
    personal_data_consent: bool
    skill_ids: frozenset[str]
    years_of_experience: float | None


@dataclass(frozen=True)
class EligibleCandidate:
    candidate: CandidateMatchInput
    verified_grade: Grade
    normalized_assessment_score: int
    assessment_verified_at: datetime | None
    grade_fit: float


def grade_fit(required_grade: Grade, verified_grade: Grade) -> float | None:
    compatibility = {
        (Grade.JUNIOR, Grade.JUNIOR): 1.0,
        (Grade.JUNIOR, Grade.MIDDLE): 0.75,
        (Grade.MIDDLE, Grade.MIDDLE): 1.0,
        (Grade.MIDDLE, Grade.SENIOR): 0.75,
        (Grade.SENIOR, Grade.SENIOR): 1.0,
    }
    return compatibility.get((required_grade, verified_grade))


def eligible_candidate(
    need: NeedCriteria,
    candidate: CandidateMatchInput,
    assessment: CandidateAssessment | None,
) -> EligibleCandidate | None:
    if candidate.personal_data_consent is not True:
        return None
    if candidate.specialization != need.specialization:
        return None
    if assessment is None or assessment.candidate_id != candidate.candidate_id:
        return None
    if assessment.verified_grade is None:
        return None
    fit = grade_fit(need.required_grade, assessment.verified_grade)
    if fit is None:
        return None
    if not need.must_have_skill_ids.issubset(candidate.skill_ids):
        return None
    score = assessment.normalized_assessment_score
    if type(score) is not int or not 0 <= score <= 100:
        return None
    return EligibleCandidate(
        candidate=candidate,
        verified_grade=assessment.verified_grade,
        normalized_assessment_score=score,
        assessment_verified_at=assessment.assessment_verified_at,
        grade_fit=fit,
    )
