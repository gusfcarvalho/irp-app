"""add_tax_calculation_cache_table

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-05-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, Sequence[str], None] = 'e6f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('taxcalculationcache',
        sa.Column('month', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('report_json', sa.Text(), nullable=False),
        sa.Column('calculated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('month')
    )


def downgrade() -> None:
    op.drop_table('taxcalculationcache')
