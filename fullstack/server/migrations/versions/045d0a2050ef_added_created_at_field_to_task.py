from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = '045d0a2050ef'
down_revision: Union[str, Sequence[str], None] = '42a5870d952e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('created_at', sa.DateTime(), nullable=False))


def downgrade() -> None:
    op.drop_column('tasks', 'created_at')