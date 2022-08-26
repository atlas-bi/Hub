"""Web Startup."""

import sys
from pathlib import Path

from web.extensions import (
    cache,
    compress,
    db,
    executor,
    htmlmin,
    login_manager,
    migrate,
    redis_client,
    sess,
    web_assets,
)

from flask import Flask, render_template  # isort:skip

sys.path.append(str(Path(__file__).parents[1]) + "/scripts")
sys.path.append(str(Path(__file__).parents[2]))
from error_print import full_stack  # isort:skip


def create_app() -> Flask:
    """Create app."""
    # pylint: disable=W0621
    app = Flask(__name__)

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

        from whitenoise import WhiteNoise

        app.wsgi_app = WhiteNoise(app.wsgi_app, root="web/static/", prefix="static/")

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

    compress.init_app(app)
    web_assets.init_app(app)

    # auth
    login_manager.init_app(app)
    login_manager.login_view = app.config["LOGIN_VIEW"]
    login_manager.login_message = app.config["LOGIN_MESSAGE"]

    sess.init_app(app)

    # database
    db.init_app(app)

    migrate.init_app(app, db, directory=app.config.get("MIGRATIONS", "migrations"))

    # web cache
    cache.init_app(app)
    cache.clear()
    # run tasks off main thread
    executor.init_app(app)

    # redis
    redis_client.init_app(app)

    # html min
    htmlmin.init_app(app)

    with app.app_context():

        # pylint: disable=W0611
        from web import cli
        from web.web import assets  # noqa: F401
        from web.web import (
            admin,
            auth,
            connection,
            dashboard,
            executors,
            filters,
            project,
            saml_auth,
            table,
            task,
            task_controls,
            task_edit,
            task_files,
        )

        app.register_blueprint(saml_auth.login_bp)
        app.register_blueprint(admin.admin_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(connection.connection_bp)
        app.register_blueprint(project.project_bp)
        app.register_blueprint(task.task_bp)
        app.register_blueprint(task_controls.task_controls_bp)
        app.register_blueprint(task_edit.task_edit_bp)
        app.register_blueprint(task_files.task_files_bp)
        app.register_blueprint(dashboard.dashboard_bp)
        app.register_blueprint(table.table_bp)
        app.register_blueprint(executors.executors_bp)
        app.register_blueprint(filters.filters_bp)
        app.register_blueprint(cli.cli_bp)

        if app.config["DEBUG"]:
            from flask_debugtoolbar import DebugToolbarExtension

            toolbar = DebugToolbarExtension()
            toolbar.init_app(app)
            assets.cache = False  # type: ignore[attr-defined]
            assets.manifest = False  # type: ignore[attr-defined]

        @app.errorhandler(404)
        @app.errorhandler(500)
        def error_message(error: str) -> str:
            """Return error page for 404 and 500 errors including the specific error message.

            :param error: error message
            :return: json web response with error message:

            .. code-block:: python

                {"error": "messsage"}

            """
            return render_template(
                "error.html.j2",
                message="<strong>" + str(error).replace(":", "</strong>:"),
                trace=full_stack(),
                title="That was an error",
            )

        return app


app = create_app()

if __name__ == "__main__":
    app.run()
