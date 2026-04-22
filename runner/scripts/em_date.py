"""
Use to make a string form data parameters.

Allows input of mathematical operations after a python date parameter, for example,
%d-1 = yesterday.

Date strings are split on the first recurring parameter and the strings processed
in groups.

For example, %Y-%d-%m_%Y-%d-%m will be processed in two groups of "%Y-%d-%m".

allowed on
    microseconds
    seconds
    minutes
    hours
    days
    weeks
    months
    years
"""

import calendar
import datetime
import re
from collections import Counter

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from typing import List, Optional

from dateutil import relativedelta

from runner.model import Task
from runner.scripts.em_messages import RunnerException


class DateParsing:
    """Used to convert a modified python strftime to a propert datetime."""

    # pylint: disable=too-few-public-methods
    def __init__(self, task: Task, run_id: Optional[str], date_string: str) -> None:
        """Set up the class parameters.

        :param task: task object
        :param date_string: string to parse into a date
        """
        self.date_string = date_string
        self.task = task
        self.run_id = run_id

    @staticmethod
    def get_date_part(my_string: str) -> str:
        """Return the date of the python date string.

        :param my_string: date part to convert

        :returns: string of datepart

        List of delta options:

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

        %m-firstday Will add the month number (01,02...) plus 1 for the first day of month.
        %m-firstday0 Will add the month number (01,02...) plus 1 for the first day of month.

        %m-lastday Will add the month number (01,02...) plus the last day of month in digets.

        Dates parts can also have math performed on them. For example, %d-1 will result in
        yesterdays date.
        """
        microseconds = 0
        offset = re.findall(r"(?<=%f)[+|-]\d+", my_string)
        if len(offset) > 0:
            microseconds = int(offset[0])
            my_string = re.sub(r"(?<=%f)[+|-]\d+", "", my_string)

        seconds = 0
        offset = re.findall(r"(?<=%S)[+|-]\d+", my_string)
        if len(offset) > 0:
            seconds = int(offset[0])
            my_string = re.sub(r"(?<=%S)[+|-]\d+", "", my_string)
        minutes = 0
        offset = re.findall(r"(?<=%M)[+|-]\d+", my_string)
        if len(offset) > 0:
            minutes = int(offset[0])
            my_string = re.sub(r"(?<=%M)[+|-]\d+", "", my_string)
        hours = 0
        offset = re.findall(r"(?<=%[H|I])[+|-]\d+", my_string)
        if len(offset) > 0:
            hours = int(offset[0])
            my_string = re.sub(r"(?<=%[H|I])[+|-]\d+", "", my_string)
        days = 0
        offset = re.findall(r"(?<=%[a|A|w|d])[+|-]\d+", my_string)
        if len(offset) > 0:
            days = int(offset[0])
            my_string = re.sub(r"(?<=%[a|A|w|d])[+|-]\d+", "", my_string)

        weeks = 0
        offset = re.findall(r"(?<=%[U|W])[+|-]\d+", my_string)
        if len(offset) > 0:
            weeks = int(offset[0])
            my_string = re.sub(r"(?<=%[U|W])[+|-]\d+", "", my_string)

        months = 0
        offset = re.findall(r"(?<=%[b|B|m])[+|-]\d+", my_string)
        if len(offset) > 0:
            months = int(offset[0])
            my_string = re.sub(r"(?<=%[b|B|m])[+|-]\d+", "", my_string)

        years = 0
        offset = re.findall(r"(?<=%[y|Y])[+|-]\d+", my_string)
        if len(offset) > 0:
            years = int(offset[0])
            my_string = re.sub(r"(?<=%[y|Y])[+|-]\d+", "", my_string)

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
        my_string = re.sub(
            r"%(?=[^a-zA-Z])",
            "",
            re.sub(r"%$", "", my_string),
        )

        date_from_string = datetime.datetime.now() + my_delta

        my_string = (
            my_string.replace("firstday0", "01")
            .replace("firstday", "1")
            .replace(
                "lastday",
                str(calendar.monthrange(date_from_string.year, date_from_string.month)[1]),
            )
        )

        return (date_from_string).strftime(my_string)

    def string_to_date(self) -> str:
        """Return a complete date string.

        Input string is split into date parts. Each part is individually converted to a
        string. All string parts are then re-joined.
        """

        def get_repeating_part(parts: List[str]) -> Optional[str]:
            """Find and return first duplicate part in array."""
            my_counter: Counter = Counter()
            for part in parts:
                my_counter[part] += 1
                if my_counter[part] > 1:
                    return part

            return None

        try:
            parameters = [x.group() for x in re.finditer(r"%[a-zA-Z]", self.date_string)]

            parts = []
            # split into parts
            param = get_repeating_part(parameters)
            if param:
                date_string = self.date_string
                while param:
                    # split the date string on the first two parameters.
                    # ex: 'file_name','%y%m_stuff','%y%m_otherstuff_%y%m'
                    split_parts = date_string.split(param, 2)

                    # join the first to parts and append them to our part list.
                    parts.append(param.join(split_parts[:2]))

                    # update the date string with our remainder (3rd element in array)
                    date_string = param + split_parts[2]

                    # update remaining parameters
                    parameters = [x.group() for x in re.finditer(r"%[a-zA-Z]", date_string)]
                    param = get_repeating_part(parameters)

                # need to add on the last part, if there are no more duplicate params.
                # pylint: disable=W0120
                else:
                    parts.append(date_string)

            else:
                parts.append(self.date_string)

            self.date_string = ("").join([self.get_date_part(part) for part in parts])
            return self.date_string

        except BaseException as e:
            raise RunnerException(self.task, self.run_id, 17, f"Failed to parse date string.\n{e}")
