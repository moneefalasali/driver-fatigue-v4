from flask import Blueprint, render_template, jsonify, request
from flask_jwt_extended import get_jwt_identity, create_access_token, jwt_required, get_jwt
from flask import jsonify
from app.models import User, Session, FatigueData, db
from datetime import datetime, timedelta
from functools import wraps
from app.admin import admin_required

main_bp = Blueprint('main', __name__)

# Pages are served as static templates; authentication is done via API Authorization header.
# Do NOT perform redirects to /login from the backend. Frontend handles redirects.

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/login')
def login():
    return render_template('login.html')

@main_bp.route('/register')
def register():
    return render_template('register.html')


@main_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token, user_id=user.id, username=user.username, role=user.role), 200
    return jsonify({"msg": "Bad username or password"}), 401

@main_bp.route('/monitoring')
def monitoring():
    return render_template('monitoring.html')

@main_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/settings')
def settings():
    return render_template('settings.html')


# Admin UI pages (protected)
@main_bp.route('/admin')
@admin_required()
def admin_index():
    return render_template('admin_index.html')


@main_bp.route('/admin/users')
@admin_required()
def admin_users():
    return render_template('admin_users.html')


@main_bp.route('/admin/sessions')
@admin_required()
def admin_sessions():
    return render_template('admin_sessions.html')


@main_bp.route('/admin/stats')
@admin_required()
def admin_stats():
    return render_template('admin_stats.html')

@main_bp.route('/api/stats', methods=['GET'])
@jwt_required()
def get_stats():
    identity = get_jwt_identity()
    user = User.query.get(int(identity))
    if not user:
        return jsonify(msg="User not found"), 404

    sessions = Session.query.filter_by(user_id=user.id).order_by(Session.start_time.desc()).all()

    total_sessions = len(sessions)
    total_alerts = sum(s.alerts_count for s in sessions)
    avg_fatigue = sum(s.fatigue_avg for s in sessions) / total_sessions if total_sessions > 0 else 0
    
    # Calculate total hours
    total_seconds = 0
    for s in sessions:
        if s.end_time:
            total_seconds += (s.end_time - s.start_time).total_seconds()
    total_hours = round(total_seconds / 3600, 1)
    
    # Get recent fatigue data for chart (last 50 points from the latest session)
    recent_fatigue = []
    if sessions:
        last_session = sessions[0]
        fatigue_points = FatigueData.query.filter_by(session_id=last_session.id).order_by(FatigueData.timestamp.asc()).limit(50).all()
        recent_fatigue = [{"time": p.timestamp.strftime("%H:%M:%S"), "score": p.fatigue_score} for p in fatigue_points]
        
    # Get recent sessions for list
    recent_sessions = []
    for s in sessions[:5]:
        duration = 0
        if s.end_time:
            duration = int((s.end_time - s.start_time).total_seconds() / 60)
        recent_sessions.append({
            "id": s.id,
            "start_time": s.start_time.isoformat(),
            "duration": duration,
            "fatigue_avg": round(s.fatigue_avg, 1),
            "alerts_count": s.alerts_count
        })
        
    return jsonify({
        "total_sessions": total_sessions,
        "total_hours": total_hours,
        "total_alerts": total_alerts,
        "avg_fatigue": round(avg_fatigue, 1),
        "recent_fatigue": recent_fatigue,
        "recent_sessions": recent_sessions
    }), 200
