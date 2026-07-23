"""
HUKUM Chatbot - Conversational Context Memory Manager.

Manages session-based context memory, detects follow-up questions,
and handles context retrieval for workers.
"""

# Global in-memory storage for session contexts
_session_storage = {}

def get_context(session_id: str) -> dict:
    """
    Retrieve the conversational context for a given session ID.
    If the session does not exist, initialize a new context dict.
    """
    if session_id not in _session_storage:
        _session_storage[session_id] = {
            "last_intent": None,
            "last_query": None,
            "last_response": None,
            "recommended_workers": [],
            "selected_worker": None,
            "recommended_jobs": [],
            "selected_job": None,
        }
    return _session_storage[session_id]

def save_context(session_id: str, context_data: dict) -> None:
    """Save the complete conversational context for a session ID."""
    _session_storage[session_id] = context_data

def clear_context(session_id: str) -> None:
    """Clear the conversational context for a session ID."""
    _session_storage[session_id] = {
        "last_intent": None,
        "last_query": None,
        "last_response": None,
        "recommended_workers": [],
        "selected_worker": None,
        "recommended_jobs": [],
        "selected_job": None,
    }

def update_context(session_id: str, updates: dict) -> None:
    """Update specific keys in the conversational context for a session ID."""
    context = get_context(session_id)
    context.update(updates)


def detect_follow_up_type(query: str) -> str:
    """
    Lightweight rule-based detection for worker follow-up queries.
    Uses exact/close string matching to avoid false positives.
    """
    query_clean = query.lower().replace("?", "").replace(".", "").replace("!", "").replace(",", "").strip()

    worker_rating_phrases = {
        "what is his rating", "what is rating", "his rating", 
        "what is the rating", "rating of the worker", 
        "worker rating", "worker's rating", "his rating status"
    }
    worker_verified_phrases = {
        "is he verified", "he verified", "is worker verified", 
        "verification status", "is he verified status"
    }
    worker_location_phrases = {
        "what is his location", "his location", "where is he", 
        "where is he located", "worker's location"
    }
    worker_another_phrases = {
        "show another worker", "next worker", "another worker", 
        "other worker", "show me another worker"
    }
    worker_first_phrases = {
        "tell me more about the first one", "tell me more about the first",
        "more about first", "first worker details", "details of first"
    }
    worker_details_phrases = {
        "tell me more about him", "show details", "give more information",
        "more details", "tell me about this worker", "explain more", 
        "give details", "tell me more"
    }

    if query_clean in worker_rating_phrases:
        return "worker_rating"
    if query_clean in worker_verified_phrases:
        return "worker_verified"
    if query_clean in worker_location_phrases:
        return "worker_location"
    if query_clean in worker_another_phrases:
        return "worker_another"
    if query_clean in worker_first_phrases:
        return "worker_first"
    if query_clean in worker_details_phrases:
        return "worker_details"

    return None


def process_follow_up(query: str, session_id: str) -> dict:
    """
    Process a follow-up query using the session's context memory.
    
    Returns:
        dict: response_data mapping the chatbot format
    """
    context = get_context(session_id)
    follow_up_type = detect_follow_up_type(query)

    graceful_fallback = {
        "intent": "matchmaking",
        "response": "I don't have enough context from our previous conversation. Please tell me which worker you are referring to.",
        "is_html": False
    }

    if not follow_up_type:
        return graceful_fallback

    # Helper: Format verification badge
    def get_verification_badge(verified):
        if verified == 1:
            return "<span style='color: #2e7d32; background-color: #e8f5e9; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;'>✓ Verified</span>"
        else:
            return "<span style='color: #c62828; background-color: #ffebee; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;'>⚠️ Unverified</span>"

    # Helper: Calculate distance in km
    def get_distance_km(worker):
        # Default conversion factor
        factor = 111.1
        if "distance_delta" in worker:
            return round(worker["distance_delta"] * factor, 1)
        elif "distance_km" in worker:
            return worker["distance_km"]
        return 0.0


    # WORKER ANOTHER
    # -------------------------------------------------------------------------
    if follow_up_type == "worker_another":
        workers = context.get("recommended_workers", [])
        selected_worker = context.get("selected_worker")
        if not workers or not selected_worker:
            return graceful_fallback

        # Find current index
        idx = -1
        for i, w in enumerate(workers):
            if w.get("w_id") == selected_worker.get("w_id"):
                idx = i
                break
        
        # Cycle to the next worker
        next_idx = (idx + 1) % len(workers)
        worker = workers[next_idx]
        context["selected_worker"] = worker
        save_context(session_id, context)

        w_name = worker.get("w_name", "N/A")
        w_profession = worker.get("w_profession", "N/A")
        w_rating = worker.get("w_rating", 0.0)
        verified = worker.get("w_is_verified", 0)
        w_location = worker.get("w_location", "N/A")
        dist_km = get_distance_km(worker)
        badge = get_verification_badge(verified)

        response = f"""
        <div style='border: 1px solid #1e88e5; border-radius: 8px; padding: 14px; margin-bottom: 10px; background: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.02); font-family: sans-serif;'>
            <div style='font-size: 11px; text-transform: uppercase; color: #1e88e5; font-weight: bold; margin-bottom: 4px;'>Selected Next Recommended Worker</div>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;'>
                <span style='font-size: 16px; font-weight: bold; color: #1e88e5;'>👤 {w_name}</span>
            </div>
            <div style='font-size: 13px; color: #546e7a; margin-bottom: 4px;'>
                <b>Profession:</b> {w_profession} | <b>Rating:</b> {w_rating} ⭐ | {badge}
            </div>
            <div style='font-size: 12px; color: #78909c;'>
                📍 Hub Proximity: <b>{dist_km} km</b> from center hub profile ({w_location})
            </div>
        </div>
        """
        return {"intent": "matchmaking", "response": response, "is_html": True}


    # -------------------------------------------------------------------------
    if follow_up_type == "worker_first":
        workers = context.get("recommended_workers", [])
        if not workers:
            return graceful_fallback

        worker = workers[0]
        context["selected_worker"] = worker
        save_context(session_id, context)

        w_name = worker.get("w_name", "N/A")
        w_profession = worker.get("w_profession", "N/A")
        w_rating = worker.get("w_rating", 0.0)
        verified = worker.get("w_is_verified", 0)
        w_location = worker.get("w_location", "N/A")
        dist_km = get_distance_km(worker)
        badge = get_verification_badge(verified)

        response = f"""
        <div style='border: 1px solid #1e88e5; border-radius: 8px; padding: 14px; margin-bottom: 10px; background: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.02); font-family: sans-serif;'>
            <div style='font-size: 11px; text-transform: uppercase; color: #1e88e5; font-weight: bold; margin-bottom: 4px;'>Selected First Recommended Worker</div>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;'>
                <span style='font-size: 16px; font-weight: bold; color: #1e88e5;'>👤 {w_name}</span>
            </div>
            <div style='font-size: 13px; color: #546e7a; margin-bottom: 4px;'>
                <b>Profession:</b> {w_profession} | <b>Rating:</b> {w_rating} ⭐ | {badge}
            </div>
            <div style='font-size: 12px; color: #78909c;'>
                📍 Hub Proximity: <b>{dist_km} km</b> from center hub profile ({w_location})
            </div>
        </div>
        """
        return {"intent": "matchmaking", "response": response, "is_html": True}

    # -------------------------------------------------------------------------
    # WORKER RATING, VERIFICATION, LOCATION, DETAILS
    # -------------------------------------------------------------------------
    worker = context.get("selected_worker")
    if not worker:
        return graceful_fallback

    w_name = worker.get("w_name", "N/A")

    if follow_up_type == "worker_rating":
        w_rating = worker.get("w_rating", 0.0)
        response = f"""
        <div style='border-left: 4px solid #1e88e5; padding: 10px 14px; background-color: #f1f8ff; border-radius: 4px; font-family: sans-serif;'>
            <span style='font-size: 14px; color: #37474f;'>Rating for worker <b>{w_name}</b>:</span><br>
            <span style='font-size: 18px; font-weight: bold; color: #2e7d32; margin-top: 4px; display: inline-block;'>{w_rating} ⭐</span>
        </div>
        """
        return {"intent": "matchmaking", "response": response, "is_html": True}

    elif follow_up_type == "worker_verified":
        verified = worker.get("w_is_verified", 0)
        badge = get_verification_badge(verified)
        response = f"""
        <div style='border-left: 4px solid #1e88e5; padding: 10px 14px; background-color: #f1f8ff; border-radius: 4px; font-family: sans-serif;'>
            <span style='font-size: 14px; color: #37474f;'>Verification status for <b>{w_name}</b>:</span><br>
            <div style='margin-top: 6px;'>{badge}</div>
        </div>
        """
        return {"intent": "matchmaking", "response": response, "is_html": True}

    elif follow_up_type == "worker_location":
        w_location = worker.get("w_location", "N/A")
        dist_km = get_distance_km(worker)
        response = f"""
        <div style='border-left: 4px solid #1e88e5; padding: 10px 14px; background-color: #f1f8ff; border-radius: 4px; font-family: sans-serif;'>
            <span style='font-size: 14px; color: #37474f;'>Location for <b>{w_name}</b>:</span><br>
            <span style='font-size: 14px; font-weight: bold; color: #0d47a1; margin-top: 4px; display: inline-block;'>📍 {w_location}</span> (Proximity: {dist_km} km)
        </div>
        """
        return {"intent": "matchmaking", "response": response, "is_html": True}

    elif follow_up_type == "worker_details":
        w_profession = worker.get("w_profession", "N/A")
        w_rating = worker.get("w_rating", 0.0)
        verified = worker.get("w_is_verified", 0)
        w_location = worker.get("w_location", "N/A")
        dist_km = get_distance_km(worker)
        badge = get_verification_badge(verified)

        response = f"""
        <div style='border: 1px solid #1e88e5; border-radius: 8px; padding: 14px; background: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.02); font-family: sans-serif;'>
            <div style='font-size: 11px; text-transform: uppercase; color: #1e88e5; font-weight: bold; margin-bottom: 4px;'>Full Worker Details</div>
            <div style='font-size: 16px; font-weight: bold; color: #1e88e5; margin-bottom: 8px;'>👤 {w_name}</div>
            <table style='width: 100%; font-size: 13px; color: #37474f; border-collapse: collapse;'>
                <tr style='border-bottom: 1px solid #e0e0e0;'><td style='padding: 6px 0;'><b>Profession:</b></td><td>{w_profession}</td></tr>
                <tr style='border-bottom: 1px solid #e0e0e0;'><td style='padding: 6px 0;'><b>Rating:</b></td><td>{w_rating} ⭐</td></tr>
                <tr style='border-bottom: 1px solid #e0e0e0;'><td style='padding: 6px 0;'><b>Verification:</b></td><td>{badge}</td></tr>
                <tr style='border-bottom: 1px solid #e0e0e0;'><td style='padding: 6px 0;'><b>Location:</b></td><td>📍 {w_location}</td></tr>
                <tr><td style='padding: 6px 0;'><b>Hub Proximity:</b></td><td>{dist_km} km</td></tr>
            </table>
        </div>
        """
        return {"intent": "matchmaking", "response": response, "is_html": True}

    return graceful_fallback
