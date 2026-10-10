"""P8-B0-002: allowed combined writes are atomic, including FSP reset."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models import CandidateProfile, FspAchievement
from tests.conftest import ORIGIN


def setup_profile(client, account, candidate_data, initial_consent, verified):
    account()
    payload = {
        **candidate_data,
        "personal_data_consent": initial_consent,
        "fsp_id": "MOCK-WINNER",
    }
    response = client.post("/candidate/profile", json=payload)
    assert response.status_code == 201, response.text
    if verified:
        response = client.post("/candidate/fsp/verify", json={})
        assert response.status_code == 200, response.text
    return payload, client.get("/candidate/profile").json()


@pytest.mark.parametrize("initial_consent", [True, False])
@pytest.mark.parametrize("verified", [True, False])
def test_combined_consent_and_fsp_id_is_one_successful_atomic_update(
    client,
    app,
    account,
    candidate_data,
    db_factory,
    initial_consent,
    verified,
):
    payload, before = setup_profile(
        client, account, candidate_data, initial_consent, verified
    )
    with TestClient(
        app, headers={"Origin": ORIGIN}, raise_server_exceptions=False
    ) as owner:
        owner.cookies.update(client.cookies)
        response = owner.put(
            "/candidate/profile",
            json={
                **payload,
                "personal_data_consent": not initial_consent,
                "fsp_id": "MOCK-TEAM",
                "first_name": "Atomic update",
            },
        )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["personal_data_consent"] is (not initial_consent)
    assert (result["personal_data_consent_at"] is not None) is (not initial_consent)
    assert result["fsp_id"] == "MOCK-TEAM"
    assert result["first_name"] == "Atomic update"
    assert result == client.get("/candidate/profile").json()
    status = client.get("/candidate/fsp").json()
    assert status["fsp_verified"] is False
    assert status["fsp_bonus"] == 0
    assert status["achievements"] == []
    with db_factory() as db:
        profile = db.get(CandidateProfile, before["id"])
        assert profile.personal_data_consent is (not initial_consent)
        assert (profile.personal_data_consent_at is not None) is (not initial_consent)
        assert profile.fsp_id == "MOCK-TEAM"
        assert profile.fsp_verified_id is None
        assert profile.fsp_verified_at is None
        assert profile.fsp_synced_at is None
        assert db.scalar(select(func.count()).select_from(FspAchievement)) == 0


@pytest.mark.parametrize("initial_consent", [True, False])
@pytest.mark.parametrize("verified", [True, False])
def test_combined_update_rolls_back_all_fields_and_evidence_after_flush_failure(
    client,
    app,
    account,
    candidate_data,
    db_factory,
    monkeypatch,
    initial_consent,
    verified,
):
    payload, before = setup_profile(
        client, account, candidate_data, initial_consent, verified
    )
    evidence_before = client.get("/candidate/fsp").json()
    original_commit = db_factory.class_.commit
    flushed = []

    def fail_after_flush(db):
        if any(
            isinstance(row, CandidateProfile) and row.first_name == "Rollback"
            for row in db.identity_map.values()
        ):
            db.flush()
            flushed.append(True)
            raise IntegrityError(
                "injected post-flush failure", {}, Exception("synthetic constraint")
            )
        return original_commit(db)

    monkeypatch.setattr(db_factory.class_, "commit", fail_after_flush)
    with TestClient(
        app, headers={"Origin": ORIGIN}, raise_server_exceptions=False
    ) as owner:
        owner.cookies.update(client.cookies)
        response = owner.put(
            "/candidate/profile",
            json={
                **payload,
                "personal_data_consent": not initial_consent,
                "fsp_id": "MOCK-TEAM",
                "first_name": "Rollback",
                "skill_ids": candidate_data["skill_ids"][:1],
            },
        )
    assert flushed == [True], (
        "Fault must occur after the complete update reached PostgreSQL"
    )
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "profile_conflict"
    assert client.get("/candidate/profile").json() == before
    assert client.get("/candidate/fsp").json() == evidence_before
