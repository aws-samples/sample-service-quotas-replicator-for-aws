"""
Sidebar components for the Streamlit interface.
"""
import streamlit as st
from src.utils.cache import clear_cache, get_cache_info
from src.utils.logger import logger

def render_sidebar():
    """Render the sidebar with cache controls and information."""
    with st.sidebar:
        st.title("Cache Control")
        if st.button("Clear Cache"):
            logger.info("User requested to clear cache")
            clear_cache()

        # Show cached profiles/regions
        st.write("### Cached Data:")
        cached_data = get_cache_info()
        if cached_data:
            for name in cached_data:
                st.text(f"✓ {name}")
        else:
            st.text("No cached data")
