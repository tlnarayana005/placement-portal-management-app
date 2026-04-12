"""Company routes — profile, drive creation, and applicant management."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, cache
from models.models import User, Student, Company, PlacementDrive, Application
import json
from datetime import datetime

company_bp = Blueprint('company', __name__)


@company_bp.route('/api/company/profile', methods=['GET'])
@jwt_required()
def get_company_profile():
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'company':
        return jsonify({'error': 'Unauthorized'}), 403
    user = User.query.get(identity['id'])
    comp = Company.query.filter_by(user_id=identity['id']).first()
    if not user or not comp:
        return jsonify({'error': 'Profile not found'}), 404
    return jsonify({
        'name': user.name, 'email': user.email,
        'website': comp.website, 'hr_contact': comp.hr_contact,
        'industry': comp.industry, 'approval_status': comp.approval_status,
        'is_blacklisted': comp.is_blacklisted
    })


@company_bp.route('/api/company/drives', methods=['POST'])
@jwt_required()
def create_drive():
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'company':
        return jsonify({'error': 'Unauthorized'}), 403

    company = Company.query.get(identity['id'])
    if not company or company.approval_status != 'approved':
        return jsonify({'error': 'Company not approved by admin'}), 403

    data = request.json
    deadline = None
    if data.get('deadline'):
        try:
            deadline = datetime.strptime(data['deadline'], '%Y-%m-%d')
        except ValueError:
            pass

    drive = PlacementDrive(
        company_id=identity['id'],
        job_title=data['job_title'],
        job_description=data.get('job_description', ''),
        base_ctc=data.get('base_ctc', ''),
        eligibility_branch=data.get('eligibility_branch', 'All'),
        min_cgpa=float(data.get('min_cgpa', 0)),
        deadline=deadline,
        status='pending'
    )
    db.session.add(drive)
    db.session.commit()
    cache.delete('admin_stats')
    return jsonify({'message': 'Drive created and pending approval'})


@company_bp.route('/api/company/drives', methods=['GET'])
@jwt_required()
def get_company_drives():
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'company':
        return jsonify({'error': 'Unauthorized'}), 403
    drives = PlacementDrive.query.filter_by(company_id=identity['id']).all()
    res = []
    for d in drives:
        app_count = Application.query.filter_by(drive_id=d.id).count()
        res.append({
            'id': d.id, 'job_title': d.job_title, 'status': d.status,
            'base_ctc': d.base_ctc, 'applicant_count': app_count,
            'deadline': d.deadline.strftime('%Y-%m-%d') if d.deadline else 'N/A'
        })
    return jsonify(res)


@company_bp.route('/api/company/drives/<int:id>/applications', methods=['GET'])
@jwt_required()
def get_drive_applications(id):
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'company':
        return jsonify({'error': 'Unauthorized'}), 403

    drive = PlacementDrive.query.filter_by(id=id, company_id=identity['id']).first()
    if not drive:
        return jsonify({'error': 'Drive not found'}), 404

    apps = db.session.query(Application, User, Student).join(
        User, Application.student_id == User.id
    ).join(
        Student, User.id == Student.user_id
    ).filter(Application.drive_id == id).all()

    res = []
    for a, u, s in apps:
        res.append({
            'application_id': a.id,
            'student_name': u.name, 'email': u.email,
            'branch': s.branch, 'cgpa': s.cgpa,
            'status': a.status,
            'date': a.date.strftime('%Y-%m-%d')
        })
    return jsonify(res)


@company_bp.route('/api/company/applications/<int:id>/status', methods=['POST'])
@jwt_required()
def update_application_status(id):
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'company':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    app_record = Application.query.get(id)
    if not app_record:
        return jsonify({'error': 'Application not found'}), 404

    drive = PlacementDrive.query.get(app_record.drive_id)
    if not drive or drive.company_id != identity['id']:
        return jsonify({'error': 'Unauthorized'}), 403

    app_record.status = data.get('status')
    db.session.commit()
    return jsonify({'message': 'Status updated'})
