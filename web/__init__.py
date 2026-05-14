"""Web Startup."""

from importlib import import_module
import os
import sys
from pathlib import Path

from flask import Flask, render_template  # isort:skip

from web.extensions import (
    cache,
    compress,
    csrf,
    db,
    executor,
    htmlmin,
    login_manager,
    migrate,
    redis_client,
    sess,
    web_assets,
)

sys.path.append(str(Path(__file__).parents[1]) + "/scripts")
sys.path.append(str(Path(__file__).parents[2]))
from error_print import full_stack  # isort:skip


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


def _register_blueprints(app: Flask) -> object:
    cli_module = import_module("web.cli")
    assets_module = import_module("web.web.assets")
    admin_module = import_module("web.web.admin")
    auth_module = import_module("web.web.auth")
    connection_module = import_module("web.web.connection")
    dashboard_module = import_module("web.web.dashboard")
    executors_module = import_module("web.web.executors")
    filters_module = import_module("web.web.filters")
    project_module = import_module("web.web.project")
    saml_auth_module = import_module("web.web.saml_auth")
    table_module = import_module("web.web.table")
    task_module = import_module("web.web.task")
    task_controls_module = import_module("web.web.task_controls")
    task_edit_module = import_module("web.web.task_edit")
    task_files_module = import_module("web.web.task_files")

    app.register_blueprint(saml_auth_module.login_bp)
    app.register_blueprint(admin_module.admin_bp)
    app.register_blueprint(auth_module.auth_bp)
    app.register_blueprint(connection_module.connection_bp)
    app.register_blueprint(project_module.project_bp)
    app.register_blueprint(task_module.task_bp)
    app.register_blueprint(task_controls_module.task_controls_bp)
    app.register_blueprint(task_edit_module.task_edit_bp)
    app.register_blueprint(task_files_module.task_files_bp)
    app.register_blueprint(dashboard_module.dashboard_bp)
    app.register_blueprint(table_module.table_bp)
    app.register_blueprint(executors_module.executors_bp)
    app.register_blueprint(filters_module.filters_bp)
    app.register_blueprint(cli_module.cli_bp)

    return assets_module


def create_app() -> Flask:
    """Create app."""
    # pylint: disable=W0621
    app = Flask(__name__)

    app.config["ENV"] = os.environ.get("FLASK_ENV", "production")
    app.config.from_object(_load_config(app.config["ENV"]))

    if app.config["ENV"] == "demo":
        white_noise = import_module("whitenoise")
        app.wsgi_app = white_noise.WhiteNoise(  # type: ignore[assignment]
            app.wsgi_app,
            root="web/static/",
            prefix="static/",
        )

    web_assets.init_app(app)
    compress.init_app(app)

    # auth
    csrf.init_app(app)
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
        assets = _register_blueprints(app)

        if app.config["DEBUG"]:
            toolbar_module = import_module("flask_debugtoolbar")
            toolbar = toolbar_module.DebugToolbarExtension()
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

        @app.route("/robots.txt")
        def robots() -> str:
            return "User-agent: * Disallow: /"

        return app


app = create_app()

if __name__ == "__main__":
    app.run()
