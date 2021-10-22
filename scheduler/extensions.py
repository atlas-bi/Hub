"""
Scheduler Extensions.

Set up basic flask items for import in other modules.

*Items Setup*

:db: database
:scheduler: scheduler

These items can be imported into other
scripts after running :obj:`scheduler.create_app`

"""

from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy_caching import CachingQuery

db = SQLAlchemy(query_class=CachingQuery)
atlas_scheduler = APScheduler()
