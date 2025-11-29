"""add_grantee_id_to_grants

Revision ID: 7bba97fb3b8f
Revises: 796eba200c3f
Create Date: 2025-11-29 12:16:43.650465

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bba97fb3b8f'
down_revision: Union[str, None] = '796eba200c3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add grantee_id column to grants table
    op.add_column('grants', sa.Column('grantee_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_grants_grantee_id'), 'grants', ['grantee_id'], unique=False)
    op.create_foreign_key(
        'fk_grants_grantee_id_users',
        'grants', 'users',
        ['grantee_id'], ['id']
    )


def downgrade() -> None:
    # Remove grantee_id column from grants table
    op.drop_constraint('fk_grants_grantee_id_users', 'grants', type_='foreignkey')
    op.drop_index(op.f('ix_grants_grantee_id'), table_name='grants')
    op.drop_column('grants', 'grantee_id')

