"""
Callback functions for the Streamlit UI.
"""
import streamlit as st
from src.utils.logger import logger

def bt_callback():
    """Callback for form submission."""
    st.session_state.form_submitted = 1
    logger.info("Form submitted callback triggered")

def select_all_callback():
    """Callback to select all quotas."""
    if st.session_state.edited_df is not None:
        st.session_state.selected_all = True
        st.session_state.edited_df["Request Increase"] = True
        logger.info("Select all callback triggered")

def deselect_all_callback():
    """Callback to deselect all quotas."""
    if st.session_state.edited_df is not None:
        st.session_state.deselected_all = True
        st.session_state.edited_df["Request Increase"] = False
        logger.info("Deselect all callback triggered")
