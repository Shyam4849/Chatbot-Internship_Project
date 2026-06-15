"""
HUKUM Chatbot - Response Generation Module.

Generates formatted responses for each intent type.
Handles HTML generation for rich responses.
Completely independent of Streamlit or UI frameworks.
"""

import logging
import re
from .config import LOGS_FILE
import pandas as pd

logging.basicConfig(
    filename=LOGS_FILE,
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
)
import numpy as np
from . import data_access, models
from .config import (
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    MATCHMAKING_DEFAULT_PROFESSION,
    MATCHMAKING_DEFAULT_PAYMENT,
    MATCHMAKING_DISTANCE_KM_FACTOR,
    PRICING_DEFAULT_QUANTITY,
    PRICING_DISTANCE_LOGISTICS,
    PRICING_BRAND_MULTIPLIERS,
    TRUST_SHIELD_RISK_THRESHOLD,
    PROFESSIONS,
    BRANDS,
    RESPONSE_HELP,
    RESPONSE_GENERAL,
    RESPONSE_WORKER_NOT_FOUND,
)


def generate_matchmaking_response(query: str, session_id: str = "default") -> str:
    """
    Generate worker matchmaking response using the trained ML model.

    Reads worker data, scores them using the model, and returns top 3 matches as HTML.

    Args:
        query: User query containing profession/worker type

    Returns:
        str: HTML formatted response with top 3 matched workers
    """

    print("Matchmaking function executed")

    try:
        df_workers = data_access.get_workers_data()
        print("\n===== WORKER DF DEBUG =====")
        print(type(df_workers))
        print("Shape:", df_workers.shape)
        print("Columns:", list(df_workers.columns))
        print(df_workers.head())
        print("===========================\n")
    except Exception as e:
        return f"<div class='error-box'>Database Access Error: Could not parse worker sheet. ({e})</div>"

    # Extract profession from query
    query_lower = query.lower()
    selected_profession = MATCHMAKING_DEFAULT_PROFESSION

    for prof in PROFESSIONS:
        if prof in query_lower:
            selected_profession = prof.capitalize()
            break

    # Filter workers by profession and availability
    subset = df_workers[
        (df_workers["w_profession"] == selected_profession)
        & (df_workers["is_blocked"] == 0)
    ].copy()
    if subset.empty:
        subset = df_workers[df_workers["is_blocked"] == 0].copy()

    # Calculate distance and payment features
    subset["distance_delta"] = np.sqrt(
        (subset["w_latitude"] - DEFAULT_LATITUDE) ** 2
        + (subset["w_longitude"] - DEFAULT_LONGITUDE) ** 2
    )
    subset["payment_amount"] = MATCHMAKING_DEFAULT_PAYMENT

    # Score workers using model
    model_matchmaker = models.get_matchmaker_model()
    features_input = subset[
        ["payment_amount", "w_rating", "distance_delta", "w_is_verified"]
    ].fillna(0)
    probabilities = model_matchmaker.predict_proba(features_input)[:, 1]

    probabilities = model_matchmaker.predict_proba(features_input)[:, 1]

    # random shit
    print("\n===== MATCH DEBUG =====")
    print(probabilities[:10])
    print("MIN =", probabilities.min())
    print("MAX =", probabilities.max())
    print("=======================\n")

    # Store raw probabilities for debugging
    logging.debug(f"Raw match probabilities: {probabilities}")
    # Normalize scores to 0-1 range to avoid rounding all to 100%
    prob_min = probabilities.min()
    prob_max = probabilities.max()
    if prob_max > prob_min:
        norm_scores = (probabilities - prob_min) / (prob_max - prob_min)
    else:
        norm_scores = np.zeros_like(probabilities)
    subset["match_probability"] = norm_scores

    # Get top 3 matches
    top_matches = subset.sort_values(by="match_probability", ascending=False).head(3)

    # Store context for follow-up detection
    from . import memory_manager

    recommended_workers = []
    for _, row in top_matches.iterrows():
        worker_dict = row.to_dict()
        for k, v in worker_dict.items():
            if hasattr(v, "item"):
                worker_dict[k] = v.item()
        recommended_workers.append(worker_dict)

    memory_manager.update_context(
        session_id,
        {
            "recommended_workers": recommended_workers,
            "selected_worker": recommended_workers[0] if recommended_workers else None,
        },
    )

    # Generate HTML response
    html_layout = f"""
    <div style='margin-bottom: 8px;'>
        <span style='background-color: #0d47a1; color: #ffffff; padding: 4px 8px; font-size: 11px; font-weight: bold; border-radius: 4px; text-transform: uppercase;'>
            🤖 Matchmaking Engine
        </span>
        <span style='margin-left: 6px; font-size: 13px; color: #455a64;'>Optimal Allocation for: <b>{selected_profession}</b></span>
    </div>
    """

    for _, row in top_matches.iterrows():
        verification_badge = (
            "<span style='color: #2e7d32; background-color: #e8f5e9; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;'>✓ Verified</span>"
            if row["w_is_verified"] == 1
            else "<span style='color: #c62828; background-color: #ffebee; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;'>⚠️ Unverified</span>"
        )
        dist_km = round(row["distance_delta"] * MATCHMAKING_DISTANCE_KM_FACTOR, 1)

        html_layout += f"""
        <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 14px; margin-bottom: 10px; background: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.02);'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;'>
                <span style='font-size: 16px; font-weight: bold; color: #1e88e5;'>👤 {row['w_name']}</span>
                <span style='font-weight: bold; font-size: 14px; color: #2e7d32; background: #e8f5e9; padding: 4px 8px; border-radius: 6px;'>
                    {round(row['match_probability']*100, 1)}% Score
                </span>
            </div>
            <div style='font-size: 13px; color: #546e7a; margin-bottom: 4px;'>
                <b>Profession:</b> {row['w_profession']} | <b>Rating:</b> {row['w_rating']} ⭐ | {verification_badge}
            </div>
            <div style='font-size: 12px; color: #78909c;'>
                📍 Hub Proximity: <b>{dist_km} km</b> from center hub profile ({row['w_location']})
            </div>
        </div>
        """

    return html_layout


def generate_pricing_response(query: str) -> str:
    """
    Generate material pricing response using the trained ML model.

    Extracts quantity, material type, and brand; uses model to predict price.

    Args:
        query: User query containing quantity and material type

    Returns:
        str: HTML formatted response with pricing estimate
    """
    query_lower = query.lower()

    # Extract quantity from query
    extracted_numbers = re.findall(r"\d+", query)
    quantity_input = (
        int(extracted_numbers[0]) if extracted_numbers else PRICING_DEFAULT_QUANTITY
    )

    # Detect brand
    detected_brand = "Standard Grade"
    for brand in BRANDS:
        if brand in query_lower:
            detected_brand = brand.upper()
            break

    # Get pricing features and model
    model_pricing = models.get_pricing_model()
    model_pricing_columns = models.get_pricing_columns()

    # Match material category
    target_column = None
    matched_item_label = "Material Load"

    for col in model_pricing_columns:
        if "mr_item_name_" in col:
            item_clean = col.replace("mr_item_name_", "").lower()
            if "cement" in query_lower and "cement" in item_clean:
                target_column = col
                matched_item_label = "Cement Bags"
                break
            elif "steel" in query_lower and "steel" in item_clean:
                target_column = col
                matched_item_label = "Steel Rods / Structural"
                break
            elif "brick" in query_lower and "brick" in item_clean:
                target_column = col
                matched_item_label = "Clay Bricks"
                break

    # Build feature vector for model
    input_row = {col: [0] for col in model_pricing_columns}
    input_row["mr_quantity"] = [quantity_input]
    input_row["distance_logistics"] = [PRICING_DISTANCE_LOGISTICS]

    if target_column and target_column in input_row:
        input_row[target_column] = [1]

    # Detect urgency
    is_urgent = "Standard Timeline"
    if any(
        k in query_lower for k in ["urgent", "now", "immediate", "fast", "emergency"]
    ):
        is_urgent = "High Urgency Priority"
        if "mr_urgency_High" in input_row:
            input_row["mr_urgency_High"] = [1]

    # Predict price
    import pandas as pd

    df_inference = pd.DataFrame(input_row)[model_pricing_columns]
    predicted_base = model_pricing.predict(df_inference)[0]

    # Apply brand multiplier
    brand_multiplier = PRICING_BRAND_MULTIPLIERS.get(detected_brand, 1.0)
    final_predicted_val = predicted_base * brand_multiplier

    # Generate HTML response
    html_layout = f"""
    <div style='margin-bottom: 8px;'>
        <span style='background-color: #0288d1; color: #ffffff; padding: 4px 8px; font-size: 11px; font-weight: bold; border-radius: 4px; text-transform: uppercase;'>
            📈 Dynamic Pricing Regressor
        </span>
    </div>
    <div style='border-left: 4px solid #0288d1; padding: 14px; background-color: #f1f8ff; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.01);'>
        <div style='font-size: 15px; font-weight: bold; color: #01579b; margin-bottom: 8px;'>
            Calculated Valuation: ₹{int(final_predicted_val):,} INR
        </div>
        <table style='width: 100%; font-size: 12px; color: #455a64; border-collapse: collapse;'>
            <tr><td style='padding: 3px 0;'>📦 <b>Material Category:</b></td><td style='text-align: right;'>{matched_item_label}</td></tr>
            <tr><td style='padding: 3px 0;'>🔢 <b>Extracted Quantity:</b></td><td style='text-align: right;'>{quantity_input} units</td></tr>
            <tr><td style='padding: 3px 0;'>🏷️ <b>Detected Premium Brand:</b></td><td style='text-align: right; color: #0288d1; font-weight: bold;'>{detected_brand}</td></tr>
            <tr><td style='padding: 3px 0;'>⚡ <b>Logistics Priority:</b></td><td style='text-align: right;'>{is_urgent}</td></tr>
            <tr style='border-top: 1px solid #d0d7de;'><td style='padding: 6px 0 0 0;'>⚖️ <b>Spread (95%-105%):</b></td><td style='text-align: right; padding: 6px 0 0 0; font-weight: bold;'>₹{int(final_predicted_val*0.95):,} - ₹{int(final_predicted_val*1.05):,}</td></tr>
        </table>
    </div>
    """

    return html_layout


def generate_trust_response(query: str) -> str:
    """
    Generate trust/risk assessment response using the trained ML model.

    Matches worker by name, retrieves their profile, and assesses risk using model.

    Args:
        query: User query containing worker name to check

    Returns:
        str: HTML formatted response with risk assessment
    """

    try:
        df_workers = data_access.get_workers_data()
    except Exception as e:
        return f"<div class='error-box'>Database Access Error: Could not parse profiling metrics. ({e})</div>"

    query_lower = query.lower()
    matched_row = None

    query_lower = query.lower()

    # -------------------------------
    # CASE 1: RISK / TRUST FILTER QUERY
    # -------------------------------
    risk_keywords = ["risk", "fraud", "suspicious", "high risk", "low risk"]

    if any(k in query_lower for k in risk_keywords):
        return generate_risk_filtered_response(df_workers, query_lower)

    # -------------------------------
    # CASE 2: NAME BASED LOOKUP ONLY
    # -------------------------------
    matched_row = None

    for _, row in df_workers.iterrows():
        if row["w_name"].lower() in query_lower:
            matched_row = row
            break

    # Worker not found
    if matched_row is None:
        return RESPONSE_WORKER_NOT_FOUND

    target_name = matched_row["w_name"]
    rating = matched_row["w_rating"]
    verified = matched_row["w_is_verified"]

    # Count disputes from reports
    try:
        df_rep = data_access.get_worker_reports_data()
        disputes = int(
            df_rep[
                (df_rep["reported_user_id"] == matched_row["w_id"])
                & (df_rep["reported_user_type"] == "Worker")
            ].shape[0]
        )
    except Exception:
        disputes = 0

    # Score using model
    import pandas as pd

    model_trust_shield = models.get_trust_shield_model()
    input_df = pd.DataFrame(
        [{"w_rating": rating, "disputes_logged": disputes, "w_is_verified": verified}]
    )
    is_blocked_pred = model_trust_shield.predict(input_df)[0]
    risk_probability = model_trust_shield.predict_proba(input_df)[0][1]

    # Determine risk level and styling
    is_flagged = is_blocked_pred == 1 or risk_probability > TRUST_SHIELD_RISK_THRESHOLD
    box_border = "#d32f2f" if is_flagged else "#388e3c"
    box_bg = "#ffebee" if is_flagged else "#e8f5e9"
    badge_color = "#c62828" if is_flagged else "#2e7d32"
    badge_text = "CRITICAL RISK / LOCKED" if is_flagged else "PASSED SECURITY CLEARANCE"

    # Generate HTML response
    html_layout = f"""
    <div style='margin-bottom: 8px;'>
        <span style='background-color: #37474f; color: #ffffff; padding: 4px 8px; font-size: 11px; font-weight: bold; border-radius: 4px; text-transform: uppercase;'>
            🛡️ The Trust Shield Classifier
        </span>
    </div>
    <div style='border: 1px solid {box_border}; padding: 14px; background-color: {box_bg}; border-radius: 8px;'>
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
            <b style='font-size: 15px; color: {badge_color};'>🛡️ Profile Audit: {target_name}</b>
            <span style='font-size: 11px; font-weight: bold; color: #ffffff; background-color: {badge_color}; padding: 3px 6px; border-radius: 4px;'>
                {badge_text}
            </span>
        </div>
        <ul style='margin: 0; padding-left: 20px; font-size: 13px; color: #263238; line-height: 1.6;'>
            <li><b>Performance Index:</b> {rating} ⭐</li>
            <li><b>Historical Dispute Incidents:</b> {disputes} flags tracked in sheet</li>
            <li><b>System Status:</b> {"Verified Identity Vector" if verified == 1 else "Unverified Profiling Trace"}</li>
            <li><b>Algorithmic Risk Score:</b> <span style='font-weight:bold; color:{badge_color};'>{round(risk_probability*100, 1)}%</span></li>
        </ul>
        <div style='margin-top: 8px; font-size: 11px; font-style: italic; color: #546e7a; border-top: 1px solid {box_border}40; padding-top: 6px;'>
            {"Verdict: Contractor allocation restricted. Entries appended to administrative enforcement tables." if is_flagged else "Verdict: System status green. Profile cleared for workflow bidding."}
        </div>
    </div>
    """

    return html_layout


def generate_help_response() -> str:
    """
    Generate static help/instruction response.

    Returns:
        str: Markdown formatted help text
    """
    return RESPONSE_HELP


def generate_general_response() -> str:
    """
    Generate static general/welcome response.

    Returns:
        str: Markdown formatted welcome text
    """
    return RESPONSE_GENERAL


def generate_risk_filtered_response(df_workers, query_lower):

    model = models.get_trust_shield_model()

    input_df = pd.DataFrame(
        {
            "w_rating": df_workers["w_rating"],
            "disputes_logged": 0,
            "w_is_verified": df_workers["w_is_verified"],
        }
    )

    risk_probs = model.predict_proba(input_df)[:, 1]

    df_workers = df_workers.copy()
    df_workers["risk_score"] = risk_probs

    # -------------------------
    # PROPER FILTER LOGIC
    # -------------------------
    if "low risk" in query_lower:
        filtered = df_workers[df_workers["risk_score"] <= TRUST_SHIELD_RISK_THRESHOLD]

    elif "high risk" in query_lower:
        filtered = df_workers[df_workers["risk_score"] > TRUST_SHIELD_RISK_THRESHOLD]

    else:
        filtered = df_workers.sort_values(by="risk_score", ascending=False)

    # -------------------------
    # HTML OUTPUT
    # -------------------------
    html = """
    <div style="
        background: #111827;
        padding: 12px;
        border-radius: 10px;
        color: #ffffff;
        font-family: Arial;
        margin-bottom: 10px;
        border: 1px solid #2d3748;
    ">
        <h3 style="margin: 0; color: #60a5fa;">⚠️ Risk Analysis Results</h3>
        <p style="margin: 4px 0 0; font-size: 12px; color: #cbd5e1;">
            AI-powered worker risk profiling dashboard
        </p>
    </div>
    """

    for _, row in filtered.head(10).iterrows():

        risk_pct = int(row["risk_score"] * 100)

        if risk_pct > 70:
            border = "#ef4444"
            badge = "HIGH RISK"
            bg = "#1f1f1f"
        elif risk_pct > 40:
            border = "#f59e0b"
            badge = "MEDIUM RISK"
            bg = "#1a1a1a"
        else:
            border = "#22c55e"
            badge = "LOW RISK"
            bg = "#0f172a"

        html += f"""
        <div style="
            background: {bg};
            border-left: 5px solid {border};
            padding: 12px;
            margin: 10px 0;
            border-radius: 8px;
            color: #e5e7eb;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        ">

            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="font-size: 15px; font-weight: bold;">
                    👤 {row['w_name']}
                </div>

                <div style="
                    background:{border};
                    color:white;
                    padding: 3px 8px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                ">
                    {badge}
                </div>
            </div>

            <div style="margin-top: 6px; font-size: 13px; color: #cbd5e1;">
                ⭐ Rating: {row['w_rating']} &nbsp; | &nbsp;
                ⚠️ Risk Score: {risk_pct}%
            </div>

        </div>
        """

    return html


def format_response(intent: str, query: str, session_id: str = "default") -> dict:
    """
    Main entry point for response generation.

    Routes to appropriate response generator based on intent.

    Args:
        intent: One of ["pricing", "matchmaking", "trust", "help", "general"]
        query: Original user query
        session_id: The session ID for conversational memory

    Returns:
        dict: {
            "intent": str,
            "response": str (HTML or Markdown),
            "is_html": bool,
        }
    """
    is_html = False
    response = ""

    if intent == "pricing":
        response = generate_pricing_response(query)
        is_html = True
    elif intent == "matchmaking":
        response = generate_matchmaking_response(query, session_id)
        is_html = True
    elif intent == "trust":
        response = generate_trust_response(query)
        is_html = True
    elif intent == "help":
        response = generate_help_response()
        is_html = False
    else:  # general
        response = generate_general_response()
        is_html = False

    return {
        "intent": intent,
        "response": response,
        "is_html": is_html,
    }
