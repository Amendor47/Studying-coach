// service-worker.js - Advanced PWA Service Worker with Intelligent Caching
// Provides offline-first experience with intelligent resource management

const CACHE_NAME = 'study-coach-v1';
const API_CACHE_NAME = 'study-coach-api-v1';
const STATIC_CACHE_NAME = 'study-coach-static-v1';

// Resources to cache immediately on install
const STATIC_RESOURCES = [
  '/',
  '/static/style.css',
  '/static/advanced-flashcards.css',
  '/static/advanced-flashcards.js',
  '/static/app.js',
  '/static/manifest.json',
  // Add other static resources
];

// API endpoints that can be cached
const CACHEABLE_API_PATTERNS = [
  /^\/api\/health\//,
  /^\/api\/themes$/,
  /^\/api\/config$/,
  /^\/api\/offline\/analyze$/,
];

// API endpoints that should never be cached
const NON_CACHEABLE_API_PATTERNS = [
  /^\/api\/upload$/,
  /^\/api\/save$/,
  /^\/api\/review\//,
  /^\/api\/advanced\/learning_interaction$/,
];

// Network timeout for cache-first strategies
const NETWORK_TIMEOUT = 3000; // 3 seconds

class AdvancedServiceWorker {
  constructor() {
    this.setupEventListeners();
  }

  setupEventListeners() {
    self.addEventListener('install', this.handleInstall.bind(this));
    self.addEventListener('activate', this.handleActivate.bind(this));
    self.addEventListener('fetch', this.handleFetch.bind(this));
    self.addEventListener('message', this.handleMessage.bind(this));
    self.addEventListener('sync', this.handleBackgroundSync.bind(this));
    self.addEventListener('push', this.handlePushNotification.bind(this));
  }

  async handleInstall(event) {
    console.log('[SW] Installing service worker...');
    
    event.waitUntil(
      this.preloadCriticalResources()
    );
    
    // Skip waiting to activate immediately
    self.skipWaiting();
  }

  async preloadCriticalResources() {
    try {
      const staticCache = await caches.open(STATIC_CACHE_NAME);
      
      // Pre-cache critical resources
      await staticCache.addAll(STATIC_RESOURCES);
      
      console.log('[SW] Critical resources cached');
    } catch (error) {
      console.error('[SW] Failed to cache critical resources:', error);
    }
  }

  async handleActivate(event) {
    console.log('[SW] Activating service worker...');
    
    event.waitUntil(
      Promise.all([
        this.cleanupOldCaches(),
        self.clients.claim()
      ])
    );
  }

  async cleanupOldCaches() {
    const cacheNames = await caches.keys();
    const oldCacheNames = cacheNames.filter(name => 
      name.startsWith('study-coach-') && 
      ![CACHE_NAME, API_CACHE_NAME, STATIC_CACHE_NAME].includes(name)
    );
    
    await Promise.all(
      oldCacheNames.map(name => caches.delete(name))
    );
    
    console.log('[SW] Old caches cleaned up');
  }

  handleFetch(event) {
    const { request } = event;
    
    // Handle different types of requests with appropriate strategies
    if (this.isApiRequest(request)) {
      event.respondWith(this.handleApiRequest(request));
    } else if (this.isStaticResource(request)) {
      event.respondWith(this.handleStaticRequest(request));
    } else if (this.isNavigationRequest(request)) {
      event.respondWith(this.handleNavigationRequest(request));
    } else {
      // Default: network first with cache fallback
      event.respondWith(this.networkFirstStrategy(request));
    }
  }

  isApiRequest(request) {
    return request.url.includes('/api/');
  }

  isStaticResource(request) {
    return request.url.includes('/static/') || 
           request.destination === 'style' ||
           request.destination === 'script' ||
           request.destination === 'font';
  }

  isNavigationRequest(request) {
    return request.mode === 'navigate';
  }

  isCacheableApiRequest(request) {
    const url = new URL(request.url);
    return CACHEABLE_API_PATTERNS.some(pattern => 
      pattern.test(url.pathname)
    );
  }

  isNonCacheableApiRequest(request) {
    const url = new URL(request.url);
    return NON_CACHEABLE_API_PATTERNS.some(pattern => 
      pattern.test(url.pathname)
    );
  }

  async handleApiRequest(request) {
    // Never cache certain API requests
    if (this.isNonCacheableApiRequest(request)) {
      return this.networkOnlyStrategy(request);
    }

    // Cache certain API requests with stale-while-revalidate
    if (this.isCacheableApiRequest(request)) {
      return this.staleWhileRevalidateStrategy(request, API_CACHE_NAME);
    }

    // Default: network first with cache fallback
    return this.networkFirstStrategy(request, API_CACHE_NAME);
  }

  async handleStaticRequest(request) {
    // Static resources: cache first with network fallback
    return this.cacheFirstStrategy(request, STATIC_CACHE_NAME);
  }

  async handleNavigationRequest(request) {
    // Navigation: network first, cache fallback, offline page as last resort
    try {
      // Try network first
      const networkResponse = await this.fetchWithTimeout(request, NETWORK_TIMEOUT);
      
      // Cache the response
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
      
      return networkResponse;
    } catch (error) {
      // Try cache
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        return cachedResponse;
      }
      
      // Return offline page
      return this.getOfflinePage();
    }
  }

  async networkOnlyStrategy(request) {
    try {
      return await fetch(request);
    } catch (error) {
      // Return error response for API requests
      return new Response(
        JSON.stringify({ error: 'Network unavailable' }),
        {
          status: 503,
          statusText: 'Service Unavailable',
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }
  }

  async networkFirstStrategy(request, cacheName = CACHE_NAME) {
    try {
      const networkResponse = await this.fetchWithTimeout(request, NETWORK_TIMEOUT);
      
      // Cache successful responses
      if (networkResponse.ok) {
        const cache = await caches.open(cacheName);
        cache.put(request, networkResponse.clone());
      }
      
      return networkResponse;
    } catch (error) {
      // Fallback to cache
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        console.log('[SW] Serving from cache:', request.url);
        return cachedResponse;
      }
      
      throw error;
    }
  }

  async cacheFirstStrategy(request, cacheName = STATIC_CACHE_NAME) {
    // Try cache first
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('[SW] Serving from cache:', request.url);
      return cachedResponse;
    }

    // Fallback to network and cache
    try {
      const networkResponse = await fetch(request);
      
      if (networkResponse.ok) {
        const cache = await caches.open(cacheName);
        cache.put(request, networkResponse.clone());
      }
      
      return networkResponse;
    } catch (error) {
      console.error('[SW] Failed to fetch:', request.url, error);
      throw error;
    }
  }

  async staleWhileRevalidateStrategy(request, cacheName = API_CACHE_NAME) {
    const cache = await caches.open(cacheName);
    const cachedResponse = cache.match(request);
    
    // Always try to fetch fresh data in background
    const networkResponse = fetch(request).then(response => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    }).catch(error => {
      console.log('[SW] Network failed, using cache:', request.url);
      return null;
    });

    // Return cached response immediately if available, otherwise wait for network
    const cached = await cachedResponse;
    if (cached) {
      console.log('[SW] Serving stale from cache:', request.url);
      return cached;
    }

    return networkResponse;
  }

  async fetchWithTimeout(request, timeout = NETWORK_TIMEOUT) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(request, {
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  async getOfflinePage() {
    // Return a simple offline page
    const offlineHTML = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Study Coach - Offline</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0d12;
            color: #e9eef5;
            text-align: center;
            padding: 2rem;
            margin: 0;
          }
          .offline-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 3rem 2rem;
          }
          .offline-icon {
            font-size: 4rem;
            margin-bottom: 2rem;
          }
          .offline-title {
            font-size: 2rem;
            margin-bottom: 1rem;
            color: #00e0b8;
          }
          .offline-message {
            font-size: 1.2rem;
            margin-bottom: 2rem;
            opacity: 0.8;
            line-height: 1.6;
          }
          .retry-btn {
            background: #00e0b8;
            color: #0a0d12;
            border: none;
            padding: 1rem 2rem;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
          }
          .retry-btn:hover {
            background: #78ffe8;
          }
        </style>
      </head>
      <body>
        <div class="offline-container">
          <div class="offline-icon">📚</div>
          <h1 class="offline-title">Mode hors-ligne</h1>
          <p class="offline-message">
            Vous êtes actuellement hors-ligne. Certaines fonctionnalités peuvent être limitées, 
            mais vos révisions en cours sont sauvegardées localement.
          </p>
          <button class="retry-btn" onclick="window.location.reload()">
            Réessayer la connexion
          </button>
        </div>
      </body>
      </html>
    `;

    return new Response(offlineHTML, {
      status: 200,
      statusText: 'OK',
      headers: { 'Content-Type': 'text/html' }
    });
  }

  handleMessage(event) {
    const { type, payload } = event.data;

    switch (type) {
      case 'SKIP_WAITING':
        self.skipWaiting();
        break;
        
      case 'CLEAR_CACHE':
        this.clearAllCaches().then(() => {
          event.ports[0].postMessage({ success: true });
        });
        break;
        
      case 'PRELOAD_RESOURCES':
        this.preloadResources(payload.resources).then(() => {
          event.ports[0].postMessage({ success: true });
        });
        break;
        
      case 'GET_CACHE_STATUS':
        this.getCacheStatus().then(status => {
          event.ports[0].postMessage({ status });
        });
        break;
    }
  }

  async clearAllCaches() {
    const cacheNames = await caches.keys();
    await Promise.all(
      cacheNames.map(name => caches.delete(name))
    );
    console.log('[SW] All caches cleared');
  }

  async preloadResources(resources) {
    const cache = await caches.open(CACHE_NAME);
    await Promise.all(
      resources.map(resource => {
        return fetch(resource).then(response => {
          if (response.ok) {
            cache.put(resource, response);
          }
        }).catch(error => {
          console.log('[SW] Failed to preload:', resource, error);
        });
      })
    );
  }

  async getCacheStatus() {
    const cacheNames = await caches.keys();
    const status = {};
    
    for (const name of cacheNames) {
      const cache = await caches.open(name);
      const keys = await cache.keys();
      status[name] = keys.length;
    }
    
    return status;
  }

  handleBackgroundSync(event) {
    console.log('[SW] Background sync:', event.tag);
    
    if (event.tag === 'learning-data-sync') {
      event.waitUntil(this.syncLearningData());
    }
  }

  async syncLearningData() {
    // Sync any pending learning interactions when back online
    try {
      // Get pending data from IndexedDB
      const pendingData = await this.getPendingLearningData();
      
      for (const data of pendingData) {
        await fetch('/api/advanced/learning_interaction', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
      }
      
      // Clear pending data after successful sync
      await this.clearPendingLearningData();
      
      console.log('[SW] Learning data synced successfully');
    } catch (error) {
      console.error('[SW] Failed to sync learning data:', error);
    }
  }

  async getPendingLearningData() {
    // This would integrate with IndexedDB to get pending data
    // For now, return empty array
    return [];
  }

  async clearPendingLearningData() {
    // This would clear pending data from IndexedDB
    console.log('[SW] Pending learning data cleared');
  }

  handlePushNotification(event) {
    console.log('[SW] Push notification received:', event);
    
    const options = {
      body: 'Il est temps de réviser vos cartes!',
      icon: '/static/icon-192x192.png',
      badge: '/static/icon-72x72.png',
      tag: 'study-reminder',
      renotify: true,
      requireInteraction: true,
      actions: [
        {
          action: 'review',
          title: 'Commencer les révisions'
        },
        {
          action: 'snooze',
          title: 'Reporter (30 min)'
        }
      ]
    };

    event.waitUntil(
      self.registration.showNotification('Study Coach', options)
    );
  }
}

// Initialize the service worker
new AdvancedServiceWorker();

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'review') {
    // Open the app to review page
    event.waitUntil(
      clients.openWindow('/#flash')
    );
  } else if (event.action === 'snooze') {
    // Schedule another notification in 30 minutes
    // This would integrate with the push service
    console.log('[SW] Notification snoozed');
  }
});