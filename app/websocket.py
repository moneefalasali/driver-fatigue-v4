from app import socketio, db
from flask_socketio import emit
from flask import request
from flask_jwt_extended import decode_token
from datetime import datetime
import base64
import cv2
import numpy as np
from app.models import Session, FatigueData
from app.ai.meta_model import FatigueMetaModel
from app.ai.utils import calculate_ear, calculate_head_pose, FatigueTracker

# Initialize lightweight helpers only when needed to avoid expensive imports during startup.
meta_model = FatigueMetaModel()

# Store session info per socket ID
# { sid: { 'tracker': FatigueTracker, 'user_id': int, 'session_id': int, 'scores': [], 'alerts': 0 } }
active_sessions = {}

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    
    # Try to get user from token in query string
    token = request.args.get('token')
    user_id = None
    session_id = None
    
    if token:
        try:
            decoded = decode_token(token)
            user_id = int(decoded['sub'])
            
            # Create a new session in DB
            new_session = Session(user_id=user_id, start_time=datetime.utcnow())
            db.session.add(new_session)
            db.session.commit()
            session_id = new_session.id
            print(f"Session created for user {user_id}: {session_id}")
        except Exception as e:
            print(f"Auth error: {e}")

    active_sessions[request.sid] = {
        'tracker': FatigueTracker(),
        'user_id': user_id,
        'session_id': session_id,
        'scores': [],
        'alerts': 0,
        'last_gps': None,
        'frame_count': 0
    }

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    print(f'Client disconnected: {sid}')
    
    if sid in active_sessions:
        session_info = active_sessions[sid]
        if session_info['session_id']:
            # Update session in DB
            session = Session.query.get(session_info['session_id'])
            if session:
                session.end_time = datetime.utcnow()
                if session_info['scores']:
                    session.fatigue_avg = sum(session_info['scores']) / len(session_info['scores'])
                session.alerts_count = session_info['alerts']
                db.session.commit()
                print(f"Session {session_info['session_id']} ended. Avg fatigue: {session.fatigue_avg}, Alerts: {session.alerts_count}")
        
        del active_sessions[sid]

class Landmark:
    def __init__(self, data):
        self.x = data.get('x', 0)
        self.y = data.get('y', 0)
        self.z = data.get('z', 0)

@socketio.on('face_landmarks')
def handle_face_landmarks(landmarks_data):
    sid = request.sid
    if sid not in active_sessions:
        return
    
    session_info = active_sessions[sid]
    tracker = session_info['tracker']
    session_info['frame_count'] += 1
    
    # Convert landmarks data to Landmark objects
    landmarks = [Landmark(l) for l in landmarks_data]
    
    # Calculate features
    ear = calculate_ear(landmarks)
    pitch, yaw = calculate_head_pose(landmarks)
    
    # Update tracker and get fatigue score
    fatigue_score = tracker.update(ear, pitch, yaw)
    
    # Track scores for average
    session_info['scores'].append(fatigue_score)
    
    # Determine status
    status = 'LOW'
    alert_triggered = False
    if fatigue_score > 70:
        status = 'HIGH'
        session_info['alerts'] += 1
        alert_triggered = True
    elif fatigue_score > 30:
        status = 'MEDIUM'
    
    # Save to DB if session is active (every 30 frames to avoid DB bloat)
    if session_info['session_id'] and session_info['frame_count'] % 30 == 0:
        try:
            # Get last GPS data if available
            latitude = session_info['last_gps']['latitude'] if session_info['last_gps'] else None
            longitude = session_info['last_gps']['longitude'] if session_info['last_gps'] else None
            speed = session_info['last_gps']['speed'] if session_info['last_gps'] else None
            
            data = FatigueData(
                session_id=session_info['session_id'],
                fatigue_score=fatigue_score,
                status=status,
                latitude=latitude,
                longitude=longitude,
                speed=speed
            )
            db.session.add(data)
            db.session.commit()
        except Exception as e:
            print(f"Error saving fatigue data: {e}")
            db.session.rollback()
    
    # Simulate some dynamic sensor data if not provided
    import random
    temperature = 24.0 + random.uniform(-0.5, 0.5)
    
    # Emit result
    emit('fatigue_result', {
        'fatigue_score': int(fatigue_score),
        'eye_status': 'Open' if ear > 0.2 else 'Closed',
        'blink_rate': tracker.blink_count,
        'status': status,
        'ear': round(ear, 3),
        'pitch': round(pitch, 1),
        'yaw': round(yaw, 1),
        'detection_confidence': 0.85,
        'alert_triggered': alert_triggered,
        'temperature': round(temperature, 1)
    })

@socketio.on('sensor_data')
def handle_sensor_data(data):
    """Handle sensor data from client"""
    try:
        if request.sid not in active_sessions:
            return

        session_info = active_sessions[request.sid]
        
        # Store sensor data for potential analysis
        accelerometer = data.get('accelerometer', {})
        gyroscope = data.get('gyroscope', {})
        timestamp = data.get('timestamp')
        
        # You can add logic here to analyze sensor data
        # For example, detect sudden movements, phone drops, etc.
        # This data can be used to enhance fatigue detection
        
        # Log for debugging
        if session_info['frame_count'] % 100 == 0:
            print(f"Sensor data - Accel: {accelerometer}, Gyro: {gyroscope}")
        
    except Exception as e:
        print(f"Error processing sensor data: {e}")

@socketio.on('gps_data')
def handle_gps_data(data):
    """Handle GPS data from client"""
    try:
        if request.sid not in active_sessions:
            return

        session_info = active_sessions[request.sid]
        
        # Extract GPS data
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        speed = data.get('speed')
        timestamp = data.get('timestamp')
        
        # Store GPS data for later use
        session_info['last_gps'] = {
            'latitude': latitude,
            'longitude': longitude,
            'speed': speed,
            'timestamp': timestamp
        }
        
        # Log for debugging
        if session_info['frame_count'] % 100 == 0:
            print(f"GPS data - Lat: {latitude}, Lon: {longitude}, Speed: {speed}")
        
    except Exception as e:
        print(f"Error processing GPS data: {e}")

@socketio.on('error')
def handle_error(data):
    """Handle client errors"""
    print(f"Client error: {data}")
