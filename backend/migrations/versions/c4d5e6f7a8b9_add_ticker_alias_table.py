"""add_ticker_alias_table

Revision ID: c4d5e6f7a8b9
Revises: f8c3a2d1e456
Create Date: 2026-04-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5f6', 'f8c3a2d1e456')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tickeralias',
        sa.Column('raw_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('ticker', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('confirmed', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('raw_name')
    )


def downgrade() -> None:
    op.drop_table('tickeralias')
