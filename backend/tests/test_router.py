import pytest
from unittest.mock import MagicMock
from app.router.routing_engine import RoutingEngine
from app.classifier.semantic_classifier import SemanticClassifier

def test_routing_coding_escalation():
    """
    Tests that coding queries route to remote immediately.
    """
    mock_classifier = MagicMock(spec=SemanticClassifier)
    mock_classifier.classify.return_value = "coding"
    
    engine = RoutingEngine(classifier=mock_classifier)
    route, reason, est = engine.route("def test_function(): pass")
    
    assert route == "remote"
    assert "coding" in reason.lower()

def test_routing_math_escalation():
    """
    Tests that math queries route to remote immediately.
    """
    mock_classifier = MagicMock(spec=SemanticClassifier)
    mock_classifier.classify.return_value = "math"
    
    engine = RoutingEngine(classifier=mock_classifier)
    route, reason, est = engine.route("What is 15 * 6?")
    
    assert route == "remote"
    assert "math" in reason.lower()

def test_routing_short_general_to_local():
    """
    Tests that short general questions are routed locally.
    """
    mock_classifier = MagicMock(spec=SemanticClassifier)
    mock_classifier.classify.return_value = "general_qa"
    
    engine = RoutingEngine(classifier=mock_classifier)
    route, reason, est = engine.route("What is the capital of Japan?")
    
    assert route == "local"
    assert "local" in reason.lower()

def test_routing_long_general_to_remote():
    """
    Tests that long general questions exceed length threshold and route to remote.
    """
    mock_classifier = MagicMock(spec=SemanticClassifier)
    mock_classifier.classify.return_value = "general_qa"
    
    engine = RoutingEngine(classifier=mock_classifier)
    
    # 26 words > 25 threshold
    long_prompt = " ".join(["word"] * 26)
    route, reason, est = engine.route(long_prompt)
    
    assert route == "remote"
    assert "exceeds local threshold" in reason.lower()
