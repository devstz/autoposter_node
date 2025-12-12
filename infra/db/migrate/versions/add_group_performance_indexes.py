"""Add performance indexes for groups table.

Adds indexes to optimize:
- Sorting by created_at (used in list, list_by_bot, list_bound)
- Filtering and sorting by assigned_bot_id + created_at (list_by_bot)
- Filtering by assigned_bot_id IS NOT NULL + sorting (list_bound)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_group_performance_indexes"
down_revision: Union[str, Sequence[str], None] = "5c2c1883910b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Index for sorting by created_at (used in list, list_by_bot, list_bound)
    # PostgreSQL can use DESC index for ORDER BY ... DESC queries
    op.execute(
        sa.text("CREATE INDEX ix_groups_created_at_desc ON groups (created_at DESC)")
    )
    
    # Composite index for list_by_bot: filtering by assigned_bot_id + sorting by created_at
    op.execute(
        sa.text(
            "CREATE INDEX ix_groups_assigned_bot_id_created_at_desc "
            "ON groups (assigned_bot_id, created_at DESC)"
        )
    )
    
    # Partial index for list_bound: filtering by assigned_bot_id IS NOT NULL + sorting
    op.execute(
        sa.text(
            "CREATE INDEX ix_groups_bound_created_at_desc "
            "ON groups (created_at DESC) "
            "WHERE assigned_bot_id IS NOT NULL"
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text("DROP INDEX IF EXISTS ix_groups_bound_created_at_desc"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_groups_assigned_bot_id_created_at_desc"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_groups_created_at_desc"))

