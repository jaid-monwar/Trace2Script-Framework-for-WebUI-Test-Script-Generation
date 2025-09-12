from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = '42a5870d952e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('username', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('tasks',
    sa.Column('task_name', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('llm_provider', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('llm_model', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('temperature', sa.Float(), nullable=False),
    sa.Column('context_length', sa.Integer(), nullable=False),
    sa.Column('base_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('api_key', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('browser_headless_mode', sa.Boolean(), nullable=False),
    sa.Column('disable_security', sa.Boolean(), nullable=False),
    sa.Column('window_width', sa.Integer(), nullable=False),
    sa.Column('window_height', sa.Integer(), nullable=False),
    sa.Column('instruction', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('search_input_input', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('search_input_action', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('expected_outcome', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('expected_status', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('results',
    sa.Column('result_gif', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('result_json_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
    sa.PrimaryKeyConstraint('task_id')
    )


def downgrade() -> None:
    op.drop_table('results')
    op.drop_table('tasks')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
