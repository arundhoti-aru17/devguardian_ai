"""add workflow run id to incidents

Revision ID: 5999daca20c7
Revises: 1f02a325fc3d
Create Date: 2026-08-14 01:43:46.029441

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5999daca20c7"
down_revision: Union[str, None] = "1f02a325fc3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------
    # Add GitHub workflow run ID
    #
    # Used to identify the exact workflow event and
    # prevent duplicate incident records.
    # -------------------------------------------------

    op.add_column(
        "incidents",
        sa.Column(
            "workflow_run_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_incidents_workflow_run_id"),
        "incidents",
        ["workflow_run_id"],
        unique=False,
    )


def downgrade() -> None:
    # -------------------------------------------------
    # Remove workflow run ID
    # -------------------------------------------------

    op.drop_index(
        op.f("ix_incidents_workflow_run_id"),
        table_name="incidents",
    )

    op.drop_column(
        "incidents",
        "workflow_run_id",
    )