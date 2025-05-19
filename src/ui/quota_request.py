"""
Functions for handling quota increase requests.
"""
import json
import uuid
import datetime
import time
import streamlit as st
import pandas as pd
import boto3

from src.utils.logger import logger
from src.utils.cache import CACHE_DIR
from src.ui.formatting import highlight_status
from src.ui.components import display_quota_submission_summary

def process_quota_increase_requests(dest_profile, dest_region, selected_quotas):
    """Process quota increase requests for selected quotas."""
    quotas_history_data = []
    unique_id = str(uuid.uuid4().int)[:8]
    now = datetime.datetime.now()
    timestamp = now.strftime('%Y%m%d%H%M%S')
    quota_submission_history_file = CACHE_DIR / f"quotas_history_{timestamp}_{unique_id}.json"
    
    if not selected_quotas.empty:
        try:
            session = boto3.Session(profile_name=dest_profile)
            client = session.client("service-quotas", region_name=dest_region)
            retry_count = 0
            base_delay = 1
            max_retries = 5

            # Process each selected quota
            for _, row in selected_quotas.iterrows():
                if row["Adjustable"] == "✅":  # Only process adjustable quotas
                    while retry_count < max_retries:
                        try:
                            response = client.request_service_quota_increase(
                                ServiceCode=row["ServiceCode"],
                                QuotaCode=row["QuotaCode"],
                                DesiredValue=float(row["Source Value"]),
                                SupportCaseAllowed=False
                            )
                            requested_quota = response['RequestedQuota']
                            quotas_history_data.append(
                                {
                                    "AqrToolRequestId": f'{timestamp}_{unique_id}',
                                    "RequestedId": requested_quota["Id"],
                                    "Service": requested_quota["ServiceName"],
                                    "Quota Name": requested_quota["QuotaName"],
                                    "Existing Quota Value": row["Destination Value"],
                                    "Desired Quota Value": requested_quota["DesiredValue"],
                                    "ServiceCode": row["ServiceCode"],
                                    "QuotaCode": requested_quota["QuotaCode"],
                                    "Request Status": requested_quota['Status'],
                                }
                            )
                            break  # Success, exit the retry loop
                        except client.exceptions.TooManyRequestsException as e:
                            retry_count += 1
                            if retry_count < max_retries:
                                delay = base_delay * (2 ** retry_count)
                                st.warning(f"Retrying in {delay} seconds due to rate limiting")
                                time.sleep(delay)
                            else:
                                st.error(f"Failed to request increase for {row['Service']} - {row['Quota Name']}: Rate limit exceeded")
                                # Add failed requests to history with error status
                                quotas_history_data.append(
                                    {
                                        "AqrToolRequestId": f'{timestamp}_{unique_id}',
                                        "RequestedId": "Failed",
                                        "Service": row["Service"],
                                        "Quota Name": row["Quota Name"],
                                        "Existing Quota Value": row["Destination Value"],
                                        "Desired Quota Value": row["Source Value"],
                                        "ServiceCode": row["ServiceCode"],
                                        "QuotaCode": row["QuotaCode"],
                                        "Request Status": f"Failed: Rate limit exceeded",
                                    }
                                )
                                break
                        except Exception as e:
                            st.error(f"Failed to request increase for {row['Service']} - {row['Quota Name']}: {str(e)}")
                            # Add failed requests to history with error status
                            quotas_history_data.append(
                                {
                                    "AqrToolRequestId": f'{timestamp}_{unique_id}',
                                    "RequestedId": "Failed",
                                    "Service": row["Service"],
                                    "Quota Name": row["Quota Name"],
                                    "Existing Quota Value": row["Destination Value"],
                                    "Desired Quota Value": row["Source Value"],
                                    "ServiceCode": row["ServiceCode"],
                                    "QuotaCode": row["QuotaCode"],
                                    "Request Status": f"Failed: {str(e)}",
                                }
                            )
                            break
                else:
                    st.warning(f"Skipped non-adjustable quota: {row['Service']} - {row['Quota Name']}")
                    # Add skipped quotas to history
                    quotas_history_data.append(
                        {
                            "AqrToolRequestId": f'{timestamp}_{unique_id}',
                            "RequestedId": "Skipped",
                            "Service": row["Service"],
                            "Quota Name": row["Quota Name"],
                            "Existing Quota Value": row["Destination Value"],
                            "Desired Quota Value": row["Source Value"],
                            "ServiceCode": row["ServiceCode"],
                            "QuotaCode": row["QuotaCode"],
                            "Request Status": "Skipped (Non-adjustable)",
                        }
                    )
        except Exception as e:
            st.error(f"Failed to create AWS client: {str(e)}")
        
        # Save quota submission history to file
        try:
            with open(quota_submission_history_file, "w") as f:
                json.dump(quotas_history_data, f)
        except Exception as e:
            st.warning(f"History write error: {str(e)}")
        
        # Display submission summary
        if quotas_history_data:
            st.success(f"Quota increase requests processed. Service quota increase is an asynchronous process and use the AqrToolRequestId {timestamp}_{unique_id} value to get the status of last submitted increase.")
            history_df = pd.DataFrame(quotas_history_data)
            display_quota_submission_summary(history_df)
        else:
            st.warning("No quota increase requests were processed.")
    else:
        st.warning("No quotas selected for increase requests.")
    
    return timestamp, unique_id

def check_quota_request_status(dest_profile, dest_region, request_id):
    """Check the status of previously submitted quota increase requests."""
    with st.spinner("Checking quota request status..."):
        logger.info(f"Checking status for request ID: {request_id}")
        # Find the selected request file
        selected_file = CACHE_DIR / f'quotas_history_{request_id}.json'
        
        # Load the request history
        try:
            with open(selected_file, "r") as f:
                history_data = json.load(f)
                logger.info(f"Successfully loaded history data with {len(history_data)} entries")
        except Exception as e:
            error_msg = f"Error reading history file: {str(e)}"
            logger.error(error_msg)
            st.error(error_msg)
            return
        
        if not history_data:
            logger.warning("No quota requests found in the history file")
            st.warning("No quota requests found in the history file.")
            return
        
        # Create AWS client for checking status
        try:
            session = boto3.Session(profile_name=dest_profile)
            sq_client = session.client("service-quotas", region_name=dest_region)
            
            # Update status for each request
            updated_status = []
            
            for request in history_data:
                # Skip entries that were already marked as skipped or failed
                if "Skipped" in request.get("Request Status", "") or "Failed" in request.get("Request Status", ""):
                    updated_status.append(request)
                    continue
                    
                # Get the current status for requests that have an ID
                if request.get("RequestedId") and request["RequestedId"] != "Failed" and request["RequestedId"] != "Skipped":
                    try:
                        response = sq_client.get_requested_service_quota_change(
                            RequestId=request["RequestedId"]
                        )
                        
                        # Update the status
                        requested_quota = response.get("RequestedQuota", {})
                        current_status = requested_quota.get("Status", "Unknown")
                        logger.info(f"Retrieved status for {request.get('Service')} - {request.get('Quota Name')}: {current_status}")
                        
                        # Create updated request entry
                        updated_request = request.copy()
                        updated_request["Request Status"] = current_status
                        updated_request["Last Checked"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        updated_status.append(updated_request)
                    except Exception as e:
                        # If we can't get the status, keep the original status but note the error
                        updated_request = request.copy()
                        updated_request["Request Status"] = f"{request.get('Request Status', 'Unknown')} (Status check failed: {str(e)})"
                        updated_request["Last Checked"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        updated_status.append(updated_request)
                else:
                    # Keep the original entry for requests without IDs
                    updated_status.append(request)
            
            # Create DataFrame for display
            if updated_status:
                logger.info(f"Displaying status for {len(updated_status)} quota requests")
                status_df = pd.DataFrame(updated_status)
                
                # Define display columns
                display_columns = ["Service", "Quota Name", "Existing Quota Value", "Desired Quota Value", "Request Status"]
                if "Last Checked" in status_df.columns:
                    display_columns.append("Last Checked")
                
                # Display the styled DataFrame
                st.write("### Quota Request Status")
                logger.info("Displaying quota request status with filtering options")
                
                # Filter to show only pending or not approved
                if not status_df.empty:
                    # Create filters
                    st.write("Filter by status:")
                    col1, col2, col3, col4 = st.columns(4)
                    # Apply filters
                    filtered_df = status_df.copy()
                    mask = pd.Series(False, index=filtered_df.index)
                    
                    with col1:
                        mask = mask | filtered_df["Request Status"].str.contains("PENDING", case=False, na=False)
                    with col2:
                        mask = mask | (filtered_df["Request Status"] == "APPROVED")
                    with col3:
                        mask = mask | filtered_df["Request Status"].str.contains("DENIED", case=False, na=False)
                    with col4:
                        mask = mask | filtered_df["Request Status"].str.contains("NOT_APPROVED", case=False, na=False)
                    
                    filtered_df = filtered_df[mask]
                    
                    if not filtered_df.empty:
                        styled_df = filtered_df[display_columns].style.apply(highlight_status, axis=1)
                        st.dataframe(styled_df, use_container_width=True, hide_index=True)
                        
                        # Show statistics
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
                    else:
                        st.info("No quota requests match the selected filters.")
                else:
                    st.info("No quota requests found with status information.")
                
                # Save the updated status back to the file
                try:
                    with open(selected_file, "w") as f:
                        json.dump(updated_status, f)
                    st.success("For all the Not Approved or Denied Quotas submit a [support ticket](https://support.console.aws.amazon.com/)")
                    st.success(f"Status information updated and saved to {selected_file.name}")
                except Exception as e:
                    st.warning(f"Could not save updated status: {str(e)}")
            else:
                st.warning("No quota requests found with status information.")
        except Exception as e:
            st.error(f"Error checking quota status: {str(e)}")

def get_request_history_files():
    """Get list of quota request history files."""
    history_files = list(CACHE_DIR.glob("quotas_history_*.json"))
    
    request_ids = []
    for file in history_files:
        # Extract timestamp and unique ID from filename
        filename = file.name
        if filename.startswith("quotas_history_"):
            # Format: quotas_history_YYYYMMDDHHMMSS_UNIQUEID.json
            parts = filename.replace("quotas_history_", "").replace(".json", "").split("_")
            if len(parts) == 2:
                timestamp, unique_id = parts
                request_ids.append({
                    "id": f"{timestamp}_{unique_id}",
                    "timestamp": timestamp,
                    "display": f"{timestamp[:8]}-{timestamp[8:]} (ID: {unique_id})",
                    "file": file
                })
    
    # Sort by timestamp (newest first)
    request_ids.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return request_ids
