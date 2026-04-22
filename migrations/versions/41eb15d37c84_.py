"""Allow string cron expressions.

Revision ID: 41eb15d37c84
Revises: e075a9d31b1a
Create Date: 2024-02-13 20:17:23.622449

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "41eb15d37c84"
down_revision = "e075a9d31b1a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Allow cron expression strings in project cron fields."""
    with op.batch_alter_table("project", schema=None) as batch_op:
        for column in CRON_COLUMNS:
            batch_op.alter_column(
                column,
                existing_type=sa.INTEGER(),
                type_=sa.String(length=120),
                existing_nullable=True,
            )


def downgrade() -> None:
    """Restore project cron fields to integer columns."""
    with op.batch_alter_table("project", schema=None) as batch_op:
        for column in reversed(CRON_COLUMNS):
            batch_op.alter_column(
                column,
                existing_type=sa.String(length=120),
                type_=sa.INTEGER(),
                existing_nullable=True,
            )


CRON_COLUMNS = (
    "cron_year",
    "cron_month",
    "cron_week",
    "cron_day",
    "cron_week_day",
    "cron_hour",
    "cron_min",
    "cron_sec",
)
