from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint

from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # admin, student, company
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_blacklisted = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    student_profile = db.relationship(
        "StudentProfile", back_populates="user", uselist=False
    )
    company_profile = db.relationship(
        "CompanyProfile", back_populates="user", uselist=False
    )


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), primary_key=True, nullable=False
    )
    full_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(30), nullable=True)

    # Eligibility attributes
    year_of_study = db.Column(db.Integer, nullable=False)  # 1..4 typically
    branch = db.Column(db.String(100), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)

    resume_path = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", back_populates="student_profile")


class CompanyProfile(db.Model):
    __tablename__ = "company_profiles"

    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), primary_key=True, nullable=False
    )
    company_name = db.Column(db.String(200), nullable=False)
    hr_contact = db.Column(db.String(200), nullable=True)
    website = db.Column(db.String(500), nullable=True)

    approval_status = db.Column(db.String(20), nullable=False, default="pending")
    deactivated = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="company_profile")


class PlacementDrive(db.Model):
    __tablename__ = "placement_drives"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    job_title = db.Column(db.String(200), nullable=False)
    job_description = db.Column(db.Text, nullable=True)

    eligibility_branch = db.Column(db.String(100), nullable=False)
    eligibility_cgpa_min = db.Column(db.Float, nullable=False)
    eligibility_year_min = db.Column(db.Integer, nullable=False)

    application_deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint("eligibility_year_min >= 1", name="ck_drive_year_min"),
        CheckConstraint("eligibility_cgpa_min >= 0", name="ck_drive_cgpa_min"),
    )


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drives.id"), nullable=False, index=True)

    application_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(30), nullable=False, default="applied")

    # Optional interview scheduling/results
    interview_scheduled_at = db.Column(db.DateTime, nullable=True)
    final_selection_status = db.Column(db.String(30), nullable=True)  # selected/rejected/etc.

    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("student_id", "drive_id", name="uq_app_student_drive"),
    )


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)

