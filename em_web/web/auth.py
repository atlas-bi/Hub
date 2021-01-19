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


from flask import Blueprint
from flask import current_app as app
from flask import redirect, render_template, request, session, url_for

from em_web import db, executor, ldap
from em_web.model import Login, User

auth_bp = Blueprint("auth_bp", __name__)



def before_request():
    """Validate user and reloads auth before each request."""
    if "username" in session:
        session["user"] = ldap.get_object_details(
            user=session.get("username"), dn_only=False
        )
        if session.get("user"):
            session["user_id"] = (
                session.get("user").get("employeeID")
                or session.get("user").get("sAMAccountName")
            )[0].decode("utf-8")
            session["user_full_name"] = (
                session.get("user").get("name")[0].decode("utf-8")
            )
            session["ldap_groups"] = ldap.get_user_groups(user=session.get("username"))

        # if user does not exist, save their data
        me = User.query.filter_by(user_id=session.get("user_id")).count()
        if me < 1:
            me = User(
                user_id=session.get("user_id"), full_name=session.get("user_full_name")
            )
            db.session.add(me)
            db.session.commit()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login page.

    :url: /login
    :returns: webpage
    """
    if session.get("user"):
        return redirect(url_for("dashboard_bp.dash"))

    if request.method == "POST":
        user = request.form.get("user")
        password = request.form.get("password")
        test = ldap.bind_user(user, password)

        if test is None or password == "":  # noqa: S105
            executor.submit(log_login, request.form["user"], 3)
            return render_template(
                "pages/login.html.j2", message="Invalid login, please try again!"
            )

        session["username"] = request.form.get("user").lower()
        session["user"] = ldap.get_object_details(
            user=session.get("username"), dn_only=False
        )
        session["user_id"] = (
            session.get("user").get("employeeID")
            or session.get("user").get("sAMAccountName")
        )[0].decode("utf-8")
        session["user_full_name"] = session.get("user").get("name")[0].decode("utf-8")
        session["ldap_groups"] = ldap.get_user_groups(user=session.get("username"))

        executor.submit(log_login, session.get("user_full_name"), 1)
        return redirect("/")

    return render_template("pages/login.html.j2", title="Login")


@auth_bp.route("/logout")
def logout():
    """User logout page.

    :url: /logout
    :returns: webpage
    """
    executor.submit(log_login, session.get("username") or "undefined", 2)
    session.pop("username", None)
    session.pop("user", None)
    session.pop("user_id", None)
    session.pop("user_full_name", None)
    session.pop("ldap_groups", None)
    return render_template("pages/logout.html.j2", title="Logout")


def log_login(name, type_id):
    """Log all login/logout attempts.

    :param name (str): name of user performing action
    :param type_id (int): id of event type
    """
    me = Login(username=name, type_id=type_id)
    db.session.add(me)
    db.session.commit()

    # if user does not exist, save their data
    me = User.query.filter_by(user_id=session.get("user_id")).count()
    if me < 1 and type_id == 1:
        me = User(
            user_id=session.get("user_id"), full_name=session.get("user_full_name")
        )
        db.session.add(me)
        db.session.commit()
