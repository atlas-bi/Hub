"""EM Web Custom CLI."""

import sys
from importlib import import_module
from pathlib import Path

from flask import Blueprint
from flask import current_app as app
from flask.cli import with_appcontext
from sqlalchemy_utils import create_database, database_exists

from web import model
from web.extensions import db

cli_bp = Blueprint("cli", __name__)

_SCRIPTS_PATH = str(Path(__file__).parents[1] / "scripts")
if _SCRIPTS_PATH not in sys.path:
    sys.path.append(_SCRIPTS_PATH)

from database import force_drop_database  # noqa: E402


@cli_bp.cli.command("create_db")
@with_appcontext
def create_db() -> None:
    """Add command to create the test database."""
    if app.config["ENV"] in ["test", "development"]:
        db.drop_all()
        db.session.commit()

        db.create_all()
        db.session.commit()


@cli_bp.cli.command("reset_db")
@with_appcontext
def reset_db() -> None:
    """Add command to clear the database."""
    if database_exists(db.engine.url):
        force_drop_database(db.engine.url, db.engine)

    create_database(db.engine.url)


@cli_bp.cli.command("seed")
@with_appcontext
def db_seed() -> None:
    """Add command to seed the database.

    This is run on each deploy to keep db settings updated.
    poetry run flask --app=web cli seed
    """
    database_module = import_module("database")

    database_module.seed(db.session, model)


@cli_bp.cli.command("seed_demo")
@with_appcontext
def db_seed_demo() -> None:
    """Add command to seed the database for a demo."""
    seed_demo = import_module("web.seed").seed_demo

    seed_demo()
