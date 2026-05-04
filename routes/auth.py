from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database import db, User
import bcrypt
import re

auth_bp = Blueprint('auth', __name__)

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'\d', password):
        return False, "Password must contain at least 1 numeral"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least 1 special character"
    return True, ""

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not name or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400

    valid, msg = validate_password(password)
    if not valid:
        return jsonify({'error': msg}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = User(name=name, email=email, password_hash=hashed.decode('utf-8'))
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.user_id))
    return jsonify({
        'message': 'Registration successful',
        'token': token,
        'user': {'id': user.user_id, 'name': user.name, 'email': user.email, 'is_admin': user.is_admin}
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_access_token(identity=str(user.user_id))
    return jsonify({
        'token': token,
        'user': {'id': user.user_id, 'name': user.name, 'email': user.email, 'is_admin': user.is_admin}
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'id': user.user_id, 'name': user.name, 'email': user.email, 'is_admin': user.is_admin})
