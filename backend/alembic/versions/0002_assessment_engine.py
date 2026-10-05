"""assessment engine

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Legacy grade alone has no assessment evidence; preserve profiles, reset grade.
    op.execute("UPDATE candidate_profiles SET verified_grade = NULL")
    with op.batch_alter_table("candidate_profiles") as batch:
        batch.add_column(
            sa.Column("normalized_assessment_score", sa.Integer(), nullable=True)
        )
        batch.add_column(
            sa.Column(
                "assessment_verified_at", sa.DateTime(timezone=True), nullable=True
            )
        )
        batch.create_check_constraint(
            "valid_assessment_score", "normalized_assessment_score BETWEEN 0 AND 100"
        )
        batch.create_check_constraint(
            "consistent_verification",
            "(verified_grade IS NULL AND normalized_assessment_score IS NULL "
            "AND assessment_verified_at IS NULL) OR "
            "(verified_grade IS NOT NULL AND normalized_assessment_score IS "
            "NOT NULL AND assessment_verified_at IS NOT NULL)",
        )
    op.create_table(
        "assessment_questions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column(
            "specialization",
            sa.Enum(
                "BACKEND",
                "FRONTEND",
                "DATA_ML",
                name="specialization",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "grade",
            sa.Enum(
                "JUNIOR",
                "MIDDLE",
                "SENIOR",
                name="grade",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("competency", sa.String(length=60), nullable=False),
        sa.Column(
            "difficulty",
            sa.Enum(
                "BASIC",
                "APPLIED",
                "ADVANCED",
                name="difficulty",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(
        "ix_assessment_question_bank",
        "assessment_questions",
        ["specialization", "grade", "is_active"],
        unique=False,
    )
    op.create_table(
        "assessment_options",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("question_id", sa.String(length=36), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["assessment_questions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assessment_options_question_id"),
        "assessment_options",
        ["question_id"],
        unique=False,
    )
    op.create_table(
        "assessment_attempts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column(
            "specialization",
            sa.Enum(
                "BACKEND",
                "FRONTEND",
                "DATA_ML",
                name="specialization",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "target_grade",
            sa.Enum(
                "JUNIOR",
                "MIDDLE",
                "SENIOR",
                name="grade",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "IN_PROGRESS",
                "PASSED",
                "FAILED",
                name="assessmentstatus",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "completion_reason",
            sa.Enum(
                "SUBMITTED",
                "TIMEOUT",
                name="completionreason",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=True,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("normalized_assessment_score", sa.Integer(), nullable=True),
        sa.Column("competency_scores", sa.JSON(), nullable=True),
        sa.CheckConstraint(
            "(status = 'IN_PROGRESS' AND completion_reason IS NULL AND "
            "finished_at IS NULL AND normalized_assessment_score IS NULL AND "
            "competency_scores IS NULL) OR (status <> 'IN_PROGRESS' AND "
            "completion_reason IS NOT NULL AND finished_at IS NOT NULL AND "
            "normalized_assessment_score IS NOT NULL AND competency_scores IS "
            "NOT NULL)",
            name="consistent_attempt_result",
        ),
        sa.CheckConstraint(
            "normalized_assessment_score BETWEEN 0 AND 100", name="valid_attempt_score"
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidate_profiles.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assessment_attempts_candidate_id"),
        "assessment_attempts",
        ["candidate_id"],
        unique=False,
    )
    op.create_index(
        "uq_assessment_active_candidate",
        "assessment_attempts",
        ["candidate_id"],
        unique=True,
        postgresql_where=sa.text("status = 'IN_PROGRESS'"),
        sqlite_where=sa.text("status = 'IN_PROGRESS'"),
    )
    op.create_table(
        "assessment_attempt_questions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("attempt_id", sa.String(length=36), nullable=False),
        sa.Column("question_id", sa.String(length=36), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("option_order", sa.JSON(), nullable=False),
        sa.Column("selected_option_id", sa.String(length=36), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("position BETWEEN 1 AND 20", name="valid_attempt_position"),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["assessment_attempts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["assessment_questions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["selected_option_id"],
            ["assessment_options.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "position", name="uq_attempt_position"),
        sa.UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),
    )
    op.create_index(
        op.f("ix_assessment_attempt_questions_attempt_id"),
        "assessment_attempt_questions",
        ["attempt_id"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        op.f("ix_assessment_attempt_questions_attempt_id"),
        table_name="assessment_attempt_questions",
    )
    op.drop_table("assessment_attempt_questions")
    op.drop_index(
        "uq_assessment_active_candidate",
        table_name="assessment_attempts",
        postgresql_where=sa.text("status = 'IN_PROGRESS'"),
        sqlite_where=sa.text("status = 'IN_PROGRESS'"),
    )
    op.drop_index(
        op.f("ix_assessment_attempts_candidate_id"), table_name="assessment_attempts"
    )
    op.drop_table("assessment_attempts")
    op.drop_index(
        op.f("ix_assessment_options_question_id"), table_name="assessment_options"
    )
    op.drop_table("assessment_options")
    op.drop_index("ix_assessment_question_bank", table_name="assessment_questions")
    op.drop_table("assessment_questions")

    with op.batch_alter_table("candidate_profiles") as batch:
        batch.drop_constraint("consistent_verification", type_="check")
        batch.drop_constraint("valid_assessment_score", type_="check")
        batch.drop_column("assessment_verified_at")
        batch.drop_column("normalized_assessment_score")
