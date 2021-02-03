"""EM Runner API routes."""
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


import datetime
import os
import tempfile
from pathlib import Path

from em_runner import executor
from em_runner.model import Task, TaskFile
from em_runner.scripts.em_cmd import Cmd
from em_runner.scripts.em_code import SourceCode
from em_runner.scripts.em_ftp import Ftp
from em_runner.scripts.em_sftp import Sftp
from em_runner.scripts.em_smb import Smb
from em_runner.scripts.em_smtp import Smtp
from em_runner.scripts.runner import Runner
from flask import Blueprint, jsonify
from jinja2 import Environment, PackageLoader, select_autoescape

web_bp = Blueprint("web_bp", __name__)

env = Environment(
    loader=PackageLoader("em_runner", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


@web_bp.route("/send_ftp/<task_id>/<run_id>/<file_id>")
def send_ftp(task_id, run_id, file_id):
    """Send file to FPT server specified in the task.

    :url: /api/send_ftp/<task_id>/<run_id>/<file_id>
    :param task_id: id of task owning the connection
    :param run_id: id of the run associated with the file
    :param file_id: id of the file to send

    :returns: json message or error

    File is loaded from the backup SMB file server into a tempfile.
    The tempfile is deposited into the FTP location.
    """
    try:
        task = Task.query.filter_by(id=task_id).first()
        my_file = TaskFile.query.filter_by(id=file_id).first()

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
            temp.write(
                Smb(
                    task,
                    "default",
                    None,
                    "",
                    my_file.path,
                    job_hash=run_id,
                ).read()
            )

        Ftp(
            task,
            task.destination_ftp_conn,
            1,
            file_id,
            temp.name,
            run_id,
        ).save()

        os.remove(temp.name)

        return jsonify({"message": "successfully sent file."})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/send_sftp/<task_id>/<run_id>/<file_id>")
def send_sftp(task_id, run_id, file_id):
    """Send file to SFPT server specified in the task.

    :url: /api/send_sftp/<task_id>/<run_id>/<file_id>
    :param task_id: id of task owning the connection
    :param run_id: id of the run associated with the file
    :param file_id: id of the file to send

    :returns: json message or error

    File is loaded from the backup SMB file server into a tempfile.
    The tempfile is deposited into the SFTP location.
    """
    try:
        task = Task.query.filter_by(id=task_id).first()
        my_file = TaskFile.query.filter_by(id=file_id).first()

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
            temp.write(
                Smb(
                    task,
                    "default",
                    None,
                    "",
                    my_file.path,
                    job_hash=run_id,
                ).read()
            )

        Sftp(
            task,
            task.destination_sftp_conn,
            1,
            my_file.name,
            temp.name,  # is full path
            job_hash=run_id,
        ).save()

        os.remove(temp.name)

        return jsonify({"message": "successfully sent file."})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/send_smb/<task_id>/<run_id>/<file_id>")
def send_smb(task_id, run_id, file_id):
    """Send file to SMB server specified in the task.

    :url: /api/send_smb/<task_id>/<run_id>/<file_id>
    :param task_id: id of task owning the connection
    :param run_id: id of the run associated with the file
    :param file_id: id of the file to send

    :returns: json message or error

    File is loaded from the backup SMB file server into a tempfile.
    The tempfile is deposited into the SMB location.
    """
    try:
        task = Task.query.filter_by(id=task_id).first()
        my_file = TaskFile.query.filter_by(id=file_id).first()

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
            temp.write(
                Smb(
                    task,
                    "default",
                    None,
                    "",
                    my_file.path,
                    job_hash=run_id,
                ).read()
            )

        Smb(
            task, task.destination_smb_conn, 1, my_file.name, temp.name, job_hash=run_id
        ).save()

        os.remove(temp.name)

        return jsonify({"message": "successfully sent file."})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/send_email/<task_id>/<run_id>/<file_id>")
def send_email(task_id, run_id, file_id):
    """Send file to email address specified in the task.

    :url: /api/send_email/<task_id>/<run_id>/<file_id>
    :param task_id: id of task owning the connection
    :param run_id: id of the run associated with the file
    :param file_id: id of the file to send

    :returns: json message or error

    File is loaded from the backup SMB file server into a tempfile.
    The tempfile is sent as an email attachment.
    """
    try:
        task = Task.query.filter_by(id=task_id).first()
        my_file = TaskFile.query.filter_by(id=file_id).first()

        date = str(datetime.datetime.now())

        template = env.get_template("email/email.html.j2")

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp:
            temp.write(
                Smb(
                    task,
                    "default",
                    None,
                    "",
                    my_file.path,
                    job_hash=run_id,
                ).read()
            )

        Smtp(
            task,
            task.email_completion_recipients,
            "(Manual Send) Project: " + task.project.name + " / Task: " + task.name,
            template.render(
                task=task,
                success=1,
                date=date,
                logs=[],
            ),
            temp.name,
            my_file.name,
            job_hash=run_id,
        )

        os.remove(temp.name)

        return jsonify({"message": "successfully sent file."})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/whoami")
def whoami():
    """Run `whoami` command on host server.

    :url: /api/whoami
    :returns: json message: who the owner server user is, or error.
    """
    try:
        cmd = "$(which whoami)"
        output = Cmd(None, cmd, "Whoami run.", "whomai failed: " + cmd, None).shell()

        return jsonify({"message": "whoami: " + output})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "whoami failed: " + str(e)})


@web_bp.route("/reloadDaemon")
def reload_daemon():
    """Reload server service daemons.

    :url: /api/reloadDaemon
    :returns: json message or error

    """
    try:
        cmd = "$(which sudo) $(which systemctl) daemon-reload"

        output = Cmd(
            None,
            cmd,
            "Web Service Reloaded.",
            "Failed to reload web service: " + cmd,
            None,
        ).shell()

        return jsonify({"message": "Reload server service daemon: " + output})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "Failed to reload web service: " + str(e)})


@web_bp.route("/restartDaemon")
def restart_daemon():
    """Restart server service daemons.

    :url: /api/restartDaemon
    :returns: json message or error
    """
    try:
        cmd = (
            "$(which sudo) $(which systemctl) restart"
            + str(Path(__file__).parent.parent.parent.parts[-1])
            + ".service"
        )

        output = Cmd(
            None,
            cmd,
            "Web Service Restarted.",
            "Failed to restart web service: " + cmd,
            None,
        ).shell()

        return jsonify({"message": "Restart server service daemon: " + output})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": "Failed to restart web service: " + str(e)})


@web_bp.route("/<task_id>")
def run(task_id):
    """Run specified task.

    :url: /api/<task_id>
    :param task_id: id of task to run

    :returns: completion message.
    """
    executor.submit(Runner, task_id)

    return jsonify({"message": "runner completed."})


@web_bp.route("/<task_id>/git")
def task_get_git_code(task_id):
    """Get git code for a task.

    :url: /api/<task_id>/git
    :param task_id: id of task

    :returns: html page with source code.
    """
    try:
        task = Task.query.filter_by(id=task_id).first()

        return jsonify({"code": SourceCode(task, task.source_git, None).gitlab()})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/<task_id>/url")
def task_get_url_code(task_id):
    """Get non-git source code for a task.

    :url: /api/<task_id>/url
    :param task_id: id of task

    :returns: html page with source code.
    """
    try:
        task = Task.query.filter_by(id=task_id).first()

        return jsonify({"code": SourceCode(task, task.source_url, None).web_url()})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/<task_id>/source")
def task_get_source_code(task_id):
    """Get source code for a task.

    :url: /api/<task_id>/source
    :param task_id: id of task

    :returns: html page with source code.
    """
    try:
        task = Task.query.filter_by(id=task_id).first()

        return jsonify({"code": SourceCode(task, None, None).source()})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/<task_id>/processing_git")
def task_get_processing_git_code(task_id):
    """Get git code for a task.

    :url: /api/<task_id>/processing_git
    :param task_id: id of task

    :returns: html page with source code.
    """
    try:
        task = Task.query.filter_by(id=task_id).first()

        return jsonify({"code": SourceCode(task, task.processing_git, None).gitlab()})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/<task_id>/processing_url")
def task_get_processing_url_code(task_id):
    """Get non-git code for a task.

    :url: /api/<task_id>/processing_url
    :param task_id: id of task

    :returns: html page with source code.
    """
    try:
        task = Task.query.filter_by(id=task_id).first()

        return jsonify({"code": SourceCode(task, task.processing_url, None).web_url()})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/file/<file_id>")
def get_task_file_download(file_id):
    """Download file from SMB backup server.

    :url: /api/<task_id>/file/<run_id>/<file_id>/download
    :param task_id: id of task owning the file
    :param run_id: id of the run owning the file
    :param file_id: id of the file to download

    :returns: file

    """
    my_file = TaskFile.query.filter_by(id=file_id).first()
    task = Task.query.filter_by(id=my_file.task_id).first()

    temp_file = Smb(
        task,
        "default",
        None,
        "",
        my_file.path,
        my_file.job_id,
    ).read()

    return jsonify({"message": temp_file})
