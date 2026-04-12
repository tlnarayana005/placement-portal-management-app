"""Authentication routes — registration and login."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash as _generate_password_hash, check_password_hash
from models import db
from models.models import User, Student, Company
import json

auth_bp = Blueprint('auth', __name__)


def generate_password_hash(password):
    return _generate_password_hash(password, method='pbkdf2:sha256')


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    # Block admin registration
    if data.get('role') == 'admin':
        return jsonify({'error': 'Admin registration is not allowed'}), 403

    if data.get('role') not in ['student', 'company']:
        return jsonify({'error': 'Invalid role'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400

    user = User(email=data['email'], password=generate_password_hash(data['password']),
                role=data['role'], name=data['name'])
    db.session.add(user)
    db.session.commit()

    if data['role'] == 'student':
        student = Student(
            user_id=user.id,
            branch=data.get('branch', ''),
            cgpa=float(data.get('cgpa', 0)),
            graduation_year=int(data.get('graduation_year', 2026))
        )
        db.session.add(student)
    elif data['role'] == 'company':
        company = Company(
            user_id=user.id,
            website=data.get('website', ''),
            hr_contact=data.get('hr_contact', ''),
            industry=data.get('industry', '')
        )
        db.session.add(company)

    db.session.commit()
    return jsonify({'message': 'User registered successfully'})


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account deactivated by admin'}), 403

    # For company check approval
    if user.role == 'company':
        comp = Company.query.filter_by(user_id=user.id).first()
        if comp and comp.is_blacklisted:
            return jsonify({'error': 'Your company has been blacklisted'}), 403

    token = create_access_token(identity=json.dumps({'id': user.id, 'role': user.role}))
    return jsonify({'token': token, 'user': {'id': user.id, 'role': user.role, 'name': user.name}})
