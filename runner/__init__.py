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
from importlib import import_module

from flask import Flask

from runner.extensions import db, executor, redis_client

logging.basicConfig(level=logging.WARNING)


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


def _register_blueprints(app: Flask) -> None:
    filters_module = import_module("runner.web.filters")
    web_module = import_module("runner.web.web")

    app.register_blueprint(web_module.web_bp)
    app.register_blueprint(filters_module.filters_bp)


def create_app() -> Flask:
    """Create task runner app."""
    # pylint: disable=W0621
    app = Flask(__name__)
    app.config["ENV"] = os.environ.get("FLASK_ENV", "production")
    app.config.from_object(_load_config(app.config["ENV"]))

    db.init_app(app)

    executor.init_app(app)

    redis_client.init_app(app)

    with app.app_context():
        _register_blueprints(app)

        return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5002)
