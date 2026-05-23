"""Notification backends for cronwrap job failures."""

import smtplib
import logging
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List

logger = logging.getLogger(__name__)


@dataclass
class NotifierConfig:
    """Configuration for failure notifications."""
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: bool = False
    from_address: str = "cronwrap@localhost"
    to_addresses: List[str] = field(default_factory=list)
    subject_prefix: str = "[cronwrap] FAILED"


def build_email_body(job_name: str, command: str, returncode: int,
                    stdout: str, stderr: str, attempts: int) -> str:
    """Build a human-readable email body for a failed job."""
    lines = [
        f"Job '{job_name}' failed after {attempts} attempt(s).",
        "",
        f"Command : {command}",
        f"Exit code: {returncode}",
        "",
    ]
    if stdout.strip():
        lines += ["--- stdout ---", stdout.strip(), ""]
    if stderr.strip():
        lines += ["--- stderr ---", stderr.strip(), ""]
    return "\n".join(lines)


def send_failure_email(
    config: NotifierConfig,
    job_name: str,
    command: str,
    returncode: int,
    stdout: str,
    stderr: str,
    attempts: int,
) -> bool:
    """Send a failure notification email.  Returns True on success."""
    if not config.to_addresses:
        logger.warning("No to_addresses configured; skipping notification.")
        return False

    subject = f"{config.subject_prefix}: {job_name}"
    body = build_email_body(job_name, command, returncode, stdout, stderr, attempts)

    msg = MIMEMultipart()
    msg["From"] = config.from_address
    msg["To"] = ", ".join(config.to_addresses)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        if config.use_tls:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port)

        if config.smtp_user and config.smtp_password:
            server.login(config.smtp_user, config.smtp_password)

        server.sendmail(config.from_address, config.to_addresses, msg.as_string())
        server.quit()
        logger.info("Failure notification sent for job '%s'.", job_name)
        return True
    except smtplib.SMTPException as exc:
        logger.error("Failed to send notification for job '%s': %s", job_name, exc)
        return False
