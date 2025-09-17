"""Add ON DELETE CASCADE to businesses.owner_id FK

Revision ID: a1b2c3d4e5f6
Revises: cf24ad97013d
Create Date: 2025-08-26 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'cf24ad97013d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing FK (created in cf24ad97013d) and recreate with ON DELETE CASCADE
    op.drop_constraint('businesses_owner_id_fkey', 'businesses', type_='foreignkey')
    op.create_foreign_key(
        'businesses_owner_id_fkey',
        'businesses',
        'owners',
        ['owner_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    # Revert to FK without ON DELETE CASCADE
    op.drop_constraint('businesses_owner_id_fkey', 'businesses', type_='foreignkey')
    op.create_foreign_key(
        'businesses_owner_id_fkey',
        'businesses',
        'owners',
        ['owner_id'],
        ['id'],
        ondelete=None,
    )


