"""Add git tracking columns to bots."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "8b76e2b49a0c"
down_revision: Union[str, Sequence[str], None] = "3fdc9c502c69"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "bots",
        sa.Column(
            "tracked_branch",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'main'"),
        ),
    )
    op.add_column(
        "bots",
        sa.Column("current_commit_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "bots",
        sa.Column("latest_available_commit_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "bots",
        sa.Column(
            "commits_behind",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "bots",
        sa.Column("last_update_check_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("bots", "last_update_check_at")
    op.drop_column("bots", "commits_behind")
    op.drop_column("bots", "latest_available_commit_hash")
    op.drop_column("bots", "current_commit_hash")
    op.drop_column("bots", "tracked_branch")
