"""add business email column

Revision ID: 9b2d7f5a0c1e
Revises: 75f170313a82
Create Date: 2025-09-18 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b2d7f5a0c1e'
down_revision: Union[str, Sequence[str], None] = '75f170313a82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('businesses', sa.Column('email', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('businesses', 'email')


