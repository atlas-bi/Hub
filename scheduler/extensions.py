"""
Scheduler Extensions.

Set up basic flask items for import in other modules.

*Items Setup*

:db: database
:scheduler: scheduler

These items can be imported into other
scripts after running :obj:`scheduler.create_app`

"""

import datetime

from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, mapped_column, registry
from sqlalchemy.sql import functions
from typing_extensions import Annotated

str_5 = Annotated[str, 5]
str_10 = Annotated[str, 10]
str_30 = Annotated[str, 30]
str_120 = Annotated[str, 120]
str_200 = Annotated[str, 200]
str_400 = Annotated[str, 400]
str_500 = Annotated[str, 500]
str_1000 = Annotated[str, 1000]
str_8000 = Annotated[str, 8000]
intpk = Annotated[int, mapped_column(primary_key=True, index=True)]
timestamp = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=functions.now()),
]


class Base(DeclarativeBase):
    """Declare base types."""

    registry = registry(
        type_annotation_map={
            str_120: String(120),
            str_200: String(200),
            str_500: String(500),
            str_1000: String(1000),
            str_8000: String(8000),
            str_5: String(5),
            str_30: String(30),
            str_400: String(400),
        }
    )


db = SQLAlchemy(model_class=Base)
atlas_scheduler = APScheduler()
