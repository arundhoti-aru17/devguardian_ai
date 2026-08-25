"""add target_file to incidents

Revision ID: 8f3ac2b91d47
Revises: 2b184344a509
Create Date: 2026-08-25 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f3ac2b91d47"
down_revision: Union[str, None] = "2b184344a509"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------
    # M7 — Add target_file
    #
    # Stores which file DevGuardian's fix actually
    # touched, so the dashboard can show real data
    # instead of guessing from fix_description text.
    # -------------------------------------------------

    op.add_column(
        "incidents",
        sa.Column(
            "target_file",
            sa.String(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("incidents", "target_file")