"""quantity_to_decimal

Revision ID: i1j2k3l4m5n6
Revises: h0i1j2k3l4m5
Create Date: 2026-05-03 11:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'i1j2k3l4m5n6'
down_revision: Union[str, Sequence[str], None] = 'h0i1j2k3l4m5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('transaction') as batch_op:
        batch_op.alter_column('quantity', type_=sa.Numeric(precision=18, scale=8), existing_nullable=False)

    with op.batch_alter_table('position') as batch_op:
        batch_op.alter_column('quantity', type_=sa.Numeric(precision=18, scale=8), existing_nullable=False)
        batch_op.alter_column('manual_quantity', type_=sa.Numeric(precision=18, scale=8), existing_nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('position') as batch_op:
        batch_op.alter_column('manual_quantity', type_=sa.Integer(), existing_nullable=True)
        batch_op.alter_column('quantity', type_=sa.Integer(), existing_nullable=False)

    with op.batch_alter_table('transaction') as batch_op:
        batch_op.alter_column('quantity', type_=sa.Integer(), existing_nullable=False)
