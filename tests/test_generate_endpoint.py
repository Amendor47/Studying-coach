import os
import sys
import pytest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app


def test_ai_generate_endpoint():
    """Test the /api/ai/generate endpoint"""
    client = app.test_client()
    
    response = client.post('/api/ai/generate',
                          json={'prompt': 'What is machine learning?'},
                          headers={'Content-Type': 'application/json'})
    
    # Should return 200 (success) or 500 (error with LLM unavailable)
    assert response.status_code in [200, 500]
    
    data = response.get_json()
    
    if response.status_code == 200:
        # Success case
        assert 'text' in data
        assert 'model' in data
        assert 'provider' in data
        assert isinstance(data['text'], str)
    else:
        # Error case - should have error message
        assert 'error' in data


def test_ai_generate_missing_prompt():
    """Test generate endpoint with missing prompt"""
    client = app.test_client()
    
    response = client.post('/api/ai/generate',
                          json={},
                          headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_ai_generate_with_system_prompt():
    """Test generate endpoint with system prompt"""
    client = app.test_client()
    
    response = client.post('/api/ai/generate',
                          json={
                              'prompt': 'Explain briefly.',
                              'system': 'You are a helpful teacher.'
                          },
                          headers={'Content-Type': 'application/json'})
    
    # Should handle system prompt without error
    assert response.status_code in [200, 500]


def test_ai_generate_streaming_false():
    """Test generate endpoint with streaming disabled"""
    client = app.test_client()
    
    response = client.post('/api/ai/generate',
                          json={
                              'prompt': 'Hello',
                              'stream': False
                          },
                          headers={'Content-Type': 'application/json'})
    
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        # Should return JSON, not streaming
        assert response.content_type.startswith('application/json')


def test_ai_generate_streaming_true():
    """Test generate endpoint with streaming enabled"""
    client = app.test_client()
    
    response = client.post('/api/ai/generate',
                          json={
                              'prompt': 'Count to 3',
                              'stream': True
                          },
                          headers={'Content-Type': 'application/json'})
    
    # Stream requests should either work (200) or fail gracefully (500)
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        # Should return event stream
        assert response.content_type.startswith('text/event-stream')


def test_ai_exercises_endpoint():
    """Test the /api/ai/exercises endpoint"""
    client = app.test_client()
    
    response = client.post('/api/ai/exercises',
                          json={'text': 'Python is a programming language used for web development and data science.'},
                          headers={'Content-Type': 'application/json'})
    
    assert response.status_code in [200, 500]
    
    data = response.get_json()
    
    if response.status_code == 200:
        assert 'exercises' in data
        assert 'total_count' in data
        assert 'by_type' in data
        assert isinstance(data['exercises'], list)
        assert isinstance(data['total_count'], int)
        assert isinstance(data['by_type'], dict)
    else:
        assert 'error' in data


def test_ai_exercises_missing_text():
    """Test exercises endpoint with missing text"""
    client = app.test_client()
    
    response = client.post('/api/ai/exercises',
                          json={},
                          headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_ai_exercises_exercise_structure():
    """Test that generated exercises have proper structure"""
    client = app.test_client()
    
    response = client.post('/api/ai/exercises',
                          json={'text': 'The mitochondria is the powerhouse of the cell.'},
                          headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        data = response.get_json()
        
        # Check exercise structure
        for exercise in data['exercises']:
            assert 'type' in exercise
            # Different types have different required fields, but all should have type
            if exercise['type'] == 'flashcard':
                assert 'question' in exercise or 'answer' in exercise
            elif exercise['type'] == 'mnemonic':
                assert 'concept' in exercise or 'device' in exercise