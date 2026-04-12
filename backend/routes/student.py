"""Student routes — profile, applications, drives, resume upload, and CSV export."""
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import db, cache
from models.models import User, Student, PlacementDrive, Application
import json
import os
import csv
from datetime import datetime

student_bp = Blueprint('student', __name__)


@student_bp.route('/api/student/profile', methods=['GET'])
@jwt_required()
def get_student_profile():
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    user = User.query.get(identity['id'])
    student = Student.query.filter_by(user_id=identity['id']).first()
    if not user or not student:
        return jsonify({'error': 'Profile not found'}), 404
    return jsonify({
        'name': user.name, 'email': user.email,
        'branch': student.branch, 'cgpa': student.cgpa,
        'graduation_year': student.graduation_year,
        'resume_url': student.resume_url,
        'projects': json.loads(student.projects or '[]')
    })


@student_bp.route('/api/student/profile', methods=['PUT'])
@jwt_required()
def update_student_profile():
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    user = User.query.get(identity['id'])
    student = Student.query.filter_by(user_id=identity['id']).first()

    if data.get('name'):
        user.name = data['name']
    if data.get('branch'):
        student.branch = data['branch']
    if data.get('cgpa'):
        student.cgpa = float(data['cgpa'])
    if data.get('graduation_year'):
        student.graduation_year = int(data['graduation_year'])
    if 'projects' in data:
        student.projects = json.dumps(data['projects'])

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'})


@student_bp.route('/api/student/resume', methods=['POST'])
@jwt_required()
def upload_resume():
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    if 'resume' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(f"resume_{identity['id']}_{file.filename}")
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    student = Student.query.filter_by(user_id=identity['id']).first()
    student.resume_url = f'/uploads/{filename}'
    db.session.commit()
    return jsonify({'message': 'Resume uploaded successfully', 'resume_url': student.resume_url})


@student_bp.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@student_bp.route('/api/student/drives', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60, key_prefix='student_drives')
def get_student_drives():
    drives = PlacementDrive.query.filter_by(status='approved').all()
    result = []
    for d in drives:
        comp = User.query.get(d.company_id)
        result.append({
            'id': d.id,
            'job_title': d.job_title,
            'job_description': d.job_description,
            'company_name': comp.name if comp else 'N/A',
            'base_ctc': d.base_ctc,
            'eligibility_branch': d.eligibility_branch or 'All',
            'min_cgpa': d.min_cgpa or 0,
            'deadline': d.deadline.strftime('%Y-%m-%d') if d.deadline else 'N/A'
        })
    return jsonify(result)


@student_bp.route('/api/student/applications', methods=['GET'])
@jwt_required()
def get_student_applications():
    identity = json.loads(get_jwt_identity())
    apps = db.session.query(Application, PlacementDrive, User).join(
        PlacementDrive, Application.drive_id == PlacementDrive.id
    ).join(
        User, PlacementDrive.company_id == User.id
    ).filter(Application.student_id == identity['id']).all()

    result = []
    for a, d, u in apps:
        result.append({
            'id': a.id, 'drive_id': d.id,
            'job_title': d.job_title,
            'company_name': u.name,
            'status': a.status,
            'date': a.date.strftime('%Y-%m-%d')
        })
    return jsonify(result)


@student_bp.route('/api/student/apply', methods=['POST'])
@jwt_required()
def apply_drive():
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    drive_id = data.get('drive_id')

    # Check drive exists and is approved
    drive = PlacementDrive.query.get(drive_id)
    if not drive or drive.status != 'approved':
        return jsonify({'error': 'Drive not available'}), 400

    # Check deadline
    if drive.deadline and drive.deadline < datetime.utcnow():
        return jsonify({'error': 'Application deadline has passed'}), 400

    # Prevent duplicate application
    existing = Application.query.filter_by(student_id=identity['id'], drive_id=drive_id).first()
    if existing:
        return jsonify({'error': 'Already applied to this drive'}), 400

    # Eligibility validation
    student = Student.query.filter_by(user_id=identity['id']).first()
    if drive.min_cgpa and student.cgpa and student.cgpa < drive.min_cgpa:
        return jsonify({'error': f'Minimum CGPA required: {drive.min_cgpa}. Your CGPA: {student.cgpa}'}), 400

    if drive.eligibility_branch and drive.eligibility_branch != 'All':
        branches = [b.strip().lower() for b in drive.eligibility_branch.split(',')]
        if student.branch and student.branch.lower() not in branches:
            return jsonify({'error': f'Your branch ({student.branch}) is not eligible for this drive'}), 400

    new_app = Application(student_id=identity['id'], drive_id=drive_id)
    db.session.add(new_app)
    db.session.commit()
    return jsonify({'message': 'Applied successfully'})


@student_bp.route('/api/student/export', methods=['POST'])
@jwt_required()
def trigger_export():
    """Trigger CSV export of application history — async via Celery or synchronous fallback."""
    identity = json.loads(get_jwt_identity())
    student_id = identity['id']
    try:
        # Attempt async via Celery
        from celery import current_app as celery_app
        celery_app.send_task('app.export_applications_csv', args=[student_id])
        return jsonify({'message': 'Export triggered! CSV will be ready soon in the uploads folder.'})
    except Exception:
        # Fallback: synchronous export if Celery/Redis unavailable
        apps = db.session.query(Application, PlacementDrive, User).join(
            PlacementDrive, Application.drive_id == PlacementDrive.id
        ).join(
            User, PlacementDrive.company_id == User.id
        ).filter(Application.student_id == student_id).all()

        filename = f"applications_{student_id}.csv"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Student ID', 'Company Name', 'Drive Title', 'Application Status', 'Application Date'])
            for a, d, u in apps:
                writer.writerow([student_id, u.name, d.job_title, a.status, a.date.strftime('%Y-%m-%d')])

        return jsonify({'message': f'Export completed: {filename}'})
