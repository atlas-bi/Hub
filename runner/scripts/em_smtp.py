"""SMTP connection manager."""


import email
import logging
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from flask import current_app as app

from runner import db
from runner.model import Task, TaskLog

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from error_print import full_stack


class Smtp:
    """SMB Connection Handler Class.

    Used to send emails. pass in recips, subject, message and any attachments
    """

    # pylint: disable=too-few-public-methods
    def __init__(
        self,
        task: Task,
        recipients: str,
        subject: str,
        message: str,
        attachment: Optional[str],
        attachment_name: Optional[str],
        job_hash: str,
    ):
        """Set up class parameters.

        :param task: task object
        :param list recipients: list of email addresses to send email to
        :param str subject: email subject
        :param str message: formated email message
        :param str attachment: local file path to item that should be attached to email
        :param str attachment_name: name to give attached file
        """
        # pylint: disable=too-many-arguments
        self.task = task
        self.message = message
        self.job_hash = job_hash
        self.attachment_name = attachment_name or None

        self.msg = MIMEMultipart()
        self.msg["From"] = email.utils.formataddr(  # type: ignore[attr-defined]
            (
                email.header.Header(app.config["SMTP_SENDER_NAME"], "utf-8").encode(
                    "utf-8"
                ),
                app.config["SMTP_SENDER_EMAIL"],
            )
        )

        self.msg["To"] = recipients.replace(";", ",")
        self.msg["Subject"] = app.config["SMTP_SUBJECT_PREFIX"] + subject

        self.mailto = recipients.split(";")

        self.__message()

        if attachment is not None:
            self.attachment: Optional[str] = attachment
            self.__attachment()
        else:
            self.attachment = None

        self.__send()

    def __message(self) -> None:

        html = self.message
        self.msg.attach(MIMEText(html, "html"))

    def __attachment(self) -> None:

        obj = email.mime.base.MIMEBase("application", "octet-stream")

        with open(str(self.attachment), "rb") as my_attachment:
            obj.set_payload(my_attachment.read())

        email.encoders.encode_base64(obj)  # type: ignore[attr-defined]
        obj.add_header(
            "Content-Disposition",
            "attachment; filename= "
            + (self.attachment_name or Path(str(self.attachment)).name),
        )

        self.msg.attach(obj)

    def __send(self) -> None:
        try:
            logging.info(
                "SMTP: Sending: Task: %s, with run: %s",
                str(self.task.id),
                str(self.job_hash),
            )
            mail_server = smtplib.SMTP(
                app.config["SMTP_SERVER"], app.config["SMTP_PORT"], timeout=180
            )
            mail_server.ehlo()
            mail_server.sendmail(
                app.config["SMTP_SENDER_EMAIL"], self.mailto, self.msg.as_string()
            )
            mail_server.quit()

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=12,
                message="Successfully sent email.",
            )
            db.session.add(log)
            db.session.commit()

        # pylint: disable=broad-except
        except BaseException:
            logging.error(
                "SMTP: Failed to Send: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.job_hash),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.job_hash,
                status_id=12,
                error=1,
                message="Failed to send email.\n" + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
