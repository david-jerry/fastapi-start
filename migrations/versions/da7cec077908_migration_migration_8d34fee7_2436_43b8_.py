"""Migration - Migration_8d34fee7-2436-43b8-b671-26746625c46a

Revision ID: da7cec077908
Revises: 852bbd6731f0
Create Date: 2024-10-20 09:08:46.881856

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'da7cec077908'
down_revision: Union[str, None] = '852bbd6731f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###