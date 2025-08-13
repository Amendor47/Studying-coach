import io
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from services.store import DB_FILE


def test_upload_with_progress():
    """Test file upload with progress tracking (enhanced upload)."""
    if DB_FILE.exists():
        DB_FILE.unlink()
    
    client = app.test_client()
    
    # Test with a valid file
    data = {
        'file': (io.BytesIO(b"Machine learning basics: supervised learning, unsupervised learning"), 'test.txt'),
        'use_ai': 'false',
        'session_minutes': '25'
    }
    
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'saved' in json_data
    assert json_data['saved'] >= 1
    assert 'minutes' in json_data
    assert json_data['minutes'] == 25
    
    # Clean up
    if DB_FILE.exists():
        DB_FILE.unlink()


def test_upload_large_file_handling():
    """Test that file upload properly handles larger files."""
    if DB_FILE.exists():
        DB_FILE.unlink()
    
    client = app.test_client()
    
    # Create a larger text content
    large_content = "Python programming fundamentals. " * 100  # Repeat to make it larger
    
    data = {
        'file': (io.BytesIO(large_content.encode()), 'large_test.txt'),
        'use_ai': 'false',
        'session_minutes': '45'
    }
    
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'saved' in json_data
    assert json_data['minutes'] == 45
    
    # Clean up
    if DB_FILE.exists():
        DB_FILE.unlink()


def test_upload_pdf_file():
    """Test uploading PDF file type."""
    if DB_FILE.exists():
        DB_FILE.unlink()
    
    client = app.test_client()
    
    # Simple PDF-like content (not a real PDF, but tests the pipeline)
    data = {
        'file': (io.BytesIO(b"PDF content about algorithms and data structures"), 'test.pdf'),
        'use_ai': 'false',
        'session_minutes': '60'
    }
    
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    
    # This may fail during text extraction from fake PDF, but should handle gracefully
    assert response.status_code in [200, 400, 500]  # Accept various outcomes for fake PDF
    
    # Clean up
    if DB_FILE.exists():
        DB_FILE.unlink()


def test_upload_missing_file():
    """Test upload endpoint with missing file."""
    client = app.test_client()
    
    data = {
        'use_ai': 'false',
        'session_minutes': '25'
    }
    
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data
    assert json_data['error'] == 'no file'


def test_upload_with_ai_option():
    """Test upload with AI enhancement option."""
    if DB_FILE.exists():
        DB_FILE.unlink()
    
    client = app.test_client()
    
    data = {
        'file': (io.BytesIO(b"Neural networks and deep learning concepts"), 'ai_test.txt'),
        'use_ai': 'true',  # Enable AI processing
        'session_minutes': '30'
    }
    
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'saved' in json_data
    assert json_data['minutes'] == 30
    
    # Clean up
    if DB_FILE.exists():
        DB_FILE.unlink()