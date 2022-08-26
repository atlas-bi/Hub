"""empty message

Revision ID: 1759736c94df
Revises: 91f4f1fe4090
Create Date: 2022-06-15 14:50:05.261836

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1759736c94df"
down_revision = "91f4f1fe4090"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "login",
        "login_date",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "project",
        "created",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "project",
        "updated",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
    )
    op.alter_column(
        "task",
        "created",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "task",
        "updated",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
    )
    op.alter_column(
        "task",
        "source_code",
        existing_type=sa.VARCHAR(length=8000),
        type_=sa.Text(),
        existing_nullable=True,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "task",
        "source_code",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=8000),
        existing_nullable=True,
    )
    op.alter_column(
        "task",
        "updated",
        existing_type=sa.DateTime(),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=True,
    )
    op.alter_column(
        "task",
        "created",
        existing_type=sa.DateTime(),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=True,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "project",
        "updated",
        existing_type=sa.DateTime(),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=True,
    )
    op.alter_column(
        "project",
        "created",
        existing_type=sa.DateTime(),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=True,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "login",
        "login_date",
        existing_type=sa.DateTime(),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=True,
        existing_server_default=sa.text("now()"),
    )
    # ### end Alembic commands ###