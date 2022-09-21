"""empty message

Revision ID: 405d512e10c7
Revises: c7e5824099a9
Create Date: 2021-02-24 08:56:04.274076

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "405d512e10c7"
down_revision = "c7e5824099a9"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("task", sa.Column("file_gpg_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_task_file_gpg_id"), "task", ["file_gpg_id"], unique=False)
    op.create_foreign_key(None, "task", "connection_gpg", ["file_gpg_id"], ["id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "task", type_="foreignkey")
    op.drop_index(op.f("ix_task_file_gpg_id"), table_name="task")
    op.drop_column("task", "file_gpg_id")
    # ### end Alembic commands ###