// Base URL helper for API calls
(function() {
    'use strict';
    
    // Get base URL from window global or default to empty string
    function getBaseURL() {
        return window.__BASE_URL__ || "";
    }
    
    // Make it globally available
    window.getBaseURL = getBaseURL;
    
    console.log('Base URL helper initialized. Base URL:', getBaseURL());
})();