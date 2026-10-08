"""Server-owned verified FSP evidence.

Revision ID: c3d9b7e21a40
Revises: a812e4c79b60
"""

import sqlalchemy as sa

from alembic import op

revision = "c3d9b7e21a40"
down_revision = "a812e4c79b60"
branch_labels = None
depends_on = None

CONSISTENCY = (
    "(fsp_verified_id IS NULL AND fsp_verified_at IS NULL "
    "AND fsp_synced_at IS NULL) OR "
    "(fsp_verified_id IS NOT NULL AND fsp_id IS NOT NULL AND fsp_verified_id = fsp_id "
    "AND fsp_verified_at IS NOT NULL AND fsp_synced_at IS NOT NULL "
    "AND fsp_synced_at >= fsp_verified_at)"
)


def upgrade() -> None:
    op.add_column("candidate_profiles", sa.Column("fsp_verified_id", sa.String(200)))
    op.add_column(
        "candidate_profiles", sa.Column("fsp_verified_at", sa.DateTime(timezone=True))
    )
    # Inline check allows SQLite ADD COLUMN without rebuilding a referenced table.
    op.add_column(
        "candidate_profiles",
        sa.Column(
            "fsp_synced_at",
            sa.DateTime(timezone=True),
            sa.CheckConstraint(CONSISTENCY, name="consistent_fsp_verification"),
        ),
    )
    op.create_index(
        "uq_candidate_verified_fsp_id",
        "candidate_profiles",
        ["fsp_verified_id"],
        unique=True,
    )
    op.create_table(
        "fsp_achievements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("candidate_id", sa.String(36), nullable=False),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("competition_id", sa.String(200), nullable=False),
        sa.Column("competition_name", sa.String(500), nullable=False),
        sa.Column("discipline", sa.String(200), nullable=False),
        sa.Column("year", sa.Integer()),
        sa.Column("event_date", sa.DateTime(timezone=True)),
        sa.Column(
            "result_level",
            sa.Enum(
                "PARTICIPANT",
                "FINALIST",
                "PRIZE_WINNER",
                "WINNER",
                name="fspresultlevel",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("placement", sa.Integer()),
        sa.Column(
            "scope",
            sa.Enum(
                "INDIVIDUAL",
                "TEAM",
                name="fspscope",
                native_enum=False,
                create_constraint=True,
            ),
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("candidate_id", "external_id", name="uq_fsp_achievement"),
        sa.CheckConstraint(
            "placement IS NULL OR placement > 0", name="valid_fsp_placement"
        ),
        sa.CheckConstraint(
            "year IS NULL OR year BETWEEN 1 AND 9999", name="valid_fsp_year"
        ),
    )
    op.create_index(
        "ix_fsp_achievements_candidate_id", "fsp_achievements", ["candidate_id"]
    )


def downgrade() -> None:
    op.drop_table("fsp_achievements")
    op.drop_index("uq_candidate_verified_fsp_id", table_name="candidate_profiles")
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint(
            "consistent_fsp_verification", "candidate_profiles", type_="check"
        )
    # On SQLite the inline column check disappears with its owning column.
    op.drop_column("candidate_profiles", "fsp_synced_at")
    op.drop_column("candidate_profiles", "fsp_verified_at")
    op.drop_column("candidate_profiles", "fsp_verified_id")
