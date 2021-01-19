"""EM Runner Configuration."""
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


class Config:
    """All configuration set here. For dev there are overrides below."""

    # pylint: disable=too-few-public-methods

    DEBUG = False
    TESTING = False
    SECRET_KEY = b"something secret"
    PASS_KEY = b"something secret"

    """
        minimum space needed to run tasks
    """
    MIN_DISK_SPACE = 1 * 1024 * 1024 * 1024
    MIN_FREE_MEM_PERC = 10
    MIN_FREE_CPU_PERC = 10

    """
        GIT connection for secure/prive repositories
    """

    GIT_URL = "https://my_git_server.net/"
    GIT_USERNAME = "username"
    GIT_PASSWORD = r"password"  # noqa: S105

    """
        SMB Connection for file storage

        All extracts backups will be stored here.
    """

    SMB_USERNAME = "username"
    SMB_PASSWORD = "password"  # noqa: S105
    SMB_SERVER_IP = "10.0.0.0"
    SMB_SERVER_NAME = "server"
    SMB_DEFAULT_SHARE = "share"

    """
        Email connection info
    """
    SMTP_SERVER = "10.0.0.0"
    SMTP_PORT = 25
    SMTP_SENDER_NAME = "Analytics / Extract Management 2.0"
    SMTP_SENDER_EMAIL = "emai@l"
    SMTP_DEFAULT_RECIEVER = "emai@l"
    SMTP_SUBJECT_PREFIX = "### "

    """
        primary webapp database
    """

    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://{user}:{pw}@{url}/{db}".format(
        user="webapp", pw="nothing", url="localhost", db="em_web"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "max_overflow": 100,  # how many spare connections we can use?
        "pool_size": 5,  # how many queries will run symultaniously?
    }

    WEB_HOST = "https://taskscheduler.riversidehealthcare.net"

    EXECUTOR_TYPE = "thread"
    EXECUTOR_MAX_WORKERS = 12
    EXECUTOR_PROPAGATE_EXCEPTIONS = True

    MIGRATIONS = "migrations"


class DevConfig(Config):
    """Configuration overides for development."""

    # pylint: disable=too-few-public-methods
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    MIGRATIONS = "migrations_dev"
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://{user}:{pw}@{url}/{db}".format(
        user="webapp", pw="nothing", url="localhost", db="em_web_dev"
    )


#   SQLALCHEMY_ECHO = True  # noqa: E800
#   DEMO = True  # noqa: E800


class TestConfig(Config):
    """Configuration overides for testing."""

    # pylint: disable=too-few-public-methods

    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://{user}:{pw}@{url}/{db}".format(
        user="webapp", pw="nothing", url="localhost", db="em_web_test"
    )

    MIGRATIONS = "migrations_test"
