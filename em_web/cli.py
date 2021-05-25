"""EM Web Custom CLI."""
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

from flask import Blueprint
from flask import current_app as app
from flask.cli import with_appcontext

from em_web.extensions import db

cli_bp = Blueprint("cli", __name__)


@cli_bp.cli.command("create_db")
@with_appcontext
def create_db():
    """Add command to create the test database."""
    if app.config["ENV"] in ["test", "development"]:

        # pylint: disable=W0611
        from em_web.model import (  # noqa: F401
            Connection,
            ConnectionDatabase,
            ConnectionDatabaseType,
            ConnectionFtp,
            ConnectionGpg,
            ConnectionSftp,
            ConnectionSmb,
            ConnectionSsh,
            Login,
            LoginType,
            Project,
            QuoteLevel,
            Task,
            TaskDestinationFileType,
            TaskFile,
            TaskLog,
            TaskProcessingType,
            TaskSourceQueryType,
            TaskSourceType,
            TaskStatus,
            User,
        )

        db.drop_all()
        db.session.commit()

        db.create_all()
        db.session.commit()


@cli_bp.cli.command("seed")
@with_appcontext
def db_seed():
    """Add command to seed the database."""
    from .seed import seed

    seed()


@cli_bp.cli.command("seed_demo")
@with_appcontext
def db_seed_demo():
    """Add command to seed the database for a demo."""
    from .seed import seed_demo

    seed_demo()
