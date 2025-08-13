# services/ai_pipeline.py
# -*- coding: utf-8 -*-
"""
AI Pipeline Orchestration

Orchestrates AdvancedRAG + EducationalAI to produce structured analysis
and study materials using local LLM integration.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from .local_llm import get_local_llm
from .advanced_rag import AdvancedRAG
from .educational_ai import EducationalAI
from .analyzer import analyze_offline

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Structured result from text analysis"""
    key_points: List[str]
    misconceptions: List[str] 
    difficulty: str
    plan: List[Dict[str, Any]]
    suggested_exercises: List[Dict[str, Any]]
    knowledge_gaps: List[str]
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class StudyMaterials:
    """Generated study materials"""
    summaries: List[str]
    flashcards: List[Dict[str, str]]
    mnemonics: List[Dict[str, str]]
    quizzes: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AIPipeline:
    """AI Pipeline orchestrator for educational analysis"""
    
    def __init__(self):
        self.llm = get_local_llm()
        self.rag = self._init_rag()
        self.educational_ai = self._init_educational_ai()
    
    def _init_rag(self) -> Optional[AdvancedRAG]:
        """Initialize Advanced RAG if available"""
        try:
            from .advanced_rag import AdvancedRAG
            return AdvancedRAG()
        except Exception as e:
            logger.warning(f"Advanced RAG initialization failed: {e}")
            return None
    
    def _init_educational_ai(self) -> Optional[EducationalAI]:
        """Initialize Educational AI if available"""
        try:
            from .educational_ai import EducationalAI
            return EducationalAI()
        except Exception as e:
            logger.warning(f"Educational AI initialization failed: {e}")
            return None
    
    def analyze_text(self, text: str, goals: Optional[List[str]] = None) -> AnalysisResult:
        """Analyze text and provide structured educational insights"""
        try:
            # Start with offline analysis as baseline
            offline_analysis = analyze_offline(text)
            
            # Get context from RAG if available
            context = []
            if self.rag:
                try:
                    context = self.rag.search(text, top_k=3)
                except Exception as e:
                    logger.warning(f"RAG search failed: {e}")
            
            # Build enhanced prompt for LLM analysis
            enhanced_text = self._build_analysis_prompt(text, offline_analysis, context, goals)
            
            # Get LLM analysis
            llm_response = self.llm.generate(
                prompt=enhanced_text,
                system="You are an expert educational analyst. Provide structured analysis in JSON format.",
                temperature=0.1
            )
            
            # Parse and structure the response
            return self._parse_analysis_response(llm_response, offline_analysis)
            
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            # Return fallback analysis based on offline results
            return self._fallback_analysis(text, offline_analysis)
    
    def _build_analysis_prompt(self, text: str, offline_analysis: List[Dict[str, Any]], 
                              context: List[str], goals: Optional[List[str]]) -> str:
        """Build comprehensive analysis prompt"""
        prompt = f"""Analyze this educational text and provide structured insights:

TEXT TO ANALYZE:
{text}

OFFLINE ANALYSIS BASELINE:
{json.dumps(offline_analysis, indent=2)}
"""
        
        if context:
            prompt += f"\nRELATED CONTEXT:\n" + "\n".join(f"- {ctx}" for ctx in context)
        
        if goals:
            prompt += f"\nLEARNING GOALS:\n" + "\n".join(f"- {goal}" for goal in goals)
        
        prompt += """

Please provide a JSON response with the following structure:
{
  "key_points": ["main concept 1", "main concept 2", ...],
  "misconceptions": ["common error 1", "common error 2", ...],
  "difficulty": "beginner|intermediate|advanced|expert",
  "knowledge_gaps": ["prerequisite 1", "prerequisite 2", ...],
  "confidence": 0.85,
  "suggested_exercises": [
    {"type": "recall", "question": "...", "answer": "..."},
    {"type": "application", "scenario": "...", "solution": "..."}
  ]
}"""
        return prompt
    
    def _parse_analysis_response(self, llm_response: Dict[str, Any], 
                                offline_analysis: List[Dict[str, Any]]) -> AnalysisResult:
        """Parse LLM response into structured analysis"""
        try:
            # Extract text from response
            response_text = llm_response.get("text", "")
            
            # Try to parse JSON from response
            # Look for JSON block in response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                parsed = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
            
            # Generate plan from key points
            plan = self._generate_study_plan(parsed.get("key_points", []))
            
            return AnalysisResult(
                key_points=parsed.get("key_points", []),
                misconceptions=parsed.get("misconceptions", []),
                difficulty=parsed.get("difficulty", "intermediate"),
                plan=plan,
                suggested_exercises=parsed.get("suggested_exercises", []),
                knowledge_gaps=parsed.get("knowledge_gaps", []),
                confidence=float(parsed.get("confidence", 0.7))
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return self._fallback_analysis("", offline_analysis)
    
    def _fallback_analysis(self, text: str, offline_analysis: List[Dict[str, Any]]) -> AnalysisResult:
        """Generate fallback analysis from offline results"""
        # Extract key points from offline analysis
        key_points = []
        exercises = []
        
        # Process offline analysis items
        for item in offline_analysis:
            payload = item.get("payload", {})
            
            # Extract key points from various sources
            if payload.get("title"):
                key_points.append(payload["title"])
            if payload.get("keywords"):
                key_points.extend(payload["keywords"])
            if payload.get("term"):
                key_points.append(payload["term"])
        
        # Generate basic plan
        plan = self._generate_study_plan(key_points[:5])
        
        # Generate exercises from analysis items  
        for item in offline_analysis:
            payload = item.get("payload", {})
            if payload.get("term") and payload.get("definition"):
                exercises.append({
                    "type": "recall",
                    "question": f"What is {payload['term']}?",
                    "answer": payload["definition"]
                })
        
        return AnalysisResult(
            key_points=key_points[:5],
            misconceptions=[],
            difficulty="intermediate",
            plan=plan,
            suggested_exercises=exercises[:3],
            knowledge_gaps=[],
            confidence=0.5
        )
    
    def _generate_study_plan(self, key_points: List[str]) -> List[Dict[str, Any]]:
        """Generate study plan from key points"""
        plan = []
        for i, point in enumerate(key_points[:5], 1):
            plan.append({
                "step": i,
                "title": f"Master {point}",
                "description": f"Study and understand {point}",
                "estimated_time": "15-30 minutes",
                "priority": "high" if i <= 2 else "medium"
            })
        return plan
    
    def generate_study_materials(self, text: str) -> StudyMaterials:
        """Generate comprehensive study materials from text"""
        try:
            # Get analysis first
            analysis = self.analyze_text(text)
            
            # Build materials generation prompt
            prompt = self._build_materials_prompt(text, analysis)
            
            # Get LLM response
            llm_response = self.llm.generate(
                prompt=prompt,
                system="You are an expert educational content creator. Generate comprehensive study materials.",
                temperature=0.2
            )
            
            return self._parse_materials_response(llm_response, analysis)
            
        except Exception as e:
            logger.error(f"Study materials generation failed: {e}")
            return self._fallback_materials(text)
    
    def _build_materials_prompt(self, text: str, analysis: AnalysisResult) -> str:
        """Build materials generation prompt"""
        return f"""Generate comprehensive study materials for this text:

TEXT:
{text}

KEY CONCEPTS:
{json.dumps(analysis.key_points)}

Please generate study materials in JSON format:
{{
  "summaries": ["concise summary 1", "detailed summary 2"],
  "flashcards": [
    {{"front": "Question or term", "back": "Answer or definition"}},
    ...
  ],
  "mnemonics": [
    {{"concept": "concept name", "mnemonic": "memory device"}},
    ...
  ],
  "quizzes": [
    {{
      "question": "Question text",
      "type": "multiple_choice|true_false|short_answer",
      "options": ["A", "B", "C", "D"],
      "correct": "A",
      "explanation": "Why this answer is correct"
    }},
    ...
  ]
}}"""
    
    def _parse_materials_response(self, llm_response: Dict[str, Any], 
                                 analysis: AnalysisResult) -> StudyMaterials:
        """Parse LLM response into study materials"""
        try:
            response_text = llm_response.get("text", "")
            
            # Extract JSON
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                parsed = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
            
            return StudyMaterials(
                summaries=parsed.get("summaries", []),
                flashcards=parsed.get("flashcards", []),
                mnemonics=parsed.get("mnemonics", []),
                quizzes=parsed.get("quizzes", [])
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse materials response: {e}")
            return self._fallback_materials("")
    
    def _fallback_materials(self, text: str) -> StudyMaterials:
        """Generate fallback study materials"""
        # Basic analysis
        offline_analysis = analyze_offline(text)
        
        # Generate basic flashcards from analysis items
        flashcards = []
        summaries = []
        
        for item in offline_analysis[:5]:
            payload = item.get("payload", {})
            
            # Create flashcard if we have term/definition
            if payload.get("term") and payload.get("definition"):
                flashcards.append({
                    "front": payload["term"],
                    "back": payload["definition"]
                })
            
            # Add summary if available
            if payload.get("summary"):
                summaries.append(payload["summary"])
        
        # Basic quiz from flashcards
        quizzes = []
        for card in flashcards[:3]:
            quizzes.append({
                "question": f"What is {card['front']}?",
                "type": "short_answer",
                "correct": card["back"],
                "explanation": f"{card['front']} is defined as {card['back']}"
            })
        
        return StudyMaterials(
            summaries=summaries,
            flashcards=flashcards,
            mnemonics=[],
            quizzes=quizzes
        )


# Global instance
_ai_pipeline_instance = None

def get_ai_pipeline() -> AIPipeline:
    """Get or create the global AI pipeline instance"""
    global _ai_pipeline_instance
    if _ai_pipeline_instance is None:
        _ai_pipeline_instance = AIPipeline()
    return _ai_pipeline_instance