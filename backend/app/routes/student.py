from datetime import datetime, timezone
import json

import os

from flask import Blueprint, current_app, jsonify, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Application, Notification, PlacementDrive, StudentProfile, User
from ..security import role_required
from ..tasks.celery_app import celery_app

student_bp = Blueprint("student", __name__, url_prefix="/api/student")


def _current_student_id():
    return int(get_jwt_identity())


@student_bp.get("/me")
@jwt_required()
@role_required("student")
def student_me():
    student_id = _current_student_id()
    user = User.query.filter_by(id=student_id, role="student").first_or_404()
    sp = user.student_profile
    if user.is_blacklisted or not user.is_active:
        return jsonify({"error": "student is not active"}), 403
    return jsonify(
        {
            "id": user.id,
            "email": user.email,
            "full_name": sp.full_name,
            "phone": sp.phone,
            "year_of_study": sp.year_of_study,
            "branch": sp.branch,
            "cgpa": sp.cgpa,
            "resume_path": sp.resume_path,
        }
    )


@student_bp.get("/drives")
@jwt_required()
@role_required("student")
def student_approved_drives():
    student_id = _current_student_id()
    user = User.query.filter_by(id=student_id, role="student").first_or_404()
    if user.is_blacklisted or not user.is_active:
        return jsonify({"error": "student is not active"}), 403
    sp = user.student_profile

    # Cache the raw approved drive list (shared across students).
    # Then we do eligibility filtering in Python per student.
    cache_key = "approved_drives_v1"
    drives_data = None
    try:
        cached = current_app.redis_client.get(cache_key)
        if cached:
            drives_data = json.loads(cached)
    except Exception:
        drives_data = None

    if drives_data is None:
        drives = (
            PlacementDrive.query.filter_by(status="approved")
            .order_by(PlacementDrive.application_deadline.asc())
            .all()
        )
        drives_data = [
            {
                "id": d.id,
                "company_id": d.company_id,
                "job_title": d.job_title,
                "job_description": d.job_description,
                "application_deadline": d.application_deadline.isoformat(),
                "eligibility_branch": d.eligibility_branch,
                "eligibility_cgpa_min": d.eligibility_cgpa_min,
                "eligibility_year_min": d.eligibility_year_min,
            }
            for d in drives
        ]

        # Cache TTL: 60 seconds (tune as needed).
        try:
            current_app.redis_client.setex(cache_key, 60, json.dumps(drives_data))
        except Exception:
            pass

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    eligible = []
    for d in drives_data:
        deadline = datetime.fromisoformat(d["application_deadline"]).replace(tzinfo=None)
        if deadline < now:
            continue
        if d["eligibility_branch"] != sp.branch:
            continue
        if float(sp.cgpa) < float(d["eligibility_cgpa_min"]):
            continue
        if int(sp.year_of_study) < int(d["eligibility_year_min"]):
            continue
        eligible.append(
            {
                "id": d["id"],
                "company_id": d["company_id"],
                "job_title": d["job_title"],
                "job_description": d["job_description"],
                "application_deadline": d["application_deadline"],
            }
        )

    return jsonify({"items": eligible})


@student_bp.post("/drives/<int:drive_id>/apply")
@jwt_required()
@role_required("student")
def student_apply(drive_id: int):
    student_id = _current_student_id()
    user = User.query.filter_by(id=student_id, role="student").first_or_404()
    if user.is_blacklisted or not user.is_active:
        return jsonify({"error": "student is not active"}), 403
    sp: StudentProfile = user.student_profile

    drive = PlacementDrive.query.filter_by(id=drive_id, status="approved").first()
    if not drive:
        return jsonify({"error": "drive not available"}), 404

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if drive.application_deadline < now:
        return jsonify({"error": "application deadline has passed"}), 400

    # Prevent multiple applications (UniqueConstraint + explicit check for friendly errors)
    existing = Application.query.filter_by(student_id=student_id, drive_id=drive_id).first()
    if existing:
        return jsonify({"error": "already applied to this drive"}), 409

    # Eligibility validation
    if drive.eligibility_branch != sp.branch:
        return jsonify({"error": "branch not eligible"}), 403
    if sp.cgpa < drive.eligibility_cgpa_min:
        return jsonify({"error": "cgpa not eligible"}), 403
    if sp.year_of_study < drive.eligibility_year_min:
        return jsonify({"error": "year not eligible"}), 403

    app_row = Application(student_id=student_id, drive_id=drive_id, status="applied")
    db.session.add(app_row)
    db.session.commit()

    return jsonify({"message": "applied", "application_id": app_row.id}), 201


@student_bp.get("/applications")
@jwt_required()
@role_required("student")
def student_applications():
    student_id = _current_student_id()
    items = (
        Application.query.filter_by(student_id=student_id)
        .order_by(Application.application_date.desc())
        .limit(200)
        .all()
    )

    drives = {d.id: d for d in PlacementDrive.query.all()}
    out = []
    for a in items:
        d = drives.get(a.drive_id)
        out.append(
            {
                "application_id": a.id,
                "drive_id": a.drive_id,
                "job_title": d.job_title if d else None,
                "status": a.status,
                "application_date": a.application_date.isoformat(),
                "final_selection_status": a.final_selection_status,
                "interview_scheduled_at": a.interview_scheduled_at.isoformat()
                if a.interview_scheduled_at
                else None,
            }
        )
    return jsonify({"items": out})


@student_bp.post("/export/applications")
@jwt_required()
@role_required("student")
def student_export_applications():
    student_id = _current_student_id()
    user = User.query.filter_by(id=student_id, role="student").first_or_404()
    if user.is_blacklisted or not user.is_active:
        return jsonify({"error": "student is not active"}), 403

    task = celery_app.send_task(
        "app.tasks.export_csv.export_student_applications_csv", args=[student_id]
    )
    return jsonify({"message": "export job started", "task_id": task.id}), 202


@student_bp.get("/export/applications/<task_id>/status")
@jwt_required()
@role_required("student")
def student_export_status(task_id: str):
    res = celery_app.AsyncResult(task_id)
    payload = {"task_id": task_id, "state": res.state}
    if res.state == "SUCCESS":
        payload["result"] = res.result
    elif res.state == "FAILURE":
        payload["error"] = str(res.result)
    return jsonify(payload)


@student_bp.get("/export/applications/<task_id>/download")
@jwt_required()
@role_required("student")
def student_export_download(task_id: str):
    res = celery_app.AsyncResult(task_id)
    if res.state != "SUCCESS":
        return jsonify({"error": "export not ready"}), 400

    result = res.result or {}
    csv_path = result.get("csv_path")
    if not csv_path or not os.path.exists(csv_path):
        return jsonify({"error": "export file not found"}), 404

    download_name = os.path.basename(csv_path)
    return send_file(csv_path, as_attachment=True, download_name=download_name)


@student_bp.get("/notifications")
@jwt_required()
@role_required("student")
def student_notifications():
    student_id = _current_student_id()
    items = (
        Notification.query.filter_by(user_id=student_id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify(
        {
            "items": [
                {
                    "id": n.id,
                    "message": n.message,
                    "created_at": n.created_at.isoformat(),
                    "read_at": n.read_at.isoformat() if n.read_at else None,
                }
                for n in items
            ]
        }
    )

