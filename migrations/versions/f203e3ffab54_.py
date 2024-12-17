"""

add a city column to the restaurant tables

Revision ID: f203e3ffab54
Revises: 
Create Date: 2024-12-17 08:44:57.159968

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f203e3ffab54'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Add a new 'city' column to the 'restaurant' table"""
    op.add_column('restaurants', sa.Column('city', sa.String(length=255), nullable=True))
    op.execute("UPDATE restaurants SET city = 'Chattanooga'")


def downgrade() -> None:
    """Drop the 'city' column from the 'restaurant' table"""
    op.drop_column('restaurants', 'city')
