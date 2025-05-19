"""
UI formatting utilities for the Streamlit interface.
"""
import streamlit as st

def add_row_numbers(df):
    """Add row numbers to a DataFrame."""
    df = df.copy()
    # Create a new column "#" with row numbers and insert it at the beginning
    df.insert(0, "#", range(1, len(df) + 1))
    return df

def highlight_differences(row):
    """Highlight rows where values are different between source and destination."""
    if isinstance(row["Delta"], (int, float)) and row["Delta"] != 0:
        return ["background-color: #ffeb99"] * len(row)
    return [""] * len(row)

def highlight_status(row):
    """Highlight rows based on request status."""
    status = str(row.get("Request Status", ""))
    if status == "APPROVED":
        return ["background-color: #ccffcc"] * len(row)  # Green
    elif status == "PENDING":
        return ["background-color: #ffffcc"] * len(row)  # Yellow
    elif status == "DENIED":
        return ["background-color: #ffcccc"] * len(row)  # Red
    elif status == "NOT_APPROVED":
        return ["background-color: #ffeecc"] * len(row)  # Light orange
    elif "Failed" in status:
        return ["background-color: #ffcccc"] * len(row)  # Red
    elif "Skipped" in status:
        return ["background-color: #ffffcc"] * len(row)  # Yellow
    else:
        return [""] * len(row)

def create_column_config():
    """Create column configuration for data editor."""
    return {
        "#": st.column_config.NumberColumn(
            "Row",
            help="Row number",
            disabled=True,
            width="small",
        ),
        "Request Increase": st.column_config.CheckboxColumn(
            "Select",
            help="Select to request quota increase",
            width="small",
        ),
        "Service": st.column_config.TextColumn(
            "Service", disabled=True
        ),
        "Quota Name": st.column_config.TextColumn(
            "Quota Name", disabled=True
        ),
        "Source Value": st.column_config.NumberColumn(
            "Source Value", disabled=True
        ),
        "Destination Value": st.column_config.NumberColumn(
            "Destination Value", disabled=True
        ),
        "Delta": st.column_config.NumberColumn(
            "Delta", disabled=True
        ),
        "Adjustable": st.column_config.TextColumn(
            "Adjustable", disabled=True
        ),
    }
