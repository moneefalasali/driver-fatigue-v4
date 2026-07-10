class SensorManager {
    constructor() {
        this.isActive = false;
        this.accelerometer = { x: 0, y: 0, z: 0 };
        this.gyroscope = { alpha: 0, beta: 0, gamma: 0 };
        this.intervalId = null;
        this.sampleRate = 10; // 10 samples per second
        this.handleMotion = null;
        this.handleOrientation = null;
    }

    async start() {
        try {
            if (typeof DeviceMotionEvent !== 'undefined' && typeof DeviceMotionEvent.requestPermission === 'function') {
                const permission = await DeviceMotionEvent.requestPermission();
                if (permission !== 'granted') {
                    console.error("Permission denied for sensors");
                    return false;
                }
            }
            
            // Bind handlers to preserve reference
            this.handleMotion = this.onDeviceMotion.bind(this);
            this.handleOrientation = this.onDeviceOrientation.bind(this);
            
            window.addEventListener('devicemotion', this.handleMotion, false);
            window.addEventListener('deviceorientation', this.handleOrientation, false);
            this.isActive = true;
            this.startSampling();
            return true;
        } catch (err) {
            console.error("Error accessing sensors:", err);
            return false;
        }
    }

    stop() {
        if (this.handleMotion) {
            window.removeEventListener('devicemotion', this.handleMotion, false);
            this.handleMotion = null;
        }
        if (this.handleOrientation) {
            window.removeEventListener('deviceorientation', this.handleOrientation, false);
            this.handleOrientation = null;
        }
        this.isActive = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    onDeviceMotion(event) {
        const acc = event.accelerationIncludingGravity;
        if (acc) {
            this.accelerometer = {
                x: acc.x || 0,
                y: acc.y || 0,
                z: acc.z || 0
            };
        }
    }

    onDeviceOrientation(event) {
        this.gyroscope = {
            alpha: event.alpha || 0,
            beta: event.beta || 0,
            gamma: event.gamma || 0
        };
    }

    startSampling() {
        this.intervalId = setInterval(() => {
            if (this.isActive) {
                this.sampleData();
            }
        }, 1000 / this.sampleRate);
    }

    sampleData() {
        const sensorData = {
            accelerometer: { ...this.accelerometer },
            gyroscope: { ...this.gyroscope },
            timestamp: Date.now()
        };
        // Dispatch event with sensor data
        window.dispatchEvent(new CustomEvent('sensor-data', { detail: sensorData }));
    }

    getMotionIntensity() {
        const acc = this.accelerometer;
        return Math.sqrt(acc.x ** 2 + acc.y ** 2 + acc.z ** 2);
    }

    detectSuddenMovement(threshold = 20) {
        return this.getMotionIntensity() > threshold;
    }
}

window.SensorManager = SensorManager;
