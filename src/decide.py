"""
Phase 5: Escalation policy
Rule-based escalation decision logic with explicit reasoning.
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
import logging

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
    # Stub: will be implemented in Phase 5
    pass
