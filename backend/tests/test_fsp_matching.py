import json

import pytest

from app.models import (
    CandidateProfile,
    FspResultLevel,
    Invitation,
    User,
)
from app.services import fsp, matching
from app.services.candidate_assessments import CandidateAssessment
from app.services.fsp_registry import MockFspRegistryProvider
from app.services.fsp_rules import UNVERIFIED, FspSignal, score_achievements
from app.services.matching_rules import CandidateMatchInput, NeedCriteria


def verify(db_factory, candidate_id, identifier="MOCK-MULTI"):
    with db_factory() as db:
        profile = db.get(CandidateProfile, candidate_id)
        profile.fsp_id = identifier
        db.commit()
        fsp.sync(db, db.get(User, profile.user_id), MockFspRegistryProvider())


def matches(client, setup):
    response = client.get(f"/employer/needs/{setup['need_id']}/matches")
    assert response.status_code == 200, response.text
    return response.json()["items"]


def test_fsp_bonus_reorders_without_changing_fit_or_assessment(
    client, invitation_setup, matching_candidate, db_factory
):
    setup = invitation_setup
    second = matching_candidate(normalized_assessment_score=79)
    before = {i["candidate_id"]: i for i in matches(client, setup)}
    assert before[setup["candidate_id"]]["fsp_bonus"] == 0
    assert before[second]["fsp_verified"] is False
    verify(db_factory, second)
    after = matches(client, setup)
    assert after[0]["candidate_id"] == second
    for item in after:
        previous = before[item["candidate_id"]]
        assert item["professional_fit_score"] == previous["professional_fit_score"]
        assert item["breakdown"] == previous["breakdown"]
        assert (
            item["normalized_assessment_score"]
            == previous["normalized_assessment_score"]
        )
        assert item["ranking_score"] == pytest.approx(
            0.95 * item["professional_fit_score"] + item["fsp_bonus"]
        )
    assert after[0]["fsp_bonus"] == 5
    assert after[0]["competition_count"] == 3
    assert "MOCK-MULTI" not in json.dumps(after)


@pytest.mark.parametrize(
    "changes",
    [
        {"verified": False},
        {"personal_data_consent": False},
        {"specialization": "FRONTEND"},
        {"verified_grade": "JUNIOR"},
    ],
)
def test_verified_fsp_cannot_override_hard_filters(
    client, invitation_setup, matching_candidate, db_factory, changes
):
    rejected = matching_candidate(**changes)
    verify(db_factory, rejected)
    assert rejected not in [
        i["candidate_id"] for i in matches(client, invitation_setup)
    ]


def test_winner_without_must_have_is_not_invitable(
    client, invitation_setup, matching_candidate, skill_ids, db_factory
):
    candidate_id = matching_candidate(skill_ids=skill_ids[1:])
    verify(db_factory, candidate_id)
    response = client.post(
        f"/employer/needs/{invitation_setup['need_id']}/invitations",
        json={"candidate_id": candidate_id},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "candidate_not_available"


def test_stronger_fit_can_win_and_ties_use_all_unrounded_keys():
    criteria = NeedCriteria(
        "need", "employer", "BACKEND", "MIDDLE", frozenset(), frozenset(), None
    )

    def evaluated(identifier, score, signal=UNVERIFIED):
        return matching.evaluate_candidate(
            criteria,
            CandidateMatchInput(identifier, "BACKEND", True, frozenset(), None),
            CandidateAssessment(identifier, "MIDDLE", score, None),
            fsp=signal,
        )

    winner = score_achievements([("one", FspResultLevel.WINNER)])
    strong, boosted = evaluated("strong", 100), evaluated("boosted", 80, winner)
    assert matching.rank_evaluations([boosted, strong])[0] == strong
    a, b = evaluated("a", 80), evaluated("b", 80)
    assert matching.rank_evaluations([b, a]) == [a, b]
    # Equal final rank: higher raw Professional Fit wins before assessment/id.
    from dataclasses import replace

    higher_fit = replace(a, fit=replace(a.fit, score=80), fsp=FspSignal())
    higher_bonus = replace(
        b,
        fit=replace(b.fit, score=75),
        fsp=FspSignal(True, 95, 3, FspResultLevel.WINNER),
    )
    assert higher_fit.ranking_score == higher_bonus.ranking_score
    assert matching.rank_evaluations([higher_bonus, higher_fit])[0] == higher_fit


def test_invitation_snapshots_keep_fsp_at_send_after_unlink(
    client, app, invitation_setup, db_factory
):
    setup = invitation_setup
    verify(db_factory, setup["candidate_id"])
    match = matches(client, setup)[0]
    created = client.post(
        f"/employer/needs/{setup['need_id']}/invitations",
        json={"candidate_id": setup["candidate_id"]},
    ).json()
    snapshot = created["candidate_snapshot"]
    for key in (
        "ranking_score",
        "fsp_verified",
        "fsp_achievement_score",
        "fsp_bonus",
        "competition_count",
        "best_result_level",
    ):
        assert snapshot[key] == match[key]
    with db_factory() as db:
        fsp.unlink(db, db.get(User, setup["candidate_user_id"]))
    assert (
        client.get(f"/employer/invitations/{created['id']}").json()[
            "candidate_snapshot"
        ]
        == snapshot
    )
    assert matches(client, setup)[0]["fsp_bonus"] == 0


def test_legacy_snapshot_read_does_not_fabricate_v2(
    client, invitation_setup, db_factory
):
    # Insert a historical V1 snapshot, rather than attempting to edit immutable history.
    setup = invitation_setup
    created = client.post(
        f"/employer/needs/{setup['need_id']}/invitations",
        json={"candidate_id": setup["candidate_id"]},
    ).json()
    assert (
        client.post(f"/employer/invitations/{created['id']}/withdraw").status_code
        == 200
    )
    old = {
        k: v
        for k, v in created["candidate_snapshot"].items()
        if not k.startswith("fsp_")
        and k not in {"ranking_score", "competition_count", "best_result_level"}
    }
    with db_factory() as db:
        source = db.get(Invitation, created["id"])
        legacy = Invitation(
            need_id=source.need_id,
            employer_id=source.employer_id,
            candidate_id=source.candidate_id,
            need_snapshot=source.need_snapshot,
            candidate_snapshot=old,
            sent_at=source.sent_at,
        )
        db.add(legacy)
        db.commit()
        identifier = legacy.id
    result = client.get(f"/employer/invitations/{identifier}").json()[
        "candidate_snapshot"
    ]
    assert result == old


def test_v2_uses_sub_display_precision_and_assessment_tertiary_key():
    from dataclasses import replace

    criteria = NeedCriteria(
        "need", "employer", "BACKEND", "MIDDLE", frozenset(), frozenset(), None
    )

    def evaluated(identifier, assessment, fit):
        item = matching.evaluate_candidate(
            criteria,
            CandidateMatchInput(identifier, "BACKEND", True, frozenset(), None),
            CandidateAssessment(identifier, "MIDDLE", assessment, None),
        )
        return replace(item, fit=replace(item.fit, score=fit))

    lower = evaluated("a", 80, 80.001)
    higher = evaluated("z", 80, 80.002)
    assert round(lower.ranking_score, 1) == round(higher.ranking_score, 1)
    assert matching.rank_evaluations([lower, higher]) == [higher, lower]
    lower_assessment = evaluated("a", 80, 80)
    higher_assessment = evaluated("z", 81, 80)
    assert lower_assessment.ranking_score == higher_assessment.ranking_score
    assert matching.rank_evaluations([lower_assessment, higher_assessment]) == [
        higher_assessment,
        lower_assessment,
    ]
