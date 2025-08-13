# services/contextual_memory.py
# -*- coding: utf-8 -*-
"""
Contextual Memory Architecture for Learning Optimization

This module implements advanced memory management for personalized learning:
- Long-term learning history tracking with spaced repetition algorithms
- Personalized knowledge state modeling (what user knows/doesn't know)  
- Intelligent review scheduling based on forgetting curves
- Cross-session continuity with learning path optimization
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import math

from .scheduler import update_srs, EF_MIN, EF_MAX
from .store import load_db, save_db


class KnowledgeState(Enum):
    """Different states of knowledge mastery"""
    UNKNOWN = "unknown"
    LEARNING = "learning"  
    PRACTICED = "practiced"
    MASTERED = "mastered"
    EXPERT = "expert"


class LearningPhase(Enum):
    """Different phases in the learning process"""
    ACQUISITION = "acquisition"  # First exposure
    CONSOLIDATION = "consolidation"  # Practice and strengthening
    RETENTION = "retention"  # Long-term memory
    TRANSFER = "transfer"  # Application in new contexts


@dataclass
class ConceptMemory:
    """Memory trace for a specific concept"""
    concept_id: str
    concept_name: str
    knowledge_state: KnowledgeState
    learning_phase: LearningPhase
    
    # Memory strength indicators
    memory_strength: float  # 0.0 to 1.0
    confidence_level: float  # User's self-reported confidence
    
    # Temporal tracking
    first_exposure: datetime
    last_review: datetime
    next_review: datetime
    review_count: int
    
    # Performance tracking
    correct_answers: int
    total_attempts: int
    average_response_time: float
    
    # Forgetting curve parameters
    decay_rate: float  # How quickly this concept is forgotten
    difficulty_adjustment: float  # Personal difficulty multiplier
    
    # Learning path information
    prerequisites: List[str]
    dependents: List[str]  # Concepts that depend on this one
    
    # Context information
    learning_contexts: List[str]  # Where this was learned/practiced
    associated_materials: List[str]  # Source materials
    
    def accuracy_rate(self) -> float:
        """Calculate accuracy percentage"""
        if self.total_attempts == 0:
            return 0.0
        return self.correct_answers / self.total_attempts
    
    def is_due_for_review(self) -> bool:
        """Check if concept is due for review"""
        return datetime.now() >= self.next_review
    
    def time_since_last_review(self) -> timedelta:
        """Get time since last review"""
        return datetime.now() - self.last_review


@dataclass 
class LearningSession:
    """Represents a learning session"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    concepts_studied: List[str]
    performance_summary: Dict[str, Any]
    learning_objectives: List[str]
    session_type: str  # "study", "review", "assessment", etc.


@dataclass
class UserLearningProfile:
    """Comprehensive user learning profile"""
    user_id: str
    
    # Learning preferences
    optimal_session_length: int  # minutes
    preferred_review_time: str  # "morning", "afternoon", "evening"
    learning_style_preferences: List[str]  # ["visual", "auditory", "kinesthetic"]
    
    # Performance patterns
    peak_performance_times: List[str]  # Times when user performs best
    attention_span_pattern: Dict[str, float]  # Time -> attention level
    forgetting_curve_profile: Dict[str, float]  # Concept type -> decay rate
    
    # Adaptive parameters
    current_cognitive_load: float  # 0.0 to 1.0
    learning_velocity: float  # Rate of knowledge acquisition
    retention_strength: float  # Overall retention ability
    
    # Knowledge state
    concept_memories: Dict[str, ConceptMemory]
    learning_history: List[LearningSession]
    
    # Goals and motivation
    learning_goals: List[str]
    achievement_history: List[Dict[str, Any]]
    motivation_factors: Dict[str, float]


class ContextualMemory:
    """Advanced memory system for learning optimization"""
    
    def __init__(self):
        self.user_profiles: Dict[str, UserLearningProfile] = {}
        self.global_concept_graph: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._load_profiles()
    
    def _load_profiles(self) -> None:
        """Load user profiles from storage"""
        try:
            db = load_db()
            profiles_data = db.get("user_profiles", {})
            
            for user_id, profile_data in profiles_data.items():
                # Convert stored data back to profile object
                profile = self._deserialize_profile(profile_data)
                self.user_profiles[user_id] = profile
        except Exception as e:
            print(f"Warning: Could not load user profiles: {e}")
    
    def _save_profiles(self) -> None:
        """Save user profiles to storage"""
        try:
            db = load_db()
            profiles_data = {}
            
            for user_id, profile in self.user_profiles.items():
                profiles_data[user_id] = self._serialize_profile(profile)
            
            db["user_profiles"] = profiles_data
            save_db(db)
        except Exception as e:
            print(f"Warning: Could not save user profiles: {e}")
    
    def _serialize_profile(self, profile: UserLearningProfile) -> Dict[str, Any]:
        """Serialize profile for storage"""
        data = asdict(profile)
        
        # Convert datetime objects to ISO strings
        for concept_id, memory in data["concept_memories"].items():
            memory["first_exposure"] = memory["first_exposure"].isoformat()
            memory["last_review"] = memory["last_review"].isoformat()  
            memory["next_review"] = memory["next_review"].isoformat()
            memory["knowledge_state"] = memory["knowledge_state"].value
            memory["learning_phase"] = memory["learning_phase"].value
        
        for session in data["learning_history"]:
            session["start_time"] = session["start_time"].isoformat()
            if session["end_time"]:
                session["end_time"] = session["end_time"].isoformat()
        
        return data
    
    def _deserialize_profile(self, data: Dict[str, Any]) -> UserLearningProfile:
        """Deserialize profile from storage"""
        
        # Convert concept memories
        concept_memories = {}
        for concept_id, memory_data in data.get("concept_memories", {}).items():
            memory = ConceptMemory(
                concept_id=memory_data["concept_id"],
                concept_name=memory_data["concept_name"],
                knowledge_state=KnowledgeState(memory_data["knowledge_state"]),
                learning_phase=LearningPhase(memory_data["learning_phase"]),
                memory_strength=memory_data["memory_strength"],
                confidence_level=memory_data["confidence_level"],
                first_exposure=datetime.fromisoformat(memory_data["first_exposure"]),
                last_review=datetime.fromisoformat(memory_data["last_review"]),
                next_review=datetime.fromisoformat(memory_data["next_review"]),
                review_count=memory_data["review_count"],
                correct_answers=memory_data["correct_answers"],
                total_attempts=memory_data["total_attempts"],
                average_response_time=memory_data["average_response_time"],
                decay_rate=memory_data["decay_rate"],
                difficulty_adjustment=memory_data["difficulty_adjustment"],
                prerequisites=memory_data["prerequisites"],
                dependents=memory_data["dependents"],
                learning_contexts=memory_data["learning_contexts"],
                associated_materials=memory_data["associated_materials"]
            )
            concept_memories[concept_id] = memory
        
        # Convert learning history
        learning_history = []
        for session_data in data.get("learning_history", []):
            session = LearningSession(
                session_id=session_data["session_id"],
                start_time=datetime.fromisoformat(session_data["start_time"]),
                end_time=datetime.fromisoformat(session_data["end_time"]) if session_data["end_time"] else None,
                concepts_studied=session_data["concepts_studied"],
                performance_summary=session_data["performance_summary"],
                learning_objectives=session_data["learning_objectives"],
                session_type=session_data["session_type"]
            )
            learning_history.append(session)
        
        return UserLearningProfile(
            user_id=data["user_id"],
            optimal_session_length=data.get("optimal_session_length", 25),
            preferred_review_time=data.get("preferred_review_time", "evening"),
            learning_style_preferences=data.get("learning_style_preferences", ["visual"]),
            peak_performance_times=data.get("peak_performance_times", ["morning"]),
            attention_span_pattern=data.get("attention_span_pattern", {}),
            forgetting_curve_profile=data.get("forgetting_curve_profile", {}),
            current_cognitive_load=data.get("current_cognitive_load", 0.5),
            learning_velocity=data.get("learning_velocity", 1.0),
            retention_strength=data.get("retention_strength", 1.0),
            concept_memories=concept_memories,
            learning_history=learning_history,
            learning_goals=data.get("learning_goals", []),
            achievement_history=data.get("achievement_history", []),
            motivation_factors=data.get("motivation_factors", {})
        )
    
    def get_or_create_profile(self, user_id: str) -> UserLearningProfile:
        """Get existing profile or create new one for user"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserLearningProfile(
                user_id=user_id,
                optimal_session_length=25,  # Default Pomodoro length
                preferred_review_time="evening",
                learning_style_preferences=["visual"],
                peak_performance_times=["morning"],
                attention_span_pattern={},
                forgetting_curve_profile={},
                current_cognitive_load=0.5,
                learning_velocity=1.0,
                retention_strength=1.0,
                concept_memories={},
                learning_history=[],
                learning_goals=[],
                achievement_history=[],
                motivation_factors={"intrinsic": 0.7, "achievement": 0.8, "social": 0.5}
            )
        return self.user_profiles[user_id]
    
    def record_learning_interaction(self, user_id: str, concept_id: str, concept_name: str,
                                  is_correct: bool, response_time: float, 
                                  confidence: float = 0.5, context: str = "") -> None:
        """Record a learning interaction for memory tracking"""
        
        profile = self.get_or_create_profile(user_id)
        now = datetime.now()
        
        # Get or create concept memory
        if concept_id not in profile.concept_memories:
            memory = ConceptMemory(
                concept_id=concept_id,
                concept_name=concept_name,
                knowledge_state=KnowledgeState.LEARNING,
                learning_phase=LearningPhase.ACQUISITION,
                memory_strength=0.1,
                confidence_level=confidence,
                first_exposure=now,
                last_review=now,
                next_review=self._calculate_next_review(now, 0.1, 1),
                review_count=0,
                correct_answers=0,
                total_attempts=0,
                average_response_time=response_time,
                decay_rate=0.1,  # Default decay rate
                difficulty_adjustment=1.0,
                prerequisites=[],
                dependents=[],
                learning_contexts=[context] if context else [],
                associated_materials=[]
            )
            profile.concept_memories[concept_id] = memory
        else:
            memory = profile.concept_memories[concept_id]
        
        # Update memory with new interaction
        memory.total_attempts += 1
        if is_correct:
            memory.correct_answers += 1
        
        # Update response time (exponential moving average)
        alpha = 0.3
        memory.average_response_time = (alpha * response_time + 
                                      (1 - alpha) * memory.average_response_time)
        
        # Update memory strength based on performance
        memory.memory_strength = self._update_memory_strength(memory, is_correct, confidence)
        
        # Update knowledge state
        memory.knowledge_state = self._update_knowledge_state(memory)
        memory.learning_phase = self._update_learning_phase(memory)
        
        # Calculate next review time using enhanced algorithm
        memory.next_review = self._calculate_next_review_enhanced(memory, is_correct)
        memory.last_review = now
        memory.review_count += 1
        
        # Update confidence
        memory.confidence_level = self._update_confidence(memory.confidence_level, confidence, is_correct)
        
        # Add context if new
        if context and context not in memory.learning_contexts:
            memory.learning_contexts.append(context)
        
        # Update forgetting curve parameters
        self._update_forgetting_curve(memory, is_correct, response_time)
        
        # Save changes
        self._save_profiles()
    
    def _update_memory_strength(self, memory: ConceptMemory, is_correct: bool, confidence: float) -> float:
        """Update memory strength based on performance"""
        
        current_strength = memory.memory_strength
        
        if is_correct:
            # Strengthen memory, but with diminishing returns
            strength_gain = 0.2 * (1 - current_strength) * confidence
            new_strength = min(1.0, current_strength + strength_gain)
        else:
            # Weaken memory based on how confident the user was (more confidence = bigger penalty)
            strength_loss = 0.15 * confidence
            new_strength = max(0.0, current_strength - strength_loss)
        
        return new_strength
    
    def _update_knowledge_state(self, memory: ConceptMemory) -> KnowledgeState:
        """Update knowledge state based on performance history"""
        
        accuracy = memory.accuracy_rate()
        attempts = memory.total_attempts
        strength = memory.memory_strength
        
        if attempts < 3:
            return KnowledgeState.LEARNING
        elif accuracy >= 0.9 and strength >= 0.8 and attempts >= 10:
            return KnowledgeState.EXPERT
        elif accuracy >= 0.8 and strength >= 0.7 and attempts >= 5:
            return KnowledgeState.MASTERED
        elif accuracy >= 0.6 and strength >= 0.5:
            return KnowledgeState.PRACTICED
        else:
            return KnowledgeState.LEARNING
    
    def _update_learning_phase(self, memory: ConceptMemory) -> LearningPhase:
        """Update learning phase based on review patterns"""
        
        days_since_first = (datetime.now() - memory.first_exposure).days
        review_count = memory.review_count
        
        if review_count <= 2:
            return LearningPhase.ACQUISITION
        elif days_since_first <= 7:
            return LearningPhase.CONSOLIDATION
        elif memory.knowledge_state in [KnowledgeState.MASTERED, KnowledgeState.EXPERT]:
            return LearningPhase.TRANSFER
        else:
            return LearningPhase.RETENTION
    
    def _calculate_next_review_enhanced(self, memory: ConceptMemory, is_correct: bool) -> datetime:
        """Calculate next review time using enhanced spaced repetition"""
        
        base_interval = 1.0  # Base interval in days
        
        # Adjust based on memory strength and accuracy
        strength_multiplier = 1 + memory.memory_strength * 2
        accuracy_multiplier = 1 + memory.accuracy_rate()
        
        # Adjust based on learning phase
        phase_multipliers = {
            LearningPhase.ACQUISITION: 0.5,
            LearningPhase.CONSOLIDATION: 1.0,
            LearningPhase.RETENTION: 1.5,
            LearningPhase.TRANSFER: 2.0
        }
        phase_multiplier = phase_multipliers[memory.learning_phase]
        
        # Personal difficulty adjustment
        difficulty_multiplier = 1 / memory.difficulty_adjustment
        
        # Calculate interval
        if is_correct:
            interval = (base_interval * strength_multiplier * accuracy_multiplier * 
                       phase_multiplier * difficulty_multiplier * (1.3 ** memory.review_count))
        else:
            # Reset to short interval for failed reviews
            interval = base_interval * 0.5
        
        # Apply bounds
        interval = max(0.1, min(365, interval))  # Between 2.4 hours and 1 year
        
        return datetime.now() + timedelta(days=interval)
    
    def _calculate_next_review(self, current_time: datetime, memory_strength: float, attempts: int) -> datetime:
        """Simple next review calculation (fallback)"""
        base_interval = 1.0  # 1 day
        strength_multiplier = 1 + memory_strength * 3
        interval = base_interval * strength_multiplier * (1.5 ** attempts)
        interval = max(0.1, min(30, interval))  # Between 2.4 hours and 30 days
        return current_time + timedelta(days=interval)
    
    def _update_confidence(self, current_confidence: float, reported_confidence: float, is_correct: bool) -> float:
        """Update confidence based on performance and self-report"""
        
        # Blend current confidence with new evidence
        alpha = 0.3
        
        if is_correct:
            # If correct, move towards reported confidence
            new_confidence = alpha * reported_confidence + (1 - alpha) * current_confidence
        else:
            # If incorrect, reduce confidence
            confidence_penalty = 0.2 * reported_confidence  # Higher reported confidence = bigger penalty
            new_confidence = max(0.1, current_confidence - confidence_penalty)
        
        return min(1.0, new_confidence)
    
    def _update_forgetting_curve(self, memory: ConceptMemory, is_correct: bool, response_time: float) -> None:
        """Update personal forgetting curve parameters"""
        
        # Adjust decay rate based on performance
        if is_correct:
            # Good performance = slower decay
            memory.decay_rate = max(0.01, memory.decay_rate * 0.95)
        else:
            # Poor performance = faster decay  
            memory.decay_rate = min(0.5, memory.decay_rate * 1.1)
        
        # Adjust difficulty based on response time
        avg_time = memory.average_response_time
        if response_time > avg_time * 1.5:
            # Slow response = increase difficulty adjustment
            memory.difficulty_adjustment = min(2.0, memory.difficulty_adjustment * 1.1)
        elif response_time < avg_time * 0.7:
            # Fast response = decrease difficulty adjustment
            memory.difficulty_adjustment = max(0.5, memory.difficulty_adjustment * 0.95)
    
    def get_due_concepts(self, user_id: str, max_count: int = 10) -> List[ConceptMemory]:
        """Get concepts due for review, prioritized by learning science"""
        
        profile = self.get_or_create_profile(user_id)
        due_concepts = []
        
        for memory in profile.concept_memories.values():
            if memory.is_due_for_review():
                due_concepts.append(memory)
        
        # Priority scoring for optimal learning
        def priority_score(memory: ConceptMemory) -> float:
            score = 0.0
            
            # Urgency (how overdue)
            days_overdue = (datetime.now() - memory.next_review).days
            score += min(10.0, max(0.0, days_overdue)) * 0.3
            
            # Memory strength (weaker memories get priority)
            score += (1.0 - memory.memory_strength) * 0.4
            
            # Learning phase importance
            phase_weights = {
                LearningPhase.ACQUISITION: 1.0,
                LearningPhase.CONSOLIDATION: 0.8,
                LearningPhase.RETENTION: 0.6,
                LearningPhase.TRANSFER: 0.4
            }
            score += phase_weights[memory.learning_phase] * 0.3
            
            return score
        
        # Sort by priority and return top concepts
        due_concepts.sort(key=priority_score, reverse=True)
        return due_concepts[:max_count]
    
    def optimize_learning_path(self, user_id: str, target_concepts: List[str]) -> List[Dict[str, Any]]:
        """Generate optimized learning path based on prerequisites and performance"""
        
        profile = self.get_or_create_profile(user_id)
        learning_path = []
        
        # Build concept dependency graph
        concept_graph = {}
        for concept_id in target_concepts:
            if concept_id in profile.concept_memories:
                memory = profile.concept_memories[concept_id]
                concept_graph[concept_id] = {
                    "memory": memory,
                    "prerequisites": memory.prerequisites,
                    "dependents": memory.dependents
                }
            else:
                # New concept - assume basic prerequisites
                concept_graph[concept_id] = {
                    "memory": None,
                    "prerequisites": [],
                    "dependents": []
                }
        
        # Topological sort for prerequisite ordering
        visited = set()
        temp_visited = set()
        sorted_concepts = []
        
        def visit(concept_id: str) -> None:
            if concept_id in temp_visited:
                return  # Cycle detected, skip
            if concept_id in visited:
                return
                
            temp_visited.add(concept_id)
            
            # Visit prerequisites first
            for prereq in concept_graph.get(concept_id, {}).get("prerequisites", []):
                if prereq in concept_graph:
                    visit(prereq)
            
            temp_visited.remove(concept_id)
            visited.add(concept_id)
            sorted_concepts.append(concept_id)
        
        # Visit all target concepts
        for concept_id in target_concepts:
            visit(concept_id)
        
        # Build learning path with optimal scheduling
        current_load = 0.0
        session_concepts = []
        
        for concept_id in sorted_concepts:
            concept_info = concept_graph[concept_id]
            memory = concept_info["memory"]
            
            # Estimate cognitive load for this concept
            if memory:
                # Existing concept - load based on difficulty and current state
                load = (1.0 - memory.memory_strength) * memory.difficulty_adjustment
            else:
                # New concept - assume moderate load
                load = 0.7
            
            # Check if adding this concept would exceed session capacity
            if current_load + load > profile.current_cognitive_load and session_concepts:
                # Save current session and start new one
                learning_path.append({
                    "session_type": "study",
                    "concepts": session_concepts.copy(),
                    "estimated_duration": len(session_concepts) * 5,  # 5 minutes per concept
                    "cognitive_load": current_load
                })
                session_concepts = []
                current_load = 0.0
            
            session_concepts.append({
                "concept_id": concept_id,
                "estimated_load": load,
                "current_state": memory.knowledge_state.value if memory else "new",
                "priority": 1.0 - (memory.memory_strength if memory else 0.0)
            })
            current_load += load
        
        # Add final session if not empty
        if session_concepts:
            learning_path.append({
                "session_type": "study",
                "concepts": session_concepts,
                "estimated_duration": len(session_concepts) * 5,
                "cognitive_load": current_load
            })
        
        return learning_path
    
    def generate_learning_analytics(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive learning analytics"""
        
        profile = self.get_or_create_profile(user_id)
        
        # Overall statistics
        total_concepts = len(profile.concept_memories)
        if total_concepts == 0:
            return {"error": "No learning data available"}
        
        # Knowledge state distribution
        state_counts = defaultdict(int)
        for memory in profile.concept_memories.values():
            state_counts[memory.knowledge_state.value] += 1
        
        # Performance metrics
        total_attempts = sum(m.total_attempts for m in profile.concept_memories.values())
        total_correct = sum(m.correct_answers for m in profile.concept_memories.values())
        overall_accuracy = total_correct / max(total_attempts, 1)
        
        # Learning velocity (concepts mastered per day)
        if profile.learning_history:
            days_active = (datetime.now() - profile.learning_history[0].start_time).days
            mastered_concepts = sum(1 for m in profile.concept_memories.values() 
                                  if m.knowledge_state in [KnowledgeState.MASTERED, KnowledgeState.EXPERT])
            learning_velocity = mastered_concepts / max(days_active, 1)
        else:
            learning_velocity = 0.0
        
        # Memory strength distribution
        strength_values = [m.memory_strength for m in profile.concept_memories.values()]
        avg_strength = sum(strength_values) / len(strength_values) if strength_values else 0.0
        
        # Weak areas (concepts needing attention)
        weak_concepts = [
            {
                "concept_id": m.concept_id,
                "concept_name": m.concept_name,
                "memory_strength": m.memory_strength,
                "accuracy": m.accuracy_rate(),
                "days_since_review": (datetime.now() - m.last_review).days
            }
            for m in profile.concept_memories.values()
            if m.memory_strength < 0.5 or m.accuracy_rate() < 0.6
        ]
        weak_concepts.sort(key=lambda x: x["memory_strength"])
        
        # Strong areas
        strong_concepts = [
            {
                "concept_id": m.concept_id,
                "concept_name": m.concept_name, 
                "memory_strength": m.memory_strength,
                "accuracy": m.accuracy_rate(),
                "knowledge_state": m.knowledge_state.value
            }
            for m in profile.concept_memories.values()
            if m.knowledge_state in [KnowledgeState.MASTERED, KnowledgeState.EXPERT]
        ]
        strong_concepts.sort(key=lambda x: x["memory_strength"], reverse=True)
        
        return {
            "user_id": user_id,
            "summary": {
                "total_concepts": total_concepts,
                "overall_accuracy": round(overall_accuracy, 3),
                "average_memory_strength": round(avg_strength, 3),
                "learning_velocity": round(learning_velocity, 3),
                "total_study_sessions": len(profile.learning_history)
            },
            "knowledge_distribution": dict(state_counts),
            "performance": {
                "total_attempts": total_attempts,
                "correct_answers": total_correct,
                "accuracy_percentage": round(overall_accuracy * 100, 1)
            },
            "recommendations": {
                "weak_areas": weak_concepts[:5],
                "strong_areas": strong_concepts[:5],
                "due_for_review": len([m for m in profile.concept_memories.values() if m.is_due_for_review()]),
                "suggested_session_length": profile.optimal_session_length
            },
            "learning_patterns": {
                "preferred_times": profile.peak_performance_times,
                "learning_styles": profile.learning_style_preferences,
                "attention_span": profile.optimal_session_length
            }
        }


# Global instance for easy access  
contextual_memory = ContextualMemory()