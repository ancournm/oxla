"""add drive service models

Revision ID: 004
Revises: 003
Create Date: 2024-01-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create drive_files table
    op.create_table('drive_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('folder_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('original_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('virus_scan_status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['folder_id'], ['drive_folders.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create drive_folders table
    op.create_table('drive_folders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('path', sa.String(length=1000), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['drive_folders.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create drive_shares table
    op.create_table('drive_shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.Column('share_token', sa.String(length=64), nullable=False),
        sa.Column('share_type', sa.String(length=20), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('accessed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['file_id'], ['drive_files.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('share_token')
    )
    
    # Create indexes
    op.create_index(op.f('ix_drive_files_file_id'), 'drive_shares', ['file_id'], unique=False)
    op.create_index(op.f('ix_drive_files_folder_id'), 'drive_files', ['folder_id'], unique=False)
    op.create_index(op.f('ix_drive_files_user_id'), 'drive_files', ['user_id'], unique=False)
    op.create_index(op.f('ix_drive_folders_parent_id'), 'drive_folders', ['parent_id'], unique=False)
    op.create_index(op.f('ix_drive_folders_user_id'), 'drive_folders', ['user_id'], unique=False)
    op.create_index(op.f('ix_drive_shares_file_id'), 'drive_shares', ['file_id'], unique=False)
    op.create_index(op.f('ix_drive_shares_share_token'), 'drive_shares', ['share_token'], unique=True)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_drive_shares_share_token'), table_name='drive_shares')
    op.drop_index(op.f('ix_drive_shares_file_id'), table_name='drive_shares')
    op.drop_index(op.f('ix_drive_folders_user_id'), table_name='drive_folders')
    op.drop_index(op.f('ix_drive_folders_parent_id'), table_name='drive_folders')
    op.drop_index(op.f('ix_drive_files_user_id'), table_name='drive_files')
    op.drop_index(op.f('ix_drive_files_folder_id'), table_name='drive_files')
    op.drop_index(op.f('ix_drive_files_file_id'), table_name='drive_shares')
    
    # Drop tables
    op.drop_table('drive_shares')
    op.drop_table('drive_folders')
    op.drop_table('drive_files')