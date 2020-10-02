"""

	Extract Management 2.0 Webapp Startup

    Extract Management 2.0
    Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

from flask import (
    Flask,
    g,
    request,
    session,
    redirect,
    url_for,
    render_template,
    jsonify,
)

app = Flask(__name__)

# load configuration settings
app.config.from_object("em.config.DevConfig")

# static files
from flask_compress import Compress
from flask_assets import Environment

Compress(app)
assets = Environment(app)


# user auth
from scripts.flask_simpleldap import LDAP

ldap = LDAP(app)

# database
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy_caching import CachingQuery

db = SQLAlchemy(app, query_class=CachingQuery)


from flask_migrate import Migrate, MigrateCommand

migrate = Migrate(app, db)
import em.model

# web cache
from flask_caching import Cache

cache = Cache(app)

# run tasks off main thread
from flask_executor import Executor

executor = Executor(app)


# other fun stuff
from em.web import (
    auth,
    project,
    task,
    connection,
    assets,
    dashboard,
    filters,
    admin,
)
from em import config, messages

from .logging import event_log

# job scheduler - must come after job & db import
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

import logging

logging.basicConfig(level=logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.DEBUG)

event_log()

if __name__ == "__main__":
    app.run()
