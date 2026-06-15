"""
HUKUM Chatbot - Intent Detection Module.

Classifies user queries into intent categories using keyword matching.
Completely independent of Streamlit or UI frameworks.
"""

from .config import INTENT_KEYWORDS


def detect_intent(query: str) -> str:
    """
    Classify a user query into an intent category.

    Uses keyword-based scoring to determine which pipeline should handle the query.
    Counts keyword matches per intent and selects the highest-scoring one.
    On ties, priority order is: trust > pricing > matchmaking.

    Args:
        query: User input string

    Returns:
        str: One of ["pricing", "matchmaking", "trust", "help", "general"]
    """
    query_lower = query.lower().strip()

    # Check help intent first (exact phrase, no ambiguity)
    if "post a job" in query_lower:
        return "help"

    # Helper function for phrase-based matching
    def count_matches(phrases, text):
        return sum(1 for phrase in phrases if phrase in text)

    # Score each intent using phrase-aware matching
    scored_intents = [
        ("trust", count_matches(INTENT_KEYWORDS["trust"], query_lower) * 2),
        ("pricing", count_matches(INTENT_KEYWORDS["pricing"], query_lower)),
        ("matchmaking", count_matches(INTENT_KEYWORDS["matchmaking"], query_lower)),
    ]

    # Find the best intent (highest score wins; list order breaks ties)
    best_intent, best_score = max(scored_intents, key=lambda x: x[1])

    if best_score > 0:
        return best_intent

    # Default fallback
    return "general"
