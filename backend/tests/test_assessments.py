from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier

import pytest
from alembic.config import Config
from conftest import ORIGIN
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.models import (
    AssessmentAttempt,
    AssessmentQuestion,
    CandidateProfile,
    Grade,
    User,
    utcnow,
)
from app.question_bank import load_bank
from app.seed import seed
from app.services import assessments

BASE = "/candidate/assessments"


@pytest.fixture
def ready(client, account, candidate_data, db_factory):
    user = account()
    profile = client.post("/candidate/profile", json=candidate_data).json()
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        db.get(User, user["id"]).email_verified = True
        db.commit()
    return profile


def start(client, grade="MIDDLE"):
    response = client.post(BASE, json={"target_grade": grade})
    assert response.status_code == 201, response.text
    return response.json()


def answer_counts(db_factory, attempt, counts=(4, 4, 4, 4, 4)):
    with db_factory() as db:
        row = db.get(AssessmentAttempt, attempt["id"])
        remaining = dict(
            zip(assessments.COMPETENCIES[row.specialization], counts, strict=True)
        )
        for item in row.questions:
            if remaining[item.question.competency] > 0:
                remaining[item.question.competency] -= 1
                item.selected_option_id = next(
                    o.id for o in item.question.options if o.is_correct
                )
                item.answered_at = utcnow()
        db.commit()


def finish(client, attempt):
    response = client.post(f"{BASE}/{attempt['id']}/submit")
    assert response.status_code == 200, response.text
    return response.json()


def expire(db_factory, attempt, now=None):
    now = now or utcnow()
    with db_factory() as db:
        row = db.get(AssessmentAttempt, attempt["id"])
        row.started_at = now - timedelta(minutes=31)
        row.expires_at = now - timedelta(minutes=1)
        db.commit()


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/availability", None),
        ("get", "/current", None),
        ("get", "/history", None),
        ("get", "/foreign", None),
        ("post", "", {"target_grade": "MIDDLE"}),
        ("post", "/foreign/submit", None),
        ("put", "/foreign/answers/question", {"selected_option_id": "option"}),
    ],
)
def test_authorization(client, account, method, path, body):
    assert (
        getattr(client, method)(
            BASE + path, **({"json": body} if body else {})
        ).status_code
        == 401
    )
    account(role="EMPLOYER")
    assert (
        getattr(client, method)(
            BASE + path, **({"json": body} if body else {})
        ).status_code
        == 403
    )


def test_prerequisites_and_missing_profile(client, account, candidate_data, db_factory):
    user = account()
    assert (
        client.post(BASE, json={"target_grade": "JUNIOR"}).json()["error"]["code"]
        == "profile_not_found"
    )
    client.post("/candidate/profile", json=candidate_data)
    assert (
        client.post(BASE, json={"target_grade": "JUNIOR"}).json()["error"]["code"]
        == "email_not_verified"
    )
    with db_factory() as db:
        db.get(User, user["id"]).email_verified = True
        db.commit()
    client.put(
        "/candidate/profile", json={**candidate_data, "personal_data_consent": False}
    )
    assert (
        client.post(BASE, json={"target_grade": "JUNIOR"}).json()["error"]["code"]
        == "consent_required"
    )


@pytest.mark.parametrize("specialization", ["FRONTEND", "DATA_ML"])
def test_unavailable_bank(client, ready, candidate_data, specialization):
    client.put(
        "/candidate/profile", json={**candidate_data, "specialization": specialization}
    )
    assert all(
        g["reason"] == "UNAVAILABLE"
        for g in client.get(BASE + "/availability").json()["grades"]
    )
    assert (
        client.post(BASE, json={"target_grade": "JUNIOR"}).json()["error"]["code"]
        == "assessment_unavailable"
    )


@pytest.mark.parametrize(
    "extra",
    [
        {"specialization": "FRONTEND"},
        {"candidate_id": "x"},
        {"score": 100},
        {"timer": 1},
        {"question_ids": []},
        {"verified_grade": "SENIOR"},
    ],
)
def test_start_forbids_client_canonical_data(client, ready, extra):
    assert (
        client.post(BASE, json={"target_grade": "MIDDLE", **extra}).status_code == 422
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("verified_grade", "SENIOR"),
        ("normalized_assessment_score", 100),
        ("assessment_verified_at", "2026-01-01T00:00:00Z"),
    ],
)
def test_profile_forbids_verification(client, ready, candidate_data, field, value):
    assert (
        client.put(
            "/candidate/profile", json={**candidate_data, field: value}
        ).status_code
        == 422
    )


@pytest.mark.parametrize("grade", ["JUNIOR", "MIDDLE", "SENIOR"])
def test_blueprint_stability_and_no_answer_leak(client, ready, db_factory, grade):
    attempt = start(client, grade)
    assert len(attempt["questions"]) == 20
    assert len({q["question_id"] for q in attempt["questions"]}) == 20
    assert [q["position"] for q in attempt["questions"]] == list(range(1, 21))
    for competency in assessments.COMPETENCIES["BACKEND"]:
        assert Counter(
            q["difficulty"]
            for q in attempt["questions"]
            if q["competency"] == competency
        ) == {"BASIC": 1, "APPLIED": 2, "ADVANCED": 1}
    assert client.get(BASE + "/current").json()["questions"] == attempt["questions"]
    assert (
        client.get(f"{BASE}/{attempt['id']}").json()["questions"]
        == attempt["questions"]
    )
    forbidden = {"is_correct", "correct_option_id", "answer", "solution", "explanation"}

    def check(data):
        if isinstance(data, dict):
            assert not forbidden.intersection(data)
            for value in data.values():
                check(value)
        elif isinstance(data, list):
            for value in data:
                check(value)

    check(attempt)
    check(finish(client, attempt))
    check(client.get(BASE + "/history").json())


def test_bank_integrity_and_immutable_seed(db_factory):
    assert len(load_bank()) == 120
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        questions = list(db.scalars(select(AssessmentQuestion)))
        assert len(questions) == 120
        assert len({q.code for q in questions}) == 120
        assert all(
            len(q.options) == 4 and sum(o.is_correct for o in q.options) == 1
            for q in questions
        )
        for grade in Grade:
            for competency in assessments.COMPETENCIES["BACKEND"]:
                assert Counter(
                    q.difficulty
                    for q in questions
                    if q.grade == grade and q.competency == competency
                ) == {"BASIC": 2, "APPLIED": 4, "ADVANCED": 2}
        questions[0].is_active = False
        db.commit()
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        question = db.scalar(
            select(AssessmentQuestion).where(AssessmentQuestion.is_active.is_(False))
        )
        question.prompt = "Changed content"
        db.commit()
    with (
        db_factory() as db,
        pytest.raises(ValueError, match="Immutable question changed"),
    ):
        seed(db)


def test_active_attempt_and_profile_edits(client, ready, candidate_data):
    attempt = start(client)
    assert (
        client.post(BASE, json={"target_grade": "SENIOR"}).json()["error"]["code"]
        == "assessment_in_progress"
    )
    assert (
        client.put(
            "/candidate/profile", json={**candidate_data, "specialization": "FRONTEND"}
        ).json()["error"]["code"]
        == "assessment_in_progress"
    )
    assert (
        client.put(
            "/candidate/profile",
            json={
                **candidate_data,
                "declared_grade": "JUNIOR",
                "personal_data_consent": False,
            },
        ).status_code
        == 200
    )
    question = attempt["questions"][0]
    assert (
        client.put(
            f"{BASE}/{attempt['id']}/answers/{question['attempt_question_id']}",
            json={"selected_option_id": question["options"][0]["id"]},
        ).status_code
        == 200
    )
    assert finish(client, attempt)["completion_reason"] == "SUBMITTED"
    assert client.get(BASE + "/history").status_code == 200


def test_answers_validation_change_and_finalized(client, ready):
    attempt = start(client)
    q, other = attempt["questions"][:2]
    path = f"{BASE}/{attempt['id']}/answers/{q['attempt_question_id']}"
    assert (
        client.put(path, json={"selected_option_id": other["options"][0]["id"]}).json()[
            "error"
        ]["code"]
        == "option_not_in_question"
    )
    assert (
        client.put(
            f"{BASE}/{attempt['id']}/answers/foreign",
            json={"selected_option_id": q["options"][0]["id"]},
        ).json()["error"]["code"]
        == "question_not_in_attempt"
    )
    for option in q["options"][:2]:
        response = client.put(path, json={"selected_option_id": option["id"]})
        assert response.status_code == 200
        assert response.json()["questions"][0]["selected_option_id"] == option["id"]
    assert (
        client.get(f"{BASE}/{attempt['id']}").json()["questions"][0][
            "selected_option_id"
        ]
        == q["options"][1]["id"]
    )
    finish(client, attempt)
    assert (
        client.put(path, json={"selected_option_id": q["options"][0]["id"]}).json()[
            "error"
        ]["code"]
        == "assessment_finished"
    )


def test_foreign_attempt_privacy(client, ready, account, candidate_data):
    attempt = start(client)
    account(email="other@example.com")
    client.post("/candidate/profile", json=candidate_data)
    assert client.get(f"{BASE}/{attempt['id']}").status_code == 404
    assert client.post(f"{BASE}/{attempt['id']}/submit").status_code == 404
    assert (
        client.put(
            f"{BASE}/{attempt['id']}/answers/{attempt['questions'][0]['attempt_question_id']}",
            json={"selected_option_id": "foreign"},
        ).status_code
        == 404
    )
    assert client.get(BASE + "/history").json() == []


@pytest.mark.parametrize(
    "counts,score,status,expected_scores",
    [
        pytest.param(
            (3, 3, 3, 3, 2),
            70,
            "PASSED",
            {
                "PROGRAMMING": 75,
                "HTTP_API": 75,
                "DATABASES": 75,
                "ARCHITECTURE": 75,
                "TESTING_SECURITY_DEBUGGING": 50,
            },
            id="G1_boundary_pass",
        ),
        pytest.param(
            (4, 4, 1, 4, 3),
            80,
            "FAILED",
            {
                "PROGRAMMING": 100,
                "HTTP_API": 100,
                "DATABASES": 25,
                "ARCHITECTURE": 100,
                "TESTING_SECURITY_DEBUGGING": 75,
            },
            id="G2_weak_competency",
        ),
        pytest.param(
            (3, 3, 3, 2, 2),
            65,
            "FAILED",
            {
                "PROGRAMMING": 75,
                "HTTP_API": 75,
                "DATABASES": 75,
                "ARCHITECTURE": 50,
                "TESTING_SECURITY_DEBUGGING": 50,
            },
            id="G3_overall_below_threshold",
        ),
        pytest.param(
            (4, 4, 4, 4, 4),
            100,
            "PASSED",
            {
                "PROGRAMMING": 100,
                "HTTP_API": 100,
                "DATABASES": 100,
                "ARCHITECTURE": 100,
                "TESTING_SECURITY_DEBUGGING": 100,
            },
            id="G4_full_score",
        ),
        pytest.param(
            (0, 0, 0, 0, 0),
            0,
            "FAILED",
            {
                "PROGRAMMING": 0,
                "HTTP_API": 0,
                "DATABASES": 0,
                "ARCHITECTURE": 0,
                "TESTING_SECURITY_DEBUGGING": 0,
            },
            id="G5_zero_score",
        ),
    ],
)
def test_scoring_and_initial_verification(
    client, ready, db_factory, counts, score, status, expected_scores
):
    attempt = start(client)
    answer_counts(db_factory, attempt, counts)
    result = finish(client, attempt)
    assert result["normalized_assessment_score"] == score
    assert result["status"] == status
    assert result["competency_scores"] == expected_scores
    assert set(result["competency_scores"]) == {
        "PROGRAMMING",
        "HTTP_API",
        "DATABASES",
        "ARCHITECTURE",
        "TESTING_SECURITY_DEBUGGING",
    }
    assert set(result["competency_scores"].values()) <= {0, 25, 50, 75, 100}
    profile = client.get("/candidate/profile").json()
    assert profile["verified_grade"] == ("MIDDLE" if status == "PASSED" else None)
    assert profile["normalized_assessment_score"] == (
        score if status == "PASSED" else None
    )
    assert bool(profile["assessment_verified_at"]) == (status == "PASSED")


@pytest.mark.parametrize(
    "scenario,unanswered",
    [
        ("all_unanswered", 20),
        ("all_wrong", 0),
        ("mixed_wrong_and_unanswered", 18),
        ("correct_to_wrong", 19),
    ],
)
def test_wrong_and_unanswered_score_zero(
    client, ready, db_factory, scenario, unanswered
):
    attempt = start(client)
    questions = attempt["questions"]
    if scenario == "all_unanswered":
        questions = []
    elif scenario == "mixed_wrong_and_unanswered":
        questions = questions[:2]
    elif scenario == "correct_to_wrong":
        questions = questions[:1]

    with db_factory() as db:
        for item in questions:
            source = db.get(AssessmentQuestion, item["question_id"])
            wrong = next(
                option.id for option in source.options if not option.is_correct
            )
            path = f"{BASE}/{attempt['id']}/answers/{item['attempt_question_id']}"
            if scenario == "correct_to_wrong":
                correct = next(
                    option.id for option in source.options if option.is_correct
                )
                response = client.put(path, json={"selected_option_id": correct})
                assert response.status_code == 200
                saved = next(
                    q
                    for q in response.json()["questions"]
                    if q["attempt_question_id"] == item["attempt_question_id"]
                )
                assert saved["selected_option_id"] == correct
            response = client.put(path, json={"selected_option_id": wrong})
            assert response.status_code == 200
            saved = next(
                q
                for q in response.json()["questions"]
                if q["attempt_question_id"] == item["attempt_question_id"]
            )
            assert saved["selected_option_id"] == wrong

    persisted = client.get(f"{BASE}/{attempt['id']}").json()
    assert (
        sum(q["selected_option_id"] is None for q in persisted["questions"])
        == unanswered
    )
    result = finish(client, attempt)
    assert result["normalized_assessment_score"] == 0
    assert result["status"] == "FAILED"
    assert result["competency_scores"] == {
        "PROGRAMMING": 0,
        "HTTP_API": 0,
        "DATABASES": 0,
        "ARCHITECTURE": 0,
        "TESTING_SECURITY_DEBUGGING": 0,
    }


@pytest.mark.parametrize("declared_grade", ["JUNIOR", "MIDDLE", "SENIOR"])
def test_declared_grade_does_not_affect_result(
    client, ready, candidate_data, db_factory, declared_grade
):
    response = client.put(
        "/candidate/profile", json={**candidate_data, "declared_grade": declared_grade}
    )
    assert response.status_code == 200
    assert response.json()["declared_grade"] == declared_grade
    assert response.json()["specialization"] == "BACKEND"
    attempt = start(client, "MIDDLE")
    assert attempt["target_grade"] == "MIDDLE"
    assert attempt["specialization"] == "BACKEND"
    answer_counts(db_factory, attempt, (3, 3, 3, 3, 2))
    result = finish(client, attempt)
    assert result["target_grade"] == "MIDDLE"
    assert result["specialization"] == "BACKEND"
    assert result["normalized_assessment_score"] == 70
    assert result["status"] == "PASSED"
    assert result["competency_scores"] == {
        "PROGRAMMING": 75,
        "HTTP_API": 75,
        "DATABASES": 75,
        "ARCHITECTURE": 75,
        "TESTING_SECURITY_DEBUGGING": 50,
    }
    assert client.get("/candidate/profile").json()["declared_grade"] == declared_grade


@pytest.mark.parametrize(
    "trigger",
    ["get", "current", "availability", "history", "answer", "submit", "start"],
)
@pytest.mark.parametrize("passed", [True, False])
def test_lazy_timeout_and_cooldown(client, ready, db_factory, trigger, passed):
    attempt = start(client)
    if passed:
        answer_counts(db_factory, attempt)
    expire(db_factory, attempt)
    if trigger == "get":
        client.get(f"{BASE}/{attempt['id']}")
    elif trigger == "current":
        assert client.get(BASE + "/current").status_code == 404
    elif trigger in ("availability", "history"):
        client.get(BASE + "/" + trigger)
    elif trigger == "submit":
        finish(client, attempt)
    elif trigger == "start":
        assert (
            client.post(BASE, json={"target_grade": "MIDDLE"}).json()["error"]["code"]
            == "assessment_cooldown"
        )
    else:
        q = attempt["questions"][0]
        assert (
            client.put(
                f"{BASE}/{attempt['id']}/answers/{q['attempt_question_id']}",
                json={"selected_option_id": q["options"][0]["id"]},
            ).json()["error"]["code"]
            == "assessment_finished"
        )
    result = client.get(f"{BASE}/{attempt['id']}").json()
    assert result["status"] == ("PASSED" if passed else "FAILED")
    assert result["completion_reason"] == "TIMEOUT"
    assert result["normalized_assessment_score"] == (100 if passed else 0)
    assert result["finished_at"] == result["expires_at"]
    assert result["questions"] == []


@pytest.mark.parametrize("passed,days", [(True, 90), (False, 7)])
def test_cooldown_boundaries_and_independent_grade(
    client, ready, db_factory, monkeypatch, passed, days
):
    attempt = start(client)
    if passed:
        answer_counts(db_factory, attempt)
    result = finish(client, attempt)
    from datetime import datetime

    finished = assessments.aware(datetime.fromisoformat(result["finished_at"]))
    monkeypatch.setattr(
        assessments, "utcnow", lambda: finished + timedelta(days=days, microseconds=-1)
    )
    available = client.get(BASE + "/availability").json()["grades"]
    assert available[1]["reason"] == "COOLDOWN"
    assert available[2]["available"]
    monkeypatch.setattr(assessments, "utcnow", lambda: finished + timedelta(days=days))
    assert client.get(BASE + "/availability").json()["grades"][1]["available"]
    start(client)


def test_failed_higher_grade_preserves_current_qualification(
    client, ready, db_factory, monkeypatch
):
    now = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)
    monkeypatch.setattr(assessments, "utcnow", lambda: now)
    middle = start(client, "MIDDLE")
    answer_counts(db_factory, middle, (4, 3, 3, 3, 3))
    t1 = now = datetime(2026, 10, 7, 9, 10, tzinfo=UTC)
    middle_result = finish(client, middle)
    assert middle_result["status"] == "PASSED"
    assert middle_result["normalized_assessment_score"] == 80
    assert middle_result["competency_scores"] == {
        "PROGRAMMING": 100,
        "HTTP_API": 75,
        "DATABASES": 75,
        "ARCHITECTURE": 75,
        "TESTING_SECURITY_DEBUGGING": 75,
    }
    expected = {
        "specialization": "BACKEND",
        "verified_grade": "MIDDLE",
        "normalized_assessment_score": 80,
        "assessment_verified_at": "2026-10-07T09:10:00Z",
    }
    assert {key: middle_result["verification"][key] for key in expected} == expected
    now = datetime(2026, 10, 7, 9, 20, tzinfo=UTC)
    senior = start(client, "SENIOR")
    answer_counts(db_factory, senior, (3, 3, 3, 2, 2))
    now = datetime(2026, 10, 7, 9, 25, tzinfo=UTC)
    senior_result = finish(client, senior)
    senior_scores = {
        "PROGRAMMING": 75,
        "HTTP_API": 75,
        "DATABASES": 75,
        "ARCHITECTURE": 50,
        "TESTING_SECURITY_DEBUGGING": 50,
    }
    assert senior_result["specialization"] == "BACKEND"
    assert senior_result["target_grade"] == "SENIOR"
    assert senior_result["status"] == "FAILED"
    assert senior_result["normalized_assessment_score"] == 65
    assert senior_result["competency_scores"] == senior_scores
    assert senior_result["finished_at"] == "2026-10-07T09:25:00Z"
    assert senior_result["completion_reason"] == "SUBMITTED"
    detail = client.get(f"{BASE}/{senior['id']}").json()
    snapshots = {
        "submit": senior_result["verification"],
        "profile": client.get("/candidate/profile").json(),
        "availability": client.get(BASE + "/availability").json()["verification"],
        "detail": detail["verification"],
        "repeated_submit": finish(client, senior)["verification"],
    }
    for boundary, profile in snapshots.items():
        assert {key: profile[key] for key in expected} == expected, boundary
    assert detail["normalized_assessment_score"] == 65
    assert detail["finished_at"] == "2026-10-07T09:25:00Z"
    assert detail["questions"] == []
    with db_factory() as db:
        profile = db.get(CandidateProfile, ready["id"])
        assert (
            profile.specialization,
            profile.verified_grade,
            profile.normalized_assessment_score,
            assessments.aware(profile.assessment_verified_at),
        ) == ("BACKEND", "MIDDLE", 80, t1)
    history = client.get(BASE + "/history").json()
    assert len(history) == 2
    assert all("verification" not in item for item in history)
    by_id = {item["id"]: item for item in history}
    assert by_id[middle["id"]]["status"] == "PASSED"
    assert by_id[middle["id"]]["normalized_assessment_score"] == 80
    assert by_id[middle["id"]]["finished_at"] == "2026-10-07T09:10:00Z"
    assert by_id[senior["id"]]["target_grade"] == "SENIOR"
    assert by_id[senior["id"]]["status"] == "FAILED"
    assert by_id[senior["id"]]["normalized_assessment_score"] == 65
    assert by_id[senior["id"]]["competency_scores"] == senior_scores
    assert by_id[senior["id"]]["finished_at"] == "2026-10-07T09:25:00Z"
    assert by_id[senior["id"]]["completion_reason"] == "SUBMITTED"


def test_grade_upgrade_fail_preservation_same_grade_and_specialization(
    client, ready, db_factory, candidate_data, monkeypatch
):
    now = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)
    monkeypatch.setattr(assessments, "utcnow", lambda: now)
    middle = start(client)
    answer_counts(db_factory, middle)
    now = datetime(2026, 10, 7, 9, 10, tzinfo=UTC)
    first = finish(client, middle)["verification"]
    assert (
        client.post(BASE, json={"target_grade": "JUNIOR"}).json()["error"]["code"]
        == "assessment_grade_not_allowed"
    )
    now = datetime(2026, 10, 7, 9, 20, tzinfo=UTC)
    senior = start(client, "SENIOR")
    now = datetime(2026, 10, 7, 9, 25, tzinfo=UTC)
    assert finish(client, senior)["verification"]["normalized_assessment_score"] == 100
    # Same grade FAIL also preserves the canonical result.
    fields = (
        "specialization",
        "verified_grade",
        "normalized_assessment_score",
        "assessment_verified_at",
    )
    before_failed = client.get("/candidate/profile").json()
    canonical_before = {key: before_failed[key] for key in fields}
    now = datetime(2026, 10, 7, 9, 0, tzinfo=UTC) + timedelta(days=91)
    failed = start(client)
    now += timedelta(minutes=5)
    after_failed = finish(client, failed)["verification"]
    assert {key: after_failed[key] for key in fields} == canonical_before
    now = datetime(2026, 10, 7, 9, 0, tzinfo=UTC) + timedelta(days=99)
    retake = start(client)
    answer_counts(db_factory, retake, (3, 3, 3, 3, 2))
    now += timedelta(minutes=10)
    retake_result = finish(client, retake)
    assert retake_result["status"] == "PASSED"
    latest = retake_result["verification"]
    assert {key: latest[key] for key in fields} == {
        "specialization": "BACKEND",
        "verified_grade": "MIDDLE",
        "normalized_assessment_score": 70,
        "assessment_verified_at": "2027-01-14T09:10:00Z",
    }
    assert latest["assessment_verified_at"] != first["assessment_verified_at"]
    # Switch clears all canonical fields and returning restores latest highest PASS.
    switched = client.put(
        "/candidate/profile", json={**candidate_data, "specialization": "FRONTEND"}
    ).json()
    assert [
        switched[k]
        for k in (
            "verified_grade",
            "normalized_assessment_score",
            "assessment_verified_at",
        )
    ] == [None, None, None]
    restored = client.put("/candidate/profile", json=candidate_data).json()
    assert {key: restored[key] for key in fields} == {
        key: latest[key] for key in fields
    }
    now += timedelta(minutes=10)
    higher = start(client, "SENIOR")
    answer_counts(db_factory, higher)
    now += timedelta(minutes=5)
    assert finish(client, higher)["verification"]["verified_grade"] == "SENIOR"
    for grade in ("JUNIOR", "MIDDLE"):
        assert (
            client.post(BASE, json={"target_grade": grade}).json()["error"]["code"]
            == "assessment_grade_not_allowed"
        )
    history = client.get(BASE + "/history").json()
    assert len(history) == 5
    assert history[0]["id"] == higher["id"]


def test_submit_idempotent_and_atomic_rollback(client, ready, db_factory, monkeypatch):
    attempt = start(client)
    answer_counts(db_factory, attempt)
    original = assessments.synchronize_verification

    def fail(db, profile):
        original(db, profile)
        db.flush()
        raise RuntimeError("Injected transaction failure")

    monkeypatch.setattr(assessments, "synchronize_verification", fail)
    with pytest.raises(RuntimeError):
        finish(client, attempt)
    with db_factory() as db:
        assert db.get(AssessmentAttempt, attempt["id"]).status == "IN_PROGRESS"
        assert db.get(CandidateProfile, ready["id"]).verified_grade is None
    monkeypatch.setattr(assessments, "synchronize_verification", original)
    first = finish(client, attempt)
    second = finish(client, attempt)
    assert {k: v for k, v in first.items() if k != "server_now"} == {
        k: v for k, v in second.items() if k != "server_now"
    }


def test_database_verification_consistency_and_single_active(client, ready, db_factory):
    attempt = start(client)
    with db_factory() as db, pytest.raises(IntegrityError):
        profile = db.get(CandidateProfile, ready["id"])
        profile.verified_grade = Grade.SENIOR
        db.commit()
    with db_factory() as db, pytest.raises(IntegrityError):
        now = utcnow()
        db.add(
            AssessmentAttempt(
                candidate_id=ready["id"],
                specialization="BACKEND",
                target_grade="JUNIOR",
                started_at=now,
                expires_at=now + timedelta(minutes=30),
            )
        )
        db.commit()
    assert client.get(BASE + "/current").json()["id"] == attempt["id"]


def test_concurrent_start_and_submit_postgres(client, ready, app, database, db_factory):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL row locks")
    cookies = dict(client.cookies)
    barrier = Barrier(2)

    def request(path, body):
        with TestClient(app, headers={"Origin": ORIGIN}, cookies=cookies) as parallel:
            barrier.wait(timeout=10)
            return parallel.post(path, json=body)

    with ThreadPoolExecutor(2) as pool:
        responses = list(
            pool.map(lambda _: request(BASE, {"target_grade": "MIDDLE"}), range(2))
        )
    assert sorted(r.status_code for r in responses) == [201, 409]
    attempt = next(r.json() for r in responses if r.status_code == 201)
    answer_counts(db_factory, attempt)
    barrier = Barrier(2)
    with ThreadPoolExecutor(2) as pool:
        results = list(
            pool.map(
                lambda _: request(f"{BASE}/{attempt['id']}/submit", None), range(2)
            )
        )
    assert all(r.status_code == 200 and r.json()["status"] == "PASSED" for r in results)
    assert results[0].json()["finished_at"] == results[1].json()["finished_at"]
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(AssessmentAttempt)) == 1
        assert db.get(CandidateProfile, ready["id"]).normalized_assessment_score == 100


def test_migration_0001_0002_preserves_profiles_and_resets_legacy_grade(database):
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    with database.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "0001")
        now = utcnow()
        connection.execute(
            text(
                "INSERT INTO users "
                "(id,email,password_hash,role,email_verified,created_at,updated_at) "
                "VALUES ('u','legacy@example.com','hash','CANDIDATE',true,:now,:now)"
            ),
            {"now": now},
        )
        connection.execute(
            text(
                "INSERT INTO candidate_profiles "
                "(id,user_id,first_name,last_name,specialization,declared_grade,"
                "verified_grade,personal_data_consent,created_at,updated_at) "
                "VALUES ('c','u','Имя','Фамилия','BACKEND','JUNIOR',"
                "'MIDDLE',false,:now,:now)"
            ),
            {"now": now},
        )
        command.upgrade(config, "0002")
        profile = (
            connection.execute(text("SELECT * FROM candidate_profiles WHERE id='c'"))
            .mappings()
            .one()
        )
        assert profile["first_name"] == "Имя"
        assert profile["verified_grade"] is None
        assert profile["normalized_assessment_score"] is None
        assert profile["assessment_verified_at"] is None
        command.upgrade(config, "head")
        command.check(config)
        command.downgrade(config, "0001")
        assert "normalized_assessment_score" not in {
            c["name"] for c in inspect(connection).get_columns("candidate_profiles")
        }
        command.upgrade(config, "head")
        command.check(config)


def test_history_aware_selection_and_cooldown_survive_specialization_restore(
    client, ready, candidate_data, monkeypatch
):
    import random

    monkeypatch.setattr(assessments.random, "SystemRandom", lambda: random.Random(42))
    first = start(client)
    finish(client, first)
    client.put(
        "/candidate/profile", json={**candidate_data, "specialization": "FRONTEND"}
    )
    client.put("/candidate/profile", json=candidate_data)
    assert (
        client.post(BASE, json={"target_grade": "MIDDLE"}).json()["error"]["code"]
        == "assessment_cooldown"
    )
    monkeypatch.setattr(assessments, "utcnow", lambda: utcnow() + timedelta(days=8))
    second = start(client)

    first_ids = {q["question_id"] for q in first["questions"]}
    second_ids = {q["question_id"] for q in second["questions"]}
    assert len(first_ids) == len(second_ids) == 20
    assert first_ids.isdisjoint(second_ids)


def test_timeout_exact_boundary(client, ready, db_factory, monkeypatch):
    from datetime import datetime

    attempt = start(client)
    answer_counts(db_factory, attempt, (3, 3, 3, 3, 2))
    deadline = datetime.fromisoformat(attempt["expires_at"])
    monkeypatch.setattr(
        assessments, "utcnow", lambda: deadline - timedelta(microseconds=1)
    )
    assert client.get(f"{BASE}/{attempt['id']}").json()["status"] == "IN_PROGRESS"
    monkeypatch.setattr(assessments, "utcnow", lambda: deadline)
    result = client.get(f"{BASE}/{attempt['id']}").json()
    assert result["status"] == "PASSED"
    assert result["completion_reason"] == "TIMEOUT"
    assert result["normalized_assessment_score"] == 70


def test_specialization_change_finalizes_expired_attempt_and_restores_history(
    client, ready, db_factory, candidate_data
):
    attempt = start(client)
    answer_counts(db_factory, attempt)
    expire(db_factory, attempt)
    changed = client.put(
        "/candidate/profile", json={**candidate_data, "specialization": "DATA_ML"}
    )
    assert changed.status_code == 200
    assert changed.json()["verified_grade"] is None
    assert (
        client.get(f"{BASE}/{attempt['id']}").json()["completion_reason"] == "TIMEOUT"
    )
    restored = client.put("/candidate/profile", json=candidate_data).json()
    assert restored["verified_grade"] == "MIDDLE"
    assert restored["normalized_assessment_score"] == 100


@pytest.mark.parametrize("score", [-1, 101])
def test_profile_score_database_range(ready, db_factory, score):
    with db_factory() as db, pytest.raises(IntegrityError):
        profile = db.get(CandidateProfile, ready["id"])
        profile.verified_grade = Grade.MIDDLE
        profile.normalized_assessment_score = score
        profile.assessment_verified_at = utcnow()
        db.commit()


def test_malformed_bank_is_unavailable(client, ready, db_factory):
    with db_factory() as db:
        question = db.scalar(
            select(AssessmentQuestion).where(AssessmentQuestion.grade == Grade.MIDDLE)
        )
        question.options[0].is_correct = False
        question.options[1].is_correct = False
        question.options[2].is_correct = False
        question.options[3].is_correct = False
        db.commit()
    assert (
        client.post(BASE, json={"target_grade": "MIDDLE"}).json()["error"]["code"]
        == "assessment_unavailable"
    )
