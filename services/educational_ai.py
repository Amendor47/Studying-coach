# services/educational_ai.py
# -*- coding: utf-8 -*-
"""
Advanced Educational AI with Pedagogical Expertise

This module implements next-generation AI features specifically designed for educational effectiveness:
- Context-aware conversation system with learning objectives tracking
- Intelligent tutoring patterns (Socratic method, scaffolding, active recall)
- Adaptive difficulty based on user performance analytics
- Multi-modal understanding capabilities
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .ai import cached_call
from .local_ai import LocalAI


class TutoringMethod(Enum):
    """Different pedagogical approaches for content delivery"""
    SOCRATIC = "socratic"  # Question-based discovery learning
    SCAFFOLDING = "scaffolding"  # Gradual complexity increase
    ACTIVE_RECALL = "active_recall"  # Memory retrieval practice
    ELABORATIVE = "elaborative"  # Connection to existing knowledge


class DifficultyLevel(Enum):
    """Adaptive difficulty levels based on user performance"""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4


@dataclass
class LearningObjective:
    """Represents a specific learning goal"""
    id: str
    title: str
    description: str
    level: DifficultyLevel
    prerequisites: List[str]
    mastery_criteria: List[str]


@dataclass
class UserProfile:
    """Tracks user learning state and preferences"""
    id: str
    performance_history: Dict[str, float]  # concept_id -> mastery_score
    preferred_method: TutoringMethod
    current_level: DifficultyLevel
    learning_objectives: List[str]
    weak_areas: List[str]
    strong_areas: List[str]


class EducationalAI:
    """Advanced AI system with educational specialization"""
    
    def __init__(self):
        self.local_ai = LocalAI()
        self.pedagogical_prompts = self._load_pedagogical_prompts()
        
    def _load_pedagogical_prompts(self) -> Dict[str, str]:
        """Load specialized educational prompts for different tutoring methods"""
        return {
            "socratic": """Tu es un tuteur utilisant la méthode socratique. Au lieu de donner des réponses directes, pose des questions qui guident l'étudiant vers la découverte. 

Principes:
- Pose des questions ouvertes qui encouragent la réflexion
- Guide par des questions de plus en plus précises
- Aide l'étudiant à identifier ses propres erreurs de raisonnement
- Encourage la justification des réponses

Format de réponse JSON:
{
    "questions": ["question1", "question2"],
    "hints": ["indice1 si nécessaire"],
    "concept_map": {"concept": "relation"},
    "next_steps": ["étape suivante"]
}""",

            "scaffolding": """Tu es un tuteur expert en scaffolding pédagogique. Décompose les concepts complexes en étapes progressives et adaptées au niveau de l'étudiant.

Principes:
- Commence par les prérequis et construis progressivement
- Utilise des analogies et exemples concrets
- Propose des exercices de difficulté croissante
- Offre un support temporaire qui peut être retiré graduellement

Format de réponse JSON:
{
    "prerequisites": ["prérequis nécessaires"],
    "progression": [{"step": 1, "concept": "...", "difficulty": "easy"}],
    "analogies": ["analogie utile"],
    "support_tools": ["outil d'aide temporaire"]
}""",

            "active_recall": """Tu es spécialisé dans les techniques de rappel actif. Crée des questions et exercices qui forcent l'étudiant à récupérer l'information de sa mémoire.

Principes:
- Varie les formats de questions (QCM, remplir les blancs, questions ouvertes)
- Espacement optimal pour la rétention
- Feedback immédiat et explicatif
- Identification des lacunes de mémoire

Format de réponse JSON:
{
    "recall_questions": [{"type": "mcq|fill|open", "question": "...", "options": [...], "explanation": "..."}],
    "memory_cues": ["indice de rappel"],
    "retention_score": 0.8,
    "next_review": "2024-01-15"
}""",

            "elaborative": """Tu es expert en apprentissage élaboratif. Aide l'étudiant à connecter les nouvelles informations aux connaissances existantes et à créer du sens.

Principes:
- Établis des liens avec les connaissances antérieures
- Encourage la création d'exemples personnels
- Utilise des cartes conceptuelles
- Promote la métacognition

Format de réponse JSON:
{
    "connections": [{"new_concept": "...", "existing_knowledge": "...", "relationship": "..."}],
    "personal_examples": ["exemple à personnaliser"],
    "concept_network": {"central_concept": ["concept_lié1", "concept_lié2"]},
    "reflection_questions": ["Comment cela se relie-t-il à...?"]
}"""
        }
    
    def generate_adaptive_content(self, text: str, user_profile: UserProfile, 
                                learning_objective: LearningObjective) -> Dict[str, Any]:
        """Generate educational content adapted to user level and learning objective"""
        
        # Select appropriate tutoring method based on user profile and objective
        method = self._select_tutoring_method(user_profile, learning_objective)
        
        # Build context-aware prompt
        system_prompt = self.pedagogical_prompts[method.value]
        
        # Enhance with user context
        user_context = f"""
Profil étudiant:
- Niveau actuel: {user_profile.current_level.name}
- Méthode préférée: {user_profile.preferred_method.value}
- Points faibles identifiés: {', '.join(user_profile.weak_areas)}
- Points forts: {', '.join(user_profile.strong_areas)}

Objectif d'apprentissage:
- Titre: {learning_objective.title}
- Description: {learning_objective.description}
- Niveau requis: {learning_objective.level.name}
- Prérequis: {', '.join(learning_objective.prerequisites)}

Contenu à analyser:
{text}

Adapte ta pédagogie selon le profil et l'objectif d'apprentissage."""
        
        def call_fn(sys: str, usr: str) -> Dict[str, Any]:
            try:
                # Try using enhanced local AI if available
                if hasattr(self.local_ai, 'chat_with_context'):
                    return self.local_ai.chat_with_context(sys + "\n\n" + usr)
                else:
                    # Fallback to standard AI service
                    from .ai import analyze_text
                    result = analyze_text(usr, f"adaptive_{method.value}")
                    return {"content": result, "method": method.value}
            except Exception as e:
                return {"error": str(e), "fallback": True}
        
        return cached_call(system_prompt, user_context, call_fn)
    
    def _select_tutoring_method(self, user_profile: UserProfile, 
                              learning_objective: LearningObjective) -> TutoringMethod:
        """Intelligently select the best tutoring method based on context"""
        
        # Consider user preferences first
        if user_profile.preferred_method:
            return user_profile.preferred_method
            
        # Adapt based on learning objective level
        if learning_objective.level == DifficultyLevel.BEGINNER:
            return TutoringMethod.SCAFFOLDING
        elif learning_objective.level == DifficultyLevel.ADVANCED:
            return TutoringMethod.SOCRATIC
        else:
            # For intermediate levels, consider performance history
            avg_performance = sum(user_profile.performance_history.values()) / max(len(user_profile.performance_history), 1)
            if avg_performance < 0.6:
                return TutoringMethod.SCAFFOLDING
            elif avg_performance > 0.8:
                return TutoringMethod.ELABORATIVE
            else:
                return TutoringMethod.ACTIVE_RECALL
    
    def assess_learning_progress(self, user_id: str, responses: List[Dict]) -> Dict[str, Any]:
        """Analyze user responses to assess learning progress and adapt difficulty"""
        
        performance_metrics = {
            "accuracy": 0.0,
            "response_time": 0.0,
            "confidence": 0.0,
            "concept_mastery": {},
            "recommended_adjustments": []
        }
        
        if not responses:
            return performance_metrics
            
        # Calculate accuracy
        correct_responses = sum(1 for r in responses if r.get("correct", False))
        performance_metrics["accuracy"] = correct_responses / len(responses)
        
        # Analyze response times
        times = [r.get("response_time", 0) for r in responses if r.get("response_time", 0) > 0]
        performance_metrics["response_time"] = sum(times) / max(len(times), 1)
        
        # Assess concept mastery
        concept_scores = {}
        for response in responses:
            concept = response.get("concept", "unknown")
            score = 1.0 if response.get("correct", False) else 0.0
            
            if concept not in concept_scores:
                concept_scores[concept] = []
            concept_scores[concept].append(score)
        
        for concept, scores in concept_scores.items():
            performance_metrics["concept_mastery"][concept] = sum(scores) / len(scores)
        
        # Generate recommendations
        if performance_metrics["accuracy"] < 0.5:
            performance_metrics["recommended_adjustments"].append("decrease_difficulty")
            performance_metrics["recommended_adjustments"].append("add_scaffolding")
        elif performance_metrics["accuracy"] > 0.9:
            performance_metrics["recommended_adjustments"].append("increase_difficulty")
            performance_metrics["recommended_adjustments"].append("add_challenge_questions")
        
        return performance_metrics
    
    def generate_socratic_questions(self, content: str, depth: int = 3) -> List[str]:
        """Generate Socratic method questions for deeper understanding"""
        
        questions = []
        
        # Basic comprehension questions
        questions.extend([
            f"Quels sont les éléments clés de {content[:50]}...?",
            "Comment pourriez-vous expliquer cela dans vos propres mots?",
            "Quels exemples concrets pouvez-vous donner?"
        ])
        
        if depth >= 2:
            # Analysis questions
            questions.extend([
                "Quelles sont les causes sous-jacentes de ce phénomène?",
                "Comment ce concept se relie-t-il à ce que vous savez déjà?",
                "Quelles sont les implications de cette information?"
            ])
        
        if depth >= 3:
            # Synthesis and evaluation questions
            questions.extend([
                "Comment pourriez-vous appliquer ce concept dans d'autres contextes?",
                "Quelles sont les limites ou exceptions à cette règle?",
                "Comment évalueriez-vous l'efficacité de cette approche?"
            ])
        
        return questions
    
    def create_scaffolding_sequence(self, complex_concept: str, 
                                  user_level: DifficultyLevel) -> List[Dict[str, Any]]:
        """Create a scaffolding sequence to build up to complex concepts"""
        
        sequence = []
        
        # Level 1: Foundation
        sequence.append({
            "level": 1,
            "title": "Concepts fondamentaux",
            "description": "Bases nécessaires pour comprendre le concept principal",
            "activities": ["définitions", "exemples simples", "reconnaissance"],
            "support": "full"  # Maximum support
        })
        
        # Level 2: Connection
        sequence.append({
            "level": 2,
            "title": "Établissement des liens",
            "description": "Connexions entre les concepts de base",
            "activities": ["comparaisons", "classifications", "relations"],
            "support": "guided"  # Guided practice
        })
        
        # Level 3: Application
        sequence.append({
            "level": 3,
            "title": "Application guidée",
            "description": "Utilisation des concepts dans des contextes familiers",
            "activities": ["exercices guidés", "problèmes structurés"],
            "support": "minimal"  # Reduced support
        })
        
        # Level 4: Mastery (only for advanced users)
        if user_level in [DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT]:
            sequence.append({
                "level": 4,
                "title": "Maîtrise autonome",
                "description": "Application indépendante dans de nouveaux contextes",
                "activities": ["problèmes ouverts", "projets créatifs"],
                "support": "none"  # Independent work
            })
        
        return sequence
    
    def generate_multimodal_content(self, text: str, modalities: List[str]) -> Dict[str, Any]:
        """Generate content for multiple learning modalities"""
        
        multimodal_content = {
            "text": text,
            "visual": {},
            "audio": {},
            "interactive": {}
        }
        
        if "visual" in modalities:
            # Generate visual content suggestions
            multimodal_content["visual"] = {
                "diagrams": self._suggest_diagrams(text),
                "infographics": self._suggest_infographics(text),
                "concept_maps": self._generate_concept_map_structure(text)
            }
        
        if "audio" in modalities:
            # Generate audio content suggestions
            multimodal_content["audio"] = {
                "narration_script": self._create_narration_script(text),
                "pronunciation_guides": self._extract_difficult_terms(text),
                "audio_mnemonics": self._suggest_audio_mnemonics(text)
            }
        
        if "interactive" in modalities:
            # Generate interactive content suggestions
            multimodal_content["interactive"] = {
                "simulations": self._suggest_simulations(text),
                "interactive_exercises": self._create_interactive_exercises(text),
                "gamified_elements": self._suggest_gamification(text)
            }
        
        return multimodal_content
    
    def _suggest_diagrams(self, text: str) -> List[str]:
        """Suggest diagram types that would help visualize the content"""
        suggestions = []
        
        if re.search(r'\bprocessus|étapes|phases\b', text, re.IGNORECASE):
            suggestions.append("flowchart")
        if re.search(r'\brelations?|liens?|connexions?\b', text, re.IGNORECASE):
            suggestions.append("network_diagram")
        if re.search(r'\bstructure|organisation|hiérarchie\b', text, re.IGNORECASE):
            suggestions.append("organizational_chart")
        if re.search(r'\bcomparaison|différences?|similitudes?\b', text, re.IGNORECASE):
            suggestions.append("comparison_table")
        
        return suggestions
    
    def _suggest_infographics(self, text: str) -> List[str]:
        """Suggest infographic layouts for the content"""
        suggestions = []
        
        if re.search(r'\bstatistiques?|données|chiffres?\b', text, re.IGNORECASE):
            suggestions.append("statistical_infographic")
        if re.search(r'\bhistoire|chronologie|évolution\b', text, re.IGNORECASE):
            suggestions.append("timeline_infographic")
        if re.search(r'\bétapes|procédure|méthode\b', text, re.IGNORECASE):
            suggestions.append("process_infographic")
        
        return suggestions
    
    def _generate_concept_map_structure(self, text: str) -> Dict[str, List[str]]:
        """Generate a basic concept map structure from text"""
        # This is a simplified version - in a full implementation,
        # this would use NLP to extract key concepts and relationships
        
        words = re.findall(r'\b[A-ZÁÀÂÄÉÈÊËÍÌÎÏÓÒÔÖÚÙÛÜ][a-záàâäéèêëíìîïóòôöúùûü]+\b', text)
        important_words = [w for w in words if len(w) > 4][:10]
        
        concept_map = {}
        for i, concept in enumerate(important_words):
            related = important_words[max(0, i-2):i] + important_words[i+1:i+3]
            concept_map[concept] = related
        
        return concept_map
    
    def _create_narration_script(self, text: str) -> str:
        """Create a script optimized for audio narration"""
        # Add pauses and emphasis markers
        script = text.replace('.', '. [PAUSE]')
        script = script.replace('!', '! [EMPHASIS]')
        script = script.replace('?', '? [QUESTIONING_TONE]')
        
        # Add introduction and conclusion
        intro = "[WELCOMING_TONE] Explorons ensemble ce concept important. [PAUSE] "
        conclusion = " [PAUSE] Voilà qui conclut notre exploration de ce sujet. [ENCOURAGING_TONE]"
        
        return intro + script + conclusion
    
    def _extract_difficult_terms(self, text: str) -> List[Dict[str, str]]:
        """Extract terms that might need pronunciation guidance"""
        # Simple heuristic: words with unusual character combinations or long words
        difficult_pattern = r'\b\w*(?:ph|ch|th|tion|sion|ique|isme)\w*\b'
        terms = re.findall(difficult_pattern, text, re.IGNORECASE)
        
        return [{"term": term, "pronunciation": f"[{term}]"} for term in set(terms)]
    
    def _suggest_audio_mnemonics(self, text: str) -> List[str]:
        """Suggest audio-based memory aids"""
        mnemonics = []
        
        # Look for lists that could become acronyms
        lists = re.findall(r'(?:(?:\d+[.\)]|[-•])\s*([A-ZÁÀÂÄÉÈÊËÍÌÎÏÓÒÔÖÚÙÛÜ][^.\n]*?)(?:\n|$))+', text)
        if lists:
            mnemonics.append("Créer un acronyme avec les premières lettres")
        
        # Look for rhyming opportunities
        if re.search(r'\b\w+tion\b', text):
            mnemonics.append("Créer des rimes avec les mots en -tion")
        
        return mnemonics
    
    def _suggest_simulations(self, text: str) -> List[str]:
        """Suggest interactive simulations based on content"""
        suggestions = []
        
        if re.search(r'\bexpérience|test|mesure\b', text, re.IGNORECASE):
            suggestions.append("virtual_lab")
        if re.search(r'\béconomie|marché|finance\b', text, re.IGNORECASE):
            suggestions.append("economic_simulation")
        if re.search(r'\bécosystème|environnement|nature\b', text, re.IGNORECASE):
            suggestions.append("ecosystem_simulation")
        
        return suggestions
    
    def _create_interactive_exercises(self, text: str) -> List[Dict[str, Any]]:
        """Create interactive exercises based on content"""
        exercises = []
        
        # Drag and drop exercise
        sentences = text.split('.')
        if len(sentences) >= 3:
            exercises.append({
                "type": "drag_and_drop",
                "title": "Remettre les étapes dans l'ordre",
                "items": sentences[:5]
            })
        
        # Fill in the blanks
        if len(text.split()) > 20:
            exercises.append({
                "type": "fill_blanks",
                "title": "Compléter le texte",
                "text_with_blanks": self._create_fill_blanks(text)
            })
        
        return exercises
    
    def _create_fill_blanks(self, text: str) -> str:
        """Create a fill-in-the-blanks version of text"""
        words = text.split()
        important_words_indices = []
        
        for i, word in enumerate(words):
            if (len(word) > 6 and 
                word.lower() not in ['cependant', 'toutefois', 'néanmoins', 'pourtant']):
                important_words_indices.append(i)
        
        # Replace every 4th important word with a blank
        for i in important_words_indices[::4]:
            words[i] = "______"
        
        return " ".join(words)
    
    def _suggest_gamification(self, text: str) -> List[Dict[str, str]]:
        """Suggest gamification elements"""
        elements = []
        
        if len(text.split()) > 100:
            elements.append({
                "type": "progress_bar",
                "description": "Barre de progression pour le contenu long"
            })
        
        if re.search(r'\bquestion|problème|défi\b', text, re.IGNORECASE):
            elements.append({
                "type": "achievement_badges",
                "description": "Badges pour les défis réussis"
            })
        
        elements.append({
            "type": "knowledge_points",
            "description": "Points de connaissance pour chaque concept maîtrisé"
        })
        
        return elements


# Global instance for easy access
educational_ai = EducationalAI()