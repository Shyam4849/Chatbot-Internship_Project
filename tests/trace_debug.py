import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chatbot.chatbot_engine import chat
from chatbot import memory_manager

print("1. Searching for painter")
chat("Find a local painter", "session_1")
ctx = memory_manager.get_context("session_1")
print("Recommended workers count:", len(ctx["recommended_workers"]))
print("Recommended workers list:", [(w.get("w_id"), w.get("w_name")) for w in ctx["recommended_workers"]])
print("Selected after search:", ctx["selected_worker"]["w_name"])

print("\n2. Showing another worker")
chat("Show another worker.", "session_1")
ctx = memory_manager.get_context("session_1")
print("Selected after another:", ctx["selected_worker"]["w_name"])
print("Recommended workers list after show another:", [(w.get("w_id"), w.get("w_name")) for w in ctx["recommended_workers"]])

print("\n3. Asking for first one details")
session_id = "session_1"
query = "Tell me more about the first one"

# Run the body of chat manually:
follow_up_type = memory_manager.detect_follow_up_type(query)
print("Detected follow-up type inside chat:", follow_up_type)

res = memory_manager.process_follow_up(query, session_id)
ctx = memory_manager.get_context("session_1")
print("Selected worker in memory after process_follow_up:", ctx["selected_worker"]["w_name"])
print("Recommended workers list after process_follow_up:", [(w.get("w_id"), w.get("w_name")) for w in ctx["recommended_workers"]])
