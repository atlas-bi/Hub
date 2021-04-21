"""
EM's scheduler module.

EM's scheduler is a Flask web API running Flask_APScheduler on a single
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

Database model should be cloned from `em_web` before running app.

.. code-block:: console

    cp em_web/model.py em_scheduler/

"""

# Extract Management 2.0
# Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging

from flask import Flask, jsonify, make_response

from em_scheduler.extensions import db, scheduler


def create_app():
    """Create task runner app.

    :return: app
    """
    # pylint: disable=W0621
    app = Flask(__name__)

    if app.config["ENV"] == "test":
        app.config.from_object("em_scheduler.config.TestConfig")

    elif app.config["DEBUG"]:
        app.config.from_object("em_scheduler.config.DevConfig")

    else:
        app.config.from_object("em_scheduler.config.Config")

    db.init_app(app)

    scheduler.init_app(app)

    logging.basicConfig(level=logging.WARNING)

    with app.app_context():
        # pylint: disable=W0611
        from em_scheduler import maintenance  # noqa: F401

        scheduler.start()
        # pylint: disable=C0415
        from em_scheduler import web
        from em_scheduler.events import scheduler_logs

        app.register_blueprint(web.web_bp)

        if app.config["ENV"] == "test":
            logging.getLogger("apscheduler").setLevel(logging.INFO)
        else:
            logging.getLogger("apscheduler").setLevel(logging.ERROR)

        scheduler_logs(app)

        return app


app = create_app()


@app.errorhandler(404)
@app.errorhandler(500)
def error_message(error):
    """Return error page for 404 and 500 errors including the specific error message.

    :param error: error message
    :return: json web response with error message:

    .. code-block:: python

        {"error": "messsage"}

    """
    return make_response(jsonify({"error": str(error)}), 404)


if __name__ == "__main__":
    app.run(port=5001)
