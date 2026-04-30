"""add_depositary_fee

Revision ID: a1b2c3d4e5f6
Revises: f8c3a2d1e456
Create Date: 2026-04-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f8c3a2d1e456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('upload', sa.Column('depositary_fee', sa.Numeric(), nullable=False, server_default='0'))
    op.add_column('manualtransaction', sa.Column('depositary_fee', sa.Numeric(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('manualtransaction', 'depositary_fee')
    op.drop_column('upload', 'depositary_fee')
