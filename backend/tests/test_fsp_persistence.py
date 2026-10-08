from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.models import CandidateProfile, FspAchievement, User


def verified(db, candidate_id, identifier="MOCK-WINNER"):
    profile = db.get(CandidateProfile, candidate_id)
    profile.fsp_id = profile.fsp_verified_id = identifier
    profile.fsp_verified_at = profile.fsp_synced_at = datetime.now(UTC)
    return profile


def achievement(candidate_id, **extra):
    return FspAchievement(
        candidate_id=candidate_id,
        external_id="achievement-1",
        competition_id="event-1",
        competition_name="Cup",
        discipline="Programming",
        result_level="WINNER",
        **extra,
    )


def test_verified_identifier_unique_but_entered_id_is_not(
    db_factory, matching_candidate
):
    one, two = matching_candidate(), matching_candidate()
    with db_factory() as db:
        verified(db, one)
        db.get(CandidateProfile, two).fsp_id = "MOCK-WINNER"
        db.commit()
        verified(db, two)
        with pytest.raises(IntegrityError):
            db.commit()


@pytest.mark.parametrize("invalid", ["missing_sync", "changed_id", "backdated_sync"])
def test_timestamp_identity_checks(db_factory, matching_candidate, invalid):
    candidate_id = matching_candidate()
    with db_factory() as db:
        profile = verified(db, candidate_id)
        if invalid == "missing_sync":
            profile.fsp_synced_at = None
        elif invalid == "changed_id":
            profile.fsp_id = "different"
        else:
            profile.fsp_synced_at -= timedelta(seconds=1)
        with pytest.raises(IntegrityError):
            db.commit()


@pytest.mark.parametrize("extra", [{"placement": 0}, {"scope": "INVALID"}, {"year": 0}])
def test_achievement_checks(db_factory, matching_candidate, extra):
    candidate_id = matching_candidate()
    with db_factory() as db:
        verified(db, candidate_id)
        db.add(achievement(candidate_id, **extra))
        with pytest.raises(IntegrityError):
            db.commit()


def test_achievement_unique_and_foreign_key(db_factory, matching_candidate):
    candidate_id = matching_candidate()
    with db_factory() as db:
        db.add(achievement(candidate_id))
        db.commit()
        db.add(achievement(candidate_id))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        db.add(achievement("missing"))
        with pytest.raises(IntegrityError):
            db.commit()


def test_migration_round_trip_preserves_existing_profile(
    database, db_factory, matching_candidate
):
    candidate_id = matching_candidate()
    with db_factory() as db:
        original = db.get(CandidateProfile, candidate_id).fsp_id
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    with database.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "a812e4c79b60")
        assert "fsp_achievements" not in inspect(connection).get_table_names()
        command.upgrade(config, "head")
        command.check(config)
    with db_factory() as db:
        profile = db.get(CandidateProfile, candidate_id)
        assert profile.fsp_id == original
        assert profile.fsp_verified_at is None
        assert db.scalar(select(User).where(User.id == profile.user_id)) is not None
