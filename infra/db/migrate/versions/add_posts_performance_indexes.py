"""Add performance indexes for posts table.

Adds indexes to optimize:
- Filtering by distribution_name
- Sorting by created_at
- Filtering and sorting by distribution_name + created_at (list_distribution_posts)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_posts_performance_indexes"
down_revision: Union[str, Sequence[str], None] = "add_group_performance_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Index for filtering by distribution_name
    op.execute(
        sa.text("CREATE INDEX ix_posts_distribution_name ON posts (distribution_name)")
    )
    
    # Index for sorting by created_at
    op.execute(
        sa.text("CREATE INDEX ix_posts_created_at_desc ON posts (created_at DESC)")
    )
    
    # Composite index for list_distribution_posts: filtering by distribution_name + sorting by created_at
    op.execute(
        sa.text(
            "CREATE INDEX ix_posts_distribution_name_created_at_desc "
            "ON posts (distribution_name, created_at DESC)"
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text("DROP INDEX IF EXISTS ix_posts_distribution_name_created_at_desc"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_posts_created_at_desc"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_posts_distribution_name"))

