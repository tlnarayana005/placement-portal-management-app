"""SQLAlchemy ORM models for the Placement Portal database."""
from models import db
from datetime import datetime


class User(db.Model):
    """Unified user model — differentiates Admin, Company, and Student by role field."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, company, student
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)


class Student(db.Model):
    """Extended profile for users with role='student'."""
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    branch = db.Column(db.String(50))
    cgpa = db.Column(db.Float)
    graduation_year = db.Column(db.Integer)
    resume_url = db.Column(db.String(200))
    projects = db.Column(db.Text, default='[]')  # JSON: [{"name": ..., "link": ...}]


class Company(db.Model):
    """Extended profile for users with role='company'."""
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    website = db.Column(db.String(200))
    hr_contact = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    approval_status = db.Column(db.String(20), default='pending')
    is_blacklisted = db.Column(db.Boolean, default=False)


class PlacementDrive(db.Model):
    """A recruitment event created by a company."""
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job_title = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text)
    eligibility_branch = db.Column(db.String(100))
    min_cgpa = db.Column(db.Float, default=0.0)
    deadline = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')
    base_ctc = db.Column(db.String(50))


class Application(db.Model):
    """A student's application to a placement drive."""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='applied')


class AuditLog(db.Model):
    """Tracks administrative actions for accountability."""
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    target_type = db.Column(db.String(50))  # student, company, drive, application
    target_id = db.Column(db.Integer)
