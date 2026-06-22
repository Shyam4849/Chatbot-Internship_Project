import sys
import os
import unittest

# Ensure the HUKUM-Chatbot directory is in Python's path so we can import chatbot module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chatbot.chatbot_engine import chat
from chatbot import memory_manager

class TestConversationalMemory(unittest.TestCase):

    def setUp(self):
        # Clear context memory for test sessions before running each test
        memory_manager.clear_context("session_1")
        memory_manager.clear_context("session_2")

    def test_context_lifecycle(self):
        # Test basic lifecycle: get, update, clear
        session_id = "test_lifecycle"
        memory_manager.clear_context(session_id)
        
        context = memory_manager.get_context(session_id)
        self.assertIsNone(context["selected_worker"])
        self.assertEqual(len(context["recommended_workers"]), 0)

        # Update
        dummy_worker = {"w_id": 1, "w_name": "Test Worker", "w_rating": 4.5}
        memory_manager.update_context(session_id, {
            "selected_worker": dummy_worker,
            "recommended_workers": [dummy_worker]
        })
        
        context = memory_manager.get_context(session_id)
        self.assertEqual(context["selected_worker"]["w_name"], "Test Worker")
        
        # Clear
        memory_manager.clear_context(session_id)
        context = memory_manager.get_context(session_id)
        self.assertIsNone(context["selected_worker"])

    def test_worker_discovery_and_follow_ups(self):
        # 1. Ask for a painter
        res = chat("Find a local painter", session_id="session_1")
        self.assertEqual(res["intent"], "matchmaking")
        self.assertTrue(res["is_html"])

        # Check that context is saved
        ctx = memory_manager.get_context("session_1")
        self.assertTrue(len(ctx["recommended_workers"]) > 0)
        self.assertIsNotNone(ctx["selected_worker"])
        first_worker = ctx["selected_worker"]
        first_worker_name = first_worker["w_name"]

        # 2. Ask rating follow-up
        res_rating = chat("What is his rating?", session_id="session_1")
        self.assertEqual(res_rating["intent"], "matchmaking")
        self.assertTrue(res_rating["is_html"])
        self.assertIn(str(first_worker["w_rating"]), res_rating["response"])
        self.assertIn(first_worker_name, res_rating["response"])

        # 3. Ask verification status follow-up
        res_ver = chat("Is he verified?", session_id="session_1")
        self.assertEqual(res_ver["intent"], "matchmaking")
        self.assertTrue(res_ver["is_html"])
        expected_status = "✓ Verified" if first_worker["w_is_verified"] == 1 else "⚠️ Unverified"
        self.assertIn(expected_status, res_ver["response"])

        # 4. Ask location follow-up
        res_loc = chat("What is his location?", session_id="session_1")
        self.assertEqual(res_loc["intent"], "matchmaking")
        self.assertTrue(res_loc["is_html"])
        self.assertIn(first_worker["w_location"], res_loc["response"])

        # 5. Ask detail follow-ups (natural phrases)
        detail_phrases = [
            "Tell me more about him",
            "Show details",
            "Give more information",
            "More details",
            "Tell me about this worker"
        ]
        for phrase in detail_phrases:
            res_det = chat(phrase, session_id="session_1")
            self.assertEqual(res_det["intent"], "matchmaking")
            self.assertTrue(res_det["is_html"])
            self.assertIn("Full Worker Details", res_det["response"])
            self.assertIn(first_worker_name, res_det["response"])

        # 6. Cycle to another worker
        res_another = chat("Show another worker.", session_id="session_1")
        self.assertEqual(res_another["intent"], "matchmaking")
        self.assertTrue(res_another["is_html"])
        
        ctx_new = memory_manager.get_context("session_1")
        new_selected = ctx_new["selected_worker"]
        self.assertNotEqual(new_selected["w_id"], first_worker["w_id"])

        # 7. Ask "Tell me more about the first one"
        res_first_one = chat("Tell me more about the first one", session_id="session_1")
        self.assertEqual(res_first_one["intent"], "matchmaking")
        self.assertTrue(res_first_one["is_html"])
        ctx_reset = memory_manager.get_context("session_1")
        self.assertEqual(ctx_reset["selected_worker"]["w_id"], first_worker["w_id"])

    def test_session_isolation(self):
        # session_1 has a painter search
        chat("Find a local painter", session_id="session_1")
        
        # session_2 is new and has no queries
        res_2 = chat("What is his rating?", session_id="session_2")
        self.assertEqual(res_2["intent"], "matchmaking")
        self.assertFalse(res_2["is_html"])
        self.assertEqual(
            res_2["response"],
            "I don't have enough context from our previous conversation. Please tell me which worker you are referring to."
        )

    def test_missing_context_fallback(self):
        # Query follow-up immediately in a fresh session
        res = chat("What is his rating?", session_id="session_fresh")
        self.assertEqual(res["intent"], "matchmaking")
        self.assertFalse(res["is_html"])
        self.assertEqual(
            res["response"],
            "I don't have enough context from our previous conversation. Please tell me which worker you are referring to."
        )


if __name__ == "__main__":
    unittest.main()
