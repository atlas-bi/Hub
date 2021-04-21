"""
EM Web Extensions.

Set up basic flask items for import in other modules.

*Items Setup*

:cache: web asset cache
:compress: compress output (gzip etc)
:db: database
:executor: run process off main thread
:htmlmin: html minifier
:migrate: sql migrations
:redis_client: redis connection
:sess: session
:toolbar: debug toolbar
:web_assets: web asset environ

Finally, set log level to warning.

These items can be imported into other
scripts after running :obj:`em_web.create_app`

"""
import logging

from flask_assets import Environment
from flask_caching import Cache
from flask_compress import Compress
from flask_debugtoolbar import DebugToolbarExtension
from flask_executor import Executor
from flask_htmlmin import HTMLMIN
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_redis import FlaskRedis
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy_caching import CachingQuery

cache = Cache()
compress = Compress()
db = SQLAlchemy(query_class=CachingQuery)
executor = Executor()
htmlmin = HTMLMIN(remove_empty_space=True)
migrate = Migrate()
redis_client = FlaskRedis()
sess = Session()
toolbar = DebugToolbarExtension()
web_assets = Environment()
login_manager = LoginManager()

logging.basicConfig(level=logging.WARNING)
