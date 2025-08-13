import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app


def test_after_request_static_files_safe():
    """Test that after_request doesn't cause RuntimeError on static files."""
    client = app.test_client()
    
    # Test static CSS file
    resp = client.get('/static/style.css')
    assert resp.status_code == 200
    assert resp.content_type.startswith('text/css')
    # Flask's default static file handler should handle ETags, not our after_request
    assert 'ETag' in resp.headers
    
    # Test static JS file
    resp = client.get('/static/app.js')
    assert resp.status_code == 200
    assert resp.content_type.startswith('text/javascript')
    assert 'ETag' in resp.headers


def test_after_request_html_responses():
    """Test that after_request adds ETags to HTML responses."""
    client = app.test_client()
    
    # Test main page
    resp = client.get('/')
    assert resp.status_code == 200
    assert resp.content_type.startswith('text/html')
    # Our after_request should add an ETag to HTML responses
    assert 'ETag' in resp.headers


def test_after_request_api_responses():
    """Test that after_request adds ETags to API responses."""
    client = app.test_client()
    
    # Test API endpoint
    resp = client.get('/api/themes')
    assert resp.status_code == 200
    assert resp.content_type.startswith('application/json')
    # Our after_request should add an ETag to JSON responses
    assert 'ETag' in resp.headers


def test_favicon_and_icons_accessible():
    """Test that favicon and apple touch icons are now accessible."""
    client = app.test_client()
    
    # Test favicon
    resp = client.get('/favicon.ico')
    assert resp.status_code == 200
    assert resp.content_type == 'image/vnd.microsoft.icon'
    
    # Test apple touch icons
    resp = client.get('/apple-touch-icon.png')
    assert resp.status_code == 200
    assert resp.content_type == 'image/png'
    
    resp = client.get('/apple-touch-icon-precomposed.png')
    assert resp.status_code == 200
    assert resp.content_type == 'image/png'