"""add incident memory fields

Revision ID: 1f02a325fc3d
Revises: 1632fd8550dc
Create Date: 2026-08-13 11:57:34.726294

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "1f02a325fc3d"
down_revision: Union[str, None] = "1632fd8550dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------
    # M6 — Add incident memory fields
    # -------------------------------------------------

    op.add_column(
        "incidents",
        sa.Column(
            "failure_type",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "incidents",
        sa.Column(
            "root_cause",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "incidents",
        sa.Column(
            "fix_description",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "incidents",
        sa.Column(
            "outcome",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "incidents",
        sa.Column(
            "embedding",
            Vector(384),
            nullable=True,
        ),
    )


def downgrade() -> None:
    # -------------------------------------------------
    # Remove M6 incident memory fields
    # -------------------------------------------------

    op.drop_column("incidents", "embedding")
    op.drop_column("incidents", "outcome")
    op.drop_column("incidents", "fix_description")
    op.drop_column("incidents", "root_cause")
    op.drop_column("incidents", "failure_type")