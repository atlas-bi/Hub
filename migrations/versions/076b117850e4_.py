"""empty message

Revision ID: 076b117850e4
Revises: 1bf7e7607501
Create Date: 2020-10-07 11:21:07.031762

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "076b117850e4"
down_revision = "1bf7e7607501"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "task", sa.Column("processing_command", sa.String(length=1000), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("task", "processing_command")
    # ### end Alembic commands ###
