const CACHE_NAME = 'driver-fatigue-v4';
const OFFLINE_URL = '/';

const ASSETS_TO_CACHE = [
    '/',
    '/login',
    '/register',
    '/monitoring',
    '/dashboard',
    '/settings',
    '/static/js/camera.js',
    '/static/js/sensors.js',
    '/static/js/gps.js',
    '/static/js/main.js',
    '/static/alert.mp3',
    '/static/icons/logo.png',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    'https://cdn.socket.io/4.5.4/socket.io.min.js',
    'https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/face_mesh.js',
    'https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js'
];

self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                return cache.addAll(ASSETS_TO_CACHE)
                    .catch((error) => {
                        console.log('Error caching assets:', error);
                    });
            })
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    if (url.pathname.startsWith('/api/') || url.origin !== location.origin || request.method !== 'GET') {
        return;
    }

    const shouldUseNetworkFirst = request.destination === 'document' || request.destination === '';

    if (shouldUseNetworkFirst) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    if (response && response.status === 200) {
                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseToCache);
                        });
                    }
                    return response;
                })
                .catch(() => caches.match(request).then((response) => response || caches.match(OFFLINE_URL)))
        );
        return;
    }

    event.respondWith(
        caches.match(request)
            .then((response) => {
                if (response) return response;
                return fetch(request)
                    .then((response) => {
                        if (response && response.status === 200) {
                            const responseToCache = response.clone();
                            caches.open(CACHE_NAME).then((cache) => {
                                cache.put(request, responseToCache);
                            });
                        }
                        return response;
                    })
                    .catch(() => caches.match(OFFLINE_URL));
            })
    );
});
