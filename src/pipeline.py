"""
Pipeline: orchestrates the full support agent workflow.
Phases: Classify → Retrieve → Draft → Decide → Output
"""

import logging
from dataclasses import dataclass
from typing import Optional, List
import json

from src.classify import classify
from src.retrieve import top_k_similar
from src.draft import draft_reply
from src.decide import escalate

logger = logging.getLogger(__name__)


@dataclass
class PipelineInput:
    """Input to the support agent."""
    customer_message: str
    thread_history: Optional[List[str]] = None
    brand: str = "support"


@dataclass
class PipelineOutput:
    """Output from the support agent."""
    customer_message: str
    intent: str
    intent_name: str
    intent_confidence: float
    decision: str  # "auto_handle" or "escalate"
    reason: str
    reason_code: str
    draft_reply: Optional[str] = None
    grounding_score: Optional[float] = None
    supporting_cases: Optional[List[str]] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "customer_message": self.customer_message,
            "intent": self.intent,
            "intent_name": self.intent_name,
            "intent_confidence": round(self.intent_confidence, 3),
            "decision": self.decision,
            "reason": self.reason,
            "reason_code": self.reason_code,
            "draft_reply": self.draft_reply,
            "grounding_score": round(self.grounding_score, 3) if self.grounding_score else None,
            "supporting_cases": self.supporting_cases or [],
        }
    
    def to_json(self):
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class SupportAgentPipeline:
    """Full support agent pipeline."""
    
    def __init__(self, classify_method: str = "keyword"):
        """
        Initialize pipeline.
        
        Args:
            classify_method: "keyword", "tfidf_lr", "llm", or "ensemble"
        """
        self.classify_method = classify_method
        logger.info(f"Initialized pipeline with classify_method={classify_method}")
    
    def run(self, input_data: PipelineInput) -> PipelineOutput:
        """
        Run the full pipeline: classify → retrieve → draft → decide → output.
        
        Process:
        1. **Classify**: Determine customer intent
        2. **Retrieve**: Find similar resolved cases
        3. **Draft**: Generate grounded reply
        4. **Decide**: Determine escalation
        5. **Output**: Format result
        """
        logger.info(f"Processing: {input_data.customer_message[:100]}")
        
        # Phase 3: Classify intent
        logger.debug("Phase 3: Classification")
        classification = classify(input_data.customer_message, method=self.classify_method)
        
        # Phase 4: Retrieve similar cases
        logger.debug(f"Phase 4: Retrieval for intent={classification.intent}")
        retrieved_cases = top_k_similar(
            input_data.customer_message,
            intent=classification.intent,
            k=5
        )
        
        # Phase 5: Draft reply
        logger.debug("Phase 5: Reply drafting")
        draft = draft_reply(
            input_data.customer_message,
            classification.intent,
            retrieved_cases,
            "\n".join(input_data.thread_history) if input_data.thread_history else None
        )
        
        # Phase 6: Escalation decision
        logger.debug("Phase 6: Escalation decision")
        decision = escalate(
            input_data.customer_message,
            classification.intent,
            classification.confidence,
            draft.grounding_score,
            input_data.thread_history
        )
        
        # Format output
        output = PipelineOutput(
            customer_message=input_data.customer_message,
            intent=classification.intent,
            intent_name=classification.intent_name,
            intent_confidence=classification.confidence,
            decision=decision.decision.value,
            reason=decision.reason_text,
            reason_code=decision.reason_code.value,
            draft_reply=draft.reply if decision.decision.value == "auto_handle" else None,
            grounding_score=draft.grounding_score,
            supporting_cases=draft.supporting_cases,
        )
        
        logger.info(f"Decision: {decision.decision.value} ({decision.reason_code.value})")
        return output


# Global pipeline instance
_pipeline = SupportAgentPipeline()


def run_pipeline(
    input_data: PipelineInput,
    classify_method: str = "keyword"
) -> PipelineOutput:
    """
    Run the full support agent pipeline.
    
    Args:
        input_data: PipelineInput with customer message and thread history
        classify_method: Classification method to use
    
    Returns:
        PipelineOutput with decision and reasoning
    """
    pipeline = SupportAgentPipeline(classify_method=classify_method)
    return pipeline.run(input_data)
