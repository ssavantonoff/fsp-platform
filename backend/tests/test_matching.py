import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from threading import Event

import pytest
from sqlalchemy import event, select, text
from sqlalchemy.exc import IntegrityError

from app.errors import ApiError
from app.models import CandidateProfile, EmployerNeed, Grade, Specialization, User
from app.need_schemas import NeedWrite
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


def test_active_must_have_edit_changes_eligibility(
    client, active_need, matching_candidate, need_data, skill_ids
):
    candidate_id = matching_candidate(skill_ids=skill_ids[:2])
    before = matches(client, active_need)
    assert [item["candidate_id"] for item in before["items"]] == [candidate_id]
    response = client.put(
        f"{BASE}/{active_need[1]}",
        json={
            **need_data,
            "must_have_skill_ids": skill_ids,
            "nice_to_have_skill_ids": [],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "ACTIVE"
    assert matches(client, active_need) == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 0,
    }


def test_active_nice_to_have_edit_changes_score_and_order(
    client, active_need, matching_candidate, need_data, skill_ids
):
    django = matching_candidate(skill_ids=skill_ids[:2])
    postgres = matching_candidate(skill_ids=[skill_ids[0], skill_ids[2]])
    payload = {
        **need_data,
        "must_have_skill_ids": skill_ids[:1],
        "nice_to_have_skill_ids": skill_ids[1:2],
        "target_experience_years": None,
    }
    assert client.put(f"{BASE}/{active_need[1]}", json=payload).status_code == 200
    before = matches(client, active_need)
    assert [item["candidate_id"] for item in before["items"]] == [django, postgres]
    payload["nice_to_have_skill_ids"] = skill_ids[2:]
    response = client.put(f"{BASE}/{active_need[1]}", json=payload)
    assert response.status_code == 200, response.text
    after = matches(client, active_need)
    assert [item["candidate_id"] for item in after["items"]] == [postgres, django]
    assert before["total"] == after["total"] == 2
    for page, optional in ((before, skill_ids[1]), (after, skill_ids[2])):
        assert [i["professional_fit_score"] for i in page["items"]] == pytest.approx(
            [1520 / 17, 1220 / 17]
        )
        for index, item in enumerate(page["items"]):
            assert item["breakdown"]["assessment"]["score"] == pytest.approx(720 / 17)
            assert item["breakdown"]["grade"]["score"] == pytest.approx(500 / 17)
            nice = item["breakdown"]["nice_to_have"]
            assert nice["active"] is True
            assert nice["total"] == 1
            assert nice["matched"] == 1 - index
            assert nice["score"] == pytest.approx(300 / 17 if index == 0 else 0)
            assert nice["max"] == pytest.approx(300 / 17)
            assert [s["id"] for s in item["matched_nice_to_have_skills"]] == (
                [optional] if index == 0 else []
            )


def test_active_grade_edit_changes_eligibility_and_fit(
    client, active_need, matching_candidate, need_data
):
    middle = matching_candidate()
    senior = matching_candidate(verified_grade=Grade.SENIOR)
    payload = {
        **need_data,
        "nice_to_have_skill_ids": [],
        "target_experience_years": None,
    }
    assert client.put(f"{BASE}/{active_need[1]}", json=payload).status_code == 200
    before = matches(client, active_need)
    assert [item["candidate_id"] for item in before["items"]] == [middle, senior]
    assert [i["professional_fit_score"] for i in before["items"]] == pytest.approx(
        [610 / 7, 547.5 / 7]
    )
    response = client.put(
        f"{BASE}/{active_need[1]}", json={**payload, "required_grade": "JUNIOR"}
    )
    assert response.status_code == 200, response.text
    after = matches(client, active_need)
    assert after["total"] == 1
    assert [item["candidate_id"] for item in after["items"]] == [middle]
    item = after["items"][0]
    assert item["professional_fit_score"] == pytest.approx(547.5 / 7)
    assert item["breakdown"]["grade"] == {
        "active": True,
        "max": pytest.approx(250 / 7),
        "score": pytest.approx(187.5 / 7),
        "exact_match": False,
    }
    assert item["breakdown"]["assessment"]["score"] == pytest.approx(360 / 7)
    for key in ("nice_to_have", "experience"):
        assert item["breakdown"][key]["active"] is False
        assert item["breakdown"][key]["max"] == 0


def test_active_experience_edit_changes_score(
    client, active_need, matching_candidate, need_data
):
    experienced = matching_candidate(years_of_experience=2)
    missing = matching_candidate(years_of_experience=None)
    before = {i["candidate_id"]: i for i in matches(client, active_need)["items"]}
    assert before[experienced]["professional_fit_score"] == pytest.approx(86)
    assert before[experienced]["breakdown"]["experience"]["score"] == 10
    assert before[missing]["professional_fit_score"] == 76
    for target, maxima, scores, totals in (
        (4, 15, (7.5, 0), (83.5, 76)),
        (None, 0, (0, 0), (1520 / 17, 1520 / 17)),
        (0, 15, (15, 15), (91, 91)),
    ):
        response = client.put(
            f"{BASE}/{active_need[1]}",
            json={**need_data, "target_experience_years": target},
        )
        assert response.status_code == 200, response.text
        page = matches(client, active_need)
        assert page["total"] == 2
        by_id = {item["candidate_id"]: item for item in page["items"]}
        for candidate_id, contribution, total in zip(
            (experienced, missing), scores, totals, strict=True
        ):
            item = by_id[candidate_id]
            assert item["professional_fit_score"] == pytest.approx(total)
            assert item["breakdown"]["experience"] == {
                "active": target is not None,
                "max": maxima,
                "score": contribution,
            }
            assert item["breakdown"]["assessment"]["max"] == pytest.approx(
                900 / 17 if target is None else 45
            )
            assert item["breakdown"]["grade"]["max"] == pytest.approx(
                500 / 17 if target is None else 25
            )
            assert item["breakdown"]["nice_to_have"]["max"] == pytest.approx(
                300 / 17 if target is None else 15
            )


def persisted_need(db_factory, need_id):
    with db_factory() as db:
        need = db.get(EmployerNeed, need_id)
        return (
            tuple(getattr(need, c.name) for c in EmployerNeed.__table__.columns),
            sorted((link.skill_id, link.kind) for link in need.skill_requirements),
        )


@pytest.mark.parametrize(
    "invalid",
    ["salary_order", "negative_from", "negative_to", "unknown", "overlap", "empty"],
)
def test_failed_active_edit_preserves_matching(
    client, active_need, matching_candidate, need_data, skill_ids, db_factory, invalid
):
    top = matching_candidate()
    lower = matching_candidate(skill_ids=skill_ids[:2], years_of_experience=1)
    before = matches(client, active_need)
    assert [item["candidate_id"] for item in before["items"]] == [top, lower]
    original = persisted_need(db_factory, active_need[1])
    payload = {
        **need_data,
        "position_title": "Rejected title",
        "description": "Rejected description",
        "additional_requirements": "Rejected requirements",
        "required_grade": "JUNIOR",
        "target_experience_years": 10,
        "must_have_skill_ids": skill_ids[2:],
        "nice_to_have_skill_ids": skill_ids[:1],
    }
    if invalid == "salary_order":
        payload["salary_from"] = "300000"
    elif invalid == "negative_from":
        payload["salary_from"] = "-1"
    elif invalid == "negative_to":
        payload["salary_to"] = "-1"
    elif invalid == "unknown":
        payload["must_have_skill_ids"] = ["unknown"]
    elif invalid == "overlap":
        payload["nice_to_have_skill_ids"] = skill_ids[2:]
    else:
        payload["must_have_skill_ids"] = []
    response = client.put(f"{BASE}/{active_need[1]}", json=payload)
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == (
        "unknown_skill" if invalid == "unknown" else "validation_error"
    )
    assert persisted_need(db_factory, active_need[1]) == original
    assert matches(client, active_need) == before


CONCURRENT_TIMEOUT = 15


def worker_result(future, stage):
    try:
        return future.result(CONCURRENT_TIMEOUT)
    except TimeoutError:
        pytest.fail(f"Timed out after {CONCURRENT_TIMEOUT}s waiting for {stage}")


@contextmanager
def postgres_session(database, db_factory):
    # Pin the physical connection across commits, without an external transaction.
    with database.connect() as connection, db_factory(bind=connection) as db:
        # Closing a detached connection closes it physically: later workers cannot
        # accidentally reuse its PID and masquerade as an independent invocation.
        connection.detach()
        db.execute(text("SET LOCAL lock_timeout = '10s'"))
        db.execute(text("SET LOCAL statement_timeout = '12s'"))
        pid = db.scalar(text("SELECT pg_backend_pid()"))
        yield db, pid


def install_criteria_checkpoint(monkeypatch):
    original = matching.load_need_criteria

    def capture(db, user, need_id):
        criteria = original(db, user, need_id)
        db.info["captured_criteria"] = criteria
        if "captured" in db.info and db.info["pause_stage"] == "criteria":
            db.info["captured"].set()
            assert db.info["release"].wait(CONCURRENT_TIMEOUT), (
                "Matching criteria captured but controller did not release the reader"
            )
        return criteria

    monkeypatch.setattr(matching, "load_need_criteria", capture)


def matching_worker(
    database,
    db_factory,
    active_need,
    captured=None,
    release=None,
    pause_stage="criteria",
):
    with postgres_session(database, db_factory) as (db, pid):
        if captured is not None:
            db.info.update(captured=captured, release=release, pause_stage=pause_stage)
        user = db.get(User, active_need[0])
        provider = ProfileAssessmentProvider(db)
        if captured is not None and pause_stage == "provider":
            original_get_assessments = provider.get_assessments

            def pause_provider(candidate_ids):
                captured.set()
                assert release.wait(CONCURRENT_TIMEOUT), (
                    "Provider phase reached but controller did not release reader A"
                )
                return original_get_assessments(candidate_ids)

            provider.get_assessments = pause_provider
        page = matching.match_need(
            db, user, active_need[1], provider, limit=20, offset=0
        )
        return pid, db.info["captured_criteria"], page.model_dump(mode="json")


def concurrent_update_payload(need_data, skill_ids):
    return {
        **need_data,
        "position_title": "Committed concurrent edit",
        "required_grade": "JUNIOR",
        "target_experience_years": 4,
        "must_have_skill_ids": [skill_ids[0], skill_ids[2]],
        "nice_to_have_skill_ids": skill_ids[1:2],
    }


def test_matching_snapshot_survives_concurrent_active_update(
    database,
    db_factory,
    active_need,
    matching_candidate,
    skill_ids,
    need_data,
    monkeypatch,
    client,
):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL independent concurrent connections")
    middle = matching_candidate()
    senior = matching_candidate(verified_grade=Grade.SENIOR)
    no_postgres = matching_candidate(skill_ids=skill_ids[:2])
    old_page = matches(client, active_need)
    assert [i["candidate_id"] for i in old_page["items"]] == [
        middle,
        senior,
        no_postgres,
    ]
    install_criteria_checkpoint(monkeypatch)
    captured, release = Event(), Event()
    with ThreadPoolExecutor(max_workers=2) as workers:
        reader = workers.submit(
            matching_worker,
            database,
            db_factory,
            active_need,
            captured,
            release,
            "provider",
        )
        try:
            assert captured.wait(CONCURRENT_TIMEOUT), (
                "Reader A did not capture criteria"
            )

            def update():
                with postgres_session(database, db_factory) as (db, pid):
                    user = db.get(User, active_need[0])
                    need = employer_needs.update_need(
                        db,
                        user,
                        active_need[1],
                        NeedWrite(**concurrent_update_payload(need_data, skill_ids)),
                    )
                    return pid, need.position_title

            writer_pid, title = worker_result(
                workers.submit(update), "ACTIVE writer commit while reader A is paused"
            )
            assert title == "Committed concurrent edit"
            assert not release.is_set() and not reader.done(), (
                "Update must commit while A is still paused with old criteria"
            )
            with db_factory() as db:
                assert db.get(EmployerNeed, active_need[1]).position_title == title
            release.set()
            reader_pid, old, result = worker_result(
                reader, "reader A old-snapshot result"
            )
        finally:
            release.set()
    assert reader_pid != writer_pid
    assert old.required_grade == Grade.MIDDLE
    assert old.target_experience_years == 3
    assert old.must_have_skill_ids == frozenset(skill_ids[:2])
    assert old.nice_to_have_skill_ids == frozenset(skill_ids[2:])
    assert result == old_page
    fresh_pid, fresh, page = matching_worker(database, db_factory, active_need)
    assert fresh_pid != reader_pid
    assert fresh.required_grade == Grade.JUNIOR
    assert fresh.target_experience_years == 4
    assert fresh.must_have_skill_ids == frozenset([skill_ids[0], skill_ids[2]])
    assert fresh.nice_to_have_skill_ids == frozenset(skill_ids[1:2])
    assert [i["candidate_id"] for i in page["items"]] == [middle]
    assert page["total"] == 1
    assert page["items"][0]["professional_fit_score"] == pytest.approx(77.25)
    breakdown = page["items"][0]["breakdown"]
    assert [
        breakdown[k]["score"]
        for k in ("assessment", "grade", "nice_to_have", "experience")
    ] == [36, 18.75, 15, 7.5]
    assert [s["id"] for s in page["items"][0]["matched_nice_to_have_skills"]] == (
        skill_ids[1:2]
    )


def test_concurrent_matching_reads_do_not_serialize(
    database, db_factory, active_need, matching_candidate, monkeypatch, client
):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL independent concurrent connections")
    matching_candidate()
    expected = matches(client, active_need)
    install_criteria_checkpoint(monkeypatch)

    def reject(*args, **kwargs):
        pytest.fail("Concurrent matching must never use mutation get_need/FOR UPDATE")

    def reject_lock(connection, cursor, statement, parameters, context, executemany):
        if "for update" in statement.lower():
            reject()

    monkeypatch.setattr(employer_needs, "get_need", reject)
    captured_a, captured_b, release = Event(), Event(), Event()
    event.listen(database, "before_cursor_execute", reject_lock)
    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            a = workers.submit(
                matching_worker, database, db_factory, active_need, captured_a, release
            )
            try:
                assert captured_a.wait(CONCURRENT_TIMEOUT), "Reader A capture timed out"
                b = workers.submit(
                    matching_worker,
                    database,
                    db_factory,
                    active_need,
                    captured_b,
                    release,
                )
                assert captured_b.wait(CONCURRENT_TIMEOUT), (
                    "Reader B could not capture criteria while reader A was open"
                )
                assert not a.done() and not b.done() and not release.is_set()
                release.set()
                pid_a, criteria_a, page_a = worker_result(
                    a, "concurrent reader A result"
                )
                pid_b, criteria_b, page_b = worker_result(
                    b, "concurrent reader B result"
                )
            finally:
                release.set()
    finally:
        event.remove(database, "before_cursor_execute", reject_lock)
    assert pid_a != pid_b
    assert criteria_a == criteria_b
    assert page_a == page_b == expected


def test_failed_active_transaction_keeps_committed_snapshot(
    database,
    db_factory,
    active_need,
    matching_candidate,
    need_data,
    skill_ids,
    monkeypatch,
    client,
):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL independent concurrent connections")
    matching_candidate()
    matching_candidate(skill_ids=skill_ids[:2])
    expected = matches(client, active_need)
    original = persisted_need(db_factory, active_need[1])
    install_criteria_checkpoint(monkeypatch)
    captured, release, rollback_done, writer_release = (
        Event(),
        Event(),
        Event(),
        Event(),
    )
    writer_state = {}
    with ThreadPoolExecutor(max_workers=3) as workers:
        reader = workers.submit(
            matching_worker, database, db_factory, active_need, captured, release
        )
        try:
            assert captured.wait(CONCURRENT_TIMEOUT), "Reader A capture timed out"

            def failed_update():
                with postgres_session(database, db_factory) as (db, pid):
                    user = db.get(User, active_need[0])
                    attempted = []

                    def fail_commit():
                        db.flush()
                        need = db.get(EmployerNeed, active_need[1])
                        attempted.append(
                            (
                                need.position_title,
                                need.required_grade,
                                need.target_experience_years,
                                sorted(
                                    (link.skill_id, link.kind)
                                    for link in (need.skill_requirements)
                                ),
                            )
                        )
                        raise IntegrityError(
                            "injected persistence failure", {}, Exception("constraint")
                        )

                    # Same deterministic post-flush failure mechanism as Task 2.
                    monkeypatch.setattr(db, "commit", fail_commit)
                    with pytest.raises(ApiError) as error:
                        employer_needs.update_need(
                            db,
                            user,
                            active_need[1],
                            NeedWrite(
                                **concurrent_update_payload(need_data, skill_ids)
                            ),
                        )
                    assert (error.value.status, error.value.code) == (
                        409,
                        "need_conflict",
                    )
                    assert not db.in_transaction(), "Service did not roll back"
                    assert len(attempted) == 1
                    assert attempted[0][:3] == (
                        "Committed concurrent edit",
                        Grade.JUNIOR,
                        4,
                    )
                    assert dict(attempted[0][3]) == {
                        skill_ids[0]: "MUST_HAVE",
                        skill_ids[2]: "MUST_HAVE",
                        skill_ids[1]: "NICE_TO_HAVE",
                    }
                    writer_state["pid"] = pid
                    rollback_done.set()
                    assert writer_release.wait(CONCURRENT_TIMEOUT), (
                        "Rolled-back writer was not released by controller"
                    )
                    return pid

            failed_writer = workers.submit(failed_update)
            assert rollback_done.wait(CONCURRENT_TIMEOUT), (
                "Writer did not complete the real post-flush rollback"
            )
            assert not reader.done() and not release.is_set()
            fresh_pid, fresh_criteria, fresh_page = worker_result(
                workers.submit(matching_worker, database, db_factory, active_need),
                "fresh reader B2 result after rollback",
            )
            assert fresh_page == expected
            assert persisted_need(db_factory, active_need[1]) == original
            release.set()
            reader_pid, old_criteria, old_page = worker_result(
                reader, "reader A unchanged result after rollback"
            )
            writer_release.set()
            writer_pid = worker_result(failed_writer, "rolled-back writer cleanup")
            assert writer_pid == writer_state["pid"]
        finally:
            release.set()
            writer_release.set()
    assert len({reader_pid, writer_pid, fresh_pid}) == 3
    assert fresh_criteria == old_criteria
    assert old_criteria.required_grade == Grade.MIDDLE
    assert old_criteria.target_experience_years == 3
    assert old_criteria.must_have_skill_ids == frozenset(skill_ids[:2])
    assert old_criteria.nice_to_have_skill_ids == frozenset(skill_ids[2:])
    assert old_page == expected
