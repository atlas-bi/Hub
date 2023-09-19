"""empty message

Revision ID: 72ea018a5049
Revises: a68731ea75d6
Create Date: 2020-12-23 08:41:09.324169

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "72ea018a5049"
down_revision = "a68731ea75d6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "task_file",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=1000), nullable=True),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("job_id", sa.String(length=1000), nullable=True),
        sa.Column("size", sa.String(length=200), nullable=True),
        sa.Column("path", sa.String(length=1000), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["task.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_task_file_created"), "task_file", ["created"], unique=False
    )
    op.create_index(op.f("ix_task_file_id"), "task_file", ["id"], unique=False)
    op.create_index(
        "ix_task_file_id_task_id_job_id",
        "task_file",
        ["id", "task_id", "job_id"],
        unique=False,
    )
    op.create_index(op.f("ix_task_file_job_id"), "task_file", ["job_id"], unique=False)
    op.create_index(op.f("ix_task_file_name"), "task_file", ["name"], unique=False)
    op.create_index(op.f("ix_task_file_path"), "task_file", ["path"], unique=False)
    op.create_index(op.f("ix_task_file_size"), "task_file", ["size"], unique=False)
    op.create_index(
        op.f("ix_task_file_task_id"), "task_file", ["task_id"], unique=False
    )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    op.drop_index(op.f("ix_task_file_task_id"), table_name="task_file")
    op.drop_index(op.f("ix_task_file_size"), table_name="task_file")
    op.drop_index(op.f("ix_task_file_path"), table_name="task_file")
    op.drop_index(op.f("ix_task_file_name"), table_name="task_file")
    op.drop_index(op.f("ix_task_file_job_id"), table_name="task_file")
    op.drop_index("ix_task_file_id_task_id_job_id", table_name="task_file")
    op.drop_index(op.f("ix_task_file_id"), table_name="task_file")
    op.drop_index(op.f("ix_task_file_created"), table_name="task_file")
    op.drop_table("task_file")
    # ### end Alembic commands ###