"""add_quote_table

Revision ID: a1b2c3d4e5f7
Revises: f7a8b9c0d1e2
Create Date: 2026-05-02 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, Sequence[str], None] = 'f7a8b9c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('quote',
        sa.Column('ticker', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('quote_date', sa.Date(), nullable=False),
        sa.Column('close_price', sa.Numeric(), nullable=False),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('ticker', 'quote_date')
    )


def downgrade() -> None:
    op.drop_table('quote')
