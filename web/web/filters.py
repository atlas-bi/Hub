"""Custom Jinja template filters used in html."""

import datetime
import hashlib
import re
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

from flask import Blueprint
from flask import current_app as app

filters_bp = Blueprint("filters_bp", __name__)
sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from crypto import em_decrypt


@filters_bp.app_template_filter("duration")
def duration(seconds: int) -> str:
    """Convert seconds to hh:mm:ss."""
    # pylint: disable=unused-argument
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return "%d:%02d:%02d" % (hours, mins, secs)


@filters_bp.app_template_filter("dateHash")
def date_hash(text: str) -> str:
    """Get a hash value of the current date."""
    # pylint: disable=unused-argument
    my_hash = hashlib.sha256()
    my_hash.update((str(time.time() * 10000)).encode("utf-8"))
    return my_hash.hexdigest()[:10]


@filters_bp.app_template_filter("time")
def to_time(my_num: str) -> str:
    """Zero pad numbers not greater than 9."""
    if my_num is None:
        return "*"

    if not isinstance(my_num, int):
        return my_num

    if my_num > 9:
        return my_num

    return str(0) + str(my_num)


@filters_bp.app_template_filter("num_st")
def num_st(my_num: str) -> str:
    """Add pronunciation text after number."""
    if not isinstance(my_num, int):
        return my_num

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

    # special case for 11
    if my_num == 11:
        return "11th"
    return str(my_num) + my_dict.get(my_num % 10)


@filters_bp.app_template_filter("cron_month")
def cron_month(text: str) -> str:
    """Convert a month number to all full text."""
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
    return my_dict.get(str(text), "")


@filters_bp.app_template_filter("intv_name")
def intv_name(data: Tuple[int, str]) -> str:
    """Get interval full spelling.

    where increment is w, d, h, m or s.
    """
    (incrememt, period) = data

    my_dict = {"w": "week", "d": "day", "h": "hour", "m": "minute", "s": "second"}
    period = my_dict.get(period, "")

    if incrememt != 1 and my_dict:
        period = str(incrememt or 0) + " " + period + "s"

    return period


@filters_bp.app_template_filter("cron_week_day")
def cron_week_day(text: str) -> str:
    """Get spelled out day of week from day number."""
    my_dict = {
        "0": "Mondays",
        "1": "Tuesdays",
        "2": "Wednesdays",
        "3": "Thursdays",
        "4": "Fridays",
        "5": "Saturdays",
        "6": "Sundays",
    }
    return my_dict.get(str(text), "")


@filters_bp.app_template_filter("year")
def year(unused_var: None) -> int:
    """Get current year."""
    # pylint: disable=unused-argument
    return datetime.date.today().year


@filters_bp.app_template_filter("datetime_format")
def datetime_format(my_date: str) -> str:
    """Format date string."""
    if isinstance(my_date, datetime.datetime):
        return datetime.datetime.strftime(
            my_date,
            "%a, %b %-d, %Y %H:%M:%S.%f",
        )

    return my_date


@filters_bp.app_template_filter("datetime_format_easy")
def datetime_format_easy(my_date: str) -> str:
    """Format date string."""
    if isinstance(my_date, datetime.datetime):
        return datetime.datetime.strftime(
            my_date,
            "%a, %b %-d, %Y %H:%M",
        )

    return my_date


@filters_bp.app_template_filter("decrypt")
def decrypt(my_string: str) -> str:
    """Decrypt a string."""
    return em_decrypt(my_string, app.config["PASS_KEY"])


@filters_bp.app_template_filter("hide_smb_pass")
def hide_smb_pass(my_string: str) -> str:
    """Remove password from smb connection string."""
    return re.sub(r"(?<=\:).+?(?=@)", "password", my_string)


@filters_bp.app_template_filter("clean_address")
def clean_address(my_address: str) -> str:
    """Normalize a path."""
    if my_address and len(my_address) > 0:
        if my_address[-1] == "/" or my_address[-1] == "\\":
            return my_address[:-1]
        return my_address

    return my_address or ""


@filters_bp.app_template_filter("clean_path")
def clean_path(my_path: str) -> str:
    """Normalize a path."""
    if my_path and len(my_path) > 0:
        if not (my_path[-1] == "/" or my_path[-1] == "\\"):
            my_path = my_path + "/"

        if my_path[0] == "/" or my_path[0] == "\\":
            my_path = my_path[1:]

    return my_path or ""


@filters_bp.app_template_filter("database_pass")
def database_pass(my_string: str) -> str:
    """Hide password in connection strings."""
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
                + '"><span class="icon is-small"><i class="fas fa-copy"></i></span></a>'
            ),
        )
    # pylint: disable=broad-except
    except BaseException:
        return my_string


@filters_bp.app_template_filter("filename")
def filename(file_name: Optional[str], file_ext: Optional[str]) -> str:  # type: ignore[no-untyped-def]
    """Convert newlines to html tag."""
    if file_ext:
        ext = f".{file_ext}"

    else:
        ext = ""

    if file_name is None:
        name = "System generated "

    else:
        name = file_name
    return f"{name}{ext}"
