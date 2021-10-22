"""Test date.

run with::

   poetry run pytest runner/tests/test_scripts_date.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest runner/tests/test_scripts_date.py::test_next \
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
    p_id, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, "%d", "").string_to_date()

    assert my_date_string == datetime.datetime.now().strftime("%d")


def test_date_parsing_microseconds(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, "%f", "").string_to_date()

    assert len(my_date_string) == 6

    my_date_string = DateParsing(task, "%f-1", "").string_to_date()

    assert len(my_date_string) == 6

    my_date_string = DateParsing(task, "%f+1", "").string_to_date()

    assert len(my_date_string) == 6


def test_date_parsing_seconds(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, "%S", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%S")

    my_date_string = DateParsing(task, "%S-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(seconds=-1)
    ).strftime("%S")

    my_date_string = DateParsing(task, "%S-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(seconds=-100)
    ).strftime("%S")

    my_date_string = DateParsing(task, "%S+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(seconds=10)
    ).strftime("%S")


def test_date_parsing_minutes(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, "%M", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%M")

    my_date_string = DateParsing(task, "%M-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(minutes=-1)
    ).strftime("%M")

    my_date_string = DateParsing(task, "%M-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(minutes=-100)
    ).strftime("%M")

    my_date_string = DateParsing(task, "%M+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(minutes=10)
    ).strftime("%M")


def test_date_parsing_hours(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, "%H", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%H")

    my_date_string = DateParsing(task, "%H-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(hours=-1)
    ).strftime("%H")

    my_date_string = DateParsing(task, "%H-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(hours=-100)
    ).strftime("%H")

    my_date_string = DateParsing(task, "%H+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(hours=10)
    ).strftime("%H")

    my_date_string = DateParsing(task, "%I", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%I")

    my_date_string = DateParsing(task, "%I-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(hours=-1)
    ).strftime("%I")

    my_date_string = DateParsing(task, "%I-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(hours=-100)
    ).strftime("%I")

    my_date_string = DateParsing(task, "%I+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(hours=10)
    ).strftime("%I")


def test_date_parsing_days(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, "%a", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%a")

    my_date_string = DateParsing(task, "%a-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-1)
    ).strftime("%a")

    my_date_string = DateParsing(task, "%a-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-100)
    ).strftime("%a")

    my_date_string = DateParsing(task, "%a+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=10)
    ).strftime("%a")

    my_date_string = DateParsing(task, "%A", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%A")

    my_date_string = DateParsing(task, "%A-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-1)
    ).strftime("%A")

    my_date_string = DateParsing(task, "%A-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-100)
    ).strftime("%A")

    my_date_string = DateParsing(task, "%A+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=10)
    ).strftime("%A")

    my_date_string = DateParsing(task, "%w", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%w")

    my_date_string = DateParsing(task, "%w-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-1)
    ).strftime("%w")

    my_date_string = DateParsing(task, "%w-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-100)
    ).strftime("%w")

    my_date_string = DateParsing(task, "%w+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=10)
    ).strftime("%w")

    my_date_string = DateParsing(task, "%d", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%d")

    my_date_string = DateParsing(task, "%d-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-1)
    ).strftime("%d")

    my_date_string = DateParsing(task, "%d-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=-100)
    ).strftime("%d")

    my_date_string = DateParsing(task, "%d+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(days=10)
    ).strftime("%d")


def test_date_parsing_weeks(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, "%U", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%U")

    my_date_string = DateParsing(task, "%U-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(weeks=-1)
    ).strftime("%U")

    my_date_string = DateParsing(task, "%U-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(weeks=-100)
    ).strftime("%U")

    my_date_string = DateParsing(task, "%U+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(weeks=10)
    ).strftime("%U")

    my_date_string = DateParsing(task, "%W", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%W")

    my_date_string = DateParsing(task, "%W-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(weeks=-1)
    ).strftime("%W")

    my_date_string = DateParsing(task, "%W-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(weeks=-100)
    ).strftime("%W")

    my_date_string = DateParsing(task, "%W+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(weeks=10)
    ).strftime("%W")


def test_date_parsing_months(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, "%b", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%b")

    my_date_string = DateParsing(task, "%b-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=-1)
    ).strftime("%b")

    my_date_string = DateParsing(task, "%b-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=-100)
    ).strftime("%b")

    my_date_string = DateParsing(task, "%b+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=10)
    ).strftime("%b")

    my_date_string = DateParsing(task, "%B", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%B")

    my_date_string = DateParsing(task, "%B-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=-1)
    ).strftime("%B")

    my_date_string = DateParsing(task, "%B-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=-100)
    ).strftime("%B")

    my_date_string = DateParsing(task, "%B+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=10)
    ).strftime("%B")

    my_date_string = DateParsing(task, "%m", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%m")

    my_date_string = DateParsing(task, "%m-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=-1)
    ).strftime("%m")

    my_date_string = DateParsing(task, "%m-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=-100)
    ).strftime("%m")

    my_date_string = DateParsing(task, "%m+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(months=10)
    ).strftime("%m")


def test_date_parsing_years(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, "%y", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%y")

    my_date_string = DateParsing(task, "%y-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(years=-1)
    ).strftime("%y")

    my_date_string = DateParsing(task, "%y-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(years=-100)
    ).strftime("%y")

    my_date_string = DateParsing(task, "%y+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(years=10)
    ).strftime("%y")

    my_date_string = DateParsing(task, "%Y", "").string_to_date()
    assert my_date_string == datetime.datetime.now().strftime("%Y")

    my_date_string = DateParsing(task, "%Y-1", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(years=-1)
    ).strftime("%Y")

    my_date_string = DateParsing(task, "%Y-100", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(years=-100)
    ).strftime("%Y")

    my_date_string = DateParsing(task, "%Y+10", "").string_to_date()
    assert my_date_string == (
        datetime.datetime.now() + relativedelta.relativedelta(years=10)
    ).strftime("%Y")


def test_date_parsing_firsday(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, "firstday", "").string_to_date()

    assert my_date_string == "1"


def test_date_parsing_firstday_zero(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, "firstday0", "").string_to_date()

    assert my_date_string == "01"


def test_date_parsing_lastday(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()

    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, "lastday", "").string_to_date()

    last_day = calendar.monthrange(
        int(datetime.datetime.now().strftime("%Y")),
        int(datetime.datetime.now().strftime("%m")),
    )[1]
    assert my_date_string == str(last_day)


def test_complex_patterns(client_fixture: fixture) -> None:
    p_id, t_id = create_demo_task()
    task = Task.query.filter_by(id=t_id).first()

    my_date_string = DateParsing(task, "%m-6-%d-30-%Y+1-lastday", "").string_to_date()

    new_date = datetime.datetime.now() + relativedelta.relativedelta(
        months=-6, days=-30, years=1
    )

    last_day = calendar.monthrange(
        int(datetime.datetime.now().strftime("%Y")),
        int(datetime.datetime.now().strftime("%m")),
    )[1]
    assert my_date_string == new_date.strftime("%m-%d-%Y-") + str(last_day)

    my_date_string = DateParsing(
        task, "%m-6-%d-30-%Y+1-lastday_something_cool_%m+6-%d+30-%Y-1-lastday", ""
    ).string_to_date()

    new_date = datetime.datetime.now() + relativedelta.relativedelta(
        months=-6, days=-30, years=1
    )

    last_day = calendar.monthrange(
        int(new_date.strftime("%Y")), int(new_date.strftime("%m"))
    )[1]

    second_new_date = datetime.datetime.now() + relativedelta.relativedelta(
        months=6, days=30, years=-1
    )

    second_last_day = calendar.monthrange(
        int(second_new_date.strftime("%Y")), int(second_new_date.strftime("%m"))
    )[1]

    assert my_date_string == new_date.strftime("%m-%d-%Y-") + str(
        last_day
    ) + "_something_cool_" + second_new_date.strftime("%m-%d-%Y-") + str(
        second_last_day
    )
