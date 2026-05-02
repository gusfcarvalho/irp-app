"""rename_quote_date_column

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f7
Create Date: 2026-05-02 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('quote', 'date', new_column_name='quote_date')


def downgrade() -> None:
    op.alter_column('quote', 'quote_date', new_column_name='date')
