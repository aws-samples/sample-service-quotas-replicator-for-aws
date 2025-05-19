"""
Functions for comparing AWS service quotas between accounts.
"""
import pandas as pd
from typing import Dict, Tuple
from src.utils.logger import logger

def compare_quotas(
    source_quotas: Dict, dest_quotas: Dict, suppress_defaults: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compare quotas between source and destination profiles."""
    logger.info(f"Comparing quotas between source and destination profiles")
    logger.info(f"Source quotas count: {len(source_quotas)}")
    logger.info(f"Destination quotas count: {len(dest_quotas)}")
    logger.info(f"Suppress defaults: {suppress_defaults}")

    all_quotas = set(source_quotas.keys()) | set(dest_quotas.keys())
    comparison_data = []
    source_only_data = []

    # Track unique services in source only
    source_only_services = set()

    for quota_name in all_quotas:
        source_quota = source_quotas.get(quota_name, {})
        dest_quota = dest_quotas.get(quota_name, {})

        service_name = quota_name.split(" - ")[0]
        quota_name_only = quota_name.split(" - ")[1]

        source_value = source_quota.get("Value", "Not Set")
        dest_value = dest_quota.get("Value", "Not Set")
        source_default = source_quota.get("DefaultValue", source_value)
        dest_default = dest_quota.get("DefaultValue", dest_value)

        unit = source_quota.get("Unit") or dest_quota.get("Unit", "")
        adjustable = source_quota.get("Adjustable") or dest_quota.get(
            "Adjustable", False
        )
        service_code = source_quota.get("ServiceCode") or dest_quota.get(
            "ServiceCode", ""
        )

        quota_code = source_quota.get("QuotaCode") or dest_quota.get(
            "QuotaCode", ""
        )

        # Check if quota exists only in source
        if quota_name in source_quotas and quota_name not in dest_quotas:
            source_only_services.add(service_name)
            source_only_data.append(
                {
                    "Service": service_name,
                    "Quota Name": quota_name_only,
                    "Source Value": source_value,
                    "Source Default": source_default,
                    "Unit": unit,
                    "Adjustable": "✅" if adjustable else "❌",
                    "ServiceCode": service_code,
                    "QuotaCode": quota_code
                }
            )
            continue

        # Skip if both values are at their defaults and suppress_defaults is True
        if (
            suppress_defaults
            and source_value == source_default
            and dest_value == dest_default
        ):
            continue

        # Calculate delta only if both values are numeric
        if isinstance(source_value, (int, float)) and isinstance(
            dest_value, (int, float)
        ):
            delta = dest_value - source_value
        else:
            delta = "N/A"

        comparison_data.append(
            {
                "Service": service_name,
                "Quota Name": quota_name_only,
                "Source Value": source_value,
                "Source Default": source_default,
                "Destination Value": dest_value,
                "Destination Default": dest_default,
                "Unit": unit,
                "Delta": delta,
                "Adjustable": "✅" if adjustable else "❌",
                "ServiceCode": service_code,
                "QuotaCode": quota_code
            }
        )

    # Create DataFrames
    comparison_df = (
        pd.DataFrame(comparison_data)
        if comparison_data
        else pd.DataFrame(
            columns=[
                "Service",
                "Quota Name",
                "Source Value",
                "Source Default",
                "Destination Value",
                "Destination Default",
                "Unit",
                "Delta",
                "Adjustable",
                "ServiceCode",
                "QuotaCode"
            ]
        )
    )

    # Convert numeric columns to strings to avoid Arrow conversion issues
    for col in comparison_df.select_dtypes(include='object').columns:
        comparison_df[col] = comparison_df[col].astype('string')
    
    source_only_df = (
        pd.DataFrame(source_only_data)
        if source_only_data
        else pd.DataFrame(
            columns=[
                "Service",
                "Quota Name",
                "Source Value",
                "Source Default",
                "Unit",
                "Adjustable",
                "ServiceCode",
                "QuotaCode"
            ]
        )
    )

     # Convert numeric columns to strings to avoid Arrow conversion issues
    for col in source_only_df.select_dtypes(include='object').columns:
        source_only_df[col] = source_only_df[col].astype('string')

    # Convert Delta to numeric in comparison_df
    if not comparison_df.empty and "Delta" in comparison_df.columns:
        comparison_df["Delta"] = pd.to_numeric(comparison_df["Delta"], errors="coerce")
    return comparison_df, source_only_df
