"""email

Revision ID: db6f90448b7d
Revises: 9b2d7f5a0c1e
Create Date: 2025-09-18 15:59:16.010934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db6f90448b7d'
down_revision: Union[str, Sequence[str], None] = '9b2d7f5a0c1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
