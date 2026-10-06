from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from math import fsum, isfinite, ulp
from typing import Final

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


@dataclass(frozen=True)
class ScoringInput:
    normalized_assessment_score: int
    grade_fit: float
    matched_nice_to_have: int
    total_nice_to_have: int
    years_of_experience: float | None
    target_experience_years: float | None


@dataclass(frozen=True)
class FactorContribution:
    score: float
    max: float
    active: bool


@dataclass(frozen=True)
class ProfessionalFit:
    score: float
    assessment: FactorContribution
    grade: FactorContribution
    nice_to_have: FactorContribution
    experience: FactorContribution


@dataclass(frozen=True)
class RankedCandidate:
    eligible: EligibleCandidate
    fit: ProfessionalFit


_BASE_WEIGHTS: Final = (45, 25, 15, 15)


def _validate_scoring_input(data: ScoringInput) -> None:
    if (
        type(data.normalized_assessment_score) is not int
        or not 0 <= data.normalized_assessment_score <= 100
    ):
        raise ValueError("Assessment score must be an integer in 0–100")
    if type(data.grade_fit) not in (int, float) or data.grade_fit not in (1.0, 0.75):
        raise ValueError("Grade fit must be exactly 1.0 or 0.75")
    if (
        type(data.matched_nice_to_have) is not int
        or type(data.total_nice_to_have) is not int
        or not 0 <= data.matched_nice_to_have <= data.total_nice_to_have
    ):
        raise ValueError(
            "Nice-to-have counts must be integers with 0 <= matched <= total"
        )
    for name, years in (
        ("Candidate experience", data.years_of_experience),
        ("Target experience", data.target_experience_years),
    ):
        if years is None:
            continue
        if type(years) not in (int, float):
            raise ValueError(f"{name} must be finite and nonnegative")
        try:
            valid = isfinite(years) and years >= 0
        except OverflowError as exc:
            raise ValueError(f"{name} must be finite and nonnegative") from exc
        if not valid:
            raise ValueError(f"{name} must be finite and nonnegative")


def score_professional_fit(data: ScoringInput) -> ProfessionalFit:
    _validate_scoring_input(data)
    nice_active = data.total_nice_to_have > 0
    experience_active = data.target_experience_years is not None
    active = (True, True, nice_active, experience_active)
    active_weight = sum(
        weight
        for weight, included in zip(_BASE_WEIGHTS, active, strict=True)
        if included
    )
    if data.target_experience_years is None:
        experience_fit = 0.0
    elif data.target_experience_years == 0:
        experience_fit = 1.0
    elif data.years_of_experience is None:
        experience_fit = 0.0
    elif data.years_of_experience >= data.target_experience_years:
        experience_fit = 1.0
    else:
        experience_fit = data.years_of_experience / data.target_experience_years
    factors = (
        data.normalized_assessment_score / 100,
        data.grade_fit,
        data.matched_nice_to_have / data.total_nice_to_have if nice_active else 0.0,
        experience_fit,
    )
    contributions = []
    for weight, factor, included in zip(_BASE_WEIGHTS, factors, active, strict=True):
        maximum = weight * 100 / active_weight if included else 0.0
        contributions.append(FactorContribution(maximum * factor, maximum, included))
    assessment, grade, nice_to_have, experience = contributions
    score = fsum(factor.score for factor in contributions)
    # Correct only boundary drift from floating-point arithmetic, never a bad score.
    epsilon = 4 * ulp(100.0)
    if not -epsilon <= score <= 100.0 + epsilon:
        raise ValueError("Professional fit is outside 0–100")
    if score < 0.0:
        score = 0.0
    elif score > 100.0:
        score = 100.0
    return ProfessionalFit(
        score=score,
        assessment=assessment,
        grade=grade,
        nice_to_have=nice_to_have,
        experience=experience,
    )


def rank_candidates(candidates: Sequence[RankedCandidate]) -> list[RankedCandidate]:
    return sorted(
        candidates,
        key=lambda item: (
            -item.fit.score,
            -item.eligible.normalized_assessment_score,
            item.eligible.candidate.candidate_id,
        ),
    )


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
