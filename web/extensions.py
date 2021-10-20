"""
Web Extensions.

Set up basic flask items for import in other modules.

Set log level to warning.

These items can be imported into other
scripts after running :obj:`web.create_app`

"""
import logging
from typing import Any

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
from flask_sqlalchemy_caching import CachingQuery
from sqlalchemy.orm import Session as SqlSession

cache = Cache()
compress = Compress()
db = SQLAlchemy(query_class=CachingQuery)
executor = Executor()
htmlmin = HTMLMIN(remove_empty_space=True)
migrate = Migrate()
redis_client = FlaskRedis()
sess = Session()


web_assets = Environment()
login_manager = LoginManager()

logging.basicConfig(level=logging.WARNING)


def get_or_create(session: SqlSession, model: Any, **kwargs: Any) -> Any:
    """Create model if not existing."""
    instance = model.query.filter_by(**kwargs).first()

    if instance:
        return instance

    instance = model(**kwargs)

    session.add(instance)
    session.commit()

    return instance
