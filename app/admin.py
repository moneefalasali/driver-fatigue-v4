from flask import Blueprint, request, jsonify
from app.models import User, Session, FatigueData, db
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            # role can be in token claims or user model
            claims = get_jwt() or {}
            role = claims.get('role')
            if not role:
                # Fallback to user model
                identity = get_jwt_identity()
                user = User.query.get(identity)
                role = getattr(user, 'role', None) if user else None

            if role != 'admin':
                return jsonify(msg='Admins only!'), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

@admin_bp.route('/users', methods=['GET'])
@admin_required()
def get_users():
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role
    } for u in users]), 200

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required()
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify(msg="User deleted"), 200

@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@admin_required()
def change_role(user_id):
    data = request.get_json()
    user = User.query.get_or_404(user_id)
    user.role = data.get('role', 'user')
    db.session.commit()
    return jsonify(msg="Role updated"), 200

@admin_bp.route('/sessions', methods=['GET'])
@admin_required()
def get_sessions():
    user_id = request.args.get('user_id')
    if user_id:
        sessions = Session.query.filter_by(user_id=user_id).all()
    else:
        sessions = Session.query.all()
        
    return jsonify([{
        "id": s.id,
        "user_id": s.user_id,
        "username": s.user.username,
        "start_time": s.start_time.isoformat(),
        "end_time": s.end_time.isoformat() if s.end_time else None,
        "fatigue_avg": s.fatigue_avg,
        "alerts_count": s.alerts_count
    } for s in sessions]), 200

@admin_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@admin_required()
def delete_session(session_id):
    session = Session.query.get_or_404(session_id)
    db.session.delete(session)
    db.session.commit()
    return jsonify(msg="Session deleted"), 200

@admin_bp.route('/stats', methods=['GET'])
@admin_required()
def get_stats():
    user_count = User.query.count()
    session_count = Session.query.count()
    
    # Calculate average fatigue across all sessions
    sessions = Session.query.all()
    avg_fatigue = sum(s.fatigue_avg for s in sessions) / len(sessions) if sessions else 0
    
    total_alerts = sum(s.alerts_count for s in sessions) if sessions else 0
    
    return jsonify({
        "user_count": user_count,
        "session_count": session_count,
        "avg_fatigue": round(avg_fatigue, 2),
        "total_alerts": total_alerts
    }), 200
