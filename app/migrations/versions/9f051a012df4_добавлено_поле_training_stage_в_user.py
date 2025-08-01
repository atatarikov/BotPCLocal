"""Добавлено поле training_stage в User

Revision ID: 9f051a012df4
Revises:
Create Date: 2025-07-30 19:21:56.439189

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f051a012df4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('training_stage', sa.Integer(), nullable=False, server_default='0'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('training_stage')

    # ### end Alembic commands ###
