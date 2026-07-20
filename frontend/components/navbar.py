"""
Navbar component for the Cross-Hospital Generalization Platform.
Displays the application title and user info.
"""

import streamlit as st

def render_navbar():
    """
    Render the navigation bar at the top of the application.
    """
    # Create a container for the navbar
    with st.container():
        # Use columns to create a layout with title and user info
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.markdown("# Cross-Hospital Generalization Platform")
            st.markdown("<small>MLOps Platform for Safe Medical AI Deployment</small>",
                       unsafe_allow_html=True)

        with col2:
            # Hospital selector (placeholder for future implementation)
            st.selectbox(
                "Hospital",
                options=["All Hospitals", "Hospital A", "Hospital B", "Hospital C"],
                label_visibility="collapsed"
            )

        with col3:
            # User info placeholder
            st.markdown("<div style='text-align: right;'>"
                       "<small>User: Admin</small><br>"
                       "<small>Role: Administrator</small>"
                       "</div>", unsafe_allow_html=True)

    # Add a divider
    st.markdown("<hr style='margin: 1rem 0; border-color: #eee;'>",
                unsafe_allow_html=True)