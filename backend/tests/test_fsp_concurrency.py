from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from sqlalchemy import select

from app.errors import ApiError
from app.invitation_schemas import InvitationSend
from app.models import CandidateProfile, FspAchievement, User
from app.schemas import CandidateWrite
from app.services import fsp, invitations, profiles
from app.services.candidate_assessments import ProfileAssessmentProvider
from app.services.fsp_registry import MockFspRegistryProvider
from tests.test_invitation_concurrency import wait_for_block, worker_session


@pytest.fixture(autouse=True)
def postgres_only(database):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL independent Sessions/connections")


def test_same_verified_id_cross_account_race(database, db_factory, matching_candidate):
    ids = [matching_candidate(fsp_id="MOCK-MULTI") for _ in range(2)]
    inserted, release, started = Event(), Event(), Event()
    pids = {}

    def worker(first):
        with worker_session(database, db_factory) as (db, pid):
            pids[first] = pid
            profile = db.get(CandidateProfile, ids[0 if first else 1])
            if first:

                def pause_commit():
                    db.flush()
                    inserted.set()
                    assert release.wait(10)
                    original_commit()

                original_commit = db.commit
                db.commit = pause_commit
            else:
                started.set()
            try:
                return fsp.sync(
                    db, db.get(User, profile.user_id), MockFspRegistryProvider()
                ).fsp_verified
            except ApiError as error:
                return error.status, error.code

    with ThreadPoolExecutor(2) as pool:
        first = pool.submit(worker, True)
        assert inserted.wait(10)
        second = pool.submit(worker, False)
        try:
            assert started.wait(10)
            assert pids[True] != pids[False]
            wait_for_block(database, pids[True], pids[False])
        finally:
            release.set()
        assert first.result(timeout=20) is True
        assert second.result(timeout=20) == (409, "fsp_verification_conflict")
    with db_factory() as db:
        verified = list(
            db.scalars(
                select(CandidateProfile).where(
                    CandidateProfile.fsp_verified_at.is_not(None)
                )
            )
        )
        assert len(verified) == 1 and verified[0].id == ids[0]
        assert len(list(db.scalars(select(FspAchievement)))) == 3


def test_verify_and_identifier_edit_use_same_parent_lock(
    database, db_factory, matching_candidate, candidate_data
):
    candidate_id = matching_candidate(fsp_id="MOCK-WINNER")
    captured, release, started = Event(), Event(), Event()
    pids = {}

    class PausedProvider(MockFspRegistryProvider):
        def lookup(self, identifier):
            captured.set()
            assert release.wait(10)
            return super().lookup(identifier)

    def worker(first):
        with worker_session(database, db_factory) as (db, pid):
            pids[first] = pid
            profile = db.get(CandidateProfile, candidate_id)
            user = db.get(User, profile.user_id)
            if first:
                return fsp.sync(db, user, PausedProvider()).fsp_verified
            started.set()
            profiles.save_candidate(
                db,
                user,
                CandidateWrite(**candidate_data, fsp_id="MOCK-TEAM"),
                create=False,
            )
            return True

    with ThreadPoolExecutor(2) as pool:
        first = pool.submit(worker, True)
        assert captured.wait(10)
        second = pool.submit(worker, False)
        try:
            assert started.wait(10)
            assert pids[True] != pids[False]
            wait_for_block(database, pids[True], pids[False])
        finally:
            release.set()
        assert first.result(timeout=20) and second.result(timeout=20)
    with db_factory() as db:
        profile = db.get(CandidateProfile, candidate_id)
        assert profile.fsp_id == "MOCK-TEAM" and profile.fsp_verified_at is None
        assert db.scalar(select(FspAchievement)) is None


def test_invitation_send_and_unlink_keep_coherent_locked_evidence(
    database, db_factory, invitation_setup
):
    setup = invitation_setup
    with db_factory() as db:
        candidate = db.get(CandidateProfile, setup["candidate_id"])
        candidate.fsp_id = "MOCK-MULTI"
        db.commit()
        fsp.sync(db, db.get(User, candidate.user_id), MockFspRegistryProvider())
    captured, release, started = Event(), Event(), Event()
    pids = {}

    class PausedAssessment:
        def __init__(self, db):
            self.db = db

        def get_assessments(self, ids):
            captured.set()
            assert release.wait(10)
            return ProfileAssessmentProvider(self.db).get_assessments(ids)

    def worker(first):
        with worker_session(database, db_factory) as (db, pid):
            pids[first] = pid
            if first:
                invitation = invitations.send(
                    db,
                    db.get(User, setup["employer_user_id"]),
                    setup["need_id"],
                    InvitationSend(candidate_id=setup["candidate_id"]),
                    PausedAssessment(db),
                )
                return invitation.candidate_snapshot
            started.set()
            return fsp.unlink(db, db.get(User, setup["candidate_user_id"])).fsp_verified

    with ThreadPoolExecutor(2) as pool:
        first = pool.submit(worker, True)
        assert captured.wait(10)
        second = pool.submit(worker, False)
        try:
            assert started.wait(10)
            assert pids[True] != pids[False]
            wait_for_block(database, pids[True], pids[False])
        finally:
            release.set()
        snapshot = first.result(timeout=20)
        assert second.result(timeout=20) is False
    assert snapshot["fsp_verified"] is True and snapshot["fsp_bonus"] == 5
    with db_factory() as db:
        assert db.get(CandidateProfile, setup["candidate_id"]).fsp_verified_at is None
        assert db.scalar(select(FspAchievement)) is None
