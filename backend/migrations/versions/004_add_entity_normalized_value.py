"""Add normalized_value column to Entity

Revision ID: 004_add_entity_normalized_value
Revises: 003_remove_upload_session
Create Date: 2025-12-16 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_add_entity_normalized_value'
down_revision = '003_remove_upload_session'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    from sqlalchemy import inspect
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if 'entity' in tables:
        # Add column if not present
        cols = [c['name'] for c in inspector.get_columns('entity')]
        if 'normalized_value' not in cols:
            op.add_column('entity', sa.Column('normalized_value', sa.Text(), nullable=True))
            # Create an index to speed up lookups by normalized values
            op.create_index(op.f('ix_entity_normalized_value'), 'entity', ['normalized_value'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    from sqlalchemy import inspect
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if 'entity' in tables:
        cols = [c['name'] for c in inspector.get_columns('entity')]
        if 'normalized_value' in cols:
            try:
                op.drop_index(op.f('ix_entity_normalized_value'), table_name='entity')
            except Exception:
                pass
            op.drop_column('entity', 'normalized_value')
