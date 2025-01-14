"""Initial Migration

Revision ID: 4b7ce6376443
Revises: 
Create Date: 2024-10-15 14:14:50.584965

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '4b7ce6376443'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'cards', ['uid'])
    op.create_unique_constraint(None, 'known_ips', ['uid'])
    op.create_unique_constraint(None, 'users', ['uid'])
    op.create_unique_constraint(None, 'verified_emails', ['uid'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'verified_emails', type_='unique')
    op.drop_constraint(None, 'users', type_='unique')
    op.drop_constraint(None, 'known_ips', type_='unique')
    op.drop_constraint(None, 'cards', type_='unique')
    # ### end Alembic commands ###
