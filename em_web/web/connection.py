"""External Connection web views."""
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


import sys
from pathlib import Path

from crypto import em_encrypt
from flask import Blueprint
from flask import current_app as app
from flask import redirect, render_template, request, session, url_for

from em_web import db, ldap
from em_web.model import (
    Connection,
    ConnectionDatabase,
    ConnectionDatabaseType,
    ConnectionFtp,
    ConnectionGpg,
    ConnectionSftp,
    ConnectionSmb,
    ConnectionSsh,
    TaskLog,
)

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")


connection_bp = Blueprint("connection_bp", __name__)


@connection_bp.route("/connection")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection():
    """List connections.

    :url: /connection

    :returns: html webpage.
    """
    connections = Connection.query.order_by(Connection.name).all()

    my_database_types = ConnectionDatabaseType.query.order_by(
        ConnectionDatabaseType.name
    ).all()
    return render_template(
        "pages/connection/all.html.j2",
        connections=connections,
        title="Destination",
        database_types=my_database_types,
    )


@connection_bp.route("/connection/<connection_id>", methods=["POST", "GET"])
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_edit(connection_id):
    """Get or edit existing connections.

    :url: /connection/<connection_id>
    :param connection_id: connection id

    :returns: redirects to connection in question.
    """
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    my_connection = Connection.query.filter_by(id=connection_id).first()
    my_database_types = ConnectionDatabaseType.query.order_by(
        ConnectionDatabaseType.name
    ).all()

    if request.method == "GET":
        return render_template(
            "pages/connection/one.html.j2",
            connection=my_connection,
            database_types=my_database_types,
            title=my_connection.name,
        )

    form = request.form
    my_connection.name = form["name"]
    my_connection.description = form.get("desc")
    my_connection.address = form.get("addr")
    my_connection.primary_contact = form.get("contact")
    my_connection.primary_contact_email = form.get("email")
    my_connection.primary_contact_phone = form.get("phone")
    db.session.commit()

    # update sftp
    sftp_list = [
        k.split("sftp")[1].split("-")[0]
        for k, v in form.items()
        if k.startswith("sftp") and "name" in k
    ]
    for sftp in sftp_list:
        # try to get first, else create.
        if ConnectionSftp.query.filter_by(connection_id=connection_id, id=sftp).count():
            sftp_conn = ConnectionSftp.query.filter_by(
                connection_id=connection_id, id=sftp
            ).first()
        else:
            sftp_conn = ConnectionSftp(connection_id=my_connection.id)
            db.session.add(sftp_conn)

        sftp_conn.connection_id = my_connection.id
        sftp_conn.name = form["sftp" + sftp + "-name"]
        sftp_conn.address = form["sftp" + sftp + "-addr"]
        sftp_conn.port = form.get("sftp" + sftp + "-port") or 22
        sftp_conn.path = form["sftp" + sftp + "-path"]
        sftp_conn.username = (
            form["sftp" + sftp + "-user"] if form.get("sftp" + sftp + "-user") else ""
        )
        sftp_conn.key = (
            em_encrypt(form["sftp" + sftp + "-key"], app.config["PASS_KEY"])
            if form.get("sftp" + sftp + "-key")
            else None
        )
        sftp_conn.password = em_encrypt(
            form["sftp" + sftp + "-pass"], app.config["PASS_KEY"]
        )

        db.session.commit()

        log = TaskLog(
            status_id=7,
            message=session.get("user_full_name")
            + ": Connection Sftp edited. ("
            + str(my_connection.id)
            + " "
            + my_connection.name
            + " "
            + str(sftp_conn.connection_id)
            + " "
            + sftp_conn.name
            + ")",
        )
        db.session.add(log)
        db.session.commit()

    # update ssh
    ssh_list = [
        k.split("ssh")[1].split("-")[0]
        for k, v in form.items()
        if k.startswith("ssh") and "name" in k
    ]
    for ssh in ssh_list:
        # try to get first, else create.
        if ConnectionSsh.query.filter_by(connection_id=connection_id, id=ssh).count():
            ssh_conn = ConnectionSsh.query.filter_by(
                connection_id=connection_id, id=ssh
            ).first()
        else:
            ssh_conn = ConnectionSsh(connection_id=my_connection.id)
            db.session.add(ssh_conn)

        ssh_conn.connection_id = my_connection.id
        ssh_conn.name = form["ssh" + ssh + "-name"]
        ssh_conn.address = form["ssh" + ssh + "-addr"]
        ssh_conn.port = form.get("ssh" + ssh + "-port") or 22
        ssh_conn.username = form["ssh" + ssh + "-user"]
        ssh_conn.password = em_encrypt(
            form["ssh" + ssh + "-pass"], app.config["PASS_KEY"]
        )

        db.session.commit()

        log = TaskLog(
            status_id=7,
            message=session.get("user_full_name")
            + ": Connection Sftp edited. ("
            + str(my_connection.id)
            + " "
            + my_connection.name
            + " "
            + str(ssh_conn.connection_id)
            + " "
            + ssh_conn.name
            + ")",
        )
        db.session.add(log)
        db.session.commit()

    # update ftp
    ftp_list = [
        k.split("ftp")[1].split("-")[0]
        for k, v in form.items()
        if k.startswith("ftp") and "name" in k
    ]
    for ftp in ftp_list:
        # try to get first, else create.
        if ConnectionFtp.query.filter_by(connection_id=connection_id, id=ftp).count():
            ftp_conn = ConnectionFtp.query.filter_by(
                connection_id=connection_id, id=ftp
            ).first()
        else:
            ftp_conn = ConnectionFtp(connection_id=my_connection.id)
            db.session.add(ftp_conn)

        ftp_conn.connection_id = my_connection.id
        ftp_conn.name = form["ftp" + ftp + "-name"]
        ftp_conn.address = form["ftp" + ftp + "-addr"]
        ftp_conn.path = form["ftp" + ftp + "-path"]
        ftp_conn.username = form["ftp" + ftp + "-user"]
        ftp_conn.password = em_encrypt(
            form["ftp" + ftp + "-pass"], app.config["PASS_KEY"]
        )

        db.session.commit()

        log = TaskLog(
            status_id=7,
            message=session.get("user_full_name")
            + ": Connection Ftp edited. ("
            + str(my_connection.id)
            + " "
            + my_connection.name
            + " "
            + str(ftp_conn.connection_id)
            + " "
            + ftp_conn.name
            + ")",
        )
        db.session.add(log)
        db.session.commit()

    # update smb
    smb_list = [
        k.split("smb")[1].split("-")[0]
        for k, v in form.items()
        if k.startswith("smb") and "name" in k
    ]

    for smb in smb_list:
        # try to get first, else create.
        if ConnectionSmb.query.filter_by(connection_id=connection_id, id=smb).count():
            smb_conn = ConnectionSmb.query.filter_by(
                connection_id=connection_id, id=smb
            ).first()
        else:
            smb_conn = ConnectionSmb(connection_id=my_connection.id)
            db.session.add(smb_conn)

        smb_conn.connection_id = my_connection.id
        smb_conn.name = form["smb" + smb + "-name"]
        smb_conn.server_name = form["smb" + smb + "-server-name"]
        smb_conn.server_ip = form["smb" + smb + "-server-ip"]
        smb_conn.share_name = form["smb" + smb + "-share-name"]
        smb_conn.path = form["smb" + smb + "-path"]
        smb_conn.username = form["smb" + smb + "-user"]
        smb_conn.password = em_encrypt(
            form["smb" + smb + "-pass"], app.config["PASS_KEY"]
        )

        db.session.commit()

        log = TaskLog(
            status_id=7,
            message=session.get("user_full_name")
            + ": Connection Smb edited. ("
            + str(my_connection.id)
            + " "
            + my_connection.name
            + " "
            + str(smb_conn.connection_id)
            + " "
            + smb_conn.name
            + ")",
        )
        db.session.add(log)
        db.session.commit()

    # update gpg
    gpg_list = [
        k.split("gpg")[1].split("-")[0]
        for k, v in form.items()
        if k.startswith("gpg") and "name" in k
    ]

    for gpg in gpg_list:
        # try to get first, else create.
        if ConnectionGpg.query.filter_by(connection_id=connection_id, id=gpg).count():
            gpg_conn = ConnectionGpg.query.filter_by(
                connection_id=connection_id, id=gpg
            ).first()
        else:
            gpg_conn = ConnectionGpg(connection_id=my_connection.id)
            db.session.add(gpg_conn)

        gpg_conn.connection_id = my_connection.id
        gpg_conn.name = form["gpg" + gpg + "-name"]
        gpg_conn.key = em_encrypt(form["gpg" + gpg + "-key"], app.config["PASS_KEY"])

        db.session.commit()

        log = TaskLog(
            status_id=7,
            message=session.get("user_full_name")
            + ": Connection Gpg edited. ("
            + str(my_connection.id)
            + " "
            + my_connection.name
            + " "
            + str(gpg_conn.connection_id)
            + " "
            + gpg_conn.name
            + ")",
        )
        db.session.add(log)
        db.session.commit()

    # update database
    database_list = [
        k.split("database")[1].split("-")[0]
        for k, v in form.items()
        if k.startswith("database") and "name" in k
    ]

    for database in database_list:
        # try to get first, else create.
        if ConnectionDatabase.query.filter_by(
            connection_id=connection_id, id=database
        ).count():
            database_conn = ConnectionDatabase.query.filter_by(
                connection_id=connection_id, id=database
            ).first()
        else:
            database_conn = ConnectionDatabase(connection_id=my_connection.id)
            db.session.add(database_conn)

        database_conn.connection_id = my_connection.id
        database_conn.name = form["database" + database + "-name"]
        database_conn.type_id = form["database" + database + "-type"]
        database_conn.connection_string = em_encrypt(
            form["database" + database + "-conn"], app.config["PASS_KEY"]
        )

        db.session.commit()

        log = TaskLog(
            status_id=7,
            message=session.get("user_full_name")
            + ": Connection Database edited. ("
            + str(my_connection.id)
            + " "
            + my_connection.name
            + " "
            + str(database_conn.connection_id)
            + " "
            + database_conn.name
            + ")",
        )
        db.session.add(log)
        db.session.commit()

    log = TaskLog(
        status_id=7,
        message=session.get("user_full_name")
        + ": Connection group edited. ("
        + str(my_connection.id)
        + " "
        + my_connection.name
        + ")",
    )
    db.session.add(log)
    db.session.commit()

    return render_template(
        "pages/connection/one.html.j2",
        connection=my_connection,
        database_types=my_database_types,
        title=my_connection.name,
    )


@connection_bp.route("/connection/sftp")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_sftp():
    """Page for adding a SFTP Connection.

    :url: /connection/sftp

    :returns: html page.
    """
    return render_template("pages/connection/type/sftp.html.j2")


@connection_bp.route("/connection/gpg")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_gpg():
    """Page for adding a GPG Encryption Key.

    :url: /connection/gpg

    :returns: html page.
    """
    return render_template("pages/connection/type/gpg.html.j2")


@connection_bp.route("/connection/smb")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_smb():
    """Page for adding a SMB Connection.

    :url: /connection/smb

    :returns: html page.
    """
    return render_template("pages/connection/type/smb.html.j2")


@connection_bp.route("/connection/ssh")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_ssh():
    """Page for adding a SSH Connection.

    :url: /connection/ssh

    :returns: html page.
    """
    return render_template("pages/connection/type/ssh.html.j2")


@connection_bp.route("/connection/database")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_database():
    """Page for adding a Database Connection.

    :url: /connection/database

    :returns: html page.
    """
    my_database_types = ConnectionDatabaseType.query.order_by(
        ConnectionDatabaseType.name
    ).all()

    return render_template(
        "pages/connection/type/database.html.j2", database_types=my_database_types
    )


@connection_bp.route("/connection/ftp")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_ftp():
    """Page for adding a FTP Connection.

    :url: /connection/ftp

    :returns: html page.
    """
    return render_template("pages/connection/type/ftp.html.j2")


@connection_bp.route("/connection/new", methods=["POST", "GET"])
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_new():
    """Page for adding a new connection group.

    :url: /connection/new

    :returns: redirects to new connection.
    """
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    if request.method == "POST":

        # form inputs
        form = request.form

        me = Connection(
            name=(form["name"] if "name" in form else ""),
            description=(form["desc"] if "desc" in form else ""),
            address=(form["addr"] if "addr" in form else ""),
            primary_contact=(form["contact"] if "contact" in form else ""),
            primary_contact_email=(form["email"] if "email" in form else ""),
            primary_contact_phone=(form["phone"] if "phone" in form else ""),
        )

        db.session.add(me)
        db.session.commit()

        # get number of sftps
        sftp_list = [
            k.split("sftp")[1].split("-")[0]
            for k, v in form.items()
            if k.startswith("sftp") and "name" in k
        ]

        for sftp in sftp_list:
            if "sftp" + sftp + "-name" in form and form["sftp" + sftp + "-name"] != "":
                sftp_conn = ConnectionSftp(
                    connection_id=me.id,
                    name=form["sftp" + sftp + "-name"],
                    address=form["sftp" + sftp + "-addr"],
                    port=form.get("sftp" + sftp + "-port") or 22,
                    path=form["sftp" + sftp + "-path"],
                    username=(
                        form["sftp" + sftp + "-user"]
                        if form.get("sftp" + sftp + "-user")
                        else None
                    ),
                    key=(
                        em_encrypt(form["sftp" + sftp + "-key"], app.config["PASS_KEY"])
                        if form.get("sftp" + sftp + "-key")
                        else None
                    ),
                    password=em_encrypt(
                        form["sftp" + sftp + "-pass"], app.config["PASS_KEY"]
                    ),
                )
                db.session.add(sftp_conn)
                db.session.commit()

                log = TaskLog(
                    status_id=7,
                    message=session.get("user_full_name")
                    + ": Connection Sftp added. ("
                    + str(me.id)
                    + " "
                    + me.name
                    + " "
                    + str(sftp_conn.id)
                    + " "
                    + sftp_conn.name
                    + ")",
                )
                db.session.add(log)
                db.session.commit()
        # get number of ssh
        ssh_list = [
            k.split("ssh")[1].split("-")[0]
            for k, v in form.items()
            if k.startswith("ssh") and "name" in k
        ]

        for ssh in ssh_list:
            if "ssh" + ssh + "-name" in form and form["ssh" + ssh + "-name"] != "":
                ssh_conn = ConnectionSsh(
                    connection_id=me.id,
                    name=form["ssh" + ssh + "-name"],
                    address=form["ssh" + ssh + "-addr"],
                    path=form["ssh" + ssh + "-path"],
                    username=form["ssh" + ssh + "-user"],
                    password=em_encrypt(
                        form["ssh" + ssh + "-pass"], app.config["PASS_KEY"]
                    ),
                )
                db.session.add(ssh_conn)
                db.session.commit()

                log = TaskLog(
                    status_id=7,
                    message=session.get("user_full_name")
                    + ": Connection SSH added. ("
                    + str(me.id)
                    + " "
                    + me.name
                    + " "
                    + str(ssh_conn.id)
                    + " "
                    + ssh_conn.name
                    + ")",
                )
                db.session.add(log)
                db.session.commit()

        # get number of ftps
        ftp_list = [
            k.split("ftp")[1].split("-")[0]
            for k, v in form.items()
            if k.startswith("ftp") and "name" in k
        ]

        for ftp in ftp_list:
            if "ftp" + ftp + "-name" in form and form["ftp" + ftp + "-name"] != "":
                ftp_conn = ConnectionFtp(
                    connection_id=me.id,
                    name=form["ftp" + ftp + "-name"],
                    address=form["ftp" + ftp + "-addr"],
                    path=form["ftp" + ftp + "-path"],
                    username=form["ftp" + ftp + "-user"],
                    password=em_encrypt(
                        form["ftp" + ftp + "-pass"], app.config["PASS_KEY"]
                    ),
                )
                db.session.add(ftp_conn)
                db.session.commit()
                log = TaskLog(
                    status_id=7,
                    message=session.get("user_full_name")
                    + ": Connection Ftp added. ("
                    + str(me.id)
                    + " "
                    + me.name
                    + " "
                    + str(ftp_conn.id)
                    + " "
                    + ftp_conn.name
                    + ")",
                )
                db.session.add(log)
                db.session.commit()

        smb_list = [
            k.split("smb")[1].split("-")[0]
            for k, v in form.items()
            if k.startswith("smb") and "name" in k
        ]

        for smb in smb_list:
            if "smb" + smb + "-name" in form and form["smb" + smb + "-name"] != "":
                smb_conn = ConnectionSmb(connection_id=me.id)
                db.session.add(smb_conn)

                smb_conn.connection_id = me.id
                smb_conn.name = form["smb" + smb + "-name"]
                smb_conn.server_name = form["smb" + smb + "-server-name"]
                smb_conn.server_ip = form["smb" + smb + "-server-ip"]
                smb_conn.share_name = form["smb" + smb + "-share-name"]
                smb_conn.path = form["smb" + smb + "-path"]
                smb_conn.username = form["smb" + smb + "-user"]
                smb_conn.password = em_encrypt(
                    form["smb" + smb + "-pass"], app.config["PASS_KEY"]
                )

                db.session.commit()

                log = TaskLog(
                    status_id=7,
                    message=session.get("user_full_name")
                    + ": Connection Smb added. ("
                    + str(me.id)
                    + " "
                    + me.name
                    + " "
                    + str(smb_conn.id)
                    + " "
                    + smb_conn.name
                    + ")",
                )
                db.session.add(log)
                db.session.commit()

        # gpg encryption keys
        gpg_list = [
            k.split("gpg")[1].split("-")[0]
            for k, v in form.items()
            if k.startswith("gpg") and "name" in k
        ]

        for gpg in gpg_list:
            if "gpg" + gpg + "-name" in form and form["gpg" + gpg + "-name"] != "":
                gpg_conn = ConnectionGpg(connection_id=me.id)
                db.session.add(gpg_conn)

                gpg_conn.connection_id = me.id
                gpg_conn.name = form["gpg" + gpg + "-name"]
                gpg_conn.key = em_encrypt(
                    form["gpg" + gpg + "-key"], app.config["PASS_KEY"]
                )

                db.session.commit()

                log = TaskLog(
                    status_id=7,
                    message=session.get("user_full_name")
                    + ": Connection Gpg added. ("
                    + str(me.id)
                    + " "
                    + me.name
                    + " "
                    + str(gpg_conn.id)
                    + " "
                    + gpg_conn.name
                    + ")",
                )
                db.session.add(log)
                db.session.commit()

        # update database
        database_list = [
            k.split("database")[1].split("-")[0]
            for k, v in form.items()
            if k.startswith("database") and "name" in k
        ]

        for database in database_list:
            # try to get first, else create.
            if (
                "database" + database + "-name" in form
                and form["database" + database + "-name"] != ""
            ):
                database_conn = ConnectionDatabase(connection_id=me.id)
                db.session.add(database_conn)

                database_conn.connection_id = me.id
                database_conn.name = form["database" + database + "-name"]
                database_conn.type_id = form["database" + database + "-type"]
                database_conn.connection_string = em_encrypt(
                    form["database" + database + "-conn"], app.config["PASS_KEY"]
                )

                db.session.commit()

                log = TaskLog(
                    status_id=7,
                    message=session.get("user_full_name")
                    + ": Connection Database added. ("
                    + str(me.id)
                    + " "
                    + me.name
                    + " "
                    + str(database_conn.id)
                    + " "
                    + database_conn.name
                    + ")",
                )
                db.session.add(log)
                db.session.commit()

        log = TaskLog(
            status_id=7,
            message=session.get("user_full_name")
            + ": Connection group added. ("
            + str(me.id)
            + " "
            + me.name
            + ")",
        )
        db.session.add(log)
        db.session.commit()

    return redirect(url_for("connection_bp.connection"))


@connection_bp.route("/connection/remove/<connection_id>", methods=["GET"])
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_remove(connection_id):
    """Delete a connection group.

    :url: /connection/remove/<connection_id>
    :param connection_id: id of connection in question.

    :returns: redirects back to connection page.
    """
    ConnectionSftp.query.filter_by(connection_id=connection_id).delete()
    ConnectionFtp.query.filter_by(connection_id=connection_id).delete()
    ConnectionSmb.query.filter_by(connection_id=connection_id).delete()
    ConnectionDatabase.query.filter_by(connection_id=connection_id).delete()
    Connection.query.filter_by(id=connection_id).delete()
    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=session.get("user_full_name")
        + ": Connection removed. ("
        + str(connection_id)
        + ")",
    )
    db.session.add(log)
    db.session.commit()
    return redirect(url_for("connection_bp.connection"))


@connection_bp.route(
    "/connection/<connection_id>/removeSftp/<sftp_id>", methods=["GET"]
)
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_remove_sftp(connection_id, sftp_id):
    """Delete a SFPT connection from group.

    :url: /connection/<connection_id>/removeSftp/<sftp_id>
    :param sftp_id: id of the SFTP connection in question.
    :param connection_id: id of connection group in question.

    :returns: redirects back to connection page.
    """
    ConnectionSftp.query.filter_by(connection_id=connection_id, id=sftp_id).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=session.get("user_full_name")
        + ": Connection Sftp removed. ("
        + str(sftp_id)
        + ")",
    )
    db.session.add(log)
    db.session.commit()
    return redirect(
        url_for("connection_bp.connection_edit", connection_id=connection_id)
    )


@connection_bp.route("/connection/<connection_id>/removeSsh/<ssh_id>", methods=["GET"])
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_remove_ssh(connection_id, ssh_id):
    """Delete a SSH connection from group.

    :url: /connection/<connection_id>/removeSsh/<ssh_id>
    :param ssh_id: id of the SSH connection in question.
    :param connection_id: id of connection group in question.

    :returns: redirects back to connection page.
    """
    ConnectionSsh.query.filter_by(connection_id=connection_id, id=ssh_id).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=session.get("user_full_name")
        + ": Connection Ssh removed. ("
        + str(ssh_id)
        + ")",
    )
    db.session.add(log)
    db.session.commit()
    return redirect(
        url_for("connection_bp.connection_edit", connection_id=connection_id)
    )


@connection_bp.route("/connection/<connection_id>/removeSmb/<smb_id>", methods=["GET"])
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_remove_smb(connection_id, smb_id):
    """Delete a SMB connection from group.

    :url: /connection/<connection_id>/removeSmb/<smb_id>
    :param smb_id: id of the SMB connection in question.
    :param connection_id: id of connection group in question.

    :returns: redirects back to connection page.
    """
    ConnectionSmb.query.filter_by(connection_id=connection_id, id=smb_id).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=session.get("user_full_name")
        + ": Connection Smb removed. ("
        + str(smb_id)
        + ")",
    )
    db.session.add(log)
    db.session.commit()
    return redirect(
        url_for("connection_bp.connection_edit", connection_id=connection_id)
    )


@connection_bp.route("/connection/<connection_id>/removeFtp/<ftp_id>", methods=["GET"])
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_remove_ftp(connection_id, ftp_id):
    """Delete a FPT connection from group.

    :url: /connection/<connection_id>/removeFtp/<ftp_id>
    :param ftp_id: id of the FTP connection in question.
    :param connection_id: id of connection group in question.

    :returns: redirects back to connection page.
    """
    ConnectionFtp.query.filter_by(connection_id=connection_id, id=ftp_id).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=session.get("user_full_name")
        + ": Connection Ftp removed. ("
        + str(ftp_id)
        + ")",
    )
    db.session.add(log)
    db.session.commit()
    return redirect(
        url_for("connection_bp.connection_edit", connection_id=connection_id)
    )


@connection_bp.route(
    "/connection/<connection_id>/removeDatabase/<database_id>", methods=["GET"]
)
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_remove_database(connection_id, database_id):
    """Delete a database connection from group.

    :url: /connection/<connection_id>/removeDatabase/<database_id>
    :param database_id: id of the database connection in question.
    :param connection_id: id of connection group in question.

    :returns: redirects back to connection page.
    """
    ConnectionDatabase.query.filter_by(
        connection_id=connection_id, id=database_id
    ).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=session.get("user_full_name")
        + ": Connection Database removed. ("
        + str(database_id)
        + ")",
    )
    db.session.add(log)
    db.session.commit()
    return redirect(
        url_for("connection_bp.connection_edit", connection_id=connection_id)
    )
