"""
Verification test for the improved intent detection logic.

Tests that:
- Risk/trust queries with "worker" classify as TRUST (not MATCHMAKING)
- Pure matchmaking queries still classify as MATCHMAKING
- Pricing queries still classify as PRICING
- Help and general fallback still work
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chatbot.intent_detector import detect_intent

# ===== TRUST queries (must NOT be classified as MATCHMAKING) =====
trust_queries = [
    ("give me the worker with high risk score", "trust"),
    ("show risky workers", "trust"),
    ("fraud report for worker", "trust"),
    ("is this worker suspicious", "trust"),
    ("worker fraud history", "trust"),
    ("report status of worker", "trust"),
    ("Check risk status for Rajesh Kumar", "trust"),
]

# ===== MATCHMAKING queries =====
matchmaking_queries = [
    ("find a painter", "matchmaking"),
    ("need an electrician", "matchmaking"),
    ("show carpenters nearby", "matchmaking"),
    ("Find a local painter", "matchmaking"),
    ("find a verified worker", "matchmaking"),
]

# ===== PRICING queries =====
pricing_queries = [
    ("price for 500 bags of cement", "pricing"),
    ("cement cost", "pricing"),
    ("steel estimate", "pricing"),
    ("Calculate price for 500 bags of cement", "pricing"),
    ("how much does brick cost", "pricing"),
]

# ===== HELP and GENERAL queries =====
other_queries = [
    ("How do I post a job on the app?", "help"),
    ("hello", "general"),
    ("what is hukum", "general"),
]

all_tests = trust_queries + matchmaking_queries + pricing_queries + other_queries

print("=" * 70)
print("  INTENT DETECTION VERIFICATION")
print("=" * 70)

passed = 0
failed = 0

for query, expected in all_tests:
    actual = detect_intent(query)
    status = "PASS" if actual == expected else "FAIL"
    if status == "PASS":
        passed += 1
    else:
        failed += 1
    symbol = "OK" if status == "PASS" else "XX"
    print(f"  [{symbol}] [{status}] \"{query}\"")
    if status == "FAIL":
        print(f"           Expected: {expected}, Got: {actual}")

print("=" * 70)
print(f"  Results: {passed} passed, {failed} failed out of {len(all_tests)}")
print("=" * 70)

if failed > 0:
    sys.exit(1)
