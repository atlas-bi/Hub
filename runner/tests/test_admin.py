"""Test web/admin.

run with::

   FLASK_APP=web; \
   FLASK_ENV=test; \
   poetry run pytest tests/test_admin.py \
   --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings

"""


def test_nothing() -> None:
    pass
