"""
HUKUM Chatbot - Data Access Layer.

Handles all Excel workbook reading and data loading operations.
Provides a clean interface for other modules to access data.
"""

import pandas as pd
import os
import logging
import streamlit as st
from pathlib import Path
from .config import MASTER_EXCEL_PATH, LOGS_FILE

# Configure logging
logging.basicConfig(filename=LOGS_FILE, level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(message)s')

def _excel_file_exists() -> bool:
    """Check if the master Excel file exists.
    Returns:
        bool: True if file exists, else False.
    """
    exists = MASTER_EXCEL_PATH.is_file()
    if not exists:
        logging.error(f"Master Excel file not found at {MASTER_EXCEL_PATH}")
    return exists

def _sheet_exists(sheet_name: str) -> bool:
    """Check if a given sheet exists in the Excel workbook.
    Args:
        sheet_name (str): Name of the sheet to check.
    Returns:
        bool: True if sheet exists, else False.
    """
    try:
        xl = pd.ExcelFile(MASTER_EXCEL_PATH, engine="openpyxl")
        return sheet_name in xl.sheet_names
    except Exception as e:
        logging.error(f"Failed to open Excel file for sheet validation: {e}")
        return False

@st.cache_data(show_spinner=False)
def read_sheet(sheet_name: str) -> pd.DataFrame:
    """Read a specific sheet from the master Excel workbook with safety checks.
    Args:
        sheet_name (str): Name of the sheet to read (e.g., 'worker', 'job_post', 'reports').
    Returns:
        pd.DataFrame: DataFrame containing the sheet data, or empty DataFrame on failure.
    """
    if not _excel_file_exists():
        return pd.DataFrame()
    if not _sheet_exists(sheet_name):
        logging.error(f"Sheet '{sheet_name}' not found in workbook.")
        return pd.DataFrame()
    try:
        return pd.read_excel(MASTER_EXCEL_PATH, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        logging.error(f"Failed to read sheet '{sheet_name}': {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def get_workers_data() -> pd.DataFrame:
    """Load the worker sheet with caching and error handling."""
    return read_sheet("worker")

@st.cache_data(show_spinner=False)
def get_worker_reports_data() -> pd.DataFrame:
    """Load the reports sheet with caching and error handling."""
    return read_sheet("reports")

@st.cache_data(show_spinner=False)
def get_material_requirements_data() -> pd.DataFrame:
    """Load the material_requirement sheet with caching and error handling."""
    return read_sheet("material_requirement")

@st.cache_data(show_spinner=False)
def get_apply_requirements_data() -> pd.DataFrame:
    """Load the apply_requirement sheet with caching and error handling."""
    return read_sheet("apply_requirement")
