from datetime import datetime

from app import create_app
from app.models import Application, PlacementDrive
from app.services.email_service import send_email_with_pdf_attachment
from app.services.report_service import render_pdf_from_template
from app.tasks.celery_app import celery_app


def _month_bounds_utc_naive():
    now = datetime.utcnow()
    # First day of current month
    current_month_start = datetime(now.year, now.month, 1)
    # First day of previous month
    if now.month == 1:
        prev_month_start = datetime(now.year - 1, 12, 1)
    else:
        prev_month_start = datetime(now.year, now.month - 1, 1)
    return prev_month_start, current_month_start


@celery_app.task(name="app.tasks.monthly_reports.monthly_admin_activity_report")
def monthly_admin_activity_report():
    app = create_app()
    with app.app_context():
        month_start, next_month_start = _month_bounds_utc_naive()
        month_label = month_start.strftime("%B %Y")

        drives_conducted = (
            PlacementDrive.query.filter(PlacementDrive.created_at >= month_start)
            .filter(PlacementDrive.created_at < next_month_start)
            .count()
        )

        apps_in_month_q = (
            Application.query.filter(Application.application_date >= month_start)
            .filter(Application.application_date < next_month_start)
        )
        students_applied = apps_in_month_q.count()

        students_selected_q = apps_in_month_q.filter(
            (Application.status == "selected")
            | (Application.final_selection_status == "selected")
        )
        students_selected = students_selected_q.count()

        pdf_bytes = render_pdf_from_template(
            "monthly_activity_report.html",
            {
                "month_label": month_label,
                "drives_conducted": drives_conducted,
                "students_applied": students_applied,
                "students_selected": students_selected,
                "generated_on": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            },
        )

        admin_email = app.config.get("ADMIN_EMAIL") or app.config.get("EMAIL_FROM")
        if not admin_email:
            return {"sent": False, "reason": "ADMIN_EMAIL not configured"}

        subject = f"Monthly Placement Activity Report - {month_label}"
        html_body = (
            f"<p>Hi Admin,</p><p>Please find attached the monthly placement activity report for <b>{month_label}</b>.</p>"
        )
        filename = f"placement_activity_{month_label.replace(' ', '_')}.pdf"

        res = send_email_with_pdf_attachment(
            admin_email, subject, html_body, pdf_bytes, filename=filename
        )
        return {"sent": res.get("sent", False)}

