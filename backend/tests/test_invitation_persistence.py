from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from threading import Barrier, Event
from time import monotonic, sleep
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import MetaData, Table, inspect, select, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from app import models
from app.models import CandidateProfile, EmployerNeed, EmployerProfile, User
from app.seed import seed

SENT_AT = datetime(2026, 10, 7, 10, tzinfo=UTC)
VIEWED_AT = SENT_AT + timedelta(minutes=1)
TERMINAL_AT = SENT_AT + timedelta(minutes=2)


@pytest.fixture
def invitation_values(db_factory):
    with db_factory() as db:
        seed(db, demo=True, demo_password="invitation-test-password")
        employer = db.scalar(select(EmployerProfile))
        candidate = db.scalar(select(CandidateProfile))
        need = EmployerNeed(
            employer_id=employer.id,
            position_title="Backend Engineer",
            specialization="BACKEND",
            required_grade="MIDDLE",
            salary_from=Decimal("180000.00"),
            salary_to=Decimal("230000.00"),
            description="Build services",
            status="ACTIVE",
        )
        db.add(need)
        db.commit()
        return {
            "id": str(uuid4()),
            "need_id": need.id,
            "employer_id": employer.id,
            "candidate_id": candidate.id,
            "status": "SENT",
            "message": "Приглашаем обсудить предложение.",
            "need_snapshot": {
                "position_title": "Backend Engineer",
                "salary_from": "180000.00",
                "salary_to": "230000.00",
                "company_name": "Tech",
            },
            "candidate_snapshot": {"display_name": "Анна И.", "breakdown": {}},
            "sent_at": SENT_AT,
            "viewed_at": None,
            "responded_at": None,
            "withdrawn_at": None,
            "created_at": SENT_AT,
            "updated_at": SENT_AT,
        }


def invitations(connection):
    # Reflect the migrated schema: tests must catch omissions in the migration too.
    return Table("invitations", MetaData(), autoload_with=connection)


def state_values(status, viewed=False):
    return {
        "status": status,
        "viewed_at": VIEWED_AT if viewed or status == "VIEWED" else None,
        "responded_at": TERMINAL_AT if status in {"ACCEPTED", "DECLINED"} else None,
        "withdrawn_at": TERMINAL_AT if status == "WITHDRAWN" else None,
    }


def test_invitation_model_registered():
    assert "invitations" in models.Base.metadata.tables
    assert set(models.InvitationStatus) == {
        "SENT",
        "VIEWED",
        "ACCEPTED",
        "DECLINED",
        "WITHDRAWN",
    }


@pytest.mark.parametrize(
    "status,viewed",
    [("SENT", False), ("VIEWED", True)]
    + [
        (status, viewed)
        for status in ("ACCEPTED", "DECLINED", "WITHDRAWN")
        for viewed in (False, True)
    ],
)
def test_invitation_model_round_trip(db_factory, invitation_values, status, viewed):
    with db_factory() as db:
        invitation = models.Invitation(
            **(invitation_values | state_values(status, viewed))
        )
        db.add(invitation)
        db.commit()
        invitation_id = invitation.id
    with db_factory() as db:
        saved = db.get(models.Invitation, invitation_id)
        assert saved.status == status
        assert (saved.viewed_at is not None) == viewed
        assert (saved.responded_at is not None) == (status in {"ACCEPTED", "DECLINED"})
        assert (saved.withdrawn_at is not None) == (status == "WITHDRAWN")
        assert saved.need_snapshot["salary_from"] == "180000.00"
        assert saved.candidate_snapshot["display_name"] == "Анна И."


@pytest.mark.parametrize(
    "changes",
    [
        {"need_id": "missing"},
        {"employer_id": "missing"},
        {"candidate_id": "missing"},
        {"status": "INVALID"},
        {"sent_at": None},
        {"need_snapshot": None},
        {"candidate_snapshot": None},
        {"need_snapshot": []},
        {"candidate_snapshot": "not an object"},
        {"message": "я" * 2001},
        {"viewed_at": VIEWED_AT},
        {"responded_at": TERMINAL_AT},
        {"withdrawn_at": TERMINAL_AT},
        {"status": "VIEWED"},
        {"status": "ACCEPTED"},
        {"status": "DECLINED"},
        {"status": "WITHDRAWN"},
        state_values("VIEWED") | {"viewed_at": SENT_AT - timedelta(seconds=1)},
        state_values("ACCEPTED") | {"responded_at": SENT_AT - timedelta(seconds=1)},
        state_values("WITHDRAWN") | {"withdrawn_at": SENT_AT - timedelta(seconds=1)},
        state_values("ACCEPTED", True) | {"responded_at": SENT_AT},
        state_values("WITHDRAWN", True) | {"withdrawn_at": SENT_AT},
        state_values("ACCEPTED") | {"withdrawn_at": TERMINAL_AT},
        state_values("DECLINED") | {"withdrawn_at": TERMINAL_AT},
        state_values("WITHDRAWN") | {"responded_at": TERMINAL_AT},
    ],
)
def test_invitation_database_rejects_invalid_state(
    database, invitation_values, changes
):
    with database.begin() as connection:
        table = invitations(connection)
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(table.insert().values(invitation_values | changes))


@pytest.mark.parametrize(
    "message", [None, "", "я" * 2000], ids=["null", "empty", "max"]
)
def test_invitation_optional_message_boundary(database, invitation_values, message):
    with database.begin() as connection:
        table = invitations(connection)
        connection.execute(
            table.insert().values(invitation_values | {"message": message})
        )
        assert connection.scalar(select(table.c.message)) == message


@pytest.mark.parametrize("existing", ["SENT", "VIEWED", "ACCEPTED"])
@pytest.mark.parametrize("incoming", ["SENT", "VIEWED", "ACCEPTED"])
def test_invitation_blocking_pair_is_database_unique(
    database, invitation_values, existing, incoming
):
    with database.begin() as connection:
        table = invitations(connection)
        connection.execute(
            table.insert().values(invitation_values | state_values(existing))
        )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                table.insert().values(
                    invitation_values | state_values(incoming) | {"id": str(uuid4())}
                )
            )


@pytest.mark.parametrize("terminal", ["DECLINED", "WITHDRAWN"])
def test_invitation_reinvitation_retains_history(database, invitation_values, terminal):
    with database.begin() as connection:
        table = invitations(connection)
        for _ in range(2):
            connection.execute(
                table.insert().values(
                    invitation_values | state_values(terminal) | {"id": str(uuid4())}
                )
            )
        connection.execute(table.insert().values(invitation_values))
        assert len(connection.execute(select(table.c.id)).all()) == 3


@pytest.mark.parametrize("target", ["VIEWED", "ACCEPTED", "DECLINED", "WITHDRAWN"])
def test_invitation_direct_transition_timestamps(database, invitation_values, target):
    with database.begin() as connection:
        table = invitations(connection)
        connection.execute(table.insert().values(invitation_values))
        connection.execute(table.update().values(state_values(target)))
        row = connection.execute(select(table)).one()
        assert row.status == target
        assert (row.viewed_at is not None) == (target == "VIEWED")


@pytest.mark.parametrize("target", ["ACCEPTED", "DECLINED", "WITHDRAWN"])
def test_invitation_viewed_transition_keeps_view_time(
    database, invitation_values, target
):
    with database.begin() as connection:
        table = invitations(connection)
        connection.execute(table.insert().values(invitation_values))
        connection.execute(table.update().values(state_values("VIEWED")))
        before = connection.scalar(select(table.c.viewed_at))
        connection.execute(table.update().values(state_values(target, True)))
        assert connection.scalar(select(table.c.viewed_at)) == before


@pytest.mark.parametrize(
    "source", ["SENT", "VIEWED", "ACCEPTED", "DECLINED", "WITHDRAWN"]
)
@pytest.mark.parametrize(
    "target", ["SENT", "VIEWED", "ACCEPTED", "DECLINED", "WITHDRAWN"]
)
def test_invitation_database_transition_matrix(
    database, invitation_values, source, target
):
    allowed = (
        source == target
        or source == "SENT"
        or (source == "VIEWED" and target in {"ACCEPTED", "DECLINED", "WITHDRAWN"})
    )
    with database.begin() as connection:
        table = invitations(connection)
        connection.execute(
            table.insert().values(invitation_values | state_values(source))
        )
        values = state_values(target, source == "VIEWED" and target != "SENT")
        if allowed:
            connection.execute(table.update().values(values))
            assert connection.scalar(select(table.c.status)) == target
        else:
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(table.update().values(values))
            assert connection.scalar(select(table.c.status)) == source


@pytest.mark.parametrize("key", ["need_id", "candidate_id", "employer_id"])
def test_invitation_pair_identity_is_immutable_with_valid_foreign_keys(
    database, db_factory, invitation_values, key
):
    with db_factory() as db:
        if key == "need_id":
            other = EmployerNeed(
                employer_id=invitation_values["employer_id"],
                position_title="Other need",
                specialization="BACKEND",
                required_grade="MIDDLE",
                salary_from=Decimal("0"),
                salary_to=Decimal("0"),
                description="Other need",
            )
        else:
            user = User(
                email="other@example.com",
                password_hash="unused",
                role="CANDIDATE" if key == "candidate_id" else "EMPLOYER",
            )
            db.add(user)
            db.flush()
            if key == "candidate_id":
                other = CandidateProfile(
                    user_id=user.id,
                    first_name="Other",
                    last_name="Candidate",
                    specialization="BACKEND",
                    declared_grade="JUNIOR",
                )
            else:
                other = EmployerProfile(
                    user_id=user.id,
                    company_name="Other",
                    contact_person_name="Other person",
                )
        db.add(other)
        db.commit()
        other_id = other.id
    with database.begin() as connection:
        table = invitations(connection)
        connection.execute(
            table.insert().values(invitation_values | state_values("ACCEPTED"))
        )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(table.update().values({key: other_id}))
        if key != "employer_id":
            # A different Need or Candidate is independently inviteable.
            connection.execute(
                table.insert().values(
                    invitation_values | {"id": str(uuid4()), key: other_id}
                )
            )
            assert len(connection.execute(select(table)).all()) == 2


@pytest.mark.parametrize("terminal", ["ACCEPTED", "DECLINED", "WITHDRAWN"])
def test_invitation_terminal_cannot_reopen_or_be_deleted(
    database, invitation_values, terminal
):
    with database.begin() as connection:
        table = invitations(connection)
        connection.execute(table.insert().values(invitation_values))
        connection.execute(table.update().values(state_values(terminal)))
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(table.update().values(state_values("SENT")))
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(table.delete())
        assert connection.scalar(select(table.c.status)) == terminal


@pytest.mark.parametrize(
    "changes",
    [
        {"message": "rewrite"},
        {"need_snapshot": {"salary_from": "0"}},
        {"candidate_snapshot": {"display_name": "rewrite"}},
        {"sent_at": SENT_AT + timedelta(seconds=1)},
        {"created_at": SENT_AT + timedelta(seconds=1)},
        {"id": str(uuid4())},
    ],
)
def test_invitation_send_time_data_is_immutable(database, invitation_values, changes):
    with database.begin() as connection:
        table = invitations(connection)
        connection.execute(table.insert().values(invitation_values))
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(table.update().values(changes))


def test_invitation_direct_terminal_cannot_manufacture_view(
    database, invitation_values
):
    with database.begin() as connection:
        table = invitations(connection)
        connection.execute(table.insert().values(invitation_values))
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(table.update().values(state_values("ACCEPTED", True)))


def test_invitation_existing_event_times_are_immutable(database, invitation_values):
    with database.begin() as connection:
        table = invitations(connection)
        connection.execute(table.insert().values(invitation_values))
        connection.execute(table.update().values(state_values("VIEWED")))
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(table.update().values(viewed_at=TERMINAL_AT))
        connection.execute(table.update().values(state_values("ACCEPTED", True)))
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                table.update().values(responded_at=TERMINAL_AT + timedelta(seconds=1))
            )


def test_invitation_snapshots_survive_source_edits(db_factory, invitation_values):
    with db_factory() as db:
        db.add(models.Invitation(**invitation_values))
        db.commit()
        need = db.get(EmployerNeed, invitation_values["need_id"])
        need.salary_from = Decimal("0")
        need.status = "CLOSED"
        employer = db.get(EmployerProfile, invitation_values["employer_id"])
        employer.company_name = "Edited company"
        candidate = db.get(CandidateProfile, invitation_values["candidate_id"])
        candidate.first_name = "Edited candidate"
        db.commit()
    with db_factory() as db:
        saved = db.get(models.Invitation, invitation_values["id"])
        assert saved.status == "SENT"
        assert saved.need_snapshot["salary_from"] == "180000.00"
        assert saved.need_snapshot["company_name"] == "Tech"
        assert saved.candidate_snapshot["display_name"] == "Анна И."


@pytest.mark.parametrize(
    "model,key",
    [
        (EmployerNeed, "need_id"),
        (EmployerProfile, "employer_id"),
        (CandidateProfile, "candidate_id"),
    ],
)
def test_invitation_foreign_keys_preserve_history(
    db_factory, invitation_values, model, key
):
    with db_factory() as db:
        db.add(models.Invitation(**invitation_values))
        db.commit()
        with pytest.raises(IntegrityError):
            db.delete(db.get(model, invitation_values[key]))
            db.commit()


def test_invitation_migration_round_trip_preserves_existing_tables(
    database, db_factory, invitation_values
):
    with db_factory() as db:
        seed(db, demo=True, demo_password="migration-test-password")
        candidate = db.scalar(select(CandidateProfile))
        candidate.verified_grade = "MIDDLE"
        candidate.normalized_assessment_score = 73
        candidate.assessment_verified_at = SENT_AT
        db.commit()
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    with database.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "fbce7259afda")
        metadata = MetaData()
        metadata.reflect(bind=connection)
        original_tables = set(metadata.tables)
        assert "invitations" not in original_tables
        before = {
            name: connection.execute(select(table).order_by(*table.primary_key)).all()
            for name, table in metadata.tables.items()
            if name != "alembic_version"
        }
        for target in ("head", "fbce7259afda", "head"):
            if target == "head":
                command.upgrade(config, target)
            else:
                command.downgrade(config, target)
            assert set(inspect(connection).get_table_names()) == original_tables | (
                {"invitations"} if target == "head" else set()
            )
            if target == "head":
                table = invitations(connection)
                connection.execute(table.insert().values(invitation_values))
                with pytest.raises(IntegrityError), connection.begin_nested():
                    connection.execute(table.update().values(message="changed"))
            elif database.dialect.name == "postgresql":
                assert (
                    connection.scalar(
                        text("SELECT to_regprocedure('guard_invitation_lifecycle()')")
                    )
                    is None
                )
            else:
                assert (
                    connection.execute(
                        text(
                            "SELECT name FROM sqlite_master WHERE type = 'trigger' "
                            "AND name LIKE 'invitation_%'"
                        )
                    ).all()
                    == []
                )
            for name, rows in before.items():
                table = metadata.tables[name]
                assert (
                    connection.execute(select(table).order_by(*table.primary_key)).all()
                    == rows
                )
        command.check(config)


@pytest.mark.parametrize("outcome", ["commit", "rollback"])
@pytest.mark.parametrize("first_status", ["SENT", "ACCEPTED"])
def test_invitation_concurrent_send_database_guard(
    database, invitation_values, first_status, outcome
):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL independent concurrent connections")
    inserted = Event()
    contender_started = Event()
    contender_pid = []
    with database.connect() as connection:
        table = invitations(connection)

    def first():
        with database.connect() as connection:
            tx = connection.begin()
            connection.execute(
                table.insert().values(invitation_values | state_values(first_status))
            )
            first_pid = connection.scalar(text("SELECT pg_backend_pid()"))
            inserted.set()
            assert contender_started.wait(10)
            # Prove actual overlap, not just two threads that could run serially.
            deadline = monotonic() + 5
            while not connection.scalar(
                text("SELECT :first = ANY(pg_blocking_pids(:contender))"),
                {"first": first_pid, "contender": contender_pid[0]},
            ):
                assert monotonic() < deadline, (
                    "Second insert did not wait on the unique index"
                )
                sleep(0.01)
            if outcome == "commit":
                tx.commit()
            else:
                tx.rollback()

    def second():
        assert inserted.wait(10)
        try:
            with database.begin() as connection:
                connection.execute(text("SET LOCAL lock_timeout = '10s'"))
                contender_pid.append(connection.scalar(text("SELECT pg_backend_pid()")))
                contender_started.set()
                connection.execute(
                    table.insert().values(invitation_values | {"id": str(uuid4())})
                )
            return "inserted"
        except IntegrityError:
            return "conflict"

    with ThreadPoolExecutor(2) as pool:
        a = pool.submit(first)
        b = pool.submit(second)
        a.result(timeout=20)
        assert b.result(timeout=20) == (
            "conflict" if outcome == "commit" else "inserted"
        )
    with database.connect() as connection:
        assert len(connection.execute(select(table)).all()) == 1


def test_invitation_accept_vs_send_keeps_pair_reserved(database, invitation_values):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL independent concurrent connections")
    with database.begin() as connection:
        table = invitations(connection)
        connection.execute(table.insert().values(invitation_values))
    barrier = Barrier(2)

    def accept():
        with database.begin() as connection:
            connection.execute(text("SET LOCAL lock_timeout = '10s'"))
            connection.execute(select(table).with_for_update()).one()
            barrier.wait(timeout=10)
            connection.execute(table.update().values(state_values("ACCEPTED")))

    def send():
        barrier.wait(timeout=10)
        with pytest.raises(IntegrityError), database.begin() as connection:
            connection.execute(text("SET LOCAL lock_timeout = '10s'"))
            connection.execute(
                table.insert().values(invitation_values | {"id": str(uuid4())})
            )

    with ThreadPoolExecutor(2) as pool:
        a, b = pool.submit(accept), pool.submit(send)
        a.result(timeout=20)
        b.result(timeout=20)
    with database.connect() as connection:
        assert connection.execute(select(table.c.status)).all() == [("ACCEPTED",)]


def test_invitation_concurrent_terminal_updates_have_one_winner(
    database, invitation_values
):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL independent concurrent connections")
    with database.begin() as connection:
        table = invitations(connection)
        connection.execute(table.insert().values(invitation_values))
    barrier = Barrier(2)

    def transition(target):
        try:
            with database.begin() as connection:
                connection.execute(text("SET LOCAL lock_timeout = '10s'"))
                barrier.wait(timeout=10)
                connection.execute(select(table).with_for_update()).one()
                connection.execute(table.update().values(state_values(target)))
            return target
        except IntegrityError:
            return "conflict"

    with ThreadPoolExecutor(2) as pool:
        a, b = pool.submit(transition, "ACCEPTED"), pool.submit(transition, "WITHDRAWN")
        results = [a.result(timeout=20), b.result(timeout=20)]
    assert results.count("conflict") == 1
    winner = next(result for result in results if result != "conflict")
    with database.connect() as connection:
        row = connection.execute(select(table)).one()
        assert row.status == winner
        assert row.viewed_at is None
        assert (row.responded_at is not None) == (winner == "ACCEPTED")
        assert (row.withdrawn_at is not None) == (winner == "WITHDRAWN")
