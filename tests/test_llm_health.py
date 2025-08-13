import os
import sys
import pytest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app


def test_health_endpoint_structure():
    """Test that /api/health returns expected structure"""
    client = app.test_client()
    
    response = client.get('/api/health')
    
    # Should return 200 or 503 depending on LLM availability
    assert response.status_code in [200, 503]
    
    data = response.get_json()
    
    # Check required fields
    assert 'status' in data
    assert 'timestamp' in data
    assert 'components' in data
    
    # Check components structure
    components = data['components']
    assert 'llm' in components
    assert 'database' in components
    assert 'ai_pipeline' in components
    
    # Check LLM component
    llm = components['llm']
    assert 'status' in llm
    assert 'message' in llm
    
    # Check database component
    db = components['database']
    assert 'status' in db
    assert 'card_count' in db
    
    # Check AI pipeline component
    pipeline = components['ai_pipeline'] 
    assert 'status' in pipeline


def test_health_endpoint_llm_status():
    """Test that health endpoint reflects LLM availability"""
    client = app.test_client()
    
    response = client.get('/api/health')
    data = response.get_json()
    
    llm_status = data['components']['llm']['status']
    
    # Should be either healthy or unhealthy
    assert llm_status in ['healthy', 'unhealthy']
    
    # If unhealthy, should have details about why
    if llm_status == 'unhealthy':
        assert 'details' in data['components']['llm']


def test_health_endpoint_caching():
    """Test that health endpoint doesn't get inappropriately cached"""
    client = app.test_client()
    
    response = client.get('/api/health')
    
    # Health endpoint should not have aggressive caching
    cache_control = response.headers.get('Cache-Control', '')
    assert 'no-cache' in cache_control or 'max-age=0' in cache_control or cache_control == ''


def test_health_endpoint_no_secrets():
    """Test that health endpoint doesn't leak sensitive information"""
    client = app.test_client()
    
    response = client.get('/api/health')
    data = response.get_json()
    
    # Convert to string and check for common secrets
    response_str = json.dumps(data).lower()
    
    # Should not contain API keys, passwords, etc.
    assert 'api_key' not in response_str
    assert 'password' not in response_str
    assert 'secret' not in response_str
    assert 'token' not in response_str or 'anythingllm_token' not in response_str  # Allow mention of token field names