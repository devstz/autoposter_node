"""merge heads

Revision ID: 9516266d991b
Revises: 6b0f1c2d1caa, 8b76e2b49a0c
Create Date: 2025-11-09 02:25:29.357602

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9516266d991b'
down_revision: Union[str, Sequence[str], None] = ('6b0f1c2d1caa', '8b76e2b49a0c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
