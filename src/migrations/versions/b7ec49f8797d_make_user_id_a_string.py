"""make user id a string

Revision ID: b7ec49f8797d
Revises: 33cfec9c9fc5
Create Date: 2025-02-24 14:40:32.044763

"""
from typing import Sequence, Union

import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7ec49f8797d'
down_revision: Union[str, None] = '33cfec9c9fc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'id',
               existing_type=sa.UUID(),
               type_=sqlmodel.sql.sqltypes.AutoString(),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'id',
               existing_type=sqlmodel.sql.sqltypes.AutoString(),
               type_=sa.UUID(),
               existing_nullable=False)
    # ### end Alembic commands ###
