"""
HUKUM Chatbot - Intent Detection Module.

Classifies user queries into intent categories using keyword matching.
Completely independent of Streamlit or UI frameworks.
"""

from .config import INTENT_KEYWORDS


def detect_intent(query: str) -> str:
    """
    Classify a user query into an intent category.

    Uses keyword-based routing to determine which pipeline should handle the query.

    Args:
        query: User input string

    Returns:
        str: One of ["pricing", "matchmaking", "trust", "help", "general"]
    """
    query_lower = query.lower().strip()

    # Check pricing intent first
    if any(word in query_lower for word in INTENT_KEYWORDS["pricing"]):
        return "pricing"

    # Check matchmaking intent
    if any(word in query_lower for word in INTENT_KEYWORDS["matchmaking"]):
        return "matchmaking"

    # Check trust/risk intent
    if any(word in query_lower for word in INTENT_KEYWORDS["trust"]):
        return "trust"

    # Check help intent (special case)
    if "post a job" in query_lower:
        return "help"

    # Default fallback
    return "general"
