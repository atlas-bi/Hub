"""
Runner module.

Runner is a Flask web API designed to run tasks on multiple worders. The API
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
* /<my_id>/<code_type> - returns tasks's source code for viewing

Database Model
**************

Database model should be cloned from `web` before running app.

.. code-block:: console

    cp web/model.py scheduler/

"""

import logging
import os

from flask import Flask

from runner.extensions import db, executor, redis_client

logging.basicConfig(level=logging.WARNING)


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

    executor.init_app(app)

    redis_client.init_app(app)

    with app.app_context():
        # pylint: disable=C0415

        from runner.web import filters, web

        app.register_blueprint(web.web_bp)
        app.register_blueprint(filters.filters_bp)

        return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5002)
