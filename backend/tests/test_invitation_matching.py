from datetime import UTC, datetime

from app.models import Grade, Specialization
from app.services import matching
from app.services.candidate_assessments import CandidateAssessment
from app.services.matching_rules import CandidateMatchInput, NeedCriteria


def test_single_candidate_evaluation_uses_frozen_rules():
    need = NeedCriteria(
        "need",
        "employer",
        Specialization.BACKEND,
        Grade.MIDDLE,
        frozenset({"python"}),
        frozenset(),
        None,
    )
    candidate = CandidateMatchInput(
        "candidate", Specialization.BACKEND, True, frozenset({"python"}), 2
    )
    assessment = CandidateAssessment(
        "candidate", Grade.MIDDLE, 80, datetime(2026, 10, 7, tzinfo=UTC)
    )
    assert hasattr(matching, "evaluate_candidate")
    result = matching.evaluate_candidate(need, candidate, assessment)
    # Only assessment and grade factors are active: (45 * .8 + 25) / 70 * 100.
    assert round(result.fit.score, 8) == round(61 / 70 * 100, 8)
    assert matching.evaluate_candidate(need, candidate, None) is None
    missing_skill = CandidateMatchInput(
        "candidate", Specialization.BACKEND, True, frozenset(), 2
    )
    assert matching.evaluate_candidate(need, missing_skill, assessment) is None
