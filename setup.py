"""
    Extract Management 2.0 setup script

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

from setuptools import setup

setup(
    name="Extract Management 2.0",
    packages=["em"],
    include_package_data=True,
    install_requires=[
        "cssmin",
        "Flask",
        "Flask-APScheduler",
        "Flask-Assets",
        "Flask-Caching",
        "Flask-Compress",
        "Jinja2",
        "jsmin",
        "SQLAlchemy",
        "python-ldap",
        "flask_mail",
        "flask_sqlalchemy",
        "flask_migrate",
        "flask_script",
        "fabric",
        "requests",
        "bs4",
        "pyodbc",
        "flask-executor",
        "psycopg2-binary",
        "black",
        "Flask-SQLAlchemy-Caching",
        "num2words",
        "pysmb",
        "pycrypto",
        "rcssmin",
        "virtualenv",
        "python-dateutil",
        "psutil",
        "flask-debugtoolbar",
        "flask-login",
        "python3-saml",
        "xmlsec",
        "gevent",
    ],
)
