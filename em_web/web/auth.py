"""Login/Logout web views."""
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
from flask import flash, redirect, render_template, request
from flask_login import current_user, login_required, login_user, logout_user
from is_safe_url import is_safe_url

from em_web import db, executor
from em_web.model import Login, User

from .ldap_auth import LDAP
from .saml_auth import SAML

auth_bp = Blueprint("auth_bp", __name__)


@app.login_manager.user_loader
def load_user(user_id):
    """Get user."""
    return User.query.filter_by(id=user_id).first()


@auth_bp.route("/not_authorized")
def not_authorized():
    """Return not authorized template."""
    return render_template("not_authorized.html.j2", title="Not Authorized")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login page.

    :url: /login
    :returns: webpage
    """
    if current_user.get_id():
        next_url = request.args.get("next", default="/")

        if not is_safe_url(next_url, app.config["ALLOWED_HOSTS"]):
            return abort(400)

        return redirect(next_url)

    if request.method == "POST":
        user = request.form.get("user")
        password = request.form.get("password")

        if app.config["AUTH_METHOD"] == "LDAP":
            ldap = LDAP(app)
            ldap_details = ldap.bind_user(user, password)

            if ldap_details is None or password == "":  # noqa: S105
                executor.submit(log_login, request.form["user"], 3)

                flash("Invalid login, please try again!")
                return render_template("pages/login.html.j2")

            # require specific user group
            if "REQUIRED_GROUPS" in app.config and not set(
                app.config["REQUIRED_GROUPS"]
            ).issubset(set(ldap.get_user_groups(user=user.lower()))):
                executor.submit(log_login, request.form["user"], 3)

                flash(
                    "You must be part of the %s group(s) to use this site."
                    % app.config["REQUIRED_GROUPS"]
                )
                return render_template("pages/login.html.j2")

            executor.submit(log_login, request.form["user"], 1)

            user = User.query.filter(
                (User.account_name == user.lower()) | (User.email == user.lower())
            ).first()

            # if user isn't existing, create
            if not user:
                user = User()

            # update user attributes
            user.account_name = (
                ldap_details.get(app.config["LDAP_ATTR_MAP"]["account_name"])[0]
                .decode("utf-8")
                .lower()
            )
            user.email = (
                ldap_details.get(app.config["LDAP_ATTR_MAP"]["email"])[0]
                .decode("utf-8")
                .lower()
            )
            user.full_name = ldap_details.get(app.config["LDAP_ATTR_MAP"]["full_name"])[
                0
            ].decode("utf-8")
            user.first_name = ldap_details.get(
                app.config["LDAP_ATTR_MAP"]["first_name"]
            )[0].decode("utf-8")

            db.session.add(user)
            db.session.commit()

            login_user(user, remember=True)

            next_url = request.args.get("next", default="/")

            if not is_safe_url(next_url, app.config["ALLOWED_HOSTS"]):
                return abort(400)

            return redirect(next_url)

        if app.config["AUTH_METHOD"] == "DEV":
            user = User.query.filter(
                (User.account_name == user.lower()) | (User.email == user.lower())
            ).first()

            if user:
                login_user(user, remember=True)
            else:
                flash("Invalid login, please try again!")

            next_url = request.args.get("next", default="/")

            if not is_safe_url(next_url, app.config["ALLOWED_HOSTS"]):
                return abort(400)

            return redirect(next_url)

        # if login methods fail, add flash message
        flash("Invalid login, please try again!")

    # saml does not have a login page but redirects to idp
    if app.config["AUTH_METHOD"] == "SAML":
        saml = SAML(app)
        saml_client = saml.saml_client_for()
        # pylint: disable=W0612
        reqid, info = saml_client.prepare_for_authenticate()

        redirect_url = None
        # Select the IdP URL to send the AuthN request to
        for key, value in info["headers"]:
            if key == "Location":
                redirect_url = value

        return redirect(redirect_url)

    return render_template("pages/login.html.j2", title="Login")


@auth_bp.route("/logout")
@login_required
def logout():
    """User logout page.

    :url: /logout
    :returns: webpage
    """
    executor.submit(log_login, current_user.account_name or "undefined", 2)
    logout_user()

    return render_template("pages/logout.html.j2", title="Logout")


def log_login(name, type_id):
    """Log all login/logout attempts.

    :param name (str): name of user performing action
    :param type_id (int): id of event type
    """
    me = Login(username=name, type_id=type_id)
    db.session.add(me)
    db.session.commit()
