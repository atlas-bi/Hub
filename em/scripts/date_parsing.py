"""
    use to make a string form data parameters

    allows input of mathematical operations after a python date parameter.

    for example %d-1 = yesterday

    allowed on
        microseconds
        seconds
        minutes
        hours
        days
        weeks
        months
        years

    Extract Management 2.0
    Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

import datetime
import re
from dateutil import relativedelta
from em import db
from .error_print import full_stack
from ..model.model import TaskLog


class DateParsing:
    """ used to convert a modified python strftime to a propert datetime """

    # pylint: disable=too-few-public-methods
    def __init__(self, task, my_string):
        self.my_string = my_string
        self.task = task

    def string_to_date(self):

        """
        list of delta options

        %f Microsecond as a decimal number, zero-padded on the left. 000000, 000001, …, 999999

        %S Second as a zero-padded decimal number. 00, 01, …, 59

        %M Minute as a zero-padded decimal number. 00, 01, …, 59

        %H Hour (24-hour clock) as a zero-padded decimal number. 00, 01, …, 23
        %I Hour (12-hour clock) as a zero-padded decimal number. 01, 02, …, 12

        %a Sun, Mon, …, Sat (en_US);
        %A Sunday, Monday, …, Saturday (en_US);
        %w Weekday as a decimal number, where 0 is Sunday and 6 is Saturday. 0, 1, …, 6
        %d Day of the month as a zero-padded decimal number. 01, 02, …, 31

        %U Week number of the year (Sunday as the first day) as a zero padded decimal number.
            00, 01,..53
        %W Week number of the year (Monday as the first day of the week) as a decimal number.
            0, 01,..53

        """

        try:
            microseconds = 0
            x = re.findall(r"(?<=%f)[+|-]\d+", self.my_string)
            if len(x) > 0:
                microseconds = int(x[0])
                self.my_string = re.sub(r"(?<=%f)[+|-]\d+", "", self.my_string)

            seconds = 0
            x = re.findall(r"(?<=%S)[+|-]\d+", self.my_string)
            if len(x) > 0:
                seconds = int(x[0])
                self.my_string = re.sub("(?<=%S)[+|-]\d+", "", self.my_string)
            minutes = 0
            x = re.findall(r"(?<=%M)[+|-]\d+", self.my_string)
            if len(x) > 0:
                minutes = int(x[0])
                self.my_string = re.sub(r"(?<=%M)[+|-]\d+", "", self.my_string)
            hours = 0
            x = re.findall(r"(?<=%[H|I])[+|-]\d+", self.my_string)
            if len(x) > 0:
                hours = int(x[0])
                self.my_string = re.sub(r"(?<=%[H|I])[+|-]\d+", "", self.my_string)
            days = 0
            x = re.findall(r"(?<=%[a|A|w|d])[+|-]\d+", self.my_string)
            if len(x) > 0:
                days = int(x[0])
                self.my_string = re.sub(r"(?<=%[a|A|w|d])[+|-]\d+", "", self.my_string)

            weeks = 0
            x = re.findall(r"(?<=%[U|W])[+|-]\d+", self.my_string)
            if len(x) > 0:
                weeks = int(x[0])
                self.my_string = re.sub(r"(?<=%[U|W])[+|-]\d+", "", self.my_string)

            months = 0
            x = re.findall(r"(?<=%[b|B|m])[+|-]\d+", self.my_string)
            if len(x) > 0:
                months = int(x[0])
                self.my_string = re.sub(r"(?<=%[b|B|m])[+|-]\d+", "", self.my_string)

            years = 0
            x = re.findall(r"(?<=%[y|Y])[+|-]\d+", self.my_string)
            if len(x) > 0:
                years = int(x[0])
                self.my_string = re.sub(r"(?<=%[y|Y])[+|-]\d+", "", self.my_string)

            my_delta = relativedelta.relativedelta(
                microseconds=microseconds,
                seconds=seconds,
                minutes=minutes,
                hours=hours,
                days=days,
                weeks=weeks,
                months=months,
                years=years,
            )

            # clean up poor formatting in string // for linux
            self.my_string = re.sub(
                r"%(?=[^a-zA-Z])",
                "",
                re.sub(r"%$", "", self.my_string),
            )

            self.my_string = (datetime.datetime.now() + my_delta).strftime(
                self.my_string
            )

        # pylint: disable=bare-except
        except:

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=17,  # date parser
                error=1,
                message="Failed to parse date string.\n" + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()

        return self.my_string
