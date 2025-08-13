import os
import sys
import pytest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from services.ai_pipeline import get_ai_pipeline, AIPipeline


def test_ai_pipeline_initialization():
    """Test that AI pipeline initializes without error"""
    pipeline = get_ai_pipeline()
    assert isinstance(pipeline, AIPipeline)


def test_ai_analyze_text_structure():
    """Test that analyze_text returns expected structure"""
    pipeline = get_ai_pipeline()
    
    test_text = "Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed."
    
    result = pipeline.analyze_text(test_text)
    
    # Check that result has expected structure
    assert hasattr(result, 'key_points')
    assert hasattr(result, 'misconceptions') 
    assert hasattr(result, 'difficulty')
    assert hasattr(result, 'plan')
    assert hasattr(result, 'suggested_exercises')
    assert hasattr(result, 'knowledge_gaps')
    assert hasattr(result, 'confidence')
    
    # Check types
    assert isinstance(result.key_points, list)
    assert isinstance(result.misconceptions, list)
    assert isinstance(result.plan, list)
    assert isinstance(result.suggested_exercises, list)
    assert isinstance(result.knowledge_gaps, list)
    assert isinstance(result.confidence, float)
    assert result.difficulty in ['beginner', 'intermediate', 'advanced', 'expert']


def test_ai_analyze_text_with_goals():
    """Test analyze_text with learning goals"""
    pipeline = get_ai_pipeline()
    
    test_text = "Python is a programming language."
    goals = ["understand Python basics", "learn syntax"]
    
    result = pipeline.analyze_text(test_text, goals)
    
    # Should still return valid structure
    assert len(result.key_points) > 0
    assert result.confidence >= 0.0 and result.confidence <= 1.0


def test_generate_study_materials_structure():
    """Test that generate_study_materials returns expected structure"""
    pipeline = get_ai_pipeline()
    
    test_text = "Photosynthesis is the process by which plants convert light energy into chemical energy."
    
    result = pipeline.generate_study_materials(test_text)
    
    # Check structure
    assert hasattr(result, 'summaries')
    assert hasattr(result, 'flashcards')
    assert hasattr(result, 'mnemonics')
    assert hasattr(result, 'quizzes')
    
    # Check types
    assert isinstance(result.summaries, list)
    assert isinstance(result.flashcards, list)
    assert isinstance(result.mnemonics, list)
    assert isinstance(result.quizzes, list)


def test_generate_study_materials_flashcards():
    """Test that generated flashcards have correct structure"""
    pipeline = get_ai_pipeline()
    
    test_text = "The mitochondria is the powerhouse of the cell."
    
    result = pipeline.generate_study_materials(test_text)
    
    # Check flashcard structure if any are generated
    for card in result.flashcards:
        assert 'front' in card or 'back' in card  # Should have question/answer structure


def test_ai_pipeline_fallback_behavior():
    """Test that pipeline gracefully handles LLM failures"""
    pipeline = get_ai_pipeline()
    
    # Test with empty text
    result = pipeline.analyze_text("")
    
    # Should still return valid structure, not crash
    assert hasattr(result, 'key_points')
    assert hasattr(result, 'confidence')
    
    # Test with very short text
    result = pipeline.analyze_text("Hi")
    assert result.confidence >= 0.0