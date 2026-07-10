// Advanced Alert System
const AlertSystem = {
    // Configuration
    config: {
        fatigueThreshold: 70,
        warningThreshold: 30,
        enableAudio: true,
        enableVibration: true,
        enableNotifications: true,
        alertCooldown: 5000 // 5 seconds between alerts
    },

    // State
    state: {
        lastAlertTime: 0,
        alertCount: 0,
        isMonitoring: false
    },

    // Initialize alert system
    init() {
        this.requestNotificationPermission();
        this.loadSettings();
    },

    // Request notification permission
    requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    },

    // Load settings from localStorage
    loadSettings() {
        const settings = localStorage.getItem('alertSettings');
        if (settings) {
            try {
                const parsed = JSON.parse(settings);
                this.config = { ...this.config, ...parsed };
            } catch (e) {
                console.error('Error loading alert settings:', e);
            }
        }
    },

    // Save settings to localStorage
    saveSettings() {
        localStorage.setItem('alertSettings', JSON.stringify(this.config));
    },

    // Check if alert should be triggered
    shouldTriggerAlert() {
        const now = Date.now();
        return now - this.state.lastAlertTime > this.config.alertCooldown;
    },

    // Trigger alert for fatigue
    triggerFatigueAlert(fatigueScore, eyeStatus = 'Closed') {
        if (!this.shouldTriggerAlert()) return;

        this.state.lastAlertTime = Date.now();
        this.state.alertCount++;

        // Determine alert level
        const alertLevel = fatigueScore >= this.config.fatigueThreshold ? 'HIGH' : 'MEDIUM';

        // Create alert object
        const alert = {
            id: `alert-${Date.now()}`,
            level: alertLevel,
            fatigueScore: fatigueScore,
            eyeStatus: eyeStatus,
            timestamp: new Date(),
            message: this.getAlertMessage(alertLevel, fatigueScore)
        };

        // Trigger different alert types
        this.playAudioAlert(alertLevel);
        this.triggerVibration(alertLevel);
        this.showNotification(alert);
        this.showVisualAlert(alert);
        this.logAlert(alert);

        return alert;
    },

    // Get alert message based on level and score
    getAlertMessage(level, score) {
        if (level === 'HIGH') {
            if (score >= 85) {
                return 'تنبيه حرج: إرهاق شديد جداً! توقف فوراً للراحة';
            }
            return 'تنبيه: إرهاق شديد! يرجى التوقف للراحة';
        }
        return 'تحذير: علامات إرهاق متوسطة. كن حذراً';
    },

    // Play audio alert
    playAudioAlert(level) {
        if (!this.config.enableAudio) return;

        try {
            // Create audio context for different alert tones
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            // Different frequencies for different alert levels
            if (level === 'HIGH') {
                oscillator.frequency.value = 1000; // Higher frequency for critical
                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.5);
            } else {
                oscillator.frequency.value = 800;
                gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.3);
            }
        } catch (e) {
            console.log('Audio alert failed:', e);
            // Fallback: try to play alert sound file
            this.playAlertFile();
        }
    },

    // Play alert sound file
    playAlertFile() {
        try {
            const audio = new Audio('/static/alert.mp3');
            audio.volume = 0.7;
            audio.play().catch(e => console.log('Audio play failed:', e));
        } catch (e) {
            console.log('Alert file play failed:', e);
        }
    },

    // Trigger vibration alert
    triggerVibration(level) {
        if (!this.config.enableVibration || !navigator.vibrate) return;

        try {
            if (level === 'HIGH') {
                // Pattern: long vibration, pause, long vibration
                navigator.vibrate([500, 200, 500, 200, 500]);
            } else {
                // Pattern: short vibrations
                navigator.vibrate([300, 100, 300]);
            }
        } catch (e) {
            console.log('Vibration failed:', e);
        }
    },

    // Show browser notification
    showNotification(alert) {
        if (!this.config.enableNotifications || !('Notification' in window)) return;

        if (Notification.permission === 'granted') {
            try {
                const notification = new Notification('تنبيه إرهاق السائق', {
                    body: alert.message,
                    icon: '/static/icons/icon-192x192.png',
                    badge: '/static/icons/icon-96x96.png',
                    tag: 'fatigue-alert',
                    requireInteraction: alert.level === 'HIGH'
                });

                // Close notification after 10 seconds
                setTimeout(() => notification.close(), 10000);
            } catch (e) {
                console.log('Notification failed:', e);
            }
        }
    },

    // Show visual alert overlay
    showVisualAlert(alert) {
        const alertOverlay = document.getElementById('alert-overlay');
        if (!alertOverlay) return;

        // Update alert content
        const title = alertOverlay.querySelector('h1');
        const message = alertOverlay.querySelector('p');

        if (title) title.textContent = alert.message;
        if (message) message.textContent = `درجة الإرهاق: ${alert.fatigueScore}%`;

        // Show overlay
        alertOverlay.classList.remove('d-none');

        // Change color based on alert level
        if (alert.level === 'HIGH') {
            alertOverlay.style.background = 'rgba(220, 53, 69, 0.95)'; // Red
        } else {
            alertOverlay.style.background = 'rgba(255, 193, 7, 0.95)'; // Yellow
        }

        // Hide after 4 seconds
        setTimeout(() => {
            alertOverlay.classList.add('d-none');
        }, 4000);
    },

    // Log alert to local storage
    logAlert(alert) {
        try {
            let alerts = JSON.parse(localStorage.getItem('alertHistory') || '[]');
            alerts.unshift({
                ...alert,
                timestamp: alert.timestamp.toISOString()
            });
            // Keep only last 100 alerts
            alerts = alerts.slice(0, 100);
            localStorage.setItem('alertHistory', JSON.stringify(alerts));
        } catch (e) {
            console.error('Error logging alert:', e);
        }
    },

    // Get alert history
    getAlertHistory(limit = 50) {
        try {
            const alerts = JSON.parse(localStorage.getItem('alertHistory') || '[]');
            return alerts.slice(0, limit);
        } catch (e) {
            return [];
        }
    },

    // Clear alert history
    clearAlertHistory() {
        localStorage.removeItem('alertHistory');
        this.state.alertCount = 0;
    },

    // Get alert statistics
    getAlertStats() {
        const history = this.getAlertHistory(1000);
        const highAlerts = history.filter(a => a.level === 'HIGH').length;
        const mediumAlerts = history.filter(a => a.level === 'MEDIUM').length;

        return {
            total: history.length,
            high: highAlerts,
            medium: mediumAlerts,
            lastAlert: history[0] ? new Date(history[0].timestamp) : null
        };
    }
};

// Initialize alert system when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    AlertSystem.init();
});
