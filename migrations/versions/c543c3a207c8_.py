"""empty message

Revision ID: c543c3a207c8
Revises: c951ce57629c
Create Date: 2021-03-24 14:45:09.500499

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c543c3a207c8"
down_revision = "c951ce57629c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "task",
        sa.Column(
            "destination_file_line_terminator", sa.String(length=10), nullable=True
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("task", "destination_file_line_terminator")
    # ### end Alembic commands ###
