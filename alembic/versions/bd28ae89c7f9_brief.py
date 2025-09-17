"""brief

Revision ID: bd28ae89c7f9
Revises: 15ba3345f063
Create Date: 2025-08-21 15:09:51.130628

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'bd28ae89c7f9'
down_revision: Union[str, Sequence[str], None] = '15ba3345f063'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make this migration resilient to prior state where webpage_url already exists
    op.execute("ALTER TABLE businesses ADD COLUMN IF NOT EXISTS webpage_url VARCHAR")
    op.execute("ALTER TABLE businesses ADD COLUMN IF NOT EXISTS brief VARCHAR")
    op.execute("ALTER TABLE businesses DROP COLUMN IF EXISTS webpage_link")


def downgrade() -> None:
    """Downgrade schema."""
    # Revert cautiously; only drop if columns exist
    op.execute("ALTER TABLE businesses ADD COLUMN IF NOT EXISTS webpage_link VARCHAR")
    op.execute("ALTER TABLE businesses DROP COLUMN IF EXISTS brief")
    op.execute("ALTER TABLE businesses DROP COLUMN IF EXISTS webpage_url")
