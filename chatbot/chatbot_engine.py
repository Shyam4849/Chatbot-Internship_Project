"""
HUKUM Chatbot - Core Engine Module.

Main orchestration layer that ties all modules together.
Provides the primary interface for chatbot operations.
Completely independent of Streamlit or UI frameworks.
"""

from datetime import datetime
from . import intent_detector, response_generator, memory_manager
from .config import LOGS_FILE


def chat(query: str, session_id: str = "default") -> dict:
    """
    Main chatbot interface: Process user query and generate response.

    This is the primary function to call when integrating the chatbot.
    It handles the complete chat pipeline:
    1. Check for conversational context memory follow-ups
    2. Detect user intent (if not a follow-up)
    3. Generate appropriate response (with context updating)
    4. Return structured result

    Args:
        query: User input string
        session_id: Session identifier to track conversational context

    Returns:
        dict: {
            "intent": str,              # Detected intent
            "response": str,            # Generated response (HTML or Markdown)
            "is_html": bool,            # Whether response is HTML or plain text
            "timestamp": str,           # ISO format timestamp
        }
    """
    # Check if this is a conversational follow-up query
    follow_up_type = memory_manager.detect_follow_up_type(query)

    if follow_up_type is not None:
        # Process follow-up using stored session context
        response_data = memory_manager.process_follow_up(query, session_id)
    else:
        # Detect user intent
        intent = intent_detector.detect_intent(query)

        # Generate response based on intent
        response_data = response_generator.format_response(intent, query, session_id)

        # Update last detected intent in context
        memory_manager.update_context(session_id, {
            "last_intent": intent
        })

    # Update general query and response in context
    memory_manager.update_context(session_id, {
        "last_query": query,
        "last_response": response_data.get("response")
    })

    # Add timestamp
    timestamp = datetime.now().isoformat()
    response_data["timestamp"] = timestamp

    return response_data


def log_query(query: str, intent: str) -> None:
    """
    Log user query and detected intent to file for analytics and debugging.

    Appends to chatbot_logs.txt with timestamp, intent, and query.

    Args:
        query: Original user query
        intent: Detected intent category

    Example:
        >>> log_query("Find a painter", "matchmaking")
        # Writes: "2026-06-12 10:30:45.123456 | MATCHMAKING | Find a painter"
    """
    try:
        with open(LOGS_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.now()
            f.write(f"{timestamp} | {intent.upper()} | {query}\n")
    except Exception as e:
        print(f"[Warning] Failed to log query: {e}")
