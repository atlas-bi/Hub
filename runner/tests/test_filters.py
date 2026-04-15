"""Test runner/filters.

run with::

   poetry run pytest runner/tests/test_filters.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest runner/tests/test_filters.py::test_filename \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings


"""

import datetime

from pytest import fixture


def test_year(client_fixture: fixture) -> None:
    from runner.web.filters import year

    assert year(None) == datetime.date.today().year
    assert year("asdf") == datetime.date.today().year


def test_datetime_format(client_fixture: fixture) -> None:
    from runner.web.filters import datetime_format

    test_date = datetime.datetime.now()
    assert datetime_format(test_date) == datetime.datetime.strftime(
        test_date,
        "%a, %b %-d, %Y %H:%M:%S.%f",
    )
    assert datetime_format("nothing") == "nothing"
