// UI Error Overlay - Affiche les erreurs JS dans un bandeau rouge
(function() {
    'use strict';
    
    let errorOverlay = null;
    let errorCount = 0;
    
    // Créer l'overlay d'erreur
    function createErrorOverlay() {
        if (errorOverlay) return;
        
        errorOverlay = document.createElement('div');
        errorOverlay.id = 'ui-error-overlay';
        errorOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #dc3545;
            color: white;
            padding: 12px 16px;
            font-family: monospace;
            font-size: 14px;
            z-index: 999999;
            border-bottom: 2px solid #c82333;
            transform: translateY(-100%);
            transition: transform 0.3s ease;
            cursor: pointer;
            display: none;
        `;
        
        // Clic pour fermer
        errorOverlay.addEventListener('click', hideErrorOverlay);
        
        // Ajouter au DOM
        document.documentElement.insertBefore(errorOverlay, document.documentElement.firstChild);
    }
    
    // Afficher une erreur
    function showError(message, source = '', lineno = '', colno = '', error = null) {
        createErrorOverlay();
        errorCount++;
        
        let errorHtml = `
            <strong>🚨 Erreur JS (#${errorCount}):</strong> ${message}
        `;
        
        if (source) {
            const filename = source.split('/').pop();
            errorHtml += `<br><small>📁 ${filename}:${lineno}:${colno}</small>`;
        }
        
        if (error && error.stack) {
            const shortStack = error.stack.split('\n').slice(0, 3).join('\n');
            errorHtml += `<br><small>📋 ${shortStack}</small>`;
        }
        
        errorHtml += `<br><small>👆 Cliquez pour fermer</small>`;
        
        errorOverlay.innerHTML = errorHtml;
        errorOverlay.style.display = 'block';
        
        // Animation d'entrée
        setTimeout(() => {
            errorOverlay.style.transform = 'translateY(0)';
        }, 10);
        
        // Auto-hide après 10 secondes
        setTimeout(hideErrorOverlay, 10000);
        
        console.error('UI Error Overlay:', message, {source, lineno, colno, error});
    }
    
    // Masquer l'overlay
    function hideErrorOverlay() {
        if (!errorOverlay) return;
        
        errorOverlay.style.transform = 'translateY(-100%)';
        setTimeout(() => {
            if (errorOverlay) {
                errorOverlay.style.display = 'none';
            }
        }, 300);
    }
    
    // Intercepter les erreurs globales
    window.addEventListener('error', function(event) {
        showError(
            event.message || 'Erreur JavaScript inconnue',
            event.filename || '',
            event.lineno || '',
            event.colno || '',
            event.error
        );
    });
    
    // Intercepter les promesses rejetées
    window.addEventListener('unhandledrejection', function(event) {
        const reason = event.reason;
        let message = 'Promise rejetée';
        
        if (reason instanceof Error) {
            message = reason.message;
        } else if (typeof reason === 'string') {
            message = reason;
        } else {
            message = 'Promise rejetée: ' + JSON.stringify(reason);
        }
        
        showError(message, '', '', '', reason);
        
        // Empêcher l'affichage par défaut dans la console
        event.preventDefault();
    });
    
    // API publique pour afficher des erreurs custom
    window.uiErrorOverlay = {
        show: showError,
        hide: hideErrorOverlay,
        clear: function() {
            errorCount = 0;
            hideErrorOverlay();
        }
    };
    
    console.log('UI Error Overlay chargé - window.uiErrorOverlay disponible');
})();