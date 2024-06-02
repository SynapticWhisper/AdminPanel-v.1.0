"""2FA field added

Revision ID: 01fdc95a0d95
Revises: b876f004e8a0
Create Date: 2024-06-01 21:03:13.961334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01fdc95a0d95'
down_revision: Union[str, None] = 'b876f004e8a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('two_factor_auth', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'two_factor_auth')
    # ### end Alembic commands ###