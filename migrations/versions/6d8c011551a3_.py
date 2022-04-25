"""empty message

Revision ID: 6d8c011551a3
Revises: 983f88885488
Create Date: 2021-03-03 13:22:36.066763

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6d8c011551a3"
down_revision = "983f88885488"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("connection_gpg", "passphrase")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "connection_gpg",
        sa.Column("passphrase", sa.TEXT(), autoincrement=False, nullable=False),
    )
    # ### end Alembic commands ###