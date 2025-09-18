"""business email

Revision ID: 75f170313a82
Revises: 2701afe2e4ff
Create Date: 2025-09-18 15:56:05.352161

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75f170313a82'
down_revision: Union[str, Sequence[str], None] = '2701afe2e4ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
