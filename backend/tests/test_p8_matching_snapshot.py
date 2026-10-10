"""P8-B0-001 regressions against real PostgreSQL, with bounded checkpoints."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, select

from app.models import AssessmentAttempt, CandidateProfile, Skill, User, utcnow
from app.question_bank import seed_questions
from app.schemas import CandidateWrite
from app.services import fsp, profiles
from app.services.candidate_assessments import ProfileAssessmentProvider
from app.services.fsp_registry import MockFspRegistryProvider
from tests.conftest import ORIGIN, PASSWORD


def candidate_state(db_factory, candidate_id):
    with db_factory() as db:
        profile = db.get(CandidateProfile, candidate_id)
        return (
            profile.personal_data_consent,
            profile.verified_grade,
            profile.normalized_assessment_score,
        )


@pytest.mark.parametrize("repeat", range(3))
def test_matching_never_combines_old_consent_with_new_assessment(
    database,
    client,
    app,
    account,
    candidate_data,
    db_factory,
    employer_account,
    need_data,
    monkeypatch,
    repeat,
):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL 17 independent committed transactions")
    with database.connect() as connection:
        assert (
            170000
            <= int(connection.exec_driver_sql("SHOW server_version_num").scalar_one())
            < 180000
        )
    user = account(email=f"snapshot-{repeat}@example.com")
    response = client.post("/candidate/profile", json=candidate_data)
    assert response.status_code == 201, response.text
    candidate_id = response.json()["id"]
    with db_factory() as db:
        seed_questions(db)
        db.get(User, user["id"]).email_verified = True
        db.commit()
    response = client.post("/candidate/assessments", json={"target_grade": "MIDDLE"})
    assert response.status_code == 201, response.text
    attempt_id = response.json()["id"]
    with db_factory() as db:
        attempt = db.get(AssessmentAttempt, attempt_id)
        answers = [
            (
                question.id,
                next(
                    option.id
                    for option in question.question.options
                    if option.is_correct
                ),
            )
            for question in attempt.questions
        ]
    for question_id, option_id in answers:
        response = client.put(
            f"/candidate/assessments/{attempt_id}/answers/{question_id}",
            json={"selected_option_id": option_id},
        )
        assert response.status_code == 200, response.text
    employer_account(f"snapshot-employer-{repeat}@example.com")
    response = client.post("/employer/needs", json=need_data)
    assert response.status_code == 201, response.text
    need_id = response.json()["id"]
    assert client.post(f"/employer/needs/{need_id}/activate").status_code == 200
    path = f"/employer/needs/{need_id}/matches"
    assert client.get(path).json()["total"] == 0

    assert candidate_state(db_factory, candidate_id) == (True, None, None)
    captured, release = Event(), Event()
    original = ProfileAssessmentProvider.get_assessments
    paused = False

    def checkpoint(provider, ids):
        nonlocal paused
        if not paused:
            paused = True
            captured.set()
            assert release.wait(20), "Matching reader was not released"
        return original(provider, ids)

    monkeypatch.setattr(ProfileAssessmentProvider, "get_assessments", checkpoint)
    with TestClient(app, headers={"Origin": ORIGIN}) as owner:
        response = owner.post(
            "/auth/login", json={"email": user["email"], "password": PASSWORD}
        )
        assert response.status_code == 200, response.text
        with ThreadPoolExecutor(1) as pool:
            reader = pool.submit(client.get, path)
            try:
                assert captured.wait(20), "Matching did not capture profile pool"
                response = owner.put(
                    "/candidate/profile",
                    json={**candidate_data, "personal_data_consent": False},
                )
                assert response.status_code == 200, response.text
                assert candidate_state(db_factory, candidate_id) == (False, None, None)
                response = owner.post(f"/candidate/assessments/{attempt_id}/submit")
                assert response.status_code == 200, response.text
                assert response.json()["status"] == "PASSED"
                assert candidate_state(db_factory, candidate_id) == (
                    False,
                    "MIDDLE",
                    100,
                )
            finally:
                release.set()
            response = reader.result(20)
    assert response.status_code == 200, response.text
    # None of the three committed states was eligible. A snapshot cannot admit it.
    assert response.json()["total"] == 0, response.json()
    assert response.json()["items"] == []
    assert client.get(path).json()["total"] == 0


@pytest.mark.parametrize(
    "change",
    [
        "skills_specialization",
        "grant_without_grade",
        "ranking_fsp",
        "fsp_reset",
        "achievement_refresh",
    ],
)
def test_matching_uses_one_candidate_version_for_all_inputs(
    database,
    db_factory,
    client,
    employer_account,
    need_data,
    matching_candidate,
    skill_ids,
    change,
):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL independent committed transactions")
    employer_account()
    need = client.post("/employer/needs", json=need_data).json()
    assert client.post(f"/employer/needs/{need['id']}/activate").status_code == 200
    candidate_id = matching_candidate(
        personal_data_consent=change != "grant_without_grade",
        skill_ids=skill_ids[:1] if change == "skills_specialization" else skill_ids[:2],
        fsp_id="MOCK-WINNER",
    )
    if change in {"fsp_reset", "achievement_refresh"}:
        with db_factory() as db:
            profile = db.get(CandidateProfile, candidate_id)
            fsp.sync(db, db.get(User, profile.user_id), MockFspRegistryProvider())
    path = f"/employer/needs/{need['id']}/matches"
    before = client.get(path).json()
    captured, release = Event(), Event()
    pids = {}
    paused = False

    def checkpoint(connection, cursor, statement, parameters, context, executemany):
        nonlocal paused
        if not paused and "candidate_profiles.first_name" in statement.lower():
            paused = True
            pids["reader"] = connection.connection.driver_connection.info.backend_pid
            captured.set()
            assert release.wait(20), "Candidate statement checkpoint not released"

    event.listen(database, "after_cursor_execute", checkpoint)
    try:
        with ThreadPoolExecutor(1) as pool:
            reader = pool.submit(client.get, path)
            try:
                assert captured.wait(20), "Candidate statement not captured"
                with db_factory() as db:
                    profile = db.get(CandidateProfile, candidate_id)
                    pids["writer"] = (
                        db.connection().connection.driver_connection.info.backend_pid
                    )
                    if change == "skills_specialization":
                        # Two valid synthetic canonical states; neither fits the Need.
                        profile.specialization = "FRONTEND"
                        profile.skills = list(db.scalars(select(Skill)))
                    elif change == "grant_without_grade":
                        profile.personal_data_consent = True
                        profile.personal_data_consent_at = utcnow()
                        profile.verified_grade = None
                        profile.normalized_assessment_score = None
                        profile.assessment_verified_at = None
                    elif change == "fsp_reset":
                        profiles.save_candidate(
                            db,
                            db.get(User, profile.user_id),
                            CandidateWrite(
                                first_name=profile.first_name,
                                last_name=profile.last_name,
                                specialization=profile.specialization,
                                declared_grade=profile.declared_grade,
                                personal_data_consent=True,
                                years_of_experience=profile.years_of_experience,
                                skill_ids=skill_ids[:2],
                                fsp_id="MOCK-TEAM",
                            ),
                            create=False,
                        )
                    elif change == "achievement_refresh":
                        registry = MockFspRegistryProvider()
                        registry._profiles["MOCK-WINNER"] = registry._profiles[
                            "MOCK-PARTICIPANT"
                        ]
                        fsp.sync(
                            db, db.get(User, profile.user_id), registry, refresh=True
                        )
                    else:
                        profile.first_name = "Updated"
                        profile.normalized_assessment_score = 100
                        profile.years_of_experience = 8
                        profile.skills = list(db.scalars(select(Skill)))
                        db.flush()
                        fsp.sync(
                            db, db.get(User, profile.user_id), MockFspRegistryProvider()
                        )
                    db.commit()
                # Writer has committed while reader still holds its checkpoint.
                assert not reader.done() and not release.is_set()
            finally:
                release.set()
            response = reader.result(20)
        assert response.status_code == 200, response.text
        assert pids["reader"] != pids["writer"]
        assert response.json() == before
        fresh = client.get(path).json()
        if change == "ranking_fsp":
            assert before["items"][0]["professional_fit_score"] == 71
            assert before["items"][0]["fsp_bonus"] == 0
            assert fresh["items"][0]["professional_fit_score"] == 100
            assert fresh["items"][0]["fsp_bonus"] == 4
            assert fresh["items"][0]["ranking_score"] == 99
        elif change in {"fsp_reset", "achievement_refresh"}:
            assert before["total"] == fresh["total"] == 1
            assert before["items"][0]["fsp_bonus"] == 4
            assert (
                before["items"][0]["professional_fit_score"]
                == fresh["items"][0]["professional_fit_score"]
            )
            assert fresh["items"][0]["fsp_bonus"] != 4
            assert fresh["items"][0]["fsp_verified"] is (
                change == "achievement_refresh"
            )
        else:
            assert before["total"] == fresh["total"] == 0
        print(
            {
                "case": change,
                "pids": pids,
                "old_total": before["total"],
                "fresh_total": fresh["total"],
            }
        )
    finally:
        release.set()
        event.remove(database, "after_cursor_execute", checkpoint)


def test_concurrent_rank_change_keeps_sorting_and_pagination_on_one_snapshot(
    database,
    db_factory,
    client,
    employer_account,
    need_data,
    matching_candidate,
):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL independent committed transactions")
    employer_account()
    need = client.post("/employer/needs", json=need_data).json()
    assert client.post(f"/employer/needs/{need['id']}/activate").status_code == 200
    low = matching_candidate(normalized_assessment_score=80, fsp_id="MOCK-WINNER")
    middle = matching_candidate(normalized_assessment_score=90, years_of_experience=3)
    high = matching_candidate(normalized_assessment_score=100, years_of_experience=3)
    path = f"/employer/needs/{need['id']}/matches"
    full = client.get(path).json()
    assert [item["candidate_id"] for item in full["items"]] == [high, middle, low]
    expected = client.get(path, params={"limit": 2, "offset": 1}).json()
    captured, release = Event(), Event()
    paused = False

    def checkpoint(connection, cursor, statement, parameters, context, executemany):
        nonlocal paused
        if not paused and "candidate_profiles.first_name" in statement.lower():
            paused = True
            captured.set()
            assert release.wait(20)

    event.listen(database, "after_cursor_execute", checkpoint)
    try:
        with ThreadPoolExecutor(1) as pool:
            reader = pool.submit(client.get, path, params={"limit": 2, "offset": 1})
            try:
                assert captured.wait(20)
                with db_factory() as db:
                    profile = db.get(CandidateProfile, low)
                    profile.normalized_assessment_score = 100
                    profile.years_of_experience = 3
                    db.flush()
                    fsp.sync(
                        db, db.get(User, profile.user_id), MockFspRegistryProvider()
                    )
                assert not reader.done()
            finally:
                release.set()
            response = reader.result(20)
        assert response.status_code == 200, response.text
        assert response.json() == expected
        fresh = client.get(path).json()
        assert [item["candidate_id"] for item in fresh["items"]] == [low, high, middle]
        page = client.get(path, params={"limit": 2, "offset": 1}).json()
        assert page["items"] == fresh["items"][1:]
        assert page["total"] == 3
    finally:
        release.set()
        event.remove(database, "after_cursor_execute", checkpoint)


def test_matching_snapshot_does_not_replace_dirty_or_stale_identity_map(
    database,
    db_factory,
    client,
    employer_account,
    need_data,
    matching_candidate,
):
    from app.services import matching

    employer_user, _ = employer_account()
    need = client.post("/employer/needs", json=need_data).json()
    assert client.post(f"/employer/needs/{need['id']}/activate").status_code == 200
    candidate_id = matching_candidate()
    with db_factory() as reader:
        owner = reader.get(User, employer_user["id"])
        retained = reader.get(CandidateProfile, candidate_id)
        retained.first_name = "Pending private edit"
        with db_factory() as writer:
            profile = writer.get(CandidateProfile, candidate_id)
            profile.personal_data_consent = False
            profile.personal_data_consent_at = None
            writer.commit()
        result = matching.match_need(
            reader,
            owner,
            need["id"],
            ProfileAssessmentProvider(reader),
            limit=20,
            offset=0,
        )
        assert result.total == 0
        assert retained.first_name == "Pending private edit"
        assert retained.personal_data_consent is True
        assert retained in reader.dirty


def test_provider_snapshot_clears_after_failure_and_restores_live_canonical_reads(
    db_factory,
    matching_candidate,
):
    candidate_id = matching_candidate()
    with db_factory() as db:
        provider = ProfileAssessmentProvider(db)
        old = provider.get_assessments([candidate_id])
        with pytest.raises(RuntimeError, match="synthetic checkpoint failure"):
            with provider.matching_snapshot(old):
                with db_factory() as writer:
                    writer.get(
                        CandidateProfile, candidate_id
                    ).normalized_assessment_score = 99
                    writer.commit()
                assert (
                    provider.get_assessments([candidate_id, candidate_id, "missing"])[
                        candidate_id
                    ].normalized_assessment_score
                    == 80
                )
                raise RuntimeError("synthetic checkpoint failure")
        assert (
            provider.get_assessments([candidate_id])[
                candidate_id
            ].normalized_assessment_score
            == 99
        )
