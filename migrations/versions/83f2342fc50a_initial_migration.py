"""Initial Migration

Revision ID: 83f2342fc50a
Revises: 8e560a151136
Create Date: 2024-10-15 19:14:00.633962

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '83f2342fc50a'
down_revision: Union[str, None] = '8e560a151136'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('countryCode', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('users', sa.Column('countryCallingCode', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('users', sa.Column('currency', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('users', sa.Column('inEu', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'inEu')
    op.drop_column('users', 'currency')
    op.drop_column('users', 'countryCallingCode')
    op.drop_column('users', 'countryCode')
    # ### end Alembic commands ###