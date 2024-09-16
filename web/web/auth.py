"""Login/Logout web views."""

from typing import Union

from flask import Blueprint, abort
from flask import current_app as app
from flask import flash, redirect, render_template, request, session
from flask_login import current_user, login_user, logout_user
from is_safe_url import is_safe_url
from werkzeug import Response

from web import db, executor
from web.model import Login, User

from .ldap_auth import LDAP
from .saml_auth import SAML

auth_bp = Blueprint("auth_bp", __name__)


@app.login_manager.user_loader
def load_user(user_id: int) -> User:
    """Get user."""
    return User.query.filter_by(id=user_id).first()


@auth_bp.route("/not_authorized")
def not_authorized() -> str:
    """Return not authorized template."""
    return render_template("not_authorized.html.j2", title="Not Authorized")


@auth_bp.route("/login", methods=["GET", "POST"])
def login() -> Union[str, Response]:
    """User login page."""
    if current_user.get_id():
        next_url = request.args.get("next", default="/")

        if is_safe_url(next_url, app.config["ALLOWED_HOSTS"]) is False:
            return abort(400)

        return redirect(next_url)

    # if demo, login as first user
    if app.config.get("DEMO"):
        session.pop("_flashes", None)

        user = User.query.first()

        if user:
            login_user(user, remember=True)
        else:
            flash("Something broke!")

        next_url = request.args.get("next", default="/")

        if is_safe_url(next_url, app.config["ALLOWED_HOSTS"]) is False:
            return abort(400)

        return redirect(next_url)

    if request.method == "POST" and app.config["AUTH_METHOD"] in ["LDAP", "DEV"]:
        user = request.form.get("user", "")
        password = request.form.get("password", "")

        if app.config["AUTH_METHOD"] == "LDAP":  # pragma: no cover
            ldap = LDAP(app)  # type: ignore[no-untyped-call]
            ldap_details = ldap.bind_user(user, password)  # type: ignore[no-untyped-call]

            if ldap_details is None or password == "":  # noqa: S105
                executor.submit(log_login, request.form["user"], 3)

                flash("Invalid login, please try again!")
                return render_template("pages/login.html.j2", title="Login")

            # require specific user group
            # fmt: off
            if "REQUIRED_GROUPS" in app.config and not bool(set(
                app.config["REQUIRED_GROUPS"]
            ) &
                set(ldap.get_user_groups(user=user.lower()))  # type: ignore[no-untyped-call]
            ):
                executor.submit(log_login, request.form["user"], 3)

                flash(
                    "You must be part of the %s group(s) to use this site."
                    % app.config["REQUIRED_GROUPS"]
                )
                return render_template("pages/login.html.j2", title="Login")
            # fmt: on
            executor.submit(log_login, request.form["user"], 1)

            user = User.query.filter(
                (User.account_name == user.lower()) | (User.email == user.lower())
            ).first()

            # if user isn't existing, create
            if not user:
                user = User()  # type: ignore[call-arg]

            # update user attributes
            user.account_name = (
                ldap_details.get(app.config["LDAP_ATTR_MAP"]["account_name"])[0]
                .decode("utf-8")
                .lower()
            )
            user.email = (
                ldap_details.get(app.config["LDAP_ATTR_MAP"]["email"])[0].decode("utf-8").lower()
            )
            user.full_name = ldap_details.get(app.config["LDAP_ATTR_MAP"]["full_name"])[0].decode(
                "utf-8"
            )
            user.first_name = ldap_details.get(app.config["LDAP_ATTR_MAP"]["first_name"])[
                0
            ].decode("utf-8")

            db.session.add(user)
            db.session.commit()

            login_user(user, remember=True)

            next_url = request.args.get("next", default="/")

            if is_safe_url(next_url, app.config["ALLOWED_HOSTS"]) is False:
                return abort(400)

            return redirect(next_url)

        if app.config["AUTH_METHOD"] == "DEV":  # pragma: no cover
            user = User.query.filter(
                (User.account_name == user.lower()) | (User.email == user.lower())
            ).first()

            if user:
                login_user(user, remember=True)
            else:
                flash("Invalid login, please try again!")

            next_url = request.args.get("next", default="/")

            if is_safe_url(next_url, app.config["ALLOWED_HOSTS"]) is False:
                return abort(400)

            return redirect(next_url)

        # if login methods fail, add flash message
        flash("Invalid login, please try again!")

    # saml does not have a login page but redirects to idp
    if app.config["AUTH_METHOD"] == "SAML":  # pragma: no cover
        saml = SAML(app)
        saml_client = saml.saml_client_for()
        # pylint: disable=W0612
        reqid, info = saml_client.prepare_for_authenticate()

        redirect_url = ""
        # Select the IdP URL to send the AuthN request to
        for key, value in info["headers"]:
            if key == "Location":
                redirect_url = value

        # add next url to request to be appropriatly redirected
        # after a successful login
        next_url = request.args.get("next", "/")
        if is_safe_url(next_url, app.config["ALLOWED_HOSTS"]):
            redirect_url += "&RelayState=" + next_url

        return redirect(redirect_url)

    return render_template("pages/login.html.j2", title="Login")


@auth_bp.route("/logout")
def logout() -> str:
    """User logout page."""
    executor.submit(log_login, current_user.account_name or "undefined", 2)
    logout_user()

    return render_template("pages/logout.html.j2", title="Logout")


def log_login(name: str, type_id: int) -> None:
    """Log all login/logout attempts."""
    me = Login(username=name, type_id=type_id)
    db.session.add(me)
    db.session.commit()
