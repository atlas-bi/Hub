"""empty message

Revision ID: e075a9d31b1a
Revises: 6b8978d637c5
Create Date: 2023-09-18 15:14:26.310892

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e075a9d31b1a'
down_revision = '6b8978d637c5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source_devops', sa.String(length=1000), nullable=True))
        batch_op.add_column(sa.Column('processing_devops', sa.String(length=1000), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.drop_column('processing_devops')
        batch_op.drop_column('source_devops')

    # ### end Alembic commands ###
