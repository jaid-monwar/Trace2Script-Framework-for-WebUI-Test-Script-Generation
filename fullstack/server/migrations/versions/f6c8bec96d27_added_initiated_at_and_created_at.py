from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'f6c8bec96d27'
down_revision: Union[str, Sequence[str], None] = '045d0a2050ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('results', sa.Column('created_at', sa.DateTime(), nullable=False))
    op.add_column('tasks', sa.Column('initiated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('tasks', 'initiated_at')
    op.drop_column('results', 'created_at')
