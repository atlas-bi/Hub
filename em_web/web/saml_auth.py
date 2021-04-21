"""SAML Login/Logout web views."""
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


from flask import Blueprint, abort
from flask import current_app as app
from flask import flash, make_response, redirect, request
from is_safe_url import is_safe_url
from saml2 import entity
from saml2.client import Saml2Client
from saml2.config import Config as Saml2Config
from saml2.metadata import entity_descriptor
from saml2.sigver import SignatureError

from em_web import db
from em_web.model import User

login_bp = Blueprint("login_bp", __name__)

import logging

from flask_login import login_user


class SAML:
    """SAML Authentication."""

    def __init__(self, flask_app):
        """Init class."""
        self.app = flask_app

    # pylint: disable=R0201
    def saml_client_for(self):
        """Build SAML client."""
        sp_config = Saml2Config()
        sp_config.load(app.config["SAML_CONFIG"])
        saml_client = Saml2Client(config=sp_config)

        return saml_client


@login_bp.route("/saml2/acs/", methods=["POST"])
def idp_initiated():
    """Get response from IDP."""
    try:
        saml = SAML(app)
        saml_client = saml.saml_client_for()
        authn_response = saml_client.parse_authn_request_response(
            request.form["SAMLResponse"], entity.BINDING_HTTP_POST
        )

        identity = authn_response.get_identity()

        if "REQUIRED_GROUPS" in app.config and not set(
            app.config["REQUIRED_GROUPS"]
        ).issubset(set(identity.get(app.config["SAML_ATTR_MAP"]["groups"]))):
            # user is not authorized.
            flash(
                "You must be part of the %s group(s) to use this site."
                % app.config["REQUIRED_GROUPS"]
            )
            redirect(app.config["NOT_AUTHORIZED_URL"])

        logging.warning(identity)

        if identity:
            account_name = identity.get(app.config["SAML_ATTR_MAP"]["account_name"])[
                0
            ].lower()

            email = identity.get(app.config["SAML_ATTR_MAP"]["email"])[0].lower()

            user = User.query.filter(
                (User.account_name == account_name) | (User.email == email)
            ).first()

            # if user isn't existing, create
            if not user:
                user = User()

            # update user attributes
            user.account_name = account_name
            user.email = email

            user.full_name = "%s %s" % (
                identity.get(app.config["SAML_ATTR_MAP"]["first_name"])[0],
                identity.get(app.config["SAML_ATTR_MAP"]["last_name"])[0],
            )

            user.first_name = identity.get(app.config["SAML_ATTR_MAP"]["first_name"])[0]

            db.session.add(user)
            db.session.commit()

            login_user(user, remember=True)

            next_url = (
                request.args.get("next")
                or request.args.get("RelayState")
                or app.config["LOGIN_REDIRECT_URL"]
            )

            if not is_safe_url(next_url, app.config["ALLOWED_HOSTS"]):
                return abort(400)

            return redirect(next_url)
        return redirect(app.congif["LOGIN_VIEW"])

    except SignatureError as e:
        flash(str(e))
        return redirect(app.congif["SAML_ATTR_MAP"])


@login_bp.route("/saml2/metadata/")
def build_metadata():
    """Build saml metadata."""
    conf = Saml2Config()
    conf.load(app.config["SAML_CONFIG"])
    metadata = entity_descriptor(conf)
    response = make_response(str(metadata).encode("utf-8"))
    response.headers["content-type"] = "text/xml; charset=utf-8"
    return response
