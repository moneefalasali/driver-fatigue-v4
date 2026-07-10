import tensorflow as tf
from tensorflow.keras import layers, models

def create_lstm_model():
    model = models.Sequential([
        layers.LSTM(64, input_shape=(30, 10), return_sequences=True),
        layers.LSTM(32),
        layers.Dense(16, activation='relu'),
        layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

class SequenceAnalyzer:
    def __init__(self):
        self.model = create_lstm_model()
        # self.model.load_weights('lstm_model_weights.h5')

    def predict(self, sequence):
        # sequence: (30, 10) array of features
        # prediction = self.model.predict(sequence.reshape(1, 30, 10))
        # return prediction[0][0]
        return 0.2 # Dummy fatigue score
