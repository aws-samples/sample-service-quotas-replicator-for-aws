"""
UI components for the Streamlit interface.
"""
import streamlit as st
from src.ui.formatting import add_row_numbers, highlight_differences, highlight_status, create_column_config
from src.ui.callbacks import select_all_callback, deselect_all_callback, bt_callback

def display_summary_metrics(df, source_only_df):
    """Display summary metrics for quota comparison."""
    st.markdown("### 📊 Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)

    total_quotas = len(df)
    different_quotas = len(df[df["Delta"].notna() & (df["Delta"] != 0)])
    adjustable_quotas = len(df[df["Adjustable"] == "✅"])
    source_only_services = len(source_only_df["Service"].unique()) if not source_only_df.empty else 0

    with col1:
        st.metric("Total Quotas", total_quotas)
    with col2:
        st.metric("Different Quotas", different_quotas)
    with col3:
        st.metric("Adjustable Quotas", adjustable_quotas)
    with col4:
        st.metric("Services Only in Source", source_only_services)

def display_source_only_quotas(source_only_df):
    """Display quotas that exist only in the source account."""
    if not source_only_df.empty:
        st.markdown("### AWS Services and Quotas Only in Source Account")
        source_only_df_numbered = add_row_numbers(source_only_df)
        st.dataframe(
            source_only_df_numbered,
            hide_index=True,
            use_container_width=True,
        )

def display_quota_selection_interface(different_df):
    """Display interface for selecting quotas to increase."""
    if not different_df.empty:
        # Add row numbers to the DataFrame
        different_df = different_df.copy()
        different_df.insert(
            0, "#", range(1, len(different_df) + 1)
        )  # Insert row numbers as first column
        different_df["Request Increase"] = False

        # Initialize session state for edited_df if not present
        if "edited_df" not in st.session_state:
            st.session_state.edited_df = different_df.copy()

        # Create selection interface
        st.markdown("Select quotas to request increases:")

        # Add select all button with improved layout and feedback
        with st.container():
            st.button("Select All Quotas", on_click=select_all_callback)
        with st.container():
            st.button("Deselect All", on_click=deselect_all_callback)

        # Create a form for batch submission
        with st.form("quota_increase_form", clear_on_submit=False):
            # Display table with checkboxes
            edited_df = st.data_editor(
                data=st.session_state.edited_df,
                hide_index=True,
                use_container_width=True,
                key="quota_editor",
                column_config=create_column_config()
            )

            # Update session state with edited values
            st.session_state.edited_df = edited_df

            # Submit button for batch processing
            st.form_submit_button(
                "Submit Quota Increase Requests",
                on_click=bt_callback
            )

def display_all_quotas(df):
    """Display all quotas with highlighting for differences."""
    st.markdown("#### All Quotas")
    if not df.empty:
        df_numbered = add_row_numbers(df)
        styled_df = df_numbered.style.apply(highlight_differences, axis=1)
        st.dataframe(styled_df, hide_index=True, use_container_width=True)

def display_quota_request_status_summary(status_df):
    """Display summary of quota request statuses."""
    if not status_df.empty:
        st.write("### Summary")
        total = len(status_df)
        pending = len(status_df[status_df["Request Status"].str.contains("PENDING", case=False, na=False)])
        approved = len(status_df[status_df["Request Status"] == "APPROVED"])
        denied = len(status_df[status_df["Request Status"].str.contains("DENIED", case=False, na=False)])
        not_approved = len(status_df[status_df["Request Status"].str.contains("NOT_APPROVED", case=False, na=False)])
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total", total)
        with col2:
            st.metric("Pending", pending)
        with col3:
            st.metric("Approved", approved)
        with col4:
            st.metric("Denied", denied)
        with col5:
            st.metric("Not Approved", not_approved)

def display_quota_submission_summary(history_df):
    """Display summary of quota submission results."""
    if not history_df.empty:
        # Format the DataFrame for better display
        display_columns = ["AqrToolRequestId", "Service", "Quota Name", "Existing Quota Value", "Desired Quota Value", "Request Status"]
        
        # Display the styled DataFrame
        st.write("### Quota Submission Summary")
        styled_history_df = history_df[display_columns].style.apply(highlight_status, axis=1)
        st.dataframe(styled_history_df, use_container_width=True, hide_index=True)
        
        # Show statistics
        total = len(history_df)
        successful = len(history_df[~history_df["Request Status"].str.contains("Failed|Skipped", na=False)])
        failed = len(history_df[history_df["Request Status"].str.contains("Failed", na=False)])
        skipped = len(history_df[history_df["Request Status"].str.contains("Skipped", na=False)])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Requests", total)
        with col2:
            st.metric("Successful", successful)
        with col3:
            st.metric("Failed", failed)
        with col4:
            st.metric("Skipped", skipped)
