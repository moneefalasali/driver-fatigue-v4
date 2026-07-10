from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
import numpy as np

class FatigueMetaModel:
    def __init__(self):
        self.rf_model = RandomForestClassifier(n_estimators=100)
        self.gb_model = GradientBoostingClassifier(n_estimators=100)
        # In a real scenario, we would load trained models here
        # self.rf_model = joblib.load('rf_model.pkl')
        # self.gb_model = joblib.load('gb_model.pkl')

    def predict(self, features):
        # features: [cnn_score, lstm_score, sensor_score, gps_score]
        # For now, return a weighted average as a dummy meta-prediction
        cnn_score, lstm_score, sensor_score, gps_score = features
        final_score = (cnn_score * 0.4) + (lstm_score * 0.3) + (sensor_score * 0.2) + (gps_score * 0.1)
        
        status = 'LOW'
        if final_score > 0.7:
            status = 'HIGH'
        elif final_score > 0.4:
            status = 'MEDIUM'
            
        return final_score, status
