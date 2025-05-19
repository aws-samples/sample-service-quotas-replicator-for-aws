"""
Cache management utilities for the AWS Service Quotas Comparison Tool.
"""
import json
from pathlib import Path
import streamlit as st
from src.utils.logger import logger

# Create a cache directory if it doesn't exist
CACHE_DIR = Path("quota_cache")
CACHE_DIR.mkdir(exist_ok=True)

def save_to_cache(data, cache_file):
    """Save data to cache file."""
    try:
        with open(cache_file, "w") as f:
            json.dump(data, f)
        logger.info(f"Cache file saved successfully: {cache_file}")
        return True
    except Exception as e:
        logger.error(f"Cache write error: {str(e)}")
        return False

def load_from_cache(cache_file):
    """Load data from cache file."""
    try:
        with open(cache_file, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Cache read error: {str(e)}")
        return None

def clear_cache():
    """Clear the quota cache."""
    try:
        logger.info("Clearing quota cache")
        cache_files = list(CACHE_DIR.glob("quotas_*.json"))
        logger.info(f"Found {len(cache_files)} cache files to delete")
        
        for file in cache_files:
            logger.debug(f"Deleting cache file: {file}")
            file.unlink()
            
        st.cache_data.clear()
        logger.info("Cache cleared successfully")
        st.success("Cache cleared successfully!")
        return True
    except Exception as e:
        error_msg = f"Error clearing cache: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        return False

def get_cache_info():
    """Get information about cached data."""
    cached_files = list(CACHE_DIR.glob("quotas_*.json"))
    logger.info(f"Found {len(cached_files)} cached quota files")
    
    cache_info = []
    if cached_files:
        for file in cached_files:
            name = file.stem.replace("quotas_", "")
            cache_info.append(name)
    
    return cache_info
