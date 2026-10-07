import json
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.dependencies import current_user
from app.models import (
    CandidateProfile,
    EmployerNeed,
    EmployerProfile,
    Invitation,
    User,
)
from app.routes.employer_needs import get_assessment_provider
from app.services.candidate_assessments import CandidateAssessment


def as_user(app, db_factory, user_id):
    def authenticated():
        with db_factory() as db:
            return db.get(User, user_id)

    app.dependency_overrides[current_user] = authenticated


def send(client, setup, **extra):
    return client.post(
        f"/employer/needs/{setup['need_id']}/invitations",
        json={"candidate_id": setup["candidate_id"], **extra},
    )


def test_send_uses_current_match_and_masks_candidate(
    client, invitation_setup, db_factory
):
    match = client.get(f"/employer/needs/{invitation_setup['need_id']}/matches").json()[
        "items"
    ][0]
    response = send(client, invitation_setup, message=" <b>Plain text</b> ")
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["status"] == "SENT"
    assert (
        result["candidate_snapshot"]["professional_fit_score"]
        == match["professional_fit_score"]
    )
    assert result["candidate_snapshot"]["breakdown"] == match["breakdown"]
    assert result["candidate_snapshot"]["display_name"] == match["display_name"]
    assert result["message"] == " <b>Plain text</b> "
    assert result["viewed_at"] is None
    assert "candidate_contact" not in result
    with db_factory() as db:
        saved = db.get(Invitation, result["id"])
        assert saved.employer_id == invitation_setup["employer_id"]
        assert set(saved.candidate_snapshot) == {
            "candidate_id",
            "display_name",
            "specialization",
            "verified_grade",
            "normalized_assessment_score",
            "assessment_verified_at",
            "professional_fit_score",
            "breakdown",
        }
        assert saved.need_snapshot["contact_person_name"] == "PRIVATE_EMPLOYER_CONTACT"
        assert saved.need_snapshot["salary_from"] == "100000.00"


@pytest.mark.parametrize(
    "extra",
    [
        {"employer_id": "foreign"},
        {"need_snapshot": {}},
        {"candidate_snapshot": {}},
        {"status": "ACCEPTED"},
        {"salary_from": "0"},
        {"message": "я" * 2001},
    ],
)
def test_send_rejects_injected_fields(client, invitation_setup, db_factory, extra):
    response = send(client, invitation_setup, **extra)
    assert response.status_code == 422
    with db_factory() as db:
        assert db.scalar(select(Invitation)) is None


@pytest.mark.parametrize(
    "action,target",
    [("view", "VIEWED"), ("accept", "ACCEPTED"), ("decline", "DECLINED")],
)
def test_candidate_actions_and_get_are_read_only(
    client, app, invitation_setup, db_factory, action, target
):
    created = send(client, invitation_setup).json()
    invitation_id = created["id"]
    as_user(app, db_factory, invitation_setup["candidate_user_id"])
    before = client.get(f"/candidate/invitations/{invitation_id}")
    assert before.status_code == 200
    assert before.json()["status"] == "SENT"
    response = client.post(f"/candidate/invitations/{invitation_id}/{action}")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == target
    assert (response.json()["viewed_at"] is not None) == (action == "view")
    repeated = client.post(f"/candidate/invitations/{invitation_id}/{action}")
    assert repeated.status_code == 200
    assert repeated.json() == response.json()


def test_employer_read_and_withdraw(client, invitation_setup):
    created = send(client, invitation_setup).json()
    invitation_id = created["id"]
    detail = client.get(f"/employer/invitations/{invitation_id}")
    assert detail.status_code == 200
    assert detail.json() == created
    page = client.get(
        f"/employer/needs/{invitation_setup['need_id']}/invitations"
    ).json()
    assert page == {"items": [created], "total": 1, "limit": 20, "offset": 0}
    withdrawn = client.post(f"/employer/invitations/{invitation_id}/withdraw")
    assert withdrawn.status_code == 200
    assert withdrawn.json()["status"] == "WITHDRAWN"
    assert withdrawn.json()["viewed_at"] is None
    assert (
        client.post(f"/employer/invitations/{invitation_id}/withdraw").json()
        == withdrawn.json()
    )


def test_mutual_contact_unlock(client, app, invitation_setup, db_factory):
    invitation_id = send(client, invitation_setup).json()["id"]
    as_user(app, db_factory, invitation_setup["candidate_user_id"])
    for payload in [
        client.get("/candidate/invitations").json(),
        client.get(f"/candidate/invitations/{invitation_id}").json(),
    ]:
        serialized = json.dumps(payload)
        assert "PRIVATE_EMPLOYER_CONTACT" not in serialized
        assert "private-company.example.com" not in serialized
        assert "employer@example.com" not in serialized
    accepted = client.post(f"/candidate/invitations/{invitation_id}/accept").json()
    assert accepted["employer_contact"] == {
        "company_name": "Tech",
        "contact_person_name": "PRIVATE_EMPLOYER_CONTACT",
        "email": "employer@example.com",
        "website": "https://private-company.example.com",
    }
    as_user(app, db_factory, invitation_setup["employer_user_id"])
    detail = client.get(f"/employer/invitations/{invitation_id}").json()
    assert detail["candidate_contact"] == {
        "first_name": "Анна",
        "last_name": "PRIVATE_SURNAME",
        "email": "private-candidate@example.com",
    }


@pytest.mark.parametrize(
    "reason",
    [
        "missing",
        "specialization",
        "skills",
        "consent",
        "verification",
        "assessment_missing",
        "score_invalid",
    ],
)
def test_unavailable_candidates_have_identical_external_error(
    client, app, invitation_setup, db_factory, reason
):
    with db_factory() as db:
        candidate = db.get(CandidateProfile, invitation_setup["candidate_id"])
        if reason == "specialization":
            candidate.specialization = "FRONTEND"
        elif reason == "skills":
            candidate.skills = []
            candidate.normalized_assessment_score = 99
        elif reason == "consent":
            candidate.personal_data_consent = False
            candidate.personal_data_consent_at = None
        elif reason == "verification":
            candidate.verified_grade = None
            candidate.normalized_assessment_score = None
            candidate.assessment_verified_at = None
        db.commit()
    if reason in {"assessment_missing", "score_invalid"}:

        class Provider:
            def get_assessments(self, ids):
                return (
                    {}
                    if reason == "assessment_missing"
                    else {
                        ids[0]: CandidateAssessment(
                            ids[0], "MIDDLE", 101, datetime.now(UTC)
                        )
                    }
                )

        app.dependency_overrides[get_assessment_provider] = lambda: Provider()
    setup = dict(invitation_setup)
    if reason == "missing":
        setup["candidate_id"] = "arbitrary-missing-candidate"
    response = send(client, setup)
    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "candidate_not_available",
            "message": "Кандидат недоступен для приглашения.",
            "fields": [],
        }
    }
    with db_factory() as db:
        assert db.scalar(select(Invitation)) is None


@pytest.mark.parametrize("state", ["DRAFT", "CLOSED"])
def test_send_requires_active_need(client, invitation_setup, db_factory, state):
    with db_factory() as db:
        db.get(EmployerNeed, invitation_setup["need_id"]).status = state
        db.commit()
    response = send(client, invitation_setup)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "need_state_conflict"


@pytest.mark.parametrize(
    "state", ["SENT", "VIEWED", "ACCEPTED", "DECLINED", "WITHDRAWN"]
)
def test_reinvite_rules(client, app, invitation_setup, db_factory, state):
    invitation_id = send(client, invitation_setup).json()["id"]
    if state in {"VIEWED", "ACCEPTED", "DECLINED"}:
        as_user(app, db_factory, invitation_setup["candidate_user_id"])
        action = {"VIEWED": "view", "ACCEPTED": "accept", "DECLINED": "decline"}[state]
        assert (
            client.post(f"/candidate/invitations/{invitation_id}/{action}").status_code
            == 200
        )
    elif state == "WITHDRAWN":
        assert (
            client.post(f"/employer/invitations/{invitation_id}/withdraw").status_code
            == 200
        )
    as_user(app, db_factory, invitation_setup["employer_user_id"])
    response = send(client, invitation_setup)
    expected = 201 if state in {"DECLINED", "WITHDRAWN"} else 409
    assert response.status_code == expected, response.text
    if expected == 409:
        assert response.json()["error"]["code"] == "invitation_conflict"
    with db_factory() as db:
        assert len(list(db.scalars(select(Invitation)))) == (
            2 if expected == 201 else 1
        )


@pytest.mark.parametrize(
    "source", ["SENT", "VIEWED", "ACCEPTED", "DECLINED", "WITHDRAWN"]
)
@pytest.mark.parametrize(
    "action,target",
    [
        ("view", "VIEWED"),
        ("accept", "ACCEPTED"),
        ("decline", "DECLINED"),
        ("withdraw", "WITHDRAWN"),
    ],
)
def test_api_transition_matrix(
    client, app, invitation_setup, db_factory, source, action, target
):
    invitation_id = send(client, invitation_setup).json()["id"]
    if source != "SENT":
        initial_action = {
            "VIEWED": "view",
            "ACCEPTED": "accept",
            "DECLINED": "decline",
            "WITHDRAWN": "withdraw",
        }[source]
        as_user(
            app,
            db_factory,
            invitation_setup["employer_user_id"]
            if source == "WITHDRAWN"
            else invitation_setup["candidate_user_id"],
        )
        route = "employer" if source == "WITHDRAWN" else "candidate"
        assert (
            client.post(
                f"/{route}/invitations/{invitation_id}/{initial_action}"
            ).status_code
            == 200
        )
    as_user(
        app,
        db_factory,
        invitation_setup["employer_user_id"]
        if action == "withdraw"
        else invitation_setup["candidate_user_id"],
    )
    route = "employer" if action == "withdraw" else "candidate"
    with db_factory() as db:
        before = db.get(Invitation, invitation_id)
        timestamps = (
            before.viewed_at,
            before.responded_at,
            before.withdrawn_at,
            before.updated_at,
        )
    response = client.post(f"/{route}/invitations/{invitation_id}/{action}")
    allowed = source in {"SENT", "VIEWED"} or source == target
    assert response.status_code == (200 if allowed else 409), response.text
    with db_factory() as db:
        saved = db.get(Invitation, invitation_id)
        assert saved.status == (target if allowed else source)
        if source == target or not allowed:
            assert (
                saved.viewed_at,
                saved.responded_at,
                saved.withdrawn_at,
                saved.updated_at,
            ) == timestamps
        if source == "SENT" and target != "VIEWED":
            assert saved.viewed_at is None


ROUTES = [
    ("POST", "/employer/needs/{need_id}/invitations", True),
    ("GET", "/employer/needs/{need_id}/invitations", True),
    ("GET", "/employer/invitations/{id}", True),
    ("POST", "/employer/invitations/{id}/withdraw", True),
    ("GET", "/candidate/invitations", False),
    ("GET", "/candidate/invitations/{id}", False),
    ("POST", "/candidate/invitations/{id}/view", False),
    ("POST", "/candidate/invitations/{id}/accept", False),
    ("POST", "/candidate/invitations/{id}/decline", False),
]


@pytest.mark.parametrize("method,path,employer", ROUTES)
@pytest.mark.parametrize("anonymous", [True, False])
def test_invitation_auth_roles(
    client, app, invitation_setup, db_factory, method, path, employer, anonymous
):
    client.cookies.clear()
    if not anonymous:
        as_user(
            app,
            db_factory,
            invitation_setup["candidate_user_id"]
            if employer
            else invitation_setup["employer_user_id"],
        )
    response = client.request(
        method,
        path.format(need_id=invitation_setup["need_id"], id="missing"),
        json={"candidate_id": invitation_setup["candidate_id"]}
        if "/needs/" in path and method == "POST"
        else None,
    )
    assert response.status_code == (401 if anonymous else 403)


@pytest.mark.parametrize("method,path,employer", [r for r in ROUTES if r[0] == "POST"])
@pytest.mark.parametrize("origin", [None, "https://untrusted.example.com"])
def test_all_invitation_mutations_require_origin(
    client, app, invitation_setup, db_factory, method, path, employer, origin
):
    invitation_id = send(client, invitation_setup).json()["id"]
    as_user(
        app,
        db_factory,
        invitation_setup["employer_user_id"]
        if employer
        else invitation_setup["candidate_user_id"],
    )
    client.headers.pop("Origin")
    response = client.request(
        method,
        path.format(need_id=invitation_setup["need_id"], id=invitation_id),
        headers={} if origin is None else {"Origin": origin},
        json={"candidate_id": invitation_setup["candidate_id"]}
        if "/needs/" in path
        else None,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "untrusted_origin"
    with db_factory() as db:
        assert db.get(Invitation, invitation_id).status == "SENT"


@pytest.mark.parametrize(
    "method,path,employer", [r for r in ROUTES if r[1] != "/candidate/invitations"]
)
@pytest.mark.parametrize("missing", [False, True])
def test_foreign_and_missing_resources_are_identical(
    client, app, invitation_setup, db_factory, account, method, path, employer, missing
):
    invitation_id = send(client, invitation_setup).json()["id"]
    foreign_user = account(
        role="EMPLOYER" if employer else "CANDIDATE", email="other@example.com"
    )
    as_user(app, db_factory, foreign_user["id"])
    with db_factory() as db:
        if employer:
            db.add(
                EmployerProfile(
                    user_id=foreign_user["id"],
                    company_name="Other",
                    contact_person_name="Other",
                )
            )
        else:
            db.add(
                CandidateProfile(
                    user_id=foreign_user["id"],
                    first_name="Other",
                    last_name="Other",
                    specialization="BACKEND",
                    declared_grade="JUNIOR",
                )
            )
        db.commit()
    response = client.request(
        method,
        path.format(
            need_id="missing" if missing else invitation_setup["need_id"],
            id="missing" if missing else invitation_id,
        ),
        json={"candidate_id": invitation_setup["candidate_id"]}
        if "/needs/" in path and method == "POST"
        else None,
    )
    assert response.status_code == 404
    code = response.json()["error"]["code"]
    assert code == ("need_not_found" if "/needs/" in path else "invitation_not_found")


@pytest.mark.parametrize("score", [None, -1, 101, True, 80.0, "80"])
def test_invalid_provider_scores_are_not_inviteable(
    client, app, invitation_setup, score
):
    class Provider:
        def get_assessments(self, ids):
            return {
                ids[0]: CandidateAssessment(ids[0], "MIDDLE", score, datetime.now(UTC))
            }

    app.dependency_overrides[get_assessment_provider] = lambda: Provider()
    response = send(client, invitation_setup)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "candidate_not_available"


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
@pytest.mark.parametrize("employer", [True, False])
def test_invitation_pagination_validation(
    client, app, invitation_setup, db_factory, query, employer
):
    as_user(
        app,
        db_factory,
        invitation_setup["employer_user_id" if employer else "candidate_user_id"],
    )
    path = (
        f"/employer/needs/{invitation_setup['need_id']}/invitations"
        if employer
        else "/candidate/invitations"
    )
    assert client.get(f"{path}?{query}").status_code == 422


def test_empty_lists_and_pagination(client, app, invitation_setup, db_factory):
    employer_path = f"/employer/needs/{invitation_setup['need_id']}/invitations"
    assert client.get(employer_path).json() == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 0,
    }
    ids = []
    for _ in range(3):
        as_user(app, db_factory, invitation_setup["employer_user_id"])
        invitation_id = send(client, invitation_setup).json()["id"]
        ids.append(invitation_id)
        assert (
            client.post(f"/employer/invitations/{invitation_id}/withdraw").status_code
            == 200
        )
    for employer in (True, False):
        as_user(
            app,
            db_factory,
            invitation_setup["employer_user_id" if employer else "candidate_user_id"],
        )
        path = employer_path if employer else "/candidate/invitations"
        page = client.get(f"{path}?limit=1&offset=1").json()
        assert page["total"] == 3 and page["limit"] == 1 and page["offset"] == 1
        assert [r["id"] for r in page["items"]] == [ids[1]]
        assert [r["id"] for r in client.get(path).json()["items"]] == list(
            reversed(ids)
        )
