"""
Runner Extensions.

Set up basic flask items for import in other modules.

*Items Setup*

:db: database
:executor: task executor

These items can be imported into other
scripts after running :obj:`scheduler.create_app`

"""

from flask_executor import Executor
from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy_caching import CachingQuery

db = SQLAlchemy(query_class=CachingQuery)
executor = Executor()
redis_client = FlaskRedis()
