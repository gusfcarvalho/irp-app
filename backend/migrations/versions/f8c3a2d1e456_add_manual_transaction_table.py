"""add_manual_transaction_table

Revision ID: f8c3a2d1e456
Revises: 005a02569080
Create Date: 2026-04-28 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'f8c3a2d1e456'
down_revision: Union[str, Sequence[str], None] = '005a02569080'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('manualtransaction',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('ticker', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('transaction_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('price', sa.Numeric(), nullable=True),
        sa.Column('ratio_from', sa.Integer(), nullable=True),
        sa.Column('ratio_to', sa.Integer(), nullable=True),
        sa.Column('settlement_fee', sa.Numeric(), nullable=False),
        sa.Column('registration_fee', sa.Numeric(), nullable=False),
        sa.Column('term_fee', sa.Numeric(), nullable=False),
        sa.Column('ana_fee', sa.Numeric(), nullable=False),
        sa.Column('emoluments', sa.Numeric(), nullable=False),
        sa.Column('operational_fee', sa.Numeric(), nullable=False),
        sa.Column('execution', sa.Numeric(), nullable=False),
        sa.Column('custody_fee', sa.Numeric(), nullable=False),
        sa.Column('taxes', sa.Numeric(), nullable=False),
        sa.Column('irrf', sa.Numeric(), nullable=False),
        sa.Column('other_fees', sa.Numeric(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_manualtransaction_ticker'), 'manualtransaction', ['ticker'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_manualtransaction_ticker'), table_name='manualtransaction')
    op.drop_table('manualtransaction')
