"""Admin routes — dashboard stats, approvals, CRUD operations, and audit trail."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, cache
from models.models import User, Student, Company, PlacementDrive, Application, AuditLog
import json
from datetime import datetime

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/api/admin/stats', methods=['GET'])
@jwt_required()
@cache.cached(timeout=30, key_prefix='admin_stats')
def get_admin_stats():
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    students = Student.query.count()
    companies = Company.query.count()
    drives = PlacementDrive.query.count()
    applications = Application.query.count()
    selected = Application.query.filter_by(status='selected').count()
    return jsonify({
        'students': students, 'companies': companies, 'drives': drives,
        'applications': applications, 'selected': selected
    })


@admin_bp.route('/api/admin/companies', methods=['GET'])
@jwt_required()
def get_admin_companies():
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    companies = db.session.query(User, Company).join(Company, User.id == Company.user_id).all()
    result = []
    for u, c in companies:
        result.append({
            'id': u.id, 'name': u.name, 'email': u.email,
            'website': c.website, 'hr_contact': c.hr_contact, 'industry': c.industry,
            'approval_status': c.approval_status, 'is_blacklisted': c.is_blacklisted,
            'is_active': u.is_active
        })
    return jsonify(result)


@admin_bp.route('/api/admin/students', methods=['GET'])
@jwt_required()
def get_admin_students():
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    students = db.session.query(User, Student).join(Student, User.id == Student.user_id).all()
    res = []
    for u, s in students:
        res.append({
            'id': u.id, 'name': u.name, 'email': u.email,
            'branch': s.branch, 'cgpa': s.cgpa, 'graduation_year': s.graduation_year,
            'is_active': u.is_active
        })
    return jsonify(res)


@admin_bp.route('/api/admin/applications', methods=['GET'])
@jwt_required()
def get_all_applications():
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    apps = db.session.query(Application, PlacementDrive, User).join(
        PlacementDrive, Application.drive_id == PlacementDrive.id
    ).join(User, Application.student_id == User.id).all()
    res = []
    for a, d, u in apps:
        comp = User.query.get(d.company_id)
        res.append({
            'id': a.id, 'student_name': u.name, 'student_email': u.email,
            'job_title': d.job_title, 'company_name': comp.name if comp else 'N/A',
            'status': a.status, 'date': a.date.strftime('%Y-%m-%d')
        })
    return jsonify(res)


@admin_bp.route('/api/admin/companies/<int:id>/approve', methods=['POST'])
@jwt_required()
def approve_company(id):
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    company = Company.query.get(id)
    if company:
        company.approval_status = 'approved'
        db.session.commit()
        cache.delete('admin_stats')
    return jsonify({'message': 'Company approved'})


@admin_bp.route('/api/admin/companies/<int:id>/reject', methods=['POST'])
@jwt_required()
def reject_company(id):
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    company = Company.query.get(id)
    if company:
        company.approval_status = 'rejected'
        db.session.commit()
        cache.delete('admin_stats')
    return jsonify({'message': 'Company rejected'})


@admin_bp.route('/api/admin/users/<int:id>/blacklist', methods=['POST'])
@jwt_required()
def blacklist_user(id):
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(id)
    if user:
        user.is_active = False
        if user.role == 'company':
            company = Company.query.filter_by(user_id=user.id).first()
            if company:
                company.is_blacklisted = True
        db.session.commit()
        cache.delete('admin_stats')
    return jsonify({'message': 'User blacklisted and deactivated'})


@admin_bp.route('/api/admin/users/<int:id>/activate', methods=['POST'])
@jwt_required()
def activate_user(id):
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(id)
    if user:
        user.is_active = True
        if user.role == 'company':
            company = Company.query.filter_by(user_id=user.id).first()
            if company:
                company.is_blacklisted = False
        db.session.commit()
        cache.delete('admin_stats')
    return jsonify({'message': 'User re-activated'})


@admin_bp.route('/api/admin/drives/pending', methods=['GET'])
@jwt_required()
def get_pending_drives():
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    drives = PlacementDrive.query.filter_by(status='pending').all()
    result = []
    for d in drives:
        comp = User.query.get(d.company_id)
        result.append({
            'id': d.id, 'job_title': d.job_title,
            'company_name': comp.name if comp else 'N/A',
            'base_ctc': d.base_ctc,
            'deadline': d.deadline.strftime('%Y-%m-%d') if d.deadline else 'N/A',
            'min_cgpa': d.min_cgpa
        })
    return jsonify(result)


@admin_bp.route('/api/admin/drives/<int:id>/approve', methods=['POST'])
@jwt_required()
def approve_drive(id):
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    drive = PlacementDrive.query.get(id)
    if drive:
        drive.status = 'approved'
        db.session.commit()
        cache.delete('admin_stats')
        cache.delete('student_drives')
    return jsonify({'message': 'Drive approved'})


@admin_bp.route('/api/admin/drives/<int:id>/reject', methods=['POST'])
@jwt_required()
def reject_drive(id):
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    drive = PlacementDrive.query.get(id)
    if drive:
        drive.status = 'rejected'
        db.session.commit()
        cache.delete('admin_stats')
    return jsonify({'message': 'Drive rejected'})


@admin_bp.route('/api/admin/students/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def admin_manage_student(id):
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(id)
    student = Student.query.filter_by(user_id=id).first()
    if not user or not student:
        return jsonify({'error': 'Student not found'}), 404

    if request.method == 'DELETE':
        db.session.delete(student)
        db.session.delete(user)
        db.session.commit()
        log = AuditLog(admin_id=identity['id'], action=f"Deleted student {user.name} ({user.email})",
                       target_type='student', target_id=id)
        db.session.add(log)
        db.session.commit()
        return jsonify({'message': 'Student deleted'})

    data = request.json
    old_data = f"Name: {user.name}, Branch: {student.branch}, CGPA: {student.cgpa}"
    if 'name' in data: user.name = data['name']
    if 'email' in data: user.email = data['email']
    if 'branch' in data: student.branch = data['branch']
    if 'cgpa' in data: student.cgpa = float(data['cgpa'])
    if 'graduation_year' in data: student.graduation_year = int(data['graduation_year'])

    db.session.commit()
    log = AuditLog(admin_id=identity['id'], action=f"Updated student {user.name}. Old: {old_data}",
                   target_type='student', target_id=id)
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': 'Student updated successfully'})


@admin_bp.route('/api/admin/companies/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def admin_manage_company(id):
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(id)
    company = Company.query.filter_by(user_id=id).first()
    if not user or not company:
        return jsonify({'error': 'Company not found'}), 404

    if request.method == 'DELETE':
        db.session.delete(company)
        db.session.delete(user)
        db.session.commit()
        log = AuditLog(admin_id=identity['id'], action=f"Deleted company {user.name}",
                       target_type='company', target_id=id)
        db.session.add(log)
        db.session.commit()
        return jsonify({'message': 'Company deleted'})

    data = request.json
    if 'name' in data: user.name = data['name']
    if 'email' in data: user.email = data['email']
    if 'website' in data: company.website = data['website']
    if 'industry' in data: company.industry = data['industry']
    if 'hr_contact' in data: company.hr_contact = data['hr_contact']

    db.session.commit()
    log = AuditLog(admin_id=identity['id'], action=f"Updated company {user.name}",
                   target_type='company', target_id=id)
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': 'Company updated successfully'})


@admin_bp.route('/api/admin/drives/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def admin_manage_drive(id):
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    drive = PlacementDrive.query.get(id)
    if not drive:
        return jsonify({'error': 'Drive not found'}), 404

    if request.method == 'DELETE':
        db.session.delete(drive)
        db.session.commit()
        log = AuditLog(admin_id=identity['id'], action=f"Deleted drive ID {id}: {drive.job_title}",
                       target_type='drive', target_id=id)
        db.session.add(log)
        db.session.commit()
        return jsonify({'message': 'Drive deleted'})

    data = request.json
    if 'job_title' in data: drive.job_title = data['job_title']
    if 'job_description' in data: drive.job_description = data['job_description']
    if 'base_ctc' in data: drive.base_ctc = data['base_ctc']
    if 'min_cgpa' in data: drive.min_cgpa = float(data['min_cgpa'])
    if 'eligibility_branch' in data: drive.eligibility_branch = data['eligibility_branch']
    if 'deadline' in data:
        try:
            drive.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d')
        except: pass

    db.session.commit()
    log = AuditLog(admin_id=identity['id'], action=f"Updated drive {drive.job_title}",
                   target_type='drive', target_id=id)
    db.session.add(log)
    db.session.commit()
    cache.delete('student_drives')
    return jsonify({'message': 'Drive updated successfully'})


@admin_bp.route('/api/admin/applications/<int:id>/status', methods=['POST'])
@jwt_required()
def admin_override_application(id):
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    app_record = Application.query.get(id)
    if not app_record:
        return jsonify({'error': 'Application not found'}), 404

    data = request.json
    old_status = app_record.status
    app_record.status = data.get('status')
    db.session.commit()

    log = AuditLog(admin_id=identity['id'],
                   action=f"Overrode application status for ID {id} from {old_status} to {app_record.status}",
                   target_type='application', target_id=id)
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': 'Application status overriden'})


@admin_bp.route('/api/admin/audit-logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    identity = json.loads(get_jwt_identity())
    if identity['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    logs = db.session.query(AuditLog, User).join(
        User, AuditLog.admin_id == User.id
    ).order_by(AuditLog.timestamp.desc()).limit(100).all()
    res = []
    for l, u in logs:
        res.append({
            'id': l.id, 'admin_name': u.name, 'action': l.action,
            'timestamp': l.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'target_type': l.target_type, 'target_id': l.target_id
        })
    return jsonify(res)
