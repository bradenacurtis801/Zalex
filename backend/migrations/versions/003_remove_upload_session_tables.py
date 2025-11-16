"""Remove UploadSession and UploadSessionFile tables

Revision ID: 003_remove_upload_session
Revises: 002_classification_one_to_one
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_remove_upload_session'
down_revision = '002_classification_one_to_one'  # Must match the revision ID from 002 migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop UploadSession and UploadSessionFile tables."""
    # Check if tables exist before dropping
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    
    # Drop foreign key constraints first (if tables exist)
    if 'uploadsessionfile' in tables:
        # Try to drop constraints, ignore if they don't exist
        try:
            op.drop_constraint('uploadsessionfile_session_id_fkey', 'uploadsessionfile', type_='foreignkey')
        except Exception:
            pass
        try:
            op.drop_constraint('uploadsessionfile_document_id_fkey', 'uploadsessionfile', type_='foreignkey')
        except Exception:
            pass
    
    if 'uploadsession' in tables:
        try:
            op.drop_constraint('uploadsession_user_id_fkey', 'uploadsession', type_='foreignkey')
        except Exception:
            pass
    
    # Drop the tables if they exist
    if 'uploadsessionfile' in tables:
        op.drop_table('uploadsessionfile')
    
    if 'uploadsession' in tables:
        op.drop_table('uploadsession')
    
    # Drop the enum type if it exists (PostgreSQL specific)
    # Use IF EXISTS to avoid errors if enum doesn't exist
    op.execute("DROP TYPE IF EXISTS uploadsessionstatus")


def downgrade() -> None:
    """Recreate UploadSession and UploadSessionFile tables."""
    # Recreate the enum type
    upload_session_status = postgresql.ENUM('active', 'completed', 'failed', 'expired', name='uploadsessionstatus', create_type=False)
    upload_session_status.create(op.get_bind(), checkfirst=True)
    
    # Recreate uploadsession table
    op.create_table(
        'uploadsession',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(length=100), nullable=False),
        sa.Column('status', upload_session_status, nullable=True),
        sa.Column('total_files', sa.Integer(), nullable=False),
        sa.Column('processed_files', sa.Integer(), nullable=False),
        sa.Column('current_file', sa.String(length=500), nullable=True),
        sa.Column('progress_percent', sa.Float(), nullable=True),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_uploadsession_client_id'), 'uploadsession', ['client_id'], unique=True)
    
    # Recreate uploadsessionfile table
    op.create_table(
        'uploadsessionfile',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('file_hash', sa.String(length=64), nullable=True),
        sa.Column('document_id', sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['document.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['uploadsession.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

