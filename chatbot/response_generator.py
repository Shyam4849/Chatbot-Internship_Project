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

    df_workers = data_access.get_workers_data()

    if df_workers.empty:
        return (
            "<div style='border: 1px dashed #b0bec5; padding: 14px; background-color: #f5f7f8;"
            "color: #37474f; border-radius: 6px;'>"
            "🔍 <b>Database Access Error:</b> Worker data is unavailable or the data sheet is empty."
            "</div>"
        )

    # Extract profession from query
    query_lower = query.lower()
    selected_profession = MATCHMAKING_DEFAULT_PROFESSION

    for prof in PROFESSIONS:
        if prof in query_lower:
            selected_profession = prof.capitalize()
            break

    # Filter workers by profession and availability (case-insensitive)
    subset = df_workers[
        (df_workers["w_profession"].str.lower() == selected_profession.lower())
        & (df_workers["is_blocked"] == 0)
    ].copy()
    if subset.empty:
        subset = df_workers[df_workers["is_blocked"] == 0].copy()

    if subset.empty:
        return (
            "<div style='border: 1px dashed #b0bec5; padding: 14px; background-color: #f5f7f8;"
            "color: #37474f; border-radius: 6px;'>"
            "🔍 <b>No workers available.</b><br>"
            "All registered workers are currently blocked or the worker database is empty."
            "</div>"
        )

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

    # === MATCHMAKER INFERENCE DIAGNOSTICS ===
    # logging.error("===== MATCHMAKING INFERENCE DIAGNOSTICS =====")
    # logging.error(f"Matchmaker model id = {id(model_matchmaker)}")
    # logging.error(f"Subset shape (workers to score): {subset.shape}")
    # logging.error(f"features_input dtypes:\n{features_input.dtypes.to_string()}")
    # logging.error(f"features_input (all rows):\n{features_input.to_string()}")
    # logging.error(
    #     f"payment_amount unique values: {sorted(features_input['payment_amount'].unique().tolist())}"
    # )
    # logging.error(
    #     f"w_rating unique values: {sorted(features_input['w_rating'].unique().tolist())}"
    # )
    # logging.error(
    #     f"distance_delta unique values: {sorted(features_input['distance_delta'].unique().tolist())}"
    # )
    # logging.error(
    #     f"w_is_verified unique values: {sorted(features_input['w_is_verified'].unique().tolist())}"
    # )
    # logging.error("================================================")

    probabilities = model_matchmaker.predict_proba(features_input)[:, 1]

    # === RAW PROBABILITIES DIAGNOSTICS ===
    # logging.error("===== RAW PROBABILITIES =====")
    # logging.error(f"RAW PROBABILITIES = {probabilities.tolist()}")
    # logging.error(f"MIN = {probabilities.min()}")
    # logging.error(f"MAX = {probabilities.max()}")
    # logging.error(f"MEAN = {probabilities.mean()}")
    # logging.error(f"STD = {probabilities.std()}")
    # logging.error(f"UNIQUE VALUES = {np.unique(probabilities).tolist()}")
    # logging.error(f"ALL SAME? = {len(np.unique(probabilities)) == 1}")
    # logging.error("==============================")

    # logging.debug(f"Raw match probabilities: {probabilities}")

    # Normalize scores to 0-1 range to avoid rounding all to 100%
    subset["raw_probability"] = probabilities

    logging.error(f"Workers with prob=1.0 = {(subset['raw_probability'] == 1.0).sum()}")

    # Create a composite score using ML prediction + rating + verification

    subset["match_probability"] = (
        subset["raw_probability"] * 0.7
        + (subset["w_rating"] / 5.0) * 0.2
        + subset["w_is_verified"] * 0.1
    )

    # Normalizing the score to 0-1
    min_score = subset["match_probability"].min()
    max_score = subset["match_probability"].max()

    if max_score > min_score:
        subset["match_probability"] = (subset["match_probability"] - min_score) / (
            max_score - min_score
        )
    else:
        subset["match_probability"] = 1.0


    # Get top 3 matches
    top_matches = subset.sort_values(
        by=["raw_probability", "w_rating", "distance_delta", "w_is_verified"],
        ascending=[False, False, True, False],
    ).head(3)

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
    try:
        model_pricing = models.get_pricing_model()
        model_pricing_columns = models.get_pricing_columns()
    except Exception as e:
        return (
            f"<div style='border: 1px dashed #b0bec5; padding: 14px; "
            f"background-color: #f5f7f8; color: #37474f; border-radius: 6px;'>"
            f"⚠️ <b>Pricing Model Error:</b> Could not load pricing model. ({e})</div>"
        )

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
    try:
        df_inference = pd.DataFrame(input_row)[model_pricing_columns]
        predicted_base = model_pricing.predict(df_inference)[0]
    except Exception as e:
        return (
            f"<div style='border: 1px dashed #b0bec5; padding: 14px; "
            f"background-color: #f5f7f8; color: #37474f; border-radius: 6px;'>"
            f"⚠️ <b>Pricing Inference Error:</b> Model prediction failed. ({e})</div>"
        )

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


def _get_dispute_counts():
    """
    Load dispute (report) counts for all workers from the reports sheet.

    Returns:
        pd.Series: Indexed by w_id, values are integer dispute counts.
    """
    try:
        df_rep = data_access.get_worker_reports_data()
        counts = (
            df_rep[df_rep["reported_user_type"] == "Worker"]
            .groupby("reported_user_id")
            .size()
        )
        return counts
    except Exception:
        return pd.Series(dtype=int)


def calculate_worker_risk(worker_row, dispute_count=0, worker_name="?"):
    """
    Single source of truth for Trust Shield risk calculation.

    Accepts a worker row (Series or dict-like) and a dispute count,
    builds the correct 3-feature input vector, and returns the model's
    probability of being high-risk.

    Args:
        worker_row: Must contain keys 'w_rating' and 'w_is_verified'.
        dispute_count: Integer number of historical disputes.
        worker_name: Optional name for debug output.

    Returns:
        float: Risk probability between 0.0 and 1.0.
    """
    model = models.get_trust_shield_model()

    logging.debug(f"Trust Shield model type: {type(model)}, id: {id(model)}")
    logging.debug(f"Trust Shield features expected: {model.feature_names_in_}")

    rating = worker_row["w_rating"]
    verified = worker_row["w_is_verified"]

    input_df = pd.DataFrame(
        [
            {
                "w_rating": rating,
                "disputes_logged": dispute_count,
                "w_is_verified": verified,
            }
        ]
    ).fillna(0)

    risk_prob = model.predict_proba(input_df)[0][1]

    logging.debug(
        f"Trust Shield [{worker_name}]: rating={rating}, disputes={dispute_count}, "
        f"verified={verified}, risk={risk_prob:.6f} ({round(risk_prob*100, 1)}%)"
    )

    return risk_prob


def generate_trust_response(query: str) -> str:
    """
    Generate trust/risk assessment response using the trained ML model.

    Matches worker by name, retrieves their profile, and assesses risk using model.

    Args:
        query: User query containing worker name to check

    Returns:
        str: HTML formatted response with risk assessment
    """

    df_workers = data_access.get_workers_data()

    if df_workers.empty:
        return (
            "<div style='border: 1px dashed #b0bec5; padding: 14px; background-color: #f5f7f8;"
            "color: #37474f; border-radius: 6px;'>"
            "🔍 <b>Database Access Error:</b> Worker data is unavailable or the data sheet is empty."
            "</div>"
        )

    query_lower = query.lower()

    # ---------------------------------------------------------------
    # STEP 1: GENERIC RISK QUERIES (delegate to bulk filter)
    # ---------------------------------------------------------------
    risk_keywords = ["high risk", "low risk", "fraud", "suspicious"]
    if any(k in query_lower for k in risk_keywords):
        return generate_risk_filtered_response(df_workers, query_lower)

    # ---------------------------------------------------------------
    # STEP 2: MATCH WORKER BY NAME
    # ---------------------------------------------------------------
    matched_row = None
    for _, row in df_workers.iterrows():
        if row["w_name"].lower() in query_lower:
            matched_row = row
            break

    if matched_row is None:
        return RESPONSE_WORKER_NOT_FOUND

    target_name = matched_row["w_name"]
    rating = matched_row["w_rating"]
    verified = matched_row["w_is_verified"]
    worker_id = matched_row["w_id"]

    # ---------------------------------------------------------------
    # STEP 3: COUNT DISPUTES FROM REPORTS SHEET
    # ---------------------------------------------------------------
    try:
        df_rep = data_access.get_worker_reports_data()
        disputes = int(
            df_rep[
                (df_rep["reported_user_id"] == worker_id)
                & (df_rep["reported_user_type"] == "Worker")
            ].shape[0]
        )
    except Exception:
        disputes = 0

    # ---------------------------------------------------------------
    # STEP 4: CALCULATE RISK VIA SINGLE SOURCE OF TRUTH
    # ---------------------------------------------------------------
    risk_probability = calculate_worker_risk(
        matched_row, disputes, worker_name=target_name
    )
    is_blocked_pred = 1 if risk_probability > TRUST_SHIELD_RISK_THRESHOLD else 0

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

    # Use actual dispute counts instead of hardcoded 0
    dispute_counts = _get_dispute_counts()

    df_workers = df_workers.copy()
    df_workers["disputes_logged"] = (
        df_workers["w_id"].map(dispute_counts).fillna(0).astype(int)
    )

    input_df = pd.DataFrame(
        {
            "w_rating": df_workers["w_rating"],
            "disputes_logged": df_workers["disputes_logged"],
            "w_is_verified": df_workers["w_is_verified"],
        }
    ).fillna(0)

    risk_probs = model.predict_proba(input_df)[:, 1]

    df_workers["risk_score"] = risk_probs

    # Debug: log Amol Chandra's risk score for verification
    amol_mask = df_workers["w_name"].str.lower().str.contains("amol", na=False)
    if amol_mask.any():
        amol_row = df_workers[amol_mask].iloc[0]
        logging.debug(
            f"Dashboard Risk [Amol Chandra]: w_id={amol_row['w_id']}, "
            f"rating={amol_row['w_rating']}, disputes={amol_row['disputes_logged']}, "
            f"verified={amol_row['w_is_verified']}, "
            f"risk={amol_row['risk_score']:.6f} ({round(amol_row['risk_score']*100, 1)}%)"
        )

    # -------------------------
    # PROPER FILTER LOGIC
    # -------------------------
    if "low risk" in query_lower:
        filtered = df_workers[df_workers["risk_score"] <= TRUST_SHIELD_RISK_THRESHOLD]

    elif "high risk" in query_lower:
        filtered = df_workers[df_workers["risk_score"] > TRUST_SHIELD_RISK_THRESHOLD]

    else:
        filtered = df_workers.sort_values(by="risk_score", ascending=False)

    if filtered.empty:
        return (
            "<div style='background: #111827; padding: 12px; border-radius: 10px; "
            "color: #ffffff; font-family: Arial; margin-bottom: 10px; "
            "border: 1px solid #2d3748;'>"
            "<h3 style='margin: 0; color: #60a5fa;'>⚠️ Risk Analysis Results</h3>"
            "<p style='margin: 4px 0 0; font-size: 13px; color: #cbd5e1;'>"
            "No workers matched the requested risk filter.</p></div>"
        )

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
