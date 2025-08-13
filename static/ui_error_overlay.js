// UI Error Overlay - Captures and displays JavaScript errors
(function() {
    'use strict';
    
    let errorOverlay = null;
    let errorCount = 0;
    
    function createErrorOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'ui-error-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: #ff4444;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            z-index: 10000;
            max-width: 400px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            cursor: pointer;
            transition: all 0.3s ease;
        `;
        overlay.title = 'Click to dismiss';
        
        overlay.addEventListener('click', function() {
            overlay.remove();
        });
        
        return overlay;
    }
    
    function showError(message, source, line, col, error) {
        errorCount++;
        
        if (!errorOverlay || !document.body.contains(errorOverlay)) {
            errorOverlay = createErrorOverlay();
            document.body.appendChild(errorOverlay);
        }
        
        const errorInfo = `
            <strong>JS Error #${errorCount}:</strong><br>
            ${message}<br>
            <small>${source}:${line}:${col}</small>
        `;
        
        errorOverlay.innerHTML = errorInfo;
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            if (errorOverlay && document.body.contains(errorOverlay)) {
                errorOverlay.remove();
            }
        }, 10000);
        
        console.error('UI Error Overlay captured:', { message, source, line, col, error });
    }
    
    // Capture window errors
    window.addEventListener('error', function(event) {
        showError(
            event.message || 'Unknown error',
            event.filename || 'unknown',
            event.lineno || 0,
            event.colno || 0,
            event.error
        );
    });
    
    // Capture unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
        const message = event.reason && event.reason.message ? event.reason.message : 'Unhandled Promise Rejection';
        showError(
            message,
            'promise',
            0,
            0,
            event.reason
        );
    });
    
    console.log('UI Error Overlay initialized');
})();