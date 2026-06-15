"""
HUKUM Chatbot - Model Management Layer.

Handles loading and caching of pre-trained ML models.
Provides lazy loading with fallback to training if models are missing.
"""

import joblib
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from .config import (
    PATH_MODEL_MATCHMAKING,
    PATH_MODEL_PRICING,
    PATH_MODEL_TRUST_SHIELD,
    PATH_PRICING_COLUMNS,
    MASTER_EXCEL_PATH,
)
from . import data_access

# =====================================================================
# GLOBAL MODEL OBJECTS (CACHED AT MODULE IMPORT)
# =====================================================================

_models = {}
_models_loaded = False


def _train_models():
    """
    Train all three ML models from the Excel workbook.

    Called only if pre-trained models are missing.
    """
    print(
        "\n[System Initialization]: Parsing Excel sheets to generate clean ML weights..."
    )

    # --- MODEL 1: MATCHMAKING RECRUITMENT ENGINE ---
    try:
        df_w = data_access.get_workers_data()
        df_j = data_access.read_sheet("job_post")
        df_a = data_access.read_sheet("apply_job")

        m1_df = df_a.merge(df_j, on="j_id").merge(df_w, on="w_id")
        m1_df["distance_delta"] = np.sqrt(
            (m1_df["w_latitude"] - m1_df["j_latitude"]) ** 2
            + (m1_df["w_longitude"] - m1_df["j_longitude"]) ** 2
        )
        m1_df["is_success"] = (m1_df["a_status"] == "Accepted").astype(int)

        features_m1 = ["payment_amount", "w_rating", "distance_delta", "w_is_verified"]
        X_m1 = m1_df[features_m1].fillna(0)
        y_m1 = m1_df["is_success"]

        m1_model = RandomForestClassifier(
            class_weight="balanced", random_state=42, n_estimators=50
        )
        m1_model.fit(X_m1, y_m1)
        joblib.dump(m1_model, PATH_MODEL_MATCHMAKING)
        print(" -> [Success]: Trained and exported Matchmaker Engine Model.")
    except Exception as e:
        print(f" -> [Failure]: Model 1 setup bypassed due to error: {e}")

    # --- MODEL 2: DYNAMIC MATERIAL PRICING REGRESSOR ---
    try:
        df_mr = data_access.get_material_requirements_data()
        df_ar = data_access.get_apply_requirements_data()

        m2_df = df_ar.merge(df_mr, on="mr_id")
        m2_df["distance_logistics"] = 0.05
        m2_df = pd.get_dummies(
            m2_df, columns=["mr_item_name", "mr_urgency"], drop_first=True
        )

        feature_cols = [
            col
            for col in m2_df.columns
            if "mr_item_name_" in col or "mr_urgency_" in col
        ] + ["mr_quantity", "distance_logistics"]

        X_m2 = m2_df[feature_cols].fillna(0)
        y_m2 = m2_df["ar_offered_price"]

        m2_model = RandomForestRegressor(n_estimators=50, random_state=42)
        m2_model.fit(X_m2, y_m2)

        joblib.dump(m2_model, PATH_MODEL_PRICING)
        joblib.dump(feature_cols, PATH_PRICING_COLUMNS)
        print(" -> [Success]: Trained and exported Dynamic Pricing Regressor Model.")
    except Exception as e:
        print(f" -> [Failure]: Model 2 setup bypassed due to error: {e}")

    # --- MODEL 3: THE TRUST SHIELD RISK CLASSIFIER ---
    try:
        df_w = data_access.get_workers_data()
        df_rep = data_access.get_worker_reports_data()

        dispute_counts = (
            df_rep[df_rep["reported_user_type"] == "Worker"]
            .groupby("reported_user_id")
            .size()
            .to_frame("disputes_logged")
        )

        df_m3 = df_w.merge(dispute_counts, left_on="w_id", right_index=True, how="left")
        df_m3["disputes_logged"] = df_m3["disputes_logged"].fillna(0)

        features_m3 = ["w_rating", "disputes_logged", "w_is_verified"]
        X_m3 = df_m3[features_m3].fillna(0)
        y_m3 = df_m3["is_blocked"].fillna(0).astype(int)

        m3_model = RandomForestClassifier(
            class_weight="balanced", random_state=42, n_estimators=50
        )
        m3_model.fit(X_m3, y_m3)
        joblib.dump(m3_model, PATH_MODEL_TRUST_SHIELD)
        print(" -> [Success]: Trained and exported Trust Shield Model.\n")
    except Exception as e:
        print(f" -> [Failure]: Model 3 setup bypassed due to error: {e}")


def load_models():
    """
    Load all pre-trained models. If models don't exist, train them first.

    Returns:
        dict: Dictionary of model objects with keys:
            - 'matchmaker': RandomForestClassifier for worker matchmaking
            - 'pricing': RandomForestRegressor for pricing predictions
            - 'pricing_columns': List of feature column names for pricing model
            - 'trust_shield': RandomForestClassifier for risk assessment
    """
    global _models, _models_loaded

    if _models_loaded:
        return _models

    # Check if pre-trained models exist
    if not (
        os.path.exists(PATH_MODEL_MATCHMAKING)
        and os.path.exists(PATH_MODEL_PRICING)
        and os.path.exists(PATH_MODEL_TRUST_SHIELD)
    ):
        print("[Models Missing]: Training new models from dataset...")
        _train_models()

    # Load models into memory
    try:
        _models = {
            "matchmaker": joblib.load(PATH_MODEL_MATCHMAKING),
            "pricing": joblib.load(PATH_MODEL_PRICING),
            "pricing_columns": joblib.load(PATH_PRICING_COLUMNS),
            "trust_shield": joblib.load(PATH_MODEL_TRUST_SHIELD),
        }
        _models_loaded = True
        return _models
    except Exception as e:
        print(f"[Critical]: Model load sequence crashed. Re-training... Details: {e}")
        _train_models()
        _models = {
            "matchmaker": joblib.load(PATH_MODEL_MATCHMAKING),
            "pricing": joblib.load(PATH_MODEL_PRICING),
            "pricing_columns": joblib.load(PATH_PRICING_COLUMNS),
            "trust_shield": joblib.load(PATH_MODEL_TRUST_SHIELD),
        }
        _models_loaded = True
        return _models


def get_matchmaker_model():
    """Get the worker matchmaking model."""
    models = load_models()
    return models["matchmaker"]


def get_pricing_model():
    """Get the pricing prediction model."""
    models = load_models()
    return models["pricing"]


def get_pricing_columns():
    """Get the list of feature columns for the pricing model."""
    models = load_models()
    return models["pricing_columns"]


def get_trust_shield_model():
    """Get the trust/risk assessment model."""
    models = load_models()
    return models["trust_shield"]
