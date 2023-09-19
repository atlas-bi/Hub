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

db = SQLAlchemy()
atlas_scheduler = APScheduler()
