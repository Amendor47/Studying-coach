// Base URL handler - Normalise les appels API
(function() {
    'use strict';
    
    // Configuration de base URL
    window.__BASE_URL__ = window.__BASE_URL__ || "";
    
    // Fonction pour obtenir la base URL
    function getBaseURL() {
        return window.__BASE_URL__ || "";
    }
    
    // Fonction pour normaliser une URL API
    function normalizeApiUrl(url) {
        // Si c'est déjà une URL complète, la retourner telle quelle
        if (url.startsWith('http://') || url.startsWith('https://')) {
            return url;
        }
        
        // Si c'est une URL relative commençant par /api/, ajouter la base URL
        if (url.startsWith('/api/')) {
            return getBaseURL() + url;
        }
        
        // Si c'est une URL relative sans /, l'ajouter
        if (!url.startsWith('/')) {
            url = '/' + url;
        }
        
        return getBaseURL() + url;
    }
    
    // Override du fetch global pour auto-normaliser les URLs
    const originalFetch = window.fetch;
    window.fetch = function(input, init) {
        // Si input est une string, la normaliser
        if (typeof input === 'string') {
            const normalizedUrl = normalizeApiUrl(input);
            console.debug('Fetch normalisé:', input, '=>', normalizedUrl);
            return originalFetch(normalizedUrl, init);
        }
        
        // Si input est un Request object
        if (input instanceof Request) {
            const normalizedUrl = normalizeApiUrl(input.url);
            if (normalizedUrl !== input.url) {
                console.debug('Request normalisé:', input.url, '=>', normalizedUrl);
                const newRequest = new Request(normalizedUrl, {
                    method: input.method,
                    headers: input.headers,
                    body: input.body,
                    mode: input.mode,
                    credentials: input.credentials,
                    cache: input.cache,
                    redirect: input.redirect,
                    referrer: input.referrer,
                    integrity: input.integrity
                });
                return originalFetch(newRequest, init);
            }
        }
        
        // Cas par défaut
        return originalFetch(input, init);
    };
    
    // API publique
    window.baseUrl = {
        get: getBaseURL,
        set: function(url) {
            window.__BASE_URL__ = url;
            console.info('Base URL définie:', url);
        },
        normalize: normalizeApiUrl
    };
    
    // Export pour les modules ES6 (si supporté)
    if (typeof window.exports === 'object') {
        window.exports.getBaseURL = getBaseURL;
        window.exports.normalizeApiUrl = normalizeApiUrl;
    }
    
    console.log('Base URL handler chargé - window.baseUrl disponible');
})();