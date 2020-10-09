"""
    smpt connection manager

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

import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import logging
from em import app, db
from ..model.model import Task, TaskLog
from .error_print import full_stack


class Smtp:
    """
    used to send emails. pass in recips, subject, message and any attachments
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, task, recipients, subject, message, attachment, attachment_name):
        # pylint: disable=too-many-arguments
        self.task = task
        self.message = message
        self.attachment_name = attachment_name or None

        self.msg = MIMEMultipart()
        self.msg["From"] = email.utils.formataddr(
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
            self.attachment = attachment
            self.__attachment()
        else:
            self.attachment = None

        self.__send()

    def __message(self):

        html = self.message
        self.msg.attach(MIMEText(html, "html"))

    def __attachment(self):

        obj = email.mime.base.MIMEBase("application", "octet-stream")
        obj.set_payload((open(self.attachment, "rb")).read())
        email.encoders.encode_base64(obj)
        obj.add_header(
            "Content-Disposition",
            "attachment; filename= "
            + (self.attachment_name or Path(self.attachment).name),
        )

        self.msg.attach(obj)

    def __send(self):
        try:
            logging.info(
                "SMTP: Sending: Task: %s, with run: %s",
                str(self.task.id),
                str(self.task.last_run_job_id),
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
                job_id=self.task.last_run_job_id,
                status_id=12,
                message="Successfully sent email.",
            )
            db.session.add(log)
            db.session.commit()

        # pylint: disable=bare-except
        except:
            logging.error(
                "SMTP: Failed to Send: Task: %s, with run: %s\n%s",
                str(self.task.id),
                str(self.task.last_run_job_id),
                str(full_stack()),
            )
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.task.last_run_job_id,
                status_id=12,
                error=1,
                message="Failed to send email.\n" + str(full_stack()),
            )
            db.session.add(log)
            db.session.commit()
