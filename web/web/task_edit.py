"""Task web views."""

from typing import Union

from crypto import em_encrypt
from flask import Blueprint
from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.wrappers import Response

from web import cache, db
from web.model import (
    Connection,
    ConnectionDatabase,
    ConnectionFtp,
    ConnectionGpg,
    ConnectionSftp,
    ConnectionSmb,
    ConnectionSsh,
    Project,
    QuoteLevel,
    Task,
    TaskDestinationFileType,
    TaskLog,
    TaskParam,
    TaskProcessingType,
    TaskSourceQueryType,
    TaskSourceType,
)
from web.web import submit_executor

from . import get_or_create

task_edit_bp = Blueprint("task_edit_bp", __name__)


@task_edit_bp.route("/project/<project_id>/task/new", methods=["GET"])
@login_required
def task_new_get(project_id: int) -> Union[str, Response]:
    """Create a new task."""
    me = Project.query.filter_by(id=project_id).first()
    if me:
        source_type = TaskSourceType.query.order_by(TaskSourceType.name).all()
        source_query_type = TaskSourceQueryType.query.order_by(
            TaskSourceQueryType.name
        ).all()
        source = ConnectionDatabase.query.order_by(ConnectionDatabase.name).all()
        conn = Connection.query.order_by(Connection.name).all()
        file_type = TaskDestinationFileType.query.order_by(
            TaskDestinationFileType.id
        ).all()
        processing_type = TaskProcessingType.query.order_by(
            TaskProcessingType.name
        ).all()
        quote_level = QuoteLevel.query.order_by(QuoteLevel.id).all()

        return render_template(
            "pages/task/new.html.j2",
            p=me,
            source_type=source_type,
            source_query_type=source_query_type,
            processing_type=processing_type,
            quote_level=quote_level,
            source=source,
            conn=conn,
            title="New Task",
            t=Task.query.filter_by(id=0).first(),
            file_type=file_type,
        )

    flash("Project does not exist.")
    return redirect(url_for("project_bp.all_projects"))


@task_edit_bp.route("/project/<project_id>/task/new", methods=["POST"])
@login_required
def task_new(project_id: int) -> Union[str, Response]:
    """Create a new task."""
    cache.clear()
    # create tasks
    form = request.form

    me = Task(
        name=form.get("name", "undefined").strip(),
        project_id=project_id,
        creator_id=current_user.id,
        updater_id=current_user.id,
        max_retries=form.get("task-retry", 0, type=int),
        order=form.get("task-rank", 0, type=int),
        source_type_id=form.get("sourceType", None, type=int),
        source_database_id=form.get("task-source-database", None, type=int),
        source_query_include_header=form.get(
            "task_include_query_headers", None, type=int
        ),
        source_smb_id=form.get("task-source-smb", None, type=int),
        source_smb_file=form.get("sourceSmbFile", None, type=str),
        source_smb_ignore_delimiter=form.get("task_smb_ignore_delimiter", 0, type=int),
        source_smb_delimiter=form.get("sourceSmbDelimiter", None, type=str),
        source_sftp_id=form.get("task-source-sftp", None, type=int),
        source_sftp_file=form.get("sourceSftpFile", None, type=str),
        source_sftp_ignore_delimiter=form.get(
            "task_sftp_ignore_delimiter", None, type=int
        ),
        enable_source_cache=form.get("task_enable_source_cache", None, type=int),
        source_require_sql_output=form.get("task_require_sql_output", None, type=int),
        source_sftp_delimiter=form.get("sourceSftpDelimiter", None, type=str),
        source_ftp_id=form.get("task-source-ftp", None, type=int),
        source_ftp_file=form.get("sourceFtpFile", None, type=str),
        source_ftp_ignore_delimiter=form.get(
            "task_ftp_ignore_delimiter", None, type=int
        ),
        source_ftp_delimiter=form.get("sourceFtpDelimiter", None, type=str),
        source_ssh_id=form.get("task-source-ssh", None, type=int),
        source_query_type_id=form.get("sourceQueryType", None, type=int),
        source_git=form.get("sourceGit", None, type=str),
        source_devops=form.get("sourceDevops", None, type=str),
        query_smb_file=form.get("sourceQuerySmbFile", None, type=str),
        query_smb_id=form.get("task-query-smb", None, type=int),
        query_sftp_file=form.get("sourceQuerySftpFile", None, type=str),
        query_sftp_id=form.get("task-query-sftp", None, type=int),
        query_ftp_file=form.get("sourceQueryFtpFile", None, type=str),
        query_ftp_id=form.get("task-query-ftp", None, type=int),
        source_url=form.get("sourceURL", None, type=str),
        source_code=form.get("sourceCode", None, type=str),
        processing_type_id=form.get("processingType", None, type=int),
        processing_smb_file=form.get("processingSmbFile", None, type=str),
        processing_smb_id=form.get("task-processing-smb", None, type=int),
        processing_sftp_file=form.get("processingSftpFile", None, type=str),
        processing_sftp_id=form.get("task-processing-sftp", None, type=int),
        processing_ftp_file=form.get("processingFtpFile", None, type=str),
        processing_ftp_id=form.get("task-processing-ftp", None, type=int),
        processing_git=form.get("processingGit", None, type=str),
        processing_devops=form.get("processingDevops", None, type=str),
        processing_url=form.get("processingUrl", None, type=str),
        processing_code=form.get("processingCode", None, type=str),
        processing_command=form.get("processingCommand", None, type=str),
        destination_quote_level_id=form.get("quoteLevel", 3, type=int),
        destination_file_type_id=form.get("fileType", None, type=int),
        destination_file_name=form.get(
            "destinationFileName", form.get("name", "undefined", type=str), type=str
        ),
        destination_create_zip=form.get("task_create_zip", None, type=int),
        destination_zip_name=form.get(
            "destinationZipName", form.get("name", "undefined", type=str), type=str
        ),
        destination_file_delimiter=form.get("fileDelimiter", None, type=str),
        destination_file_line_terminator=form.get("fileTerminator", None, type=str),
        destination_ignore_delimiter=form.get(
            "task_ignore_file_delimiter", None, type=int
        ),
        file_gpg=form.get("task_file_gpg", 0, type=int),
        file_gpg_id=form.get("task-file-gpg", None, type=int),
        destination_sftp=form.get("task_save_sftp", 0, type=int),
        destination_sftp_id=form.get("task-destination-sftp", None, type=int),
        destination_sftp_overwrite=form.get("task_overwrite_sftp", None, type=int),
        destination_sftp_dont_send_empty_file=form.get(
            "task_sftp_dont_send_empty", 0, type=int
        ),
        destination_ftp=form.get("task_save_ftp", 0, type=int),
        destination_ftp_id=form.get("task-destination-ftp", None, type=int),
        destination_ftp_overwrite=form.get("task_overwrite_ftp", None, type=int),
        destination_ftp_dont_send_empty_file=form.get(
            "task_ftp_dont_send_empty", 0, type=int
        ),
        destination_smb=form.get("task_save_smb", 0, type=int),
        destination_smb_id=form.get("task-destination-smb", None, type=int),
        destination_smb_overwrite=form.get("task_overwrite_smb", None, type=int),
        destination_smb_dont_send_empty_file=form.get(
            "task_smb_dont_send_empty", 0, type=int
        ),
        email_completion=form.get("task_send_completion_email", 0, type=int),
        email_completion_recipients=form.get("completionEmailRecip", "", type=str),
        email_completion_message=form.get("completion_email_msg", "", type=str),
        email_completion_subject=form.get("completionEmailSubject", "", type=str),
        email_completion_log=form.get("task_send_completion_email_log", 0, type=int),
        email_completion_file=form.get("task_send_output", 0, type=int),
        email_completion_dont_send_empty_file=form.get(
            "task_dont_send_empty", 0, type=int
        ),
        email_completion_file_embed=form.get("task_embed_output", 0, type=int),
        email_error=form.get("task_send_error_email", 0, type=int),
        email_error_recipients=form.get("errorEmailRecip", "", type=str),
        email_error_message=form.get("errorEmailMsg", "", type=str),
        email_error_subject=form.get("errorEmailSubject", "", type=str),
        enabled=form.get("task-ooff", 0, type=int),
    )

    db.session.add(me)
    db.session.commit()

    # add params
    for param in list(
        zip(
            form.getlist("param-key"),
            form.getlist("param-value"),
            form.getlist("param-sensitive"),
        )
    ):
        if param[0]:
            db.session.add(
                TaskParam(
                    task_id=me.id,
                    key=param[0],
                    value=em_encrypt(param[1], app.config["PASS_KEY"]),
                    sensitive=int(param[2] or 0),
                )
            )

    db.session.commit()

    log = TaskLog(
        task_id=me.id,
        status_id=7,
        message=(current_user.full_name or "none") + ": Task created.",
    )
    db.session.add(log)
    db.session.commit()

    if me.enabled == 1:
        submit_executor("enable_task", me.id)

    return redirect(url_for("task_bp.one_task", task_id=me.id))


@task_edit_bp.route("/task/<task_id>/edit", methods=["GET"])
@login_required
def task_edit_get(task_id: int) -> Union[Response, str]:
    """Task edit page."""
    # pylint: disable=too-many-locals
    me = Task.query.filter_by(id=task_id).first()

    if me:
        source_type = TaskSourceType.query.order_by(TaskSourceType.name).all()
        processing_type = TaskProcessingType.query.order_by(
            TaskProcessingType.name
        ).all()
        source_query_type = TaskSourceQueryType.query.order_by(
            TaskSourceQueryType.name
        ).all()

        source = ConnectionDatabase.query.order_by(ConnectionDatabase.name).all()

        conn = Connection.query.order_by(Connection.name).all()

        file_type = TaskDestinationFileType.query.order_by(
            TaskDestinationFileType.id
        ).all()
        sftp_dest = (
            ConnectionSftp.query.filter_by(
                connection_id=me.destination_sftp_conn.connection_id
            ).all()
            if me.destination_sftp_id
            else ""
        )
        ftp_dest = (
            ConnectionFtp.query.filter_by(
                connection_id=me.destination_ftp_conn.connection_id
            ).all()
            if me.destination_ftp_id
            else ""
        )
        smb_dest = (
            ConnectionSmb.query.filter_by(
                connection_id=me.destination_smb_conn.connection_id
            ).all()
            if me.destination_smb_id
            else ""
        )
        gpg_file = (
            (
                ConnectionGpg.query.filter_by(
                    connection_id=me.file_gpg_conn.connection_id
                ).all()
            )
            if me.file_gpg_conn
            else ""
        )
        sftp_source = (
            ConnectionSftp.query.filter_by(
                connection_id=me.source_sftp_conn.connection_id
            ).all()
            if me.source_sftp_id
            else ""
        )
        sftp_query = (
            ConnectionSftp.query.filter_by(
                connection_id=me.query_sftp_conn.connection_id
            ).all()
            if me.query_sftp_id
            else ""
        )
        ssh_source = (
            ConnectionSsh.query.filter_by(
                connection_id=me.source_ssh_conn.connection_id
            ).all()
            if me.source_ssh_id
            else ""
        )
        ftp_source = (
            ConnectionFtp.query.filter_by(
                connection_id=me.source_ftp_conn.connection_id
            ).all()
            if me.source_ftp_id
            else ""
        )
        ftp_query = (
            ConnectionFtp.query.filter_by(
                connection_id=me.query_ftp_conn.connection_id
            ).all()
            if me.query_ftp_id
            else ""
        )
        smb_source = (
            ConnectionSmb.query.filter_by(
                connection_id=me.source_smb_conn.connection_id
            ).all()
            if me.source_smb_id
            else ""
        )
        smb_query = (
            ConnectionSmb.query.filter_by(
                connection_id=me.query_smb_conn.connection_id
            ).all()
            if me.query_smb_id
            else ""
        )
        database_source = (
            ConnectionDatabase.query.filter_by(
                connection_id=me.source_database_conn.connection_id
            ).all()
            if me.source_database_id
            else ""
        )

        sftp_processing = (
            ConnectionSftp.query.filter_by(
                connection_id=me.processing_sftp_conn.connection_id
            ).all()
            if me.processing_sftp_id
            else ""
        )
        ftp_processing = (
            ConnectionFtp.query.filter_by(
                connection_id=me.processing_ftp_conn.connection_id
            ).all()
            if me.processing_ftp_id
            else ""
        )
        smb_processing = (
            ConnectionSmb.query.filter_by(
                connection_id=me.processing_smb_conn.connection_id
            ).all()
            if me.processing_smb_id
            else ""
        )

        quote_level = QuoteLevel.query.order_by(QuoteLevel.id).all()

        return render_template(
            "pages/task/new.html.j2",
            t=me,
            title="Editing " + me.name,
            source_type=source_type,
            processing_type=processing_type,
            source_query_type=source_query_type,
            source=source,
            sftp_dest=sftp_dest,
            ftp_dest=ftp_dest,
            smb_dest=smb_dest,
            conn=conn,
            sftp_source=sftp_source,
            ftp_source=ftp_source,
            smb_source=smb_source,
            ssh_source=ssh_source,
            sftp_query=sftp_query,
            ftp_query=ftp_query,
            smb_query=smb_query,
            sftp_processing=sftp_processing,
            ftp_processing=ftp_processing,
            smb_processing=smb_processing,
            database_source=database_source,
            gpg_file=gpg_file,
            file_type=file_type,
            quote_level=quote_level,
            p=me.project,
        )

    flash("Task does not exist.")
    return redirect(url_for("task_bp.all_tasks"))


@task_edit_bp.route("/task/<task_id>/edit", methods=["POST"])
@login_required
def task_edit_post(task_id: int) -> Response:
    """Save task edits."""
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    form = request.form

    task = get_or_create(db.session, Task, id=task_id)

    me = Task.query.filter_by(id=task.id)

    # pylint: disable=R1735
    me.update(
        dict(  # noqa: C408
            name=form.get("name", "undefined").strip(),
            updater_id=current_user.id,
            max_retries=form.get("task-retry", 0, type=int),
            order=form.get("task-rank", 0, type=int),
            source_type_id=form.get("sourceType", None, type=int),
            source_database_id=form.get("task-source-database", None, type=int),
            source_query_include_header=form.get(
                "task_include_query_headers", None, type=int
            ),
            source_smb_id=form.get("task-source-smb", None, type=int),
            source_smb_file=form.get("sourceSmbFile", None, type=str),
            source_smb_ignore_delimiter=form.get(
                "task_smb_ignore_delimiter", 0, type=int
            ),
            source_smb_delimiter=form.get("sourceSmbDelimiter", None, type=str),
            source_sftp_id=form.get("task-source-sftp", None, type=int),
            source_sftp_file=form.get("sourceSftpFile", None, type=str),
            source_sftp_ignore_delimiter=form.get(
                "task_sftp_ignore_delimiter", None, type=int
            ),
            source_sftp_delimiter=form.get("sourceSftpDelimiter", None, type=str),
            source_ftp_id=form.get("task-source-ftp", None, type=int),
            source_ftp_file=form.get("sourceFtpFile", None, type=str),
            source_ftp_ignore_delimiter=form.get(
                "task_ftp_ignore_delimiter", None, type=int
            ),
            enable_source_cache=form.get("task_enable_source_cache", None, type=int),
            source_require_sql_output=form.get(
                "task_require_sql_output", None, type=int
            ),
            source_ftp_delimiter=form.get("sourceFtpDelimiter", None, type=str),
            source_ssh_id=form.get("task-source-ssh", None, type=int),
            source_query_type_id=form.get("sourceQueryType", None, type=int),
            source_git=form.get("sourceGit", None, type=str),
            source_devops=form.get("sourceDevops", None, type=str),
            query_smb_file=form.get("sourceQuerySmbFile", None, type=str),
            query_smb_id=form.get("task-query-smb", None, type=int),
            query_sftp_file=form.get("sourceQuerySftpFile", None, type=str),
            query_sftp_id=form.get("task-query-sftp", None, type=int),
            query_ftp_file=form.get("sourceQueryFtpFile", None, type=str),
            query_ftp_id=form.get("task-query-ftp", None, type=int),
            source_url=form.get("sourceURL", None, type=str),
            source_code=form.get("sourceCode", None, type=str),
            processing_type_id=form.get("processingType", None, type=int),
            processing_smb_file=form.get("processingSmbFile", None, type=str),
            processing_smb_id=form.get("task-processing-smb", None, type=int),
            processing_sftp_file=form.get("processingSftpFile", None, type=str),
            processing_sftp_id=form.get("task-processing-sftp", None, type=int),
            processing_ftp_file=form.get("processingFtpFile", None, type=str),
            processing_ftp_id=form.get("task-processing-ftp", None, type=int),
            processing_git=form.get("processingGit", None, type=str),
            processing_devops=form.get("processingDevops", None, type=str),
            processing_url=form.get("processingUrl", None, type=str),
            processing_code=form.get("processingCode", None, type=str),
            processing_command=form.get("processingCommand", None, type=str),
            destination_quote_level_id=form.get("quoteLevel", 3, type=int),
            destination_file_type_id=form.get("fileType", None, type=int),
            destination_file_name=form.get(
                "destinationFileName", form.get("name", "undefined", type=str), type=str
            ),
            destination_create_zip=form.get("task_create_zip", None, type=int),
            destination_zip_name=form.get(
                "destinationZipName", form.get("name", "undefined", type=str), type=str
            ),
            destination_file_delimiter=form.get("fileDelimiter", None, type=str),
            destination_file_line_terminator=form.get("fileTerminator", None, type=str),
            destination_ignore_delimiter=form.get(
                "task_ignore_file_delimiter", None, type=int
            ),
            file_gpg=form.get("task_file_gpg", 0, type=int),
            file_gpg_id=form.get("task-file-gpg", None, type=int),
            destination_sftp=form.get("task_save_sftp", 0, type=int),
            destination_sftp_id=form.get("task-destination-sftp", None, type=int),
            destination_sftp_overwrite=form.get("task_overwrite_sftp", None, type=int),
            destination_sftp_dont_send_empty_file=form.get(
                "task_sftp_dont_send_empty", 0, type=int
            ),
            destination_ftp=form.get("task_save_ftp", 0, type=int),
            destination_ftp_id=form.get("task-destination-ftp", None, type=int),
            destination_ftp_overwrite=form.get("task_overwrite_ftp", None, type=int),
            destination_ftp_dont_send_empty_file=form.get(
                "task_ftp_dont_send_empty", 0, type=int
            ),
            destination_smb=form.get("task_save_smb", 0, type=int),
            destination_smb_id=form.get("task-destination-smb", None, type=int),
            destination_smb_overwrite=form.get("task_overwrite_smb", None, type=int),
            destination_smb_dont_send_empty_file=form.get(
                "task_smb_dont_send_empty", 0, type=int
            ),
            email_completion=form.get("task_send_completion_email", 0, type=int),
            email_completion_recipients=form.get("completionEmailRecip", "", type=str),
            email_completion_message=form.get("completion_email_msg", "", type=str),
            email_completion_subject=form.get("completionEmailSubject", "", type=str),
            email_completion_log=form.get(
                "task_send_completion_email_log", 0, type=int
            ),
            email_completion_file=form.get("task_send_output", 0, type=int),
            email_completion_dont_send_empty_file=form.get(
                "task_dont_send_empty", 0, type=int
            ),
            email_completion_file_embed=form.get("task_embed_output", 0, type=int),
            email_error=form.get("task_send_error_email", 0, type=int),
            email_error_recipients=form.get("errorEmailRecip", "", type=str),
            email_error_message=form.get("errorEmailMsg", "", type=str),
            email_error_subject=form.get("errorEmailSubject", "", type=str),
            enabled=form.get("task-ooff", 0, type=int),
        )
    )

    db.session.commit()

    # update params 1. remove old params
    TaskParam.query.filter_by(task_id=task_id).delete()
    db.session.commit()

    # update params 2. add new params
    for param in list(
        zip(
            form.getlist("param-key"),
            form.getlist("param-value"),
            form.getlist("param-sensitive"),
        )
    ):
        if param[0]:
            db.session.add(
                TaskParam(
                    task_id=task_id,
                    key=param[0],
                    value=em_encrypt(param[1], app.config["PASS_KEY"]),
                    sensitive=int(param[2] or 0),
                )
            )

    db.session.commit()

    me = me.first()

    log = TaskLog(
        task_id=task_id,
        status_id=7,
        message=(current_user.full_name or "none") + ": Task edited.",
    )
    db.session.add(log)
    db.session.commit()

    if me.enabled == 1:
        log = TaskLog(
            task_id=task_id,
            status_id=7,
            message=(current_user.full_name or "none") + ": Task enabled.",
        )
        db.session.add(log)
        db.session.commit()

        submit_executor("enable_task", task_id)

    else:
        submit_executor("disable_task", task_id)

    return redirect(url_for("task_bp.one_task", task_id=task_id))
