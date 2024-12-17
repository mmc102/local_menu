"""empty message

Revision ID: ff66ee192fd6
Revises: f203e3ffab54
Create Date: 2024-12-17 08:58:15.605258

"""
from typing import Sequence, Union
from datetime import datetime, timezone


from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff66ee192fd6'
down_revision: Union[str, None] = 'f203e3ffab54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('restaurants', sa.Column('url_verified_at', sa.DateTime, default=datetime.now(timezone.utc)))


def downgrade() -> None:
    op.drop_column('restaurants', 'url_verified_at')
