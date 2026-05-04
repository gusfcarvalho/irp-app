"""add_tax_payment_table

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-05-01 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, Sequence[str], None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('taxpayment',
        sa.Column('month', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('amount_paid', sa.Numeric(), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint('month')
    )


def downgrade() -> None:
    op.drop_table('taxpayment')
