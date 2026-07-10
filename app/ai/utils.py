import numpy as np
import math

def calculate_ear(landmarks):
    """
    Calculate Eye Aspect Ratio (EAR)
    Landmarks indices for MediaPipe Face Mesh:
    Left Eye: [362, 385, 387, 263, 373, 380]
    Right Eye: [33, 160, 158, 133, 153, 144]
    """
    def get_ear(eye_points):
        # Vertical distances
        v1 = np.linalg.norm(np.array([landmarks[eye_points[1]].x, landmarks[eye_points[1]].y]) - 
                            np.array([landmarks[eye_points[5]].x, landmarks[eye_points[5]].y]))
        v2 = np.linalg.norm(np.array([landmarks[eye_points[2]].x, landmarks[eye_points[2]].y]) - 
                            np.array([landmarks[eye_points[4]].x, landmarks[eye_points[4]].y]))
        # Horizontal distance
        h = np.linalg.norm(np.array([landmarks[eye_points[0]].x, landmarks[eye_points[0]].y]) - 
                           np.array([landmarks[eye_points[3]].x, landmarks[eye_points[3]].y]))
        return (v1 + v2) / (2.0 * h)

    left_ear = get_ear([362, 385, 387, 263, 373, 380])
    right_ear = get_ear([33, 160, 158, 133, 153, 144])
    
    return (left_ear + right_ear) / 2.0

def calculate_head_pose(landmarks):
    """
    Estimate head pose (pitch, yaw, roll) from landmarks
    Simplified version using specific points
    """
    # Nose tip: 1, Chin: 152, Left eye left corner: 33, Right eye right corner: 263
    # Left mouth corner: 61, Right mouth corner: 291
    
    # Yaw: horizontal rotation (left/right)
    # Compare distance from nose to left/right eye corners
    nose = landmarks[1]
    left_eye = landmarks[33]
    right_eye = landmarks[263]
    
    dist_l = abs(nose.x - left_eye.x)
    dist_r = abs(nose.x - right_eye.x)
    yaw = (dist_r - dist_l) / (dist_r + dist_l) if (dist_r + dist_l) != 0 else 0
    
    # Pitch: vertical rotation (up/down)
    # Compare distance from nose to forehead/chin
    forehead = landmarks[10]
    chin = landmarks[152]
    dist_u = abs(nose.y - forehead.y)
    dist_d = abs(nose.y - chin.y)
    pitch = (dist_d - dist_u) / (dist_d + dist_u) if (dist_d + dist_u) != 0 else 0
    
    return pitch, yaw

class FatigueTracker:
    def __init__(self, window_size=15):
        self.ear_history = []
        self.pitch_history = []
        self.yaw_history = []
        self.window_size = window_size
        self.blink_count = 0
        self.is_closed = False
        self.closed_frames = 0
        
    def update(self, ear, pitch, yaw):
        self.ear_history.append(ear)
        self.pitch_history.append(pitch)
        self.yaw_history.append(yaw)
        
        if len(self.ear_history) > self.window_size:
            self.ear_history.pop(0)
            self.pitch_history.pop(0)
            self.yaw_history.pop(0)
            
        # Blink detection
        if ear < 0.2: # Threshold for closed eye
            if not self.is_closed:
                self.is_closed = True
                self.blink_count += 1
            self.closed_frames += 1
        else:
            self.is_closed = False
            self.closed_frames = 0
            
        # Calculate fatigue score (0-100)
        # Factors: 
        # 1. PERCLOS (Percentage of Eye Closure)
        # 2. Head pose stability
        # 3. Average EAR
        
        perclos = (sum(1 for e in self.ear_history if e < 0.2) / len(self.ear_history)) * 100
        
        # Head pose deviation
        pitch_dev = np.std(self.pitch_history) * 100 if self.pitch_history else 0
        yaw_dev = np.std(self.yaw_history) * 100 if self.yaw_history else 0
        pose_score = min(100, (pitch_dev + yaw_dev) * 5)
        
        # Long closure penalty
        closure_penalty = min(50, self.closed_frames * 5)
        
        fatigue_score = (perclos * 0.6) + (pose_score * 0.2) + closure_penalty
        return min(100, fatigue_score)
