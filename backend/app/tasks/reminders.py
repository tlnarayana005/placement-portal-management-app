from datetime import datetime, timedelta

from app import create_app
from app.models import Application, PlacementDrive, User
from app.services.email_service import send_email
from app.tasks.celery_app import celery_app


def _now_utc_naive():
    # This MVP uses naive datetimes stored in SQLite; keep comparisons consistent.
    return datetime.utcnow()


def build_deadline_map(days_ahead: int):
    now = _now_utc_naive()
    upper = now + timedelta(days=days_ahead)

    drives = (
        PlacementDrive.query.filter(PlacementDrive.status == "approved")
        .filter(PlacementDrive.application_deadline >= now)
        .filter(PlacementDrive.application_deadline <= upper)
        .all()
    )

    students = (
        User.query.filter_by(role="student")
        .filter(User.is_active.is_(True))
        .filter(User.is_blacklisted.is_(False))
        .all()
    )
    student_profile_map = {u.id: u.student_profile for u in students if u.student_profile}

    applied_map = {}
    for d in drives:
        apps = Application.query.filter_by(drive_id=d.id).all()
        applied_map[d.id] = {a.student_id for a in apps}

    notifications = {}
    for d in drives:
        for student_user in students:
            sp = student_profile_map.get(student_user.id)
            if not sp:
                continue

            if sp.branch != d.eligibility_branch:
                continue
            if float(sp.cgpa) < float(d.eligibility_cgpa_min):
                continue
            if int(sp.year_of_study) < int(d.eligibility_year_min):
                continue

            if student_user.id in applied_map.get(d.id, set()):
                continue

            notifications.setdefault(student_user.id, []).append(
                {
                    "job_title": d.job_title,
                    "company_id": d.company_id,
                    "deadline": d.application_deadline.strftime("%Y-%m-%d %H:%M"),
                }
            )

    return notifications


@celery_app.task(name="app.tasks.reminders.daily_reminders")
def daily_reminders(days_ahead: int = 7):
    app = create_app()
    with app.app_context():
        notifications = build_deadline_map(days_ahead)
        if not notifications:
            return {"sent": 0}

        sent = 0
        for student_id, drives in notifications.items():
            user = User.query.filter_by(id=student_id, role="student").first()
            if not user or not user.email or not user.student_profile:
                continue

            subject = "Upcoming placement drive deadlines"
            html_body = (
                f"<p>Hi {user.student_profile.full_name},</p>"
                f"<p>Upcoming placement drive deadlines within the next {days_ahead} days:</p>"
                "<ul>"
                + "".join(
                    f"<li><strong>{d['job_title']}</strong> - Deadline: {d['deadline']}</li>"
                    for d in drives
                )
                + "</ul>"
                "<p>Log in to the portal to apply before the deadline.</p>"
            )

            res = send_email(user.email, subject, html_body)
            if res.get("sent"):
                sent += 1

        return {"sent": sent}

