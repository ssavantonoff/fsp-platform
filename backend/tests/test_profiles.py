import pytest
from sqlalchemy import select

from app.models import CandidateProfile, Grade


@pytest.mark.parametrize(
    "role,other", [("CANDIDATE", "employer"), ("EMPLOYER", "candidate")]
)
@pytest.mark.parametrize("method", ["GET", "POST", "PUT"])
def test_roles_reject_other_profile_api(
    client, account, candidate_data, employer_data, role, other, method
):
    account(role=role)
    data = candidate_data if other == "candidate" else employer_data
    result = client.request(
        method, f"/{other}/profile", json=data if method != "GET" else None
    )
    assert result.status_code == 403


@pytest.mark.parametrize("path", ["/candidate/profile", "/employer/profile"])
def test_anonymous_has_no_profile_access(client, path):
    assert client.get(path).status_code == 401


def test_candidate_create_read_update_and_skills(client, account, candidate_data):
    user = account()
    assert client.get("/candidate/profile").status_code == 404
    result = client.post("/candidate/profile", json=candidate_data)
    assert result.status_code == 201
    profile = result.json()
    assert profile["user_id"] == user["id"]
    assert profile["verified_grade"] is None
    assert profile["declared_grade"] == "MIDDLE"
    assert profile["personal_data_consent_at"] is not None
    assert {s["id"] for s in profile["skills"]} == set(candidate_data["skill_ids"])
    assert client.get("/candidate/profile").json() == profile
    candidate_data.update(
        first_name="Мария",
        declared_grade="SENIOR",
        skill_ids=candidate_data["skill_ids"][:1],
    )
    updated = client.put("/candidate/profile", json=candidate_data)
    assert updated.status_code == 200
    assert updated.json()["first_name"] == "Мария"
    assert updated.json()["verified_grade"] is None
    assert len(updated.json()["skills"]) == 1
    assert (
        updated.json()["personal_data_consent_at"]
        == profile["personal_data_consent_at"]
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("verified_grade", "SENIOR"),
        ("user_id", "foreign-user"),
        ("role", "EMPLOYER"),
        ("personal_data_consent_at", "2020-01-01T00:00:00Z"),
    ],
)
@pytest.mark.parametrize("method", ["POST", "PUT"])
def test_candidate_cannot_write_canonical_fields(
    client, account, candidate_data, field, value, method
):
    account()
    if method == "PUT":
        assert client.post("/candidate/profile", json=candidate_data).status_code == 201
    result = client.request(
        method, "/candidate/profile", json={**candidate_data, field: value}
    )
    assert result.status_code == 422
    profile = client.get("/candidate/profile")
    if method == "PUT":
        assert profile.json()["verified_grade"] is None
        assert profile.json()["personal_data_consent_at"] != "2020-01-01T00:00:00Z"
    else:
        assert profile.status_code == 404


def test_existing_verified_grade_is_preserved(
    client, account, candidate_data, db_factory
):
    user = account()
    client.post("/candidate/profile", json=candidate_data)
    # Represents a future trusted system operation, never a client API write.
    with db_factory() as db:
        profile = db.scalar(
            select(CandidateProfile).where(CandidateProfile.user_id == user["id"])
        )
        profile.verified_grade = Grade.MIDDLE
        db.commit()
    candidate_data["declared_grade"] = "SENIOR"
    assert (
        client.put("/candidate/profile", json=candidate_data).json()["verified_grade"]
        == "MIDDLE"
    )


@pytest.mark.parametrize("kind", ["candidate", "employer"])
def test_cannot_read_or_mutate_foreign_profile(
    client, account, candidate_data, employer_data, kind
):
    role = kind.upper()
    data = candidate_data if kind == "candidate" else employer_data
    account(role=role, email="owner@example.com")
    original = client.post(f"/{kind}/profile", json=data).json()
    account(role=role, email="intruder@example.com")
    assert client.get(f"/{kind}/profile").status_code == 404
    assert client.put(f"/{kind}/profile", json=data).status_code == 404
    assert client.put(f"/{kind}/profile/{original['id']}", json=data).status_code == 404
    assert client.get(f"/{kind}/profile/{original['id']}").status_code == 404
    assert (
        client.post(
            f"/{kind}/profile", json={**data, "user_id": original["user_id"]}
        ).status_code
        == 422
    )
    assert client.post(f"/{kind}/profile", json=data).status_code == 201
    assert (
        client.put(
            f"/{kind}/profile", json={**data, "user_id": original["user_id"]}
        ).status_code
        == 422
    )
    from conftest import PASSWORD

    client.post(
        "/auth/login", json={"email": "owner@example.com", "password": PASSWORD}
    )
    assert client.get(f"/{kind}/profile").json() == original


def test_unknown_skills_do_not_partially_update_profile(
    client, account, candidate_data
):
    account()
    original = client.post("/candidate/profile", json=candidate_data).json()
    result = client.put(
        "/candidate/profile",
        json={**candidate_data, "first_name": "Изменено", "skill_ids": ["unknown"]},
    )
    assert result.status_code == 422
    assert client.get("/candidate/profile").json() == original


@pytest.mark.parametrize(
    "patch",
    [
        {"skill_ids": ["duplicate", "duplicate"]},
        {"years_of_experience": -1},
        {"years_of_experience": 81},
        {"years_of_experience": "NaN"},
        {"first_name": "   "},
        {"specialization": "UNKNOWN"},
        {"declared_grade": "EXPERT"},
    ],
)
def test_candidate_validation(client, account, candidate_data, patch):
    account()
    assert (
        client.post("/candidate/profile", json={**candidate_data, **patch}).status_code
        == 422
    )


def test_consent_timestamp_transitions_and_skills_clear(
    client, account, candidate_data
):
    account()
    candidate_data["personal_data_consent"] = False
    result = client.post("/candidate/profile", json=candidate_data)
    assert result.json()["personal_data_consent_at"] is None
    candidate_data["personal_data_consent"] = True
    assert (
        client.put("/candidate/profile", json=candidate_data).json()[
            "personal_data_consent_at"
        ]
        is not None
    )
    candidate_data.update(personal_data_consent=False, skill_ids=[])
    result = client.put("/candidate/profile", json=candidate_data)
    assert result.json()["personal_data_consent_at"] is None
    assert result.json()["skills"] == []


@pytest.mark.parametrize("kind", ["candidate", "employer"])
def test_repeated_profile_creation_is_conflict(
    client, account, candidate_data, employer_data, kind
):
    account(role=kind.upper())
    data = candidate_data if kind == "candidate" else employer_data
    assert client.post(f"/{kind}/profile", json=data).status_code == 201
    assert client.post(f"/{kind}/profile", json=data).status_code == 409


def test_employer_create_and_update(client, account, employer_data):
    user = account(role="EMPLOYER")
    result = client.post("/employer/profile", json=employer_data)
    assert result.status_code == 201
    assert result.json()["user_id"] == user["id"]
    assert result.json()["website"] is None
    employer_data.update(
        company_name="Updated",
        website="https://example.com",
        company_description="Описание",
    )
    result = client.put("/employer/profile", json=employer_data)
    assert result.status_code == 200
    assert result.json()["company_name"] == "Updated"
    assert result.json()["website"] == "https://example.com/"
    assert client.get("/employer/profile").json() == result.json()


@pytest.mark.parametrize(
    "website", ["javascript:alert(1)", "ftp://example.com", "not-a-url"]
)
def test_employer_website_validation(client, account, employer_data, website):
    account(role="EMPLOYER")
    assert (
        client.post(
            "/employer/profile", json={**employer_data, "website": website}
        ).status_code
        == 422
    )


def test_employer_required_fields(client, account, employer_data):
    account(role="EMPLOYER")
    assert (
        client.post(
            "/employer/profile", json={**employer_data, "company_name": " "}
        ).status_code
        == 422
    )


def test_skills_endpoint_returns_catalog(client, skill_ids):
    result = client.get("/skills")
    assert result.status_code == 200
    assert {skill["id"] for skill in result.json()} == set(skill_ids)
    assert [s["name"] for s in result.json()] == ["Django", "PostgreSQL", "Python"]


def test_no_role_update_api(client, account):
    account()
    assert client.put("/auth/me", json={"role": "EMPLOYER"}).status_code == 405
    assert client.get("/auth/me").json()["role"] == "CANDIDATE"
