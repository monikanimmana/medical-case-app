"""
Phase 4: Grounded reply drafting
Generates replies based on retrieved precedents with grounding scores.
"""

from dataclasses import dataclass
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class DraftResult:
    """A drafted reply with supporting evidence."""
    reply: str
    grounding_score: float  # 0-1, how grounded in precedents
    supporting_cases: List[str]  # IDs or indices of retrieved cases
    evidence: List[str]  # Snippets from retrieved cases


def draft_reply(
    message: str,
    intent: str,
    retrieved_cases: List,  # From retrieve.top_k_similar
    conversation_context: Optional[str] = None,
) -> DraftResult:
    """Draft a reply grounded in retrieved precedents."""
    # Stub: will be implemented in Phase 4
    pass
