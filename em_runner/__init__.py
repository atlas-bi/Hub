"""
EM's runner module.

EM's runner is a Flask web API designed to run tasks on multiple worders. The API
should quickly respont to a request to run a task and launch the task on a separate
thread.

The run should be only accessable on localhost.

Tasks are run by sending a simple web request. Note - EM's runner works only from task id's,
so there is not need to specify that a value sent to the API is a `task`.. that is assumed.

.. code-block:: console

    /api/<task_id>

The API will respond that is has successfully recieved a request to run the task. The
task will launch on a separate thread on the same worker.

Other Urls
**********

* /api/send_<type>/<task_id>/<run_id>/<file_id> - use to resend archived output files
* /api/whoami - returns the username of the active user on the web server
* /api/reloadDaemon - reload web server service daemon
* /api/restartDaemon - restart web server service daemon
* /<my_id>/<code_type> - returns tasks's source code for viewing

Database Model
**************

Database model should be cloned from `em_web` before running app.

.. code-block:: console

    cp em_web/model.py em_scheduler/

"""
# Extract Management 2.0 Webapp Startup.

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

from flask import Flask

from em_runner.extensions import db, executor, redis_client

logging.basicConfig(level=logging.WARNING)


def create_app():
    """Create task runner app.

    :return: app
    """
    # pylint: disable=W0621
    app = Flask(__name__)

    if app.config["ENV"] == "test":
        logging.info("loading test config")
        app.config.from_object("em_runner.config.TestConfig")
    elif app.config["DEBUG"] or app.config["ENV"] == "test":
        logging.info("loading debug config")
        app.config.from_object("em_runner.config.DevConfig")
    else:
        logging.info("loading prod config")
        app.config.from_object("em_runner.config.Config")

    db.init_app(app)

    executor.init_app(app)

    redis_client.init_app(app)

    with app.app_context():
        # pylint: disable=C0415
        from em_runner.web import filters, web

        app.register_blueprint(web.web_bp, url_prefix="/api")
        app.register_blueprint(filters.filters_bp)

        return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5002)
