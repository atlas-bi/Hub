"""Task web views."""

import json
import os
import zipfile
from dataclasses import dataclass
from typing import Generator, Optional

import requests
from flask import Blueprint
from flask import current_app as app
from flask import jsonify, redirect, send_file, url_for
from flask_login import current_user, login_required
from werkzeug.wrappers import Response

from runner.model import Task, TaskLog
from web import db
from web.model import TaskFile

task_files_bp = Blueprint("task_files_bp", __name__)


@dataclass
class RunnerLog:
    """Save log messages."""

    task: Task
    run_id: Optional[str]
    source_id: int
    message: str
    error: Optional[int] = 0

    def __post_init__(self) -> None:
        """Save message."""
        log = TaskLog(
            task_id=self.task.id,
            job_id=self.run_id,
            error=self.error,
            status_id=self.source_id,
            message=f"{self.message}",
        )
        db.session.add(log)
        db.session.commit()


@task_files_bp.route("/task/<task_id>/filename_preview")
@login_required
def filename_preview(task_id: int) -> str:
    """Generate a task filename preview."""
    try:
        return requests.get(
            f"{app.config['RUNNER_HOST']}/task/{task_id}/filename_preview", timeout=60
        ).text
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">Offline</span>'


@task_files_bp.route("/task/<task_id>/file/<file_id>/sendSftp")
@login_required
def one_task_file_send_sftp(task_id: int, file_id: int) -> Response:
    """Reload task SFTP output."""
    try:
        my_file = TaskFile.query.filter_by(id=file_id).first()
        output = requests.get(
            f"{app.config['RUNNER_HOST']}/send_sftp/{my_file.job_id}/{file_id}",
            timeout=60,
        ).json()
        if output.get("error"):
            raise ValueError(output.get("error"))

        RunnerLog(
            my_file.task,
            my_file.job_id,
            7,
            f"{current_user.full_name} Manually sending file to SFTP server.\n{my_file.name}",
        )

    except BaseException as e:
        RunnerLog(
            my_file.task,
            my_file.job_id,
            7,
            f"{current_user.full_name} Failed to manually sending file to SFTP server.\n{my_file.name}\n{e}",
            1,
        )

    return redirect(url_for("task_bp.one_task", task_id=task_id))


@task_files_bp.route("/task/<task_id>/file/<file_id>/sendFtp")
@login_required
def one_task_file_send_ftp(task_id: int, file_id: int) -> Response:
    """Reload task FTP output."""
    try:
        my_file = TaskFile.query.filter_by(id=file_id).first()
        output = requests.get(
            f"{app.config['RUNNER_HOST']}/send_ftp/{task_id}/{my_file.job_id}/{file_id}",
            timeout=60,
        ).json()
        if output.get("error"):
            raise ValueError(output.get("error"))

        RunnerLog(
            my_file.task,
            my_file.job_id,
            7,
            f"{current_user.full_name} Manually sending file to FTP server.\n{my_file.name}",
        )

    except BaseException as e:
        RunnerLog(
            my_file.task,
            my_file.job_id,
            7,
            f"{current_user.full_name} Failed to manually sending file to FTP server.\n{my_file.name}\n{e}",
            1,
        )

    return redirect(url_for("task_bp.one_task", task_id=task_id))


@task_files_bp.route("/task/<task_id>/file/<file_id>/sendSmb")
@login_required
def one_task_file_send_smb(task_id: int, file_id: int) -> Response:
    """Reload task SMB output."""
    try:
        my_file = TaskFile.query.filter_by(id=file_id).first()
        output = requests.get(
            f"{app.config['RUNNER_HOST']}/send_smb/{my_file.job_id}/{file_id}",
            timeout=60,
        ).json()
        if output.get("error"):
            raise ValueError(output.get("error"))

        RunnerLog(
            my_file.task,
            my_file.job_id,
            7,
            f"{current_user.full_name} Manually sending file to SMB server.\n{my_file.name}",
        )

    except BaseException as e:
        RunnerLog(
            my_file.task,
            my_file.job_id,
            7,
            f"{current_user.full_name} Failed to manually sending file to SMB server.\n{my_file.name}\n{e}",
            1,
        )

    return redirect(url_for("task_bp.one_task", task_id=task_id))


@task_files_bp.route("/task/<task_id>/file/<file_id>/sendEmail")
@login_required
def one_task_file_send_email(task_id: int, file_id: int) -> Response:
    """Resend task email output."""
    try:
        my_file = TaskFile.query.filter_by(id=file_id).first()
        output = requests.get(
            f"{app.config['RUNNER_HOST']}/send_email/{task_id}/{my_file.job_id}/{file_id}",
            timeout=60,
        ).json()
        if output.get("error"):
            raise ValueError(output.get("error"))

        RunnerLog(
            my_file.task,
            my_file.job_id,
            7,
            f"{current_user.full_name} Manually sending file to email.\n{my_file.name}",
        )

    except BaseException as e:
        RunnerLog(
            my_file.task,
            my_file.job_id,
            7,
            f"{current_user.full_name} Failed to manually sending file to email.\n{my_file.name}\n{e}",
            1,
        )

    return redirect(url_for("task_bp.one_task", task_id=task_id))


@task_files_bp.route("/file/<file_id>")
@login_required
def one_task_file_download(file_id: int) -> Response:
    """Download task backup file."""
    my_file = TaskFile.query.filter_by(id=file_id).first()

    if my_file:
        RunnerLog(
            my_file.task,
            my_file.job_id,
            7,
            f"{current_user.full_name} Manually downloading file.\n{my_file.name}",
        )

        source_file = json.loads(
            requests.get("%s/file/%s" % (app.config["RUNNER_HOST"], file_id), timeout=60).text,
        ).get("message")

        def stream_and_remove_file() -> Generator:
            yield from file_handle
            os.remove(source_file)

        # check if it is a zip

        if zipfile.is_zipfile(source_file):
            return send_file(source_file, as_attachment=True, download_name=my_file.name)

        # otherwise, stream it.
        # pylint: disable=R1732
        file_handle = open(source_file, "r")  # noqa:SIM115

        return Response(
            stream_and_remove_file(),
            mimetype="text",
            headers={"Content-disposition": "attachment; filename=" + my_file.name},
        )

    return jsonify({"error": "no such file."})
