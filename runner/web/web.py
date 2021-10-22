"""Runner API routes."""

import datetime

from flask import Blueprint, jsonify
from jinja2 import Environment, PackageLoader, select_autoescape

from runner import executor
from runner.model import Task, TaskFile
from runner.scripts.em_code import SourceCode
from runner.scripts.em_ftp import Ftp
from runner.scripts.em_sftp import Sftp
from runner.scripts.em_smb import Smb
from runner.scripts.em_smtp import Smtp
from runner.scripts.task_runner import Runner

web_bp = Blueprint("web_bp", __name__)

env = Environment(
    loader=PackageLoader("runner", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


@web_bp.route("/api")
def alive() -> dict:
    """Check API status."""
    return jsonify({"status": "alive"})


@web_bp.route("/api/send_ftp/<task_id>/<run_id>/<file_id>")
def send_ftp(task_id: int, run_id: int, file_id: int) -> dict:
    """Send file to FPT server specified in the task.

    File is loaded from the backup SMB file server into a tempfile.
    The tempfile is deposited into the FTP location.
    """
    try:
        task = Task.query.filter_by(id=task_id).first()
        my_file = TaskFile.query.filter_by(id=file_id).first()

        Ftp(
            task=task,
            connection=task.destination_ftp_conn,
            overwrite=1,
            file_name=my_file.name,
            file_path=Smb(
                task=task,
                connection=None,  # "default",
                overwrite=0,
                file_name="",
                file_path=str(my_file.path),
                job_hash=str(run_id),
            ).read()
            or "",
            job_hash=str(run_id),
        ).save()

        return jsonify({"message": "successfully sent file."})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/api/send_sftp/<task_id>/<run_id>/<file_id>")
def send_sftp(task_id: int, run_id: int, file_id: int) -> dict:
    """Send file to SFPT server specified in the task.

    File is loaded from the backup SMB file server into a tempfile.
    The tempfile is deposited into the SFTP location.
    """
    try:
        task = Task.query.filter_by(id=task_id).first()
        my_file = TaskFile.query.filter_by(id=file_id).first()

        Sftp(
            task=task,
            connection=task.destination_sftp_conn,
            overwrite=1,
            file_name=my_file.name,
            file_path=Smb(
                task=task,
                connection=None,  # "default",
                overwrite=0,
                file_name="",
                file_path=my_file.path,
                job_hash=str(run_id),
            ).read()
            or "",  # is full path
            job_hash=str(run_id),
        ).save()

        return jsonify({"message": "successfully sent file."})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/api/send_smb/<task_id>/<run_id>/<file_id>")
def send_smb(task_id: int, run_id: int, file_id: int) -> dict:
    """Send file to SMB server specified in the task.

    File is loaded from the backup SMB file server into a tempfile.
    The tempfile is deposited into the SMB location.
    """
    try:
        task = Task.query.filter_by(id=task_id).first()
        my_file = TaskFile.query.filter_by(id=file_id).first()

        Smb(
            task=task,
            connection=task.destination_smb_conn,
            overwrite=1,
            file_name=my_file.name,
            file_path=Smb(
                task=task,
                connection=None,  # "default",
                overwrite=0,
                file_name="",
                file_path=my_file.path,
                job_hash=str(run_id),
            ).read()
            or "",
            job_hash=str(run_id),
        ).save()

        return jsonify({"message": "successfully sent file."})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/api/send_email/<task_id>/<run_id>/<file_id>")
def send_email(task_id: int, run_id: int, file_id: int) -> dict:
    """Send file to email address specified in the task.

    File is loaded from the backup SMB file server into a tempfile.
    The tempfile is sent as an email attachment.
    """
    try:
        task = Task.query.filter_by(id=task_id).first()
        my_file = TaskFile.query.filter_by(id=file_id).first()

        date = str(datetime.datetime.now())

        template = env.get_template("email/email.html.j2")

        Smtp(
            task=task,
            recipients=task.email_completion_recipients,
            subject="(Manual Send) Project: "
            + task.project.name
            + " / Task: "
            + task.name,
            message=template.render(
                task=task,
                success=1,
                date=date,
                logs=[],
            ),
            attachment=Smb(
                task=task,
                connection=None,  # "default",
                overwrite=0,
                file_name="",
                file_path=my_file.path or "",
                job_hash=str(run_id),
            ).read()
            or "",
            attachment_name=my_file.name,
            job_hash=str(run_id),
        )

        return jsonify({"message": "successfully sent file."})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/api/<task_id>")
def run(task_id: int) -> dict:
    """Run specified task."""
    executor.submit(Runner, task_id)

    return jsonify({"message": "runner completed."})


@web_bp.route("/api/<task_id>/source_code")
def task_get_source_code(task_id: int) -> dict:
    """Get source code for a task."""
    try:
        task = Task.query.filter_by(id=task_id).first()
        # pylint: disable=R1705
        if task.source_query_type_id == 1:
            return jsonify({"code": SourceCode(task, task.source_git, None).gitlab()})
        elif task.source_query_type_id == 3:
            return jsonify({"code": SourceCode(task, task.source_url, None).web_url()})
        elif task.source_query_type_id == 4:
            return jsonify({"code": SourceCode(task, None, None).source()})

        return jsonify({})
    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/api/<task_id>/processing_code")
def task_get_processing_git_code(task_id: int) -> dict:
    """Get processing code for a task."""
    try:
        task = Task.query.filter_by(id=task_id).first()
        # pylint: disable=R1705
        if task.processing_type_id == 4:
            return jsonify(
                {"code": SourceCode(task, task.processing_git, None).gitlab()}
            )
        elif task.processing_type_id == 5:
            return jsonify(
                {"code": SourceCode(task, task.processing_url, None).web_url()}
            )
        elif task.processing_type_id == 6:
            # we should be using the sourcecode class to insert vars
            return jsonify({"code": task.processing_code})

        return jsonify({})
    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/api/file/<file_id>")
def get_task_file_download(file_id: int) -> dict:
    """Download file from SMB backup server."""
    my_file = TaskFile.query.filter_by(id=file_id).first()
    task = Task.query.filter_by(id=my_file.task_id).first()

    temp_file = Smb(
        task=task,
        connection=None,  # "default",
        overwrite=0,
        file_name=None,
        file_path=my_file.path,
        job_hash=my_file.job_id,
    ).read()

    return jsonify({"message": temp_file})
