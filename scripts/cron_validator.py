"""Cron expression validation."""

from typing import Optional

from apscheduler.triggers.cron import CronTrigger


class CronValidator:
    """Validate project cron fields with APScheduler's cron parser."""  # noqa: D203

    def __init__(
        self,
        cron: int,
        cron_year: Optional[str],
        cron_month: Optional[str],
        cron_week: Optional[str],
        cron_day: Optional[str],
        cron_week_day: Optional[str],
        cron_hour: Optional[str],
        cron_min: Optional[str],
        cron_sec: Optional[str],
    ) -> None:
        """Store cron form values."""
        self.cron = cron
        self.cron_year = cron_year
        self.cron_month = cron_month
        self.cron_week = cron_week
        self.cron_day = cron_day
        self.cron_week_day = cron_week_day
        self.cron_hour = cron_hour
        self.cron_min = cron_min
        self.cron_sec = cron_sec

    def validate(self) -> None:
        """Raise ValueError when enabled cron fields are invalid."""
        if not self.cron:
            return

        try:
            CronTrigger(
                year=self.cron_year or None,
                month=self.cron_month or None,
                week=self.cron_week or None,
                day=self.cron_day or None,
                day_of_week=self.cron_week_day or None,
                hour=self.cron_hour or None,
                minute=self.cron_min or None,
                second=self.cron_sec or None,
            )
        except ValueError as exc:
            raise ValueError(f"Invalid cron schedule: {exc}") from exc
