from flask import Blueprint, request, jsonify
from app.models import User, db
from flask_jwt_extended import create_access_token
from datetime import timedelta
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

auth_bp = Blueprint('auth', __name__)

# Simple blacklist for logout (in memory for now, should be Redis in production)
blacklist = set()


def _ensure_database_ready():
    try:
        with db.engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        return True
    except Exception:
        try:
            db.session.remove()
            db.engine.dispose()
        except Exception:
            pass
        try:
            db.create_all()
            with db.engine.connect() as connection:
                connection.execute(text('SELECT 1'))
            return True
        except Exception:
            return False


def _safe_rollback():
    try:
        db.session.rollback()
    except Exception:
        pass
    try:
        db.session.remove()
    except Exception:
        pass
    try:
        db.engine.dispose()
    except Exception:
        pass


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}

    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({"msg": "Missing required fields"}), 400

    if not _ensure_database_ready():
        return jsonify({"msg": "Database is not ready"}), 503

    try:
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"msg": "Username already exists"}), 400

        if User.query.filter_by(email=data['email']).first():
            return jsonify({"msg": "Email already exists"}), 400

        user = User(
            username=data['username'],
            email=data['email'],
            role=data.get('role', 'user')
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()
        return jsonify({"msg": "User created successfully"}), 201
    except SQLAlchemyError as exc:
        _safe_rollback()
        return jsonify({"msg": "Database error", "error": str(exc)}), 500
    except Exception as exc:
        _safe_rollback()
        return jsonify({"msg": "Database error", "error": str(exc)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    if not _ensure_database_ready():
        return jsonify({"msg": "Database is not ready"}), 503

    try:
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role}, expires_delta=timedelta(hours=24))
            return jsonify(access_token=access_token, user_id=user.id, role=user.role, username=user.username), 200
        return jsonify({"msg": "Bad username or password"}), 401
    except SQLAlchemyError as exc:
        _safe_rollback()
        return jsonify({"msg": "Database error", "error": str(exc)}), 500
    except Exception as exc:
        _safe_rollback()
        return jsonify({"msg": "Database error", "error": str(exc)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # Stateless JWT: logout is client-side (remove token). Backend can support revocation list here.
    return jsonify({"msg": "Successfully logged out"}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    if not _ensure_database_ready():
        return jsonify({"msg": "Database is not ready"}), 503

    identity = get_jwt_identity()
    claims = get_jwt()
    # Stored identity is a string; convert to int for DB lookup
    try:
        user = User.query.get(int(identity))
    except Exception:
        user = None
    if not user:
        return jsonify({"msg": "User not found"}), 401
    return jsonify(id=user.id, username=user.username, email=user.email, role=user.role, claims=claims), 200
