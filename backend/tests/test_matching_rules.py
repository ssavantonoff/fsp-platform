from dataclasses import replace
from datetime import UTC, datetime

import pytest

from app.models import Grade, Specialization
from app.services.candidate_assessments import CandidateAssessment
from app.services.matching_rules import (
    CandidateMatchInput,
    EligibleCandidate,
    NeedCriteria,
    eligible_candidate,
    grade_fit,
)


@pytest.mark.parametrize(
    "required,verified,expected",
    [
        (Grade.JUNIOR, Grade.JUNIOR, 1.0),
        (Grade.JUNIOR, Grade.MIDDLE, 0.75),
        (Grade.JUNIOR, Grade.SENIOR, None),
        (Grade.MIDDLE, Grade.JUNIOR, None),
        (Grade.MIDDLE, Grade.MIDDLE, 1.0),
        (Grade.MIDDLE, Grade.SENIOR, 0.75),
        (Grade.SENIOR, Grade.JUNIOR, None),
        (Grade.SENIOR, Grade.MIDDLE, None),
        (Grade.SENIOR, Grade.SENIOR, 1.0),
    ],
)
def test_grade_compatibility(required, verified, expected):
    assert grade_fit(required, verified) == expected
    if expected is None:
        assert grade_fit(required, verified) is None


@pytest.fixture
def need():
    return NeedCriteria(
        need_id="need-1",
        employer_id="employer-1",
        specialization=Specialization.BACKEND,
        required_grade=Grade.MIDDLE,
        must_have_skill_ids=frozenset({"python", "postgresql"}),
        nice_to_have_skill_ids=frozenset({"django"}),
        target_experience_years=4.0,
    )


@pytest.fixture
def candidate():
    return CandidateMatchInput(
        candidate_id="candidate-1",
        specialization=Specialization.BACKEND,
        personal_data_consent=True,
        skill_ids=frozenset({"python", "postgresql", "django"}),
        years_of_experience=2.0,
    )


@pytest.fixture
def assessment():
    return CandidateAssessment(
        candidate_id="candidate-1",
        verified_grade=Grade.MIDDLE,
        normalized_assessment_score=80,
        assessment_verified_at=datetime(2026, 9, 18, tzinfo=UTC),
    )


@pytest.mark.parametrize(
    "candidate_changes,assessment_changes,missing_assessment",
    [
        pytest.param(
            {"specialization": Specialization.FRONTEND}, {}, False, id="frontend"
        ),
        pytest.param(
            {"specialization": Specialization.DATA_ML}, {}, False, id="data-ml"
        ),
        pytest.param({"personal_data_consent": False}, {}, False, id="consent-false"),
        pytest.param({"personal_data_consent": None}, {}, False, id="consent-null"),
        pytest.param({"personal_data_consent": 1}, {}, False, id="consent-integer"),
        pytest.param({"personal_data_consent": "true"}, {}, False, id="consent-string"),
        pytest.param({}, {"verified_grade": None}, False, id="grade-null"),
        pytest.param(
            {}, {"verified_grade": Grade.JUNIOR}, False, id="grade-incompatible"
        ),
        pytest.param(
            {"skill_ids": frozenset({"python", "django"})},
            {},
            False,
            id="missing-must-have",
        ),
        pytest.param({}, {}, True, id="missing-provider-record"),
        pytest.param({}, {"candidate_id": "candidate-2"}, False, id="wrong-record-id"),
        pytest.param({}, {"normalized_assessment_score": None}, False, id="score-null"),
        pytest.param(
            {}, {"normalized_assessment_score": -1}, False, id="score-negative"
        ),
        pytest.param(
            {}, {"normalized_assessment_score": 101}, False, id="score-above-100"
        ),
        pytest.param(
            {}, {"normalized_assessment_score": float("nan")}, False, id="score-nan"
        ),
        pytest.param(
            {}, {"normalized_assessment_score": float("inf")}, False, id="score-inf"
        ),
        pytest.param(
            {},
            {"normalized_assessment_score": float("-inf")},
            False,
            id="score-minus-inf",
        ),
        pytest.param({}, {"normalized_assessment_score": True}, False, id="score-true"),
        pytest.param(
            {}, {"normalized_assessment_score": False}, False, id="score-false"
        ),
        pytest.param(
            {}, {"normalized_assessment_score": 80.5}, False, id="score-fraction"
        ),
        pytest.param(
            {}, {"normalized_assessment_score": 80.0}, False, id="score-float"
        ),
        pytest.param(
            {}, {"normalized_assessment_score": "80"}, False, id="score-string"
        ),
    ],
)
def test_eligibility_hard_filters(
    need,
    candidate,
    assessment,
    candidate_changes,
    assessment_changes,
    missing_assessment,
):
    candidate = replace(candidate, **candidate_changes)
    assessment = (
        None if missing_assessment else replace(assessment, **assessment_changes)
    )

    assert eligible_candidate(need, candidate, assessment) is None


def test_eligible_zero_score(need, candidate, assessment):
    assessment = replace(assessment, normalized_assessment_score=0)

    result = eligible_candidate(need, candidate, assessment)

    assert result == EligibleCandidate(
        candidate=candidate,
        verified_grade=Grade.MIDDLE,
        normalized_assessment_score=0,
        assessment_verified_at=datetime(2026, 9, 18, tzinfo=UTC),
        grade_fit=1.0,
    )


def test_consent_false_excludes_verified_perfect_candidate(need, candidate, assessment):
    candidate = replace(
        candidate, personal_data_consent=False, years_of_experience=20.0
    )
    assessment = replace(assessment, normalized_assessment_score=100)

    assert eligible_candidate(need, candidate, assessment) is None


@pytest.mark.parametrize(
    "required,verified,expected_fit",
    [
        (Grade.JUNIOR, Grade.JUNIOR, 1.0),
        (Grade.JUNIOR, Grade.MIDDLE, 0.75),
        (Grade.MIDDLE, Grade.MIDDLE, 1.0),
        (Grade.MIDDLE, Grade.SENIOR, 0.75),
        (Grade.SENIOR, Grade.SENIOR, 1.0),
    ],
)
def test_eligibility_returns_validated_candidate(
    need, candidate, assessment, required, verified, expected_fit
):
    need = replace(need, required_grade=required)
    assessment = replace(assessment, verified_grade=verified)

    result = eligible_candidate(need, candidate, assessment)

    assert result == EligibleCandidate(
        candidate=candidate,
        verified_grade=verified,
        normalized_assessment_score=80,
        assessment_verified_at=datetime(2026, 9, 18, tzinfo=UTC),
        grade_fit=expected_fit,
    )


def test_eligibility_accepts_score_100(need, candidate, assessment):
    assessment = replace(assessment, normalized_assessment_score=100)

    result = eligible_candidate(need, candidate, assessment)

    assert result is not None
    assert result.normalized_assessment_score == 100


@pytest.mark.parametrize(
    "verified_at",
    [None, datetime(2000, 1, 1, tzinfo=UTC), datetime(2099, 1, 1, tzinfo=UTC)],
    ids=["no-date", "old-date", "future-date"],
)
def test_eligibility_assessment_date_is_informational(
    need, candidate, assessment, verified_at
):
    assessment = replace(assessment, assessment_verified_at=verified_at)

    result = eligible_candidate(need, candidate, assessment)

    assert result == EligibleCandidate(
        candidate=candidate,
        verified_grade=Grade.MIDDLE,
        normalized_assessment_score=80,
        assessment_verified_at=verified_at,
        grade_fit=1.0,
    )


def test_eligibility_does_not_require_optional_skills_or_experience(
    need, candidate, assessment
):
    candidate = replace(
        candidate,
        skill_ids=frozenset({"python", "postgresql"}),
        years_of_experience=None,
    )

    result = eligible_candidate(need, candidate, assessment)

    assert result is not None
    assert result.candidate == candidate
