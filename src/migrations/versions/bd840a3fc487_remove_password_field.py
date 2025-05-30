"""remove password field

Revision ID: bd840a3fc487
Revises: 29466908bf3e
Create Date: 2025-02-22 18:48:17.575899

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bd840a3fc487'
down_revision: Union[str, None] = '29466908bf3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_tokenblacklist_token', table_name='tokenblacklist')
    op.drop_table('tokenblacklist')
    op.drop_column('user', 'hashed_password')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('hashed_password', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.create_table('tokenblacklist',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('token', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('expires_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='tokenblacklist_pkey')
    )
    op.create_index('ix_tokenblacklist_token', 'tokenblacklist', ['token'], unique=True)
    # ### end Alembic commands ###
