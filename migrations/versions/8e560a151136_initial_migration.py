"""Initial Migration

Revision ID: 8e560a151136
Revises: 3e089000f398
Create Date: 2024-10-15 18:29:13.065401

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '8e560a151136'
down_revision: Union[str, None] = '3e089000f398'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'banned_ips', ['uid'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'banned_ips', type_='unique')
    # ### end Alembic commands ###
