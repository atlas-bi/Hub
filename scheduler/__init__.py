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
from importlib import import_module
import logging
import os

from apscheduler.schedulers import SchedulerAlreadyRunningError
from flask import Flask, jsonify, make_response
from werkzeug import Response

from scheduler.extensions import atlas_scheduler, db


def _load_config(env: str) -> object:
    config_name = {
        "development": "DevConfig",
        "demo": "DemoConfig",
        "test": "TestConfig",
    }.get(env, "Config")

    for module_name in ("config_cust", "config"):
        try:
            module = import_module(module_name)
            return getattr(module, config_name)()
        except (AttributeError, ImportError):
            continue

    raise ImportError(f"Unable to load configuration for env {env!r}.")


def _register_scheduler_components(app: Flask) -> None:
    apscheduler_events = import_module("apscheduler.events")
    web_module = import_module("scheduler.web")
    scheduler_events = import_module("scheduler.events")

    app.register_blueprint(web_module.web_bp)

    atlas_scheduler.add_listener(
        scheduler_events.job_missed,
        apscheduler_events.EVENT_JOB_MISSED,
    )
    atlas_scheduler.add_listener(
        scheduler_events.job_error,
        apscheduler_events.EVENT_JOB_ERROR,
    )
    atlas_scheduler.add_listener(
        scheduler_events.job_executed,
        apscheduler_events.EVENT_JOB_EXECUTED,
    )
    atlas_scheduler.add_listener(
        scheduler_events.job_added,
        apscheduler_events.EVENT_JOB_ADDED,
    )
    atlas_scheduler.add_listener(
        scheduler_events.job_removed,
        apscheduler_events.EVENT_JOB_REMOVED,
    )
    atlas_scheduler.add_listener(
        scheduler_events.job_submitted,
        apscheduler_events.EVENT_JOB_SUBMITTED,
    )


def create_app() -> Flask:
    """Create task runner app."""
    # pylint: disable=W0621
    app = Flask(__name__)

    app.config["ENV"] = os.environ.get("FLASK_ENV", "production")
    app.config.from_object(_load_config(app.config["ENV"]))

    db.init_app(app)

    import_module("scheduler.maintenance")

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

        _register_scheduler_components(app)

        if app.config["ENV"] == "test":
            logging.getLogger("apscheduler").setLevel(logging.INFO)
        else:
            logging.getLogger("apscheduler").setLevel(logging.ERROR)

        @app.errorhandler(404)
        @app.errorhandler(500)
        def error_message(error: str) -> Response:
            """Return error page for 404 and 500 errors including the specific error message."""
            return make_response(jsonify({"error": str(error)}), 404)

        return app


app = create_app()

if __name__ == "__main__":  # pragma: no cover
    app.run(port=5001)
