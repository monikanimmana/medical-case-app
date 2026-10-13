"""
Phase 6: Escalation policy
Rule-based escalation decision logic with explicit reasoning.
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
import logging
import os

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    AUTO_HANDLE = "auto_handle"
    ESCALATE = "escalate"


class ReasonCode(Enum):
    """Machine-readable reason codes for escalation decisions."""
    LOW_CONFIDENCE = "low_confidence"
    LOW_GROUNDING = "low_grounding"
    SENSITIVE_INTENT = "sensitive_intent"
    CUSTOMER_FRUSTRATION = "customer_frustration"
    REPEATED_FOLLOWUP = "repeated_followup"
    AUTO_HANDLED = "auto_handled"


@dataclass
class EscalationDecision:
    """An escalation decision with reasoning."""
    decision: DecisionType
    reason_code: ReasonCode
    reason_text: str
    confidence: float  # confidence in the decision itself


class EscalationPolicy:
    """Rule-based escalation policy with thresholds from config."""
    
    def __init__(self):
        # Load thresholds from environment
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
        self.grounding_threshold = float(os.getenv("GROUNDING_THRESHOLD", "0.6"))
        
        # Intents that should always escalate due to sensitivity
        self.sensitive_intents = {"BILLING_ISSUE", "COMPLAINT", "ACCOUNT_ACCESS"}
        
        # Keywords indicating frustration
        self.frustration_keywords = [
            "still", "frustrated", "angry", "unacceptable", "horrible", "terrible",
            "refuse", "cancel", "never", "worst", "terrible", "unacceptable"
        ]
    
    def escalate(
        self,
        message: str,
        intent: str,
        intent_confidence: float,
        grounding_score: float,
        thread_history: Optional[List[str]] = None,
    ) -> EscalationDecision:
        """
        Decide whether to auto-handle or escalate.
        
        Args:
            message: Current customer message
            intent: Classified intent
            intent_confidence: Confidence of intent classification (0-1)
            grounding_score: How grounded the reply is in similar cases (0-1)
            thread_history: Previous messages in conversation
        
        Returns:
            EscalationDecision with reasoning
        """
        # Rule 1: Low intent confidence
        if intent_confidence < self.confidence_threshold:
            return EscalationDecision(
                decision=DecisionType.ESCALATE,
                reason_code=ReasonCode.LOW_CONFIDENCE,
                reason_text=f"Intent classification confidence too low ({intent_confidence:.2f} < {self.confidence_threshold})",
                confidence=0.9
            )
        
        # Rule 2: Sensitive intents with low grounding
        if intent in self.sensitive_intents and grounding_score < self.grounding_threshold:
            return EscalationDecision(
                decision=DecisionType.ESCALATE,
                reason_code=ReasonCode.LOW_GROUNDING,
                reason_text=f"Sensitive intent ({intent}) with low grounding ({grounding_score:.2f} < {self.grounding_threshold})",
                confidence=0.95
            )
        
        # Rule 3: Sensitive intents generally
        if intent in self.sensitive_intents and intent_confidence < 0.85:
            return EscalationDecision(
                decision=DecisionType.ESCALATE,
                reason_code=ReasonCode.SENSITIVE_INTENT,
                reason_text=f"Sensitive intent ({intent}) detected - escalating to human agent",
                confidence=0.9
            )
        
        # Rule 4: Detect frustration
        message_lower = message.lower()
        frustration_count = sum(1 for kw in self.frustration_keywords if kw in message_lower)
        if frustration_count >= 2:
            return EscalationDecision(
                decision=DecisionType.ESCALATE,
                reason_code=ReasonCode.CUSTOMER_FRUSTRATION,
                reason_text=f"Detected {frustration_count} frustration keywords - escalating",
                confidence=0.85
            )
        
        # Rule 5: Repeated follow-up (no resolution in thread history)
        if thread_history and len(thread_history) >= 3:
            # Multiple messages without resolution suggests repeat escalation
            return EscalationDecision(
                decision=DecisionType.ESCALATE,
                reason_code=ReasonCode.REPEATED_FOLLOWUP,
                reason_text="Repeated follow-ups with no resolution - escalating",
                confidence=0.8
            )
        
        # Default: Auto-handle
        return EscalationDecision(
            decision=DecisionType.AUTO_HANDLE,
            reason_code=ReasonCode.AUTO_HANDLED,
            reason_text=f"Auto-handled: Intent={intent}, Confidence={intent_confidence:.2f}, Grounding={grounding_score:.2f}",
            confidence=intent_confidence
        )


# Global escalation policy
_policy = EscalationPolicy()


def escalate(
    message: str,
    intent: str,
    intent_confidence: float,
    grounding_score: float,
    thread_history: Optional[List[str]] = None,
) -> EscalationDecision:
    """
    Decide whether to auto-handle or escalate.
    All thresholds are loaded from config.
    """
    return _policy.escalate(message, intent, intent_confidence, grounding_score, thread_history)
