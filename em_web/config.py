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

import os
from pathlib import Path

import redis
import saml2
import saml2.saml


class Config:
    """All configuration set here. For dev there are overrides below."""

    # pylint: disable=too-few-public-methods

    ALLOWED_HOSTS = ["*", "localhost"]

    DEBUG = False
    TESTING = False
    DEMO = False

    # https://stackoverflow.com/a/50575445/10265880
    # dd if=/dev/urandom bs=32 count=1 2>/dev/null | openssl base64
    SECRET_KEY = b"hAGBYwfuCRkBFvf1l0JyJZQA9VTqo6sl6scdCUt0T+Y="  # noqa: S105
    IV_KEY = b"hAGBYwfuCRkBFvf1l0JyJZQA9VTqo6sl6scdCUt0T+Y="  # noqa: S105
    PASS_KEY = b"hAGBYwfuCRkBFvf1l0JyJZQA9VTqo6sl6scdCUt0T+Y="  # noqa: S105

    # redis sessions
    SESSION_TYPE = "redis"

    if os.environ.get("REDIS_URL"):
        SESSION_REDIS = redis.Redis.from_url(os.environ.get("REDIS_URL"))  # type: ignore
    else:
        SESSION_REDIS = redis.Redis(host="localhost", port=6379)  # type: ignore

    # authentication
    LOGIN_VIEW = "auth_bp.login"
    REQUIRED_GROUPS = [b"Analytics"]
    LOGIN_MESSAGE = "Please login to access this page."
    AUTH_METHOD = "SAML"  # LDAP, SAML, or DEV for no pass.
    LOGIN_REDIRECT_URL = "/"
    NOT_AUTHORIZED_URL = "auth_bp.not_authorized"

    # ldap
    LDAP_HOST = "10.0.0.0"  # defaults to localhost
    LDAP_BASE_DN = "OU=People,OU=Employees,DC=Org"
    LDAP_USER_OBJECT_FILTER = "(|(sAMAccountName=%s)(userPrincipalName=%s))"
    LDAP_USERNAME = "username"
    LDAP_PASSWORD = "password"  # noqa: S105
    LDAP_USE_SSL = True
    LDAP_ATTR_MAP = {
        "account_name": "sAMAccountName",
        "email": "userPrincipalName",
        "full_name": "cn",
        "first_name": "givenName",
    }

    # cache
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300

    # database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://{user}:{pw}@{url}/{db}".format(
            user="webapp", pw="nothing", url="localhost", db="em_web"
        ).replace("postgres://", "postgresql://"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "max_overflow": 100,  # how many spare connections we can use?
        "pool_size": 5,  # how many queries will run symultaniously?
    }

    SCHEUDULER_HOST = "http://127.0.0.1:5001/api"

    RUNNER_HOST = "http://127.0.0.1:5002/api"

    WEB_HOST = "http://127.0.0.1"  # noqa: S104

    """
        process executor. must be thread type, not process, otherwise we cannot
        have sql access inside the called functions.
    """

    EXECUTOR_TYPE = "thread"
    EXECUTOR_MAX_WORKERS = 12
    EXECUTOR_PROPAGATE_EXCEPTIONS = True
    REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")

    # compression
    MINIFY_HTML = True

    # migrations
    MIGRATIONS = "migrations"

    # saml config
    BASE_DIR = Path(__file__).resolve().parent.parent
    BASE_URL = "https://taskscheduler.me.net/"
    # pylint: disable=C0301
    SAML_CONFIG = {
        "xmlsec_binary": "/usr/bin/xmlsec1",
        "entityid": BASE_URL + "saml2/metadata/",
        "allow_unknown_attributes": True,
        "service": {
            "sp": {
                "name": "Atlas of Information Management SP",
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
                    "url": "https://your.org.net/FederationMetadata/2007-06/FederationMetadata.XML",  # noqa: E501
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
                "given_name": "Mr",
                "sur_name": "Cool",
                "company": "Hospital",
                "email_address": "mr@co.ol",
                "contact_type": "technical",
            },
        ],
        "organization": {
            "name": [("Hospital", "en")],
            "display_name": [("Hospital", "en")],
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


class DevConfig(Config):
    """Configuration overides for development.

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

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://{user}:{pw}@{url}/{db}".format(
            user="webapp", pw="nothing", url="localhost", db="em_web_dev"
        ).replace("postgres://", "postgresql://"),
    )

    # migrations override
    MIGRATIONS = "migrations_dev"

    if os.environ.get("REDIS_URL"):
        SESSION_REDIS = redis.Redis.from_url(os.environ.get("REDIS_URL"))  # type: ignore
    else:
        SESSION_REDIS = redis.Redis(host="redis", port=6379)  # type: ignore
    REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")


class TestConfig(DevConfig):
    """Configuration overrides for dev testing.

    To Use:
    FLASK_ENV=test
    FLASK_DEBUG=0
    """

    # pylint: disable=too-few-public-methods
    SQLALCHEMY_DATABASE_URI = "sqlite:///../test.sqlite"
    SQLALCHEMY_ENGINE_OPTIONS: dict = {}
    MIGRATIONS = "migrations_test"

    DEMO = True
    TEST = True
    AUTH_METHOD = "DEV"
    DEBUG = False
