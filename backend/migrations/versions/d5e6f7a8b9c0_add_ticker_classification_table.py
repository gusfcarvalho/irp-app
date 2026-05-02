"""add_ticker_classification_table

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-05-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tickerclassification',
        sa.Column('ticker', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('asset_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('ticker')
    )


def downgrade() -> None:
    op.drop_table('tickerclassification')
