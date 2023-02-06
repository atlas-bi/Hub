#!/usr/bin/python3
"""Atlas Hub Installer Helpers."""
import base64
import configparser
import hashlib
import json
import os
import socket
import time
from pathlib import Path

import requests
from colorama import Fore, Style
from tqdm import tqdm


def get_pass() -> str:
    """Create a password based on sha1 of current time."""
    password = hashlib.sha256()
    password.update(str(time.time()).encode("utf-8"))
    return password.hexdigest()


def build_secrets() -> None:
    """Build a secrets.json file."""
    secrets = Path("secrets.json")
    secrets.touch(exist_ok=True)

    try:
        secrets_json = json.loads(secrets.read_text())
    except BaseException:
        secrets_json = {}

    if "PG_PASS" not in secrets_json:
        secrets_json["PG_PASS"] = get_pass()

    if "APP_SECRET" not in secrets_json:
        secrets_json["APP_SECRET"] = get_pass()

    if "FERNET_KEY" not in secrets_json:
        secrets_json["FERNET_KEY"] = base64.urlsafe_b64encode(os.urandom(32)).decode(
            "utf-8"
        )

    secrets.write_text(json.dumps(secrets_json))


def build_web_configuration(install_dir: str, config_ini: str) -> None:
    """Build cust_config.py file from config.ini."""
    configuration = configparser.ConfigParser()
    configuration.read(config_ini)

    if (
        configuration.has_section("MASTER")
        and "EXTERNAL_URL" in configuration["MASTER"]
    ):
        hostname = configuration["MASTER"]["EXTERNAL_URL"]
    else:
        hostname = socket.gethostname()

    secrets = json.loads(Path("secrets.json").read_text())

    config = f"""

from pathlib import Path

import redis
import saml2
import saml2.saml
from apscheduler.jobstores.redis import RedisJobStore

from config import Config as BaseConfig


class Config(BaseConfig):
    ALLOWED_HOSTS = ["{hostname}", "localhost", "127.0.0.1"]
    BASE_URL="{hostname}"
    SECRET_KEY = "{secrets["APP_SECRET"]}"
    PASS_KEY = "{secrets["FERNET_KEY"]}"
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://{{user}}:{{pw}}@{{url}}/{{db}}".format(
        user="atlas_me", pw="{secrets["PG_PASS"]}", url="localhost", db="atlas_hub"
    )
"""

    if configuration.has_section("MASTER"):
        master = configuration["MASTER"]
        if "DATABASE" in configuration["MASTER"]:
            config += f"\n    DATABASE={master['DATABASE']}"

        if "MIN_DISK_SPACE" in configuration["MASTER"]:
            config += f"\n    MIN_DISK_SPACE={master['MIN_DISK_SPACE']}"

        if "MIN_FREE_MEM_PERC" in master:
            config += f"\n    MIN_FREE_MEM_PERC={master['MIN_FREE_MEM_PERC']}"

        if "MIN_FREE_CPU_PERC" in master:
            config += f"\n    MIN_FREE_CPU_PERC={master['MIN_FREE_CPU_PERC']}"

        if "GIT_URL" in master:
            config += f"\n    GIT_URL={master['GIT_URL']}"

        if "GIT_USERNAME" in master:
            config += f"\n    GIT_USERNAME={master['GIT_USERNAME']}"

        if "GIT_PASSWORD" in master:
            config += f"\n    GIT_PASSWORD={master['GIT_PASSWORD']}"

        if "GIT_TOKEN" in master:
            config += f"\n    GIT_TOKEN={master['GIT_TOKEN']}"

        if "GIT_VERIFY_SSL" in master:
            config += f"\n    GIT_VERIFY_SSL={master['GIT_VERIFY_SSL']}"

        if "HTTP_VERIFY_SSL" in master:
            config += f"\n    HTTP_VERIFY_SSL={master['HTTP_VERIFY_SSL']}"

        if "DEFAULT_SQL_TIMEOUT" in master:
            config += f"\n    DEFAULT_SQL_TIMEOUT={master['DEFAULT_SQL_TIMEOUT']}"

        if "SMB_USERNAME" in master:
            config += f"\n    SMB_USERNAME={master['SMB_USERNAME']}"

        if "SMB_PASSWORD" in master:
            config += f"\n    SMB_PASSWORD={master['SMB_PASSWORD']}"

        if "SMB_SERVER_IP" in master:
            config += f"\n    SMB_SERVER_IP={master['SMB_SERVER_IP']}"

        if "SMB_SERVER_NAME" in master:
            config += f"\n    SMB_SERVER_NAME={master['SMB_SERVER_NAME']}"

        if "SMB_DEFAULT_SHARE" in master:
            config += f"\n    SMB_DEFAULT_SHARE={master['SMB_DEFAULT_SHARE']}"
        if "SMTP_SERVER" in master:
            config += f"\n    SMTP_SERVER={master['SMTP_SERVER']}"
        if "SMTP_PORT" in master:
            config += f"\n    SMTP_PORT={master['SMTP_PORT']}"
        if "SMTP_SENDER_NAME" in master:
            config += f"\n    SMTP_SENDER_NAME={master['SMTP_SENDER_NAME']}"
        if "SMTP_SENDER_EMAIL" in master:
            config += f"\n    SMTP_SENDER_EMAIL={master['SMTP_SENDER_EMAIL']}"
        if "SMTP_DEFAULT_RECIEVER" in master:
            config += f"\n    SMTP_DEFAULT_RECIEVER={master['SMTP_DEFAULT_RECIEVER']}"

        if "SMTP_SUBJECT_PREFIX" in master:
            config += f"\n    SMTP_SUBJECT_PREFIX={master['SMTP_SUBJECT_PREFIX']}"
        if "ORG_NAME" in master:
            config += f"\n    ORG_NAME={master['ORG_NAME']}"
        if "AUTH_METHOD" in master:
            config += f"\n    AUTH_METHOD={master['AUTH_METHOD']}"

    if configuration.has_section("LDAP"):
        if "REQUIRED_GROUPS" in configuration["LDAP"]:
            config += (
                f"\n    REQUIRED_GROUPS={configuration['LDAP']['REQUIRED_GROUPS']}"
            )

        if "LDAP_HOST" in configuration["LDAP"]:
            config += f"\n    LDAP_HOST={configuration['LDAP']['LDAP_HOST']}"
        if "LDAP_BASE_DN" in configuration["LDAP"]:
            config += f"\n    LDAP_BASE_DN={configuration['LDAP']['LDAP_BASE_DN']}"
        if "LDAP_USER_OBJECT_FILTER" in configuration["LDAP"]:
            config += f"\n    LDAP_USER_OBJECT_FILTER={configuration['LDAP']['LDAP_USER_OBJECT_FILTER']}"
        if "LDAP_USERNAME" in configuration["LDAP"]:
            config += f"\n    LDAP_USERNAME={configuration['LDAP']['LDAP_USERNAME']}"
        if "LDAP_PASSWORD" in configuration["LDAP"]:
            config += f"\n    LDAP_PASSWORD={configuration['LDAP']['LDAP_PASSWORD']}"

    if (
        configuration.has_section("SAML")
        and "AUTH_METHOD" in configuration["MASTER"]
        and configuration["MASTER"]["AUTH_METHOD"] == "SAML"
    ):
        import subprocess

        xmlsec = (
            subprocess.check_output(["whereis", "xmlsec1"])
            .decode("utf8")
            .splitlines()[0]
            .split(":")[-1]
            .strip()
        )

        remote_meta_url = (
            configuration["SAML"]["REMOTE_META_URL"]
            if "REMOTE_META_URL" in configuration["SAML"]
            else ""
        )
        saml_cert = (
            configuration["SAML"]["SAML_CERT"]
            if "SAML_CERT" in configuration["SAML"]
            else ""
        )
        saml_cert_key = (
            configuration["SAML"]["SAML_CERT_KEY"]
            if "SAML_CERT_KEY" in configuration["SAML"]
            else ""
        )
        contact_first = (
            configuration["SAML"]["CONTACT_PERSON_FIRST_NAME"]
            if "CONTACT_PERSON_FIRST_NAME" in configuration["SAML"]
            else ""
        )
        contact_last = (
            configuration["SAML"]["CONTACT_PERSON_LAST_NAME"]
            if "CONTACT_PERSON_LAST_NAME" in configuration["SAML"]
            else ""
        )
        contact_company = (
            configuration["SAML"]["CONTACT_PERSON_COMPANY"]
            if "CONTACT_PERSON_COMPANY" in configuration["SAML"]
            else ""
        )
        contact_email = (
            configuration["SAML"]["CONTACT_PERSON_EMAIL"]
            if "CONTACT_PERSON_EMAIL" in configuration["SAML"]
            else ""
        )

        config += f"""\n    SAML_CONFIG = {{
    "xmlsec_binary": "{xmlsec}",
    "entityid": BASE_URL + "saml2/metadata/",
    "allow_unknown_attributes": True,
    "service": {{
        "sp": {{
            "name": "Automation Hub SP",
            "name_id_format": saml2.saml.NAMEID_FORMAT_PERSISTENT,
            "allow_unsolicited": True,
            "endpoints": {{
                "assertion_consumer_service": [
                    (BASE_URL + "saml2/acs/", saml2.BINDING_HTTP_POST),
                ],
                "single_logout_service": [
                    (BASE_URL + "saml2/ls/", saml2.BINDING_HTTP_REDIRECT),
                    (BASE_URL + "saml2/ls/post/", saml2.BINDING_HTTP_POST),
                ],
            }},
            "force_authn": False,
            "name_id_format_allow_create": True,
            "required_attributes": ["emailAddress"],
            "authn_requests_signed": False,
            "logout_requests_signed": True,
            "want_assertions_signed": True,
            "want_response_signed": False,
        }},
    }},
    "metadata": {{
        "remote": [
            {{
                "url": "{remote_meta_url}",
                "disable_ssl_certificate_validation": True,
            }},
        ],
    }},
    "debug": 1,
    "key_file": "{saml_cert_key}",
    "cert_file": "{saml_cert_file}",
    "encryption_keypairs": [
        {{
            "key_file": "{saml_cert_key}",
            "cert_file": "{saml_cert_file}",
        }}
    ],
    "contact_person": [
        {{
            "given_name": "{contact_first}",
            "sur_name": "{contact_last}",
            "company": "{contact_company}",
            "email_address": "{contact_email}",
            "contact_type": "technical",
        }},
    ],
    "organization": {{
        "name": [("{contact_company}", "en")],
        "display_name": [("{contact_company}", "en")],
        "url": [(BASE_URL, "en")],
    }},
}}"""

    config_file = Path(install_dir) / "config_cust.py"
    config_file.touch(exist_ok=True)
    config_file.write_text(config)


def build_nginx_configuration(config_ini: str) -> None:
    """Build nginx config from config.ini."""
    atlas_config = configparser.ConfigParser()
    atlas_config.read(config_ini)

    hostname = (
        atlas_config["MASTER"]["EXTERNAL_URL"]
        if atlas_config.has_section("MASTER")
        and "EXTERNAL_URL" in atlas_config["MASTER"]
        else socket.gethostname()
    )

    if (
        atlas_config.has_section("NGINX")
        and "NGINX_HTTPS_CERT" in atlas_config["NGINX"]
        and "NGINX_HTTPS_CERT_KEY" in atlas_config["NGINX"]
    ):
        config = f"""
server {{
    listen 80;
    server_name {hostname};
    return 301 https://{hostname}$request_uri;
}}

server {{
    listen 443 ssl http2;
    ssl_certificate {atlas_config["NGINX"]["NGINX_HTTPS_CERT"]};
    ssl_certificate_key {atlas_config["NGINX"]["NGINX_HTTPS_CERT_KEY"]};
    server_name {hostname};

    location /static {{
        access_log   off;
        alias /usr/lib/atlas-hub/app/web/static/;
    }}

    location / {{
        access_log   off;
        include proxy_params;
        proxy_pass http://unix:/usr/lib/atlas-hub/app/gunicorn.sock;
    }}
}}
"""

    else:
        config = f"""
server {{
    listen 80;
    server_name {hostname} localhost 127.0.0.1;

    location /static {{
        access_log   off;
        alias /usr/lib/atlas-hub/app/web/static/;
    }}

    location / {{
        access_log   off;
        include proxy_params;
        proxy_pass http://unix:/usr/lib/atlas-hub/app/web.sock;
    }}
}}
"""

    # add in standard config for runner and scheduler
    config += f"""
# localhost configcur
server {{
    listen 80;
    server_name localhost 127.0.0.1;

    location /static {{
        access_log   off;
        alias /usr/lib/atlas-hub/app/web/static/;
    }}

    location / {{
        access_log   off;
        include proxy_params;
        proxy_pass http://unix:/usr/lib/atlas-hub/app/web.sock;
    }}
}}
server {{
    listen 5002;
    server_name 127.0.0.1;

    location / {{
        access_log   off;
        include proxy_params;
        proxy_pass http://unix:/usr/lib/atlas-hub/app/runner.sock;
    }}
}}

server {{
    listen 5001;
    server_name 127.0.0.1;

    location / {{
        access_log   off;
        include proxy_params;
        proxy_pass http://unix:/usr/lib/atlas-hub/app/scheduler.sock;
    }}
}}
"""

    # save to config file
    Path("/etc/nginx/sites-available/atlas-hub").write_text(config)

    # link to enabled configs
    if os.path.islink("/etc/nginx/sites-enabled/atlas-hub"):
        os.unlink("/etc/nginx/sites-enabled/atlas-hub")
    os.symlink(
        "/etc/nginx/sites-available/atlas-hub", "/etc/nginx/sites-enabled/atlas-hub"
    )


def download(url: str, name: str, outfile: str) -> None:
    """Download a file with progress bar."""
    bar_message = "{}{}{} {}{{n_fmt}}/{{total_fmt}}{} {{bar}} {}{{elapsed}} {{rate_fmt}}{{postfix}}{}".format(
        Fore.BLUE + Style.BRIGHT,
        "Downloading " + name,
        Style.RESET_ALL,
        Fore.RED + Style.BRIGHT,
        Style.RESET_ALL,
        Fore.GREEN + Style.BRIGHT,
        Style.RESET_ALL + "    ",
    )

    in_file = requests.get(url, stream=True)

    total_size = int(in_file.headers.get("Content-Length", 0))
    initial_size = total_size

    elapsed = "00:00"
    with tqdm(
        total=total_size,
        bar_format=bar_message,
        colour="BLUE",
        ascii="┈━",
        leave=False,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        with open(outfile, "wb") as out_file:
            for chunk in in_file.iter_content(chunk_size=1024):
                pbar.update(len(chunk))

                # if size was unknown, we will know it now.
                if initial_size == 0:
                    total_size += len(chunk)

                elapsed = pbar.format_interval(pbar.format_dict["elapsed"])

                out_file.write(chunk)

    finshed_bar_message = (
        "{}{}{} {}{{n_fmt}}/{{total_fmt}}{} {{bar}} {}{}{}    ".format(
            Fore.BLUE + Style.BRIGHT,
            "Downloaded " + name,
            Style.RESET_ALL,
            Fore.GREEN + Style.BRIGHT,
            Style.RESET_ALL,
            Fore.GREEN + Style.BRIGHT,
            elapsed,
            Style.RESET_ALL,
        )
    )

    finished_bar = tqdm(
        total=total_size,
        initial=total_size,
        bar_format=finshed_bar_message,
        colour="GREEN",
        ascii="┈━",
        leave=True,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
    )
    finished_bar.close()
