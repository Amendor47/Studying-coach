import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app


def test_basic_chat_endpoint():
    """Test the basic chat endpoint works."""
    client = app.test_client()
    
    response = client.post('/api/chat', 
                          json={'message': 'Hello'},
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'answer' in data
    assert isinstance(data['answer'], str)


def test_chat_stream_endpoint():
    """Test the streaming chat endpoint returns proper SSE format."""
    client = app.test_client()
    
    response = client.post('/api/chat/stream',
                          json={'message': 'Test question'},
                          content_type='application/json')
    
    assert response.status_code == 200
    assert response.content_type == 'text/event-stream; charset=utf-8'
    
    # Check that response contains SSE data
    data = response.data.decode('utf-8')
    assert 'data:' in data
    assert 'done' in data


def test_chat_empty_message():
    """Test chat endpoint handles empty messages gracefully."""
    client = app.test_client()
    
    response = client.post('/api/chat',
                          json={'message': ''},
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'answer' in data


def test_chat_malformed_request():
    """Test chat endpoint handles malformed requests."""
    client = app.test_client()
    
    # Missing message field
    response = client.post('/api/chat',
                          json={},
                          content_type='application/json')
    
    assert response.status_code == 200  # Should handle gracefully
    data = response.get_json()
    assert 'answer' in data


def test_chat_stream_malformed_request():
    """Test streaming chat endpoint handles malformed requests."""
    client = app.test_client()
    
    response = client.post('/api/chat/stream',
                          json={},
                          content_type='application/json')
    
    assert response.status_code == 200
    assert response.content_type == 'text/event-stream; charset=utf-8'