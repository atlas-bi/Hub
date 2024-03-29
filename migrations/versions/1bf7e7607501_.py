"""empty message

Revision ID: 1bf7e7607501
Revises: 040c7dc467f2
Create Date: 2020-10-02 14:07:29.307928

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1bf7e7607501"
down_revision = "040c7dc467f2"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "project", sa.Column("global_params", sa.String(length=8000), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("project", "global_params")
    # ### end Alembic commands ###
