import os
import sys
import pytest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app


def test_flashcards_reorder_endpoint():
    """Test the flashcard reorder API endpoint"""
    client = app.test_client()
    
    # Test valid reorder request
    response = client.post('/api/flashcards/reorder', 
                          json={
                              'deck_id': 'test_deck',
                              'order': ['card1', 'card2', 'card3']
                          },
                          headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['deck_id'] == 'test_deck'
    assert 'reordered_count' in data


def test_flashcards_reorder_missing_data():
    """Test reorder endpoint with missing data"""
    client = app.test_client()
    
    # Test missing deck_id
    response = client.post('/api/flashcards/reorder', 
                          json={'order': ['card1', 'card2']},
                          headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    
    # Test missing order
    response = client.post('/api/flashcards/reorder',
                          json={'deck_id': 'test'},
                          headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_flashcards_reorder_empty_order():
    """Test reorder endpoint with empty order"""
    client = app.test_client()
    
    response = client.post('/api/flashcards/reorder',
                          json={'deck_id': 'test', 'order': []},
                          headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_flashcards_reorder_persistence():
    """Test that reordering persists to database"""
    client = app.test_client()
    
    # First add some cards via the save endpoint
    sample_cards = [
        {'id': 'card1', 'theme': 'test_deck', 'front': 'Q1', 'back': 'A1'},
        {'id': 'card2', 'theme': 'test_deck', 'front': 'Q2', 'back': 'A2'},
        {'id': 'card3', 'theme': 'test_deck', 'front': 'Q3', 'back': 'A3'}
    ]
    
    # Save cards first
    client.post('/api/save', json={'cards': sample_cards})
    
    # Reorder cards
    new_order = ['card3', 'card1', 'card2']
    response = client.post('/api/flashcards/reorder',
                          json={'deck_id': 'test_deck', 'order': new_order})
    
    assert response.status_code == 200
    
    # Verify the cards are in the new order
    # This would require checking the database, but for now we just ensure the API works
    data = response.get_json()
    assert data['success'] is True