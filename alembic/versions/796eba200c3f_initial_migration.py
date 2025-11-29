"""Initial migration

Revision ID: 796eba200c3f
Revises: 
Create Date: 2025-11-29 10:57:42.898984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '796eba200c3f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types (if not exist)
    op.execute("DO $$ BEGIN CREATE TYPE userrole AS ENUM ('government', 'university', 'grantee'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE grantstate AS ENUM ('active', 'completed', 'cancelled'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE spendingrequeststatus AS ENUM ('pending_university_approval', 'pending_receipt', 'paid', 'rejected', 'blocked'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('role', postgresql.ENUM('government', 'university', 'grantee', name='userrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_role', 'users', ['role'], unique=False)
    
    # Create grants table
    grantstate_enum = postgresql.ENUM('active', 'completed', 'cancelled', name='grantstate', create_type=False)
    op.create_table(
        'grants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('total_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('amount_spent', sa.Numeric(18, 2), nullable=True),
        sa.Column('university_id', sa.Integer(), nullable=False),
        sa.Column('state', grantstate_enum, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['university_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_grants_id', 'grants', ['id'], unique=False)
    op.create_index('ix_grants_state', 'grants', ['state'], unique=False)
    op.create_index('ix_grants_title', 'grants', ['title'], unique=False)
    op.create_index('ix_grants_university_id', 'grants', ['university_id'], unique=False)
    
    # Create spending_items table
    op.create_table(
        'spending_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('grant_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('planned_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('priority_index', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['grant_id'], ['grants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_spending_items_grant_id', 'spending_items', ['grant_id'], unique=False)
    op.create_index('ix_spending_items_id', 'spending_items', ['id'], unique=False)
    op.create_index('ix_spending_items_priority_index', 'spending_items', ['priority_index'], unique=False)
    
    # Create spending_requests table
    spendingrequeststatus_enum = postgresql.ENUM(
        'pending_university_approval', 'pending_receipt', 'paid', 'rejected', 'blocked',
        name='spendingrequeststatus',
        create_type=False
    )
    op.create_table(
        'spending_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('spending_item_id', sa.Integer(), nullable=False),
        sa.Column('grantee_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('status', spendingrequeststatus_enum, nullable=True),
        sa.Column('aml_flags', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('approved_by_university', sa.Integer(), nullable=True),
        sa.Column('paid_tx_hash', sa.String(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['approved_by_university'], ['users.id'], ),
        sa.ForeignKeyConstraint(['grantee_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['spending_item_id'], ['spending_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_spending_requests_grantee_id', 'spending_requests', ['grantee_id'], unique=False)
    op.create_index('ix_spending_requests_id', 'spending_requests', ['id'], unique=False)
    op.create_index('ix_spending_requests_paid_tx_hash', 'spending_requests', ['paid_tx_hash'], unique=False)
    op.create_index('ix_spending_requests_spending_item_id', 'spending_requests', ['spending_item_id'], unique=False)
    op.create_index('ix_spending_requests_status', 'spending_requests', ['status'], unique=False)
    
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('spending_request_id', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('destination', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('external_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['spending_request_id'], ['spending_requests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transactions_id', 'transactions', ['id'], unique=False)
    op.create_index('ix_transactions_spending_request_id', 'transactions', ['spending_request_id'], unique=False)
    op.create_index('ix_transactions_external_id', 'transactions', ['external_id'], unique=False)
    
    # Create receipts table
    op.create_table(
        'receipts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('spending_request_id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['spending_request_id'], ['spending_requests.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('spending_request_id')
    )
    op.create_index('ix_receipts_id', 'receipts', ['id'], unique=False)
    op.create_index('ix_receipts_spending_request_id', 'receipts', ['spending_request_id'], unique=False)
    op.create_index('ix_receipts_verified', 'receipts', ['verified'], unique=False)
    
    # Create smart_contract_operation_logs table
    op.create_table(
        'smart_contract_operation_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(), nullable=False),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('tx_hash', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_smart_contract_operation_logs_id', 'smart_contract_operation_logs', ['id'], unique=False)
    op.create_index('ix_smart_contract_operation_logs_operation_type', 'smart_contract_operation_logs', ['operation_type'], unique=False)
    op.create_index('ix_smart_contract_operation_logs_timestamp', 'smart_contract_operation_logs', ['timestamp'], unique=False)
    op.create_index('ix_smart_contract_operation_logs_tx_hash', 'smart_contract_operation_logs', ['tx_hash'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_smart_contract_operation_logs_tx_hash', table_name='smart_contract_operation_logs')
    op.drop_index('ix_smart_contract_operation_logs_timestamp', table_name='smart_contract_operation_logs')
    op.drop_index('ix_smart_contract_operation_logs_operation_type', table_name='smart_contract_operation_logs')
    op.drop_index('ix_smart_contract_operation_logs_id', table_name='smart_contract_operation_logs')
    op.drop_table('smart_contract_operation_logs')
    op.drop_index('ix_receipts_verified', table_name='receipts')
    op.drop_index('ix_receipts_spending_request_id', table_name='receipts')
    op.drop_index('ix_receipts_id', table_name='receipts')
    op.drop_table('receipts')
    op.drop_index('ix_transactions_external_id', table_name='transactions')
    op.drop_index('ix_transactions_spending_request_id', table_name='transactions')
    op.drop_index('ix_transactions_id', table_name='transactions')
    op.drop_table('transactions')
    op.drop_index('ix_spending_requests_status', table_name='spending_requests')
    op.drop_index('ix_spending_requests_spending_item_id', table_name='spending_requests')
    op.drop_index('ix_spending_requests_paid_tx_hash', table_name='spending_requests')
    op.drop_index('ix_spending_requests_id', table_name='spending_requests')
    op.drop_index('ix_spending_requests_grantee_id', table_name='spending_requests')
    op.drop_table('spending_requests')
    op.drop_index('ix_spending_items_priority_index', table_name='spending_items')
    op.drop_index('ix_spending_items_id', table_name='spending_items')
    op.drop_index('ix_spending_items_grant_id', table_name='spending_items')
    op.drop_table('spending_items')
    op.drop_index('ix_grants_university_id', table_name='grants')
    op.drop_index('ix_grants_title', table_name='grants')
    op.drop_index('ix_grants_state', table_name='grants')
    op.drop_index('ix_grants_id', table_name='grants')
    op.drop_table('grants')
    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    op.execute("DROP TYPE spendingrequeststatus")
    op.execute("DROP TYPE grantstate")
    op.execute("DROP TYPE userrole")

