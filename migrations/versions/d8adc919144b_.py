"""empty message

Revision ID: d8adc919144b
Revises: 7f13e85587a2
Create Date: 2021-01-19 09:06:28.762712

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d8adc919144b"
down_revision = "7f13e85587a2"
branch_labels = None
depends_on = None


def upgrade():
    print("")
    # ### commands auto generated by Alembic - please adjust! ###

    # op.drop_index(
    #     "ix_connection_database_type_id", table_name="connection_database_type"
    # )
    # op.drop_index(
    #     "ix_task_destination_file_type_id", table_name="task_destination_file_type"
    # )
    # op.drop_index("ix_task_processing_type_id", table_name="task_processing_type")
    # op.drop_index("ix_task_source_query_type_id", table_name="task_source_query_type")
    # op.drop_index("ix_task_source_type_id", table_name="task_source_type")
    # op.drop_index("ix_task_status_id", table_name="task_status")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index("ix_task_status_id", "task_status", ["id"], unique=False)
    op.create_index("ix_task_source_type_id", "task_source_type", ["id"], unique=False)
    op.create_index(
        "ix_task_source_query_type_id", "task_source_query_type", ["id"], unique=False
    )
    op.create_index(
        "ix_task_processing_type_id", "task_processing_type", ["id"], unique=False
    )
    op.create_index(
        "ix_task_destination_file_type_id",
        "task_destination_file_type",
        ["id"],
        unique=False,
    )
    op.drop_index(op.f("ix_task_status_id"), table_name="task")
    op.drop_index(op.f("ix_task_source_type_id"), table_name="task")
    op.drop_index(op.f("ix_task_source_query_type_id"), table_name="task")
    op.drop_index(op.f("ix_task_processing_type_id"), table_name="task")
    op.drop_index(op.f("ix_task_destination_file_type_id"), table_name="task")
    op.create_index(
        "ix_connection_database_type_id",
        "connection_database_type",
        ["id"],
        unique=False,
    )
    op.drop_index(
        op.f("ix_connection_database_type_id"), table_name="connection_database"
    )
    # ### end Alembic commands ###
