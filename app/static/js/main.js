document.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements
    const video = document.getElementById('video');
    const canvas = document.getElementById('overlay');
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const fatigueScoreEl = document.getElementById('fatigue-score');
    const fatigueProgressEl = document.getElementById('fatigue-progress');
    const eyeStatusEl = document.getElementById('eye-status');
    const blinkRateEl = document.getElementById('blink-rate');
    const gpsSpeedEl = document.getElementById('gps-speed');
    const gpsLocationEl = document.getElementById('gps-location');
    const statusBadge = document.getElementById('status-badge');
    const headPoseEl = document.getElementById('head-pose');
    const detectionQualityEl = document.getElementById('detection-quality');
    const alertLog = document.getElementById('alert-log');
    const cameraError = document.getElementById('camera-error');
    const errorText = document.getElementById('error-text');

    // Check if we're on monitoring page
    if (!video || !canvas) return;

    // Get token from localStorage
    const token = localStorage.getItem('token');

    // Initialize managers
    const camera = new CameraManager(video, canvas);
    const sensors = new SensorManager();
    const gps = new GPSManager();

    // MediaPipe Face Mesh initialization
    const faceMesh = new FaceMesh({
        locateFile: (file) => {
            return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
        }
    });

    faceMesh.setOptions({
        maxNumFaces: 1,
        refineLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });

    // Socket.IO connection
    let socket = null;
    let isMonitoring = false;
    let alertCount = 0;

    // Initialize Socket.IO connection if token exists
    if (token) {
        socket = io({
            query: { token: token },
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: 5
        });

        socket.on('connect', () => {
            console.log('Connected to server');
        });

        socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });

        socket.on('fatigue_result', (data) => {
            // Update UI with fatigue analysis results
            const fatigueScore = Math.round(data.fatigue_score || 0);
            fatigueScoreEl.innerText = `${fatigueScore}%`;
            fatigueProgressEl.style.width = `${fatigueScore}%`;

            // Update progress bar color based on fatigue level
            if (fatigueScore < 30) {
                fatigueProgressEl.className = 'progress-bar bg-success';
            } else if (fatigueScore < 70) {
                fatigueProgressEl.className = 'progress-bar bg-warning';
            } else {
                fatigueProgressEl.className = 'progress-bar bg-danger';
                showAlert(fatigueScore, data.eye_status);
            }

            // Update eye status
            eyeStatusEl.innerText = data.eye_status === 'Open' ? 'مفتوحة' : 'مغلقة';
            eyeStatusEl.className = data.eye_status === 'Open' ? 'fw-bold text-success' : 'fw-bold text-danger';

            // Update blink rate
            blinkRateEl.innerText = `${Math.round(data.blink_rate || 0)}/د`;

            // Update head pose if available
            if (data.pitch !== undefined && data.yaw !== undefined) {
                headPoseEl.innerText = `P:${Math.round(data.pitch)}° Y:${Math.round(data.yaw)}°`;
            }

            // Update detection quality
            if (data.detection_confidence !== undefined) {
                detectionQualityEl.innerText = `${Math.round(data.detection_confidence * 100)}%`;
            }

            // Update temperature if available
            const tempEl = document.getElementById('temperature');
            if (tempEl && data.temperature !== undefined) {
                tempEl.innerText = data.temperature;
            }
        });

        socket.on('error', (error) => {
            console.error('Socket error:', error);
        });
    }

    // MediaPipe Face Mesh results handler
    faceMesh.onResults((results) => {
        const canvasCtx = canvas.getContext('2d');
        canvasCtx.save();
        canvasCtx.clearRect(0, 0, canvas.width, canvas.height);

        if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
            for (const landmarks of results.multiFaceLandmarks) {
                // Draw face mesh connections
                if (typeof drawConnectors !== 'undefined') {
                    drawConnectors(canvasCtx, landmarks, FACEMESH_TESSELATION, {
                        color: '#C0C0C030',
                        lineWidth: 1
                    });
                    drawConnectors(canvasCtx, landmarks, FACEMESH_RIGHT_EYE, {
                        color: '#FF3030',
                        lineWidth: 2
                    });
                    drawConnectors(canvasCtx, landmarks, FACEMESH_LEFT_EYE, {
                        color: '#30FF30',
                        lineWidth: 2
                    });
                }

                // Send landmarks to server if connected
                if (socket && socket.connected && isMonitoring) {
                    socket.emit('face_landmarks', landmarks);
                }
            }
        }

        canvasCtx.restore();
    });

    // Alert display function using AlertSystem
    function showAlert(fatigueScore = 0, eyeStatus = 'Closed') {
        if (AlertSystem) {
            const alert = AlertSystem.triggerFatigueAlert(fatigueScore, eyeStatus);
            if (alert) {
                addAlertLog(alert);
            }
        }
    }

    // Add alert to log
    function addAlertLog(alert) {
        if (!alert) return;
        
        alertCount++;
        const time = new Date().toLocaleTimeString('ar-SA');
        const alertItem = document.createElement('div');
        alertItem.className = 'list-group-item small py-2';
        
        const icon = alert.level === 'HIGH' ? 'fa-exclamation-triangle text-danger' : 'fa-exclamation-circle text-warning';
        const badge = alert.level === 'HIGH' ? '<span class="badge bg-danger ms-2">حرج</span>' : '<span class="badge bg-warning ms-2">تحذير</span>';
        
        alertItem.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span><i class="fas ${icon} me-2"></i>${alert.message}${badge}</span>
                <span class="text-muted">${time}</span>
            </div>
        `;

        // Clear placeholder if exists
        if (alertLog.children.length === 1 && alertLog.children[0].textContent.includes('لا توجد')) {
            alertLog.innerHTML = '';
        }

        alertLog.insertBefore(alertItem, alertLog.firstChild);

        // Keep only last 10 alerts
        while (alertLog.children.length > 10) {
            alertLog.removeChild(alertLog.lastChild);
        }
    }

    // Start monitoring
    startBtn.addEventListener('click', async () => {
        try {
            // Hide camera error if shown
            if (cameraError) {
                cameraError.classList.add('d-none');
            }

            // Start camera
            const cameraStarted = await camera.start();

            if (cameraStarted) {
                // Start sensors and GPS
                sensors.start();
                gps.start();

                // Update UI
                startBtn.disabled = true;
                stopBtn.disabled = false;
                isMonitoring = true;

                if (statusBadge) {
                    statusBadge.innerHTML = '<i class="fas fa-circle me-1"></i>نشط';
                    statusBadge.className = 'badge bg-success';
                }

                // Start processing frames
                const processFrame = async () => {
                    if (camera.isActive && isMonitoring) {
                        try {
                            await faceMesh.send({ image: video });
                        } catch (error) {
                            console.error('Error processing frame:', error);
                        }
                        requestAnimationFrame(processFrame);
                    }
                };

                processFrame();
            } else {
                // Show camera error
                if (cameraError && errorText) {
                    errorText.textContent = 'فشل الوصول إلى الكاميرا. تحقق من الأذونات.';
                    cameraError.classList.remove('d-none');
                }
            }
        } catch (error) {
            console.error('Error starting monitoring:', error);
            if (cameraError && errorText) {
                errorText.textContent = 'حدث خطأ أثناء بدء المراقبة';
                cameraError.classList.remove('d-none');
            }
        }
    });

    // Stop monitoring
    stopBtn.addEventListener('click', () => {
        try {
            camera.stop();
            sensors.stop();
            gps.stop();
            isMonitoring = false;

            // Update UI
            startBtn.disabled = false;
            stopBtn.disabled = true;

            if (statusBadge) {
                statusBadge.innerHTML = '<i class="fas fa-circle me-1"></i>متوقف';
                statusBadge.className = 'badge bg-secondary';
            }

            // Hide camera error
            if (cameraError) {
                cameraError.classList.add('d-none');
            }
        } catch (error) {
            console.error('Error stopping monitoring:', error);
        }
    });

    // Listen for GPS data
    window.addEventListener('gps-data', (e) => {
        const data = e.detail;
        if (gpsSpeedEl) {
            gpsSpeedEl.innerText = `${Math.round(data.speed * 3.6)} كم/س`;
        }
        if (gpsLocationEl) {
            gpsLocationEl.innerText = `${data.latitude.toFixed(2)}, ${data.longitude.toFixed(2)}`;
        }

        // Send GPS data to server if connected
        if (socket && socket.connected && isMonitoring) {
            socket.emit('gps_data', {
                latitude: data.latitude,
                longitude: data.longitude,
                speed: data.speed,
                timestamp: data.timestamp
            });
        }
    });

    // Listen for sensor data
    window.addEventListener('sensor-data', (e) => {
        const data = e.detail;

        // Update sensor display
        const accelX = document.getElementById('accel-x');
        const accelY = document.getElementById('accel-y');
        const accelZ = document.getElementById('accel-z');

        if (accelX && data.accelerometer) {
            accelX.textContent = data.accelerometer.x?.toFixed(2) || '0';
            accelY.textContent = data.accelerometer.y?.toFixed(2) || '0';
            accelZ.textContent = data.accelerometer.z?.toFixed(2) || '0';
        }

        // Send sensor data to server if connected
        if (socket && socket.connected && isMonitoring) {
            socket.emit('sensor_data', {
                accelerometer: data.accelerometer,
                gyroscope: data.gyroscope,
                timestamp: data.timestamp
            });
        }
    });

    // Handle camera errors
    window.addEventListener('camera-error', (e) => {
        console.error('Camera error:', e.detail);
        if (cameraError && errorText) {
            errorText.textContent = e.detail.message;
            cameraError.classList.remove('d-none');
        }
        startBtn.disabled = false;
        stopBtn.disabled = true;
    });

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (isMonitoring) {
            camera.stop();
            sensors.stop();
            gps.stop();
        }
        if (socket) {
            socket.disconnect();
        }
    });
});
