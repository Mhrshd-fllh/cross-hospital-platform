"""
Hospitals page for the Cross-Hospital Generalization Platform.
Displays hospital information, statistics, and management capabilities.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import services
from frontend.services.hospital_service import HospitalService

def create_hospital_service():
    """Create an instance of the hospital service."""
    return HospitalService()

def get_status_badge(status: str) -> str:
    """Generate HTML for status badge."""
    status_lower = status.lower()
    if status_lower == "online":
        return '''
        <span style="
            background-color: #28a745;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        ">ONLINE</span>
        '''
    elif status_lower == "offline":
        return '''
        <span style="
            background-color: #dc3545;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        ">OFFLINE</span>
        '''
    else:
        return '''
        <span style="
            background-color: #ffc107;
            color: #212529;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        ">UNKNOWN</span>
        '''

def render_hospitals_table(hospitals):
    """Render hospitals as a table"""
    # Convert to DataFrame for display
    df = pd.DataFrame([{
        "Hospital ID": hospital.hospital_id,
        "Name": hospital.name,
        "Status": hospital.status,
        "Avg Drift": f"{hospital.avg_drift:.3f}",
        "Images Processed": f"{hospital.images_processed:,}",
        "Models Used": hospital.models_used,
        "Last Activity": hospital.last_activity.strftime("%Y-%m-%d %H:%M"),
        "Health Score": f"{hospital.health_score:.2f}"
    } for hospital in hospitals])

    # Configure column display
    column_config = {
        "Status": st.column_config.TextColumn(
            "Status",
            width="small"
        ),
        "Avg Drift": st.column_config.NumberColumn(
            "Avg Drift",
            format="%.3f"
        ),
        "Health Score": st.column_config.NumberColumn(
            "Health Score",
            format="%.2f"
        ),
        "Last Activity": st.column_config.DatetimeColumn(
            "Last Activity",
            format="MM/DD/YYYY HH:mm"
        )
    }

    # Display the dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )

def render_hospital_details(hospital):
    """Render detailed view of a hospital"""
    st.header(f"Hospital Details: {hospital.name}")

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status_badge_html = get_status_badge(hospital.status)
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; border-radius: 0.5rem;">
            {status_badge_html}
            <div style="font-size: 0.9rem; margin-top: 0.5rem;">Status</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.metric("Images Processed", f"{hospital.images_processed:,}")

    with col3:
        st.metric("Models Used", hospital.models_used)

    with col4:
        st.metric("Last Activity", hospital.last_activity.strftime("%m/%d %H:%M"))

    st.markdown("---")

    # Additional information
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Location & Contact")
        # In a real implementation, we would have this data
        st.text("Location: Not available in mock data")
        st.text("Contact: Not available in mock data")
        st.text("Specialties: Not available in mock data")

        st.subheader("Health Metrics")
        st.metric("Average Drift Score", f"{hospital.avg_drift:.3f}")
        st.metric("Health Score", f"{hospital.health_score:.2f}")

    with col2:
        st.subheader("Model Usage")
        # In a real implementation, we would have this data
        st.text("Model usage data not available in mock implementation")

        st.subheader("Activity Chart")
        # Placeholder for activity chart
        st.info("Activity chart would be displayed here in a full implementation")

    st.markdown("---")

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("📊 View Reports", use_container_width=True):
            st.info("Hospital reports functionality would be implemented here")

    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.info("Refreshing hospital data...")
            st.experimental_rerun()

    with col3:
        # Status change buttons (for demo)
        current_status = hospital.status.lower()
        if current_status == "online":
            if st.button("🔴 Set Offline", use_container_width=True):
                # In a real implementation, we would call the service
                st.success("Hospital status updated to offline!")
                st.experimental_rerun()
        else:
            if st.button("🟢 Set Online", use_container_width=True):
                # In a real implementation, we would call the service
                st.success("Hospital status updated to online!")
                st.experimental_rerun()

def hospitals_page():
    """Main hospitals page function"""
    # Header
    st.header("🏥 Hospitals")
    st.markdown("Manage and monitor connected healthcare facilities")

    # Create hospital service
    hospital_service = create_hospital_service()

    # Get hospitals data from service
    try:
        with st.spinner("Loading hospital data..."):
            hospitals = hospital_service.get_hospitals()
    except Exception as e:
        st.error(f"Error loading hospital data: {str(e)}")
        return

    # Tabs for different views
    tab1, tab2 = st.tabs(["🏥 Hospital List", "📊 Hospital Details"])

    with tab1:
        st.subheader("Hospital Directory")
        st.markdown("Overview of all healthcare facilities connected to the CHGP platform")

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1):
            st.metric("Total Hospitals", len(hospitals))
        with col2:
            online_count = sum(1 for h in hospitals if h.status.lower() == "online")
            st.metric("Online Hospitals", online_count)
        with col3:
            total_images = sum(h.images_processed for h in hospitals)
            st.metric("Total Images Processed", f"{total_images:,}")
        with col4:
            avg_health = sum(h.health_score for h in hospitals) / len(hospitals) if hospitals else 0
            st.metric("Average Health Score", f"{avg_health:.2f}")

        st.markdown("---")

        # Render hospitals table
        render_hospitals_table(hospitals)

        # Allow selecting a hospital to view details
        selected_idx = st.selectbox(
            "Select a hospital to view details:",
            options=range(len(hospitals)),
            format_func=lambda i: f"{hospitals[i].name} ({hospitals[i].hospital_id})"
        )

        if st.button("View Hospital Details"):
            st.session_state.selected_hospital = hospitals[selected_idx]
            st.experimental_rerun()

    with tab2:
        # Show selected hospital details or prompt to select one
        if 'selected_hospital' in st.session_state:
            hospital = st.session_state.selected_hospital
            render_hospital_details(hospital)

            if st.button("← Back to Hospital List"):
                del st.session_state.selected_hospital
                st.experimental_rerun()
        else:
            st.info("Please select a hospital from the list to view detailed information.")

    # TODO comments for future integration
    st.markdown("---")
    st.markdown("### 🔧 Future Integration Points")
    st.markdown("""
    - TODO: Connect to actual HospitalService (replace mock)
    - TODO: Integrate with actual hospital management system
    - TODO: Allow adding/editing/removing hospitals (with appropriate permissions)
    - TODO: Show real-time status of hospital connections
    - TODO: Integrate with authentication/authorization for hospital-specific access
    - TODO: Provide hospital-specific API keys or tokens
    - TODO: Show detailed audit logs for each hospital
    - TODO: Allow configuration of hospital-specific settings (alert thresholds per hospital)
    - TODO: Show federated learning participation status (if applicable)
    - TODO: Add ability to view historical performance and trends
    """)