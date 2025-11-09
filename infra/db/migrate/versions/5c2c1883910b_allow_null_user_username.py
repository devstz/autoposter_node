"""Allow nullable usernames for Telegram users without @handles."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5c2c1883910b"
down_revision: Union[str, Sequence[str], None] = "9516266d991b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "users",
        "username",
        existing_type=sa.String(length=50),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text(
            "UPDATE users "
            "SET username = CONCAT('user_', user_id) "
            "WHERE username IS NULL"
        )
    )
    op.alter_column(
        "users",
        "username",
        existing_type=sa.String(length=50),
        nullable=False,
    )
