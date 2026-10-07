from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Event
from time import monotonic

import pytest
from sqlalchemy import select, text

from app.errors import ApiError
from app.invitation_schemas import InvitationSend
from app.models import (
    CandidateProfile,
    EmployerNeed,
    EmployerProfile,
    Invitation,
    InvitationStatus,
    User,
)
from app.need_schemas import NeedWrite
from app.schemas import CandidateWrite, EmployerWrite
from app.services import employer_needs, invitations, profiles
from app.services.candidate_assessments import ProfileAssessmentProvider


@pytest.fixture(autouse=True)
def postgres_only(database):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL independent Sessions/connections")


@contextmanager
def worker_session(database, db_factory):
    with database.connect() as connection, db_factory(bind=connection) as db:
        connection.detach()
        db.execute(text("SET LOCAL lock_timeout = '10s'"))
        db.execute(text("SET LOCAL statement_timeout = '15s'"))
        yield db, db.scalar(text("SELECT pg_backend_pid()"))


def wait_for_block(database, blocker, contender):
    deadline = monotonic() + 5
    with database.connect() as connection:
        while monotonic() < deadline:
            if connection.scalar(
                text("SELECT :blocker = ANY(pg_blocking_pids(:contender))"),
                {"blocker": blocker, "contender": contender},
            ):
                return
    pytest.fail("Expected PostgreSQL lock wait was not observed")


def test_concurrent_duplicate_send_one_winner(database, db_factory, invitation_setup):
    captured, release, started = Event(), Event(), Event()
    pids = {}
    setup = invitation_setup

    class PausedProvider:
        def __init__(self, db):
            self.db = db

        def get_assessments(self, ids):
            captured.set()
            assert release.wait(10)
            return ProfileAssessmentProvider(self.db).get_assessments(ids)

    def send_worker(first):
        with worker_session(database, db_factory) as (db, pid):
            pids[first] = pid
            user = db.get(User, setup["employer_user_id"])
            if not first:
                started.set()
            try:
                row = invitations.send(
                    db,
                    user,
                    setup["need_id"],
                    InvitationSend(candidate_id=setup["candidate_id"]),
                    PausedProvider(db) if first else ProfileAssessmentProvider(db),
                )
                return ("created", row.id)
            except ApiError as error:
                return (error.status, error.code)

    with ThreadPoolExecutor(2) as pool:
        first = pool.submit(send_worker, True)
        assert captured.wait(10)
        second = pool.submit(send_worker, False)
        try:
            assert started.wait(10)
            assert pids[True] != pids[False]
            wait_for_block(database, pids[True], pids[False])
        finally:
            release.set()
        a, b = first.result(timeout=20), second.result(timeout=20)
    assert a[0] == "created"
    assert b == (409, "invitation_conflict")
    with db_factory() as db:
        rows = list(db.scalars(select(Invitation)))
        assert len(rows) == 1
        assert rows[0].status == InvitationStatus.SENT


@pytest.mark.parametrize(
    "winner", [InvitationStatus.ACCEPTED, InvitationStatus.WITHDRAWN]
)
def test_accept_withdraw_race_stable_conflict(
    database, db_factory, invitation_setup, monkeypatch, winner
):
    setup = invitation_setup
    with db_factory() as db:
        invitation_id = invitations.send(
            db,
            db.get(User, setup["employer_user_id"]),
            setup["need_id"],
            InvitationSend(candidate_id=setup["candidate_id"]),
            ProfileAssessmentProvider(db),
        ).id
    captured, release, started = Event(), Event(), Event()
    pids = {}
    original_get = invitations.get

    def paused_get(db, *args, **kwargs):
        row = original_get(db, *args, **kwargs)
        if db.info.get("pause"):
            captured.set()
            assert release.wait(10)
        return row

    monkeypatch.setattr(invitations, "get", paused_get)
    loser = (
        InvitationStatus.WITHDRAWN
        if winner == InvitationStatus.ACCEPTED
        else InvitationStatus.ACCEPTED
    )

    def transition_worker(target, first):
        with worker_session(database, db_factory) as (db, pid):
            pids[first] = pid
            db.info["pause"] = first
            user_id = (
                setup["employer_user_id"]
                if target == InvitationStatus.WITHDRAWN
                else setup["candidate_user_id"]
            )
            user = db.get(User, user_id)
            if not first:
                started.set()
            try:
                return invitations.transition(db, user, invitation_id, target).status
            except ApiError as error:
                return (error.status, error.code)

    with ThreadPoolExecutor(2) as pool:
        a = pool.submit(transition_worker, winner, True)
        assert captured.wait(10)
        b = pool.submit(transition_worker, loser, False)
        try:
            assert started.wait(10)
            assert pids[True] != pids[False]
            wait_for_block(database, pids[True], pids[False])
        finally:
            release.set()
        assert a.result(timeout=20) == winner
        assert b.result(timeout=20) == (409, "invitation_state_conflict")
    with db_factory() as db:
        row = db.get(Invitation, invitation_id)
        assert row.status == winner
        assert row.viewed_at is None
        assert (row.responded_at is not None) == (winner == InvitationStatus.ACCEPTED)
        assert (row.withdrawn_at is not None) == (winner == InvitationStatus.WITHDRAWN)


@pytest.mark.parametrize("source", ["need", "candidate", "company"])
def test_send_snapshot_holds_source_locks(
    database,
    db_factory,
    invitation_setup,
    need_data,
    candidate_data,
    employer_data,
    source,
):
    setup = invitation_setup
    captured, release, started = Event(), Event(), Event()
    pids = {}

    class PausedProvider:
        def __init__(self, db):
            self.db = db

        def get_assessments(self, ids):
            captured.set()
            assert release.wait(10)
            return ProfileAssessmentProvider(self.db).get_assessments(ids)

    def sender():
        with worker_session(database, db_factory) as (db, pid):
            pids["send"] = pid
            return invitations.send(
                db,
                db.get(User, setup["employer_user_id"]),
                setup["need_id"],
                InvitationSend(candidate_id=setup["candidate_id"]),
                PausedProvider(db),
            ).id

    def editor():
        with worker_session(database, db_factory) as (db, pid):
            pids["edit"] = pid
            user = db.get(
                User,
                setup["candidate_user_id"]
                if source == "candidate"
                else setup["employer_user_id"],
            )
            started.set()
            if source == "need":
                employer_needs.update_need(
                    db,
                    user,
                    setup["need_id"],
                    NeedWrite(
                        **(
                            need_data
                            | {"position_title": "Changed need", "salary_from": "0"}
                        )
                    ),
                )
            elif source == "candidate":
                profiles.save_candidate(
                    db,
                    user,
                    CandidateWrite(
                        **(
                            candidate_data
                            | {"first_name": "Changed candidate", "skill_ids": []}
                        )
                    ),
                    create=False,
                )
            else:
                profiles.save_employer(
                    db,
                    user,
                    EmployerWrite(
                        **(employer_data | {"company_name": "Changed company"})
                    ),
                    create=False,
                )

    with ThreadPoolExecutor(2) as pool:
        a = pool.submit(sender)
        assert captured.wait(10)
        b = pool.submit(editor)
        try:
            assert started.wait(10)
            wait_for_block(database, pids["send"], pids["edit"])
        finally:
            release.set()
        invitation_id = a.result(timeout=20)
        b.result(timeout=20)
    with db_factory() as db:
        row = db.get(Invitation, invitation_id)
        assert row.need_snapshot["position_title"] == "Backend developer"
        assert row.need_snapshot["salary_from"] == "100000.00"
        assert row.need_snapshot["company_name"] == "Tech"
        assert row.candidate_snapshot["display_name"] == "Анна P."
        assert row.candidate_snapshot["normalized_assessment_score"] == 80


def test_send_refreshes_stale_session_objects(
    database, db_factory, invitation_setup, need_data
):
    setup = invitation_setup
    with db_factory() as old:
        need = old.get(EmployerNeed, setup["need_id"])
        candidate = old.get(CandidateProfile, setup["candidate_id"])
        company = old.get(EmployerProfile, setup["employer_id"])
        assert candidate.normalized_assessment_score == 80
        assert company.company_name == "Tech"
        with db_factory() as edit:
            employer_needs.update_need(
                edit,
                edit.get(User, setup["employer_user_id"]),
                setup["need_id"],
                NeedWrite(**(need_data | {"position_title": "Current need"})),
            )
        with db_factory() as edit:
            edit.get(
                CandidateProfile, setup["candidate_id"]
            ).normalized_assessment_score = 99
            edit.get(
                EmployerProfile, setup["employer_id"]
            ).company_name = "Current company"
            edit.commit()
        assert need.position_title != "Current need"
        row = invitations.send(
            old,
            old.get(User, setup["employer_user_id"]),
            setup["need_id"],
            InvitationSend(candidate_id=setup["candidate_id"]),
            ProfileAssessmentProvider(old),
        )
        assert row.need_snapshot["position_title"] == "Current need"
        assert row.need_snapshot["company_name"] == "Current company"
        assert row.candidate_snapshot["normalized_assessment_score"] == 99
