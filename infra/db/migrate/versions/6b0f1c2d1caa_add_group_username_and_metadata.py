"""Add username and metadata refresh timestamp to groups."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6b0f1c2d1caa"
down_revision: Union[str, Sequence[str], None] = "3fdc9c502c69"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "groups",
        sa.Column("username", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "groups",
        sa.Column("metadata_refreshed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("groups", "metadata_refreshed_at")
    op.drop_column("groups", "username")
