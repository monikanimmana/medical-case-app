"""
Phase 3: Intent classification
Three classifiers: majority baseline, TF-IDF + LR, and LLM-based.
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class ClassificationResult:
    intent: str
    confidence: float
    classifier: str  # "majority", "tfidf_lr", "llm"
    reasoning: Optional[str] = None


def classify(text: str) -> ClassificationResult:
    """Classify a message into an intent."""
    # Stub: will be implemented in Phase 3
    pass
