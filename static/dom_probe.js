// dom_probe.js - Sonde DOM interactive pour debugging
(function() {
    'use strict';
    
    let debugMode = false;
    let infoPanel = null;
    let debugControls = null;
    let currentMousePos = { x: 0, y: 0 };
    let lastHoveredElement = null;
    
    // Configuration
    const config = {
        hotkey: '`', // Touche backquote pour toggle
        updateInterval: 100, // ms
        maxStackDepth: 5
    };
    
    // Initialisation
    function init() {
        createInfoPanel();
        createDebugControls();
        setupEventListeners();
        
        console.log('🔍 DOM Probe initialisé - Appuyez sur ~ pour activer le debug');
    }
    
    // Créer le panneau d'informations
    function createInfoPanel() {
        infoPanel = document.createElement('div');
        infoPanel.className = 'debug-info-panel';
        infoPanel.innerHTML = `
            <h4>🔍 DOM Probe</h4>
            <div class="debug-item">
                <span class="debug-key">Mode:</span>
                <span class="debug-value" id="debug-mode-status">Inactif</span>
            </div>
            <div class="debug-item">
                <span class="debug-key">Élément:</span>
                <span class="debug-value" id="debug-current-element">Aucun</span>
            </div>
            <div class="debug-item">
                <span class="debug-key">Z-Index:</span>
                <span class="debug-value" id="debug-z-index">-</span>
            </div>
            <div class="debug-item">
                <span class="debug-key">Pointer:</span>
                <span class="debug-value" id="debug-pointer-events">-</span>
            </div>
            <div class="debug-item">
                <span class="debug-key">Position:</span>
                <span class="debug-value" id="debug-position">-</span>
            </div>
            <div class="debug-item">
                <span class="debug-key">Parents:</span>
                <div class="debug-value" id="debug-parents">-</div>
            </div>
        `;
        
        document.body.appendChild(infoPanel);
    }
    
    // Créer les contrôles de debug
    function createDebugControls() {
        debugControls = document.createElement('div');
        debugControls.className = 'debug-controls';
        debugControls.innerHTML = `
            <button class="debug-btn" id="debug-toggle-clickable">Surligner cliquables</button>
            <button class="debug-btn" id="debug-fix-overlays">Fixer overlays</button>
            <button class="debug-btn" id="debug-toggle-grid">Grille CSS</button>
            <button class="debug-btn" id="debug-contrast">Contraste</button>
        `;
        
        document.body.appendChild(debugControls);
        
        // Ajouter les event listeners pour les boutons
        setupControlListeners();
    }
    
    // Configurer les event listeners
    function setupEventListeners() {
        // Toggle debug avec la touche ~
        document.addEventListener('keydown', function(e) {
            if (e.key === config.hotkey && !e.ctrlKey && !e.altKey && !e.metaKey) {
                e.preventDefault();
                toggleDebugMode();
            }
        });
        
        // Suivre la souris
        document.addEventListener('mousemove', function(e) {
            if (!debugMode) return;
            
            currentMousePos.x = e.clientX;
            currentMousePos.y = e.clientY;
            
            // Throttle les mises à jour
            clearTimeout(this._updateTimer);
            this._updateTimer = setTimeout(updateDebugInfo, config.updateInterval);
        });
        
        // Clic pour actions de debug
        document.addEventListener('click', function(e) {
            if (!debugMode) return;
            
            // Si Ctrl+Click, proposer des actions
            if (e.ctrlKey) {
                e.preventDefault();
                showElementActions(e.target);
            }
        });
    }
    
    // Configurer les event listeners pour les contrôles
    function setupControlListeners() {
        const toggleClickable = debugControls.querySelector('#debug-toggle-clickable');
        const fixOverlays = debugControls.querySelector('#debug-fix-overlays');
        const toggleGrid = debugControls.querySelector('#debug-toggle-grid');
        const toggleContrast = debugControls.querySelector('#debug-contrast');
        
        toggleClickable.addEventListener('click', function() {
            const body = document.body;
            const isActive = body.hasAttribute('data-debug-clickable');
            
            if (isActive) {
                body.removeAttribute('data-debug-clickable');
                this.textContent = 'Surligner cliquables';
            } else {
                body.setAttribute('data-debug-clickable', 'true');
                this.textContent = 'Masquer surlignage';
            }
        });
        
        fixOverlays.addEventListener('click', fixOverlayPointerEvents);
        
        toggleGrid.addEventListener('click', function() {
            const body = document.body;
            const isActive = body.getAttribute('data-debug-grid') === 'true';
            
            if (isActive) {
                body.removeAttribute('data-debug-grid');
                this.textContent = 'Grille CSS';
            } else {
                body.setAttribute('data-debug-grid', 'true');
                this.textContent = 'Masquer grille';
            }
        });
        
        toggleContrast.addEventListener('click', function() {
            const body = document.body;
            const isActive = body.getAttribute('data-debug-contrast') === 'true';
            
            if (isActive) {
                body.removeAttribute('data-debug-contrast');
                this.textContent = 'Contraste';
            } else {
                body.setAttribute('data-debug-contrast', 'true');
                this.textContent = 'Contraste normal';
            }
        });
    }
    
    // Toggle le mode debug
    function toggleDebugMode() {
        debugMode = !debugMode;
        
        const body = document.body;
        const modeStatus = document.getElementById('debug-mode-status');
        
        if (debugMode) {
            body.setAttribute('data-debug', 'true');
            infoPanel.classList.add('show');
            debugControls.classList.add('show');
            modeStatus.textContent = 'Actif';
            modeStatus.style.color = '#28a745';
            
            // Commencer les mises à jour
            updateDebugInfo();
            
            console.log('🔍 Mode debug activé - Ctrl+Clic pour actions, touches ~ pour désactiver');
        } else {
            body.removeAttribute('data-debug');
            body.removeAttribute('data-debug-clickable');
            body.removeAttribute('data-debug-grid');
            body.removeAttribute('data-debug-contrast');
            infoPanel.classList.remove('show');
            debugControls.classList.remove('show');
            modeStatus.textContent = 'Inactif';
            modeStatus.style.color = '#6c757d';
            
            console.log('🔍 Mode debug désactivé');
        }
    }
    
    // Mettre à jour les informations de debug
    function updateDebugInfo() {
        if (!debugMode) return;
        
        const elementAtCursor = document.elementFromPoint(currentMousePos.x, currentMousePos.y);
        if (!elementAtCursor || elementAtCursor === lastHoveredElement) return;
        
        lastHoveredElement = elementAtCursor;
        
        const computedStyle = window.getComputedStyle(elementAtCursor);
        const parents = getParentChain(elementAtCursor);
        
        // Mettre à jour l'affichage
        document.getElementById('debug-current-element').textContent = getElementDescription(elementAtCursor);
        document.getElementById('debug-z-index').textContent = computedStyle.zIndex || 'auto';
        document.getElementById('debug-pointer-events').textContent = computedStyle.pointerEvents || 'auto';
        document.getElementById('debug-position').textContent = computedStyle.position || 'static';
        
        // Afficher la chaîne des parents
        const parentsDiv = document.getElementById('debug-parents');
        parentsDiv.innerHTML = parents.map(parent => {
            const parentStyle = window.getComputedStyle(parent.element);
            const zIndex = parentStyle.zIndex !== 'auto' ? ` z:${parentStyle.zIndex}` : '';
            const pointerEvents = parentStyle.pointerEvents !== 'auto' ? ` pe:${parentStyle.pointerEvents}` : '';
            
            return `<div style="margin: 2px 0; padding: 2px; background: rgba(255,255,255,0.1); font-size: 10px;">
                ${parent.tag}${parent.classes}${zIndex}${pointerEvents}
            </div>`;
        }).join('');
    }
    
    // Obtenir la description d'un élément
    function getElementDescription(element) {
        let desc = element.tagName.toLowerCase();
        
        if (element.id) desc += `#${element.id}`;
        if (element.className) {
            const classes = element.className.split(' ').filter(c => c.trim());
            if (classes.length > 0) {
                desc += '.' + classes.slice(0, 2).join('.');
                if (classes.length > 2) desc += '...';
            }
        }
        
        return desc;
    }
    
    // Obtenir la chaîne des parents
    function getParentChain(element, maxDepth = config.maxStackDepth) {
        const parents = [];
        let current = element.parentElement;
        let depth = 0;
        
        while (current && depth < maxDepth) {
            const classes = current.className ? 
                '.' + current.className.split(' ').filter(c => c.trim()).slice(0, 2).join('.') : '';
            
            parents.push({
                element: current,
                tag: current.tagName.toLowerCase(),
                classes: classes
            });
            
            current = current.parentElement;
            depth++;
        }
        
        return parents;
    }
    
    // Afficher les actions possibles pour un élément
    function showElementActions(element) {
        const computedStyle = window.getComputedStyle(element);
        const actions = [];
        
        // Détecter les problèmes potentiels
        if (computedStyle.pointerEvents === 'none') {
            actions.push({
                text: '🔧 Activer pointer-events',
                action: () => {
                    element.style.pointerEvents = 'auto';
                    console.log('✅ pointer-events activé sur', element);
                }
            });
        }
        
        if (computedStyle.position === 'fixed' || computedStyle.position === 'absolute') {
            const zIndex = parseInt(computedStyle.zIndex) || 0;
            if (zIndex > 1000) {
                actions.push({
                    text: '📉 Réduire z-index',
                    action: () => {
                        element.style.zIndex = '100';
                        console.log('✅ Z-index réduit sur', element);
                    }
                });
            }
        }
        
        if (computedStyle.display === 'none') {
            actions.push({
                text: '👁️ Afficher élément',
                action: () => {
                    element.style.display = 'block';
                    console.log('✅ Élément affiché', element);
                }
            });
        }
        
        // Afficher un menu contextuel
        if (actions.length > 0) {
            showActionMenu(actions, currentMousePos.x, currentMousePos.y);
        } else {
            console.log('ℹ️ Aucune action suggérée pour cet élément');
        }
    }
    
    // Afficher un menu d'actions
    function showActionMenu(actions, x, y) {
        // Supprimer le menu existant
        const existingMenu = document.querySelector('.debug-action-menu');
        if (existingMenu) existingMenu.remove();
        
        const menu = document.createElement('div');
        menu.className = 'debug-action-menu';
        menu.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            background: rgba(0, 0, 0, 0.95);
            border: 1px solid #00e0b8;
            border-radius: 4px;
            padding: 8px 0;
            z-index: 100003;
            font-family: monospace;
            font-size: 12px;
            min-width: 180px;
        `;
        
        actions.forEach(action => {
            const button = document.createElement('button');
            button.textContent = action.text;
            button.style.cssText = `
                display: block;
                width: 100%;
                padding: 6px 12px;
                background: transparent;
                color: #00e0b8;
                border: none;
                text-align: left;
                cursor: pointer;
                font-family: inherit;
                font-size: inherit;
            `;
            
            button.addEventListener('mouseover', () => {
                button.style.background = '#00e0b8';
                button.style.color = 'black';
            });
            
            button.addEventListener('mouseout', () => {
                button.style.background = 'transparent';
                button.style.color = '#00e0b8';
            });
            
            button.addEventListener('click', () => {
                action.action();
                menu.remove();
            });
            
            menu.appendChild(button);
        });
        
        document.body.appendChild(menu);
        
        // Supprimer le menu après 5 secondes
        setTimeout(() => {
            if (menu.parentNode) menu.remove();
        }, 5000);
    }
    
    // Fixer les overlays avec pointer-events: none
    function fixOverlayPointerEvents() {
        const overlaySelectors = [
            '.overlay', '.modal-backdrop', '.backdrop', '.loader', '.spinner',
            '[class*="overlay"]', '[class*="backdrop"]', '[class*="modal"]'
        ];
        
        let fixed = 0;
        
        overlaySelectors.forEach(selector => {
            try {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.position === 'fixed' || style.position === 'absolute') {
                        const zIndex = parseInt(style.zIndex) || 0;
                        if (zIndex > 100) {
                            el.style.pointerEvents = 'none';
                            fixed++;
                            console.log('🔧 Overlay fixed:', el);
                        }
                    }
                });
            } catch (e) {
                console.warn('Erreur avec sélecteur:', selector);
            }
        });
        
        if (fixed > 0) {
            console.log(`✅ ${fixed} overlay(s) fixé(s)`);
            if (window.uiErrorOverlay) {
                window.uiErrorOverlay.show(`${fixed} overlay(s) fixé(s) avec pointer-events: none`);
            }
        } else {
            console.log('ℹ️ Aucun overlay à fixer détecté');
        }
    }
    
    // API publique
    window.domProbe = {
        toggle: toggleDebugMode,
        fixOverlays: fixOverlayPointerEvents,
        isActive: () => debugMode
    };
    
    // Auto-initialisation
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    console.log('🔍 DOM Probe chargé - window.domProbe disponible');
})();