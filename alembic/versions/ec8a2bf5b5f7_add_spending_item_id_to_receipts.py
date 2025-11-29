"""add_spending_item_id_to_receipts

Revision ID: ec8a2bf5b5f7
Revises: 7bba97fb3b8f
Create Date: 2025-11-29 12:19:52.606273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec8a2bf5b5f7'
down_revision: Union[str, None] = '7bba97fb3b8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make spending_request_id nullable and remove unique constraint
    op.alter_column('receipts', 'spending_request_id',
                    existing_type=sa.Integer(),
                    nullable=True)
    
    # Drop unique constraint on spending_request_id
    op.drop_constraint('receipts_spending_request_id_key', 'receipts', type_='unique')
    
    # Add spending_item_id column
    op.add_column('receipts', sa.Column('spending_item_id', sa.Integer(), nullable=True))
    
    # Create index for spending_item_id
    op.create_index(op.f('ix_receipts_spending_item_id'), 'receipts', ['spending_item_id'], unique=False)
    
    # Create foreign key for spending_item_id
    op.create_foreign_key(
        'fk_receipts_spending_item_id',
        'receipts', 'spending_items',
        ['spending_item_id'], ['id']
    )


def downgrade() -> None:
    # Remove foreign key and index
    op.drop_constraint('fk_receipts_spending_item_id', 'receipts', type_='foreignkey')
    op.drop_index(op.f('ix_receipts_spending_item_id'), table_name='receipts')
    
    # Remove spending_item_id column
    op.drop_column('receipts', 'spending_item_id')
    
    # Restore unique constraint on spending_request_id
    op.create_unique_constraint('receipts_spending_request_id_key', 'receipts', ['spending_request_id'])
    
    # Make spending_request_id not nullable again
    op.alter_column('receipts', 'spending_request_id',
                    existing_type=sa.Integer(),
                    nullable=False)

