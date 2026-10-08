import pytest

from app.models import FspResultLevel
from app.services.fsp_registry import MockFspRegistryProvider
from app.services.fsp_rules import score_achievements


@pytest.mark.parametrize(
    "levels,expected",
    [
        ([], 0),
        (["PARTICIPANT"], 10),
        (["PARTICIPANT"] * 3, 30),
        (["FINALIST"], 45),
        (["PRIZE_WINNER"], 66),
        (["WINNER"], 80),
        (["WINNER", "PARTICIPANT", "FINALIST"], 100),
        (["WINNER"] * 10, 100),
    ],
)
def test_exact_score_examples_and_bonus_cap(levels, expected):
    result = score_achievements(
        [(str(i), FspResultLevel(level)) for i, level in enumerate(levels)]
    )
    assert result.fsp_achievement_score == pytest.approx(expected)
    assert result.fsp_bonus == pytest.approx(expected / 100 * 5)
    assert 0 <= result.fsp_bonus <= 5
    assert result.competition_count == len(levels)


def test_competition_breadth_counts_distinct_events_not_achievements():
    result = score_achievements(
        [("same", FspResultLevel.PARTICIPANT), ("same", FspResultLevel.WINNER)]
    )
    assert result.competition_count == 1
    assert result.fsp_achievement_score == 80
    assert result.best_result_level == FspResultLevel.WINNER


def test_mock_is_deterministic_and_unknown_id_is_absent():
    provider = MockFspRegistryProvider()
    assert provider.lookup("missing") is None
    assert provider.lookup("MOCK-EMPTY").achievements == ()
    for key in ("PARTICIPANT", "FINALIST", "PRIZE", "WINNER", "MULTI", "TEAM"):
        first = provider.lookup(f"MOCK-{key}")
        assert first == provider.lookup(f"MOCK-{key}")
        assert first.achievements


def test_team_discipline_and_recency_do_not_affect_score():
    provider = MockFspRegistryProvider()
    individual = provider.lookup("MOCK-WINNER").achievements
    team = provider.lookup("MOCK-TEAM").achievements
    assert individual[0].scope != team[0].scope
    assert individual[0].discipline != team[0].discipline
    assert individual[0].year != team[0].year
    scores = [
        score_achievements([(a.competition_id, a.result_level) for a in values])
        for values in (individual, team)
    ]
    assert scores[0].fsp_achievement_score == scores[1].fsp_achievement_score == 80
