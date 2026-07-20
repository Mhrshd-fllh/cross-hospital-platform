"""
Sidebar component for the Cross-Hospital Generalization Platform.
Provides navigation to all sections of the application.
"""

import streamlit as st

def render_sidebar():
    """
    Render the sidebar navigation and return the selected page.

    Returns:
        str: The name of the selected page
    """
    with st.sidebar:
        st.markdown("# 🏥 CHGP Platform")
        st.markdown("---")

        # Navigation menu
        st.markdown("## Navigation")

        # Main sections
        if st.button("📊 Dashboard", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == "Dashboard" else "secondary"):
            st.session_state.current_page = "Dashboard"
            st.rerun()

        st.markdown("### Inference Pipeline")
        if st.button("📤 Upload Request", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == "Upload Request" else "secondary"):
            st.session_state.current_page = "Upload Request"
            st.rerun()

        if st.button("🔍 Validation", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == "Validation" else "secondary"):
            st.session_state.current_page = "Validation"
            st.rerun()

        if st.button("📈 Drift Detection", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == "Drift Detection" else "secondary"):
            st.session_state.current_page = "Drift Detection"
            st.rerun()

        if st.button("🎨 Style Adaptation", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == "Style Adaptation" else "secondary"):
            st.session_state.current_page = "Style Adaptation"
            st.rerun()

        if st.button("📦 Model Registry", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == "Model Registry" else "secondary"):
            st.session_state.current_page = "Model Registry"
            st.rerun()

        if st.button("🚀 Production Inference", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == "Production Inference" else "secondary"):
            st.session_state.current_page = "Production Inference"
            st.rerun()

        st.markdown("### Monitoring")
        if st.button("📊 Monitoring", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == "Monitoring" else "secondary"):
            st.session_state.current_page = "Monitoring"
            st.rerun()

        st.markdown("### Management")
        if st.button("🏥 Hospitals", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == "Hospitals" else "secondary"):
            st.session_state.current_page = "Hospitals"
            st.rerun()

        if st.button("📋 Logs", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == "Logs" else "secondary"):
            st.session_state.current_page = "Logs"
            st.rerun()

        if st.button("🚨 Alerts", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == "Alerts" else "secondary"):
            st.session_state.current_page = "Alerts"
            st.rerun()

        if st.button("💬 Feedback", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == "Feedback" else "secondary"):
            st.session_state.current_page = "Feedback"
            st.rerun()

        if st.button("⚙️ Settings", use_container_width=True,
                    type="primary" if st.session_state.get('current_page') == "Settings" else "secondary"):
            st.session_state.current_page = "Settings"
            st.rerun()

        st.markdown("---")

        # System status indicator
        st.markdown("### System Status")
        st.markdown("<span style='color: green;'>●</span> System Online", unsafe_allow_html=True)

        # Version info
        st.markdown("<small>v1.0.0</small>", unsafe_allow_html=True)

    return st.session_state.get('current_page', "Dashboard")