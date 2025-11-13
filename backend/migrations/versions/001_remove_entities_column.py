"""Remove entities column from EmbeddingMetadata

Revision ID: 001_remove_entities
Revises: 
Create Date: 2025-11-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_remove_entities'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Remove the old 'entities' column from EmbeddingMetadata table.
    This column was replaced by a separate Entity table with a foreign key relationship.
    """
    # Check if column exists before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('embeddingmetadata')]
    
    if 'entities' in columns:
        op.drop_column('embeddingmetadata', 'entities')
        print("✅ Removed 'entities' column from EmbeddingMetadata table")
    else:
        print("ℹ️  'entities' column does not exist (already removed)")


def downgrade() -> None:
    """
    Re-add the 'entities' column (as JSON/Text) for rollback purposes.
    Note: This won't restore the original data, just the column structure.
    """
    # Re-add the column as TEXT (original was likely JSON)
    op.add_column('embeddingmetadata', sa.Column('entities', sa.Text(), nullable=True))
    print("⚠️  Re-added 'entities' column (data will be empty)")

