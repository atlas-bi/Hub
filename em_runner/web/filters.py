"""Custom Jinja template filters used in html."""
# Extract Management 2.0
# Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import datetime

from flask import Blueprint

filters_bp = Blueprint("filters_bp", __name__)


@filters_bp.app_template_filter("year")
def year(none):
    """Get current year.

    :param none: empty param
    :returns: the current year.
    """
    # pylint: disable=unused-argument
    return datetime.date.today().year


@filters_bp.app_template_filter("datetime_format")
def datetime_format(my_date):
    """Format date string.

    :param str my_date: stirng to format
    :returns: formatted date string
    """
    return datetime.datetime.strftime(
        my_date,
        "%a, %b %-d, %Y %H:%M:%S.%f",
    )
