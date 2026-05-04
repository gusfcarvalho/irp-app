"""manualtxn_quantity_to_decimal

Revision ID: j2k3l4m5n6o7
Revises: i1j2k3l4m5n6
Create Date: 2026-05-03 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'j2k3l4m5n6o7'
down_revision: Union[str, Sequence[str], None] = 'i1j2k3l4m5n6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('manualtransaction') as batch_op:
        batch_op.alter_column('quantity', type_=sa.Numeric(precision=18, scale=8), existing_nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('manualtransaction') as batch_op:
        batch_op.alter_column('quantity', type_=sa.Integer(), existing_nullable=True)
