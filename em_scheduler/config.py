"""EM Scheduler Configuration."""
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


from apscheduler.jobstores.redis import RedisJobStore


class Config:
    """All configuration set here. For dev there are overrides below."""

    # pylint: disable=too-few-public-methods

    DEBUG = False
    TESTING = False
    SECRET_KEY = "something secret"  # noqa: S105

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

    """
        scheduler settings
    """

    SCHEDULER_JOBSTORES = {
        "default": RedisJobStore(
            jobs_key="em_jobs", run_times_key="em_running", host="127.0.0.1", port=6379
        )
    }

    SCHEDULER_EXECUTORS = {
        "default": {
            "type": "threadpool",
            "max_workers": 100,
        }
    }

    SCHEDULER_JOB_DEFAULTS = {
        "coalesce": True,
        "max_instances": 50,
        "replace_existing": True,
        "misfire_grace_time": 30,
    }

    SCHEDULER_API_ENABLED = False

    RUNNER_HOST = "http://127.0.0.1:5002/api"

    MIGRATIONS = "migrations"


class DevConfig(Config):
    """Configuration overides for development."""

    # pylint: disable=too-few-public-methods
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://{user}:{pw}@{url}/{db}".format(
        user="webapp", pw="nothing", url="localhost", db="em_web_dev"
    )
    MIGRATIONS = "migrations_dev"


#    DEMO = True  # noqa: E800


class TestConfig(Config):
    """Configuration overides for testing."""

    # pylint: disable=too-few-public-methods

    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://{user}:{pw}@{url}/{db}".format(
        user="webapp", pw="nothing", url="localhost", db="em_web_test"
    )

    MIGRATIONS = "migrations_test"