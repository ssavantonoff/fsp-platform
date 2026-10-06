from dataclasses import replace
from datetime import UTC, datetime
from itertools import permutations, product
from math import isfinite
from sys import float_info

import pytest

from app.models import Grade, Specialization
from app.services.candidate_assessments import CandidateAssessment
from app.services.matching_rules import (
    CandidateMatchInput,
    EligibleCandidate,
    NeedCriteria,
    RankedCandidate,
    ScoringInput,
    eligible_candidate,
    grade_fit,
    rank_candidates,
    score_professional_fit,
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


def assert_contributions(fit, expected):
    actual = [
        (factor.score, factor.max, factor.active)
        for factor in (
            fit.assessment,
            fit.grade,
            fit.nice_to_have,
            fit.experience,
        )
    ]
    for (score, maximum, active), (want_score, want_maximum, want_active) in zip(
        actual, expected, strict=True
    ):
        assert score == pytest.approx(want_score)
        assert maximum == pytest.approx(want_maximum)
        assert active is want_active


def test_score_contributions():
    fit = score_professional_fit(ScoringInput(80, 1.0, 1, 2, 2.0, 4.0))

    assert fit.score == 76.0
    assert fit.assessment.score == 36.0
    assert fit.grade.score == 25.0
    assert fit.nice_to_have.score == 7.5
    assert fit.experience.score == 7.5
    assert_contributions(
        fit,
        [(36.0, 45.0, True), (25.0, 25.0, True), (7.5, 15.0, True), (7.5, 15.0, True)],
    )


def test_overqualified_contribution():
    fit = score_professional_fit(ScoringInput(80, 0.75, 1, 2, 2.0, 4.0))

    assert fit.score == 69.75
    assert_contributions(
        fit,
        [(36.0, 45.0, True), (18.75, 25.0, True), (7.5, 15.0, True), (7.5, 15.0, True)],
    )


def test_experience_cap():
    fit = score_professional_fit(ScoringInput(80, 1.0, 1, 2, 8.0, 4.0))

    assert fit.score == 83.5
    assert_contributions(
        fit,
        [(36.0, 45.0, True), (25.0, 25.0, True), (7.5, 15.0, True), (15.0, 15.0, True)],
    )


def test_missing_candidate_experience():
    fit = score_professional_fit(ScoringInput(80, 1.0, 1, 2, None, 4.0))

    assert fit.score == 68.5
    assert_contributions(
        fit,
        [(36.0, 45.0, True), (25.0, 25.0, True), (7.5, 15.0, True), (0.0, 15.0, True)],
    )


@pytest.mark.parametrize("years", [None, 0.0, 8.0])
def test_zero_experience_target(years):
    fit = score_professional_fit(ScoringInput(80, 1.0, 1, 2, years, 0.0))

    assert fit.score == 83.5
    assert_contributions(
        fit,
        [(36.0, 45.0, True), (25.0, 25.0, True), (7.5, 15.0, True), (15.0, 15.0, True)],
    )


def test_no_nice_factor_renormalization():
    fit = score_professional_fit(ScoringInput(80, 1.0, 0, 0, 2.0, 4.0))

    assert fit.score == pytest.approx(80.58823529411765)
    assert_contributions(
        fit,
        [
            (42.35294117647059, 52.94117647058823, True),
            (29.41176470588235, 29.41176470588235, True),
            (0.0, 0.0, False),
            (8.823529411764707, 17.647058823529413, True),
        ],
    )


def test_no_experience_factor_renormalization():
    fit = score_professional_fit(ScoringInput(80, 1.0, 1, 2, 2.0, None))

    assert fit.score == pytest.approx(80.58823529411765)
    assert_contributions(
        fit,
        [
            (42.35294117647059, 52.94117647058823, True),
            (29.41176470588235, 29.41176470588235, True),
            (8.823529411764707, 17.647058823529413, True),
            (0.0, 0.0, False),
        ],
    )


def test_both_optional_factors_absent():
    fit = score_professional_fit(ScoringInput(80, 1.0, 0, 0, None, None))

    assert fit.score == pytest.approx(87.14285714285714)
    assert_contributions(
        fit,
        [
            (51.42857142857143, 64.28571428571429, True),
            (35.714285714285715, 35.714285714285715, True),
            (0.0, 0.0, False),
            (0.0, 0.0, False),
        ],
    )


def test_scoring_bounds_and_component_endpoints():
    maximum = score_professional_fit(ScoringInput(100, 1.0, 2, 2, 4.0, 4.0))
    zero_assessment = score_professional_fit(ScoringInput(0, 1.0, 0, 2, None, 4.0))

    assert maximum.score == 100.0
    assert_contributions(
        maximum,
        [
            (45.0, 45.0, True),
            (25.0, 25.0, True),
            (15.0, 15.0, True),
            (15.0, 15.0, True),
        ],
    )
    assert zero_assessment.score == 25.0
    assert_contributions(
        zero_assessment,
        [(0.0, 45.0, True), (25.0, 25.0, True), (0.0, 15.0, True), (0.0, 15.0, True)],
    )
    for assessment, grade, skills, years, target in product(
        [0, 80, 100],
        [0.75, 1.0],
        [(0, 0), (0, 2), (1, 2), (2, 2)],
        [None, 0.0, 2.0, 8.0],
        [None, 0.0, 4.0],
    ):
        fit = score_professional_fit(
            ScoringInput(assessment, grade, *skills, years, target)
        )
        assert isfinite(fit.score)
        assert 0.0 <= fit.score <= 100.0
        for factor in (fit.assessment, fit.grade, fit.nice_to_have, fit.experience):
            assert 0.0 <= factor.score <= factor.max <= 100.0


@pytest.mark.parametrize(
    "field,value",
    [
        ("normalized_assessment_score", -1),
        ("normalized_assessment_score", 101),
        ("normalized_assessment_score", 80.0),
        ("normalized_assessment_score", 80.5),
        ("normalized_assessment_score", float("nan")),
        ("normalized_assessment_score", float("inf")),
        ("normalized_assessment_score", float("-inf")),
        ("normalized_assessment_score", True),
        ("normalized_assessment_score", False),
        ("normalized_assessment_score", "80"),
        ("normalized_assessment_score", None),
        ("grade_fit", 0.0),
        ("grade_fit", 0.5),
        ("grade_fit", 1.01),
        ("grade_fit", 0.75000001),
        ("grade_fit", float("nan")),
        ("grade_fit", float("inf")),
        ("grade_fit", True),
        ("grade_fit", "1"),
        ("grade_fit", None),
        ("matched_nice_to_have", -1),
        ("matched_nice_to_have", 3),
        ("matched_nice_to_have", 1.0),
        ("matched_nice_to_have", True),
        ("matched_nice_to_have", None),
        ("matched_nice_to_have", "1"),
        ("total_nice_to_have", -1),
        ("total_nice_to_have", 0),
        ("total_nice_to_have", 2.0),
        ("total_nice_to_have", True),
        ("total_nice_to_have", None),
        ("total_nice_to_have", "2"),
        ("years_of_experience", -0.01),
        ("years_of_experience", float("nan")),
        ("years_of_experience", float("inf")),
        ("years_of_experience", float("-inf")),
        ("years_of_experience", True),
        ("years_of_experience", "2"),
        ("years_of_experience", 10**1000),
        ("target_experience_years", -0.01),
        ("target_experience_years", float("nan")),
        ("target_experience_years", float("inf")),
        ("target_experience_years", float("-inf")),
        ("target_experience_years", True),
        ("target_experience_years", "4"),
        ("target_experience_years", 10**1000),
    ],
)
def test_scoring_bounds_reject_invalid_inputs(field, value):
    data = replace(ScoringInput(80, 1.0, 1, 2, 2.0, 4.0), **{field: value})

    with pytest.raises(ValueError):
        score_professional_fit(data)


@pytest.mark.parametrize("target", [None, 0.0])
def test_scoring_bounds_reject_invalid_experience_when_optional(target):
    with pytest.raises(ValueError):
        score_professional_fit(ScoringInput(80, 1.0, 0, 0, float("nan"), target))


@pytest.mark.parametrize(
    "years,target,want_experience,want_total",
    [
        (float_info.max, float_info.max, 15.0, 83.5),
        (float_info.max, 5e-324, 15.0, 83.5),
        (5e-324, 5e-324, 15.0, 83.5),
        (5e-324, float_info.max, 0.0, 68.5),
        (0.0, 5e-324, 0.0, 68.5),
    ],
)
def test_scoring_bounds_extreme_finite_experience(
    years, target, want_experience, want_total
):
    fit = score_professional_fit(ScoringInput(80, 1.0, 1, 2, years, target))

    assert fit.experience.score == want_experience
    assert fit.score == want_total
    assert isfinite(fit.score)


def ranked_candidate(need, candidate, assessment, candidate_id, data):
    nice_ids = ("django", "fastapi")[: data.total_nice_to_have]
    need = replace(
        need,
        nice_to_have_skill_ids=frozenset(nice_ids),
        target_experience_years=data.target_experience_years,
    )
    candidate = replace(
        candidate,
        candidate_id=candidate_id,
        skill_ids=need.must_have_skill_ids
        | frozenset(nice_ids[: data.matched_nice_to_have]),
        years_of_experience=data.years_of_experience,
    )
    assessment = replace(
        assessment,
        candidate_id=candidate_id,
        normalized_assessment_score=data.normalized_assessment_score,
        verified_grade=Grade.MIDDLE if data.grade_fit == 1.0 else Grade.SENIOR,
    )
    eligible = eligible_candidate(need, candidate, assessment)
    assert eligible is not None
    return RankedCandidate(eligible, score_professional_fit(data))


def test_unrounded_score_wins(need, candidate, assessment):
    lower = ranked_candidate(
        need, candidate, assessment, "a", ScoringInput(80, 1.0, 1, 2, 2.0000001, 4.0)
    )
    higher = ranked_candidate(
        need, candidate, assessment, "z", ScoringInput(80, 1.0, 1, 2, 2.0000002, 4.0)
    )

    assert lower.fit.score == pytest.approx(76.000000375, rel=0, abs=1e-12)
    assert higher.fit.score == pytest.approx(76.00000075, rel=0, abs=1e-12)
    assert higher.fit.score > lower.fit.score
    assert f"{higher.fit.score:.1f}" == f"{lower.fit.score:.1f}" == "76.0"
    for inputs in permutations([lower, higher]):
        assert [
            item.eligible.candidate.candidate_id for item in rank_candidates(inputs)
        ] == [
            "z",
            "a",
        ]


def test_deterministic_ties(need, candidate, assessment):
    higher_assessment_experience = ranked_candidate(
        need, candidate, assessment, "z", ScoringInput(90, 1.0, 0, 2, 5.0, 10.0)
    )
    higher_assessment_skills = ranked_candidate(
        need, candidate, assessment, "b", ScoringInput(90, 1.0, 1, 2, 0.0, 10.0)
    )
    lower_assessment = ranked_candidate(
        need, candidate, assessment, "a", ScoringInput(80, 1.0, 0, 2, 8.0, 10.0)
    )
    candidates = [
        lower_assessment,
        higher_assessment_experience,
        higher_assessment_skills,
    ]

    assert [item.fit.score for item in candidates] == [73.0, 73.0, 73.0]
    assert higher_assessment_experience.fit.experience.score == 7.5
    assert higher_assessment_experience.fit.nice_to_have.score == 0.0
    assert higher_assessment_skills.fit.experience.score == 0.0
    assert higher_assessment_skills.fit.nice_to_have.score == 7.5
    assert lower_assessment.fit.experience.score == 12.0
    for inputs in permutations(candidates):
        ranked = rank_candidates(inputs)
        assert [item.eligible.candidate.candidate_id for item in ranked] == [
            "b",
            "z",
            "a",
        ]
    original_order = candidates.copy()
    rank_candidates(candidates)
    assert candidates == original_order


def test_deterministic_ties_ignore_assessment_dates(need, candidate, assessment):
    candidates = [
        ranked_candidate(
            need,
            candidate,
            assessment,
            candidate_id,
            ScoringInput(80, 1.0, 1, 2, 2.0, 4.0),
        )
        for candidate_id in ("z", "b", "a")
    ]
    dates = [None, datetime(2000, 1, 1, tzinfo=UTC), datetime(2099, 1, 1, tzinfo=UTC)]

    for assigned_dates in permutations(dates):
        dated = [
            replace(item, eligible=replace(item.eligible, assessment_verified_at=date))
            for item, date in zip(candidates, assigned_dates, strict=True)
        ]
        assert [
            item.eligible.candidate.candidate_id for item in rank_candidates(dated)
        ] == [
            "a",
            "b",
            "z",
        ]


def test_exact_grade_advantage(need, candidate, assessment):
    exact = ranked_candidate(
        need, candidate, assessment, "middle", ScoringInput(88, 1.0, 2, 2, 4.0, 4.0)
    )
    overqualified = ranked_candidate(
        need, candidate, assessment, "senior", ScoringInput(100, 0.75, 2, 2, 4.0, 4.0)
    )

    assert exact.eligible.verified_grade == Grade.MIDDLE
    assert overqualified.eligible.verified_grade == Grade.SENIOR
    assert exact.fit.score == 94.6
    assert overqualified.fit.score == 93.75
    assert rank_candidates([overqualified, exact]) == [exact, overqualified]


def test_deterministic_ties_empty_and_singleton(need, candidate, assessment):
    only = ranked_candidate(
        need, candidate, assessment, "only", ScoringInput(80, 1.0, 1, 2, 2.0, 4.0)
    )

    assert rank_candidates([]) == []
    assert rank_candidates((only,)) == [only]
