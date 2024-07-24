"""Test date.

run with::

   poetry run pytest runner/tests/test_scripts_date.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest runner/tests/test_scripts_date.py::test_complex_patterns \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings

"""

import calendar
import datetime

from dateutil import relativedelta
from pytest import fixture

from runner.model import Task
from runner.scripts.em_date import DateParsing

from .conftest import create_demo_task


def test_date_parsing(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, None, "%d").string_to_date()

    assert my_date_string == datetime.datetime.now().strftime("%d")


def test_date_parsing_microseconds(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, None, "%f").string_to_date()

    assert len(my_date_string) == 6

    my_date_string = DateParsing(task, None, "%f-1").string_to_date()

    assert len(my_date_string) == 6

    my_date_string = DateParsing(task, None, "%f+1").string_to_date()

    assert len(my_date_string) == 6


def test_date_parsing_seconds(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, None, "%S").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%S")

    my_date_string = DateParsing(task, None, "%S-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(seconds=-1)
    ).strftime("%S")

    my_date_string = DateParsing(task, None, "%S-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(seconds=-100)
    ).strftime("%S")

    my_date_string = DateParsing(task, None, "%S+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(seconds=10)
    ).strftime("%S")


def test_date_parsing_minutes(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, None, "%M").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%M")

    my_date_string = DateParsing(task, None, "%M-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(minutes=-1)
    ).strftime("%M")

    my_date_string = DateParsing(task, None, "%M-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(minutes=-100)
    ).strftime("%M")

    my_date_string = DateParsing(task, None, "%M+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(minutes=10)
    ).strftime("%M")


def test_date_parsing_hours(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, None, "%H").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%H")

    my_date_string = DateParsing(task, None, "%H-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(hours=-1)
    ).strftime("%H")

    my_date_string = DateParsing(task, None, "%H-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(hours=-100)
    ).strftime("%H")

    my_date_string = DateParsing(task, None, "%H+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(hours=10)
    ).strftime("%H")

    my_date_string = DateParsing(task, None, "%I").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%I")

    my_date_string = DateParsing(task, None, "%I-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(hours=-1)
    ).strftime("%I")

    my_date_string = DateParsing(task, None, "%I-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(hours=-100)
    ).strftime("%I")

    my_date_string = DateParsing(task, None, "%I+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(hours=10)
    ).strftime("%I")


def test_date_parsing_days(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, None, "%a").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%a")

    my_date_string = DateParsing(task, None, "%a-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-1)
    ).strftime("%a")

    my_date_string = DateParsing(task, None, "%a-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-100)
    ).strftime("%a")

    my_date_string = DateParsing(task, None, "%a+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=10)
    ).strftime("%a")

    my_date_string = DateParsing(task, None, "%A").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%A")

    my_date_string = DateParsing(task, None, "%A-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-1)
    ).strftime("%A")

    my_date_string = DateParsing(task, None, "%A-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-100)
    ).strftime("%A")

    my_date_string = DateParsing(task, None, "%A+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=10)
    ).strftime("%A")

    my_date_string = DateParsing(task, None, "%w").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%w")

    my_date_string = DateParsing(task, None, "%w-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-1)
    ).strftime("%w")

    my_date_string = DateParsing(task, None, "%w-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-100)
    ).strftime("%w")

    my_date_string = DateParsing(task, None, "%w+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=10)
    ).strftime("%w")

    my_date_string = DateParsing(task, None, "%d").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%d")

    my_date_string = DateParsing(task, None, "%d-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-1)
    ).strftime("%d")

    my_date_string = DateParsing(task, None, "%d-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-100)
    ).strftime("%d")

    my_date_string = DateParsing(task, None, "%d+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=10)
    ).strftime("%d")


def test_date_parsing_weeks(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, None, "%U").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%U")

    my_date_string = DateParsing(task, None, "%U-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(weeks=-1)
    ).strftime("%U")

    my_date_string = DateParsing(task, None, "%U-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(weeks=-100)
    ).strftime("%U")

    my_date_string = DateParsing(task, None, "%U+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(weeks=10)
    ).strftime("%U")

    my_date_string = DateParsing(task, None, "%W").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%W")

    my_date_string = DateParsing(task, None, "%W-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(weeks=-1)
    ).strftime("%W")

    my_date_string = DateParsing(task, None, "%W-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(weeks=-100)
    ).strftime("%W")

    my_date_string = DateParsing(task, None, "%W+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(weeks=10)
    ).strftime("%W")


def test_date_parsing_months(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, None, "%b").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%b")

    my_date_string = DateParsing(task, None, "%b-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=-1)
    ).strftime("%b")

    my_date_string = DateParsing(task, None, "%b-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=-100)
    ).strftime("%b")

    my_date_string = DateParsing(task, None, "%b+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=10)
    ).strftime("%b")

    my_date_string = DateParsing(task, None, "%B").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%B")

    my_date_string = DateParsing(task, None, "%B-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=-1)
    ).strftime("%B")

    my_date_string = DateParsing(task, None, "%B-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=-100)
    ).strftime("%B")

    my_date_string = DateParsing(task, None, "%B+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=10)
    ).strftime("%B")

    my_date_string = DateParsing(task, None, "%m").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%m")

    my_date_string = DateParsing(task, None, "%m-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=-1)
    ).strftime("%m")

    my_date_string = DateParsing(task, None, "%m-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=-100)
    ).strftime("%m")

    my_date_string = DateParsing(task, None, "%m+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=10)
    ).strftime("%m")


def test_date_parsing_years(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, None, "%y").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%y")

    my_date_string = DateParsing(task, None, "%y-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(years=-1)
    ).strftime("%y")

    my_date_string = DateParsing(task, None, "%y-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(years=-100)
    ).strftime("%y")

    my_date_string = DateParsing(task, None, "%y+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(years=10)
    ).strftime("%y")

    my_date_string = DateParsing(task, None, "%Y").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%Y")

    my_date_string = DateParsing(task, None, "%Y-1").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(years=-1)
    ).strftime("%Y")

    my_date_string = DateParsing(task, None, "%Y-100").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(years=-100)
    ).strftime("%Y")

    my_date_string = DateParsing(task, None, "%Y+10").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(years=10)
    ).strftime("%Y")


def test_date_parsing_firsday(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, None, "firstday").string_to_date()

    assert my_date_string == "1"


def test_date_parsing_firstday_zero(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, None, "firstday0").string_to_date()

    assert my_date_string == "01"


def test_date_parsing_lastday(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, None, "lastday").string_to_date()

    last_day = calendar.monthrange(
        int(datetime.datetime.now().strftime("%Y")),
        int(datetime.datetime.now().strftime("%m")),
    )[1]
    assert my_date_string == str(last_day)


def test_complex_patterns(client_fixture: fixture) -> None:
    _, t_id = create_demo_task()
    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, None, "%m-6-%d-30-%Y+1-lastday").string_to_date()

    new_date = datetime.datetime.now() + relativedelta.relativedelta(months=-6, days=-30, years=1)

    last_day = calendar.monthrange(
        int(new_date.strftime("%Y")),
        int(new_date.strftime("%m")),
    )[1]
    assert my_date_string == new_date.strftime("%m-%d-%Y-") + str(last_day)

    my_date_string = DateParsing(
        task, None, "%m-6-%d-30-%Y+1-lastday_something_cool_%m+6-%d+30-%Y-1-lastday"
    ).string_to_date()

    new_date = datetime.datetime.now() + relativedelta.relativedelta(months=-6, days=-30, years=1)

    last_day = calendar.monthrange(int(new_date.strftime("%Y")), int(new_date.strftime("%m")))[1]

    second_new_date = datetime.datetime.now() + relativedelta.relativedelta(
        months=6, days=30, years=-1
    )

    second_last_day = calendar.monthrange(
        int(second_new_date.strftime("%Y")), int(second_new_date.strftime("%m"))
    )[1]

    assert my_date_string == new_date.strftime("%m-%d-%Y-") + str(
        last_day
    ) + "_something_cool_" + second_new_date.strftime("%m-%d-%Y-") + str(second_last_day)
