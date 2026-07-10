class CameraManager {
    constructor(videoElement, canvasElement) {
        this.video = videoElement;
        this.canvas = canvasElement;
        this.ctx = this.canvas.getContext('2d');
        this.stream = null;
        this.isActive = false;
        this.fps = 15;
        this.intervalId = null;
        this.frameCount = 0;
        this.lastFrameTime = Date.now();
    }

    async start() {
        try {
            // Request camera access with optimal constraints
            const constraints = {
                video: {
                    facingMode: 'user',
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    aspectRatio: { ideal: 4 / 3 }
                },
                audio: false
            };

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            
            // Set video source
            this.video.srcObject = this.stream;
            
            // Wait for video to load
            return new Promise((resolve) => {
                this.video.onloadedmetadata = () => {
                    this.isActive = true;
                    this.startCapturing();
                    resolve(true);
                };

                // Timeout after 5 seconds
                setTimeout(() => {
                    if (!this.isActive) {
                        this.stop();
                        resolve(false);
                    }
                }, 5000);
            });
        } catch (err) {
            console.error("Error accessing camera:", err);
            this.handleCameraError(err);
            return false;
        }
    }

    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => {
                track.stop();
            });
            this.video.srcObject = null;
        }
        this.isActive = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    startCapturing() {
        this.intervalId = setInterval(() => {
            if (this.isActive && this.video.readyState === this.video.HAVE_ENOUGH_DATA) {
                this.captureFrame();
            }
        }, 1000 / this.fps);
    }

    captureFrame() {
        try {
            // Set canvas dimensions to match video
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;

            // Draw current frame to canvas
            this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);

            // Convert frame to base64
            const frameData = this.canvas.toDataURL('image/jpeg', 0.7);

            // Dispatch custom event with frame data
            window.dispatchEvent(new CustomEvent('camera-frame', {
                detail: {
                    frameData: frameData,
                    timestamp: Date.now(),
                    width: this.canvas.width,
                    height: this.canvas.height
                }
            }));

            this.frameCount++;
        } catch (error) {
            console.error("Error capturing frame:", error);
        }
    }

    getFrameCount() {
        return this.frameCount;
    }

    getActualFPS() {
        const now = Date.now();
        const elapsed = (now - this.lastFrameTime) / 1000;
        const actualFps = this.frameCount / elapsed;
        return Math.round(actualFps);
    }

    handleCameraError(error) {
        let errorMessage = 'فشل الوصول إلى الكاميرا';

        if (error.name === 'NotAllowedError') {
            errorMessage = 'تم رفض إذن الوصول للكاميرا. يرجى السماح بالوصول في إعدادات المتصفح.';
        } else if (error.name === 'NotFoundError') {
            errorMessage = 'لم يتم العثور على كاميرا متصلة بالجهاز.';
        } else if (error.name === 'NotReadableError') {
            errorMessage = 'الكاميرا قيد الاستخدام من قبل تطبيق آخر.';
        } else if (error.name === 'SecurityError') {
            errorMessage = 'لا يمكن الوصول للكاميرا لأسباب أمنية. تأكد من استخدام HTTPS.';
        }

        // Dispatch error event
        window.dispatchEvent(new CustomEvent('camera-error', {
            detail: {
                error: error.name,
                message: errorMessage
            }
        }));
    }

    setFPS(fps) {
        if (fps >= 5 && fps <= 30) {
            this.fps = fps;
            if (this.isActive) {
                clearInterval(this.intervalId);
                this.startCapturing();
            }
        }
    }

    getFPS() {
        return this.fps;
    }
}

window.CameraManager = CameraManager;
