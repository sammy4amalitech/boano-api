"""make id uuid

Revision ID: 623ef1e66179
Revises: 3ecb4e9492d0
Create Date: 2025-02-12 12:41:10.417355

"""
from typing import Sequence, Union

import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '623ef1e66179'
down_revision: Union[str, None] = '3ecb4e9492d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable the uuid-ossp extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Add a new UUID column
    op.add_column('user', sa.Column('id_new', sqlmodel.sql.sqltypes.GUID(), nullable=False))

    # Populate the new column with UUID values
    op.execute('UPDATE "user" SET id_new = uuid_generate_v4()')

    # Drop the old column
    op.drop_column('user', 'id')

    # Rename the new column to the old column name
    op.alter_column('user', 'id_new', new_column_name='id', existing_type=sqlmodel.sql.sqltypes.GUID(), nullable=False)


def downgrade() -> None:
    # Add a new INTEGER column
    op.add_column('user', sa.Column('id_new', sa.INTEGER(), nullable=False))

    # Populate the new column with integer values (assuming you have a way to map UUIDs back to integers)
    op.execute('UPDATE "user" SET id_new = CAST(SUBSTRING(id::text FROM 1 FOR 8) AS INTEGER)')

    # Drop the UUID column
    op.drop_column('user', 'id')

    # Rename the new column to the old column name
    op.alter_column('user', 'id_new', new_column_name='id', existing_type=sa.INTEGER(), nullable=False)
