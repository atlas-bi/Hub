"""Default Configuration."""

import os
from pathlib import Path
from urllib.parse import urlparse

import redis
import saml2
import saml2.saml
from apscheduler.jobstores.redis import RedisJobStore


class Config:
    """All prod configuration set here. For dev there are overrides below."""

    # pylint: disable=too-few-public-methods

    ALLOWED_HOSTS = ["*", "localhost"]

    ORG_NAME = "Riverside Healthcare"

    DEBUG = False
    TESTING = False
    DEMO = False

    # flask cookie encryption
    SECRET_KEY = b"zL-yN8sVPaheeWmLJz8CxHXSLt8ZMI9jrAPXn167a8I="

    # password encryption key (multiple of 4 bytes) https://fernetkeygen.com
    PASS_KEY = b"zL-yN8sVPaheeWmLJz8CxHXSLt8ZMI9jrAPXn167a8I="

    # redis sessions

    redis_host = os.environ.get("REDISHOST", "localhost")
    redis_port = int(os.environ.get("REDISPORT", 6379))
    redis_password = os.environ.get("REDISPASSWORD")
    redis_user = os.environ.get("REDISUSER")

    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.Redis(host=redis_host, port=redis_port)

    if os.environ.get("REDIS_URL"):
        url = urlparse(os.environ["REDIS_URL"])
        redis_host = url.hostname or "localhost"
        redis_port = url.port or 6379
        redis_password = url.password
        redis_user = url.username

        SESSION_REDIS = redis.Redis(
            host=redis_host,
            port=redis_port,
            username=redis_user,
            password=redis_password,
        )

    # for flask-redis
    REDIS_URL = os.environ.get("REDIS_URL", f"redis://{redis_host}:{redis_port}")

    # authentication
    LOGIN_VIEW = "auth_bp.login"
    REQUIRED_GROUPS = ["Analytics"]
    LOGIN_MESSAGE = "Please login to access this page."
    AUTH_METHOD = "DEV"  # LDAP, SAML, or DEV for no pass.
    LOGIN_REDIRECT_URL = "/"
    NOT_AUTHORIZED_URL = "auth_bp.not_authorized"

    # ldap
    LDAP_HOST = "ldap.host.net"  # defaults to localhost
    LDAP_BASE_DN = "OU=RHC & Offsite Locations,OU=Employees,DC=MyOrg,DC=net"
    LDAP_USER_OBJECT_FILTER = "(|(sAMAccountName=%s)(userPrincipalName=%s))"
    LDAP_USERNAME = "MYORG\\username"
    LDAP_PASSWORD = "password"  # noqa: S105
    LDAP_USE_SSL = True
    LDAP_ATTR_MAP = {
        "account_name": "sAMAccountName",
        "email": "userPrincipalName",
        "full_name": "cn",
        "first_name": "givenName",
    }

    # cache
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300

    # database

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://{user}:{pw}@{url}/{db}".format(
            user="username", pw="password", url="server", db="atlas_automation_hub"
        ),
    ).replace("postgres://", "postgresql://")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "max_overflow": 100,  # how many spare connections we can use?
        "pool_size": 5,  # how many queries will run symultaniously?
    }

    SCHEDULER_HOST = "http://127.0.0.1:5001/api"

    RUNNER_HOST = "http://127.0.0.1:5002/api"

    WEB_HOST = "locahost"

    """
        process executor. must be thread type, not process, otherwise we cannot
        have sql access inside the called functions.
    """
    EXECUTOR_TYPE = "thread"
    EXECUTOR_MAX_WORKERS = 12
    EXECUTOR_PROPAGATE_EXCEPTIONS = True

    # compression
    MINIFY_HTML = True

    # saml config
    BASE_DIR = Path(__file__).resolve().parent
    BASE_URL = "https://automationhub.MyOrg.net/"
    # pylint: disable=C0301
    SAML_CONFIG = {
        "xmlsec_binary": "/usr/bin/xmlsec1",
        "entityid": BASE_URL + "saml2/metadata/",
        "allow_unknown_attributes": True,
        "service": {
            "sp": {
                "name": "Automation Hub SP",
                "name_id_format": saml2.saml.NAMEID_FORMAT_PERSISTENT,
                "allow_unsolicited": True,
                "endpoints": {
                    "assertion_consumer_service": [
                        (BASE_URL + "saml2/acs/", saml2.BINDING_HTTP_POST),
                    ],
                    "single_logout_service": [
                        (BASE_URL + "saml2/ls/", saml2.BINDING_HTTP_REDIRECT),
                        (BASE_URL + "saml2/ls/post/", saml2.BINDING_HTTP_POST),
                    ],
                },
                "force_authn": False,
                "name_id_format_allow_create": True,
                "required_attributes": ["emailAddress"],
                "authn_requests_signed": False,
                "logout_requests_signed": True,
                "want_assertions_signed": True,
                "want_response_signed": False,
            },
        },
        "metadata": {
            "remote": [
                {
                    "url": "https://rhcfs.MyOrg.net/FederationMetadata/2007-06/FederationMetadata.XML",  # noqa: E501
                    "disable_ssl_certificate_validation": True,
                },
            ],
        },
        "debug": 1,
        "key_file": str(BASE_DIR / "publish/cert.key"),  # private part
        "cert_file": str(BASE_DIR / "publish/cert.crt"),  # public part
        "encryption_keypairs": [
            {
                "key_file": str(BASE_DIR / "publish/cert.key"),  # private part
                "cert_file": str(BASE_DIR / "publish/cert.crt"),  # public part
            }
        ],
        "contact_person": [
            {
                "given_name": "First Name",
                "sur_name": "Last Name",
                "company": "Riverside Healthcare",
                "email_address": "em@i.l",
                "contact_type": "technical",
            },
        ],
        "organization": {
            "name": [("Riverside Healthcare", "en")],
            "display_name": [("Riverside Healthcare", "en")],
            "url": [(BASE_URL, "en")],
        },
    }
    SAML_ATTR_MAP = {
        "account_name": "name",
        "email": "emailAddress",
        "last_name": "surname",
        "first_name": "givenName",
        "groups": "group",
    }

    """
        scheduler settings
    """

    SCHEDULER_JOBSTORES = {
        "default": RedisJobStore(
            jobs_key="atlas_hub_jobs",
            run_times_key="atlas_hub_running",
            host=redis_host,
            port=redis_port,
            username=redis_user,
            password=redis_password,
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

    """
       runner settings
    """

    """
        minimum space needed to run tasks
    """
    MIN_DISK_SPACE = 1 * 1024 * 1024 * 1024
    MIN_FREE_MEM_PERC = 3
    MIN_FREE_CPU_PERC = 3

    """
        GIT connection for secure/prive repositories
    """

    GIT_URL = "https://git.example.net/"
    GIT_USERNAME = "username"
    GIT_PASSWORD = r"password"  # noqa: S105
    GIT_TOKEN = r"token"  # noqa: S105
    GIT_VERIFY_SSL = False

    HTTP_VERIFY_SSL = False

    """
        Default SQL Connection Settings
    """
    # minutes
    DEFAULT_SQL_TIMEOUT = 90

    """
        SMB Connection for file storage

        All extracts backups will be stored here.
    """

    SMB_USERNAME = "username"
    SMB_PASSWORD = "password"  # noqa: S105
    SMB_SERVER_IP = "10.0.0.0"
    SMB_SERVER_NAME = "servername"
    SMB_DEFAULT_SHARE = "BackupShare"

    """
        Email connection info
    """
    SMTP_SERVER = "10.0.0.0"
    SMTP_PORT = 25
    SMTP_SENDER_NAME = "⚒️ Atlas Hub"
    SMTP_SENDER_EMAIL = "noreply@example.net"
    SMTP_DEFAULT_RECIEVER = "noreply@example.net"
    SMTP_SUBJECT_PREFIX = "### "

    EXECUTOR_TYPE = "thread"
    EXECUTOR_MAX_WORKERS = 12
    EXECUTOR_PROPAGATE_EXCEPTIONS = True

    PYTHON_TASKS_ENABLED = True

    ROLLUP_BIN = "./node_modules/.bin/rollup"
    ROLLUP_EXTRA_ARGS = ["-c", "rollup.config.mjs"]

    UGLIFYJS_BIN = "./node_modules/.bin/uglifyjs"

    POSTCSS_BIN = "./node_modules/.bin/postcss"


class DevConfig(Config):
    """Configuration overrides for development.

    To Use:
    FLASK_ENV=development
    """

    # pylint: disable=too-few-public-methods

    # authentication override
    AUTH_METHOD = "DEV"

    DEBUG = False
    DEMO = True

    SESSION_COOKIE_SECURE = False

    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # database overrides
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://{user}:{pw}@{url}/{db}".format(
            user="username", pw="password", url="server", db="atlas_hub_dev"
        ),
    ).replace("postgres://", "postgresql://")

    ASSETS_DEBUG = False

    SQLALCHEMY_RECORD_QUERIES = True


class DemoConfig(Config):
    DEBUG = False
    DEMO = True
    AUTH_METHOD = "DEV"
    PYTHON_TASKS_ENABLED = False


class TestConfig(DevConfig):
    """Configuration overrides for dev testing.

    Test config is also used for public demo.

    To Use:
    FLASK_ENV=test
    FLASK_DEBUG=0
    """

    # test db:
    # 1 try to get DATABASE_URL
    # 2 try to build from pieces
    # 3 use sqlite

    # pylint: disable=too-few-public-methods
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres@localhost/atlas_hub_scrap_test"
        # "sqlite:///../test.sqlite",
    ).replace("postgres://", "postgresql://")

    SQLALCHEMY_ENGINE_OPTIONS: dict = {}

    DEMO = True
    TEST = True
    ASSETS_DEBUG = False
    AUTH_METHOD = "DEV"
    DEBUG = False
    from apscheduler.executors.pool import ThreadPoolExecutor

    SCHEDULER_EXECUTORS = {"default": ThreadPoolExecutor(100)}

    # logins for test.
    # docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=@Passw0rd>" -p 1433:1433 --name sql1 -h sql1  -d mcr.microsoft.com/mssql/server:2017-latest
    SQL_SERVER_CONN = "SERVER=127.0.0.1;UID=SA;PWD=@Passw0rd>"

    PG_SERVER_CONN = "host=127.0.0.1 user=postgres password=12345"

    # docker run -p 22:22 -d emberstack/sftp --name sftp
    SFTP_SERVER_USER = "demo"
    SFTP_SERVER_PASS = "demo"

    # docker run -d --name ftpd_server -p 21:21  onekilo79/ftpd_test
    # docker run -d --name ftpd_server -p 21:21 -p 30000-30009:30000-30009 -e FTP_USER_NAME=demo -e FTP_USER_PASS=demo -e FTP_USER_HOME=/home/demo -e "PUBLICHOST=localhost" -e "ADDED_FLAGS=-d -d" stilliard/pure-ftpd
    FTP_SERVER_USER = "demo"
    FTP_SERVER_PASS = "demo"
