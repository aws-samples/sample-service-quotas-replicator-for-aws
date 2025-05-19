"""
AWS Service Quotas Comparison Tool - Main Application

This tool allows users to compare service quotas between different AWS accounts and regions,
identify differences, and request quota increases to match source account values.
"""
import streamlit as st
import time
import pandas as pd

# Import modules
from src.utils.logger import logger
from src.aws.profiles import get_aws_profiles, get_aws_regions
from src.aws.quotas import fetch_quotas_in_parallel
from src.aws.comparison import compare_quotas
from src.ui.sidebar import render_sidebar
from src.ui.callbacks import bt_callback, select_all_callback, deselect_all_callback
from src.ui.components import (
    display_summary_metrics, 
    display_source_only_quotas, 
    display_quota_selection_interface,
    display_all_quotas
)
from src.ui.quota_request import (
    process_quota_increase_requests,
    check_quota_request_status,
    get_request_history_files
)
from src.ui.formatting import add_row_numbers, highlight_differences

# IMPORTANT: set_page_config must be the first Streamlit command
st.set_page_config(
    page_title="AWS Service Quotas Comparison", page_icon="☁️", layout="wide"
)

def main():
    """Main application function."""
    logger.info("Starting main application function")
    
    # Display title with AWS logo using markdown with HTML
    st.markdown(
        """
        <div style="display: flex; align-items: center;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg" width="40" style="margin-right: 10px;">
            <span style="font-size: 2em; font-weight: bold;">AWS Service Quotas Replicator</span>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Render sidebar with cache controls
    render_sidebar()

    # Get available AWS profiles
    aws_profiles = get_aws_profiles()

    if not aws_profiles:
        st.error("No AWS profiles found. Please configure your AWS credentials.")
        st.info(
            """
        💡 Configure your AWS profiles in ~/.aws/credentials or ~/.aws/config
        Example format in ~/.aws/config:
        ```
        profile profile-name
        region = us-west-2
        output = json
        ```
        """
        )
        return

    # AWS Profile and Region Selection with improved layout
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Source Configuration")
        source_profile = st.selectbox(
            "Select source AWS profile", options=aws_profiles, key="source"
        )
        source_region = st.selectbox(
            "Select source region", options=get_aws_regions(), key="source_region"
        )

    with col2:
        st.markdown("### Destination Configuration")
        dest_profile = st.selectbox(
            "Select destination AWS profile", options=aws_profiles, key="dest"
        )
        dest_region = st.selectbox(
            "Select destination region", options=get_aws_regions(), key="dest_region"
        )

    # Add suppress defaults checkbox
    suppress_defaults = st.checkbox(
        "Suppress default values",
        value=False,
        help="Only show quotas that have been modified from their defaults",
    )

    # Add cache support checkbox
    enable_cache = st.checkbox(
        "Cache",
        value=False,
        help="Enable cache if you want to use the cached files for the selected profile...",
    )

    # Handle selected_all state
    if "selected_all" in st.session_state and "edited_df" in st.session_state:
        if st.session_state.selected_all:
            dest_profile = st.session_state.dest
            dest_region = st.session_state.dest_region
            edited_df = st.session_state.edited_df
            selected_quotas_count = edited_df["Request Increase"].sum()
            st.write(f'Going to submit quotas for {selected_quotas_count}')
            with st.container():
                st.button("Deselect All", on_click=deselect_all_callback)
            with st.form("quota_increase_form", clear_on_submit=False):
                # Display table with checkboxes
                st.data_editor(
                    data=edited_df,
                    hide_index=True,
                    use_container_width=True,
                    key="quota_editor",
                    column_config={
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
                    },
                )

                # Update session state with edited values
                st.session_state.edited_df = edited_df

                # Submit button for batch processing
                st.form_submit_button(
                    "Submit Quota Increase Requests",
                    on_click=bt_callback
                )
            st.session_state.selected_all=False
    
    # Handle deselected_all state
    if "deselected_all" in st.session_state and "edited_df" in st.session_state:
        if st.session_state.deselected_all:
            dest_profile = st.session_state.dest
            dest_region = st.session_state.dest_region
            edited_df = st.session_state.edited_df
            selected_quotas_count = edited_df["Request Increase"].sum()
            st.write(f'Going to submit quotas for {selected_quotas_count}')
            with st.container():
                st.button("Select All", on_click=select_all_callback)
            with st.form("quota_increase_form", clear_on_submit=False):
                # Display table with checkboxes
                st.data_editor(
                    data=edited_df,
                    hide_index=True,
                    use_container_width=True,
                    key="quota_editor",
                    column_config={
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
                    },
                )

                # Update session state with edited values
                st.session_state.edited_df = edited_df

                # Submit button for batch processing
                st.form_submit_button(
                    "Submit Quota Increase Requests",
                    on_click=bt_callback
                )
            st.session_state.deselected_all=False

    # Handle selected_request_id state
    if "selected_request_id" in st.session_state:
        check_quota_request_status(dest_profile, dest_region, st.session_state.selected_request_id)
    
    # Handle form_submitted state
    if "form_submitted" in st.session_state and "edited_df" in st.session_state:
        dest_profile = st.session_state.dest
        dest_region = st.session_state.dest_region
        edited_df = st.session_state.edited_df
        edited_rows_session = st.session_state.quota_editor['edited_rows']
        
        # First, explicitly convert the column to boolean type
        edited_df["Request Increase"] = edited_df["Request Increase"].astype(bool)

        # Get selected rows
        for pos_index, update in edited_rows_session.items():
            if pos_index < len(edited_df):  # Avoid out-of-range
                actual_index = edited_df.index[pos_index]  # Get actual row index from position
                for col, val in update.items():
                    if col in edited_df.columns:
                        edited_df.at[actual_index, col] = val
        
        # Get the selected quotas using boolean indexing
        selected_quotas = edited_df[edited_df["Request Increase"] == True]
        
        # Process quota increase requests
        process_quota_increase_requests(dest_profile, dest_region, selected_quotas)
        
        # Clear session state after processing
        st.session_state.clear()

    # Compare Quotas button
    if (
        st.button("🔍 Compare Quotas", type="primary")
        and source_profile
        and dest_profile
        and ("selected_all" or "deselected_all") not in st.session_state
    ):
        with st.spinner("Fetching and comparing quotas ..."):
            progress_bar = st.progress(0)
            cache_message_placeholder= st.empty()

            # Fetch quotas in parallel
            if enable_cache:
                source_quotas, dest_quotas = fetch_quotas_in_parallel(
                    source_profile, source_region, dest_profile, dest_region, enable_cache
                )
            else:
                cache_message_placeholder.info("Please wait while AQR compares quota data between regions...")
                source_quotas, dest_quotas = fetch_quotas_in_parallel(
                    source_profile, source_region, dest_profile, dest_region
                )
            # Clear the message once quotas are fetched
            cache_message_placeholder.empty()
            progress_bar.progress(100)
            time.sleep(0.5)
            progress_bar.empty()

            if source_quotas and dest_quotas:
                # Compare quotas and create DataFrames
                df, source_only_df = compare_quotas(
                    source_quotas, dest_quotas, suppress_defaults
                )

                if df.empty and source_only_df.empty:
                    st.info("No differences found or all values are at their defaults.")
                    return

                # Add region information to the display
                st.markdown(f"### Comparing quotas between:")
                st.markdown(f"- Source: {source_profile} ({source_region})")
                st.markdown(f"- Destination: {dest_profile} ({dest_region})")
                
                # Clear the loading info messages
                if "info_placeholders" in st.session_state:
                    for placeholder in st.session_state.info_placeholders:
                        placeholder.empty()
                    st.session_state.info_placeholders = []
                
                # Display summary metrics
                display_summary_metrics(df, source_only_df)

                # Display source-only quotas
                display_source_only_quotas(source_only_df)
                
                # Different quotas
                st.markdown("### 📋 Quota Comparisons")
                st.markdown("#### Different Quotas")

                different_df = df[df["Delta"].notna() & (df["Delta"] != 0)].copy()
                if not different_df.empty:
                    display_quota_selection_interface(different_df)

                # Display all quotas
                display_all_quotas(df)
    
    # Get Quota Status button
    elif (
        st.button("⏰ Get Quota Status", type="primary", help="Check the status of previously submitted quota increase requests")
        and dest_profile and ("selected_all" or "deselected_all") not in st.session_state
    ):
        # Create a container for the quota status check interface
        status_container = st.container()
        
        with status_container:
            # Get request history files
            request_ids = get_request_history_files()
            
            if not request_ids:
                st.error("No quota request history found. Please submit quota increase requests first.")
                return
                
            # Let user select a request ID
            selected_request = st.selectbox(
                "Select a previous quota request to check status:",
                options=[req["id"] for req in request_ids],
                index=None,
                format_func=lambda x: next((req["display"] for req in request_ids if req["id"] == x), x),
                key="selected_request_id"
            )

if __name__ == "__main__":
    main()
