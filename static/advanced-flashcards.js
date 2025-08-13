// Advanced Flashcard System with Hardware-Accelerated Animations
// Supports multiple card types, gestures, and spaced repetition optimization

class AdvancedFlashcardSystem {
    constructor(options = {}) {
        this.options = {
            enableGestures: true,
            enableAnimations: true,
            enableAudio: false,
            animationDuration: 300,
            stackSize: 4,
            autoAdvance: false,
            autoAdvanceDelay: 3000,
            enableKeyboard: true,
            enableHaptics: true,
            enableDragReorder: true,
            ...options
        };
        
        this.currentCard = 0;
        this.cards = [];
        this.isFlipped = false;
        this.isAnimating = false;
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.isDragging = false;
        this.dragStartIndex = -1;
        this.dragOverIndex = -1;
        
        this.initializeEventListeners();
        this.loadSettings();
    }
    
    initializeEventListeners() {
        // Keyboard controls
        if (this.options.enableKeyboard) {
            document.addEventListener('keydown', this.handleKeypress.bind(this));
        }
        
        // Global touch events for gestures
        if (this.options.enableGestures) {
            document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
            document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
            document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
        }
        
        // Pointer events for unified mouse/touch handling
        document.addEventListener('pointerdown', this.handlePointerDown.bind(this));
        document.addEventListener('pointermove', this.handlePointerMove.bind(this));
        document.addEventListener('pointerup', this.handlePointerUp.bind(this));
        
        // Visibility change handling
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
        
        // Resize handling for responsive design
        window.addEventListener('resize', this.handleResize.bind(this));
    }
    
    loadSettings() {
        // Load user preferences from localStorage
        const settings = JSON.parse(localStorage.getItem('flashcard_settings') || '{}');
        this.options = { ...this.options, ...settings };
    }
    
    saveSettings() {
        localStorage.setItem('flashcard_settings', JSON.stringify(this.options));
    }
    
    // ===== CARD MANAGEMENT =====
    
    loadCards(cardData) {
        this.cards = cardData.map((card, index) => ({
            ...card,
            id: card.id || `card_${index}`,
            type: card.type || 'basic',
            difficulty: card.difficulty || 'medium',
            srsData: card.srsData || { interval: 1, easeFactor: 2.5, repetitions: 0 },
            views: card.views || 0,
            lastViewed: card.lastViewed || null,
            createdAt: card.createdAt || new Date().toISOString()
        }));
        
        this.currentCard = 0;
        this.renderCurrentCard();
        this.updateProgress();
    }
    
    getCurrentCard() {
        return this.cards[this.currentCard] || null;
    }
    
    getNextCards(count = 3) {
        const nextCards = [];
        for (let i = 1; i <= count && this.currentCard + i < this.cards.length; i++) {
            nextCards.push(this.cards[this.currentCard + i]);
        }
        return nextCards;
    }
    
    // ===== RENDERING =====
    
    renderCurrentCard() {
        const container = document.getElementById('flashcard-container');
        if (!container) return;
        
        const card = this.getCurrentCard();
        if (!card) {
            this.renderEmptyState(container);
            return;
        }
        
        const cardHTML = this.generateCardHTML(card);
        container.innerHTML = cardHTML;
        
        // Add event listeners to the new card
        this.attachCardEventListeners(container);
        
        // Render card stack preview
        this.renderCardStack();
        
        // Update metadata
        this.updateCardMetadata(card);
        
        // Apply entrance animation
        if (this.options.enableAnimations) {
            this.applyEntranceAnimation(container);
        }
    }
    
    generateCardHTML(card) {
        const difficultyClass = `difficulty-${card.difficulty}`;
        const cardTypeClass = `flashcard-type-${card.type}`;
        const srsClass = `srs-${this.getSRSState(card.srsData)}`;
        
        return `
            <div class="flashcard-deck">
                <div class="flashcard-stack">
                    <div class="flashcard-container ${cardTypeClass}" data-card-id="${card.id}">
                        <div class="flashcard ${difficultyClass}">
                            <div class="flashcard-side flashcard-front">
                                <div class="difficulty-indicator ${difficultyClass}">
                                    <div class="difficulty-dot"></div>
                                    <div class="difficulty-dot"></div>
                                    <div class="difficulty-dot"></div>
                                </div>
                                <div class="flashcard-content">
                                    ${this.renderCardContent(card, 'front')}
                                </div>
                                <div class="srs-indicator ${srsClass}">
                                    <div class="srs-dot"></div>
                                    <span>${this.getSRSLabel(card.srsData)}</span>
                                </div>
                            </div>
                            <div class="flashcard-side flashcard-back">
                                <div class="flashcard-content">
                                    ${this.renderCardContent(card, 'back')}
                                </div>
                                <div class="flashcard-controls">
                                    <button class="flashcard-btn btn-again" data-quality="1">
                                        😕 Encore
                                    </button>
                                    <button class="flashcard-btn btn-hard" data-quality="2">
                                        😐 Difficile
                                    </button>
                                    <button class="flashcard-btn btn-good" data-quality="3">
                                        😊 Bien
                                    </button>
                                    <button class="flashcard-btn btn-easy" data-quality="4">
                                        😄 Facile
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderCardContent(card, side) {
        const content = card[side] || '';
        
        switch (card.type) {
            case 'basic':
                return this.renderBasicCard(content, side);
            case 'cloze':
                return this.renderClozeCard(content, side);
            case 'image_occlusion':
                return this.renderImageOcclusionCard(content, side);
            case 'audio':
                return this.renderAudioCard(content, side);
            case 'formula':
                return this.renderFormulaCard(content, side);
            default:
                return this.renderBasicCard(content, side);
        }
    }
    
    renderBasicCard(content, side) {
        return `
            <div class="flashcard-title">
                ${content.title || (side === 'front' ? 'Question' : 'Réponse')}
            </div>
            <div class="flashcard-text">
                ${content.text || content}
            </div>
        `;
    }
    
    renderClozeCard(content, side) {
        if (side === 'front') {
            // Show text with blanks
            return `
                <div class="flashcard-title">Compléter</div>
                <div class="flashcard-text">
                    ${this.renderClozeText(content.text, true)}
                </div>
            `;
        } else {
            // Show complete text
            return `
                <div class="flashcard-title">Solution</div>
                <div class="flashcard-text">
                    ${this.renderClozeText(content.text, false)}
                </div>
            `;
        }
    }
    
    renderClozeText(text, showBlanks) {
        // Replace {{c1::answer}} with blanks or answers
        return text.replace(/\{\{c\d+::([^}]+)\}\}/g, (match, answer) => {
            if (showBlanks) {
                return `<span class="cloze-blank" data-answer="${answer}">_____</span>`;
            } else {
                return `<span class="cloze-answer">${answer}</span>`;
            }
        });
    }
    
    renderImageOcclusionCard(content, side) {
        if (side === 'front') {
            return `
                <div class="flashcard-title">Identifier</div>
                <div class="image-occlusion-container">
                    <img src="${content.image}" alt="Diagram" style="max-width: 100%; height: auto;">
                    ${content.occlusions.map((occlusion, index) => `
                        <div class="occlusion-overlay" 
                             style="left: ${occlusion.x}%; top: ${occlusion.y}%; 
                                    width: ${occlusion.w}%; height: ${occlusion.h}%;"
                             data-label="${occlusion.label}">
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            return `
                <div class="flashcard-title">Solution</div>
                <div class="image-occlusion-container">
                    <img src="${content.image}" alt="Diagram" style="max-width: 100%; height: auto;">
                    <div class="occlusion-labels">
                        ${content.occlusions.map(occlusion => `
                            <div class="occlusion-label">${occlusion.label}</div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
    }
    
    renderAudioCard(content, side) {
        if (side === 'front') {
            return `
                <div class="flashcard-title">Écouter</div>
                <div class="audio-controls">
                    <button class="audio-btn" onclick="this.parentNode.querySelector('audio').play()">
                        ▶️
                    </button>
                    <audio src="${content.audio}" preload="metadata"></audio>
                </div>
                <div class="flashcard-text">${content.question || 'Que signifie ce son?'}</div>
            `;
        } else {
            return `
                <div class="flashcard-title">Réponse</div>
                <div class="flashcard-text">${content.answer}</div>
                ${content.audio ? `
                    <div class="audio-controls">
                        <button class="audio-btn" onclick="this.parentNode.querySelector('audio').play()">
                            🔁
                        </button>
                        <audio src="${content.audio}" preload="metadata"></audio>
                    </div>
                ` : ''}
            `;
        }
    }
    
    renderFormulaCard(content, side) {
        if (side === 'front') {
            return `
                <div class="flashcard-title">Formule</div>
                <div class="flashcard-formula">
                    ${content.formula || content.question}
                </div>
            `;
        } else {
            return `
                <div class="flashcard-title">Solution</div>
                <div class="flashcard-text">${content.explanation}</div>
                ${content.steps ? `
                    <div class="formula-steps">
                        ${content.steps.map((step, index) => `
                            <div class="formula-step">
                                <strong>Étape ${index + 1}:</strong> ${step}
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            `;
        }
    }
    
    renderCardStack() {
        const nextCards = this.getNextCards(this.options.stackSize - 1);
        const stackContainer = document.querySelector('.flashcard-stack');
        
        if (!stackContainer || nextCards.length === 0) return;
        
        // Remove existing stack cards
        const existingStackCards = stackContainer.querySelectorAll('.flashcard-container:not(:first-child)');
        existingStackCards.forEach(card => card.remove());
        
        // Add preview cards to stack
        nextCards.forEach((card, index) => {
            const cardElement = document.createElement('div');
            cardElement.className = 'flashcard-container stack-preview';
            cardElement.innerHTML = `
                <div class="flashcard">
                    <div class="flashcard-side flashcard-front">
                        <div class="flashcard-content">
                            <div class="flashcard-title">Suivant ${index + 1}</div>
                        </div>
                    </div>
                </div>
            `;
            stackContainer.appendChild(cardElement);
        });
    }
    
    renderEmptyState(container) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📚</div>
                <div class="empty-state-title">Aucune carte à réviser</div>
                <div class="empty-state-text">
                    Félicitations ! Vous avez terminé toutes vos révisions.
                </div>
            </div>
        `;
    }
    
    // ===== ANIMATIONS =====
    
    applyEntranceAnimation(container) {
        const animations = ['card-enter-slide', 'card-enter-flip', 'card-enter-scale'];
        const randomAnimation = animations[Math.floor(Math.random() * animations.length)];
        
        const flashcard = container.querySelector('.flashcard-container');
        if (flashcard) {
            flashcard.classList.add(randomAnimation);
            
            setTimeout(() => {
                flashcard.classList.remove(randomAnimation);
            }, this.options.animationDuration);
        }
    }
    
    flipCard() {
        if (this.isAnimating) return;
        
        this.isAnimating = true;
        const flashcard = document.querySelector('.flashcard');
        
        if (flashcard) {
            this.isFlipped = !this.isFlipped;
            flashcard.classList.toggle('flipped', this.isFlipped);
            
            // Trigger haptic feedback
            if (this.options.enableHaptics && navigator.vibrate) {
                navigator.vibrate(50);
            }
            
            setTimeout(() => {
                this.isAnimating = false;
            }, this.options.animationDuration);
        }
    }
    
    // ===== INTERACTION HANDLING =====
    
    attachCardEventListeners(container) {
        const flashcard = container.querySelector('.flashcard-container');
        const controlButtons = container.querySelectorAll('.flashcard-btn');
        const clozeElements = container.querySelectorAll('.cloze-blank');
        const occlusionElements = container.querySelectorAll('.occlusion-overlay');
        
        // Card click to flip
        if (flashcard) {
            flashcard.addEventListener('click', (e) => {
                // Don't flip if clicking on controls
                if (!e.target.closest('.flashcard-controls') && 
                    !e.target.closest('.cloze-blank') && 
                    !e.target.closest('.occlusion-overlay')) {
                    this.flipCard();
                }
            });
        }
        
        // Control button handlers
        controlButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const quality = parseInt(button.dataset.quality);
                this.handleCardResponse(quality);
            });
        });
        
        // Cloze deletion interactions
        clozeElements.forEach(element => {
            element.addEventListener('click', (e) => {
                e.stopPropagation();
                element.classList.toggle('revealed');
                element.textContent = element.classList.contains('revealed') 
                    ? element.dataset.answer 
                    : '_____';
            });
        });
        
        // Image occlusion interactions
        occlusionElements.forEach(element => {
            element.addEventListener('click', (e) => {
                e.stopPropagation();
                element.classList.add('revealed');
                
                // Show label
                const label = document.createElement('div');
                label.className = 'occlusion-label-popup';
                label.textContent = element.dataset.label;
                label.style.position = 'absolute';
                label.style.top = '50%';
                label.style.left = '50%';
                label.style.transform = 'translate(-50%, -50%)';
                label.style.background = 'var(--accent)';
                label.style.color = 'var(--bg)';
                label.style.padding = '0.5rem 1rem';
                label.style.borderRadius = 'var(--radius)';
                label.style.fontSize = '0.875rem';
                label.style.fontWeight = '600';
                label.style.zIndex = '10';
                
                element.appendChild(label);
                
                setTimeout(() => {
                    label.remove();
                }, 2000);
            });
        });
    }
    
    handleCardResponse(quality) {
        const card = this.getCurrentCard();
        if (!card) return;
        
        // Update SRS data
        this.updateSRSData(card, quality);
        
        // Record interaction
        this.recordInteraction(card, quality);
        
        // Move to next card
        this.nextCard();
    }
    
    // ===== GESTURE HANDLING =====
    
    handleTouchStart(e) {
        if (!this.options.enableGestures) return;
        
        const touch = e.touches[0];
        this.touchStartX = touch.clientX;
        this.touchStartY = touch.clientY;
        this.isDragging = false;
    }
    
    handleTouchMove(e) {
        if (!this.options.enableGestures) return;
        
        const touch = e.touches[0];
        const deltaX = touch.clientX - this.touchStartX;
        const deltaY = touch.clientY - this.touchStartY;
        
        // Check if this is a horizontal swipe (not vertical scroll)
        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
            e.preventDefault();
            this.isDragging = true;
            
            const container = document.querySelector('.flashcard-container');
            if (container) {
                container.classList.add('swiping');
                
                if (deltaX > 0) {
                    container.classList.add('swipe-right');
                    container.classList.remove('swipe-left');
                } else {
                    container.classList.add('swipe-left');
                    container.classList.remove('swipe-right');
                }
            }
        }
    }
    
    handleTouchEnd(e) {
        if (!this.options.enableGestures || !this.isDragging) return;
        
        const touch = e.changedTouches[0];
        const deltaX = touch.clientX - this.touchStartX;
        const container = document.querySelector('.flashcard-container');
        
        if (container) {
            container.classList.remove('swiping', 'swipe-left', 'swipe-right');
        }
        
        // Handle swipe actions
        if (Math.abs(deltaX) > 100) {
            if (deltaX > 0) {
                // Swipe right - easy/good
                this.handleCardResponse(3);
            } else {
                // Swipe left - again/hard
                this.handleCardResponse(1);
            }
        }
        
        this.isDragging = false;
    }
    
    // ===== POINTER EVENTS FOR UNIFIED MOUSE/TOUCH DRAG & DROP =====
    
    handlePointerDown(e) {
        if (!this.options.enableDragReorder) return;
        
        const dragHandle = e.target.closest('.drag-handle');
        if (!dragHandle) return;
        
        e.preventDefault();
        
        const cardElement = dragHandle.closest('.flashcard-item');
        if (!cardElement) return;
        
        this.dragStartIndex = parseInt(cardElement.dataset.index);
        this.isDragging = true;
        
        // Add dragging class for visual feedback
        cardElement.classList.add('dragging');
        document.body.classList.add('drag-active');
        
        // Store initial pointer position
        this.pointerStartX = e.clientX;
        this.pointerStartY = e.clientY;
        
        // Set up drag image (optional)
        if (e.dataTransfer) {
            const dragImage = cardElement.cloneNode(true);
            dragImage.style.transform = 'rotate(5deg)';
            dragImage.style.opacity = '0.8';
            e.dataTransfer.setDragImage(dragImage, e.offsetX, e.offsetY);
        }
    }
    
    handlePointerMove(e) {
        if (!this.isDragging || !this.options.enableDragReorder) return;
        
        e.preventDefault();
        
        // Check if this is a significant drag (not just a tap)
        const deltaX = Math.abs(e.clientX - this.pointerStartX);
        const deltaY = Math.abs(e.clientY - this.pointerStartY);
        
        if (deltaX < 5 && deltaY < 5) return;
        
        // Find the element we're dragging over
        const elementBelow = document.elementFromPoint(e.clientX, e.clientY);
        const cardBelow = elementBelow?.closest('.flashcard-item');
        
        if (cardBelow && cardBelow.dataset.index) {
            const overIndex = parseInt(cardBelow.dataset.index);
            
            if (overIndex !== this.dragOverIndex) {
                // Remove previous drag-over class
                document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
                
                // Add drag-over class to new target
                cardBelow.classList.add('drag-over');
                this.dragOverIndex = overIndex;
            }
        }
    }
    
    handlePointerUp(e) {
        if (!this.isDragging || !this.options.enableDragReorder) return;
        
        e.preventDefault();
        
        // Clean up visual feedback
        document.querySelectorAll('.dragging, .drag-over').forEach(el => {
            el.classList.remove('dragging', 'drag-over');
        });
        document.body.classList.remove('drag-active');
        
        // Perform reorder if valid
        if (this.dragOverIndex >= 0 && this.dragStartIndex !== this.dragOverIndex) {
            this.reorderCard(this.dragStartIndex, this.dragOverIndex);
        }
        
        // Reset drag state
        this.isDragging = false;
        this.dragStartIndex = -1;
        this.dragOverIndex = -1;
    }
    
    // ===== DRAG & DROP REORDERING =====
    
    reorderCard(fromIndex, toIndex) {
        if (fromIndex < 0 || toIndex < 0 || fromIndex >= this.cards.length || toIndex >= this.cards.length) {
            return;
        }
        
        // Move card in local array
        const [movedCard] = this.cards.splice(fromIndex, 1);
        this.cards.splice(toIndex, 0, movedCard);
        
        // Update current card index if necessary
        if (this.currentCard === fromIndex) {
            this.currentCard = toIndex;
        } else if (fromIndex < this.currentCard && toIndex >= this.currentCard) {
            this.currentCard--;
        } else if (fromIndex > this.currentCard && toIndex <= this.currentCard) {
            this.currentCard++;
        }
        
        // Re-render the card list
        this.renderCardList();
        
        // Persist to backend
        this.persistCardOrder();
        
        // Visual feedback
        this.showReorderFeedback(`Card moved from position ${fromIndex + 1} to ${toIndex + 1}`);
    }
    
    persistCardOrder() {
        // Get current deck/theme
        const currentCard = this.getCurrentCard();
        const deckId = currentCard?.theme || 'default';
        
        // Build order array
        const order = this.cards.map(card => card.id || card.title || `card_${this.cards.indexOf(card)}`);
        
        // Send to backend
        fetch(`${getBaseURL()}/api/flashcards/reorder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                deck_id: deckId,
                order: order
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Card order persisted successfully');
            } else {
                console.warn('Failed to persist card order:', data.error);
            }
        })
        .catch(error => {
            console.error('Error persisting card order:', error);
        });
    }
    
    showReorderFeedback(message) {
        // Create or update feedback element
        let feedback = document.querySelector('.reorder-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'reorder-feedback';
            document.body.appendChild(feedback);
        }
        
        feedback.textContent = message;
        feedback.classList.add('show');
        
        // Hide after delay
        setTimeout(() => {
            feedback.classList.remove('show');
        }, 2000);
    }
    
    // ===== KEYBOARD REORDERING FOR ACCESSIBILITY =====
    
    handleKeyboardReorder(direction) {
        const currentIndex = this.currentCard;
        let newIndex;
        
        if (direction === 'up' && currentIndex > 0) {
            newIndex = currentIndex - 1;
        } else if (direction === 'down' && currentIndex < this.cards.length - 1) {
            newIndex = currentIndex + 1;
        } else {
            return; // Invalid move
        }
        
        this.reorderCard(currentIndex, newIndex);
    }
    
    renderCardList() {
        // This method would render a list view of cards with drag handles
        // For now, just update the current card display
        this.renderCurrentCard();
    }
    
    // ===== KEYBOARD HANDLING =====
    
    handleKeypress(e) {
        if (!this.options.enableKeyboard) return;
        
        // Don't handle keys when typing in inputs
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        
        switch (e.code) {
            case 'Space':
            case 'Enter':
                e.preventDefault();
                this.flipCard();
                break;
            case 'Digit1':
                e.preventDefault();
                this.handleCardResponse(1);
                break;
            case 'Digit2':
                e.preventDefault();
                this.handleCardResponse(2);
                break;
            case 'Digit3':
                e.preventDefault();
                this.handleCardResponse(3);
                break;
            case 'Digit4':
                e.preventDefault();
                this.handleCardResponse(4);
                break;
            case 'ArrowLeft':
                e.preventDefault();
                this.previousCard();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.nextCard();
                break;
            case 'ArrowUp':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    this.handleKeyboardReorder('up');
                }
                break;
            case 'ArrowDown':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    this.handleKeyboardReorder('down');
                }
                break;
        }
    }
    
    // ===== NAVIGATION =====
    
    nextCard() {
        if (this.currentCard < this.cards.length - 1) {
            this.currentCard++;
            this.isFlipped = false;
            this.renderCurrentCard();
            this.updateProgress();
        } else {
            this.handleSessionComplete();
        }
    }
    
    previousCard() {
        if (this.currentCard > 0) {
            this.currentCard--;
            this.isFlipped = false;
            this.renderCurrentCard();
            this.updateProgress();
        }
    }
    
    goToCard(index) {
        if (index >= 0 && index < this.cards.length) {
            this.currentCard = index;
            this.isFlipped = false;
            this.renderCurrentCard();
            this.updateProgress();
        }
    }
    
    // ===== SPACED REPETITION SYSTEM =====
    
    updateSRSData(card, quality) {
        const srs = card.srsData;
        
        if (quality < 3) {
            // Reset for poor performance
            srs.repetitions = 0;
            srs.interval = 1;
        } else {
            srs.repetitions++;
            
            if (srs.repetitions === 1) {
                srs.interval = 1;
            } else if (srs.repetitions === 2) {
                srs.interval = 6;
            } else {
                srs.interval = Math.ceil(srs.interval * srs.easeFactor);
            }
        }
        
        // Update ease factor
        srs.easeFactor = Math.max(1.3, srs.easeFactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)));
        
        // Set next review date
        card.nextReview = new Date(Date.now() + srs.interval * 24 * 60 * 60 * 1000);
        card.lastReviewed = new Date().toISOString();
    }
    
    getSRSState(srsData) {
        if (srsData.repetitions === 0) return 'new';
        if (srsData.repetitions < 3) return 'learning';
        if (srsData.interval < 21) return 'review';
        return 'mastered';
    }
    
    getSRSLabel(srsData) {
        const state = this.getSRSState(srsData);
        const labels = {
            'new': 'Nouveau',
            'learning': 'Apprentissage',
            'review': 'Révision',
            'mastered': 'Maîtrisé'
        };
        return labels[state] || 'Nouveau';
    }
    
    // ===== PROGRESS TRACKING =====
    
    updateProgress() {
        const progressBar = document.querySelector('.flashcard-progress');
        if (progressBar) {
            const progress = ((this.currentCard + 1) / this.cards.length) * 100;
            progressBar.style.width = `${progress}%`;
        }
        
        // Update counter
        const counter = document.getElementById('card-counter');
        if (counter) {
            counter.textContent = `${this.currentCard + 1} / ${this.cards.length}`;
        }
    }
    
    updateCardMetadata(card) {
        // Update view count
        card.views = (card.views || 0) + 1;
        card.lastViewed = new Date().toISOString();
    }
    
    recordInteraction(card, quality) {
        const interaction = {
            cardId: card.id,
            quality: quality,
            timestamp: new Date().toISOString(),
            responseTime: this.getResponseTime(),
            sessionId: this.sessionId
        };
        
        // Send to analytics API
        fetch(`${getBaseURL()}/api/advanced/learning_interaction`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: 'default',
                concept_id: card.id,
                concept_name: card.front?.title || card.front,
                is_correct: quality >= 3,
                response_time: this.getResponseTime(),
                confidence: quality / 4,
                context: 'flashcard_review'
            })
        }).catch(console.error);
    }
    
    getResponseTime() {
        // Calculate time since card was displayed
        return this.cardDisplayTime ? Date.now() - this.cardDisplayTime : 0;
    }
    
    // ===== SESSION MANAGEMENT =====
    
    handleSessionComplete() {
        const completionHTML = `
            <div class="session-complete">
                <div class="completion-icon">🎉</div>
                <div class="completion-title">Session terminée!</div>
                <div class="completion-stats">
                    <div class="stat">
                        <div class="stat-value">${this.cards.length}</div>
                        <div class="stat-label">Cartes révisées</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">${this.getAccuracy()}%</div>
                        <div class="stat-label">Précision</div>
                    </div>
                </div>
                <button class="btn-primary" onclick="location.reload()">
                    Nouvelle session
                </button>
            </div>
        `;
        
        const container = document.getElementById('flashcard-container');
        if (container) {
            container.innerHTML = completionHTML;
        }
    }
    
    getAccuracy() {
        // Calculate accuracy from recorded interactions
        const goodResponses = this.cards.filter(card => 
            card.lastResponse && card.lastResponse >= 3
        ).length;
        return Math.round((goodResponses / this.cards.length) * 100);
    }
    
    // ===== UTILITY FUNCTIONS =====
    
    handleVisibilityChange() {
        if (document.hidden) {
            this.pauseSession();
        } else {
            this.resumeSession();
        }
    }
    
    handleResize() {
        // Recalculate layout on resize
        this.renderCurrentCard();
    }
    
    pauseSession() {
        this.sessionPaused = true;
        // Save current progress
        this.saveSession();
    }
    
    resumeSession() {
        this.sessionPaused = false;
        this.cardDisplayTime = Date.now(); // Reset timer
    }
    
    saveSession() {
        const sessionData = {
            cards: this.cards,
            currentCard: this.currentCard,
            isFlipped: this.isFlipped,
            sessionStartTime: this.sessionStartTime
        };
        localStorage.setItem('flashcard_session', JSON.stringify(sessionData));
    }
    
    loadSession() {
        const sessionData = JSON.parse(localStorage.getItem('flashcard_session') || '{}');
        if (sessionData.cards && sessionData.cards.length > 0) {
            this.cards = sessionData.cards;
            this.currentCard = sessionData.currentCard || 0;
            this.isFlipped = sessionData.isFlipped || false;
            this.sessionStartTime = sessionData.sessionStartTime || Date.now();
            return true;
        }
        return false;
    }
    
    clearSession() {
        localStorage.removeItem('flashcard_session');
    }
}

// Initialize global flashcard system
window.flashcardSystem = new AdvancedFlashcardSystem({
    enableGestures: true,
    enableAnimations: true,
    enableKeyboard: true,
    enableHaptics: 'vibrate' in navigator,
    stackSize: 4
});

// Add progress bar to page if not exists
document.addEventListener('DOMContentLoaded', () => {
    if (!document.querySelector('.flashcard-progress')) {
        const progressBar = document.createElement('div');
        progressBar.className = 'flashcard-progress';
        progressBar.style.width = '0%';
        document.body.appendChild(progressBar);
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdvancedFlashcardSystem;
}