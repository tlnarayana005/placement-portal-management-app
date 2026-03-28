import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from flask import current_app


def send_email(to_email: str, subject: str, html_body: str):
    """
    Sends an email via SMTP using Flask config.
    If SMTP credentials are missing, the function becomes a no-op (safe for local demos).
    """
    cfg = current_app.config
    email_user = cfg.get("EMAIL_USER", "")
    email_password = cfg.get("EMAIL_PASSWORD", "")
    if not email_user or not email_password:
        # Local/demo mode: avoid failing background jobs.
        return {"sent": False, "reason": "SMTP not configured"}

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg.get("EMAIL_FROM", email_user)
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    smtp_host = cfg.get("EMAIL_HOST")
    smtp_port = cfg.get("EMAIL_PORT", 587)

    server = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
    try:
        if cfg.get("EMAIL_USE_TLS", True):
            server.starttls()
        server.login(email_user, email_password)
        server.sendmail(msg["From"], [to_email], msg.as_string())
    finally:
        server.quit()

    return {"sent": True}


def send_email_with_pdf_attachment(
    to_email: str, subject: str, html_body: str, pdf_bytes: bytes, filename: str
):
    """
    Sends an email with a PDF attachment (MVP for monthly activity report).
    If SMTP credentials are missing, becomes a no-op.
    """
    cfg = current_app.config
    email_user = cfg.get("EMAIL_USER", "")
    email_password = cfg.get("EMAIL_PASSWORD", "")
    if not email_user or not email_password:
        return {"sent": False, "reason": "SMTP not configured"}

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = cfg.get("EMAIL_FROM", email_user)
    msg["To"] = to_email

    # HTML body
    msg_body = MIMEMultipart("alternative")
    msg_body.attach(MIMEText(html_body, "html"))
    msg.attach(msg_body)

    # PDF attachment
    pdf_part = MIMEBase("application", "pdf")
    pdf_part.set_payload(pdf_bytes)
    encoders.encode_base64(pdf_part)
    pdf_part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(pdf_part)

    smtp_host = cfg.get("EMAIL_HOST")
    smtp_port = cfg.get("EMAIL_PORT", 587)
    server = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
    try:
        if cfg.get("EMAIL_USE_TLS", True):
            server.starttls()
        server.login(email_user, email_password)
        server.sendmail(msg["From"], [to_email], msg.as_string())
    finally:
        server.quit()

    return {"sent": True}


def send_email_with_file_attachment(to_email: str, subject: str, html_body: str, file_path: str):
    """
    Generic helper for attaching a file (used for CSV exports).
    """
    cfg = current_app.config
    email_user = cfg.get("EMAIL_USER", "")
    email_password = cfg.get("EMAIL_PASSWORD", "")
    if not email_user or not email_password:
        return {"sent": False, "reason": "SMTP not configured"}

    from pathlib import Path

    file = Path(file_path)
    if not file.exists():
        return {"sent": False, "reason": "attachment file missing"}

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = cfg.get("EMAIL_FROM", email_user)
    msg["To"] = to_email

    msg_body = MIMEMultipart("alternative")
    msg_body.attach(MIMEText(html_body, "html"))
    msg.attach(msg_body)

    with open(file_path, "rb") as f:
        mime_part = MIMEBase("application", "octet-stream")
        mime_part.set_payload(f.read())
        encoders.encode_base64(mime_part)
        mime_part.add_header(
            "Content-Disposition", f'attachment; filename="{file.name}"'
        )
        msg.attach(mime_part)

    smtp_host = cfg.get("EMAIL_HOST")
    smtp_port = cfg.get("EMAIL_PORT", 587)
    server = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
    try:
        if cfg.get("EMAIL_USE_TLS", True):
            server.starttls()
        server.login(email_user, email_password)
        server.sendmail(msg["From"], [to_email], msg.as_string())
    finally:
        server.quit()

    return {"sent": True}

