"""
    contains all login/logout routes

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

from flask import g, redirect, url_for, render_template, request, session
from em import app, ldap, executor, db
import em.messages as messages
from ..model.auth import Login


# validate user
@app.before_request
def before_request():
    """ checks and reloads auth before each request """
    # if "user_id" in session:
    g.user = []  # ldap.get_object_details(user=session["user_id"], dn_only=False)
    g.user_id = "1234"  # g.user["employeeID"][0].decode("utf-8")
    g.user_full_name = "Boss Man"  # g.user["name"][0].decode("utf-8")
    g.ldap_groups = []  # ldap.get_user_groups(user=session["user_id"])


# login page
@app.route("/login", methods=["GET", "POST"])
def login():
    """ user login route """
    if "user" in g and g.user:
        return redirect(url_for("dash"))

    if request.method == "POST":
        user = request.form["user"]
        password = request.form["password"]
        test = ldap.bind_user(user, password)

        if test is None or password == "":
            executor.submit(log_login, request.form["user"], 3)
            return render_template(
                "pages/login.html.j2", message=messages.messages["login-invalid"]
            )

        session["user_id"] = request.form["user"].lower()

        g.user = ldap.get_object_details(user=session["user_id"], dn_only=False)
        g.user_id = g.user["employeeID"][0].decode("utf-8")
        g.user_full_name = g.user["name"][0].decode("utf-8")
        g.ldap_groups = ldap.get_user_groups(user=session["user_id"])

        executor.submit(log_login, g.user_full_name, 1)
        return redirect("/")

    return render_template("pages/login.html.j2", title="Login")


# logout page
@app.route("/logout")
def logout():
    """ user logout route """
    executor.submit(log_login, session["user_id"], 2)
    session.pop("user_id", None)
    return render_template("pages/logout.html.j2", title="Logout")


# keep auto history
def log_login(name, type_id):
    """ keeps all login/logout attempts in the db. """
    me = Login(username=name, type_id=type_id)
    db.session.add(me)
    db.session.commit()
