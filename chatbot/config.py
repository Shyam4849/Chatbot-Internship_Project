"""
HUKUM Chatbot - Configuration and Constants.

All hardcoded values, paths, keywords, and static responses are defined here.
"""

import os
import os
from pathlib import Path

# =====================================================================
# FILE PATHS AND DIRECTORIES
# =====================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "saved_models"
DATA_DIR = BASE_DIR / "dataset"
LOGS_FILE = BASE_DIR / "chatbot_logs.txt"

# Excel Dataset Path
MASTER_EXCEL_PATH = DATA_DIR / "Hukum_Builders_Master_Dataset_v2.xlsx"

# Model File Paths
PATH_MODEL_MATCHMAKING = MODEL_DIR / "hukum_matchmaker_engine.pkl"
PATH_MODEL_PRICING = MODEL_DIR / "hukum_pricing_regressor.pkl"
PATH_MODEL_TRUST_SHIELD = MODEL_DIR / "hukum_trust_shield_classifier.pkl"
PATH_PRICING_COLUMNS = MODEL_DIR / "hukum_pricing_features.pkl"

import logging
# Configure standard logger
logging.basicConfig(
    filename=str(LOGS_FILE),
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s'
)
logger = logging.getLogger("hukum_chatbot")

# =====================================================================
# GEOGRAPHIC DEFAULTS
# =====================================================================

# Fallback Anchor Coordinates (Jamshedpur City Bounds Center)
DEFAULT_LATITUDE = 22.8046
DEFAULT_LONGITUDE = 86.2029

# =====================================================================
# INTENT DETECTION KEYWORDS
# =====================================================================

INTENT_KEYWORDS = {
    "pricing": [
        "price",
        "cost",
        "budget",
        "estimate",
        "rate",
        "how much",
        "cement",
        "steel",
        "brick",
        "bags",
        "material",
    ],
    "matchmaking": [
        "find",
        "worker",
        "builder",
        "mason",
        "electrician",
        "plumber",
        "painter",
        "carpenter",
    ],
    "trust": [
        "risk",
        "risk status",
        "trust",
        "fraud",
        "block",
        "scam",
        "report",
        "fake",
        "suspicious",
        "verification",
    ],
}

# =====================================================================
# MATERIAL AND PROFESSION LISTS
# =====================================================================

PROFESSIONS = ["painter", "plumber", "electrician", "carpenter", "mason"]
MATERIALS = ["cement", "steel", "brick", "sand", "aggregate"]
BRANDS = ["acc", "ambuja", "ultratech", "dalmia", "jk लक्ष्मी", "lafarge"]

# =====================================================================
# STATIC RESPONSE TEXTS
# =====================================================================

RESPONSE_HELP = """
### To post a job on Hukum Builders:

1. Log into your **Customer Dashboard**
2. Click **Post New Project**
3. Select worker/material requirements
4. Submit

The platform will automatically process:
- Worker Matching
- Pricing Estimation
- Verification Checks
"""

RESPONSE_GENERAL = """
### 🤖 Hukum Builders AI Assistant

I can help with:

#### 🔍 Worker Discovery
- Find electricians
- Find plumbers
- Find painters

#### 💰 Pricing Estimation
- Cement pricing
- Steel pricing
- Brick pricing

#### 🛡️ Trust Shield
- Worker verification
- Risk assessment

#### Example Queries

- Find a verified electrician
- Estimate cost for 500 bags of cement
- Check risk status for Rajesh Kumar
"""

RESPONSE_WORKER_NOT_FOUND = """
<div style='border: 1px dashed #b0bec5; padding: 14px; background-color: #f5f7f8; color: #37474f; border-radius: 6px; font-family: sans-serif;'>
    🔍 <b>Trust Shield Security Registry:</b><br>
    <span style='color: #c62828; font-weight: bold;'>⚠️ Worker Profile Not Found</span><br>
    The specified name does not match any registered entities within our active database sheets. Please check the spelling or verify registration credentials.
</div>
"""

# =====================================================================
# MODEL INFERENCE PARAMETERS
# =====================================================================

MATCHMAKING_DEFAULT_PROFESSION = "Mason"
MATCHMAKING_DEFAULT_PAYMENT = 5000
MATCHMAKING_DISTANCE_KM_FACTOR = 111.1

PRICING_DEFAULT_QUANTITY = 100
PRICING_DISTANCE_LOGISTICS = 0.045
PRICING_BRAND_MULTIPLIERS = {
    "ACC": 1.08,
    "ULTRATECH": 1.08,
    "AMBUJA": 1.04,
}

TRUST_SHIELD_RISK_THRESHOLD = 0.45

# =====================================================================
# UI CONSTANTS
# =====================================================================

STREAMLIT_TITLE = "🏗️ Hukum Builders Intelligent System Terminal"
STREAMLIT_CAPTION = (
    "Interface integrated directly with Master Excel Workbook ML Pipelines"
)
STREAMLIT_PAGE_ICON = "🏗️"
