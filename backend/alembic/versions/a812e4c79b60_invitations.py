"""invitation persistence and lifecycle

Revision ID: a812e4c79b60
Revises: fbce7259afda
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a812e4c79b60"
down_revision: str | Sequence[str] | None = "fbce7259afda"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_type = (
        "json_typeof" if op.get_bind().dialect.name == "postgresql" else "json_type"
    )
    op.create_table(
        "invitations",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("need_id", sa.String(36), nullable=False),
        sa.Column("employer_id", sa.String(36), nullable=False),
        sa.Column("candidate_id", sa.String(36), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "SENT",
                "VIEWED",
                "ACCEPTED",
                "DECLINED",
                "WITHDRAWN",
                name="invitationstatus",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("need_snapshot", sa.JSON(none_as_null=True), nullable=False),
        sa.Column("candidate_snapshot", sa.JSON(none_as_null=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["need_id"], ["employer_needs.id"]),
        sa.ForeignKeyConstraint(["employer_id"], ["employer_profiles.id"]),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            f"{json_type}(need_snapshot) = 'object' AND "
            f"{json_type}(candidate_snapshot) = 'object'",
            name="valid_invitation_snapshots",
        ),
        sa.CheckConstraint(
            "message IS NULL OR length(message) <= 2000",
            name="valid_invitation_message",
        ),
        sa.CheckConstraint(
            "(status = 'SENT' AND viewed_at IS NULL AND responded_at IS NULL "
            "AND withdrawn_at IS NULL) OR "
            "(status = 'VIEWED' AND viewed_at IS NOT NULL AND responded_at IS NULL "
            "AND withdrawn_at IS NULL) OR "
            "(status IN ('ACCEPTED', 'DECLINED') AND responded_at IS NOT NULL "
            "AND withdrawn_at IS NULL) OR "
            "(status = 'WITHDRAWN' AND withdrawn_at IS NOT NULL "
            "AND responded_at IS NULL)",
            name="consistent_invitation_state",
        ),
        sa.CheckConstraint(
            "(viewed_at IS NULL OR viewed_at >= sent_at) AND "
            "(responded_at IS NULL OR responded_at >= sent_at) AND "
            "(withdrawn_at IS NULL OR withdrawn_at >= sent_at) AND "
            "(viewed_at IS NULL OR responded_at IS NULL OR responded_at >= viewed_at) "
            "AND (viewed_at IS NULL OR withdrawn_at IS NULL "
            "OR withdrawn_at >= viewed_at)",
            name="ordered_invitation_timestamps",
        ),
    )
    for name, predicate in (
        ("uq_invitation_active_pair", "status IN ('SENT', 'VIEWED')"),
        ("uq_invitation_blocking_pair", "status IN ('SENT', 'VIEWED', 'ACCEPTED')"),
    ):
        op.create_index(
            name,
            "invitations",
            ["need_id", "candidate_id"],
            unique=True,
            postgresql_where=sa.text(predicate),
            sqlite_where=sa.text(predicate),
        )
    for owner in ("need", "employer", "candidate"):
        op.create_index(
            f"ix_invitation_{owner}_sent",
            "invitations",
            [f"{owner}_id", sa.text("sent_at DESC"), "id"],
        )
    _create_lifecycle_guards()


def _create_lifecycle_guards() -> None:
    # Checks protect each row's state. Triggers protect its history, including
    # immutable snapshots and the permanent ACCEPTED reservation in the index.
    immutable = (
        "id",
        "need_id",
        "employer_id",
        "candidate_id",
        "message",
        "need_snapshot",
        "candidate_snapshot",
        "sent_at",
        "created_at",
    )
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        comparisons = " OR ".join(
            f"NEW.{column}::jsonb IS DISTINCT FROM OLD.{column}::jsonb"
            if column.endswith("snapshot")
            else f"NEW.{column} IS DISTINCT FROM OLD.{column}"
            for column in immutable
        )
        op.execute(
            sa.text(f"""
            CREATE FUNCTION guard_invitation_lifecycle() RETURNS trigger
            LANGUAGE plpgsql AS $$
            BEGIN
                IF TG_OP = 'DELETE' THEN
                    RAISE EXCEPTION 'Invitation history must be retained'
                        USING ERRCODE = '23514';
                END IF;
                IF {comparisons} THEN
                    RAISE EXCEPTION 'Invitation send-time data is immutable'
                        USING ERRCODE = '23514';
                END IF;
                IF NEW.status <> OLD.status AND NOT (
                    (OLD.status = 'SENT' AND NEW.status IN
                        ('VIEWED', 'ACCEPTED', 'DECLINED', 'WITHDRAWN')) OR
                    (OLD.status = 'VIEWED' AND NEW.status IN
                        ('ACCEPTED', 'DECLINED', 'WITHDRAWN'))
                ) THEN
                    RAISE EXCEPTION 'Invalid invitation transition'
                        USING ERRCODE = '23514';
                END IF;
                IF NOT (OLD.status = 'SENT' AND NEW.status = 'VIEWED')
                    AND NEW.viewed_at IS DISTINCT FROM OLD.viewed_at OR
                    OLD.responded_at IS NOT NULL AND
                        NEW.responded_at IS DISTINCT FROM OLD.responded_at OR
                    OLD.withdrawn_at IS NOT NULL AND
                        NEW.withdrawn_at IS DISTINCT FROM OLD.withdrawn_at THEN
                    RAISE EXCEPTION 'Invitation event timestamps are immutable'
                        USING ERRCODE = '23514';
                END IF;
                RETURN NEW;
            END;
            $$
        """)
        )
        op.execute(
            sa.text("""
            CREATE TRIGGER invitation_lifecycle_guard
            BEFORE UPDATE OR DELETE ON invitations
            FOR EACH ROW EXECUTE FUNCTION guard_invitation_lifecycle()
        """)
        )
    elif dialect == "sqlite":
        comparisons = " OR ".join(
            f"NEW.{column} IS NOT OLD.{column}" for column in immutable
        )
        op.execute(
            sa.text(f"""
            CREATE TRIGGER invitation_lifecycle_guard BEFORE UPDATE ON invitations
            BEGIN
                SELECT RAISE(ABORT, 'Invitation send-time data is immutable')
                WHERE {comparisons};
                SELECT RAISE(ABORT, 'Invalid invitation transition')
                WHERE NEW.status <> OLD.status AND NOT (
                    (OLD.status = 'SENT' AND NEW.status IN
                        ('VIEWED', 'ACCEPTED', 'DECLINED', 'WITHDRAWN')) OR
                    (OLD.status = 'VIEWED' AND NEW.status IN
                        ('ACCEPTED', 'DECLINED', 'WITHDRAWN'))
                );
                SELECT RAISE(ABORT, 'Invitation event timestamps are immutable')
                WHERE NOT (OLD.status = 'SENT' AND NEW.status = 'VIEWED')
                    AND NEW.viewed_at IS NOT OLD.viewed_at OR
                    OLD.responded_at IS NOT NULL AND
                        NEW.responded_at IS NOT OLD.responded_at OR
                    OLD.withdrawn_at IS NOT NULL AND
                        NEW.withdrawn_at IS NOT OLD.withdrawn_at;
            END
        """)
        )
        op.execute(
            sa.text("""
            CREATE TRIGGER invitation_history_guard BEFORE DELETE ON invitations
            BEGIN
                SELECT RAISE(ABORT, 'Invitation history must be retained');
            END
        """)
        )
    else:
        raise RuntimeError("Invitation lifecycle requires PostgreSQL or SQLite")


def downgrade() -> None:
    # Dropping the table removes only its indexes, checks and triggers; no
    # existing table is altered and no historical source rows are rewritten.
    op.drop_table("invitations")
    if op.get_bind().dialect.name == "postgresql":
        op.execute(sa.text("DROP FUNCTION guard_invitation_lifecycle()"))
