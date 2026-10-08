import pytest
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError

from app.models import CandidateProfile, FspAchievement
from app.routes.fsp import get_registry_provider
from app.services.fsp_registry import (
    MockFspRegistryProvider,
    RegistryProfile,
    RegistryUnavailable,
)


@pytest.fixture
def fsp_candidate(client, account, candidate_data):
    account()
    data = {**candidate_data, "fsp_id": "MOCK-WINNER"}
    response = client.post("/candidate/profile", json=data)
    assert response.status_code == 201
    return response.json(), data


def state(db_factory, candidate_id):
    with db_factory() as db:
        profile = db.get(CandidateProfile, candidate_id)
        return (
            profile.fsp_verified_id,
            profile.fsp_verified_at,
            profile.fsp_synced_at,
            tuple(
                (a.external_id, a.result_level)
                for a in db.scalars(select(FspAchievement))
            ),
            profile.verified_grade,
            profile.normalized_assessment_score,
            profile.assessment_verified_at,
        )


def test_verify_read_refresh_unlink_preserve_entered_id(
    client, fsp_candidate, db_factory
):
    profile, _ = fsp_candidate
    before = state(db_factory, profile["id"])[4:]
    assert client.get("/candidate/fsp").json()["fsp_verified"] is False
    verified = client.post("/candidate/fsp/verify", json={})
    assert verified.status_code == 200, verified.text
    data = verified.json()
    assert data["fsp_verified"] is True
    assert data["fsp_achievement_score"] == 80
    assert data["fsp_bonus"] == 4
    assert data["provider"] == "MOCK"
    assert data["fsp_verified_at"] and data["fsp_synced_at"]
    assert set(data["achievements"][0]) == {
        "competition_name",
        "discipline",
        "year",
        "event_date",
        "result_level",
        "placement",
        "scope",
    }
    assert client.get("/candidate/fsp").json() == data
    assert client.post("/candidate/fsp/refresh", json={}).status_code == 200
    removed = client.delete("/candidate/fsp/verification")
    assert removed.status_code == 200
    assert removed.json()["fsp_id"] == "MOCK-WINNER"
    assert removed.json()["achievements"] == []
    assert removed.json()["fsp_bonus"] == 0
    assert removed.json()["fsp_synced_at"] is None
    assert client.delete("/candidate/fsp/verification").json() == removed.json()
    assert client.post("/candidate/fsp/refresh", json={}).status_code == 409
    assert state(db_factory, profile["id"])[4:] == before


def test_changing_identifier_invalidates_evidence_atomically(
    client, fsp_candidate, db_factory
):
    profile, data = fsp_candidate
    assert client.post("/candidate/fsp/verify", json={}).status_code == 200
    assert client.put("/candidate/profile", json=data).status_code == 200
    assert client.get("/candidate/fsp").json()["fsp_verified"] is True
    assert (
        client.put(
            "/candidate/profile", json={**data, "fsp_id": "MOCK-TEAM"}
        ).status_code
        == 200
    )
    result = client.get("/candidate/fsp").json()
    assert not result["fsp_verified"]
    assert result["fsp_bonus"] == 0 and result["achievements"] == []
    assert state(db_factory, profile["id"])[0:4] == (None, None, None, ())


@pytest.mark.parametrize("identifier", [None, "", "unknown"])
def test_missing_unknown_id_has_safe_error(client, fsp_candidate, identifier):
    _, data = fsp_candidate
    assert (
        client.put(
            "/candidate/profile", json={**data, "fsp_id": identifier}
        ).status_code
        == 200
    )
    response = client.post("/candidate/fsp/verify", json={})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "fsp_not_available"
    assert not client.get("/candidate/fsp").json()["fsp_verified"]


@pytest.mark.parametrize(
    "field",
    [
        "fsp_id",
        "candidate_id",
        "achievements",
        "fsp_verified_at",
        "fsp_bonus",
        "provider_payload",
    ],
)
def test_mutations_reject_mass_assignment(client, fsp_candidate, field):
    for endpoint in ("verify", "refresh"):
        assert (
            client.post(
                f"/candidate/fsp/{endpoint}", json={field: "injected"}
            ).status_code
            == 422
        )
    assert client.get("/candidate/fsp").json()["fsp_verified"] is False


@pytest.mark.parametrize(
    "role,status", [(None, 401), ("EMPLOYER", 403), ("CANDIDATE", 404)]
)
def test_auth_role_and_profile_required(client, account, role, status):
    if role:
        account(role=role)
    for path, method in (
        ("/candidate/fsp", "get"),
        ("/candidate/fsp/verify", "post"),
        ("/candidate/fsp/refresh", "post"),
        ("/candidate/fsp/verification", "delete"),
    ):
        assert getattr(client, method)(path).status_code == status


def test_untrusted_origin_blocks_all_mutations(client, fsp_candidate):
    for path, method in (
        ("verify", "post"),
        ("refresh", "post"),
        ("verification", "delete"),
    ):
        response = getattr(client, method)(
            f"/candidate/fsp/{path}", headers={"Origin": "https://evil.example"}
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "untrusted_origin"


def test_failed_refresh_rolls_back_and_changed_provider_results_replace(
    app, client, fsp_candidate, db_factory
):
    profile, _ = fsp_candidate
    assert client.post("/candidate/fsp/verify", json={}).status_code == 200
    before = state(db_factory, profile["id"])

    class Failed:
        def lookup(self, identifier):
            raise RegistryUnavailable("PRIVATE_PROVIDER_ERROR")

    app.dependency_overrides[get_registry_provider] = Failed
    response = client.post("/candidate/fsp/refresh", json={})
    assert response.status_code == 503
    assert "PRIVATE" not in response.text
    assert state(db_factory, profile["id"]) == before

    class Changed:
        def lookup(self, identifier):
            item = MockFspRegistryProvider().lookup("MOCK-FINALIST").achievements[0]
            return RegistryProfile((item,))

    app.dependency_overrides[get_registry_provider] = Changed
    result = client.post("/candidate/fsp/refresh", json={}).json()
    assert result["fsp_achievement_score"] == 45
    assert result["achievements"][0]["result_level"] == "FINALIST"
    after = state(db_factory, profile["id"])
    assert after[1] == before[1]
    assert after[2] >= before[2]
    assert after[4:] == before[4:]


def test_duplicate_verified_id_is_conflict_without_foreign_identity_leak(
    client, account, candidate_data, fsp_candidate
):
    assert client.post("/candidate/fsp/verify", json={}).status_code == 200
    account(email="second@example.com")
    assert (
        client.post(
            "/candidate/profile", json={**candidate_data, "fsp_id": "MOCK-WINNER"}
        ).status_code
        == 201
    )
    result = client.post("/candidate/fsp/verify", json={})
    assert result.status_code == 409
    assert result.json()["error"]["code"] == "fsp_verification_conflict"
    assert "candidate@example.com" not in result.text
    assert not client.get("/candidate/fsp").json()["fsp_verified"]


def test_refresh_not_found_preserves_existing_evidence(
    app, client, fsp_candidate, db_factory
):
    profile, _ = fsp_candidate
    assert client.post("/candidate/fsp/verify", json={}).status_code == 200
    before = state(db_factory, profile["id"])

    class Missing:
        def lookup(self, identifier):
            return None

    app.dependency_overrides[get_registry_provider] = Missing
    assert client.post("/candidate/fsp/refresh", json={}).status_code == 404
    assert state(db_factory, profile["id"]) == before


def test_fsp_actions_never_call_assessment_write_paths(
    client, fsp_candidate, monkeypatch
):
    from app.services import assessments

    def forbidden(*args, **kwargs):
        pytest.fail("FSP must not synchronize, finalize or read assessment history")

    for name in ("synchronize_verification", "finalize", "history"):
        monkeypatch.setattr(assessments, name, forbidden)
    for path, method in (
        ("verify", "post"),
        ("refresh", "post"),
        ("verification", "delete"),
    ):
        assert (
            client.request(
                method.upper(), f"/candidate/fsp/{path}", json={}
            ).status_code
            == 200
        )


def test_failure_during_replacement_restores_complete_snapshot(
    app, client, fsp_candidate, db_factory, database
):
    profile, _ = fsp_candidate
    assert client.post("/candidate/fsp/verify", json={}).status_code == 200
    before = state(db_factory, profile["id"])
    with database.connect() as connection:
        before_rows = connection.execute(
            select(FspAchievement.__table__).order_by(FspAchievement.id)
        ).all()
    deleted = []

    class Changed:
        def lookup(self, identifier):
            return MockFspRegistryProvider().lookup("MOCK-MULTI")

    def fail_insert(connection, cursor, statement, parameters, context, executemany):
        sql = statement.lower().lstrip()
        if sql.startswith("delete") and "fsp_achievements" in sql:
            deleted.append(True)
        if sql.startswith("insert") and "fsp_achievements" in sql:
            assert deleted
            raise IntegrityError("PRIVATE_SQL", parameters, RuntimeError("injected"))

    app.dependency_overrides[get_registry_provider] = Changed
    event.listen(database, "before_cursor_execute", fail_insert)
    try:
        response = client.post("/candidate/fsp/refresh", json={})
    finally:
        event.remove(database, "before_cursor_execute", fail_insert)
    assert response.status_code == 409
    assert "PRIVATE_SQL" not in response.text
    assert deleted
    assert state(db_factory, profile["id"]) == before
    with database.connect() as connection:
        assert (
            connection.execute(
                select(FspAchievement.__table__).order_by(FspAchievement.id)
            ).all()
            == before_rows
        )
