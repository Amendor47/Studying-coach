// degraded_mode.js - Support pour mode dégradé quand Ollama est indisponible
(function() {
    'use strict';
    
    let degradedMode = false;
    let mocksEnabled = false;
    
    // Mock responses for when LLM is not available
    const mockResponses = {
        improve: {
            "suggestions": [
                "Ajoutez des exemples concrets pour illustrer les concepts",
                "Structurez le contenu avec des titres et sous-titres clairs",
                "Utilisez des listes à puces pour les informations importantes",
                "Ajoutez des schémas ou diagrammes si applicable"
            ],
            "enhanced_text": "Version améliorée du texte avec une structure plus claire et des exemples pratiques.",
            "readability_score": 0.75,
            "word_count": 150,
            "mode": "mock"
        },
        analyze: {
            "drafts": [
                {
                    "kind": "card",
                    "payload": {
                        "type": "QA",
                        "theme": "Concept principal",
                        "front": "Qu'est-ce que le concept principal abordé dans ce texte?",
                        "back": "Le concept principal concerne [extrait du texte analysé]",
                        "difficulty": 1,
                        "tags": ["concept", "définition"]
                    }
                },
                {
                    "kind": "card", 
                    "payload": {
                        "type": "QCM",
                        "theme": "Compréhension",
                        "question": "Parmi les affirmations suivantes, laquelle est correcte?",
                        "choices": [
                            "Option A (correcte d'après le texte)",
                            "Option B (incorrecte)", 
                            "Option C (incorrecte)",
                            "Option D (incorrecte)"
                        ],
                        "answer": 0,
                        "difficulty": 2
                    }
                }
            ],
            "meta": {
                "readability": 0.7,
                "density": 0.6,
                "estimated_study_time": 15
            },
            "mode": "mock"
        }
    };
    
    // Détecter si on est en mode dégradé
    function checkDegradedMode() {
        fetch('/api/health/llm')
            .then(response => response.json())
            .then(data => {
                degradedMode = !data.ok;
                if (degradedMode) {
                    showDegradedModeNotice();
                    enableMocks();
                }
            })
            .catch(() => {
                degradedMode = true;
                showDegradedModeNotice();
                enableMocks();
            });
    }
    
    // Afficher notice de mode dégradé
    function showDegradedModeNotice() {
        const notice = document.createElement('div');
        notice.id = 'degraded-mode-notice';
        notice.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #ffc107, #fd7e14);
            color: #212529;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
            text-align: center;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(255, 193, 7, 0.3);
            border-bottom: 1px solid rgba(0,0,0,0.1);
        `;
        
        notice.innerHTML = `
            ⚠️ Mode dégradé actif - Ollama indisponible. 
            Fonctionnalités IA simulées pour démonstration.
            <button onclick="this.parentNode.style.display='none'" style="
                background: rgba(255,255,255,0.3); 
                border: none; 
                border-radius: 4px; 
                padding: 2px 8px; 
                margin-left: 10px;
                cursor: pointer;
            ">×</button>
        `;
        
        // Ajouter padding au body pour compenser
        document.body.style.paddingTop = '45px';
        
        document.body.insertBefore(notice, document.body.firstChild);
    }
    
    // Activer les mocks
    function enableMocks() {
        mocksEnabled = true;
        
        // Override fetch pour intercepter les appels API
        const originalFetch = window.fetch;
        window.fetch = function(url, options) {
            if (mocksEnabled && typeof url === 'string') {
                if (url.includes('/api/improve') || url.includes('/api/ai/analyze')) {
                    return Promise.resolve({
                        ok: true,
                        status: 200,
                        json: () => Promise.resolve(mockResponses.improve)
                    });
                }
                
                if (url.includes('/api/offline/analyze')) {
                    return Promise.resolve({
                        ok: true,
                        status: 200,
                        json: () => Promise.resolve(mockResponses.analyze)
                    });
                }
            }
            
            return originalFetch(url, options);
        };
        
        console.log('🎭 Mode dégradé activé - mocks AI enabled');
    }
    
    // Désactiver OCR par défaut si Tesseract absent
    function checkOCRAvailability() {
        const ocrCheckbox = document.getElementById('enable-advanced-analysis');
        if (ocrCheckbox) {
            // Laisser désactivé par défaut et ajouter un message
            ocrCheckbox.checked = false;
            const label = ocrCheckbox.closest('label');
            if (label && !label.querySelector('.ocr-warning')) {
                const warning = document.createElement('small');
                warning.className = 'ocr-warning';
                warning.style.cssText = 'display: block; color: #dc3545; margin-top: 4px;';
                warning.textContent = '⚠️ OCR désactivé par défaut (Tesseract requis)';
                label.appendChild(warning);
            }
        }
    }
    
    // Initialisation
    function init() {
        // Vérifier mode dégradé après un court délai
        setTimeout(checkDegradedMode, 1000);
        
        // Configurer OCR
        checkOCRAvailability();
    }
    
    // API publique
    window.degradedMode = {
        isEnabled: () => degradedMode,
        enableMocks: enableMocks,
        disableMocks: () => { mocksEnabled = false; },
        check: checkDegradedMode
    };
    
    // Initialiser quand le DOM est prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    console.log('🔧 Degraded mode support loaded');
})();