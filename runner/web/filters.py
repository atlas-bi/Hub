"""Custom Jinja template filters used in html."""

import datetime

from flask import Blueprint

filters_bp = Blueprint("filters_bp", __name__)


@filters_bp.app_template_filter("year")
def year(none: None) -> int:
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
