"""
Add firebase_uid column to users table
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_firebase_uid_to_users'
down_revision = None  # You might need to set this to the last migration
branch_labels = None
depends_on = None


def upgrade():
    # Add firebase_uid column to users table
    op.add_column('users', sa.Column('firebase_uid', sa.String(), nullable=True, unique=True, index=True))

    # For existing users, we can't set firebase_uid since we don't have it
    # They will need to re-authenticate or we need to handle this differently
    # For now, we'll leave it nullable and handle in application logic


def downgrade():
    # Remove firebase_uid column from users table
    op.drop_column('users', 'firebase_uid')