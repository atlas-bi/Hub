"""
Scheduler module.

Scheduler is a Flask web API running Flask_APScheduler on a single
worker process.

The scheduler should be running on a single worker process and only accessable on localhost.

Tasks are started and stopped by sending a web request to various URL's.

* /add/<task_id>
* /delete/<task_id>
* /run/<task_id>


When the scheduler is ready to run a task it will send an async web request to the runner API
with the id of the task to run next.

Other Urls
**********

* /delete - delete all jobs
* /pause - pause all jobs
* /resume - resume all paused jobs
* /shutdown - gracefully shutdown the scheduler
* /kill - kill the scheduler
* /jobs - list all id's
* /details - list all job details
* /scheduled - list id's of scheduled jobs
* /delete-orphans - delete all orphaned jobs (jobs that no
  longer have an associated EM task existing)

Database Model
**************

Database model should be cloned from `web` before running app.

.. code-block:: console

    cp web/model.py scheduler/

"""

import contextlib
import logging
import os

from apscheduler.schedulers import SchedulerAlreadyRunningError
from flask import Flask, jsonify, make_response
from werkzeug import Response

from scheduler.extensions import atlas_scheduler, db


def create_app() -> Flask:
    """Create task runner app."""
    # pylint: disable=W0621
    app = Flask(__name__)

    app.config["ENV"] = os.environ.get("FLASK_ENV", "production")

    if app.config["ENV"] == "development":
        try:
            from config_cust import DevConfig as DevConfigCust

            app.config.from_object(DevConfigCust())
        except ImportError:
            from config import DevConfig

            app.config.from_object(DevConfig())

    elif app.config["ENV"] == "demo":
        try:
            from config_cust import DemoConfig as DemoConfigCust

            app.config.from_object(DemoConfigCust())
        except ImportError:
            from config import DemoConfig

            app.config.from_object(DemoConfig())

    elif app.config["ENV"] == "test":
        try:
            from config_cust import (
                TestConfig as TestConfigCust,  # type: ignore[attr-defined]
            )

            app.config.from_object(TestConfigCust())
        except ImportError:
            from config import TestConfig

            app.config.from_object(TestConfig())

    else:
        try:
            from config_cust import Config as ConfigCust

            app.config.from_object(ConfigCust())
        except ImportError:
            from config import Config

            app.config.from_object(Config())

    db.init_app(app)

    # pylint: disable=W0611
    from scheduler import maintenance  # noqa: F401

    with contextlib.suppress(SchedulerAlreadyRunningError):
        # pytest imports twice, this will catch on the second import.
        atlas_scheduler.init_app(app)

    logging.basicConfig(level=logging.WARNING)

    with app.app_context():
        # pylint: disable=W0611
        if atlas_scheduler.running is False:
            # pytest imports twice. this will save us on the
            # second import.
            atlas_scheduler.start()

        # pylint: disable=C0415
        from apscheduler.events import (
            EVENT_JOB_ADDED,
            EVENT_JOB_ERROR,
            EVENT_JOB_EXECUTED,
            EVENT_JOB_MISSED,
            EVENT_JOB_REMOVED,
            EVENT_JOB_SUBMITTED,
        )

        from scheduler import web
        from scheduler.events import (
            job_added,
            job_error,
            job_executed,
            job_missed,
            job_removed,
            job_submitted,
        )

        app.register_blueprint(web.web_bp)

        if app.config["ENV"] == "test":
            logging.getLogger("apscheduler").setLevel(logging.INFO)
        else:
            logging.getLogger("apscheduler").setLevel(logging.ERROR)

        atlas_scheduler.add_listener(job_missed, EVENT_JOB_MISSED)
        atlas_scheduler.add_listener(job_error, EVENT_JOB_ERROR)
        atlas_scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)
        atlas_scheduler.add_listener(job_added, EVENT_JOB_ADDED)
        atlas_scheduler.add_listener(job_removed, EVENT_JOB_REMOVED)
        atlas_scheduler.add_listener(job_submitted, EVENT_JOB_SUBMITTED)

        @app.errorhandler(404)
        @app.errorhandler(500)
        def error_message(error: str) -> Response:
            """Return error page for 404 and 500 errors including the specific error message."""
            return make_response(jsonify({"error": str(error)}), 404)

        return app


app = create_app()

if __name__ == "__main__":  # pragma: no cover
    app.run(port=5001)
