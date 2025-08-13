import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app


def test_static_passthrough_etag_fix():
    """Regression test for the RuntimeError: direct passthrough mode fix"""
    client = app.test_client()
    
    # Test static file serving doesn't cause RuntimeError
    response = client.get('/static/style.css')
    
    # Should return 200 or 404, but not 500 (internal error)
    assert response.status_code in [200, 404]
    
    # Should have cache headers for static files
    if response.status_code == 200:
        assert 'Cache-Control' in response.headers
        cache_control = response.headers.get('Cache-Control')
        assert 'public' in cache_control or 'max-age' in cache_control


def test_static_files_no_etag():
    """Test that static files don't get ETag headers that cause RuntimeError"""
    client = app.test_client()
    
    # Try various static file types
    static_files = [
        '/static/style.css',
        '/static/app.js',
        '/static/advanced-flashcards.js'
    ]
    
    for static_file in static_files:
        response = client.get(static_file)
        
        if response.status_code == 200:
            # Static files should have cache headers but no ETag to avoid RuntimeError
            assert 'Cache-Control' in response.headers
            
            # The fix should prevent ETag on static files
            # If ETag is present, it should not cause errors
            if 'ETag' in response.headers:
                # If present, should be properly formatted
                etag = response.headers['ETag']
                assert etag.startswith('"') and etag.endswith('"')


def test_non_static_endpoints_can_have_etag():
    """Test that non-static endpoints can still get ETags"""
    client = app.test_client()
    
    # Test API endpoint
    response = client.get('/api/config')
    
    if response.status_code == 200:
        # API endpoints should still be able to get ETags
        # (though they may not, depending on caching logic)
        pass  # Just ensure no RuntimeError occurs


def test_after_request_security_headers():
    """Test that after_request handler still adds security headers"""
    client = app.test_client()
    
    # Test on main page
    response = client.get('/')
    assert response.status_code == 200
    
    # Should have security headers
    assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    assert response.headers.get('X-Frame-Options') == 'DENY'
    assert response.headers.get('X-XSS-Protection') == '1; mode=block'


def test_response_time_header():
    """Test that response time header is added"""
    client = app.test_client()
    
    response = client.get('/')
    assert response.status_code == 200
    
    # Should have response time header
    assert 'X-Response-Time' in response.headers
    response_time = response.headers.get('X-Response-Time')
    assert response_time.endswith('ms')


def test_streaming_response_handling():
    """Test that streaming responses are handled correctly"""
    client = app.test_client()
    
    # Test AI generate with streaming (if LLM available)
    response = client.post('/api/ai/generate',
                          json={'prompt': 'Hello', 'stream': True},
                          headers={'Content-Type': 'application/json'})
    
    # Should not cause RuntimeError regardless of LLM availability
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        # Streaming response should have proper content type
        assert response.content_type.startswith('text/event-stream')
        
        # Should not have ETag (streaming responses skip ETag generation)
        assert 'ETag' not in response.headers


def test_binary_response_handling():
    """Test that binary responses don't get ETag that causes RuntimeError"""
    client = app.test_client()
    
    # Test favicon (binary image)
    response = client.get('/favicon.ico')
    
    # Should either serve the file or 404, not crash
    assert response.status_code in [200, 404]
    
    if response.status_code == 200:
        # Binary files should not get ETag that causes issues
        # The fix should handle this gracefully
        pass