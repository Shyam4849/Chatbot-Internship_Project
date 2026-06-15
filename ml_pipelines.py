"""
HUKUM Chatbot - ML Pipelines (Legacy Module).

This module maintains backward compatibility with existing code.
All functionality has been refactored into the 'chatbot' module.
New code should import directly from 'chatbot' module.

Legacy Support:
- predict_matchmaking()
- predict_pricing()
- predict_trust_shield()
"""

# Import from new modular architecture for backward compatibility
from chatbot.response_generator import (
    generate_matchmaking_response as predict_matchmaking,
    generate_pricing_response as predict_pricing,
    generate_trust_response as predict_trust_shield,
)
from chatbot.models import load_models

__all__ = [
    "predict_matchmaking",
    "predict_pricing",
    "predict_trust_shield",
    "load_models",
]

# Ensure models are loaded at import time (legacy behavior)
load_models()
