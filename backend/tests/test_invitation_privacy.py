import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import MetaData, select

from app.models import (
    AssessmentAttempt,
    CandidateProfile,
    EmployerNeed,
    EmployerProfile,
    Invitation,
)
from app.services import matching
from tests.test_invitations import as_user, send

FACTOR = {"score": None, "max": None, "active": None}
BREAKDOWN = {
    "assessment": FACTOR,
    "grade": FACTOR | {"exact_match": None},
    "nice_to_have": FACTOR | {"matched": None, "total": None},
    "experience": FACTOR,
}
SKILL = {"id": None, "name": None}
NEED = dict.fromkeys(
    [
        "need_id",
        "position_title",
        "specialization",
        "required_grade",
        "target_experience_years",
        "salary_from",
        "salary_to",
        "description",
        "additional_requirements",
        "company_name",
    ]
) | {
    "must_have_skills": [SKILL],
    "nice_to_have_skills": [SKILL],
}
CANDIDATE = dict.fromkeys(
    [
        "ranking_score",
        "fsp_verified",
        "fsp_achievement_score",
        "fsp_bonus",
        "competition_count",
        "best_result_level",
        "candidate_id",
        "display_name",
        "specialization",
        "verified_grade",
        "normalized_assessment_score",
        "assessment_verified_at",
        "professional_fit_score",
    ]
) | {"breakdown": BREAKDOWN}
COMMON = dict.fromkeys(
    [
        "id",
        "need_id",
        "status",
        "message",
        "sent_at",
        "viewed_at",
        "responded_at",
        "withdrawn_at",
    ]
) | {"need_snapshot": NEED}


def exact_shape(value, schema):
    if isinstance(schema, dict):
        assert isinstance(value, dict)
        assert set(value) == set(schema)
        for key, child in schema.items():
            exact_shape(value[key], child)
    elif isinstance(schema, list):
        assert isinstance(value, list)
        for child in value:
            exact_shape(child, schema[0])


@pytest.mark.parametrize(
    "status", ["SENT", "VIEWED", "ACCEPTED", "DECLINED", "WITHDRAWN"]
)
def test_recursive_privacy_allowlists_on_every_read_surface(
    client, app, invitation_setup, db_factory, status
):
    created = send(client, invitation_setup).json()
    invitation_id = created["id"]
    if status != "SENT":
        owner = "employer" if status == "WITHDRAWN" else "candidate"
        as_user(app, db_factory, invitation_setup[f"{owner}_user_id"])
        action = {
            "VIEWED": "view",
            "ACCEPTED": "accept",
            "DECLINED": "decline",
            "WITHDRAWN": "withdraw",
        }[status]
        response = client.post(f"/{owner}/invitations/{invitation_id}/{action}")
        assert response.status_code == 200
    for employer in (True, False):
        owner = "employer" if employer else "candidate"
        as_user(app, db_factory, invitation_setup[f"{owner}_user_id"])
        detail = client.get(f"/{owner}/invitations/{invitation_id}").json()
        url = (
            f"/employer/needs/{invitation_setup['need_id']}/invitations"
            if employer
            else "/candidate/invitations"
        )
        page = client.get(url).json()
        shape = dict(COMMON)
        if employer:
            shape["candidate_snapshot"] = CANDIDATE
        if status == "ACCEPTED":
            shape["candidate_contact" if employer else "employer_contact"] = (
                {"first_name": None, "last_name": None, "email": None}
                if employer
                else {
                    "company_name": None,
                    "contact_person_name": None,
                    "email": None,
                    "website": None,
                }
            )
        exact_shape(detail, shape)
        exact_shape(
            page, {"items": [shape], "total": None, "limit": None, "offset": None}
        )
        serialized = json.dumps([detail, page])
        for marker in [
            "PRIVATE_ABOUT",
            "PRIVATE_CITY",
            "PRIVATE_FSP",
            invitation_setup["candidate_user_id"],
            invitation_setup["employer_user_id"],
        ]:
            assert marker not in serialized
        if status != "ACCEPTED":
            for marker in [
                "PRIVATE_SURNAME",
                "private-candidate@example.com",
                "employer@example.com",
                "PRIVATE_EMPLOYER_CONTACT",
                "private-company.example.com",
            ]:
                assert marker not in serialized


def test_snapshots_survive_all_edits_and_accept_does_not_reevaluate(
    client, app, invitation_setup, db_factory, monkeypatch
):
    invitation_id = send(client, invitation_setup).json()["id"]
    with db_factory() as db:
        row = db.get(Invitation, invitation_id)
        original = (row.need_snapshot.copy(), row.candidate_snapshot.copy())
        need = db.get(EmployerNeed, invitation_setup["need_id"])
        need.position_title = "Changed title"
        need.salary_from = 0
        need.skill_requirements = []
        need.status = "CLOSED"
        employer = db.get(EmployerProfile, invitation_setup["employer_id"])
        employer.company_name = "Changed company"
        employer.contact_person_name = "Changed contact"
        employer.website = None
        candidate = db.get(CandidateProfile, invitation_setup["candidate_id"])
        candidate.first_name = "Changed candidate"
        candidate.specialization = "FRONTEND"
        candidate.skills = []
        candidate.personal_data_consent = False
        candidate.personal_data_consent_at = None
        candidate.verified_grade = None
        candidate.normalized_assessment_score = None
        candidate.assessment_verified_at = None
        db.commit()

    def forbidden(*args, **kwargs):
        pytest.fail("Responding must not evaluate Matching or assessment")

    monkeypatch.setattr(matching, "evaluate_candidate", forbidden)
    as_user(app, db_factory, invitation_setup["candidate_user_id"])
    response = client.post(f"/candidate/invitations/{invitation_id}/accept")
    assert response.status_code == 200, response.text
    assert response.json()["need_snapshot"]["company_name"] == "Tech"
    assert response.json()["employer_contact"]["company_name"] == "Changed company"
    with db_factory() as db:
        row = db.get(Invitation, invitation_id)
        assert (row.need_snapshot, row.candidate_snapshot) == original


def assessment_state(database):
    with database.connect() as connection:
        metadata = MetaData()
        metadata.reflect(bind=connection)
        state = {}
        for name, table in metadata.tables.items():
            if name.startswith("assessment_") or name == "candidate_profiles":
                state[name] = connection.execute(
                    select(table).order_by(*table.primary_key)
                ).all()
        return state


def test_invitation_operations_do_not_write_or_finalize_assessment(
    client, app, invitation_setup, db_factory, database
):
    with db_factory() as db:
        db.add(
            AssessmentAttempt(
                candidate_id=invitation_setup["candidate_id"],
                specialization="BACKEND",
                target_grade="SENIOR",
                status="IN_PROGRESS",
                started_at=datetime.now(UTC) - timedelta(hours=2),
                expires_at=datetime.now(UTC) - timedelta(hours=1),
            )
        )
        db.commit()
    before = assessment_state(database)
    invitation_id = send(client, invitation_setup).json()["id"]
    client.get(f"/employer/invitations/{invitation_id}")
    client.get(f"/employer/needs/{invitation_setup['need_id']}/invitations")
    as_user(app, db_factory, invitation_setup["candidate_user_id"])
    client.get("/candidate/invitations")
    client.get(f"/candidate/invitations/{invitation_id}")
    assert (
        client.post(f"/candidate/invitations/{invitation_id}/view").status_code == 200
    )
    assert (
        client.post(f"/candidate/invitations/{invitation_id}/accept").status_code == 200
    )
    assert (
        client.post(f"/candidate/invitations/{invitation_id}/accept").status_code == 200
    )
    assert assessment_state(database) == before


def test_send_and_matches_use_same_evaluator(
    client, app, invitation_setup, monkeypatch
):
    original = matching.evaluate_candidate
    calls = []

    def tracked(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append((args[1].candidate_id, result))
        return result

    monkeypatch.setattr(matching, "evaluate_candidate", tracked)
    assert (
        client.get(f"/employer/needs/{invitation_setup['need_id']}/matches").status_code
        == 200
    )
    match_result = calls[-1][1]
    assert send(client, invitation_setup).status_code == 201
    assert calls[-1][1] == match_result
    assert len(calls) == 2
