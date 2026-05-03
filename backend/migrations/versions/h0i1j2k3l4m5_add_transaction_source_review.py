"""add_transaction_source_review

Revision ID: h0i1j2k3l4m5
Revises: f8c3a2d1e456
Create Date: 2026-05-03 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'h0i1j2k3l4m5'
down_revision: Union[str, Sequence[str], None] = ('f8c3a2d1e456', 'b2c3d4e5f6a7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('transaction', sa.Column('source', sa.String(), nullable=False, server_default='NOTA'))
    op.add_column('transaction', sa.Column('needs_review', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('transaction', 'needs_review')
    op.drop_column('transaction', 'source')
