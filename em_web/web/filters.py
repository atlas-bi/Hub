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
import hashlib
import re
import sys
import time
from pathlib import Path

from flask import Blueprint
from flask import current_app as app
from num2words import num2words

filters_bp = Blueprint("filters_bp", __name__)
sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from scripts.crypto import em_decrypt


@filters_bp.app_template_filter("duration")
def duration(seconds):
    """Convert seconds to hh:mm:ss.

    :param seconds: seconds to convert

    :returns: hh:mm:ss.
    """
    # pylint: disable=unused-argument
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return "%d:%02d:%02d" % (hours, mins, secs)


@filters_bp.app_template_filter("dateHash")
def date_hash(text):
    """Get a hash value of the current date.

    :param text: unused

    :returns: hash of the current datetime.
    """
    # pylint: disable=unused-argument
    my_hash = hashlib.sha256()
    my_hash.update((str(time.time() * 10000)).encode("utf-8"))
    return my_hash.hexdigest()[:10]


@filters_bp.app_template_filter("time")
def to_time(my_num):
    """Zero pad numbers not greater than 9.

    :param my_num: number

    :returns: zero padded number.
    """
    if my_num is None:
        return "*"

    if my_num > 9:
        return my_num

    return str(0) + str(my_num)


@filters_bp.app_template_filter("num_st")
def num_st(my_num):
    """Add pronunciation text after number.

    :param my_num: number

    :returns: number with pronunciation text.
    """
    my_dict = {
        0: "th",
        1: "st",
        2: "nd",
        3: "rd",
        4: "th",
        5: "th",
        6: "th",
        7: "th",
        8: "th",
        9: "th",
    }

    return str(my_num) + my_dict.get(my_num % 10)


@filters_bp.app_template_filter("cron_month")
def cron_month(text):
    """Convert a month number to all full text.

    :param text (str): month number

    :returns: full text of month name.
    """
    my_dict = {
        "1": "January",
        "2": "February",
        "3": "March",
        "4": "April",
        "5": "May",
        "6": "June",
        "7": "July",
        "8": "August",
        "9": "September",
        "10": "October",
        "11": "November",
        "12": "December",
    }
    return my_dict.get(str(text))


@filters_bp.app_template_filter("intv_name")
def intv_name(data):
    """Get interval full spelling.

    :param data:[number, incement]

    where increment is w, d, h, m or s.

    :returns: string of number and spelled out incement.
    """
    (incrememt, period) = data
    my_dict = {"w": "week", "d": "day", "h": "hour", "m": "minute", "s": "second"}
    period = my_dict.get(period)

    if incrememt > 1:
        period = str(incrememt) + " " + period + "s"

    return period


@filters_bp.app_template_filter("cron_week_day")
def cron_week_day(text):
    """Get spelled out day of week from day number.

    :param text (str): day number of week

    :returns: string of week day with full spelling.
    """
    my_dict = {
        "0": "Mondays",
        "1": "Tuesdays",
        "2": "Wednesdays",
        "3": "Thursdays",
        "4": "Fridays",
        "5": "Saturdays",
        "6": "Sundays",
    }
    return my_dict.get(str(text))


@filters_bp.app_template_filter("num_str")
def num_str(num):
    """Convert a number to string.

    :param num (int): number to convert to string

    :returns: string representation of the number
    """
    return num2words(num, to="ordinal")


@filters_bp.app_template_filter("year")
def year(unused_var):
    """Get current year.

    :param none: empty param

    :returns: the current year.
    """
    # pylint: disable=unused-argument
    return datetime.date.today().year


@filters_bp.app_template_filter("datetime_format")
def datetime_format(my_date):
    """Format date string.

    :param my_date (str): stirng to format

    :returns: formatted date string
    """
    return datetime.datetime.strftime(
        my_date,
        "%a, %b %-d, %Y %H:%M:%S.%f",
    )


@filters_bp.app_template_filter("decrypt")
def decrypt(my_string):
    """Decrypt a string.

    :param my_string: string to decrypt.

    :returns: decrypted string.
    """
    return em_decrypt(my_string, app.config["PASS_KEY"])


@filters_bp.app_template_filter("hide_smb_pass")
def hide_smb_pass(my_string):
    """Remove password from smb connection string.

    :param my_string: connection string

    :returns: connection string with password removed.
    """
    return re.sub(r"(?<=\:).+?(?=@)", "password", my_string)


@filters_bp.app_template_filter("clean_path")
def clean_path(my_path):
    """Normalize a path.

    :param my_path: path to cleanup

    :returns: cleanedup path.
    """
    if len(my_path) > 0:
        if my_path[-1] == "/" or my_path[-1] == "\\":
            return my_path
        return my_path + "/"

    return my_path


@filters_bp.app_template_filter("database_pass")
def database_pass(my_string):
    """Hide password in connection strings.

    :param my_string: connection string

    :returns: connection string with hidden password.
    """
    try:
        if "PWD" in my_string:
            my_pass = my_string.split("PWD=")[1]
        elif "password" in my_string:
            my_pass = my_string.split("password=")[1]
        else:
            my_pass = my_string.split("@")[0].split(":")[1]

        return my_string.replace(
            my_pass,
            (
                '<input type="password" class="em-inputPlain" disabled="true" value="'
                + str(my_pass)
                + '" style="width:'
                + str(len(my_pass) * 6)
                + 'px;cursor: text;"/>'
                + '<a class="em-inputPlainCopy" title="copy password" data-value="'
                + str(my_pass)
                + '"><svg viewBox="0 0 448 512" xmlns="http://www.w3.org/2000/svg">'
                + '<path d="M320 448v40c0 13.255-10.745 24-24 24H24c-13.255 0-24-10.745-24-24V12'
                + "0c0-13.255 10.745-24 24-24h72v296c0 30.879 25.121 56 56 56h168zm0-344V0H152c-1"
                + "3.255 0-24 10.745-24 24v368c0 13.255 10.745 24 24 24h272c13.255 0 24-10.745 24"
                + "-24V128H344c-13.2 0-24-10.8-24-24zm120.971-31.029L375.029 7.029A24 24 0 0 0 35"
                + '8.059 0H352v96h96v-6.059a24 24 0 0 0-7.029-16.97z"/></svg></a>'
            ),
        )
    # pylint: disable=broad-except
    except BaseException:
        return my_string
