const CACHE_NAME = 'dokumentor-cache-v2';  // Increment to force update
const urlsToCache = [
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/js/main.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css'
];

// Install service worker
self.addEventListener('install', event => {
    console.log('[SW] Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Caching app shell');
                return cache.addAll(urlsToCache);
            })
            .then(() => {
                console.log('[SW] Installed successfully');
                return self.skipWaiting();
            })
    );
});

// Fetch from cache
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);
    
    // Skip caching for:
    // - API calls
    // - Login/register pages
    // - Any authenticated requests
    if (url.pathname.includes('/api/') || 
        url.pathname.includes('/login') || 
        url.pathname.includes('/register') ||
        event.request.headers.get('Cookie')) {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return cached version or fetch new
                return response || fetch(event.request);
            })
    );
});

// Update service worker
self.addEventListener('activate', event => {
    console.log('[SW] Activating...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[SW] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('[SW] Activated');
            return self.clients.claim();
        })
    );
});
