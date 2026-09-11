"""
Pipeline: orchestrates the full support agent workflow.
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PipelineInput:
    """Input to the support agent."""
    customer_message: str
    thread_history: Optional[list] = None


@dataclass
class PipelineOutput:
    """Output from the support agent."""
    customer_message: str
    intent: str
    intent_confidence: float
    decision: str  # "auto_handle" or "escalate"
    reason: str
    draft_reply: Optional[str] = None
    grounding_score: Optional[float] = None
    supporting_cases: Optional[list] = None


def run_pipeline(input_data: PipelineInput) -> PipelineOutput:
    """
    Run the full pipeline: classify → retrieve → draft → decide → output.
    """
    # Stub: will be implemented after all phases
    pass
