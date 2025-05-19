"""
AWS Service Quotas API interaction functions.
"""
import time
import boto3
import streamlit as st
import concurrent.futures
from typing import Dict, Tuple
from pathlib import Path

from src.utils.logger import logger
from src.utils.cache import CACHE_DIR, save_to_cache, load_from_cache

def fetch_quotas_from_aws(profile_name: str, region_name: str) -> Dict:
    """Fetch quotas from AWS for a specific profile and region."""
    try:
        logger.info(f"Fetching quotas from AWS for {profile_name} in {region_name}")
        session = boto3.Session(profile_name=profile_name)
        client = session.client("service-quotas", region_name=region_name)

        quotas_data = {}

        # Get list of AWS services
        logger.info("Listing AWS services")
        paginator = client.get_paginator("list_services")
        service_count = 0
        for page in paginator.paginate():
            for service in page["Services"]:
                service_code = service["ServiceCode"]
                service_name = service["ServiceName"]
                service_count += 1

                default_value = None
                retry_count = 0
                base_delay = 1
                max_retries = 5
                
                logger.debug(f"Processing service: {service_name} ({service_code})")

                # Get quotas for each service
                try:
                    quota_paginator = client.get_paginator("list_service_quotas")
                    for quota_page in quota_paginator.paginate(
                        ServiceCode=service_code
                    ):
                        for quota in quota_page["Quotas"]:
                            key = f"{service_name} - {quota['QuotaName']}"

                            # Get the default value
                            default_value = None
                            while retry_count < max_retries:
                                try:  
                                    default_response = client.get_aws_default_service_quota(
                                        ServiceCode=service_code,
                                        QuotaCode=quota["QuotaCode"],
                                    )
                                    default_value = default_response.get("Quota", {}).get("Value")
                                    # If successful, break out of the retry loop
                                    break
                                except client.exceptions.TooManyRequestsException:
                                    # Calculate exponential backoff delay
                                    delay = base_delay * (0.2 ** retry_count)
                                    # print(f"Rate limited as Throttle rate for GetAWSDefaultServiceQuota is 5 per second Retrying in {delay} seconds...")
                                    time.sleep(delay)
                                    retry_count += 1
                                    # If we've reached max retries, use the quota value as default
                                    if retry_count >= max_retries:
                                        default_value = quota["Value"]
                                except client.exceptions.NoSuchResourceException:
                                    default_value = quota["Value"]

                            quotas_data[key] = {
                                "Value": quota["Value"],
                                "DefaultValue": default_value,
                                "Unit": quota.get("Unit", "None"),
                                "Adjustable": quota["Adjustable"],
                                "ServiceCode": service_code,
                                "QuotaCode": quota["QuotaCode"],
                            }
                except Exception as e:
                    st.warning(
                        f"Error fetching quotas for service {service_code}: {str(e)}"
                    )
                    continue

        logger.info(f"Successfully fetched {len(quotas_data)} quotas for {profile_name} in {region_name}")
        return quotas_data

    except Exception as e:
        st.error(
            f"Error fetching quotas for profile {profile_name} in region {region_name}: {str(e)}"
        )
        return {}

def fetch_quotas_in_parallel(source_profile: str, source_region: str, dest_profile: str, dest_region: str, enable_cache: bool = False) -> Tuple[Dict, Dict]:
    """Fetch quotas for source and destination in parallel."""
    logger.info(f"Fetching quotas in parallel for source ({source_profile}/{source_region}) and destination ({dest_profile}/{dest_region})")
    logger.info(f"Enable Cache: {enable_cache}")
    
    # Create placeholders for progress messages
    source_placeholder = st.empty()
    dest_placeholder = st.empty()
    source_placeholder.info(f"Fetching data for {source_profile} in {source_region}...")
    dest_placeholder.info(f"Fetching data for {dest_profile} in {dest_region}...")
    
    # Store the placeholders in session state so we can clear them later
    if "info_placeholders" not in st.session_state:
        st.session_state.info_placeholders = []
    st.session_state.info_placeholders.extend([source_placeholder, dest_placeholder])
    
    source_cache_file = CACHE_DIR / f"quotas_{source_profile}_{source_region}.json"
    dest_cache_file = CACHE_DIR / f"quotas_{dest_profile}_{dest_region}.json"
    
    source_quotas = {}
    dest_quotas = {}
    source_cached = False
    dest_cached = False
    
    # Check if cache files exist
    if enable_cache:
        source_cached = source_cache_file.exists()
        dest_cached = dest_cache_file.exists()
    
    # Use ThreadPoolExecutor to fetch quotas in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Define tasks based on cache availability
        tasks = {}
        
        if source_cached:
            source_placeholder.info(f"Loading cached data for {source_profile} in {source_region}...")
            source_quotas = load_from_cache(source_cache_file)
            if source_quotas is None:  # Cache read failed
                source_placeholder.warning(f"Cache read failed for {source_profile}, fetching from AWS...")
                tasks[executor.submit(fetch_quotas_from_aws, source_profile, source_region)] = "source"
        else:
            tasks[executor.submit(fetch_quotas_from_aws, source_profile, source_region)] = "source"
            
        if dest_cached:
            dest_placeholder.info(f"Loading cached data for {dest_profile} in {dest_region}...")
            dest_quotas = load_from_cache(dest_cache_file)
            if dest_quotas is None:  # Cache read failed
                dest_placeholder.warning(f"Cache read failed for {dest_profile}, fetching from AWS...")
                tasks[executor.submit(fetch_quotas_from_aws, dest_profile, dest_region)] = "dest"
        else:
            tasks[executor.submit(fetch_quotas_from_aws, dest_profile, dest_region)] = "dest"
        
        # Process completed tasks
        for future in concurrent.futures.as_completed(tasks):
            task_type = tasks[future]
            try:
                result = future.result()
                if task_type == "source":
                    source_quotas = result
                    source_placeholder.success(f"Completed fetching data for {source_profile} in {source_region}")
                    if not source_cached and source_quotas:
                        save_to_cache(source_quotas, source_cache_file)
                else:  # dest
                    dest_quotas = result
                    dest_placeholder.success(f"Completed fetching data for {dest_profile} in {dest_region}")
                    if not dest_cached and dest_quotas:
                        save_to_cache(dest_quotas, dest_cache_file)
            except Exception as e:
                if task_type == "source":
                    source_placeholder.error(f"Error fetching quotas for {source_profile}: {str(e)}")
                else:  # dest
                    dest_placeholder.error(f"Error fetching quotas for {dest_profile}: {str(e)}")
    
    return source_quotas, dest_quotas

def request_quota_increase(profile_name: str, region_name: str, service_code: str, quota_code: str, desired_value: float):
    """Request a quota increase for a specific service and quota."""
    try:
        session = boto3.Session(profile_name=profile_name)
        client = session.client("service-quotas", region_name=region_name)
        
        response = client.request_service_quota_increase(
            ServiceCode=service_code,
            QuotaCode=quota_code,
            DesiredValue=float(desired_value),
            SupportCaseAllowed=False
        )
        
        return response.get('RequestedQuota', {})
    except Exception as e:
        logger.error(f"Error requesting quota increase: {str(e)}")
        raise

def get_quota_request_status(profile_name: str, region_name: str, request_id: str):
    """Get the status of a quota increase request."""
    try:
        session = boto3.Session(profile_name=profile_name)
        client = session.client("service-quotas", region_name=region_name)
        
        response = client.get_requested_service_quota_change(
            RequestId=request_id
        )
        
        return response.get('RequestedQuota', {})
    except Exception as e:
        logger.error(f"Error getting quota request status: {str(e)}")
        raise
