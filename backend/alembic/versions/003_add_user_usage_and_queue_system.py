"""add user usage and queue system

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_usage table
    op.create_table('user_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('month', sa.String(length=7), nullable=False),
        sa.Column('emails_sent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('emails_received', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('storage_used_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'month', name='uq_user_month_usage')
    )
    
    # Create index for user_id
    op.create_index(op.f('ix_user_usage_user_id'), 'user_usage', ['user_id'], unique=False)
    
    # Fix password_reset_tokens table (add missing columns)
    op.add_column('password_reset_tokens', sa.Column('expires_at', sa.DateTime(), nullable=False))
    op.add_column('password_reset_tokens', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('password_reset_tokens', sa.Column('used_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Drop index
    op.drop_index(op.f('ix_user_usage_user_id'), table_name='user_usage')
    
    # Drop user_usage table
    op.drop_table('user_usage')
    
    # Remove columns from password_reset_tokens
    op.drop_column('password_reset_tokens', 'used_at')
    op.drop_column('password_reset_tokens', 'created_at')
    op.drop_column('password_reset_tokens', 'expires_at')