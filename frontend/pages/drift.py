"""
Drift detection page for the Cross-Hospital Generalization Platform.
Displays drift detection results and visualizations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# Import services
from frontend.services.drift_service import DriftService

def create_drift_service():
    """Create an instance of the drift service."""
    return DriftService()

def get_status_color(status: str) -> str:
    """Get color for drift status."""
    status_colors = {
        "Low": "green",
        "Medium": "orange",
        "High": "orangered",
        "Critical": "red"
    }
    return status_colors.get(status, "gray")

def render_drift_metrics(drift_result):
    """Render drift metrics cards."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Drift Score",
            value=f"{drift_result.drift_score:.3f}",
            delta=None
        )

    with col2:
        status_color = get_status_color(drift_result.status)
        st.markdown(f"""
        <div style="
            padding: 0.5rem;
            border-radius: 0.5rem;
            text-align: center;
            background-color: {status_color}20;
            border-left: 4px solid {status_color};
        ">
            <h4 style="color: {status_color}; margin: 0;">{drift_result.status}</h4>
            <p style="margin: 0; font-size: 0.9rem;">Drift Level</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.metric(
            label="Statistical Significance",
            value=f"{drift_result.p_value:.4f}",
            delta="Significant" if drift_result.p_value < 0.05 else "Not Significant"
        )

    with col4:
        st.metric(
            label="Metric Used",
            value=drift_result.metric_used.split('(')[0].strip(),
            delta=drift_result.metric_used.split('(')[1].rstrip(')') if '(' in drift_result.metric_used else ""
        )

def render_drift_trend_chart(drift_result):
    """Render drift trend chart."""
    # In a real implementation, we would get historical data from the service
    # For now, we'll generate some sample historical data

    # Generate historical drift scores (last 30 days)
    dates = [datetime.now() - timedelta(days=x) for x in range(30, 0, -1)]
    # Simulate some variation with occasional spikes
    base_drift = drift_result.drift_score * 0.8  # Use current as baseline
    drift_scores = []

    for i, date in enumerate(dates):
        # Add some noise and occasional spikes
        noise = (np.random.random() - 0.5) * 0.1
        spike = 0.3 if (i % 7 == 0 and i > 0) else 0  # Weekly spike
        drift = max(0, min(1, base_drift + noise + spike))
        drift_scores.append(round(drift, 3))

    # Ensure the last value matches current drift
    drift_scores[-1] = round(drift_result.drift_score, 3)

    # Create DataFrame
    df = pd.DataFrame({
        'Date': dates,
        'Drift Score': drift_scores
    })

    # Create the line chart
    fig = px.line(
        df,
        x='Date',
        y='Drift Score',
        title='Drift Score Trend (Last 30 Days)',
        labels={'Drift Score': 'Drift Score (MMD)', 'Date': 'Date'}
    )

    # Add threshold lines
    fig.add_hline(y=0.3, line_dash="dash", line_color="orange",
                  annotation_text="Medium Threshold", annotation_position="bottom right")
    fig.add_hline(y=0.6, line_dash="dash", line_color="orangered",
                  annotation_text="High Threshold", annotation_position="bottom right")
    fig.add_hline(y=0.8, line_dash="dash", line_color="red",
                  annotation_text="Critical Threshold", annotation_position="bottom right")

    # Update layout
    fig.update_layout(
        hovermode="x unified",
        showlegend=False,
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

def render_feature_drift_chart(drift_result):
    """Render feature-level drift chart."""
    # Prepare data for bar chart
    features = list(drift_result.feature_drift.keys())
    drift_values = list(drift_result.feature_drift.values())

    # Create DataFrame
    df = pd.DataFrame({
        'Feature': features,
        'Drift Score': drift_values
    })

    # Create bar chart
    fig = px.bar(
        df,
        x='Feature',
        y='Drift Score',
        title='Feature-Level Drift Analysis',
        color='Drift Score',
        color_continuous_scale='RdYlGn_r',  # Red-Yellow-Green reversed (red'
        range_color=[0, 1]
    )

    # Add threshold lines
    fig.add_hline(y=0.3, line_dash="dash", line_color="orange",
                  annotation_text="Medium Threshold")
    fig.add_hline(y=0.6, line_dash="dash", line_color="orangered",
                  annotation_text="High Threshold")

    # Update layout
    fig.update_layout(
        showlegend=False,
        height=400,
        xaxis_tickangle=-45
    )

    st.plotly_chart(fig, use_container_width=True)

def render_distribution_comparison(drift_result):
    """Render distribution comparison visualization."""
    # Create sample data for visualization
    # In a real implementation, this would come from the drift result

    # Generate sample distributions
    np.random.seed(42)  # For consistent visualization
    reference_data = np.random.normal(0, 1, 1000)
    # Shift the distribution to show difference
    current_data = np.random.normal(drift_result.drift_score * 2, 1, 1000)

    # Create histogram data
    hist_range = (-4, 4)
    bins = 30

    ref_counts, bin_edges = np.histogram(reference_data, bins=bins, range=hist_range, density=True)
    curr_counts, _ = np.histogram(current_data, bins=bins, range=hist_range, density=True)

    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # Create the figure
    fig = go.Figure()

    # Add reference distribution
    fig.add_trace(go.Scatter(
        x=bin_centers,
        y=ref_counts,
        mode='lines',
        name='Reference Distribution',
        line=dict(color='blue', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 100, 255, 0.2)'
    ))

    # Add current distribution
    fig.add_trace(go.Scatter(
        x=bin_centers,
        y=curr_counts,
        mode='lines',
        name='Current Distribution',
        line=dict(color='red', width=2),
        fill='tozeroy',
        fillcolor='rgba(255, 50, 50, 0.2)'
    ))

    # Update layout
    fig.update_layout(
        title='Distribution Comparison: Reference vs Current',
        xaxis_title='Feature Value',
        yaxis_title='Density',
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

def render_drift_explanation(drift_result):
    """Render drift explanation and interpretation."""
    st.subheader("Drift Interpretation")

    drift_score = drift_result.drift_score
    status = drift_result.status
    p_value = drift_result.p_value

    # Provide explanation based on drift level
    if status == "Low":
        st.info("""
        **Low Drift Detected**: The input data shows minimal deviation from the training distribution.
        The model should perform reliably without requiring significant adaptation.
        """)
    elif status == "Medium":
        st.warning("""
        **Moderate Drift Detected**: There is a noticeable difference between input data and training distribution.
        Consider reviewing model performance, though adaptation may not be strictly necessary.
        """)
    elif status == "High":
        st.error("""
        **High Drift Detected**: Significant difference detected between input data and training distribution.
        Model performance may be degraded. Style adaptation is strongly recommended.
        """)
    else:  # Critical
        st.error("""
        **Critical Drift Detected**: Substantial difference between input data and training distribution.
        Model predictions may be unreliable. Style adaptation is required before proceeding.
        """)

    # Statistical interpretation
    st.markdown("### Statistical Significance")
    if p_value < 0.01:
        st.success(f"The drift is statistically significant (p = {p_value:.4f} < 0.01)")
    elif p_value < 0.05:
        st.warning(f"The drift is statistically significant (p = {p_value:.4f} < 0.05)")
    else:
        st.info(f"The drift is not statistically significant (p = {p_value:.4f} ≥ 0.05)")

    # Technical details
    with st.expander("Technical Details"):
        st.json({
            "request_id": drift_result.request_id,
            "timestamp": drift_result.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "reference_population": drift_result.reference_hospital,
            "target_population": drift_result.target_hospital,
            "drift_metric": drift_result.metric_used,
            "metric_value": drift_result.metric_value,
            "drift_score": drift_result.drift_score,
            "p_value": drift_result.p_value,
            "interpretation": f"Drift score of {drift_result.drift_score:.3f} indicates {drift_result.status.lower()} drift"
        })

def render_drift_controls():
    """Render drift detection controls."""
    st.subheader("Analysis Controls")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Reference hospital selector
        reference_options = ["CheXpert (Training)", "MIMIC-CXR", "NIH ChestX-ray", "Custom Baseline"]
        st.selectbox(
            "Reference Population",
            options=reference_options,
            index=0,
            help="Select the reference population for drift comparison"
        )

    with col2:
        # Target hospital selector
        target_options = ["General Hospital", "City Medical Center", "University Hospital", "Children's Hospital", "All Hospitals"]
        st.selectbox(
            "Target Population",
            options=target_options,
            index=0,
            help="Select the target hospital/population being evaluated"
        )

    with col3:
        # Time range selector
        time_options = ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"]
        st.selectbox(
            "Time Range",
            options=time_options,
            index=2,
            help="Select the time range for historical drift analysis"
        )

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("🔄 Re-run Analysis", use_container_width=True):
            # Re-run drift detection
            st.rerun()

    with col2:
        if st.button("📊 Export Report", use_container_width=True):
            st.info("Export functionality would be implemented here")

def drift_detection_page():
    """Main drift detection page function."""
    # Header
    st.header("📈 Drift Detection")
    st.markdown("Monitor and analyze data distribution shifts between training and incoming data")

    # Get request ID from session state (should be set from upload/validation pages)
    if 'current_request_id' not in st.session_state:
        st.warning("No request ID found. Please upload and validate an image first.")
        if st.button("Go to Upload Page"):
            st.switch_page("upload.py")
        return

    request_id = st.session_state.current_request_id

    # Create drift service
    drift_service = create_drift_service()

    # Get drift results from service
    try:
        with st.spinner("Analyzing data drift..."):
            drift_result = drift_service.detect_drift(request_id)
    except Exception as e:
        st.error(f"Error running drift analysis: {str(e)}")
        return

    # Display drift metrics
    st.subheader("Current Drift Assessment")
    render_drift_metrics(drift_result)

    # Add some spacing
    st.markdown("<br>", unsafe_allow_html=True)

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Trend Analysis", "🔬 Feature Analysis", "📊 Distribution Comparison", "📋 Details"])

    with tab1:
        render_drift_trend_chart(drift_result)

    with tab2:
        render_feature_drift_chart(drift_result)

    with tab3:
        render_distribution_comparison(drift_result)

    with tab4:
        render_drift_explanation(drift_result)

    # Controls section
    st.markdown("<br>", unsafe_allow_html=True)
    render_drift_controls()

    # TODO comments for future integration
    st.markdown("---")
    st.markdown("### 🔧 Future Integration Points")
    st.markdown("""
    - TODO: Connect to actual DriftService (replace mock)
    - TODO: Integrate with actual Alibi Detect drift detection models
    - TODO: Show real-time drift monitoring (live updates)
    - TODO: Allow manual triggering of drift analysis for specific time periods
    - TODO: Store drift results in database for longitudinal tracking
    - TODO: Add ability to upload reference datasets for custom baseline
    - TODO: Integrate with alerting system to notify when drift thresholds are exceeded
    - TODO: Provide detailed feature importance and contribution analysis
    """)