"""SMTP connection manager."""

import email
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional, Tuple

from flask import current_app as app

from runner import db
from runner.model import Task, TaskLog


class Smtp:
    """SMB Connection Handler Class.

    Used to send emails. pass in recips, subject, message and any attachments
    """

    # pylint: disable=too-few-public-methods
    def __init__(
        self,
        task: Task,
        run_id: Optional[str],
        recipients: str,
        subject: str,
        message: str,
        short_message: str,
        attachments: List[str],
    ):
        """Set up class parameters."""
        self.task = task
        self.message = message
        self.short_message = short_message
        self.run_id = run_id
        self.attachments = attachments
        self.subject = subject
        self.ssmsto, self.mailto = self.__mailto(recipients)

        self.__send_mail()
        self.__send_ssms()

    def __mailto(self, recipients: str) -> Tuple[List[str], List[str]]:
        """Build mailto groups.

        Text messages are sent in a different group than
        emails in order to send a smaller sized message.
        """
        recip_list = [x.strip() for x in recipients.split(";") if x.strip()]

        phone = list(filter(lambda x: re.match(r"\d+@", x), recip_list))
        email_recip = list(set(recip_list) - set(phone))

        return phone, email_recip

    def __send_ssms(self) -> None:
        try:
            for phone in self.ssmsto:
                msg = email.message.Message()
                msg["From"] = app.config["SMTP_SENDER_EMAIL"]
                msg["To"] = phone
                msg.add_header("Content-Type", "text")
                msg.set_payload(self.short_message)

                mail_server = smtplib.SMTP(
                    app.config["SMTP_SERVER"], app.config["SMTP_PORT"], timeout=180
                )
                mail_server.ehlo()

                if app.config.get("SMTP_USE_TLS", False):
                    mail_server.starttls()
                    mail_server.ehlo()
                    mail_server.login(
                        app.config["SMTP_USERNAME"],
                        app.config.get("SMTP_PASSWORD", None),
                    )

                mail_server.sendmail(app.config["SMTP_SENDER_EMAIL"], phone, self.msg.as_string())
                mail_server.quit()

                log = TaskLog(
                    task_id=self.task.id,
                    job_id=self.run_id,
                    status_id=12,
                    message=f"Successfully sent sms to {phone}.",
                )
                db.session.add(log)
                db.session.commit()

        except BaseException as e:
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.run_id,
                status_id=12,
                error=1,
                message=f"Failed to send sms to {phone}.\n{e}",
            )
            db.session.add(log)
            db.session.commit()

            raise

    def __send_mail(self) -> None:
        try:
            self.msg = MIMEMultipart()
            self.msg["From"] = email.utils.formataddr(  # type: ignore[attr-defined]
                (
                    email.header.Header(app.config["SMTP_SENDER_NAME"], "utf-8").encode("utf-8"),
                    app.config["SMTP_SENDER_EMAIL"],
                )
            )

            # subject only needed for html mail
            self.msg["Subject"] = app.config["SMTP_SUBJECT_PREFIX"] + self.subject
            self.msg["To"] = ",".join(self.mailto)

            html = self.message
            self.msg.attach(MIMEText(html, "html"))

            for attachment in self.attachments:
                obj = email.mime.base.MIMEBase("application", "octet-stream")

                with open(str(attachment), "rb") as my_attachment:
                    obj.set_payload(my_attachment.read())

                email.encoders.encode_base64(obj)  # type: ignore[attr-defined]
                obj.add_header(
                    "Content-Disposition",
                    "attachment; filename= " + Path(str(attachment)).name,
                )

                self.msg.attach(obj)

            mail_server = smtplib.SMTP(
                app.config["SMTP_SERVER"], app.config["SMTP_PORT"], timeout=180
            )

            mail_server.ehlo()
            if app.config.get("SMTP_USE_TLS", False):
                mail_server.starttls()
                mail_server.ehlo()
                mail_server.login(
                    app.config["SMTP_USERNAME"],
                    app.config.get("SMTP_PASSWORD", None),
                )
            mail_server.sendmail(
                app.config["SMTP_SENDER_EMAIL"], self.mailto, self.msg.as_string()
            )
            mail_server.quit()

            log = TaskLog(
                task_id=self.task.id,
                job_id=self.run_id,
                status_id=12,
                message="Successfully sent email.",
            )
            db.session.add(log)
            db.session.commit()

        # don't use the normal error raise here or we may end up in an error loop
        # as the error class uses this function.
        except BaseException as e:
            log = TaskLog(
                task_id=self.task.id,
                job_id=self.run_id,
                status_id=12,
                error=1,
                message=f"Failed to send email.\n{e}",
            )
            db.session.add(log)
            db.session.commit()

            raise
