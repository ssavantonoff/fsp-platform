"""employer_needs

Revision ID: fbce7259afda
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "fbce7259afda"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "employer_needs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("employer_id", sa.String(length=36), nullable=False),
        sa.Column("position_title", sa.String(length=200), nullable=False),
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
            "required_grade",
            sa.Enum(
                "JUNIOR",
                "MIDDLE",
                "SENIOR",
                name="required_grade",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("target_experience_years", sa.Float(), nullable=True),
        sa.Column("salary_from", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("salary_to", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("additional_requirements", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "ACTIVE",
                "CLOSED",
                name="needstatus",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("salary_from <= salary_to", name="ordered_salary_range"),
        sa.CheckConstraint("salary_from >= 0", name="nonnegative_salary_from"),
        sa.CheckConstraint("salary_to >= 0", name="nonnegative_salary_to"),
        sa.CheckConstraint(
            "target_experience_years IS NULL OR "
            "target_experience_years BETWEEN 0 AND 1.7976931348623157e308",
            name="valid_target_experience",
        ),
        sa.ForeignKeyConstraint(
            ["employer_id"],
            ["employer_profiles.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_employer_needs_employer_id"),
        "employer_needs",
        ["employer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employer_needs_status"), "employer_needs", ["status"], unique=False
    )
    op.create_table(
        "employer_need_skills",
        sa.Column("need_id", sa.String(length=36), nullable=False),
        sa.Column("skill_id", sa.String(length=36), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "MUST_HAVE",
                "NICE_TO_HAVE",
                name="needskillkind",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["need_id"], ["employer_needs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
        ),
        sa.PrimaryKeyConstraint("need_id", "skill_id"),
    )


def downgrade() -> None:
    op.drop_table("employer_need_skills")
    op.drop_index(op.f("ix_employer_needs_status"), table_name="employer_needs")
    op.drop_index(op.f("ix_employer_needs_employer_id"), table_name="employer_needs")
    op.drop_table("employer_needs")
