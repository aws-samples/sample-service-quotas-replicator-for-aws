"""
AWS profile and region management utilities.
"""
import boto3
from src.utils.logger import logger

def get_aws_profiles():
    """Get list of available AWS profiles."""
    try:
        logger.info("Fetching available AWS profiles")
        session = boto3.Session()
        profiles = session.available_profiles
        logger.info(f"Found {len(profiles)} AWS profiles")
        return profiles
    except Exception as e:
        error_msg = f"Error fetching AWS profiles: {str(e)}"
        logger.error(error_msg)
        return []

def get_aws_regions():
    """Get list of AWS regions."""
    logger.info("Returning list of AWS regions")
    return [
        "us-east-1",  # US East (N. Virginia)
        "us-east-2",  # US East (Ohio)
        "us-west-1",  # US West (N. California)
        "us-west-2",  # US West (Oregon)
        "af-south-1",  # Africa (Cape Town)
        "ap-east-1",  # Asia Pacific (Hong Kong)
        "ap-south-1",  # Asia Pacific (Mumbai)
        "ap-south-2",  # Asia Pacific (Hyderabad)
        "ap-southeast-1",  # Asia Pacific (Singapore)
        "ap-southeast-2",  # Asia Pacific (Sydney)
        "ap-southeast-3",  # Asia Pacific (Jakarta)
        "ap-southeast-4",  # Asia Pacific (Melbourne)
        "ap-northeast-1",  # Asia Pacific (Tokyo)
        "ap-northeast-2",  # Asia Pacific (Seoul)
        "ap-northeast-3",  # Asia Pacific (Osaka)
        "ca-central-1",  # Canada (Central)
        "ca-west-1",  # Canada West (Calgary)
        "eu-central-1",  # Europe (Frankfurt)
        "eu-central-2",  # Europe (Zurich)
        "eu-west-1",  # Europe (Ireland)
        "eu-west-2",  # Europe (London)
        "eu-west-3",  # Europe (Paris)
        "eu-south-1",  # Europe (Milan)
        "eu-south-2",  # Europe (Spain)
        "eu-north-1",  # Europe (Stockholm)
        "il-central-1",  # Israel (Tel Aviv)
        "me-central-1",  # Middle East (UAE)
        "me-south-1",  # Middle East (Bahrain)
        "sa-east-1",  # South America (São Paulo)
        "us-gov-east-1",  # AWS GovCloud (US-East)
        "us-gov-west-1",  # AWS GovCloud (US-West)
    ]
