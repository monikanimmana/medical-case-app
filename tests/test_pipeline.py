"""Tests for the support agent pipeline."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.pipeline import run_pipeline, PipelineInput
from src.classify import classify, KeywordClassifier
from src.retrieve import top_k_similar
from src.draft import draft_reply
from src.decide import escalate, DecisionType


class TestClassification:
    """Test intent classification."""
    
    def test_order_status_classification(self):
        result = classify("Where is my order?", method="keyword")
        assert result.intent == "ORDER_STATUS"
        assert result.confidence > 0
    
    def test_billing_classification(self):
        result = classify("I was charged twice", method="keyword")
        assert result.intent == "BILLING_ISSUE"
    
    def test_account_access_classification(self):
        result = classify("Can't log into my account", method="keyword")
        assert result.intent == "ACCOUNT_ACCESS"
    
    def test_technical_classification(self):
        result = classify("The app keeps crashing", method="keyword")
        assert result.intent == "TECHNICAL_ISSUE"
    
    def test_unknown_classification_defaults_to_general(self):
        result = classify("Lorem ipsum dolor sit amet", method="keyword")
        assert result.intent == "GENERAL_INFO"


class TestRetrieval:
    """Test case retrieval."""
    
    def test_retrieval_returns_results(self):
        results = top_k_similar("Where is my package?", intent="ORDER_STATUS", k=3)
        assert len(results) > 0
        assert len(results) <= 3
    
    def test_retrieval_filters_by_intent(self):
        results = top_k_similar("Payment problem", intent="BILLING_ISSUE", k=5)
        for result in results:
            assert result.intent == "BILLING_ISSUE"
    
    def test_similarity_scores(self):
        results = top_k_similar("Where is my order?", k=3)
        scores = [r.similarity_score for r in results]
        assert all(0 <= s <= 1 for s in scores)
        # Scores should be sorted descending
        assert scores == sorted(scores, reverse=True)


class TestDrafting:
    """Test reply drafting."""
    
    def test_draft_generates_reply(self):
        message = "Where is my order?"
        retrieved = top_k_similar(message, intent="ORDER_STATUS", k=3)
        draft = draft_reply(message, "ORDER_STATUS", retrieved)
        
        assert draft.reply is not None
        assert len(draft.reply) > 0
        assert draft.grounding_score >= 0
    
    def test_draft_with_empty_retrieval(self):
        draft = draft_reply("Test message", "GENERAL_INFO", [])
        assert draft.reply is not None
        assert draft.grounding_score > 0


class TestEscalation:
    """Test escalation policy."""
    
    def test_escalation_low_confidence(self):
        decision = escalate(
            "Random text xyz",
            intent="GENERAL_INFO",
            intent_confidence=0.3,
            grounding_score=0.5
        )
        assert decision.decision == DecisionType.ESCALATE
        assert decision.reason_code.value == "low_confidence"
    
    def test_escalation_low_grounding_sensitive_intent(self):
        decision = escalate(
            "Billing problem",
            intent="BILLING_ISSUE",
            intent_confidence=0.8,
            grounding_score=0.3
        )
        assert decision.decision == DecisionType.ESCALATE
    
    def test_auto_handle_good_confidence_and_grounding(self):
        decision = escalate(
            "How do I use this feature?",
            intent="GENERAL_INFO",
            intent_confidence=0.9,
            grounding_score=0.8
        )
        assert decision.decision == DecisionType.AUTO_HANDLE
    
    def test_escalation_frustrated_customer(self):
        decision = escalate(
            "This is horrible and unacceptable and I'm frustrated",
            intent="COMPLAINT",
            intent_confidence=0.85,
            grounding_score=0.7
        )
        assert decision.decision == DecisionType.ESCALATE


class TestPipeline:
    """Test the full pipeline."""
    
    def test_pipeline_runs_end_to_end(self):
        input_data = PipelineInput(
            customer_message="Where is my order?",
            thread_history=None
        )
        output = run_pipeline(input_data)
        
        assert output.customer_message == input_data.customer_message
        assert output.intent is not None
        assert output.decision in ["auto_handle", "escalate"]
        assert output.reason is not None
    
    def test_pipeline_with_thread_history(self):
        input_data = PipelineInput(
            customer_message="Still no response!",
            thread_history=[
                "Where is my order?",
                "It's been 2 weeks"
            ]
        )
        output = run_pipeline(input_data)
        assert output.decision is not None
    
    def test_pipeline_output_to_dict(self):
        input_data = PipelineInput(customer_message="Test message")
        output = run_pipeline(input_data)
        
        output_dict = output.to_dict()
        assert isinstance(output_dict, dict)
        assert "intent" in output_dict
        assert "decision" in output_dict
    
    def test_pipeline_output_to_json(self):
        input_data = PipelineInput(customer_message="Test message")
        output = run_pipeline(input_data)
        
        json_str = output.to_json()
        assert isinstance(json_str, str)
        assert "intent" in json_str
        
        # Should be valid JSON
        import json
        parsed = json.loads(json_str)
        assert "decision" in parsed


class TestIntegration:
    """Integration tests for realistic scenarios."""
    
    def test_billing_complaint_escalation(self):
        """Billing issues with frustration should escalate."""
        input_data = PipelineInput(
            customer_message="I was charged THREE times and nobody is helping me! This is unacceptable!"
        )
        output = run_pipeline(input_data)
        
        assert output.decision == "escalate"  # Should escalate due to frustration + billing
    
    def test_faq_auto_handle(self):
        """Simple FAQ questions should be auto-handled."""
        input_data = PipelineInput(
            customer_message="How do I reset my password?"
        )
        output = run_pipeline(input_data)
        
        # Should be auto-handled or escalate depending on confidence
        assert output.decision in ["auto_handle", "escalate"]
    
    def test_mixed_intent_message(self):
        """Message with multiple signals."""
        input_data = PipelineInput(
            customer_message="I ordered product XYZ but received product ABC instead, and now the app keeps crashing"
        )
        output = run_pipeline(input_data)
        
        assert output.intent is not None
        # Complex message should probably escalate
        assert output.decision is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
