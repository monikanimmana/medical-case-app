"""
Phase 4: Retrieval-grounded reply drafting
Similar case retrieval for grounding replies.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import cosine

logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """A retrieved precedent case."""
    customer_message: str
    intent: str
    agent_reply: str
    similarity_score: float


# In-memory KB of resolved cases
KNOWLEDGE_BASE: List[Dict] = [
    {
        "customer_message": "Where is my order?",
        "intent": "ORDER_STATUS",
        "agent_reply": "You can track your order using the tracking number sent to your email. Expected delivery is within 5 business days.",
    },
    {
        "customer_message": "I was charged twice for my order",
        "intent": "BILLING_ISSUE",
        "agent_reply": "I apologize for the duplicate charge. We've initiated a refund for the extra charge, which should appear in 3-5 business days.",
    },
    {
        "customer_message": "Can't log into my account",
        "intent": "ACCOUNT_ACCESS",
        "agent_reply": "Please try our password reset at [link]. If you still can't access your account, reply with your email and I'll help you manually.",
    },
    {
        "customer_message": "The app keeps crashing on my phone",
        "intent": "TECHNICAL_ISSUE",
        "agent_reply": "Try uninstalling and reinstalling the app, or clearing your app cache in phone settings. Let me know if that fixes it.",
    },
    {
        "customer_message": "How do I cancel my subscription?",
        "intent": "SUBSCRIPTION",
        "agent_reply": "You can cancel anytime from your account settings under Subscription. No cancellation fees apply.",
    },
    {
        "customer_message": "This product arrived broken",
        "intent": "PRODUCT_QUALITY",
        "agent_reply": "We're sorry to hear that. Please reply with photos and we'll send a replacement or full refund immediately.",
    },
    {
        "customer_message": "How do I use this feature?",
        "intent": "GENERAL_INFO",
        "agent_reply": "Here's a guide to using this feature: [link]. Let me know if you have any questions!",
    },
    {
        "customer_message": "Your service has been horrible",
        "intent": "COMPLAINT",
        "agent_reply": "I sincerely apologize that we haven't met your expectations. I'd like to make this right. Can you tell us more about what went wrong?",
    },
]


class RetrievalEngine:
    """Similarity-based retrieval for grounding replies."""
    
    def __init__(self, kb: Optional[List[Dict]] = None):
        self.kb = kb or KNOWLEDGE_BASE
        self._build_index()
    
    def _build_index(self):
        """Build TF-IDF index for similarity search."""
        messages = [case["customer_message"] for case in self.kb]
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.vectors = self.vectorizer.fit_transform(messages)
        logger.info(f"Built retrieval index with {len(self.kb)} cases")
    
    def top_k_similar(
        self,
        message: str,
        intent: Optional[str] = None,
        k: int = 5
    ) -> List[RetrievalResult]:
        """
        Retrieve top-k similar cases.
        
        Args:
            message: Customer message
            intent: Optional intent filter
            k: Number of results to return
        
        Returns:
            List of RetrievalResult ordered by similarity (descending)
        """
        # Filter KB by intent if provided
        candidate_cases = self.kb
        if intent:
            candidate_cases = [c for c in self.kb if c["intent"] == intent]
            if not candidate_cases:
                candidate_cases = self.kb  # Fallback to all if no match
        
        if not candidate_cases:
            return []
        
        # Vectorize query
        query_vector = self.vectorizer.transform([message])
        
        # Compute similarities
        similarities = []
        for idx, case in enumerate(candidate_cases):
            # Find index in original KB
            kb_idx = self.kb.index(case)
            case_vector = self.vectors[kb_idx]
            
            # Cosine similarity
            sim = 1 - cosine(query_vector.toarray().flatten(), case_vector.toarray().flatten())
            similarities.append((idx, sim))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        results = []
        for idx, sim_score in similarities[:k]:
            case = candidate_cases[idx]
            results.append(RetrievalResult(
                customer_message=case["customer_message"],
                intent=case["intent"],
                agent_reply=case["agent_reply"],
                similarity_score=float(sim_score)
            ))
        
        return results


# Global retrieval engine
_retrieval_engine = RetrievalEngine()


def top_k_similar(
    message: str,
    intent: Optional[str] = None,
    k: int = 5
) -> List[RetrievalResult]:
    """Retrieve top-k similar resolved cases, optionally filtered by intent."""
    return _retrieval_engine.top_k_similar(message, intent, k)


def add_to_kb(customer_message: str, intent: str, agent_reply: str):
    """Add a new case to the knowledge base (for learning from resolved cases)."""
    KNOWLEDGE_BASE.append({
        "customer_message": customer_message,
        "intent": intent,
        "agent_reply": agent_reply,
    })
    _retrieval_engine._build_index()
    logger.info(f"Added case to KB. Total: {len(KNOWLEDGE_BASE)}")
