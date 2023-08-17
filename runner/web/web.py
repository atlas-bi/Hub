"""Runner API routes."""

import datetime
import sys
import re
from pathlib import Path

from flask import Blueprint
from flask import current_app as app
from flask import jsonify
from jinja2 import Environment, PackageLoader, select_autoescape
from pathvalidate import sanitize_filename

from runner import executor
from runner.model import (
    ConnectionDatabase,
    ConnectionFtp,
    ConnectionSftp,
    ConnectionSmb,
    ConnectionSsh,
    Task,
    TaskFile,
)
from runner.scripts.em_code import SourceCode
from runner.scripts.em_date import DateParsing
from runner.scripts.em_ftp import Ftp
from runner.scripts.em_ftp import connect as ftp_connect
from runner.scripts.em_params import ParamLoader
from runner.scripts.em_postgres import connect as pg_connect
from runner.scripts.em_sftp import Sftp
from runner.scripts.em_sftp import connect as sftp_connect
from runner.scripts.em_smb import Smb
from runner.scripts.em_smb import connect as smb_connect
from runner.scripts.em_smtp import Smtp
from runner.scripts.em_sqlserver import connect as sql_connect
from runner.scripts.em_ssh import connect as ssh_connect
from runner.scripts.task_runner import Runner

web_bp = Blueprint("web_bp", __name__)

env = Environment(
    loader=PackageLoader("runner", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from crypto import em_decrypt


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

        temp_path = Path(
            Path(__file__).parent.parent
            / "temp"
            / sanitize_filename(task.project.name)
            / sanitize_filename(task.name)
            / my_file.job_id
        )

        temp_path.mkdir(parents=True, exist_ok=True)

        # download the file
        Smb(
            task=task,
            run_id=my_file.job_id,
            connection=None,  # "default",
            directory=temp_path,
        ).read(my_file.path)

        # upload the file
        Ftp(
            task=task,
            run_id=str(run_id),
            connection=task.destination_ftp_conn,
            directory=temp_path,
        ).save(overwrite=1, file_name=my_file.name)

        return jsonify({"message": "successfully sent file."})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/api/send_sftp/<run_id>/<file_id>")
def send_sftp(run_id: int, file_id: int) -> dict:
    """Send file to SFPT server specified in the task.

    File is loaded from the backup SMB file server into a tempfile.
    The tempfile is deposited into the SFTP location.
    """
    try:
        my_file = TaskFile.query.filter_by(id=file_id).first()
        task = my_file.task

        temp_path = Path(
            Path(__file__).parent.parent
            / "temp"
            / sanitize_filename(task.project.name)
            / sanitize_filename(task.name)
            / my_file.job_id
        )

        temp_path.mkdir(parents=True, exist_ok=True)

        # download the file
        Smb(
            task=task,
            run_id=my_file.job_id,
            connection=None,  # "default",
            directory=temp_path,
        ).read(my_file.path)

        # upload the file
        Sftp(
            task=task,
            run_id=str(run_id),
            connection=task.destination_sftp_conn,
            directory=temp_path,
        ).save(
            overwrite=1,
            file_name=my_file.name,
        )

        return jsonify({"message": "successfully sent file."})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/api/send_smb/<run_id>/<file_id>")
def send_smb(run_id: int, file_id: int) -> dict:
    """Send file to SMB server specified in the task.

    File is loaded from the backup SMB file server into a tempfile.
    The tempfile is deposited into the SMB location.
    """
    try:
        my_file = TaskFile.query.filter_by(id=file_id).first()
        task = my_file.task

        temp_path = Path(
            Path(__file__).parent.parent
            / "temp"
            / sanitize_filename(task.project.name)
            / sanitize_filename(task.name)
            / my_file.job_id
        )

        temp_path.mkdir(parents=True, exist_ok=True)

        # download the file
        Smb(
            task=task,
            run_id=my_file.job_id,
            connection=None,  # "default",
            directory=temp_path,
        ).read(my_file.path)

        # upload the file
        Smb(
            task=task,
            run_id=str(run_id),
            connection=task.destination_smb_conn,
            directory=temp_path,
        ).save(
            overwrite=1,
            file_name=my_file.name,
        )

        return jsonify({"message": "successfully sent file."})

    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/api/send_email/<task_id>/<run_id>/<file_id>")
def send_email(run_id: int, file_id: int) -> dict:
    """Send file to email address specified in the task.

    File is loaded from the backup SMB file server into a tempfile.
    The tempfile is sent as an email attachment.
    """
    try:
        my_file = TaskFile.query.filter_by(id=file_id).first()
        task = my_file.task

        temp_path = Path(
            Path(__file__).parent.parent
            / "temp"
            / sanitize_filename(task.project.name)
            / sanitize_filename(task.name)
            / my_file.job_id
        )

        temp_path.mkdir(parents=True, exist_ok=True)

        # download the file
        downloaded_files = Smb(
            task=task,
            run_id=my_file.job_id,
            connection=None,  # "default",
            directory=temp_path,
        ).read(my_file.path)

        # send the file

        date = datetime.datetime.now()

        template = env.get_template("email/email.html.j2")

        Smtp(
            task=task,
            run_id=str(run_id),
            recipients=task.email_completion_recipients,
            short_message=f"Atlas Hub: {task.name} data emailed.",
            subject="(Manual Send) Project: "
            + task.project.name
            + " / Task: "
            + task.name,
            message=template.render(
                task=task, success=1, date=date, logs=[], org=app.config["ORG_NAME"]
            ),
            attachments=[x.name for x in downloaded_files],
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
        params = ParamLoader(task, None)
        source = SourceCode(task, None, params)
        # pylint: disable=R1705
        if task.source_query_type_id == 1:
            return jsonify({"code": source.gitlab(task.source_git)})
        elif task.source_query_type_id == 7:
            return jsonify({"code": source.devops(task.source_devops)})
        elif task.source_query_type_id == 3:
            return jsonify({"code": source.web_url(task.source_url)})
        elif task.source_query_type_id == 4:
            return jsonify({"code": source.source()})

        return jsonify({})
    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/api/<task_id>/processing_code")
def task_get_processing_git_code(task_id: int) -> dict:
    """Get processing code for a task."""
    try:
        task = Task.query.filter_by(id=task_id).first()
        params = ParamLoader(task, None)
        source = SourceCode(task, None, params)
        # pylint: disable=R1705
        if task.processing_type_id == 4:
            return jsonify({"code": source.gitlab(task.processing_git)})
        elif task.processing_type_id == 5:
            return jsonify({"code": source.web_url(task.processing_url)})
        elif task.processing_type_id == 6:
            # we should be using the sourcecode class to insert vars
            return jsonify({"code": task.processing_code})
        elif task.processing_type_id == 7:
            #if there is a branch we need rearrange the url.
            branch = re.findall(r"(&version[=]GB.+?)$",task.processing_devops)
            url = re.sub((branch[0] if len(branch) >0 else ''),'',task.processing_devops) + "/"+task.processing_command + (branch[0] if len(branch) >0 else '')
            return jsonify({"code": source.devops(url)})
        return jsonify({})
    # pylint: disable=broad-except
    except BaseException as e:
        return jsonify({"error": str(e)})


@web_bp.route("/api/file/<file_id>")
def get_task_file_download(file_id: int) -> dict:
    """Download file from SMB backup server."""
    my_file = TaskFile.query.filter_by(id=file_id).first()
    task = my_file.task

    temp_path = Path(
        Path(__file__).parent.parent
        / "temp"
        / sanitize_filename(task.project.name)
        / sanitize_filename(task.name)
        / my_file.job_id
    )

    temp_path.mkdir(parents=True, exist_ok=True)

    temp_file = (
        Smb(
            task=task,
            run_id=my_file.job_id,
            connection=None,  # "default",
            directory=temp_path,
        )
        .read(my_file.path)[0]
        .name
    )

    return jsonify({"message": temp_file})


@web_bp.route("/api/ssh/<ssh_id>/status")
def ssh_online(ssh_id: int) -> str:
    """Check if connection is online."""
    try:
        ssh_connection = ConnectionSsh.query.filter_by(id=ssh_id).first()
        session = ssh_connect(ssh_connection)
        session.close()
        return '<span class="tag is-success is-light">Online</span>'
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">Offline</span>'


@web_bp.route("/api/database/<database_id>/status")
def database_online(database_id: int) -> str:
    """Check if connection is online."""
    try:
        database_connection = ConnectionDatabase.query.filter_by(id=database_id).first()
        if database_connection.type_id == 2:
            conn, _ = sql_connect(
                em_decrypt(
                    database_connection.connection_string, app.config["PASS_KEY"]
                ).strip(),
                database_connection.timeout or app.config["DEFAULT_SQL_TIMEOUT"],
            )
            conn.close()
        else:
            conn, _ = pg_connect(
                em_decrypt(
                    database_connection.connection_string, app.config["PASS_KEY"]
                ).strip(),
                database_connection.timeout or app.config["DEFAULT_SQL_TIMEOUT"],
            )
            conn.close()

        return '<span class="tag is-success is-light">Online</span>'
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">Offline</span>'


@web_bp.route("/api/sftp/<sftp_id>/status")
def sftp_online(sftp_id: int) -> str:
    """Check if connection is online."""
    try:
        sftp_connection = ConnectionSftp.query.filter_by(id=sftp_id).first()
        transport, conn = sftp_connect(sftp_connection)
        conn.close()
        transport.close()
        return '<span class="tag is-success is-light">Online</span>'
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">Offline</span>'


@web_bp.route("/api/ftp/<ftp_id>/status")
def ftp_online(ftp_id: int) -> str:
    """Check if connection is online."""
    try:
        ftp_connection = ConnectionFtp.query.filter_by(id=ftp_id).first()
        conn = ftp_connect(ftp_connection)
        conn.close()
        return '<span class="tag is-success is-light">Online</span>'
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">Offline</span>'


@web_bp.route("/api/smb/<smb_id>/status")
def smb_online(smb_id: int) -> str:
    """Check if connection is online."""
    try:
        smb_connection = ConnectionSmb.query.filter_by(id=smb_id).first()
        smb_connect(
            smb_connection.username,
            em_decrypt(smb_connection.password, app.config["PASS_KEY"]),
            smb_connection.server_name,
            smb_connection.server_ip,
        )
        # we do not close smb connections. they are recycled.
        return '<span class="tag is-success is-light">Online</span>'
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">Offline</span>'


@web_bp.route("/api/task/<task_id>/filename_preview")
def filename_preview(task_id: int) -> str:
    """Generate filename preview."""
    try:
        task = Task.query.filter_by(id=task_id).first()
        param_loader = ParamLoader(task, None)

        # insert params
        file_name = param_loader.insert_file_params(task.destination_file_name)

        # parse python dates
        file_name = DateParsing(task, None, file_name).string_to_date()

        if task.file_type and task.file_type.id != 4:
            file_name = f"{file_name}.{task.file_type.ext}"

        return f'<span class="tag is-success is-light">ex: {file_name}</span>'
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">No preview.</span>'


@web_bp.route("/api/task/<task_id>/email_success_subject_preview")
def email_success_subject_preview(task_id: int) -> str:
    """Generate email subject preview."""
    try:
        task = Task.query.filter_by(id=task_id).first()
        param_loader = ParamLoader(task, None)

        # insert params
        email_subject = param_loader.insert_file_params(task.email_completion_subject)

        # parse python dates
        email_subject = DateParsing(task, None, email_subject).string_to_date()

        if task.file_type and task.file_type.id != 4:
            email_subject = f"{email_subject}.{task.file_type.ext}"

        return f'<span class="tag is-success is-light">ex: {email_subject}</span>'
    except BaseException as e:
        return f'<span class="has-tooltip-arrow has-tooltip-right has-tooltip-multiline tag is-danger is-light" data-tooltip="{e}">No preview.</span>'


@web_bp.route("/api/task/<task_id>/refresh_cache")
def refresh_cache(task_id: int) -> str:
    """Get source code for a task."""
    try:
        task = Task.query.filter_by(id=task_id).first()
        params = ParamLoader(task, None)
        source = SourceCode(task=task, run_id=None, params=params, refresh_cache=True)
        # cache is only saveable for downloaded code from git and web.
        # pylint: disable=R1705
        if task.source_query_type_id == 1:
            source.gitlab(task.source_git)
            return "Cache refreshed."
        elif task.source_query_type_id == 3:
            source.web_url(task.source_url)
            return "Cache refreshed."
        elif task.source_query_type_id == 7:
            source.devops(task.source_devops)
            return "Cache refreshed."

        return "Cache refreshing is only for git or web source queries."
    # pylint: disable=broad-except
    except BaseException:
        return "Failed to refresh cache."
