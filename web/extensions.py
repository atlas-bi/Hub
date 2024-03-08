"""
Web Extensions.

Set up basic flask items for import in other modules.

Set log level to warning.

These items can be imported into other
scripts after running :obj:`web.create_app`

"""

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

cache = Cache()
compress = Compress()
db = SQLAlchemy()
executor = Executor()
htmlmin = HTMLMIN(remove_empty_space=True)
migrate = Migrate(compare_type=True)
redis_client = FlaskRedis()
sess = Session()


web_assets = Environment()
login_manager = LoginManager()

logging.basicConfig(level=logging.WARNING)
