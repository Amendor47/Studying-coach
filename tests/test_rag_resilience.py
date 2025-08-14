import io
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.rag import RAGIndex, get_context


def test_rag_index_error_resilience():
    """Test that RAGIndex gracefully handles cases that previously caused IndexError"""
    
    # Test case 1: Empty text should not cause IndexError
    context = get_context("", 5)
    assert isinstance(context, list)
    assert context == []
    
    # Test case 2: Whitespace-only text should not cause IndexError
    context = get_context("\n\n  \n  \n", 5) 
    assert isinstance(context, list)
    assert context == []
    
    # Test case 3: Single line should work
    context = get_context("Single line text", 3)
    assert isinstance(context, list)
    assert context == ["Single line text"]
    
    # Test case 4: Multiple calls should be consistent
    text = "Line 1\nLine 2\nLine 3"
    context1 = get_context(text, 5)
    context2 = get_context(text, 5)
    assert context1 == context2
    assert len(context1) == 3


def test_rag_index_direct_manipulation():
    """Test RAGIndex direct usage to ensure state consistency"""
    
    index = RAGIndex()
    
    # Test initial state
    assert index.passages == []
    assert index.search("query", 5) == []
    
    # Test build with valid text
    index.build("Test line 1\nTest line 2")
    assert len(index.passages) == 2
    
    result = index.search("test", 5)
    assert isinstance(result, list)
    assert len(result) <= 2
    
    # Test build with empty text (should reset state)
    index.build("")
    assert index.passages == []
    assert index.search("query", 5) == []
    
    # Test build with whitespace only
    index.build("\n  \n  \n")
    assert index.passages == []


def test_rag_index_bounds_checking():
    """Test that search method properly handles bounds checking"""
    
    index = RAGIndex()
    
    # Create a scenario where we have passages
    index.build("Line 1\nLine 2\nLine 3")
    assert len(index.passages) == 3
    
    # Test search with different k values
    result1 = index.search("test", 1)
    assert isinstance(result1, list)
    assert len(result1) <= 1
    
    result5 = index.search("test", 5)
    assert isinstance(result5, list)
    assert len(result5) <= 3  # Should not exceed number of passages
    
    # Test with very large k
    result100 = index.search("test", 100)
    assert isinstance(result100, list)
    assert len(result100) <= 3  # Should not exceed number of passages


if __name__ == "__main__":
    test_rag_index_error_resilience()
    test_rag_index_direct_manipulation()
    test_rag_index_bounds_checking()
    print("All RAG resilience tests passed!")