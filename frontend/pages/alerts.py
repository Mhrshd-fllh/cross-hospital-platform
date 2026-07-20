"""
Alerts page for the Cross-Hospital Generalization Platform.
Displays and manages system alerts and notifications.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Import services
from frontend.services.alert_service import AlertService

def create_alert_service():
    """Create an instance of the alert service."""
    return AlertService()

def get_severity_color(severity: str) -> str:
    """Get color for alert severity."""
    severity_colors = {
        "info": "blue",
        "warning": "orange",
        "error": "red",
        "critical": "darkred"
    }
    return severity_colors.get(severity.lower(), "gray")

def render_alerts_table(alerts):
    """Render alerts as a table"""
    # Convert to DataFrame for display
    df = pd.DataFrame([{
        "ID": alert.alert_id,
        "Timestamp": alert.timestamp,
        "Hospital": alert.hospital,
        "Type": alert.type,
        "Message": alert.message,
        "Severity": alert.severity,
        "Drift Score": getattr(alert, 'drift_score', '-'),
        "Acknowledged": alert.acknowledged,
        "Resolved": alert.resolved
    } for alert in alerts])

    # Configure column display
    column_config = {
        "Timestamp": st.column_config.DatetimeColumn(
            "Timestamp",
            format="MM/DD/YYYY HH:mm:ss"
        ),
        "Severity": st.column_config.TextColumn(
            "Severity",
            width="small"
        ),
        "Drift Score": st.column_config.TextColumn(
            "Drift Score",
            width="small"
        ),
        "Acknowledged": st.column_config.CheckboxColumn(
            "Acked",
            width="small"
        ),
        "Resolved": st.column_config.CheckboxColumn(
            "Resolved",
            width="small"
        )
    }

    # Display the dataframe
    event = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        on_select="rerun",
        selection_mode="single-row"
    )

    # Handle row selection for details
    # Note: Streamlit's dataframe selection handling is limited
    # We'll use a button approach instead
    return event

def render_alert_details(alert):
    """Render detailed view of a selected alert"""
    st.header(f"Alert Details: {alert.alert_id}")

    # Alert header with severity coloring
    severity_color = get_severity_color(alert.severity)

    st.markdown(f"""
    <div style="
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid {severity_color};
        background-color: rgba({int(severity_color[1:3], 16)}, {int(severity_color[3:5], 16)}, {int(severity_color[5:7], 16)}, 0.1);
        margin-bottom: 1.5rem;
    ">
        <h2 style="color: {severity_color}; margin-top: 0;">
            {alert.type} Alert
        </h2>
        <p><strong>Severity:</strong> <span style="color: {severity_color}; font-weight: bold;">{alert.severity.upper()}</span></p>
    </div>
    """, unsafe_allow_html=True)

    # Basic information
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Timestamp", alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        st.metric("Hospital", alert.hospital)

    with col2:
        st.metric("Alert ID", alert.alert_id)
        if hasattr(alert, 'drift_score') and alert.drift_score != 0:
            st.metric("Drift Score", f"{alert.drift_score:.3f}")

    with col3:
        status_text = []
        if alert.acknowledged:
            status_text.append("✅ Acknowledged")
        else:
            status_text.append("⏳ Pending Acknowledgment")

        if alert.resolved:
            status_text.append("✅ Resolved")
        else:
            status_text.append("⏳ Pending Resolution")

        st.markdown("<br>".join(status_text))

    st.markdown("---")

    # Alert message
    st.subheader("Alert Details")
    st.write(alert.message)

    # Webhook information (if available)
    # In a real implementation, we would have webhook details
    st.subheader("Notifications")
    st.info("Notification details would be shown here in a real implementation")

    # Action timeline
    st.subheader("Action Timeline")
    timeline_data = [
        {"timestamp": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "event": "Alert Generated"},
    ]

    # In a real implementation, we would have actual timestamps for these events
    if alert.acknowledged:
        # Simulate acknowledgment time (some time after generation)
        ack_time = alert.timestamp + timedelta(minutes=30)  # Placeholder
        timeline_data.append({"timestamp": ack_time.strftime("%Y-%m-%d %H:%M:%S"), "event": f"Acknowledged by {getattr(alert, 'acknowledged_by', 'Unknown'))"})

    if alert.resolved:
        # Simulate resolution time (some time after acknowledgment)
        resolve_time = alert.timestamp + timedelta(hours=2)  # Placeholder
        timeline_data.append({"timestamp": resolve_time.strftime("%Y-%m-%d %H:%M:%S"), "event": "Alert Resolved"})

    # Sort timeline by timestamp
    timeline_data.sort(key=lambda x: x["timestamp"])

    for item in timeline_data:
        st.text(f"• {item['timestamp']} - {item['event']}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if not alert.acknowledged:
            if st.button("✅ Acknowledge Alert", type="primary", use_container_width=True):
                # In reality, this would call the alert service to acknowledge
                st.success("Alert acknowledged!")
                # For demo, we'll just show the change - in reality would refresh from service
                st.experimental_rerun()
        else:
            if st.button("↩️ Unacknowledge Alert", use_container_width=True):
                st.info("Alert unacknowledged")
                st.experimental_rerun()

    with col2:
        if alert.acknowledged and not alert.resolved:
            if st.button("✅ Resolve Alert", type="primary", use_container_width=True):
                # In reality, this would call the alert service to resolve
                st.success("Alert resolved!")
                st.experimental_rerun()
        elif alert.resolved:
            if st.button("↩️ Reopen Alert", use_container_width=True):
                st.info("Alert reopened")
                st.experimental_rerun()
        else:
            st.info("Please acknowledge the alert first.")

    with col3:
        if st.button("📋 Copy Alert ID", use_container_width=True):
            st.info(f"Alert ID copied: {alert.alert_id}")
        if st.button("🔄 Refresh Alert", use_container_width=True):
            st.info("Refreshing alert...")
            st.experimental_rerun()

def alerts_page():
    """Main alerts page function"""
    # Header
    st.header("🚨 Alerts & Notifications")
    st.markdown("View and manage system alerts and notifications")

    # Create alert service
    alert_service = create_alert_service()

    # Check if we're viewing a specific alert or the list
    # Since we don't have a good way to get selected alert from dataframe,
    # we'll always show the list for now and note the limitation
    st.subheader("Active Alerts")
    st.markdown("Chronological list of system alerts requiring attention")

    # Get alerts data from service
    try:
        with st.spinner("Loading alerts..."):
            alerts = alert_service.get_alert_history(limit=50)  # Get recent alerts
    except Exception as e:
        st.error(f"Error loading alerts: {str(e)}")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Alerts", len(alerts))
    with col2:
        unresolved_count = sum(1 for alert in alerts if not alert.resolved)
        st.metric("Unresolved", unresolved_count)
    with col3:
        unacked_count = sum(1 for alert in alerts if not alert.acknowledged)
        st.metric("Unacknowledged", unacked_count)
    with col4:
        critical_count = sum(1 for alert in alerts if alert.severity.lower() == "critical" and not alert.resolved)
        st.metric("Critical Active", critical_count)

    st.markdown("---")

    # Filters and controls
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        severity_filter = st.multiselect(
            "Filter by Severity",
            options=["info", "warning", "critical", "error"],
            default=["info", "warning", "critical", "error"]
        )

    with col2:
        status_filter = st.multiselect(
            "Filter by Status",
            options=["All", "Unacknowledged", "Unresolved"],
            default=["All"]
        )

    with col3:
        # In a real implementation, we would get hospitals from the service
        hospital_options = list(set(alert.hospital for alert in alerts))
        hospital_filter = st.multiselect(
            "Filter by Hospital",
            options=hospital_options,
            default=hospital_options
        )

    with col4:
        if st.button("🔄 Refresh", use_container_width=True):
            st.experimental_rerun()

    # Apply filters
    filtered_alerts = alerts
    if severity_filter:
        filtered_alerts = [alert for alert in filtered_alerts if alert.severity.lower() in [s.lower() for s in severity_filter]]
    if hospital_filter:
        filtered_alerts = [alert for alert in filtered_alerts if alert.hospital in hospital_filter]

    # Status filtering
    if status_filter:
        if "Unacknowledged" in status_filter and "All" not in status_filter:
            filtered_alerts = [alert for alert in filtered_alerts if not alert.acknowledged]
        if "Unresolved" in status_filter and "All" not in status_filter:
            filtered_alerts = [alert for alert in filtered_alerts if not alert.resolved]

    st.markdown(f"**Showing {len(filtered_alerts)} of {len(alerts)} alerts**")

    st.markdown("---")

    # Render alerts table
    render_alerts_table(filtered_alerts)

    # TODO comments for future integration
    st.markdown("---")
    st.markdown("### 🔧 Future Integration Points")
    st.markdown("""
    - TODO: Connect to actual AlertService (replace mock)
    - TODO: Integrate with actual alerting system (PagerDuty, OpsGenie, etc.)
    - TODO: Implement real-time alert streaming (WebSocket)
    - TODO: Add alert silencing and suppression capabilities
    - TODO: Add alert routing based on severity and type
    - TODO: Add alert aggregation and deduplication
    - TODO: Add ability to add notes and comments to alerts
    - TODO: Add alert escalation policies
    - TODO: Integrate with on-call scheduling systems
    - TODO: Add alert analytics and trends
    - TODO: Add ability to create custom alert rules
    - TODO: Add selection handling for detailed alert views
    """)