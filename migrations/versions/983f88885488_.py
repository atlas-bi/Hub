"""empty message

Revision ID: 983f88885488
Revises: d3ea7dc4570a
Create Date: 2021-03-03 11:21:04.036925

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "983f88885488"
down_revision = "d3ea7dc4570a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("task", sa.Column("file_gpg", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_task_file_gpg"), "task", ["file_gpg"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_task_file_gpg"), table_name="task")
    op.drop_column("task", "file_gpg")
    # ### end Alembic commands ###
