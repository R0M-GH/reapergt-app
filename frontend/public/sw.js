const CACHE_NAME = 'reaper-v1';
const urlsToCache = [
    '/',
    '/index.html',
    '/logo.png',
    '/manifest.json'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(urlsToCache))
    );
});

// Fetch event - serve from cache if available
self.addEventListener('fetch', (event) => {
    // Skip caching for authentication and API requests
    if (event.request.url.includes('accounts.google.com') ||
        event.request.url.includes('127.0.0.1:3000') ||
        event.request.url.includes('api') ||
        event.request.url.includes('.well-known')) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Return cached version or fetch from network
                return response || fetch(event.request);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Push event - handle incoming push notifications
self.addEventListener('push', (event) => {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body || 'A course you\'re tracking has an update!',
            icon: '/logo.png',
            badge: '/logo.png',
            vibrate: [200, 100, 200],
            data: {
                url: data.url || '/',
                crn: data.crn
            },
            actions: [
                {
                    action: 'view',
                    title: 'View Course',
                    icon: '/logo.png'
                },
                {
                    action: 'dismiss',
                    title: 'Dismiss'
                }
            ],
            requireInteraction: true,
            tag: data.crn ? `crn-${data.crn}` : 'reaper-notification'
        };

        event.waitUntil(
            self.registration.showNotification(data.title || 'Reaper', options)
        );
    }
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'view') {
        // Open the course in Oscar
        const url = event.notification.data.url;
        event.waitUntil(
            clients.openWindow(url)
        );
    } else if (event.action === 'dismiss') {
        // Just close the notification
        return;
    } else {
        // Default action - open the app
        event.waitUntil(
            clients.matchAll({ type: 'window' }).then((clientList) => {
                // Check if app is already open
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        return client.focus();
                    }
                }
                // If app is not open, open it
                if (clients.openWindow) {
                    return clients.openWindow('/');
                }
            })
        );
    }
});

// Background sync for offline functionality
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

function doBackgroundSync() {
    // This would handle background sync when connection is restored
    return Promise.resolve();
} 