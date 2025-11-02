"""Add distribution metadata fields to posts."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3fdc9c502c69"
down_revision: Union[str, Sequence[str], None] = "d9b8149e55f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "posts",
        sa.Column("distribution_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "posts",
        sa.Column(
            "notify_on_failure",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("posts", "notify_on_failure")
    op.drop_column("posts", "distribution_name")
