"""EM Web Configuration."""
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

import redis


class Config:
    """All configuration set here. For dev there are overrides below."""

    # pylint: disable=too-few-public-methods

    DEBUG = False
    TESTING = False
    SECRET_KEY = b"something secret"
    IV_KEY = b"something secret"
    PASS_KEY = b"something secret"

    """
        redis connection settings
    """

    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.Redis(host="localhost", port=6379)

    """
        LDAP Connection used for user authentication
    """
    LDAP_HOST = "10.0.0.0"  # defaults to localhost
    LDAP_BASE_DN = "OU=People,OU=Employees,DC=Org"
    LDAP_USER_OBJECT_FILTER = "(sAMAccountName=%s)"
    LDAP_USERNAME = "username"
    LDAP_PASSWORD = "password"  # noqa: S105
    LDAP_USE_SSL = True
    LDAP_LOGIN_VIEW = "auth_bp.login"

    """
        Flask-Caching related configs
    """
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300

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

    SCHEUDULER_HOST = "http://127.0.0.1:5001/api"

    RUNNER_HOST = "http://127.0.0.1:5002/api"

    WEB_HOST = "0.0.0.0"  # noqa: S104

    """
        process executor. must be thread type, not process, otherwise we cannot
        have sql access inside the called functions.
    """

    EXECUTOR_TYPE = "thread"
    EXECUTOR_MAX_WORKERS = 12
    EXECUTOR_PROPAGATE_EXCEPTIONS = True

    REDIS_URL = "redis://127.0.0.1:6379/0"

    MINIFY_HTML = True

    DEMO = False

    MIGRATIONS = "migrations"


class DevConfig(Config):
    """Configuration overides for development.

    To Use:
    FLASK_ENV=development
    """

    # pylint: disable=too-few-public-methods
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    MIN_DISK_SPACE = 1 * 1024 * 1024 * 1024
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://{user}:{pw}@{url}/{db}".format(
        user="webapp", pw="nothing", url="localhost", db="em_web_dev"
    )

    MIGRATIONS = "migrations_dev"


#    SQLALCHEMY_ECHO = True  # noqa: E800

#    DEMO = True  # noqa: E800


class DevTestConfig(DevConfig):
    """Configuration overrides for dev testing.

    To Use:
    FLASK_ENV=test
    FLASK_DEBUG=0
    """

    # pylint: disable=too-few-public-methods
    LDAP_BASE_DN = ""

    AUTH_USERNAME = "username"
    AUTH_PASSWORD = "password"  # noqa: S105


class TestConfig(DevTestConfig):
    """Configuration overides for testing.

    To Use:
    FLASK_ENV=test
    FLASK_DEBUG=1
    """

    # pylint: disable=too-few-public-methods
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://{user}:{pw}@{url}/{db}".format(
        user="webapp", pw="nothing", url="localhost", db="em_web_test"
    )

    MIGRATIONS = "migrations_test"
    DEMO = True
