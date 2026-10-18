"""Create data_types, datasets and the link table."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None


def upgrade() -> None:
    op.create_table(
        "data_types",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("content", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("threshold", sa.Integer(), nullable=False),
        sa.Column("case_sensitive", sa.Boolean(), nullable=False),
        sa.CheckConstraint("type IN ('keywords')", name="type_is_known"),
        sa.CheckConstraint("threshold >= 1", name="threshold_at_least_one"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "dataset_data_types",
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("data_type_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["data_type_id"], ["data_types.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("dataset_id", "data_type_id"),
    )
    op.create_index(
        op.f("ix_dataset_data_types_data_type_id"),
        "dataset_data_types",
        ["data_type_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_dataset_data_types_data_type_id"), table_name="dataset_data_types")
    op.drop_table("dataset_data_types")
    op.drop_table("datasets")
    op.drop_table("data_types")
