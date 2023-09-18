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

db = SQLAlchemy()
executor = Executor()
redis_client = FlaskRedis()
