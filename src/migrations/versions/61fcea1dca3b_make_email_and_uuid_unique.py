"""make email and uuid unique

Revision ID: 61fcea1dca3b
Revises: bd840a3fc487
Create Date: 2025-02-22 21:56:17.952914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '61fcea1dca3b'
down_revision: Union[str, None] = 'bd840a3fc487'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_tokenblacklist_token', table_name='tokenblacklist')
    op.drop_table('tokenblacklist')
    op.create_unique_constraint(None, 'user', ['email'])
    op.create_unique_constraint(None, 'user', ['uuid'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='unique')
    op.drop_constraint(None, 'user', type_='unique')
    op.create_table('tokenblacklist',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('token', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('expires_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='tokenblacklist_pkey')
    )
    op.create_index('ix_tokenblacklist_token', 'tokenblacklist', ['token'], unique=True)
    # ### end Alembic commands ###
