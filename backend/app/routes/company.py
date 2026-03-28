from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Application, CompanyProfile, PlacementDrive, User
from ..security import role_required

company_bp = Blueprint("company", __name__, url_prefix="/api/company")


def _current_company_id():
    return int(get_jwt_identity())


@company_bp.get("/me")
@jwt_required()
@role_required("company")
def company_me():
    company_id = _current_company_id()
    user = User.query.filter_by(id=company_id, role="company").first_or_404()
    cp = user.company_profile
    return jsonify(
        {
            "id": user.id,
            "email": user.email,
            "company_name": cp.company_name,
            "hr_contact": cp.hr_contact,
            "website": cp.website,
            "approval_status": cp.approval_status,
            "deactivated": cp.deactivated,
        }
    )


@company_bp.post("/drives")
@jwt_required()
@role_required("company")
def company_create_drive():
    company_id = _current_company_id()
    user = User.query.filter_by(id=company_id, role="company").first_or_404()
    cp = user.company_profile

    if cp.deactivated or user.is_blacklisted or not user.is_active:
        return jsonify({"error": "company is not active"}), 403
    if cp.approval_status != "approved":
        return jsonify({"error": "company must be approved by admin"}), 403

    body = request.get_json(force=True)
    application_deadline = body.get("application_deadline")
    try:
        application_deadline_dt = datetime.fromisoformat(application_deadline)
    except Exception:
        return jsonify({"error": "application_deadline must be ISO datetime"}), 400

    drive = PlacementDrive(
        company_id=company_id,
        job_title=(body.get("job_title") or "").strip(),
        job_description=body.get("job_description"),
        eligibility_branch=(body.get("eligibility_branch") or "").strip(),
        eligibility_cgpa_min=float(body.get("eligibility_cgpa_min")),
        eligibility_year_min=int(body.get("eligibility_year_min")),
        application_deadline=application_deadline_dt,
        status="pending",
    )
    if not drive.job_title or not drive.eligibility_branch:
        return jsonify({"error": "job_title and eligibility_branch are required"}), 400

    db.session.add(drive)
    db.session.commit()
    return jsonify({"message": "drive created (pending admin approval)", "drive_id": drive.id}), 201


@company_bp.get("/drives")
@jwt_required()
@role_required("company")
def company_drives():
    company_id = _current_company_id()
    drives = (
        PlacementDrive.query.filter_by(company_id=company_id)
        .order_by(PlacementDrive.created_at.desc())
        .all()
    )

    items = []
    for d in drives:
        applicant_count = Application.query.filter_by(drive_id=d.id).count()
        items.append(
            {
                "id": d.id,
                "job_title": d.job_title,
                "application_deadline": d.application_deadline.isoformat(),
                "status": d.status,
                "applicant_count": applicant_count,
            }
        )
    return jsonify({"items": items})


@company_bp.get("/drives/<int:drive_id>/applications")
@jwt_required()
@role_required("company")
def company_drive_applications(drive_id: int):
    company_id = _current_company_id()
    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=company_id).first_or_404()

    apps = (
        Application.query.filter_by(drive_id=drive.id)
        .order_by(Application.application_date.desc())
        .limit(500)
        .all()
    )

    # Student details from the unified user+student_profile tables
    from ..models import StudentProfile

    items = []
    for a in apps:
        student_user = User.query.filter_by(id=a.student_id, role="student").first()
        sp = student_user.student_profile if student_user else None
        items.append(
            {
                "application_id": a.id,
                "student_id": a.student_id,
                "application_date": a.application_date.isoformat(),
                "status": a.status,
                "final_selection_status": a.final_selection_status,
                "interview_scheduled_at": a.interview_scheduled_at.isoformat()
                if a.interview_scheduled_at
                else None,
                "student": {
                    "full_name": sp.full_name if sp else None,
                    "branch": sp.branch if sp else None,
                    "cgpa": sp.cgpa if sp else None,
                },
            }
        )

    return jsonify({"drive": {"id": drive.id, "job_title": drive.job_title, "status": drive.status}, "items": items})


@company_bp.post("/drives/<int:drive_id>/applications/<int:app_id>/status")
@jwt_required()
@role_required("company")
def company_update_application_status(drive_id: int, app_id: int):
    company_id = _current_company_id()
    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=company_id).first_or_404()

    a = Application.query.filter_by(id=app_id, drive_id=drive.id).first_or_404()
    body = request.get_json(force=True)

    status = (body.get("status") or "").strip().lower()
    allowed = {"shortlisted", "selected", "rejected", "applied"}
    if status not in allowed:
        return jsonify({"error": "invalid status"}), 400

    a.status = status
    if status in {"selected", "rejected"}:
        a.final_selection_status = status

    # Optional interview schedule
    interview_scheduled_at = body.get("interview_scheduled_at")
    if interview_scheduled_at:
        try:
            a.interview_scheduled_at = datetime.fromisoformat(interview_scheduled_at)
        except Exception:
            return jsonify({"error": "interview_scheduled_at must be ISO datetime"}), 400

    db.session.commit()
    return jsonify({"message": "application updated"})

