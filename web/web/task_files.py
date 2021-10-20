"""Task web views."""

import json
import os
import zipfile
from typing import Generator

import requests
from flask import Blueprint
from flask import current_app as app
from flask import jsonify, redirect, send_file, url_for
from flask_login import current_user, login_required
from werkzeug.wrappers import Response

from web import db
from web.model import Task, TaskFile, TaskLog

task_files_bp = Blueprint("task_files_bp", __name__)


@task_files_bp.route("/task/<task_id>/file/<file_id>/sendSftp")
@login_required
def one_task_file_send_sftp(task_id: int, file_id: int) -> Response:
    """Reload task SFTP output."""
    try:
        my_file = TaskFile.query.filter_by(id=file_id).first()
        requests.get(
            app.config["RUNNER_HOST"]
            + "/send_sftp/"
            + task_id
            + "/"
            + my_file.job_id
            + "/"
            + file_id
        )
        task = Task.query.filter_by(id=task_id).first()

        log = TaskLog(
            task_id=task.id,
            job_id=my_file.job_id,
            status_id=7,
            message="("
            + (current_user.full_name or "none")
            + ") Manually sending file to SFTP server: "
            + task.destination_sftp_conn.path
            + my_file.name,
        )
        db.session.add(log)
        db.session.commit()

    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            task_id=task_id,
            job_id=my_file.job_id,
            error=1,
            message=(
                (current_user.full_name or "none")
                + ": Failed to send file to SFTP server. ("
                + str(task_id)
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()

    return redirect(url_for("task_bp.one_task", task_id=task_id))


@task_files_bp.route("/task/<task_id>/file/<file_id>/sendFtp")
@login_required
def one_task_file_send_ftp(task_id: int, file_id: int) -> Response:
    """Reload task FTP output."""
    try:
        my_file = TaskFile.query.filter_by(id=file_id).first()
        requests.get(
            app.config["RUNNER_HOST"]
            + "/send_ftp/"
            + task_id
            + "/"
            + my_file.job_id
            + "/"
            + file_id
        )

        task = Task.query.filter_by(id=task_id).first()

        log = TaskLog(
            task_id=task.id,
            job_id=my_file.job_id,
            status_id=7,
            message="("
            + (current_user.full_name or "none")
            + ") Manually sending file to FTP server: "
            + task.destination_ftp_conn.path
            + "/"
            + my_file.name,
        )
        db.session.add(log)
        db.session.commit()

    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            task_id=task_id,
            job_id=my_file.job_id,
            error=1,
            message=(
                (current_user.full_name or "none")
                + ": Failed to send file to FTP server. ("
                + str(task_id)
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()

    return redirect(url_for("task_bp.one_task", task_id=task_id))


@task_files_bp.route("/task/<task_id>/file/<file_id>/sendSmb")
@login_required
def one_task_file_send_smb(task_id: int, file_id: int) -> Response:
    """Reload task SMB output."""
    try:
        my_file = TaskFile.query.filter_by(id=file_id).first().job_id
        requests.get(
            app.config["RUNNER_HOST"]
            + "/send_smb/"
            + task_id
            + "/"
            + my_file.job_id
            + "/"
            + file_id
        )

        task = Task.query.filter_by(id=task_id).first()

        log = TaskLog(
            task_id=task.id,
            job_id=my_file.job_id,
            status_id=7,
            message="("
            + (current_user.full_name or "none")
            + ") Manually sending file to SMB server: "
            + task.destination_smb_conn.path
            + "/"
            + my_file.name,
        )
        db.session.add(log)
        db.session.commit()
    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            task_id=task_id,
            job_id=my_file.job_id,
            error=1,
            message=(
                (current_user.full_name or "none")
                + ": Failed to send file to SMB server. ("
                + str(task_id)
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()

    return redirect(url_for("task_bp.one_task", task_id=task_id))


@task_files_bp.route("/task/<task_id>/file/<file_id>/sendEmail")
@login_required
def one_task_file_send_email(task_id: int, file_id: int) -> Response:
    """Resend task email output."""
    try:
        my_file = TaskFile.query.filter_by(id=file_id).first()
        requests.get(
            app.config["RUNNER_HOST"]
            + "/send_email/"
            + task_id
            + "/"
            + my_file.job_id
            + "/"
            + file_id
        )

        task = Task.query.filter_by(id=task_id).first()

        log = TaskLog(
            task_id=task.id,
            job_id=my_file.job_id,
            status_id=7,
            message="("
            + (current_user.full_name or "none")
            + ") Manually sending email with file: "
            + my_file.name,
        )
        db.session.add(log)
        db.session.commit()
    # pylint: disable=broad-except
    except BaseException as e:
        log = TaskLog(
            status_id=7,
            task_id=task_id,
            job_id=my_file.job_id,
            error=1,
            message=(
                (current_user.full_name or "none")
                + ": Failed to send email with file. ("
                + str(task_id)
                + ")\n"
                + str(e)
            ),
        )
        db.session.add(log)
        db.session.commit()

    return redirect(url_for("task_bp.one_task", task_id=task_id))


@task_files_bp.route("/file/<file_id>")
@login_required
def one_task_file_download(file_id: int) -> Response:
    """Download task backup file."""
    my_file = TaskFile.query.filter_by(id=file_id)

    if my_file.count() > 0:
        my_file = my_file.first()
        log = TaskLog(
            task_id=my_file.task_id,
            job_id=my_file.job_id,
            status_id=7,
            message=(
                "(%s) Manually downloading file %s."
                % ((current_user.full_name or "none"), my_file.name)
            ),
        )
        db.session.add(log)
        db.session.commit()

        source_file = json.loads(
            requests.get("%s/file/%s" % (app.config["RUNNER_HOST"], file_id)).text
        ).get("message")

        def stream_and_remove_file() -> Generator:
            yield from file_handle
            os.remove(source_file)

        # check if it is a zip

        if zipfile.is_zipfile(source_file):
            return send_file(
                source_file, as_attachment=True, attachment_filename=my_file.name
            )

        # otherwise, stream it.
        # pylint: disable=R1732
        file_handle = open(source_file, "r")  # noqa:SIM115

        return Response(
            stream_and_remove_file(),
            mimetype="text",
            headers={"Content-disposition": "attachment; filename=" + my_file.name},
        )

    return jsonify({"error": "no such file."})
