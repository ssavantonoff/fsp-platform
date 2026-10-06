import json
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest
from sqlalchemy import event, select

from app.models import CandidateProfile, EmployerNeed, Grade, Specialization, User
from app.routes.employer_needs import get_assessment_provider
from app.services import assessments, employer_needs, matching
from app.services.candidate_assessments import (
    CandidateAssessment,
    ProfileAssessmentProvider,
)
from app.services.matching_rules import (
    CandidateMatchInput,
    eligible_candidate,
    score_professional_fit,
)

BASE = "/employer/needs"


@pytest.fixture
def active_need(client, employer_account, need_data):
    user, _ = employer_account()
    response = client.post(BASE, json=need_data)
    assert response.status_code == 201, response.text
    need_id = response.json()["id"]
    assert client.post(f"{BASE}/{need_id}/activate").status_code == 200
    return user["id"], need_id


def matches(client, active_need, **params):
    response = client.get(f"{BASE}/{active_need[1]}/matches", params=params)
    assert response.status_code == 200, response.text
    assert response.headers["Cache-Control"] == "no-store"
    return response.json()


@contextmanager
def captured_sql(database):
    statements = []

    def capture(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())

    event.listen(database, "before_cursor_execute", capture)
    try:
        yield statements
    finally:
        event.remove(database, "before_cursor_execute", capture)


class FakeProvider:
    def __init__(self, values):
        self.values = values
        self.calls = []

    def get_assessments(self, candidate_ids):
        self.calls.append(list(candidate_ids))
        return self.values


def canonical(db_factory, candidate_id):
    with db_factory() as db:
        return tuple(
            db.execute(
                select(
                    CandidateProfile.verified_grade,
                    CandidateProfile.normalized_assessment_score,
                    CandidateProfile.assessment_verified_at,
                ).where(CandidateProfile.id == candidate_id)
            ).one()
        )


@pytest.mark.parametrize(
    "scenario,status,code",
    [
        ("active", 200, None),
        ("anonymous", 401, "unauthorized"),
        ("candidate", 403, "forbidden"),
        ("foreign", 404, "need_not_found"),
        ("missing", 404, "need_not_found"),
        ("draft", 409, "need_state_conflict"),
        ("closed", 409, "need_state_conflict"),
        ("no_profile", 404, "profile_not_found"),
    ],
)
def test_matching_permissions_and_status(
    client, account, employer_account, need_data, scenario, status, code
):
    if scenario in {"anonymous", "candidate", "no_profile"}:
        if scenario != "anonymous":
            account(role="EMPLOYER" if scenario == "no_profile" else "CANDIDATE")
        need_id = "missing"
    else:
        employer_account()
        need_id = client.post(BASE, json=need_data).json()["id"]
        if scenario != "draft":
            assert client.post(f"{BASE}/{need_id}/activate").status_code == 200
        if scenario == "closed":
            assert client.post(f"{BASE}/{need_id}/close").status_code == 200
        if scenario == "foreign":
            employer_account("other@example.com")
        if scenario == "missing":
            need_id = "missing"
    response = client.get(f"{BASE}/{need_id}/matches")
    assert response.status_code == status, response.text
    assert response.headers["Cache-Control"] == "no-store"
    if code is not None:
        assert set(response.json()) == {"error"}
        assert set(response.json()["error"]) == {"code", "message", "fields"}
        assert response.json()["error"]["code"] == code
    else:
        assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


def test_matching_uses_injected_assessment_provider(
    app, client, active_need, matching_candidate, db_factory
):
    candidate_id = matching_candidate()
    before = canonical(db_factory, candidate_id)
    provider = FakeProvider(
        {candidate_id: CandidateAssessment(candidate_id, Grade.MIDDLE, 0, None)}
    )
    app.dependency_overrides[get_assessment_provider] = lambda: provider
    result = matches(client, active_need)
    assert provider.calls == [[candidate_id]]
    assert result["items"][0]["normalized_assessment_score"] == 0
    assert result["items"][0]["professional_fit_score"] == pytest.approx(50)
    assert canonical(db_factory, candidate_id) == before


def test_matching_excludes_failed_hard_filters(
    client, active_need, matching_candidate, skill_ids, monkeypatch
):
    allowed = matching_candidate(normalized_assessment_score=0)
    matching_candidate(skill_ids=skill_ids[1:], normalized_assessment_score=100)
    matching_candidate(verified=False)
    matching_candidate(specialization=Specialization.FRONTEND)
    matching_candidate(personal_data_consent=False)
    matching_candidate(verified_grade=Grade.JUNIOR)
    scoring_calls = []
    original = score_professional_fit

    def score(data):
        scoring_calls.append(data)
        return original(data)

    monkeypatch.setattr(matching, "score_professional_fit", score, raising=False)
    result = matches(client, active_need)
    assert [item["candidate_id"] for item in result["items"]] == [allowed]
    assert result["total"] == 1
    assert len(scoring_calls) == 1
    assert scoring_calls[0].normalized_assessment_score == 0


@pytest.mark.parametrize(
    "nice,target,years,grade,score,maxima,active",
    [
        (True, 4, 2, Grade.MIDDLE, 76, [45, 25, 15, 15], [True] * 4),
        (
            False,
            None,
            None,
            Grade.MIDDLE,
            610 / 7,
            [450 / 7, 250 / 7, 0, 0],
            [True, True, False, False],
        ),
        (
            False,
            4,
            2,
            Grade.MIDDLE,
            1370 / 17,
            [900 / 17, 500 / 17, 0, 300 / 17],
            [True, True, False, True],
        ),
        (
            True,
            None,
            None,
            Grade.SENIOR,
            1245 / 17,
            [900 / 17, 500 / 17, 300 / 17, 0],
            [True, True, True, False],
        ),
    ],
)
def test_matching_breakdown_and_optional_exclusion(
    client,
    active_need,
    need_data,
    matching_candidate,
    skill_ids,
    nice,
    target,
    years,
    grade,
    score,
    maxima,
    active,
):
    # Two nice requirements with one matching: 36 + 25 + 7.5 + 7.5 = 76.
    payload = {
        **need_data,
        "must_have_skill_ids": skill_ids[:1],
        "nice_to_have_skill_ids": skill_ids[1:] if nice else [],
        "target_experience_years": target,
    }
    assert client.put(f"{BASE}/{active_need[1]}", json=payload).status_code == 200
    matching_candidate(
        skill_ids=skill_ids[:2], years_of_experience=years, verified_grade=grade
    )
    item = matches(client, active_need)["items"][0]
    assert item["professional_fit_score"] == pytest.approx(score)
    breakdown = item["breakdown"]
    factors = [
        breakdown[key] for key in ("assessment", "grade", "nice_to_have", "experience")
    ]
    assert [factor["max"] for factor in factors] == pytest.approx(maxima)
    assert [factor["active"] for factor in factors] == active
    assert sum(factor["score"] for factor in factors) == pytest.approx(score)
    assert breakdown["grade"]["exact_match"] is (grade == Grade.MIDDLE)
    assert breakdown["nice_to_have"]["matched"] == (1 if nice else 0)
    assert breakdown["nice_to_have"]["total"] == (2 if nice else 0)
    assert [s["id"] for s in item["matched_must_have_skills"]] == skill_ids[:1]
    assert [s["id"] for s in item["matched_nice_to_have_skills"]] == (
        skill_ids[1:2] if nice else []
    )
    assert [s["id"] for s in item["missing_nice_to_have_skills"]] == (
        skill_ids[2:] if nice else []
    )
    if nice and target == 4:
        assert [factor["score"] for factor in factors] == [36, 25, 7.5, 7.5]


def test_matching_preview_exact_allowlist(
    client, active_need, matching_candidate, database
):
    matching_candidate()
    with captured_sql(database) as statements:
        result = matches(client, active_need)
    assert set(result) == {"items", "total", "limit", "offset"}
    item = result["items"][0]
    assert set(item) == {
        "candidate_id",
        "display_name",
        "specialization",
        "verified_grade",
        "skills",
        "years_of_experience",
        "normalized_assessment_score",
        "assessment_verified_at",
        "professional_fit_score",
        "breakdown",
        "matched_must_have_skills",
        "matched_nice_to_have_skills",
        "missing_nice_to_have_skills",
    }
    assert item["display_name"] == "Анна И."
    for key in (
        "skills",
        "matched_must_have_skills",
        "matched_nice_to_have_skills",
        "missing_nice_to_have_skills",
    ):
        for skill in item[key]:
            assert set(skill) == {"id", "name"}
        assert item[key] == sorted(
            item[key], key=lambda skill: (skill["name"], skill["id"])
        )
    assert set(item["breakdown"]) == {
        "assessment",
        "grade",
        "nice_to_have",
        "experience",
    }
    for key, factor in item["breakdown"].items():
        assert set(factor) == {"score", "max", "active"} | (
            {"exact_match"}
            if key == "grade"
            else {"matched", "total"}
            if key == "nice_to_have"
            else set()
        )
    forbidden = {
        "email",
        "phone",
        "telegram",
        "address",
        "city",
        "about",
        "user_id",
        "last_name",
        "declared_grade",
        "fsp_id",
        "personal_data_consent",
        "personal_data_consent_at",
        "created_at",
        "updated_at",
        "attempt_id",
        "history",
    }

    def assert_safe(value):
        if isinstance(value, dict):
            assert not forbidden.intersection(value)
            for nested in value.values():
                assert_safe(nested)
        elif isinstance(value, list):
            for nested in value:
                assert_safe(nested)

    assert_safe(result)
    serialized = json.dumps(result, ensure_ascii=False)
    for marker in ("Иванова", "PRIVATE_", "@example.com", "+79991234567", "@anna"):
        assert marker not in serialized
    pool = next(sql for sql in statements if "substr(" in sql)
    projection = pool.split("from candidate_profiles")[0]
    assert "substr(candidate_profiles.last_name" in projection
    assert "candidate_profiles.last_name" not in projection.replace(
        "substr(candidate_profiles.last_name", "substr(surname_initial"
    )
    for field in (
        "user_id",
        "city",
        "about",
        "fsp_id",
        "personal_data_consent_at",
        "declared_grade",
        "verified_grade",
        "normalized_assessment_score",
        "assessment_verified_at",
        "created_at",
        "updated_at",
    ):
        assert f"candidate_profiles.{field}" not in projection


@pytest.mark.parametrize(
    "date", [None, datetime(2026, 9, 18), datetime(2026, 9, 18, tzinfo=UTC)]
)
def test_matching_allows_assessment_verified_at(
    app, client, active_need, matching_candidate, date
):
    candidate_id = matching_candidate()
    provider = FakeProvider(
        {candidate_id: CandidateAssessment(candidate_id, Grade.MIDDLE, 80, date)}
    )
    app.dependency_overrides[get_assessment_provider] = lambda: provider
    item = matches(client, active_need)["items"][0]
    assert item["assessment_verified_at"] == ("2026-09-18T00:00:00Z" if date else None)


@pytest.mark.parametrize(
    "invalid",
    [
        "missing",
        "null_score",
        "no_grade",
        "mismatch",
        "nan",
        "float",
        "boolean",
        "out_of_range",
    ],
)
def test_matching_rejects_invalid_provider_state(
    app, client, active_need, matching_candidate, invalid
):
    candidate_id = matching_candidate()
    scores = {
        "null_score": None,
        "nan": float("nan"),
        "float": 80.0,
        "boolean": True,
        "out_of_range": 101,
    }
    value = CandidateAssessment(
        "foreign" if invalid == "mismatch" else candidate_id,
        None if invalid == "no_grade" else Grade.MIDDLE,
        scores.get(invalid, 80),
        None,
    )
    provider = FakeProvider({} if invalid == "missing" else {candidate_id: value})
    app.dependency_overrides[get_assessment_provider] = lambda: provider
    assert matches(client, active_need)["items"] == []
    assert provider.calls == [[candidate_id]]


@pytest.mark.parametrize(
    "field,value",
    [
        ("declared_grade", Grade.SENIOR),
        ("fsp_id", "new-private-fsp"),
        ("updated_at", datetime(2000, 1, 1, tzinfo=UTC)),
        ("assessment_verified_at", datetime(2000, 1, 1, tzinfo=UTC)),
    ],
)
def test_matching_ignores_declared_grade_fsp_and_recency(
    client, active_need, matching_candidate, db_factory, field, value
):
    candidate_id = matching_candidate()
    matching_candidate(verified_grade=Grade.SENIOR, normalized_assessment_score=81)
    before = matches(client, active_need)
    with db_factory() as db:
        setattr(db.get(CandidateProfile, candidate_id), field, value)
        db.commit()
    after = matches(client, active_need)

    def ranking(page):
        return [
            (item["candidate_id"], item["professional_fit_score"])
            for item in page["items"]
        ]

    assert ranking(after) == ranking(before)


def test_matching_ranks_before_pagination(client, active_need, matching_candidate):
    low = matching_candidate(
        id="00000000-0000-0000-0000-000000000001", normalized_assessment_score=70
    )
    tie_b = matching_candidate(
        id="00000000-0000-0000-0000-000000000003",
        normalized_assessment_score=80,
        years_of_experience=2.001,
    )
    tie_a = matching_candidate(
        id="00000000-0000-0000-0000-000000000002",
        normalized_assessment_score=80,
        years_of_experience=2.001,
    )
    top = matching_candidate(
        id="00000000-0000-0000-0000-000000000004",
        normalized_assessment_score=80,
        years_of_experience=2.002,
    )
    full = matches(client, active_need, limit=100)
    assert [item["candidate_id"] for item in full["items"]] == [top, tie_a, tie_b, low]
    assert round(full["items"][0]["professional_fit_score"], 1) == round(
        full["items"][1]["professional_fit_score"], 1
    )
    first = matches(client, active_need, limit=2)
    second = matches(client, active_need, limit=2, offset=2)
    assert first["items"] == full["items"][:2]
    assert second["items"] == full["items"][2:]
    assert first["total"] == second["total"] == 4
    assert matches(client, active_need, offset=99)["items"] == []


@pytest.mark.parametrize(
    "count,provider_queries,max_queries", [(5, 1, 7), (50, 1, 7), (501, 2, 9)]
)
def test_matching_batches_queries(
    client,
    active_need,
    matching_candidate,
    database,
    count,
    provider_queries,
    max_queries,
):
    for _ in range(count):
        matching_candidate()
    with captured_sql(database) as statements:
        page = matches(client, active_need)
    assert page["total"] == count
    assert len(page["items"]) == 20 if count > 20 else len(page["items"]) == count
    assert len(statements) <= max_queries
    provider_reads = [
        sql
        for sql in statements
        if "candidate_profiles.normalized_assessment_score" in sql
    ]
    assert len(provider_reads) == provider_queries
    assert all(" in (" in sql for sql in provider_reads)
    skill_reads = [sql for sql in statements if "join candidate_skills" in sql]
    assert len(skill_reads) == (2 if count > 500 else 1)


def test_matching_is_read_only(
    client, active_need, matching_candidate, database, db_factory, monkeypatch
):
    candidate_id = matching_candidate()
    before = canonical(db_factory, candidate_id)

    def reject(*args, **kwargs):
        pytest.fail("Matching must not commit, synchronize or finalize assessments")

    monkeypatch.setattr(assessments, "synchronize_verification", reject)
    monkeypatch.setattr(assessments, "finalize", reject)
    monkeypatch.setattr(assessments, "history", reject)
    with captured_sql(database) as statements:
        assert matches(client, active_need)["total"] == 1
    assert canonical(db_factory, candidate_id) == before
    assert all(sql.lstrip().startswith("select") for sql in statements)
    assert all(
        "assessment_attempt" not in sql and "for update" not in sql
        for sql in statements
    )
    with db_factory() as db:
        user = db.get(User, active_need[0])
        candidate = db.get(CandidateProfile, candidate_id)
        profile = employer_needs.employer_profile(db, user)
        candidate.about = "uncommitted-private"
        profile.company_name = "uncommitted-company"
        monkeypatch.setattr(db, "commit", reject)
        with captured_sql(database) as direct_statements:
            page = matching.match_need(
                db,
                user,
                active_need[1],
                ProfileAssessmentProvider(db),
                limit=20,
                offset=0,
            )
        assert page.total == 1
        assert all(sql.lstrip().startswith("select") for sql in direct_statements)
        assert candidate in db.dirty
        assert profile in db.dirty


def test_matching_loads_criteria_without_mutation_lock(
    client, active_need, matching_candidate, database, monkeypatch, skill_ids
):
    matching_candidate()

    def reject(*args, **kwargs):
        pytest.fail("Matching must not use management get_need")

    monkeypatch.setattr(employer_needs, "get_need", reject)
    with captured_sql(database) as statements:
        result = matches(client, active_need)
    assert result["total"] == 1
    reads = [
        sql
        for sql in statements
        if "from employer_needs" in sql or "from employer_need_skills" in sql
    ]
    assert len(reads) == 1
    joined = reads[0]
    for field in (
        "id",
        "employer_id",
        "status",
        "specialization",
        "required_grade",
        "target_experience_years",
    ):
        assert f"employer_needs.{field}" in joined
    assert "left outer join employer_need_skills" in joined
    assert (
        "employer_need_skills.skill_id" in joined
        and "employer_need_skills.kind" in joined
    )
    assert "employer_needs.id =" in joined and "employer_needs.employer_id =" in joined
    assert "for update" not in joined
    assert {s["id"] for s in result["items"][0]["matched_must_have_skills"]} == set(
        skill_ids[:2]
    )


def test_need_criteria_is_immutable(active_need, db_factory, skill_ids):
    with db_factory() as db:
        user = db.get(User, active_need[0])
        criteria = matching.load_need_criteria(db, user, active_need[1])
        assert isinstance(criteria.must_have_skill_ids, frozenset)
        assert isinstance(criteria.nice_to_have_skill_ids, frozenset)
        with pytest.raises(FrozenInstanceError):
            criteria.required_grade = Grade.SENIOR
        candidate = CandidateMatchInput(
            "candidate", Specialization.BACKEND, True, frozenset(skill_ids), 2
        )
        assessment = CandidateAssessment("candidate", Grade.MIDDLE, 80, None)
        before = eligible_candidate(criteria, candidate, assessment)
        need = db.get(EmployerNeed, active_need[1])
        need.required_grade = Grade.SENIOR
        need.target_experience_years = 50
        need.skill_requirements.clear()
        assert criteria.required_grade == Grade.MIDDLE
        assert criteria.target_experience_years == 3
        assert criteria.must_have_skill_ids == frozenset(skill_ids[:2])
        assert criteria.nice_to_have_skill_ids == frozenset(skill_ids[2:])
        assert eligible_candidate(criteria, candidate, assessment) == before


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"limit": "bad"},
        {"limit": "1.5"},
        {"offset": -1},
        {"offset": "bad"},
    ],
)
def test_matching_pagination_validation(client, active_need, params):
    response = client.get(f"{BASE}/{active_need[1]}/matches", params=params)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.headers["Cache-Control"] == "no-store"
