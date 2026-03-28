import csv
import os
from datetime import datetime

from app import create_app
from app.models import Application, Notification, PlacementDrive, User
from app.services.email_service import send_email_with_file_attachment
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.export_csv.export_student_applications_csv")
def export_student_applications_csv(student_id: int):
    app = create_app()
    with app.app_context():
        student = User.query.filter_by(id=student_id, role="student").first()
        if not student:
            return {"error": "student not found"}

        applications = Application.query.filter_by(student_id=student_id).all()

        base_dir = os.path.dirname(os.path.dirname(__file__))  # backend/app -> backend
        exports_dir = os.path.join(base_dir, "exports")
        os.makedirs(exports_dir, exist_ok=True)

        # Using Celery task id ensures unique filenames.
        task_id = export_student_applications_csv.request.id or "job"
        csv_filename = f"export_{student_id}_{task_id}.csv"
        csv_path = os.path.join(exports_dir, csv_filename)

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Student ID",
                    "Company Name",
                    "Drive Title",
                    "Application Status",
                    "Application Date",
                    "Updated At",
                ]
            )

            for a in applications:
                drive = PlacementDrive.query.filter_by(id=a.drive_id).first()
                company_user = User.query.filter_by(id=drive.company_id, role="company").first() if drive else None
                company_name = company_user.company_profile.company_name if company_user and company_user.company_profile else None

                writer.writerow(
                    [
                        student_id,
                        company_name,
                        drive.job_title if drive else None,
                        a.status,
                        a.application_date.isoformat() if a.application_date else None,
                        a.updated_at.isoformat() if a.updated_at else None,
                    ]
                )

        # Notify student via email (optional)
        if student.email:
            subject = "Your placement applications CSV export is ready"
            html_body = (
                "<p>Your CSV export has been generated successfully.</p>"
                "<p>You can also download it from the portal export section.</p>"
            )
            send_email_with_file_attachment(
                student.email, subject, html_body, file_path=csv_path
            )

        # Also write an in-app notification for the student.
        notif = Notification(
            user_id=student_id,
            message=f"Your CSV export is ready. Task ID: {task_id}",
        )
        # Best-effort: if Notification table exists, persist it.
        try:
            from app.extensions import db as _db  # local import to avoid cycles

            _db.session.add(notif)
            _db.session.commit()
        except Exception:
            pass

        return {"student_id": student_id, "csv_path": csv_path, "task_id": task_id}

