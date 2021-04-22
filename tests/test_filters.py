# flake8: noqa,
# pylint: skip-file


def test_duration(em_web_authed):
    from em_web.web.filters import duration

    assert duration(30) == "0:00:30"
    assert duration(60) == "0:01:00"
    assert duration(61) == "0:01:01"
    assert duration(3600) == "1:00:00"
    assert duration(3601) == "1:00:01"
    assert duration(3661) == "1:01:01"


def test_date_hash(em_web_authed):
    from em_web.web.filters import date_hash

    assert date_hash("none") is not None


def test_to_time(em_web_authed):
    from em_web.web.filters import to_time

    assert to_time(None) == "*"
    assert to_time(0) == "00"
    assert to_time("0") == "0"
    assert to_time(10) == 10
    assert to_time("10") == "10"


def test_num_st(em_web_authed):
    from em_web.web.filters import num_st

    assert num_st(0) == "0th"
    assert num_st(1) == "1st"
    assert num_st(2) == "2nd"
    assert num_st(3) == "3rd"
    assert num_st(4) == "4th"
    assert num_st(5) == "5th"
    assert num_st(6) == "6th"
    assert num_st(7) == "7th"
    assert num_st(8) == "8th"
    assert num_st(9) == "9th"
    assert num_st(10) == "10th"
    assert num_st(11) == "11th"
    assert num_st(15) == "15th"
    assert num_st(None) == None
    assert num_st("None") == "None"


def test_cron_month(em_web_authed):
    from em_web.web.filters import cron_month

    assert cron_month("1") == "January"
    assert cron_month("2") == "February"
    assert cron_month("3") == "March"
    assert cron_month("4") == "April"
    assert cron_month("5") == "May"
    assert cron_month("6") == "June"
    assert cron_month("7") == "July"
    assert cron_month("8") == "August"
    assert cron_month("9") == "September"
    assert cron_month("10") == "October"
    assert cron_month("11") == "November"
    assert cron_month("12") == "December"
    assert cron_month("13") == None


def test_intv_name(em_web_authed):
    from em_web.web.filters import intv_name

    assert intv_name((1, "w")) == "week"
    assert intv_name((1, "d")) == "day"
    assert intv_name((1, "h")) == "hour"
    assert intv_name((1, "m")) == "minute"
    assert intv_name((1, "s")) == "second"
    assert intv_name((1, "joe")) == None
    assert intv_name((1, 10)) == None


def test_num_str(em_web_authed):
    from em_web.web.filters import num_str

    assert num_str(1) == "first"
    assert num_str(2) == "second"
    assert num_str(12) == "twelfth"
    assert num_str("12") == "twelfth"
    assert num_str("this") == "this"


def test_datetime_format(em_web_authed):
    from em_web.web.filters import datetime_format

    assert datetime_format("nothing") == "nothing"


def test_hide_smb_pass(em_web_authed):
    from em_web.web.filters import hide_smb_pass

    assert hide_smb_pass(":asdf@") == ":password@"
    assert hide_smb_pass("blah") == "blah"


def test_clean_path(em_web_authed):
    from em_web.web.filters import clean_path

    assert clean_path("") == ""


def test_database_pass(em_web_authed):
    from em_web.web.filters import database_pass

    assert database_pass("PWD=asdf") is not None
    assert database_pass("password=asdf") is not None
