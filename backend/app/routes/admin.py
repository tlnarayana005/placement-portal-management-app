from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import CompanyProfile, PlacementDrive, User
from ..security import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/dashboard/stats")
@jwt_required()
@role_required("admin")
def dashboard_stats():
    total_students = User.query.filter_by(role="student").count()
    total_companies = User.query.filter_by(role="company").count()
    total_drives = PlacementDrive.query.count()
    pending_companies = CompanyProfile.query.filter_by(approval_status="pending").count()

    return jsonify(
        {
            "total_students": total_students,
            "total_companies": total_companies,
            "total_drives": total_drives,
            "pending_companies": pending_companies,
        }
    )


@admin_bp.post("/companies/<int:company_id>/approve")
@jwt_required()
@role_required("admin")
def approve_company(company_id: int):
    user = User.query.filter_by(id=company_id, role="company").first_or_404()
    user.company_profile.approval_status = "approved"
    user.company_profile.deactivated = False
    db.session.commit()
    return jsonify({"message": "company approved"})


@admin_bp.post("/companies/<int:company_id>/reject")
@jwt_required()
@role_required("admin")
def reject_company(company_id: int):
    user = User.query.filter_by(id=company_id, role="company").first_or_404()
    user.company_profile.approval_status = "rejected"
    user.company_profile.deactivated = True
    user.is_active = False
    db.session.commit()
    return jsonify({"message": "company rejected"})


@admin_bp.post("/drives/<int:drive_id>/approve")
@jwt_required()
@role_required("admin")
def approve_drive(drive_id: int):
    drive = PlacementDrive.query.filter_by(id=drive_id).first_or_404()
    drive.status = "approved"
    db.session.commit()
    return jsonify({"message": "placement drive approved"})


@admin_bp.post("/drives/<int:drive_id>/reject")
@jwt_required()
@role_required("admin")
def reject_drive(drive_id: int):
    drive = PlacementDrive.query.filter_by(id=drive_id).first_or_404()
    drive.status = "rejected"
    db.session.commit()
    return jsonify({"message": "placement drive rejected"})


@admin_bp.post("/users/<int:user_id>/blacklist")
@jwt_required()
@role_required("admin")
def blacklist_user(user_id: int):
    user = User.query.filter_by(id=user_id).first_or_404()
    user.is_blacklisted = True
    user.is_active = False
    db.session.commit()
    return jsonify({"message": "user blacklisted"})


@admin_bp.post("/users/<int:user_id>/deactivate")
@jwt_required()
@role_required("admin")
def deactivate_user(user_id: int):
    user = User.query.filter_by(id=user_id).first_or_404()
    user.is_active = False
    if user.role == "company":
        user.company_profile.deactivated = True
    db.session.commit()
    return jsonify({"message": "user deactivated"})


@admin_bp.get("/search/companies")
@jwt_required()
@role_required("admin")
def search_companies():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"items": []})
    items = (
        User.query.filter_by(role="company")
        .join(CompanyProfile, CompanyProfile.user_id == User.id)
        .filter(CompanyProfile.company_name.ilike(f"%{q}%"))
        .limit(20)
        .all()
    )
    return jsonify(
        {
            "items": [
                {
                    "id": u.id,
                    "email": u.email,
                    "company_name": u.company_profile.company_name,
                    "approval_status": u.company_profile.approval_status,
                    "deactivated": u.company_profile.deactivated,
                }
                for u in items
            ]
        }
    )


@admin_bp.get("/search/students")
@jwt_required()
@role_required("admin")
def search_students():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"items": []})
    items = (
        User.query.filter_by(role="student")
        .join(User.student_profile)
        .filter(User.student_profile.full_name.ilike(f"%{q}%"))
        .limit(20)
        .all()
    )
    return jsonify(
        {
            "items": [
                {
                    "id": u.id,
                    "email": u.email,
                    "full_name": u.student_profile.full_name,
                    "year_of_study": u.student_profile.year_of_study,
                    "branch": u.student_profile.branch,
                    "cgpa": u.student_profile.cgpa,
                    "is_blacklisted": u.is_blacklisted,
                    "is_active": u.is_active,
                }
                for u in items
            ]
        }
    )


@admin_bp.get("/applications")
@jwt_required()
@role_required("admin")
def list_applications():
    # Optional filters
    drive_id = request.args.get("drive_id", type=int)
    status = request.args.get("status")

    from ..models import Application, PlacementDrive

    q = Application.query
    if drive_id:
        q = q.filter(Application.drive_id == drive_id)
    if status:
        q = q.filter(Application.status == status)

    items = q.order_by(Application.updated_at.desc()).limit(200).all()
    return jsonify(
        {
            "items": [
                {
                    "id": a.id,
                    "student_id": a.student_id,
                    "drive_id": a.drive_id,
                    "application_date": a.application_date.isoformat(),
                    "status": a.status,
                }
                for a in items
            ]
        }
    )

