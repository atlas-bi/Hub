"""External Connection web views."""

import sys
from pathlib import Path
from typing import Union

import requests
from crypto import em_encrypt
from flask import Blueprint
from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.wrappers import Response

from web import db
from web.model import (
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
@login_required
def all_connections() -> str:
    """List all connections."""
    connections = Connection.query.order_by(Connection.name).all()

    return render_template(
        "pages/connection/all.html.j2",
        connections=connections,
        title="Connections",
    )


@connection_bp.route("/connection/<connection_id>", methods=["GET"])
@login_required
def one_connection(connection_id: int) -> str:
    """Get one connection."""
    connection = Connection.query.filter_by(id=connection_id).first()

    return render_template(
        "pages/connection/one.html.j2",
        connection=connection,
        title=connection.name,
    )


@connection_bp.route("/connection/<connection_id>/edit", methods=["POST", "GET"])
@login_required
def edit_connection(connection_id: int) -> Union[str, Response]:
    """Edit a connection."""
    connection = Connection.query.filter_by(id=connection_id).first_or_404()

    if request.method == "GET":
        return render_template(
            "pages/connection/new.html.j2",
            connection=connection,
            title=f"Editing connection {connection}",
        )

    form = request.form
    my_connection = Connection.query.filter_by(id=connection.id)
    my_connection.update(
        {
            "name": form.get("name", "undefined", type=str).strip(),
            "description": form.get("description", "", type=str).strip(),
            "address": form.get("address", "", type=str).strip(),
            "primary_contact": form.get("contact", type=str),
            "primary_contact_email": form.get("email", type=str),
            "primary_contact_phone": form.get("phone", type=str),
        }
    )

    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: Connection group edited. ({connection.id}) {connection}",
    )
    db.session.add(log)
    db.session.commit()
    flash("Connection edited.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/new", methods=["POST", "GET"])
@login_required
def new_connection() -> Union[str, Response]:
    """Add a new connection."""
    if request.method == "GET":
        return render_template(
            "pages/connection/new.html.j2",
            title="New connection",
        )

    form = request.form

    me = Connection(
        name=form.get("name", "undefined", type=str).strip(),
        description=form.get("description", "", type=str).strip(),
        address=form.get("address", "", type=str).strip(),
        primary_contact=form.get("contact", "", type=str).strip(),
        primary_contact_email=form.get("email", "", type=str).strip(),
        primary_contact_phone=form.get("phone", "", type=str).strip(),
    )

    db.session.add(me)
    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: Connection group added. ({me.id}) {me}",
    )

    db.session.add(log)
    db.session.commit()
    flash("Connection added.")
    return redirect(url_for("connection_bp.one_connection", connection_id=me.id))


@connection_bp.route("/connection/<connection_id>/delete", methods=["GET"])
@login_required
def delete_connection(connection_id: int) -> Response:
    """Delete a connection."""
    ConnectionSftp.query.filter_by(connection_id=connection_id).delete()
    ConnectionGpg.query.filter_by(connection_id=connection_id).delete()
    ConnectionFtp.query.filter_by(connection_id=connection_id).delete()
    ConnectionSmb.query.filter_by(connection_id=connection_id).delete()
    ConnectionSsh.query.filter_by(connection_id=connection_id).delete()
    ConnectionDatabase.query.filter_by(connection_id=connection_id).delete()
    Connection.query.filter_by(id=connection_id).delete()
    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: Connection deleted. ({connection_id})",
    )
    db.session.add(log)
    db.session.commit()
    flash("Connection deleted.")
    return redirect(url_for("connection_bp.all_connections"))


@connection_bp.route("/connection/<connection_id>/sftp/<sftp_id>/delete", methods=["GET"])
@login_required
def delete_connection_sftp(connection_id: int, sftp_id: int) -> Response:
    """Delete a SFTP connection."""
    ConnectionSftp.query.filter_by(connection_id=connection_id, id=sftp_id).delete()
    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: SFTP Connection deleted. ({sftp_id})",
    )
    db.session.add(log)
    db.session.commit()
    flash("Connection deleted.")

    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/sftp/<sftp_id>/edit", methods=["GET", "POST"])
@login_required
def edit_connection_sftp(connection_id: int, sftp_id: int) -> Union[Response, str]:
    """Edit a SFTP connection."""
    sftp = ConnectionSftp.query.filter_by(id=sftp_id, connection_id=connection_id).first_or_404()
    if request.method == "GET":
        return render_template(
            "pages/connection/sftp_edit.html.j2",
            sftp=sftp,
            connection=sftp.connection,
            title=f"Editing Connection {sftp.connection}",
        )

    form = request.form
    this_sftp = ConnectionSftp.query.filter_by(id=sftp.id)
    this_sftp.update(
        {
            "name": form.get("name", "undefined", type=str).strip(),
            "address": form.get("address", "", type=str).strip(),
            "port": form.get("port", 22, type=int),
            "path": form.get("path", "", type=str).strip(),
            "username": form.get("username", "", type=str).strip(),
            "key": (
                em_encrypt(form.get("ssh_key", "", type=str).strip(), app.config["PASS_KEY"])
                if form.get("ssh_key", type=str)
                else None
            ),
            "password": (
                em_encrypt(form.get("password", "", type=str).strip(), app.config["PASS_KEY"])
                if form.get("password", type=str)
                else None
            ),
            "key_password": (
                em_encrypt(
                    form.get("key_password", "", type=str).strip(),
                    app.config["PASS_KEY"],
                )
                if form.get("key_password", type=str)
                else None
            ),
        }
    )

    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: SFTP Connection edited. ({sftp_id}) {sftp}",
    )
    db.session.add(log)
    db.session.commit()

    flash("Connection updated.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/sftp/new", methods=["GET", "POST"])
@login_required
def new_connection_sftp(connection_id: int) -> Union[str, Response]:
    """Create a SFTP connection."""
    connection = Connection.query.filter_by(id=connection_id).first_or_404()
    if request.method == "GET":
        return render_template(
            "pages/connection/sftp_edit.html.j2",
            connection=connection,
            title="New SFTP Connection",
        )
    form = request.form

    sftp = ConnectionSftp(
        connection_id=connection_id,
        name=form.get("name", "undefined", type=str).strip(),
        address=form.get("address", "", type=str).strip(),
        port=form.get("port", 22, type=int),
        path=form.get("path", "", type=str).strip(),
        username=form.get("username", "", type=str).strip(),
        key=(
            em_encrypt(form.get("ssh_key", "", type=str).strip(), app.config["PASS_KEY"])
            if form.get("ssh_key", type=str)
            else None
        ),
        password=(
            em_encrypt(form.get("password", "", type=str).strip(), app.config["PASS_KEY"])
            if form.get("password", type=str)
            else None
        ),
        key_password=(
            em_encrypt(form.get("key_password", "", type=str).strip(), app.config["PASS_KEY"])
            if form.get("key_password", type=str)
            else None
        ),
    )

    db.session.add(sftp)
    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: SFTP Connection added. ({sftp.id}) {sftp}",
    )
    db.session.add(log)
    db.session.commit()

    flash("Connection added.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/ssh/<ssh_id>/delete", methods=["GET"])
@login_required
def delete_connection_ssh(connection_id: int, ssh_id: int) -> Response:
    """Delete a SSH connection."""
    ConnectionSsh.query.filter_by(connection_id=connection_id, id=ssh_id).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: SSH Connection deleted. ({ssh_id})",
    )
    db.session.add(log)
    db.session.commit()
    flash("Connection deleted.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/ssh/new", methods=["GET", "POST"])
@login_required
def new_connection_ssh(connection_id: int) -> Union[str, Response]:
    """Create a SSH connection."""
    connection = Connection.query.filter_by(id=connection_id).first_or_404()
    if request.method == "GET":
        return render_template(
            "pages/connection/ssh_edit.html.j2",
            connection=connection,
            title="New SSH Connection",
        )
    form = request.form

    ssh = ConnectionSsh(
        connection_id=connection_id,
        name=form.get("name", "undefined", type=str).strip(),
        address=form.get("address", "", type=str).strip(),
        port=form.get("port", 22, type=int),
        username=form.get("username", "", type=str).strip(),
        password=(
            em_encrypt(form.get("password", "", type=str).strip(), app.config["PASS_KEY"])
            if form.get("password", type=str)
            else None
        ),
    )

    db.session.add(ssh)
    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: SSH Connection added. ({ssh.id}) {ssh}",
    )
    db.session.add(log)
    db.session.commit()

    flash("Connection added.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/ssh/<ssh_id>/edit", methods=["GET", "POST"])
@login_required
def edit_connection_ssh(connection_id: int, ssh_id: int) -> Union[Response, str]:
    """Edit a SSH connection."""
    ssh = ConnectionSsh.query.filter_by(id=ssh_id, connection_id=connection_id).first_or_404()
    if request.method == "GET":
        return render_template(
            "pages/connection/ssh_edit.html.j2",
            ssh=ssh,
            connection=ssh.connection,
            title=f"Editing Connection {ssh.connection}",
        )

    form = request.form
    this_ssh = ConnectionSsh.query.filter_by(id=ssh.id)
    this_ssh.update(
        {
            "name": form.get("name", "undefined", type=str).strip(),
            "address": form.get("address", "", type=str).strip(),
            "port": form.get("port", 22, type=int),
            "username": form.get("username", "", type=str).strip(),
            "password": (
                em_encrypt(form.get("password", "", type=str).strip(), app.config["PASS_KEY"])
                if form.get("password", type=str)
                else None
            ),
        }
    )

    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: SSH Connection edited. ({ssh.id}) {ssh}",
    )
    db.session.add(log)
    db.session.commit()
    flash("Connection updated.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/smb/<smb_id>/delete", methods=["GET"])
@login_required
def delete_connection_smb(connection_id: int, smb_id: int) -> Response:
    """Delete a SMB connection."""
    ConnectionSmb.query.filter_by(connection_id=connection_id, id=smb_id).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: SMB Connection deleted. ({smb_id})",
    )
    db.session.add(log)
    db.session.commit()

    flash("Connection deleted.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/smb/new", methods=["GET", "POST"])
@login_required
def new_connection_smb(connection_id: int) -> Union[Response, str]:
    """Create a SMB connection."""
    connection = Connection.query.filter_by(id=connection_id).first_or_404()
    if request.method == "GET":
        return render_template(
            "pages/connection/smb_edit.html.j2",
            connection=connection,
            title="New SMB Connection",
        )
    form = request.form

    smb = ConnectionSmb(
        connection_id=connection_id,
        name=form.get("name", "undefined", type=str),
        server_name=form.get("server_name", "", type=str).strip(),
        server_ip=form.get("server_ip", "", type=str).strip(),
        share_name=form.get("share_name", "", type=str).strip(),
        path=form.get("path", "", type=str).strip(),
        username=form.get("username", "", type=str).strip(),
        password=(
            em_encrypt(form.get("password", "", type=str).strip(), app.config["PASS_KEY"])
            if form.get("password", type=str)
            else None
        ),
    )

    db.session.add(smb)
    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: SMB Connection added. ({smb.id}) {smb}",
    )
    db.session.add(log)
    db.session.commit()

    flash("Connection added.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/smb/<smb_id>/edit", methods=["GET", "POST"])
@login_required
def edit_connection_smb(connection_id: int, smb_id: int) -> Union[Response, str]:
    """Edit a SMB connection."""
    smb = ConnectionSmb.query.filter_by(id=smb_id, connection_id=connection_id).first_or_404()
    if request.method == "GET":
        return render_template(
            "pages/connection/smb_edit.html.j2",
            smb=smb,
            connection=smb.connection,
            title=f"Editing Connection {smb.connection}",
        )

    form = request.form
    this_smb = ConnectionSmb.query.filter_by(id=smb.id)
    this_smb.update(
        {
            "name": form.get("name", "undefined", type=str),
            "server_name": form.get("server_name", "", type=str).strip(),
            "server_ip": form.get("server_ip", "", type=str).strip(),
            "share_name": form.get("share_name", "", type=str).strip(),
            "path": form.get("path", "", type=str).strip(),
            "username": form.get("username", "", type=str).strip(),
            "password": (
                em_encrypt(form.get("password", "", type=str).strip(), app.config["PASS_KEY"])
                if form.get("password", type=str)
                else None
            ),
        }
    )

    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: SMB Connection added. ({smb.id}) {smb}",
    )
    db.session.add(log)
    db.session.commit()
    flash("Connection updated.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/ftp/<ftp_id>/delete", methods=["GET"])
@login_required
def delete_connection_ftp(connection_id: int, ftp_id: int) -> Response:
    """Delete a FPT connection."""
    ConnectionFtp.query.filter_by(connection_id=connection_id, id=ftp_id).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: FTP Connection deleted. ({ftp_id})",
    )
    db.session.add(log)
    db.session.commit()

    flash("Connection deleted.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/ftp/new", methods=["GET", "POST"])
@login_required
def new_connection_ftp(connection_id: int) -> Union[Response, str]:
    """Create a FTP connection."""
    connection = Connection.query.filter_by(id=connection_id).first_or_404()
    if request.method == "GET":
        return render_template(
            "pages/connection/ftp_edit.html.j2",
            connection=connection,
            title="New FTP Connection",
        )
    form = request.form

    ftp = ConnectionFtp(
        connection_id=connection_id,
        name=form.get("name", "undefined", type=str).strip(),
        address=form.get("address", "", type=str).strip(),
        path=form.get("path", "", type=str).strip(),
        username=form.get("username", "", type=str).strip(),
        password=(
            em_encrypt(form.get("password", "", type=str).strip(), app.config["PASS_KEY"])
            if form.get("password", type=str)
            else None
        ),
    )

    db.session.add(ftp)
    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: FTP Connection added. ({ftp.id}) {ftp}",
    )
    db.session.add(log)
    db.session.commit()

    flash("Connection added.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/ftp/<ftp_id>/edit", methods=["GET", "POST"])
@login_required
def edit_connection_ftp(connection_id: int, ftp_id: int) -> Union[Response, str]:
    """Edit a FTP connection."""
    ftp = ConnectionFtp.query.filter_by(id=ftp_id, connection_id=connection_id).first_or_404()
    if request.method == "GET":
        return render_template(
            "pages/connection/ftp_edit.html.j2",
            ftp=ftp,
            connection=ftp.connection,
            title=f"Editing Connection {ftp.connection}",
        )

    form = request.form
    this_ftp = ConnectionFtp.query.filter_by(id=ftp.id)
    this_ftp.update(
        {
            "name": form.get("name", "undefined", type=str).strip(),
            "address": form.get("address", "", type=str).strip(),
            "path": form.get("path", "", type=str).strip(),
            "username": form.get("username", "", type=str).strip(),
            "password": (
                em_encrypt(form.get("password", "", type=str).strip(), app.config["PASS_KEY"])
                if form.get("password", type=str)
                else None
            ),
        }
    )

    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: FTP Connection edited. ({ftp.id}) {ftp}",
    )
    db.session.add(log)
    db.session.commit()

    flash("Connection updated.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/gpg/<gpg_id>/delete", methods=["GET"])
@login_required
def delete_connection_gpg(connection_id: int, gpg_id: int) -> Response:
    """Delete a GPG connection."""
    ConnectionGpg.query.filter_by(connection_id=connection_id, id=gpg_id).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: GPG Connection deleted. ({gpg_id})",
    )
    db.session.add(log)
    db.session.commit()
    flash("Connection deleted.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>gpg/new", methods=["GET", "POST"])
@login_required
def new_connection_gpg(connection_id: int) -> Union[Response, str]:
    """Create a GPG connection."""
    connection = Connection.query.filter_by(id=connection_id).first_or_404()
    if request.method == "GET":
        return render_template(
            "pages/connection/gpg_edit.html.j2",
            connection=connection,
            title="New GPG Connection",
        )
    form = request.form

    gpg = ConnectionGpg(
        connection_id=connection_id,
        name=form.get("name", "undefined", type=str).strip(),
        key=(
            em_encrypt(form.get("key", "", type=str).strip(), app.config["PASS_KEY"])
            if form.get("key", type=str)
            else None
        ),
    )

    db.session.add(gpg)
    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: GPG Connection added. ({gpg.id}) {gpg}",
    )
    db.session.add(log)
    db.session.commit()

    flash("Connection added.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/gpg/<gpg_id>/edit", methods=["GET", "POST"])
@login_required
def edit_connection_gpg(connection_id: int, gpg_id: int) -> Union[str, Response]:
    """Edit a GPG connection."""
    gpg = ConnectionGpg.query.filter_by(id=gpg_id, connection_id=connection_id).first_or_404()
    if request.method == "GET":
        return render_template(
            "pages/connection/gpg_edit.html.j2",
            gpg=gpg,
            connection=gpg.connection,
            title=f"Editing Connection {gpg.connection}",
        )

    form = request.form
    this_gpg = ConnectionGpg.query.filter_by(id=gpg.id)
    this_gpg.update(
        {
            "name": form.get("name", "undefined", type=str).strip(),
            "key": (
                em_encrypt(form.get("key", "", type=str).strip(), app.config["PASS_KEY"])
                if form.get("key", type=str)
                else None
            ),
        }
    )

    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: GPG Connection edited. ({gpg.id}) {gpg}",
    )
    db.session.add(log)
    db.session.commit()
    flash("Connection updated.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/database/<database_id>/delete", methods=["GET"])
@login_required
def delete_connection_database(connection_id: int, database_id: int) -> Response:
    """Delete a database connection."""
    ConnectionDatabase.query.filter_by(connection_id=connection_id, id=database_id).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: Database Connection deleted. ({database_id})",
    )
    db.session.add(log)
    db.session.commit()
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route(
    "/connection/<connection_id>/database/<database_id>/edit", methods=["GET", "POST"]
)
@login_required
def edit_connection_database(connection_id: int, database_id: int) -> Union[Response, str]:
    """Edit a database connection."""
    database = ConnectionDatabase.query.filter_by(
        id=database_id, connection_id=connection_id
    ).first_or_404()
    if request.method == "GET":
        return render_template(
            "pages/connection/database_edit.html.j2",
            database=database,
            connection=database.connection,
            database_types=ConnectionDatabaseType.query.all(),
            title=f"Editing Database Connection {database.connection}",
        )

    form = request.form
    this_database = ConnectionDatabase.query.filter_by(id=database.id)
    this_database.update(
        {
            "name": form.get("name", "undefined", type=str).strip(),
            "type_id": form.get("database_type", 1, type=int),
            "connection_string": (
                em_encrypt(form.get("connection_string", None), app.config["PASS_KEY"])
                if form.get("connection_string", None)
                else None
            ),
            "timeout": form.get("timeout", app.config["DEFAULT_SQL_TIMEOUT"], type=int),
        }
    )

    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: Database Connection edited. ({database.id}) {database}",
    )
    db.session.add(log)
    db.session.commit()

    flash("Changes saved.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/<connection_id>/database/new", methods=["GET", "POST"])
@login_required
def new_connection_database(connection_id: int) -> Union[Response, str]:
    """Create a database connection."""
    connection = Connection.query.filter_by(id=connection_id).first_or_404()
    if request.method == "GET":
        return render_template(
            "pages/connection/database_edit.html.j2",
            connection=connection,
            database_types=ConnectionDatabaseType.query.all(),
            title="New Database Connection",
        )
    form = request.form
    database = ConnectionDatabase(
        connection_id=connection_id,
        name=form.get("name", "undefined", type=str).strip(),
        type_id=form.get("database_type", 1, type=int),
        connection_string=(
            em_encrypt(form.get("connection_string"), app.config["PASS_KEY"])
            if form.get("connection_string")
            else None
        ),
        timeout=form.get("timeout", app.config["DEFAULT_SQL_TIMEOUT"], type=int),
    )

    db.session.add(database)
    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=f"{current_user.full_name}: Database Connection added. ({database.id}) {database}",
    )
    db.session.add(log)
    db.session.commit()
    flash("Connection added.")
    return redirect(url_for("connection_bp.one_connection", connection_id=connection_id))


@connection_bp.route("/connection/ssh/<ssh_id>/status")
@login_required
def ssh_online(ssh_id: int) -> str:
    """Check if connection is online."""
    try:
        return requests.get(f"{app.config['RUNNER_HOST']}/ssh/{ssh_id}/status", timeout=60).text
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">Offline</span>'


@connection_bp.route("/connection/database/<database_id>/status")
@login_required
def database_online(database_id: int) -> str:
    """Check if connection is online."""
    try:
        return requests.get(
            f"{app.config['RUNNER_HOST']}/database/{database_id}/status", timeout=60
        ).text
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">Offline</span>'


@connection_bp.route("/connection/sftp/<sftp_id>/status")
@login_required
def sftp_online(sftp_id: int) -> str:
    """Check if connection is online."""
    try:
        return requests.get(f"{app.config['RUNNER_HOST']}/sftp/{sftp_id}/status", timeout=60).text
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">Offline</span>'


@connection_bp.route("/connection/ftp/<ftp_id>/status")
@login_required
def ftp_online(ftp_id: int) -> str:
    """Check if connection is online."""
    try:
        return requests.get(f"{app.config['RUNNER_HOST']}/ftp/{ftp_id}/status", timeout=60).text
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">Offline</span>'


@connection_bp.route("/connection/smb/<smb_id>/status")
@login_required
def smb_online(smb_id: int) -> str:
    """Check if connection is online."""
    try:
        return requests.get(f"{app.config['RUNNER_HOST']}/smb/{smb_id}/status", timeout=60).text
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">Offline</span>'
