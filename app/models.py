from app import db
from datetime import datetime
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user') # user / admin
    sessions = db.relationship('Session', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    fatigue_avg = db.Column(db.Float, default=0.0)
    alerts_count = db.Column(db.Integer, default=0)
    fatigue_data = db.relationship('FatigueData', backref='session', lazy='dynamic')

class FatigueData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    fatigue_score = db.Column(db.Float)
    status = db.Column(db.String(20)) # LOW, MEDIUM, HIGH
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    speed = db.Column(db.Float)
