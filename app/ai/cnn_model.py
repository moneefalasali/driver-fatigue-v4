try:
    import tensorflow as tf
    from tensorflow.keras import layers, models
except Exception:  # pragma: no cover - fallback for lightweight environments
    tf = None
    layers = None
    models = None


def create_eye_model():
    if models is None or layers is None:
        return None

    model = models.Sequential([
        layers.Conv2D(32, (3, 3), activation='relu', input_shape=(24, 24, 1)),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model


class EyeClassifier:
    def __init__(self):
        self.model = create_eye_model()
        # In a real scenario, we would load weights here
        # self.model.load_weights('eye_model_weights.h5')

    def predict(self, eye_image):
        if self.model is None:
            return 0.1

        # Preprocess eye_image
        # prediction = self.model.predict(eye_image)
        # return prediction[0][0]
        return 0.1
