"""
Web Extensions.

Set up basic flask items for import in other modules.

Set log level to warning.

These items can be imported into other
scripts after running :obj:`web.create_app`

"""

import datetime
import logging

from flask_assets import Environment
from flask_caching import Cache
from flask_compress import Compress
from flask_executor import Executor
from flask_htmlmin import HTMLMIN
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_redis import FlaskRedis
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, mapped_column, registry
from sqlalchemy.sql import functions
from typing_extensions import Annotated

cache = Cache()
compress = Compress()
executor = Executor()
htmlmin = HTMLMIN(remove_empty_space=True)
migrate = Migrate(compare_type=True)
redis_client = FlaskRedis()
sess = Session()

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

web_assets = Environment()
login_manager = LoginManager()

logging.basicConfig(level=logging.WARNING)
