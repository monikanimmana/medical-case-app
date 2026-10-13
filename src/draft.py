"""
Phase 5: Grounded reply drafting
Generates replies based on retrieved precedents with grounding scores.
"""

from dataclasses import dataclass
from typing import List, Optional
import logging
import os
import json

from src.retrieve import RetrievalResult

logger = logging.getLogger(__name__)

@dataclass
class DraftResult:
    """A drafted reply with supporting evidence."""
    reply: str
    grounding_score: float  # 0-1, how grounded in precedents
    supporting_cases: List[str]  # Retrieved case messages
    evidence: List[str]  # Snippets from retrieved cases


class ReplyDrafter:
    """Draft customer support replies grounded in retrieved cases."""
    
    def __init__(self):
        self.llm_provider = os.getenv("LLM_PROVIDER", "gemini")
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
            self.genai = genai
        except ImportError:
            logger.warning("google.generativeai not available")
            self.genai = None
    
    def draft_reply(
        self,
        message: str,
        intent: str,
        retrieved_cases: List[RetrievalResult],
        conversation_context: Optional[str] = None,
    ) -> DraftResult:
        """
        Draft a reply grounded in retrieved precedents.
        
        Args:
            message: Customer message
            intent: Classified intent
            retrieved_cases: List of similar resolved cases
            conversation_context: Previous messages in thread
        
        Returns:
            DraftResult with reply, grounding score, and evidence
        """
        if not retrieved_cases:
            # No retrieval, use template-based reply
            return self._template_reply(message, intent)
        
        if self.genai and os.getenv("GEMINI_API_KEY"):
            return self._llm_draft(message, intent, retrieved_cases, conversation_context)
        else:
            return self._rule_based_draft(message, intent, retrieved_cases)
    
    def _template_reply(self, message: str, intent: str) -> DraftResult:
        """Generate template-based reply when no cases are retrieved."""
        templates = {
            "ORDER_STATUS": "Thank you for your inquiry. You can track your order using the link in your confirmation email. We typically deliver within 5-7 business days.",
            "BILLING_ISSUE": "We apologize if there's a billing issue. Please reply with details and we'll investigate and resolve it immediately.",
            "ACCOUNT_ACCESS": "If you're having trouble accessing your account, please try resetting your password. If that doesn't work, we're happy to help manually.",
            "TECHNICAL_ISSUE": "We're sorry you're experiencing technical issues. Please try the troubleshooting steps in our help center, or let us know and we'll investigate.",
            "SUBSCRIPTION": "You can manage your subscription anytime from your account settings. We're here if you have any questions!",
            "PRODUCT_QUALITY": "We're sorry if you received a defective product. Please share details and we'll send a replacement or refund right away.",
            "GENERAL_INFO": "Thank you for your question! Check out our help center for more information, or reply if you need further assistance.",
            "COMPLAINT": "We truly apologize that we haven't met your expectations. We'd like to make this right. Could you tell us more about your experience?",
        }
        
        reply = templates.get(intent, "Thank you for reaching out. How can we help?")
        
        return DraftResult(
            reply=reply,
            grounding_score=0.3,  # Low: template-based
            supporting_cases=[],
            evidence=[]
        )
    
    def _rule_based_draft(
        self,
        message: str,
        intent: str,
        retrieved_cases: List[RetrievalResult]
    ) -> DraftResult:
        """Draft reply using rule-based approach from similar cases."""
        if not retrieved_cases:
            return self._template_reply(message, intent)
        
        # Use the best matching case as template
        best_case = retrieved_cases[0]
        grounding_score = best_case.similarity_score
        
        # Build evidence list
        evidence = [f"'{case.agent_reply[:80]}...'" for case in retrieved_cases[:2]]
        
        # Compose reply
        reply = f"Thank you for reaching out. Based on similar cases, here's what I can help with:\n\n{best_case.agent_reply}"
        
        if len(retrieved_cases) > 1 and retrieved_cases[1].similarity_score > 0.6:
            reply += f"\n\nAlternatively: {retrieved_cases[1].agent_reply[:100]}..."
        
        return DraftResult(
            reply=reply,
            grounding_score=float(grounding_score),
            supporting_cases=[case.customer_message for case in retrieved_cases],
            evidence=evidence
        )
    
    def _llm_draft(
        self,
        message: str,
        intent: str,
        retrieved_cases: List[RetrievalResult],
        conversation_context: Optional[str]
    ) -> DraftResult:
        """Draft reply using LLM (Gemini) with retrieved cases as grounding."""
        try:
            # Build context from similar cases
            cases_context = "\n".join([
                f"- Customer: {case.customer_message}\n  Agent: {case.agent_reply}\n  (Similarity: {case.similarity_score:.2f})"
                for case in retrieved_cases[:3]
            ])
            
            prompt = f"""You are a helpful customer support agent. Based on these similar resolved cases:

{cases_context}

And the customer's message: "{message}"
Intent: {intent}

Draft a professional, empathetic reply that:
1. Addresses their concern directly
2. Is grounded in the similar cases above
3. Is concise (2-3 sentences max)
4. Provides clear next steps

Reply in JSON:
{{
    "reply": "<your reply here>",
    "grounding_score": <0.0-1.0>,
    "confidence": <0.0-1.0>
}}"""
            
            model = self.genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            
            # Parse response
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                return DraftResult(
                    reply=result.get("reply", "Thank you for contacting us."),
                    grounding_score=min(float(result.get("grounding_score", 0.7)), 1.0),
                    supporting_cases=[case.customer_message for case in retrieved_cases],
                    evidence=[f"'{case.agent_reply[:80]}...'" for case in retrieved_cases[:2]]
                )
        except Exception as e:
            logger.error(f"LLM drafting failed: {e}")
        
        # Fallback to rule-based
        return self._rule_based_draft(message, intent, retrieved_cases)


# Global drafter
_drafter = ReplyDrafter()


def draft_reply(
    message: str,
    intent: str,
    retrieved_cases: List[RetrievalResult],
    conversation_context: Optional[str] = None,
) -> DraftResult:
    """Draft a reply grounded in retrieved precedents."""
    return _drafter.draft_reply(message, intent, retrieved_cases, conversation_context)
