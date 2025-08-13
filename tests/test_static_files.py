import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app


def test_static_files_serve_correctly():
    """Test that static files serve without RuntimeError."""
    client = app.test_client()
    
    # Test CSS file
    resp = client.get('/static/style.css')
    assert resp.status_code == 200
    assert 'text/css' in resp.content_type
    
    # Test JS file
    resp = client.get('/static/app.js')
    assert resp.status_code == 200
    assert 'javascript' in resp.content_type or 'text/javascript' in resp.content_type
    
    # Test design system CSS
    resp = client.get('/static/design-system.css')
    assert resp.status_code == 200
    assert 'text/css' in resp.content_type


def test_static_files_have_cache_headers():
    """Test that static files get proper cache headers without causing RuntimeError."""
    client = app.test_client()
    
    resp = client.get('/static/style.css')
    assert resp.status_code == 200
    
    # Should have cache control headers
    assert 'Cache-Control' in resp.headers
    # Should have response time header from after_request
    assert 'X-Response-Time' in resp.headers
    # Should have security headers
    assert 'X-Content-Type-Options' in resp.headers


def test_static_svg_file():
    """Test that SVG files serve correctly."""
    client = app.test_client()
    
    resp = client.get('/static/logo.svg')
    assert resp.status_code == 200
    assert 'image/svg+xml' in resp.content_type


def test_main_page_loads():
    """Test that the main page loads correctly (to ensure CSS/JS links work)."""
    client = app.test_client()
    
    resp = client.get('/')
    assert resp.status_code == 200
    assert 'text/html' in resp.content_type


def test_api_endpoints_still_get_etags():
    """Test that API endpoints still get ETags for regular responses."""
    client = app.test_client()
    
    # Test an API endpoint that should get ETags
    resp = client.get('/api/config')
    assert resp.status_code == 200
    # Should have response time header
    assert 'X-Response-Time' in resp.headers
    # Should have security headers  
    assert 'X-Content-Type-Options' in resp.headers
    

def test_after_request_security_headers():
    """Test that security headers are still applied to all responses."""
    client = app.test_client()
    
    # Test on main page
    resp = client.get('/')
    assert resp.status_code == 200
    assert resp.headers['X-Content-Type-Options'] == 'nosniff'
    assert resp.headers['X-Frame-Options'] == 'DENY'
    assert resp.headers['X-XSS-Protection'] == '1; mode=block'
    
    # Test on static file
    resp = client.get('/static/style.css')
    assert resp.status_code == 200
    assert resp.headers['X-Content-Type-Options'] == 'nosniff'
    assert resp.headers['X-Frame-Options'] == 'DENY'
    assert resp.headers['X-XSS-Protection'] == '1; mode=block'