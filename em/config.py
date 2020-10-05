"""

    Extract Management 2.0 Configuration

    Extract Management 2.0
    Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor


class Config:
    """
        all configuration set here. For dev there are overrides below.
    """

    # pylint: disable=too-few-public-methods

    DEBUG = False
    TESTING = False
    SECRET_KEY = b"This is a key123"
    IV_KEY = b"This is an IV456"

    """
        LDAP Connection used for user authentication
    """
    LDAP_HOST = "ldap_host"  # defaults to localhost
    LDAP_BASE_DN = "ldap_search_base"
    LDAP_USER_OBJECT_FILTER = "(AccountName=%s)"
    LDAP_USERNAME = "ldap_username"
    LDAP_PASSWORD = "ldap_password"
    LDAP_USE_SSL = True
    LDAP_LOGIN_VIEW = "login"

    """
        GIT connection for secure/prive repositories
    """

    GIT_URL = "my_git_website"
    GIT_USERNAME = "git_username"
    GIT_PASSWORD = r"git_password"

    """
        SMB Connection for file storage

        All extracts will be logged here, either by the output file
        or by a lot file <extract_name_%date%_%time%>.log
    """

    SMB_USERNAME = "smb_username"
    SMB_PASSWORD = "smb_password"
    SMB_SERVER_IP = "0.0.0.0"
    SMB_SERVER_NAME = "smb_server_name"
    SMB_DEFAULT_SHARE = "smb_default_share"

    """
        Email connection info
    """
    SMTP_SERVER = "smtp_server"
    SMTP_PORT = 25
    SMTP_SENDER_NAME = "Riverside Healthcare Analytics / Extract Management 2.0"
    SMTP_SENDER_EMAIL = "sender_email"
    SMTP_DEFAULT_RECIEVER = "reciever_email"
    SMTP_SUBJECT_PREFIX = "### "

    """
        Flask-Caching related configs
    """
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300

    """
        primary webapp database
    """
    SQLALCHEMY_DATABASE_URI = "sqlite:///../em.sqlite"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLALCHEMY_ENGINE_OPTIONS = {
    #     "max_overflow": 100,  # how many spare connections we can use?
    #     "pool_size": 5,  # how many queries will run symultaniously?
    # }

    """
        scheduler settings
    """
    JOBS = []

    SCHEDULER_JOBSTORES = {"default": SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")}

    SCHEDULER_EXECUTORS = {
        "default": {
            "type": "threadpool",
            "max_workers": 100,
        }  # how many tasks will run at one time?
        #'default': ProcessPoolExecutor(max_workers=5)
    }

    SCHEDULER_JOB_DEFAULTS = {
        "coalesce": True,
        "max_instances": 50,
        "replace_existing": True,
    }

    SCHEDULER_API_ENABLED = True

    DEMO = True


class DevConfig(Config):
    """
        Configuration overides for development
    """

    # pylint: disable=too-few-public-methods
    DEBUG = True
    SESSION_COOKIE_SECURE = False
