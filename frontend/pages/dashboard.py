"""
Dashboard page for the Cross-Hospital Generalization Platform.
Displays an overview of system health, metrics, and recent activity.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Import services
from frontend.services.monitoring_service import MonitoringService
from frontend.services.alert_service import AlertService
from frontend.services.ingestion_service import IngestionService

def create_service_instances():
    """Create instances of the services."""
    monitoring_service = MonitoringService()
    alert_service = AlertService()
    ingestion_service = IngestionService()
    return monitoring_service, alert_service, ingestion_service

def render_metric_card(title, value, delta=None, delta_color="normal"):
    """
    Render a metric card component.

    Args:
        title (str): The title of the metric
        value: The value to display
        delta (str, optional): The delta value to display
        delta_color (str): Color of the delta ("normal", "inverse", "off")
    """
    st.metric(label=title, value=value, delta=delta, delta_color=delta_color)

def render_dashboard():
    """Render the dashboard page"""
    # Header
    st.header("📊 System Dashboard")
    st.markdown("Real-time overview of platform health and performance")

    # Create service instances
    monitoring_service, alert_service, ingestion_service = create_service_instances()

    # Get data from services
    try:
        dashboard_data = monitoring_service.get_dashboard_metrics()
        recent_alerts = alert_service.get_alert_history(limit=10)
        recent_requests = ingestion_service.get_recent_uploads(limit=10)
    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")
        # Fallback to empty data in case of service failure
        dashboard_data = {}
        recent_alerts = []
        recent_requests = []

    # Extract metrics from dashboard data with defaults
    requests_today = dashboard_data.get("requests_today", 0)
    drift_alerts = dashboard_data.get("drift_alerts", 0)
    active_hospitals = dashboard_data.get("active_hospitals", 0)
    registered_models = dashboard_data.get("registered_models", 0)
    avg_latency = dashboard_data.get("avg_latency", 0)
    avg_drift_score = dashboard_data.get("avg_drift_score", 0)
    gpu_usage = dashboard_data.get("gpu_usage", 0)
    cpu_usage = dashboard_data.get("cpu_usage", 0)
    saved_accuracy = dashboard_data.get("saved_accuracy", 0)
    avg_f1 = dashboard_data.get("avg_f1", 0)
    avg_ece = dashboard_data.get("avg_ece", 0)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card("Requests Today", f"{requests_today:,}")
        render_metric_card("Drift Alerts", drift_alerts,
                          delta=f"{drift_alerts} today" if drift_alerts > 0 else "0 today",
                          delta_color="inverse" if drift_alerts > 0 else "normal")

    with col2:
        render_metric_card("Active Hospitals", active_hospitals)
        render_metric_card("Registered Models", registered_models)

    with col3:
        render_metric_card("Avg Latency", f"{avg_latency} ms")
        render_metric_card("Avg Drift Score", f"{avg_drift_score:.3f}")

    with col4:
        render_metric_card("GPU Usage", f"{gpu_usage}%",
                          delta=f"{gpu_usage}%" if gpu_usage > 70 else None,
                          delta_color="inverse" if gpu_usage > 70 else "normal")
        render_metric_card("CPU Usage", f"{cpu_usage}%",
                          delta=f"{cpu_usage}%" if cpu_usage > 80 else None,
                          delta_color="inverse" if cpu_usage > 80 else "normal")

    # Second row of metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card("Saved Accuracy", f"+{saved_accuracy*100:.1f}%")

    with col2:
        render_metric_card("Avg F1 Score", f"{avg_f1:.3f}")

    with col3:
        render_metric_card("Avg ECE", f"{avg_ece:.3f}")

    with col4:
        # System uptime placeholder
        st.metric("System Uptime", "99.9%")

    st.markdown("---")

    # Charts section
    st.subheader("📈 System Analytics")

    # First row of charts
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Prediction Distribution**")
        # Try to get prediction distribution from monitoring service
        try:
            prediction_dist = monitoring_service.get_prediction_distribution()
            if prediction_dist:
                fig = px.pie(
                    values=list(prediction_dist.values()),
                    names=list(prediction_dist.keys()),
                    title="Distribution of Predictions"
                )
            else:
                # Fallback to empty chart if no data
                fig = px.pie(values=[0], names=["No Data"], title="Distribution of Predictions")
        except Exception:
            fig = px.pie(values=[0], names=["No Data"], title="Distribution of Predictions")

        fig.update_layout(showlegend=True, height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**Hospital Status**")
        # Try to get hospital status from monitoring service
        try:
            hospital_status = monitoring_service.get_hospital_status()
            if hospital_status:
                hospital_data = pd.DataFrame(hospital_status)
                fig = px.bar(
                    hospital_data,
                    x="hospital",
                    y="avg_drift_score",
                    color="status",
                    color_discrete_map={"healthy": "green", "degraded": "orange", "offline": "red"},
                    title="Average Drift Score by Hospital"
                )
                fig.update_layout(xaxis_title="Hospital", yaxis_title="Avg Drift Score", showlegend=True, height=300)
            else:
                # Fallback to empty chart
                fig = px.bar(x=[], y=[], title="Average Drift Score by Hospital")
        except Exception:
            fig = px.bar(x=[], y=[], title="Average Drift Score by Hospital")

        fig.update_layout(showlegend=True, height=300)
        st.plotly_chart(fig, use_container_width=True)

    # Second row of charts
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Pipeline Health**")
        # Try to get pipeline health from monitoring service
        try:
            pipeline_health = monitoring_service.get_pipeline_health()
            if pipeline_health:
                pipeline_data = pd.DataFrame(pipeline_health)
                fig = px.bar(
                    pipeline_data,
                    x="stage",
                    y="success_rate",
                    color="status",
                    color_discrete_map={"healthy": "green", "degraded": "orange", "error": "red"},
                    title="Pipeline Stage Success Rates"
                )
                fig.update_layout(xaxis_title="Stage", yaxis_title="Success Rate", showlegend=True, height=300)
            else:
                # Fallback to empty chart
                fig = px.bar(x=[], y=[], title="Pipeline Stage Success Rates")
        except Exception:
            fig = px.bar(x=[], y=[], title="Pipeline Stage Success Rates")

        fig.update_layout(showlegend=True, height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("**System Health Indicators**")
        # Create a simple gauge-like visualization
        try:
            system_health = monitoring_service.get_system_health()
            cpu_usage = system_health.get("cpu_usage", 0) if isinstance(system_health, dict) else 0
            gpu_usage = system_health.get("gpu_usage", 0) if isinstance(system_health, dict) else 0
            drift_score = system_health.get("drift_score", 0) if isinstance(system_health, dict) else 0
        except Exception:
            cpu_usage, gpu_usage, drift_score = 0, 0, 0

        fig = go.Figure()

        # Add gauge traces for CPU, GPU, Memory
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=cpu_usage,
            title={'text': "CPU Usage (%)"},
            domain={'row': 0, 'column': 0},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))

        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=gpu_usage,
            title={'text': "GPU Usage (%)"},
            domain={'row': 0, 'column': 1},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 70], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 85
                }
            }
        ))

        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=drift_score * 100,  # Convert to percentage
            title={'text': "Avg Drift Score (%)"},
            domain={'row': 1, 'column': 0},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkred"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgreen"},
                    {'range': [30, 70], 'color': "yellow"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))

        fig.update_layout(grid={'rows': 2, 'columns': 2, 'pattern': "independent"}, height=350)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Recent activity section
    st.subheader("🕒 Recent Activity")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Recent Requests**")
        if recent_requests:
            # Convert to DataFrame for display
            requests_data = []
            for req in recent_requests:
                requests_data.append({
                    "Request ID": getattr(req, 'request_id', 'N/A'),
                    "Hospital": getattr(req, 'hospital', 'N/A'),
                    "Timestamp": getattr(req, 'timestamp', 'N/A').strftime("%Y-%m-%d %H:%M") if hasattr(getattr(req, 'timestamp', None), 'strftime') else str(getattr(req, 'timestamp', 'N/A')),
                    "Modality": getattr(req, 'modality', 'N/A'),
                    "Prediction": getattr(req, 'prediction', 'N/A'),
                    "Status": getattr(req, 'status', 'N/A'),
                    "Drift Score": getattr(req, 'drift_score', 0)
                })
            recent_requests_df = pd.DataFrame(requests_data)

            # Style the dataframe to show status with colors
            st.dataframe(
                recent_requests_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Status": st.column_config.TextColumn(
                        "Status",
                        help": Request processing status"
                    ),
                    "Drift Score": st.column_config.NumberColumn(
                        "Drift Score",
                        help": Domain drift score",
                        format="%.3f"
                    )
                }
            )
        else:
            st.info("No recent requests available")

    with col2:
        st.write("**Recent Alerts**")
        if recent_alerts:
            # Convert to DataFrame for display
            alerts_data = []
            for alert in recent_alerts:
                alerts_data.append({
                    "Timestamp": getattr(alert, 'timestamp', 'N/A').strftime("%Y-%m-%d %H:%M") if hasattr(getattr(alert, 'timestamp', None), 'strftime') else str(getattr(alert, 'timestamp', 'N/A')),
                    "Hospital": getattr(alert, 'hospital', 'N/A'),
                    "Message": getattr(alert, 'message', 'N/A'),
                    "Severity": getattr(alert, 'severity', 'N/A'),
                    "Drift Score": getattr(alert, 'drift_score', 0)
                })
            recent_alerts_df = pd.DataFrame(alerts_data)

            # Style the dataframe to show severity with colors
            st.dataframe(
                recent_alerts_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Severity": st.column_config.TextColumn(
                        "Severity",
                        help": Alert severity level"
                    ),
                    "Drift Score": st.column_config.NumberColumn(
                        "Drift Score",
                        help": Associated drift score",
                        format="%.3f"
                    )
                }
            )
        else:
            st.info("No recent alerts available")

    # TODO comments for future integration
    st.markdown("---")
    st.markdown("### 🔧 Future Integration Points")
    st.markdown("""
    - TODO: Add auto-refresh capability (every 30 seconds)
    - TODO: Add customizable time range selectors
    - TODO: Add drill-down capabilities for metrics
    - TODO: Add export functionality for reports
    """)

if __name__ == "__main__":
    render_dashboard()