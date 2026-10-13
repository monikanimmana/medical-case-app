"""
Phase 2: Intent taxonomy
Defines the classification schema and intent labels.
"""

from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Intent:
    """Represents a customer support intent."""
    id: str
    name: str
    definition: str
    keywords: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


# Intent taxonomy - discovered via clustering in Phase 2
INTENT_LIST: List[Intent] = [
    Intent(
        id="ORDER_STATUS",
        name="Order Status Inquiry",
        definition="Customer asking about order status, tracking, or delivery",
        keywords=["order", "tracking", "delivery", "where is", "status", "arrived"],
        examples=[
            "Where is my order?",
            "My package hasn't arrived yet",
            "Can you track my delivery?",
        ]
    ),
    Intent(
        id="BILLING_ISSUE",
        name="Billing/Payment Issue",
        definition="Issues with charges, refunds, billing, or payment processing",
        keywords=["charge", "refund", "billing", "payment", "credit card", "invoice"],
        examples=[
            "I was charged twice",
            "Can I get a refund?",
            "Why is this on my bill?",
        ]
    ),
    Intent(
        id="ACCOUNT_ACCESS",
        name="Account Access Problem",
        definition="Can't login, password reset, account locked, 2FA issues",
        keywords=["login", "password", "account", "locked", "2fa", "reset"],
        examples=[
            "I can't log in",
            "Password reset not working",
            "My account is locked",
        ]
    ),
    Intent(
        id="TECHNICAL_ISSUE",
        name="Technical/App Problem",
        definition="App crashes, bugs, feature not working, compatibility issues",
        keywords=["crash", "bug", "error", "broken", "app", "not working"],
        examples=[
            "The app keeps crashing",
            "Feature isn't working",
            "I'm getting an error",
        ]
    ),
    Intent(
        id="SUBSCRIPTION",
        name="Subscription Management",
        definition="Upgrade, downgrade, cancel, or manage subscriptions",
        keywords=["subscribe", "unsubscribe", "cancel", "upgrade", "subscription"],
        examples=[
            "How do I cancel my subscription?",
            "I want to upgrade my plan",
            "Can I downgrade?",
        ]
    ),
    Intent(
        id="PRODUCT_QUALITY",
        name="Product Quality/Return",
        definition="Defective product, returns, quality concerns",
        keywords=["defective", "quality", "broken", "return", "damaged"],
        examples=[
            "This product is broken",
            "How do I return this?",
            "This is poor quality",
        ]
    ),
    Intent(
        id="GENERAL_INFO",
        name="General Information",
        definition="General questions, feature info, how-to, documentation",
        keywords=["how", "what", "feature", "help", "explain", "info"],
        examples=[
            "How do I use this feature?",
            "What is this?",
            "Can you explain this?",
        ]
    ),
    Intent(
        id="COMPLAINT",
        name="Complaint/Dissatisfaction",
        definition="Complaints about service, poor experience, frustration",
        keywords=["disappointed", "frustrating", "unacceptable", "horrible", "terrible"],
        examples=[
            "Your service is terrible",
            "I'm very disappointed",
            "This is unacceptable",
        ]
    ),
]

# Map intent name to Intent object
TAXONOMY: Dict[str, Intent] = {intent.id: intent for intent in INTENT_LIST}
INTENT_NAMES: Dict[str, str] = {intent.id: intent.name for intent in INTENT_LIST}
INTENT_KEYWORDS: Dict[str, List[str]] = {intent.id: intent.keywords for intent in INTENT_LIST}
