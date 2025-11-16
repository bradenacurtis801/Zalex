"""Make DocumentClassification one-to-one with Document

Revision ID: 002_classification_one_to_one
Revises: 001_remove_entities
Create Date: 2025-11-15

This migration:
1. Removes duplicate classifications (keeps only the latest one per document)
2. Adds unique constraint to document_id in documentclassification table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '002_classification_one_to_one'
down_revision = '001_remove_entities'
branch_labels = None
depends_on = None


def upgrade():
    """
    Convert DocumentClassification from one-to-many to one-to-one.
    """
    # Step 1: Remove duplicate classifications, keeping only the latest one per document
    # This query deletes all but the most recent classification for each document
    op.execute(text("""
        DELETE FROM documentclassification
        WHERE id NOT IN (
            SELECT DISTINCT ON (document_id) id
            FROM documentclassification
            ORDER BY document_id, created_at DESC
        )
    """))
    
    # Step 2: Add unique constraint to document_id
    # First, check if constraint already exists
    op.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'documentclassification_document_id_key'
            ) THEN
                ALTER TABLE documentclassification
                ADD CONSTRAINT documentclassification_document_id_key 
                UNIQUE (document_id);
            END IF;
        END $$;
    """))


def downgrade():
    """
    Revert to one-to-many relationship (remove unique constraint).
    """
    # Remove unique constraint
    op.execute(text("""
        ALTER TABLE documentclassification
        DROP CONSTRAINT IF EXISTS documentclassification_document_id_key;
    """))

