"""empty message

Revision ID: a431d98b274c
Revises: 3cc8c5a8323c
Create Date: 2021-01-19 08:43:27.505580

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a431d98b274c"
down_revision = "3cc8c5a8323c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "connection_sftp", sa.Column("key", sa.String(length=8000), nullable=True)
    )
    op.alter_column(
        "connection_sftp",
        "username",
        existing_type=sa.VARCHAR(length=120),
        nullable=True,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "connection_sftp",
        "username",
        existing_type=sa.VARCHAR(length=120),
        nullable=False,
    )
    op.drop_column("connection_sftp", "key")
    # ### end Alembic commands ###