class GPSManager {
    constructor() {
        this.watchId = null;
        this.isActive = false;
        this.location = { latitude: 0, longitude: 0, speed: 0 };
    }

    async start() {
        if (!navigator.geolocation) {
            console.error("Geolocation not supported");
            return false;
        }

        try {
            this.watchId = navigator.geolocation.watchPosition(
                this.handlePosition.bind(this),
                this.handleError.bind(this),
                {
                    enableHighAccuracy: true,
                    timeout: 5000,
                    maximumAge: 0
                }
            );
            this.isActive = true;
            return true;
        } catch (err) {
            console.error("Error accessing GPS:", err);
            return false;
        }
    }

    stop() {
        if (this.watchId) {
            navigator.geolocation.clearWatch(this.watchId);
            this.watchId = null;
        }
        this.isActive = false;
    }

    handlePosition(position) {
        this.location = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            speed: position.coords.speed || 0,
            timestamp: position.timestamp
        };
        // Dispatch event with GPS data
        window.dispatchEvent(new CustomEvent('gps-data', { detail: this.location }));
    }

    handleError(error) {
        console.error("GPS Error:", error.message);
    }
}

window.GPSManager = GPSManager;
