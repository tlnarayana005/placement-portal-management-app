from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import CompanyProfile, StudentProfile, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _password_from_body(body):
    password = body.get("password")
    if not password or len(password) < 6:
        return None
    return password


@auth_bp.post("/student/register")
def student_register():
    body = request.get_json(force=True)
    email = (body.get("email") or "").lower().strip()
    if not email:
        return jsonify({"error": "email is required"}), 400

    password = _password_from_body(body)
    if password is None:
        return jsonify({"error": "password must be at least 6 chars"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already exists"}), 409

    student = StudentProfile(
        full_name=body.get("full_name", "").strip(),
        phone=body.get("phone"),
        year_of_study=int(body.get("year_of_study")),
        branch=(body.get("branch") or "").strip(),
        cgpa=float(body.get("cgpa")),
    )

    if not student.full_name or not student.branch:
        return jsonify({"error": "full_name and branch are required"}), 400

    user = User(
        role="student",
        email=email,
        password_hash=generate_password_hash(password),
        is_active=True,
        is_blacklisted=False,
        student_profile=student,
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "student registered"}), 201


@auth_bp.post("/student/login")
def student_login():
    body = request.get_json(force=True)
    email = (body.get("email") or "").lower().strip()
    password = body.get("password") or ""

    user = User.query.filter_by(email=email, role="student").first()
    if not user or user.is_blacklisted or not user.is_active:
        return jsonify({"error": "invalid credentials"}), 401

    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(
        {
            "access_token": access_token,
            "token_type": "Bearer",
            "user": {"id": user.id, "role": user.role, "email": user.email},
        }
    )


@auth_bp.post("/company/register")
def company_register():
    body = request.get_json(force=True)
    email = (body.get("email") or "").lower().strip()
    if not email:
        return jsonify({"error": "email is required"}), 400

    password = _password_from_body(body)
    if password is None:
        return jsonify({"error": "password must be at least 6 chars"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already exists"}), 409

    company = CompanyProfile(
        company_name=(body.get("company_name") or "").strip(),
        hr_contact=body.get("hr_contact"),
        website=body.get("website"),
        approval_status="pending",
        deactivated=False,
    )

    if not company.company_name:
        return jsonify({"error": "company_name is required"}), 400

    user = User(
        role="company",
        email=email,
        password_hash=generate_password_hash(password),
        is_active=True,
        is_blacklisted=False,
        company_profile=company,
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "company registered, pending admin approval"}), 201


@auth_bp.post("/company/login")
def company_login():
    body = request.get_json(force=True)
    email = (body.get("email") or "").lower().strip()
    password = body.get("password") or ""

    user = User.query.filter_by(email=email, role="company").first()
    if not user or user.is_blacklisted or not user.is_active:
        return jsonify({"error": "invalid credentials"}), 401

    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401

    if user.company_profile.deactivated:
        return jsonify({"error": "company is deactivated"}), 403

    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(
        {
            "access_token": access_token,
            "token_type": "Bearer",
            "user": {"id": user.id, "role": user.role, "email": user.email},
        }
    )


@auth_bp.post("/admin/login")
def admin_login():
    body = request.get_json(force=True)
    email = (body.get("email") or "").lower().strip()
    password = body.get("password") or ""

    user = User.query.filter_by(email=email, role="admin").first()
    if not user or user.is_blacklisted or not user.is_active:
        return jsonify({"error": "invalid credentials"}), 401

    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(
        {
            "access_token": access_token,
            "token_type": "Bearer",
            "user": {"id": user.id, "role": user.role, "email": user.email},
        }
    )

