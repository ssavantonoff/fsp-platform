from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest
from sqlalchemy import event, select

from app.models import CandidateProfile, Grade, Role, Specialization, User
from app.services.candidate_assessments import (
    CandidateAssessment,
    CandidateAssessmentProvider,
    ProfileAssessmentProvider,
)

VERIFIED_AT = datetime(2026, 9, 1, 12, tzinfo=UTC)
ASSESSMENT_COLUMNS = (
    CandidateProfile.verified_grade,
    CandidateProfile.normalized_assessment_score,
    CandidateProfile.assessment_verified_at,
)


class FakeAssessmentProvider(CandidateAssessmentProvider):
    def __init__(self, records: Mapping[str, CandidateAssessment]):
        self.records = dict(records)
        self.calls: list[tuple[str, ...]] = []

    def get_assessments(
        self, candidate_ids: Sequence[str]
    ) -> Mapping[str, CandidateAssessment]:
        self.calls.append(tuple(candidate_ids))
        return {
            candidate_id: self.records[candidate_id]
            for candidate_id in candidate_ids
            if candidate_id in self.records
        }


@pytest.fixture
def candidate_ids(db_factory):
    def create(count=1, *, grade=Grade.MIDDLE, score=80, verified_at=VERIFIED_AT):
        with db_factory() as db:
            users = [
                User(
                    email=f"provider-{index}@example.com",
                    password_hash="unused-test-hash",
                    role=Role.CANDIDATE,
                )
                for index in range(count)
            ]
            db.add_all(users)
            db.flush()
            profiles = [
                CandidateProfile(
                    user_id=user.id,
                    first_name="Анна",
                    last_name="Иванова",
                    specialization=Specialization.BACKEND,
                    declared_grade=Grade.JUNIOR,
                    verified_grade=grade,
                    normalized_assessment_score=score,
                    assessment_verified_at=verified_at,
                )
                for user in users
            ]
            db.add_all(profiles)
            db.commit()
            return [profile.id for profile in profiles]

    return create


@contextmanager
def capture_sql(engine):
    statements = []
    commits = []

    def executed(connection, cursor, statement, parameters, context, executemany):
        statements.append((statement, parameters, context))

    def committed(connection):
        commits.append(connection)

    event.listen(engine, "before_cursor_execute", executed)
    event.listen(engine, "commit", committed)
    try:
        yield statements, commits
    finally:
        event.remove(engine, "before_cursor_execute", executed)
        event.remove(engine, "commit", committed)


@pytest.mark.parametrize(
    "grade,score,verified_at",
    [
        (Grade.MIDDLE, 80, VERIFIED_AT),
        (Grade.JUNIOR, 0, VERIFIED_AT),
        (Grade.SENIOR, 100, VERIFIED_AT),
        (None, None, None),
    ],
)
def test_provider_returns_canonical_current_state(
    db_factory, candidate_ids, grade, score, verified_at
):
    candidate_id = candidate_ids(grade=grade, score=score, verified_at=verified_at)[0]
    with db_factory() as db:
        provider: CandidateAssessmentProvider = ProfileAssessmentProvider(db)
        records = provider.get_assessments([candidate_id])
        persisted = db.execute(
            select(*ASSESSMENT_COLUMNS).where(CandidateProfile.id == candidate_id)
        ).one()
        assert set(records) == {candidate_id}
        assessment = records[candidate_id]
        assert assessment == CandidateAssessment(candidate_id, *persisted)
        assert assessment.verified_grade == grade
        assert assessment.normalized_assessment_score == score
        with pytest.raises(FrozenInstanceError):
            assessment.normalized_assessment_score = 99

        # A repeated read must reflect current persisted state, even when an ORM
        # instance in this Session still holds the earlier canonical values.
        stale_profile = db.get(CandidateProfile, candidate_id)
        with db_factory() as writer:
            profile = writer.get(CandidateProfile, candidate_id)
            profile.verified_grade = Grade.SENIOR
            profile.normalized_assessment_score = 95
            profile.assessment_verified_at = datetime(2026, 10, 1, tzinfo=UTC)
            writer.commit()
        current = provider.get_assessments([candidate_id])[candidate_id]
        assert current.verified_grade == Grade.SENIOR
        assert current.normalized_assessment_score == 95
        assert stale_profile.normalized_assessment_score == score
        with db_factory() as reader:
            persisted = reader.execute(
                select(*ASSESSMENT_COLUMNS).where(CandidateProfile.id == candidate_id)
            ).one()
        assert current == CandidateAssessment(candidate_id, *persisted)


def test_provider_empty_and_missing_ids(database, db_factory, candidate_ids):
    candidate_id = candidate_ids()[0]
    with db_factory() as db:
        provider = ProfileAssessmentProvider(db)
        with capture_sql(database) as (statements, commits):
            assert provider.get_assessments([]) == {}
        assert statements == []
        assert commits == []
        assert provider.get_assessments(["missing-profile"]) == {}
        assert set(provider.get_assessments(["missing-profile", candidate_id])) == {
            candidate_id
        }


def test_provider_batches_and_deduplicates(database, db_factory, candidate_ids):
    ids = candidate_ids(501)
    with db_factory() as db:
        with capture_sql(database) as (statements, commits):
            records = ProfileAssessmentProvider(db).get_assessments(ids * 3)
        assert set(records) == set(ids)
        assert len(statements) == 2
        assert commits == []
        bound_ids = []
        for statement, parameters, context in statements:
            assert statement.lstrip().upper().startswith("SELECT")
            query = context.compiled.statement
            assert tuple(query.selected_columns.keys()) == (
                "id",
                "verified_grade",
                "normalized_assessment_score",
                "assessment_verified_at",
            )
            assert [table.name for table in query.get_final_froms()] == [
                "candidate_profiles"
            ]
            values = (
                list(parameters.values())
                if isinstance(parameters, dict)
                else parameters
            )
            assert 1 <= len(values) <= 500
            bound_ids.extend(values)
        assert len(bound_ids) == 501
        assert set(bound_ids) == set(ids)


def test_provider_does_not_write_assessment_fields(database, db_factory, candidate_ids):
    candidate_id = candidate_ids()[0]
    with db_factory() as reader:
        before = reader.execute(
            select(*ASSESSMENT_COLUMNS).where(CandidateProfile.id == candidate_id)
        ).one()
    with db_factory() as db:
        profile = db.get(CandidateProfile, candidate_id)
        profile.verified_grade = Grade.SENIOR
        profile.normalized_assessment_score = 96
        profile.assessment_verified_at = datetime(2026, 10, 2, tzinfo=UTC)
        pending_user = User(
            email="pending@example.com",
            password_hash="unused-test-hash",
            role=Role.CANDIDATE,
        )
        db.add(pending_user)
        flushes = []
        session_commits = []

        def flushed(session, flush_context, instances):
            flushes.append(session)

        def committed(session):
            session_commits.append(session)

        event.listen(db, "before_flush", flushed)
        event.listen(db, "before_commit", committed)
        try:
            with capture_sql(database) as (statements, commits):
                records = ProfileAssessmentProvider(db).get_assessments([candidate_id])
        finally:
            event.remove(db, "before_flush", flushed)
            event.remove(db, "before_commit", committed)
        assert records[candidate_id] == CandidateAssessment(candidate_id, *before)
        assert len(statements) == 1
        assert statements[0][0].lstrip().upper().startswith("SELECT")
        assert flushes == []
        assert commits == []
        assert session_commits == []
        assert profile in db.dirty
        assert pending_user in db.new
        assert profile.normalized_assessment_score == 96
        with db_factory() as reader:
            after = reader.execute(
                select(*ASSESSMENT_COLUMNS).where(CandidateProfile.id == candidate_id)
            ).one()
            assert after == before
            assert (
                reader.scalar(
                    select(User.id).where(User.email == "pending@example.com")
                )
                is None
            )
