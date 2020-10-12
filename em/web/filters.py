"""
    Jinja template filter functions

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
import hashlib
import time
from num2words import num2words
from em import app
import re
from ..scripts.crypto import em_decrypt


@app.template_filter("dateHash")
def date_hash(text):
    my_hash = hashlib.sha256()
    my_hash.update((str(time.time() * 10000)).encode("utf-8"))
    return my_hash.hexdigest()[:10]


@app.template_filter("time")
def to_time(my_num):
    if my_num is None:
        return "*"

    if my_num > 9:
        return my_num

    else:
        return str(0) + str(my_num)


@app.template_filter("num_st")
def num_st(my_num):
    """Convert a string to all caps."""
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


@app.template_filter("cron_month")
def cron_month(text):
    """Convert a string to all caps."""
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


@app.template_filter("intv_name")
def intv_name(data):
    (incrememt, period) = data
    my_dict = {"w": "week", "d": "day", "h": "hour", "m": "minute", "s": "second"}
    period = my_dict.get(period)

    if incrememt > 1:
        period = str(incrememt) + " " + period + "s"

    """Convert a string to all caps."""

    return period


@app.template_filter("cron_week_day")
def cron_week_day(text):
    """Convert a string to all caps."""
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


@app.template_filter("num_str")
def num_str(num):
    ""
    return num2words(num, to="ordinal")


@app.template_filter("year")
def year(none):
    """ returns current year """
    return datetime.date.today().year


@app.template_filter("datetime_format")
def datetime_format(my_date):
    """ formats date string """
    return datetime.datetime.strftime(
        my_date,
        "%a, %b %-d, %Y %H:%M:%S.%f",
    )


@app.template_filter("decrypt")
def decrypt(my_string):
    """ decrypt string """
    return em_decrypt(my_string)


@app.template_filter("hide_smb_pass")
def hide_smb_pass(my_string):
    """ remove password from smb connection string """
    return re.sub(r"(?<=\:).+?(?=@)", "password", my_string)


@app.template_filter("clean_path")
def clean_path(my_path):
    if len(my_path) > 0:
        if my_path[-1] == "/" or my_path[-1] == "\\":
            return my_path
        else:
            return my_path + "/"

    return my_path


@app.template_filter("smb_server")
def smb_server(my_string):
    try:
        return " (".join(my_string.split("@")[1].split("/")[0].split(",")) + ")"
    except Exception as e:
        # print(str(e))
        return my_string


@app.template_filter("smb_path")
def smb_path(my_string):
    try:
        return "/" + str(my_string.split("/")[1])
    except Exception as e:
        # print(str(e))
        return my_string


@app.template_filter("smb_user")
def smb_user(my_string):
    try:
        return my_string.split(":")[0]
    except Exception as e:
        # print(str(e))
        return my_string


@app.template_filter("smb_pass")
def smb_pass(my_string):
    try:

        my_pass = my_string.split("@")[0].split(":")[1]
        return (
            '<input type="password" class="em-inputPlain" disabled="true" value="'
            + str(my_pass)
            + '" style="width:'
            + str(len(my_pass) * 6)
            + 'px;cursor: text;"/><a class="em-inputPlainCopy" title="copy password" data-value="'
            + str(my_pass)
            + '">'
        )

    except Exception as e:
        # print(str(e))
        return my_string


@app.template_filter("database_pass")
def database_pass(my_string):
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
                + 'px;cursor: text;"/><a class="em-inputPlainCopy" title="copy password" data-value="'
                + str(my_pass)
                + '"><svg viewBox="0 0 448 512" xmlns="http://www.w3.org/2000/svg"><path d="M320 448v40c0 13.255-10.745 24-24 24H24c-13.255 0-24-10.745-24-24V120c0-13.255 10.745-24 24-24h72v296c0 30.879 25.121 56 56 56h168zm0-344V0H152c-13.255 0-24 10.745-24 24v368c0 13.255 10.745 24 24 24h272c13.255 0 24-10.745 24-24V128H344c-13.2 0-24-10.8-24-24zm120.971-31.029L375.029 7.029A24 24 0 0 0 358.059 0H352v96h96v-6.059a24 24 0 0 0-7.029-16.97z"/></svg></a>'
            ),
        )

    except Exception as e:
        # print(str(e))
        return my_string
