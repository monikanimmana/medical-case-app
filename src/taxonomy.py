"""
Phase 2: Intent taxonomy
Defines the classification schema and intent labels.
"""

from dataclasses import dataclass
from typing import List

# Stub: will be populated in Phase 2 after clustering analysis

@dataclass
class Intent:
    """Represents a customer support intent."""
    id: str
    name: str
    definition: str
    examples: List[str] = None


# Placeholder taxonomy — will be updated after Phase 2 clustering
TAXONOMY = {
    # To be filled in Phase 2
}

INTENT_LIST: List[Intent] = [
    # To be filled in Phase 2
]
