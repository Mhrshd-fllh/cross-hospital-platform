"""
Main entry point for the Cross-Hospital Generalization Platform Frontend.
This Streamlit application provides a professional MLOps dashboard for monitoring
and interacting with the cross-hospital generalization platform.
"""

import streamlit as st
from components.sidebar import render_sidebar
from components.navbar import render_navbar

# Page imports
from pages.dashboard import render_dashboard
from pages.upload import render_upload
from pages.validation import render_validation
from pages.drift import render_drift
from pages.adaptation import render_adaptation
from pages.models import render_models
from pages.inference import render_inference
from pages.monitoring import render_monitoring
from pages.hospitals import render_hospitals
from pages.logs import render_logs
from pages.alerts import render_alerts
from pages.feedback import render_feedback
from pages.settings import render_settings

# Configure Streamlit page
st.set_page_config(
    page_title="Cross-Hospital Generalization Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourorg/chgp-help',
        'Report a bug': 'https://github.com/yourorg/chgp/issues',
        'About': "# Cross-Hospital Generalization Platform\nMLOps middleware for safe cross-hospital deployment of medical AI models."
    }
)

# Initialize session state for navigation if not present
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Render navbar
render_navbar()

# Render sidebar and get selected page
selected_page = render_sidebar()

# Update session state based on sidebar selection
if selected_page != st.session_state.current_page:
    st.session_state.current_page = selected_page

# Route to appropriate page based on selection
page_mapping = {
    "Dashboard": render_dashboard,
    "Upload Request": render_upload,
    "Validation": render_validation,
    "Drift Detection": render_drift,
    "Style Adaptation": render_adaptation,
    "Model Registry": render_models,
    "Production Inference": render_inference,
    "Monitoring": render_monitoring,
    "Hospitals": render_hospitals,
    "Logs": render_logs,
    "Alerts": render_alerts,
    "Feedback": render_feedback,
    "Settings": render_settings
}

# Get the render function for the selected page
render_function = page_mapping.get(st.session_state.current_page, render_dashboard)

# Render the selected page
render_function()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 1rem;'>"
    "Cross-Hospital Generalization Platform © 2026"
    "</div>",
    unsafe_allow_html=True
)