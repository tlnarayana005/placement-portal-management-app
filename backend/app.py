"""
Placement Portal Application — Main Entry Point

Creates the Flask app, initializes extensions, seeds the database,
defines Celery background tasks, and registers route blueprints.
"""
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash as _generate_password_hash
import json
import csv


def generate_password_hash(password):
    return _generate_password_hash(password, method='pbkdf2:sha256')


# --- Flask App Creation ---

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
src_dir = os.path.join(frontend_dir, 'src')

app = Flask(__name__, template_folder=frontend_dir, static_folder=src_dir, static_url_path='/src')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///iitm_placement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = '5f4dcc3b5aa765d61d8327deb882cf99f36f9479b43d39589d970e30d41829e2'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=10)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

# Cache config — SimpleCache for dev; switch to RedisCache in production
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 120


# --- Initialize Extensions (imported from models package) ---

from models import db, jwt, cache

db.init_app(app)
jwt.init_app(app)
cache.init_app(app)
CORS(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# --- Celery Configuration ---

celery = Celery(app.name, broker='redis://localhost:6379/0')
celery.conf.update(
    app.config,
    beat_schedule={
        'daily-reminders': {
            'task': 'app.send_daily_reminders',
            'schedule': crontab(minute=0, hour=9),
        },
        'monthly-reports': {
            'task': 'app.generate_monthly_report',
            'schedule': crontab(0, 0, day_of_month='1'),
        }
    },
    timezone='UTC'
)


# --- Import Models ---

from models.models import User, Student, Company, PlacementDrive, Application, AuditLog


# --- Database Initialization & Seed Data ---

with app.app_context():
    db.create_all()

    # Create Admin if not exists (admin is pre-existing, no registration allowed)
    admin = User.query.filter_by(email='admin@iitm.ac.in').first()
    if not admin:
        new_admin = User(
            email='admin@iitm.ac.in',
            password=generate_password_hash('adminpassword'),
            role='admin',
            name='IITM Admin'
        )
        db.session.add(new_admin)
        db.session.commit()

    # Create default company
    company_user = User.query.filter_by(email='hr@techcorp.com').first()
    if not company_user:
        company_user = User(
            email='hr@techcorp.com',
            password=generate_password_hash('password123'),
            role='company',
            name='TechCorp Solutions'
        )
        db.session.add(company_user)
        db.session.commit()
        company_profile = Company(
            user_id=company_user.id,
            website='https://techcorp.example.com',
            hr_contact='Jane Smith',
            industry='IT Services',
            approval_status='approved'
        )
        db.session.add(company_profile)
        db.session.commit()

        drive = PlacementDrive(
            company_id=company_user.id,
            job_title='Data Scientist',
            job_description='Analyze models and build AI infrastructure.',
            base_ctc='24 LPA',
            status='approved',
            eligibility_branch='All',
            min_cgpa=7.0,
            deadline=datetime(2026, 5, 30)
        )
        db.session.add(drive)
        db.session.commit()

    # Create default student
    student_user = User.query.filter_by(email='student@iitm.ac.in').first()
    if not student_user:
        student_user = User(
            email='student@iitm.ac.in',
            password=generate_password_hash('password123'),
            role='student',
            name='Aarav Patel'
        )
        db.session.add(student_user)
        db.session.commit()
        student_profile = Student(
            user_id=student_user.id,
            branch='Data Science',
            cgpa=9.1,
            graduation_year=2026,
            projects='[{"name": "Placement Portal", "link": "https://github.com"}]'
        )
        db.session.add(student_profile)
        db.session.commit()


# --- Celery Background Tasks ---

@celery.task(name='app.send_daily_reminders')
def send_daily_reminders():
    """Scheduled Job: Daily reminders for upcoming placement drive deadlines."""
    with app.app_context():
        upcoming = PlacementDrive.query.filter(
            PlacementDrive.status == 'approved',
            PlacementDrive.deadline != None,
            PlacementDrive.deadline >= datetime.utcnow(),
            PlacementDrive.deadline <= datetime.utcnow() + timedelta(days=3)
        ).all()
        for drive in upcoming:
            comp = User.query.get(drive.company_id)
            print(f"[REMINDER] Deadline approaching for '{drive.job_title}' by {comp.name} - Deadline: {drive.deadline}")


@celery.task(name='app.generate_monthly_report')
def generate_monthly_report():
    """Scheduled Job: Monthly placement activity report for admin."""
    with app.app_context():
        total_drives = PlacementDrive.query.count()
        total_apps = Application.query.count()
        selected = Application.query.filter_by(status='selected').count()
        admin_user = User.query.filter_by(role='admin').first()
        report = f"""
        <html><body>
        <h1>Monthly Placement Report</h1>
        <p>Total Drives: {total_drives}</p>
        <p>Total Applications: {total_apps}</p>
        <p>Students Selected: {selected}</p>
        <p>Generated: {datetime.utcnow().strftime('%Y-%m-%d')}</p>
        </body></html>
        """
        print(f"[REPORT] Monthly report generated for {admin_user.email}")
        print(report)


@celery.task(name='app.export_applications_csv')
def export_applications_csv(student_id):
    """User-triggered Async Job: Export student's application history as CSV."""
    with app.app_context():
        apps = db.session.query(Application, PlacementDrive, User).join(
            PlacementDrive, Application.drive_id == PlacementDrive.id
        ).join(
            User, PlacementDrive.company_id == User.id
        ).filter(Application.student_id == student_id).all()

        filename = f"applications_{student_id}.csv"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Student ID', 'Company Name', 'Drive Title', 'Application Status', 'Application Date'])
            for a, d, u in apps:
                writer.writerow([student_id, u.name, d.job_title, a.status, a.date.strftime('%Y-%m-%d')])
        print(f"[EXPORT] CSV export completed: {filepath}")
        return filename


# --- Core Routes (index + error handlers) ---

@app.route('/')
def index():
    return render_template('index.html')


# Smart 404 handler: returns JSON for API calls, HTML for Vue Router SPA fallback
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Resource not found'}), 404
    return render_template('index.html')


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# --- Register Route Blueprints ---

from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.company import company_bp
from routes.student import student_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(company_bp)
app.register_blueprint(student_bp)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
