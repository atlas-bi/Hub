"""Cron schedule descriptions."""

import calendar
from typing import Callable, Optional


class ExpressionDescriptor:
    """Convert project cron fields into a readable description."""

    def __init__(
        self,
        cron_year: Optional[str] = None,
        cron_month: Optional[str] = None,
        cron_week: Optional[str] = None,
        cron_day: Optional[str] = None,
        cron_week_day: Optional[str] = None,
        cron_hour: Optional[str] = "0",
        cron_min: Optional[str] = "0",
        cron_sec: Optional[str] = "0",
    ) -> None:
        """Store normalized cron field values."""
        self.cron_year = self._wildcard(cron_year)
        self.cron_month = self._wildcard(cron_month)
        self.cron_week = self._wildcard(cron_week)
        self.cron_day = self._wildcard(cron_day)
        self.cron_week_day = self._wildcard(cron_week_day)
        self.cron_hour = cron_hour or "0"
        self.cron_min = cron_min or "0"
        self.cron_sec = cron_sec or "0"

    @staticmethod
    def _wildcard(value: Optional[str]) -> str:
        """Return a cron wildcard for blank values."""
        return value or "*"

    def get_full_description(self) -> str:
        """Return a readable schedule description."""
        parts = [f"At {self.format_time(self.cron_hour, self.cron_min, self.cron_sec)}"]

        for label, value, formatter in (
            ("day", self.cron_day, self._format_day),
            ("weekday", self.cron_week_day, self._format_weekday),
            ("month", self.cron_month, self._format_month),
            ("week", self.cron_week, str),
            ("year", self.cron_year, str),
        ):
            if value != "*":
                parts.append(f"{label} {formatter(value)}")

        if len(parts) == 1:
            parts.append("every day")

        return ", ".join(parts)

    def _format_day(self, value: str) -> str:
        """Return a readable day-of-month value."""
        if value.lower().startswith("last"):
            return value
        return self._format_list(value, self._add_suffix)

    def _format_weekday(self, value: str) -> str:
        """Return a readable day-of-week value."""
        return self._format_list(value, self._weekday_name)

    def _format_month(self, value: str) -> str:
        """Return a readable month value."""
        return self._format_list(value, self._month_name)

    def _format_list(self, value: str, formatter: Callable[[str], str]) -> str:
        """Format comma-separated cron values."""
        return ", ".join(formatter(part.strip()) for part in value.split(","))

    @staticmethod
    def _add_suffix(value: str) -> str:
        """Return an ordinal day number when possible."""
        try:
            day = int(value)
        except ValueError:
            return value

        if 10 <= day % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return f"{day}{suffix}"

    @staticmethod
    def _weekday_name(value: str) -> str:
        """Return a weekday name when possible."""
        try:
            return calendar.day_name[int(value)]
        except (IndexError, ValueError):
            pass

        try:
            return calendar.day_name[list(calendar.day_abbr).index(value.title())]
        except ValueError:
            return value

    @staticmethod
    def _month_name(value: str) -> str:
        """Return a month name when possible."""
        try:
            return calendar.month_name[int(value)]
        except (IndexError, ValueError):
            pass

        try:
            return calendar.month_name[list(calendar.month_abbr).index(value.title())]
        except ValueError:
            return value

    @staticmethod
    def format_time(
        hour_expression: str, minute_expression: str, second_expression: str = ""
    ) -> str:
        """Return a formatted time description."""
        hour = int(hour_expression)
        period = "PM" if hour >= 12 else "AM"

        if hour > 12:
            hour -= 12
        elif hour == 0:
            hour = 12

        minute = str(int(minute_expression)).zfill(2)
        second = f":{str(int(second_expression)).zfill(2)}" if second_expression else ""

        return f"{str(hour).zfill(2)}:{minute}{second} {period}"

    def __str__(self) -> str:
        """Return the full description."""
        return self.get_full_description()

    def __repr__(self) -> str:
        """Return the full description."""
        return self.get_full_description()
