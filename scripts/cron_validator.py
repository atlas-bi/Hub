"""
Cron validation.

Will validate that the values entered into the schedule are valid.
"""

import calendar
import re
from typing import ClassVar, Optional


class CronValidator:
    """Group of functions to make sure each cron field is correct."""

    _cron_days: ClassVar[dict[str, int]] = {
        v.upper(): k for (k, v) in enumerate(calendar.day_abbr)
    }
    _cron_months: ClassVar[dict[str, int]] = {
        v.upper(): k for (k, v) in enumerate(calendar.month_abbr) if k != 0
    }

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
        """Initializes values with this class."""
        self.cron = cron
        self.cron_year = str(cron_year)
        self.cron_month = str(cron_month)
        self.cron_week = str(cron_week)
        self.cron_day = str(cron_day)
        self.cron_week_day = str(cron_week_day)
        self.cron_hour = str(cron_hour)
        self.cron_min = str(cron_min)
        self.cron_sec = str(cron_sec)

    def validate(self) -> None:
        """Main method called to validate the cron values."""
        if self.cron == 1:
            self._month(expr=self.cron_month, prefix="Month")
            self._day_of_month(expr=self.cron_day, prefix="Day")
            self._day_of_week(expr=self.cron_week_day, prefix="Week Day")
            self._number_validate(expr=self.cron_year, prefix="Year", mi=1970, mx=2099, limit=84)
            self._number_validate(expr=self.cron_week, prefix="Week", mi=1, mx=53, limit=53)
            self._number_validate(expr=self.cron_hour, prefix="Hour", mi=0, mx=23, limit=24)
            self._number_validate(expr=self.cron_min, prefix="Minute", mi=0, mx=59, limit=60)
            self._number_validate(expr=self.cron_sec, prefix="Second", mi=0, mx=59, limit=60)

    def _number_validate(self, expr: str, prefix: str, mi: int, mx: int, limit: int) -> None:
        """Validates any records that are number only.

        *
        nn (mi-mx)
        nn-nn
        nn/nn
        nn-nn/nn
        */nn
        nn,nn,nn.
        """
        if expr is None or expr == "" or expr == "*":
            pass
        elif re.match(r"^\d*$", expr):
            self.check_range(expr=expr, mi=mi, mx=mx, prefix=prefix)

        elif re.match(r"^\d*-\d*$", expr):
            parts = expr.split("-")
            self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
            self.check_range(expr=parts[1], mi=mi, mx=mx, prefix=prefix)
            self.compare_range(st=int(parts[0]), ed=int(parts[1]), mi=mi, mx=mx, prefix=prefix)

        elif re.match(r"^\d*/\d*$", expr):
            parts = expr.split("/")
            self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
            self.check_range(type="interval", expr=parts[1], mi=1, mx=mx, prefix=prefix)

        elif re.match(r"^\d*-\d*/\d*$", expr):
            parts = expr.split("/")
            fst_parts = parts[0].split("-")
            self.check_range(expr=fst_parts[0], mi=mi, mx=mx, prefix=prefix)
            self.check_range(expr=fst_parts[1], mi=mi, mx=mx, prefix=prefix)
            self.compare_range(
                st=int(fst_parts[0]), ed=int(fst_parts[1]), mi=mi, mx=mx, prefix=prefix
            )
            self.check_range(type="interval", expr=parts[1], mi=1, mx=mx, prefix=prefix)

        elif re.match(r"^\*/\d*$", expr):
            parts = expr.split("/")
            self.check_range(type="interval", expr=parts[1], mi=1, mx=mx, prefix=prefix)

        elif "," in expr:
            expr_ls = expr.split(",")
            if len(expr_ls) > limit:
                msg = f"({prefix}) Exceeded maximum number({limit}) of specified value. '{len(expr_ls)}' is provided"
                raise ValueError(msg)
            else:
                for n in expr_ls:
                    self._number_validate(expr=n.strip(), prefix=prefix, mi=mi, mx=mx, limit=limit)
        else:
            msg = f"({prefix}) Illegal Expression Format '{expr}'"
            raise ValueError(msg)

    def _day_of_month(self, expr: str, prefix: str) -> None:
        """DAY Of Month expressions (n : Number, s: String).

        *
        nn (1~31)
        nn-nn
        nn/nn
        nn-nn/nn
        */nn
        nn,nn,nn, nth sss, last sss, last (Maximum 31 elements)
        last
        nth sss
        last sss.
        """
        mi, mx = (1, 31)
        if expr is None or expr == "" or expr == "*" or expr.lower() == "last":
            pass
        elif "," in expr:
            limit = 31
            expr_ls = expr.split(",")
            if len(expr_ls) > 31:
                msg = f"({prefix}) Exceeded maximum number({limit}) of specified value. '{len(expr_ls)}' is provided"
                raise ValueError(msg)
            else:
                for dayofmonth in expr_ls:
                    self._day_of_month(expr=dayofmonth.strip(), prefix=prefix)
        # if it is number only then just use _number_validate function
        elif re.match(
            r"^(\*|(\d{1,2})-(\d{1,2})(/(\d{1,2}))?|\*/\d{1,2}|\d{1,2}(/\d{1,2})?)$",
            expr,
        ):
            self._number_validate(expr=expr, prefix=prefix, mi=mi, mx=mx, limit=31)
        elif re.match(r"^[1-5](nd|st|rd|th)\s\D{3}$", expr, re.IGNORECASE):
            parts = expr.split()
            parts[0] = re.sub("[nd|st|rd|th]", "", parts[0])
            try:
                self._cron_days[parts[1].upper()]
            except KeyError:
                msg = f"({prefix}) Invalid value '{expr}'"
                raise ValueError(msg)
            self.check_range(expr=parts[0], mi=mi, mx=5, prefix=prefix)
        elif re.match(r"^last\s\D{3}$", expr, re.IGNORECASE):
            parts = expr.split()
            try:
                self._cron_days[parts[1].upper()]
            except KeyError:
                msg = f"({prefix}) Invalid value '{expr}'"
                raise ValueError(msg)
        else:
            msg = f"({prefix}) Illegal Expression Format '{expr}'"
            raise ValueError(msg)

    def _month(self, expr: str, prefix: str) -> None:
        """Month expressions (n : Number, s: String).

        *
        nn (1~12)
        sss (JAN~DEC)
        nn-nn
        sss-sss
        nn/nn
        nn-nn/nn
        */nn
        nn,nn,nn,nn-nn,sss-sss (Maximum 12 elements).
        """
        mi, mx = (1, 12)
        if expr is None or expr == "" or expr == "*":
            pass
        elif "," in expr:
            """
            get values with a comma and then run each part through months again.
            """
            limit = 12
            expr_ls = expr.split(",")
            if len(expr_ls) > limit:
                msg = f"({prefix}) Exceeded maximum number({limit}) of specified value. '{len(expr_ls)}' is provided"
                raise ValueError(msg)
            else:
                for mon in expr_ls:
                    self._month(expr=mon.strip(), prefix=prefix)
        # if it is number only then just use _number_validate function
        elif re.match(
            r"^(\*|(\d{1,2})-(\d{1,2})(/(\d{1,2}))?|\*/\d{1,2}|\d{1,2}(/\d{1,2})?)$",
            expr,
        ):
            self._number_validate(expr=expr, prefix=prefix, mi=mi, mx=mx, limit=12)
        elif re.match(r"\D{3}$", expr):
            try:
                st_mon = int(self._cron_months[expr.upper()])
            except KeyError:
                msg = f"Invalid Month value '{expr}'"
                raise ValueError(msg)
        elif re.match(r"\D{3}-\D{3}$", expr):
            parts = expr.split("-")
            try:
                st_mon = int(self._cron_months[parts[0].upper()])
                ed_mon = int(self._cron_months[parts[1].upper()])
            except KeyError:
                msg = f"Invalid Month value '{expr}'"
                raise ValueError(msg)
            self.compare_range(
                st=st_mon,
                ed=ed_mon,
                mi=mi,
                mx=mx,
                prefix=prefix,
            )
        else:
            msg = f"({prefix}) Illegal Expression Format '{expr}'"
            raise ValueError(msg)

    def _day_of_week(self, expr: str, prefix: str) -> None:
        """DAYOfWeek expressions (n : Number, s: String).

        *
        n (0~6)
        sss (SUN~SAT)
        n/n
        n-n/n
        */n
        n-n
        sss-sss
        n-n,sss-sss (maximum 7 elements).
        """
        mi, mx = (0, 6)
        if expr is None or expr == "" or expr == "*" or expr.upper() in self._cron_days.keys():
            pass
        elif "," in expr:
            limit = 7
            expr_ls = expr.split(",")

            if len(expr_ls) > limit:
                msg = f"({prefix}) Exceeded maximum number({limit}) of specified value. '{len(expr_ls)}' is provided"
                raise ValueError(msg)
            else:
                for day in expr_ls:
                    self._day_of_week(expr=day.strip(), prefix=prefix)
        # if it is number only then just use _number_validate function
        elif re.match(r"^(\*|(\d{1})-(\d{1})(/(\d{1}))?|\*/\d{1}|\d{1}(/\d{1})?)$", expr):
            self._number_validate(expr=expr, prefix=prefix, mi=mi, mx=mx, limit=7)
        elif re.match(r"\D{3}-\D{3}$", expr):
            parts = expr.split("-")
            try:
                st_day = self._cron_days[parts[0].upper()]
                ed_day = self._cron_days[parts[1].upper()]
            except KeyError:
                msg = f"({prefix}) Invalid value '{expr}'"
                raise ValueError(msg)
            self.compare_range(st=st_day, ed=ed_day, mi=mi, mx=mx, prefix=prefix)
        else:
            msg = f"({prefix}) Illegal Expression Format '{expr}'"
            raise ValueError(msg)

    def check_range(
        self, expr: str, mi: int, mx: int, prefix: str, type: Optional[str] = None
    ) -> None:
        """Check if expression value within range of specified limit."""
        if int(expr) < mi or mx < int(expr):
            if type is None:
                msg = f"{prefix} values must be between {mi} and {mx} but '{expr}' is provided"
            elif type == "interval":
                msg = f"({prefix}) Accepted increment value range is {mi}~{mx} but '{expr}' is provided"
            raise ValueError(msg)

    def compare_range(self, prefix: str, st: int, ed: int, mi: int, mx: int) -> None:
        """Check 2 expression value's size.

        does not allow {st} value to be greater than {ed} value.
        """
        if int(st) > int(ed):
            msg = f"({prefix}) Invalid range '{st}-{ed}'. Accepted range is {mi}-{mx}"
            raise ValueError(msg)
