"""
    webapp views of all data destinations

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

import datetime
from flask import redirect, url_for, render_template, request, jsonify, g
from em import app, ldap, db
from ..model.model import (
    Connection,
    ConnectionSftp,
    ConnectionFtp,
    ConnectionSmb,
    ConnectionSsh,
    ConnectionDatabase,
    ConnectionDatabaseType,
    Task,
    TaskLog,
)
from ..scripts.crypto import em_encrypt


@app.route("/connection")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection():
    """ list of all destinations """
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


@app.route("/connection/<my_id>", methods=["POST", "GET"])
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_edit(my_id):
    """ used to view or edit an existing destination """
    my_connection = Connection.query.filter_by(id=my_id).first()
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
    my_connection.description = form["desc"] if "desc" in form else None
    my_connection.address = form["addr"] if "addr" in form else None
    my_connection.primary_contact = form["contact"] if "contact" in form else None
    my_connection.primary_contact_email = form["email"] if "email" in form else None
    my_connection.primary_contact_phone = form["phone"] if "phone" in form else None
    db.session.commit()

    # update sftp
    sftp_list = [
        k.split("sftp")[1].split("-")[0]
        for k, v in form.items()
        if k.startswith("sftp") and "name" in k
    ]
    for x in sftp_list:
        # try to get first, else create.
        if ConnectionSftp.query.filter_by(connection_id=my_id, id=x).count():
            sftp = ConnectionSftp.query.filter_by(connection_id=my_id, id=x).first()
        else:
            sftp = ConnectionSftp(connection_id=my_connection.id)
            db.session.add(sftp)

        sftp.connection_id = my_connection.id
        sftp.name = form["sftp" + x + "-name"]
        sftp.address = form["sftp" + x + "-addr"]
        sftp.port = (
            form["sftp" + x + "-port"] or 22
            if form["sftp" + x + "-port"] != "None"
            else 22
        )
        sftp.path = form["sftp" + x + "-path"]
        sftp.username = form["sftp" + x + "-user"]
        sftp.password = em_encrypt(form["sftp" + x + "-pass"])

        db.session.commit()

        log = TaskLog(
            status_id=7,
            message=g.user_full_name
            + ": Connection Sftp edited. ("
            + str(my_connection.id)
            + " "
            + my_connection.name
            + " "
            + str(sftp.connection_id)
            + " "
            + sftp.name
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
    for x in ssh_list:
        # try to get first, else create.
        if ConnectionSsh.query.filter_by(connection_id=my_id, id=x).count():
            ssh = ConnectionSsh.query.filter_by(connection_id=my_id, id=x).first()
        else:
            ssh = ConnectionSsh(connection_id=my_connection.id)
            db.session.add(ssh)

        ssh.connection_id = my_connection.id
        ssh.name = form["ssh" + x + "-name"]
        ssh.address = form["ssh" + x + "-addr"]
        ssh.port = (
            form["ssh" + x + "-port"] or 22
            if form["ssh" + x + "-port"] != "None"
            else 22
        )
        ssh.username = form["ssh" + x + "-user"]
        ssh.password = em_encrypt(form["ssh" + x + "-pass"])

        db.session.commit()

        log = TaskLog(
            status_id=7,
            message=g.user_full_name
            + ": Connection Sftp edited. ("
            + str(my_connection.id)
            + " "
            + my_connection.name
            + " "
            + str(ssh.connection_id)
            + " "
            + sftp.name
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
    for x in ftp_list:
        # try to get first, else create.
        if ConnectionFtp.query.filter_by(connection_id=my_id, id=x).count():
            ftp = ConnectionFtp.query.filter_by(connection_id=my_id, id=x).first()
        else:
            ftp = ConnectionFtp(connection_id=my_connection.id)
            db.session.add(ftp)

        ftp.connection_id = my_connection.id
        ftp.name = form["ftp" + x + "-name"]
        ftp.address = form["ftp" + x + "-addr"]
        ftp.path = form["ftp" + x + "-path"]
        ftp.username = form["ftp" + x + "-user"]
        ftp.password = em_encrypt(form["ftp" + x + "-pass"])

        db.session.commit()

        log = TaskLog(
            status_id=7,
            message=g.user_full_name
            + ": Connection Ftp edited. ("
            + str(my_connection.id)
            + " "
            + my_connection.name
            + " "
            + str(ftp.connection_id)
            + " "
            + ftp.name
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

    for x in smb_list:
        # try to get first, else create.
        if ConnectionSmb.query.filter_by(connection_id=my_id, id=x).count():
            smb = ConnectionSmb.query.filter_by(connection_id=my_id, id=x).first()
        else:
            smb = ConnectionSmb(connection_id=my_connection.id)
            db.session.add(smb)

        smb.connection_id = my_connection.id
        smb.name = form["smb" + x + "-name"]
        smb.server_name = form["smb" + x + "-server-name"]
        smb.server_ip = form["smb" + x + "-server-ip"]
        smb.share_name = form["smb" + x + "-share-name"]
        smb.path = form["smb" + x + "-path"]
        smb.username = form["smb" + x + "-user"]
        smb.password = em_encrypt(form["smb" + x + "-pass"])

        db.session.commit()

        log = TaskLog(
            status_id=7,
            message=g.user_full_name
            + ": Connection Smb edited. ("
            + str(my_connection.id)
            + " "
            + my_connection.name
            + " "
            + str(smb.connection_id)
            + " "
            + smb.name
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

    for x in database_list:
        # try to get first, else create.
        if ConnectionDatabase.query.filter_by(connection_id=my_id, id=x).count():
            database = ConnectionDatabase.query.filter_by(
                connection_id=my_id, id=x
            ).first()
        else:
            database = ConnectionDatabase(connection_id=my_connection.id)
            db.session.add(database)

        database.connection_id = my_connection.id
        database.name = form["database" + x + "-name"]
        database.type_id = form["database" + x + "-type"]
        em_encrypt(form["database" + x + "-conn"])
        database.connection_string = em_encrypt(form["database" + x + "-conn"])

        db.session.commit()

        log = TaskLog(
            status_id=7,
            message=g.user_full_name
            + ": Connection Database edited. ("
            + str(my_connection.id)
            + " "
            + my_connection.name
            + " "
            + str(database.connection_id)
            + " "
            + database.name
            + ")",
        )
        db.session.add(log)
        db.session.commit()

    log = TaskLog(
        status_id=7,
        message=g.user_full_name
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


@app.route("/connection/<my_id>/task")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_task(my_id):
    """ get table of tasks associated with the connection """
    page = request.args.get("p", default=1, type=int)
    sort = request.args.get("s", default="Status.desc", type=str)
    split_sort = sort.split(".")

    page -= 1

    task_list = []

    # sftp source
    [
        task_list.append(
            {
                "id": task.id,
                "name": task.name,
                "project_id": task.project_id,
                "project_name": task.project.name,
                "connection_name": task.source_sftp_conn.name,
                "enabled": task.enabled,
                "last_run": task.last_run,
                "status_name": (task.status.name if task.status else "N/A"),
                "status_id": (task.status.id if task.status else "N/A"),
            }
        )
        for task in (
            Task.query.join(ConnectionSftp, ConnectionSftp.id == Task.source_sftp_id)
            .join(
                Connection,
                Connection.id == ConnectionSftp.connection_id
                and Connection.id == my_id,
            )
            .all()
        )
    ]

    # sftp destination
    [
        task_list.append(
            {
                "id": task.id,
                "name": task.name,
                "project_id": task.project_id,
                "project_name": task.project.name,
                "connection_name": task.destination_sftp_conn.name,
                "enabled": task.enabled,
                "last_run": task.last_run,
                "status_name": (task.status.name if task.status else "N/A"),
                "status_id": (task.status.id if task.status else "N/A"),
            }
        )
        for task in (
            Task.query.join(
                ConnectionSftp, ConnectionSftp.id == Task.destination_sftp_id
            )
            .join(
                Connection,
                Connection.id == ConnectionSftp.connection_id
                and Connection.id == my_id,
            )
            .all()
        )
    ]

    # sftp query
    [
        task_list.append(
            {
                "id": task.id,
                "name": task.name,
                "project_id": task.project_id,
                "project_name": task.project.name,
                "connection_name": task.query_sftp_conn.name,
                "enabled": task.enabled,
                "last_run": task.last_run,
                "status_name": (task.status.name if task.status else "N/A"),
                "status_id": (task.status.id if task.status else "N/A"),
            }
        )
        for task in (
            Task.query.join(ConnectionSftp, ConnectionSftp.id == Task.query_sftp_id)
            .join(
                Connection,
                Connection.id == ConnectionSftp.connection_id
                and Connection.id == my_id,
            )
            .all()
        )
    ]

    # ssh
    [
        task_list.append(
            {
                "id": task.id,
                "name": task.name,
                "project_id": task.project_id,
                "project_name": task.project.name,
                "connection_name": task.source_ssh_conn.name,
                "enabled": task.enabled,
                "last_run": task.last_run,
                "status_name": (task.status.name if task.status else "N/A"),
                "status_id": (task.status.id if task.status else "N/A"),
            }
        )
        for task in (
            Task.query.join(ConnectionSsh, ConnectionSsh.id == Task.source_ssh_id)
            .join(
                Connection,
                Connection.id == ConnectionSsh.connection_id and Connection.id == my_id,
            )
            .all()
        )
    ]

    # ftp source
    [
        task_list.append(
            {
                "id": task.id,
                "name": task.name,
                "project_id": task.project_id,
                "project_name": task.project.name,
                "connection_name": task.source_ftp_conn.name,
                "enabled": task.enabled,
                "last_run": task.last_run,
                "status_name": (task.status.name if task.status else "N/A"),
                "status_id": (task.status.id if task.status else "N/A"),
            }
        )
        for task in (
            Task.query.join(ConnectionFtp, ConnectionFtp.id == Task.source_ftp_id)
            .join(
                Connection,
                Connection.id == ConnectionFtp.connection_id and Connection.id == my_id,
            )
            .all()
        )
    ]

    # ftp destination
    [
        task_list.append(
            {
                "id": task.id,
                "name": task.name,
                "project_id": task.project_id,
                "project_name": task.project.name,
                "connection_name": task.destination_ftp_conn.name,
                "enabled": task.enabled,
                "last_run": task.last_run,
                "status_name": (task.status.name if task.status else "N/A"),
                "status_id": (task.status.id if task.status else "N/A"),
            }
        )
        for task in (
            Task.query.join(ConnectionFtp, ConnectionFtp.id == Task.destination_ftp_id)
            .join(
                Connection,
                Connection.id == ConnectionFtp.connection_id and Connection.id == my_id,
            )
            .all()
        )
    ]
    # ftp query
    [
        task_list.append(
            {
                "id": task.id,
                "name": task.name,
                "project_id": task.project_id,
                "project_name": task.project.name,
                "connection_name": task.query_ftp_conn.name,
                "enabled": task.enabled,
                "last_run": task.last_run,
                "status_name": (task.status.name if task.status else "N/A"),
                "status_id": (task.status.id if task.status else "N/A"),
            }
        )
        for task in (
            Task.query.join(ConnectionFtp, ConnectionFtp.id == Task.query_ftp_id)
            .join(
                Connection,
                Connection.id == ConnectionFtp.connection_id and Connection.id == my_id,
            )
            .all()
        )
    ]

    # smb source
    [
        task_list.append(
            {
                "id": task.id,
                "name": task.name,
                "project_id": task.project_id,
                "project_name": task.project.name,
                "connection_name": task.source_smb_conn.name,
                "enabled": task.enabled,
                "last_run": task.last_run,
                "status_name": (task.status.name if task.status else "N/A"),
                "status_id": (task.status.id if task.status else "N/A"),
            }
        )
        for task in (
            Task.query.join(ConnectionSmb, ConnectionSmb.id == Task.source_smb_id)
            .join(
                Connection,
                Connection.id == ConnectionSmb.connection_id and Connection.id == my_id,
            )
            .all()
        )
    ]

    # smb destination
    [
        task_list.append(
            {
                "id": task.id,
                "name": task.name,
                "project_id": task.project_id,
                "project_name": task.project.name,
                "connection_name": task.destination_smb_conn.name,
                "enabled": task.enabled,
                "last_run": task.last_run,
                "status_name": (task.status.name if task.status else "N/A"),
                "status_id": (task.status.id if task.status else "N/A"),
            }
        )
        for task in (
            Task.query.join(ConnectionSmb, ConnectionSmb.id == Task.destination_smb_id)
            .join(
                Connection,
                Connection.id == ConnectionSmb.connection_id and Connection.id == my_id,
            )
            .all()
        )
    ]
    # smb query
    [
        task_list.append(
            {
                "id": task.id,
                "name": task.name,
                "project_id": task.project_id,
                "project_name": task.project.name,
                "connection_name": task.query_smb_conn.name,
                "enabled": task.enabled,
                "last_run": task.last_run,
                "status_name": (task.status.name if task.status else "N/A"),
                "status_id": (task.status.id if task.status else "N/A"),
            }
        )
        for task in (
            Task.query.join(ConnectionSmb, ConnectionSmb.id == Task.query_smb_id)
            .join(
                Connection,
                Connection.id == ConnectionSmb.connection_id and Connection.id == my_id,
            )
            .all()
        )
    ]

    # database source
    [
        task_list.append(
            {
                "id": task.id,
                "name": task.name,
                "project_id": task.project_id,
                "project_name": task.project.name,
                "connection_name": task.source_database_conn.name,
                "enabled": task.enabled,
                "last_run": task.last_run,
                "status_name": (task.status.name if task.status else "N/A"),
                "status_id": (task.status.id if task.status else "N/A"),
            }
        )
        for task in (
            Task.query.join(
                ConnectionDatabase, ConnectionDatabase.id == Task.source_database_id
            )
            .join(
                Connection,
                Connection.id == ConnectionDatabase.connection_id
                and Connection.id == my_id,
            )
            .all()
        )
    ]

    head = [
        "Name",
        "Project",
        "Connection",
        "Enabled",
        "Last Active",
        "Run Now",
        "Status",
        "Next Run Date",
    ]

    me = [{"head": str(head)}]
    table = []

    [
        table.append(
            {
                "Name": '<a class="em-link" href="/task/'
                + str(task["id"])
                + '">'
                + task["name"]
                + "</a>",
                "Project": '<a class="em-link" href="/project/'
                + str(task["project_id"])
                + '">'
                + task["project_name"]
                + "</a>"
                if task["project_id"]
                else "Orphan :'(",
                "Connection": task["connection_name"],
                "Enabled": "<a class='em-link' href=/task/"
                + str(task["id"])
                + "/disable>Disable</a>"
                if task["enabled"] == 1
                else "<a class='em-link' href=/task/"
                + str(task["id"])
                + "/enable>Enable</a>",
                "Last Active": datetime.datetime.strftime(
                    task["last_run"], "%a, %b %-d, %Y %H:%M:%S"
                )
                if task["last_run"]
                else "Never",
                "Run Now": "<a class='em-link' href='/task/"
                + str(task["id"])
                + "/run'>Run Now</a>",
                "Status": task["status_name"] if task["status_id"] else "None",
                "Next Run Date": "Error: Task must be <a class='em-link' href='/task/"
                + str(task["id"])
                + "/schedule'>rescheduled</a> to run."
                if (
                    len(
                        [
                            job.next_run_time
                            for job in app.apscheduler.get_jobs()
                            if str(job.args[0]) == str(task["id"])
                            and job.next_run_time is not None
                        ]
                        or []
                    )
                    == 0
                    and task["enabled"] == 1
                )
                else (
                    datetime.datetime.strftime(
                        min(
                            [
                                job.next_run_time
                                for job in app.apscheduler.get_jobs()
                                if str(job.args[0]) == str(task["id"])
                            ]
                        ),
                        "%a, %b %-d, %Y %H:%M:%S",
                    )
                    if [
                        job.next_run_time
                        for job in app.apscheduler.get_jobs()
                        if str(job.args[0]) == str(task["id"])
                    ]
                    else "None"
                ),
                "class": "error"
                if task["status_id"] == 2
                or (
                    len(
                        [
                            job.next_run_time
                            for job in app.apscheduler.get_jobs()
                            if str(job.args[0]) == str(task["id"])
                            and job.next_run_time is not None
                        ]
                        or []
                    )
                    == 0
                    and task["enabled"] == 1
                )
                else "",
            }
        )
        for task in task_list
    ]

    table = (
        sorted(table, key=lambda k: k[split_sort[0]])
        if split_sort[1] == "desc"
        else sorted(table, key=lambda k: k[split_sort[0]], reverse=True)
    )
    [me.append(s) for s in table[page * 10 : page * 10 + 10]]

    me.append({"total": len(table) or 0})  # runs.total
    me.append({"page": page})  # page
    me.append({"sort": sort})  # page

    return jsonify(me)


@app.route("/connection/sftp")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_sftp():
    """ return html page for adding a sftp conncetion """
    return render_template("pages/connection/sftp.html.j2")


@app.route("/connection/smb")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_smb():
    """ return html page for adding a smb conncetion """
    return render_template("pages/connection/smb.html.j2")


@app.route("/connection/ssh")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_ssh():
    """ return html page for adding a smb conncetion """
    return render_template("pages/connection/ssh.html.j2")


@app.route("/connection/database")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_database():
    """ return html page for adding a smb conncetion """
    return render_template("pages/connection/database.html.j2")


@app.route("/connection/ftp")
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_ftp():
    """ return html page for adding a smb conncetion """
    return render_template("pages/connection/ftp.html.j2")


@app.route("/connection/new", methods=["POST", "GET"])
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_new():
    """ adding a new destination """
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

        for x in sftp_list:
            if "sftp" + x + "-name" in form and form["sftp" + x + "-name"] != "":
                sftp = ConnectionSftp(
                    connection_id=me.id,
                    name=form["sftp" + x + "-name"],
                    address=form["sftp" + x + "-addr"],
                    port=form["sftp" + x + "-port"],
                    path=form["sftp" + x + "-path"],
                    username=form["sftp" + x + "-user"],
                    password=em_encrypt(form["sftp" + x + "-pass"]),
                )
                db.session.add(sftp)
                db.session.commit()

                log = TaskLog(
                    status_id=7,
                    message=g.user_full_name
                    + ": Connection Sftp added. ("
                    + str(me.id)
                    + " "
                    + me.name
                    + " "
                    + str(sftp.id)
                    + " "
                    + sftp.name
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

        for x in ssh_list:
            if "ssh" + x + "-name" in form and form["ssh" + x + "-name"] != "":
                ssh = ConnectionSsh(
                    connection_id=me.id,
                    name=form["ssh" + x + "-name"],
                    address=form["ssh" + x + "-addr"],
                    path=form["ssh" + x + "-path"],
                    username=form["ssh" + x + "-user"],
                    password=em_encrypt(form["ssh" + x + "-pass"]),
                )
                db.session.add(ssh)
                db.session.commit()

                log = TaskLog(
                    status_id=7,
                    message=g.user_full_name
                    + ": Connection SSH added. ("
                    + str(me.id)
                    + " "
                    + me.name
                    + " "
                    + str(ssh.id)
                    + " "
                    + ssh.name
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

        for x in ftp_list:
            if "ftp" + x + "-name" in form and form["ftp" + x + "-name"] != "":
                ftp = ConnectionFtp(
                    connection_id=me.id,
                    name=form["ftp" + x + "-name"],
                    address=form["ftp" + x + "-addr"],
                    path=form["ftp" + x + "-path"],
                    username=form["ftp" + x + "-user"],
                    password=em_encrypt(form["ftp" + x + "-pass"]),
                )
                db.session.add(ftp)
                db.session.commit()
                log = TaskLog(
                    status_id=7,
                    message=g.user_full_name
                    + ": Connection Ftp added. ("
                    + str(me.id)
                    + " "
                    + me.name
                    + " "
                    + str(ftp.id)
                    + " "
                    + ftp.name
                    + ")",
                )
                db.session.add(log)
                db.session.commit()

        smb_list = [
            k.split("smb")[1].split("-")[0]
            for k, v in form.items()
            if k.startswith("smb") and "name" in k
        ]

        for x in smb_list:
            if "smb" + x + "-name" in form and form["smb" + x + "-name"] != "":
                smb = ConnectionSmb(connection_id=me.id)
                db.session.add(smb)

                smb.connection_id = me.id
                smb.name = form["smb" + x + "-name"]
                smb.server_name = form["smb" + x + "-server-name"]
                smb.server_ip = form["smb" + x + "-server-ip"]
                smb.share_name = form["smb" + x + "-share-name"]
                smb.path = form["smb" + x + "-path"]
                smb.username = form["smb" + x + "-user"]
                smb.password = em_encrypt(form["smb" + x + "-pass"])

                db.session.commit()

                log = TaskLog(
                    status_id=7,
                    message=g.user_full_name
                    + ": Connection Smb added. ("
                    + str(me.id)
                    + " "
                    + me.name
                    + " "
                    + str(smb.id)
                    + " "
                    + smb.name
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

        for x in database_list:
            # try to get first, else create.
            if (
                "database" + x + "-name" in form
                and form["database" + x + "-name"] != ""
            ):
                database = ConnectionDatabase(connection_id=me.id)
                db.session.add(database)

                database.connection_id = me.id
                database.name = form["database" + x + "-name"]
                database.type_id = form["database" + x + "-type"]
                database.connection_string = em_encrypt(form["database" + x + "-conn"])

                db.session.commit()

                log = TaskLog(
                    status_id=7,
                    message=g.user_full_name
                    + ": Connection Database added. ("
                    + str(me.id)
                    + " "
                    + me.name
                    + " "
                    + str(database.id)
                    + " "
                    + database.name
                    + ")",
                )
                db.session.add(log)
                db.session.commit()

        log = TaskLog(
            status_id=7,
            message=g.user_full_name
            + ": Connection group added. ("
            + str(me.id)
            + " "
            + me.name
            + ")",
        )
        db.session.add(log)
        db.session.commit()

    return redirect(url_for("connection"))


@app.route("/connection/remove/<my_id>", methods=["GET"])
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_remove(my_id):
    """ remove a destination """
    ConnectionSftp.query.filter_by(connection_id=my_id).delete()
    ConnectionFtp.query.filter_by(connection_id=my_id).delete()
    ConnectionSmb.query.filter_by(connection_id=my_id).delete()
    ConnectionDatabase.query.filter_by(connection_id=my_id).delete()
    Connection.query.filter_by(id=my_id).delete()
    db.session.commit()

    log = TaskLog(
        status_id=7,
        message=g.user_full_name + ": Connection removed. (" + str(my_id) + ")",
    )
    db.session.add(log)
    db.session.commit()
    return redirect(url_for("connection"))


@app.route("/connection/<conn_id>/removeSftp/<my_id>", methods=["GET"])
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_remove_sftp(conn_id, my_id):
    ConnectionSftp.query.filter_by(connection_id=conn_id, id=my_id).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=g.user_full_name + ": Connection Sftp removed. (" + str(my_id) + ")",
    )
    db.session.add(log)
    db.session.commit()
    return redirect(url_for("connection_edit", my_id=conn_id))


@app.route("/connection/<conn_id>/removeSsh/<my_id>", methods=["GET"])
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_remove_ssh(conn_id, my_id):
    ConnectionSsh.query.filter_by(connection_id=conn_id, id=my_id).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=g.user_full_name + ": Connection Ssh removed. (" + str(my_id) + ")",
    )
    db.session.add(log)
    db.session.commit()
    return redirect(url_for("connection_edit", my_id=conn_id))


@app.route("/connection/<conn_id>/removeSmb/<my_id>", methods=["GET"])
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_remove_smb(conn_id, my_id):
    ConnectionSmb.query.filter_by(connection_id=conn_id, id=my_id).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=g.user_full_name + ": Connection Smb removed. (" + str(my_id) + ")",
    )
    db.session.add(log)
    db.session.commit()
    return redirect(url_for("connection_edit", my_id=conn_id))


@app.route("/connection/<conn_id>/removeFtp/<my_id>", methods=["GET"])
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_remove_ftp(conn_id, my_id):
    ConnectionFtp.query.filter_by(connection_id=conn_id, id=my_id).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=g.user_full_name + ": Connection Ftp removed. (" + str(my_id) + ")",
    )
    db.session.add(log)
    db.session.commit()
    return redirect(url_for("connection_edit", my_id=conn_id))


@app.route("/connection/<conn_id>/removeDatabase/<my_id>", methods=["GET"])
# @ldap.login_required
# @ldap.group_required(["Analytics"])
def connection_remove_database(conn_id, my_id):
    ConnectionDatabase.query.filter_by(connection_id=conn_id, id=my_id).delete()
    db.session.commit()
    log = TaskLog(
        status_id=7,
        message=g.user_full_name
        + ": Connection Database removed. ("
        + str(my_id)
        + ")",
    )
    db.session.add(log)
    db.session.commit()
    return redirect(url_for("connection_edit", my_id=conn_id))
