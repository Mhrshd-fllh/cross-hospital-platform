"""
Style adaptation page for the Cross-Hospital Generalization Platform.
Displays image style adaptation process and results.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# Import services
from frontend.services.adaptation_service import AdaptationService
from frontend.services.drift_service import DriftService

def create_services():
    """Create instances of the services."""
    adaptation_service = AdaptationService()
    drift_service = DriftService()
    return adaptation_service, drift_service

def get_status_color(status: str) -> str:
    """Get color for adaptation step status."""
    status_colors = {
        "complete": "green",
        "processing": "blue",
        "pending": "gray",
        "error": "red",
        "skipped": "gray"
    }
    return status_colors.get(status, "gray")

def render_adaptation_step(step):
    """Render a single adaptation step"""
    # Determine status styling
    status_icon = "✅" if step["status"] == "complete" else "🔄" if step["status"] == "processing" else "⏳" if step["status"] == "pending" else "❌"
    status_color = get_status_color(step["status"])

    # Create step container
    with st.container():
        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])

        with col1:
            st.markdown(f"<div style='text-align: center;'>{status_icon}</div>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"**{step['step']}**")
            st.caption(step["description"])

        with col3:
            if step["execution_time"] > 0:
                st.markdown(f"<span style='color: {status_color};'>{step['execution_time']}s</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span>-</span>", unsafe_allow_html=True)

        with col4:
            with st.expander("Details"):
                st.write(step["details"])

        st.markdown("<br>", unsafe_allow_html=True)

def render_image_comparison():
    """Render image comparison placeholder"""
    st.subheader("Image Adaptation Results Visualization")

    # Create three columns for original, adapted, and difference
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Original Image")
        st.info("📄 Original Image\n(DICOM/JPG)")
        st.caption("Input from hospital")

    with col2:
        st.markdown("#### Adapted Image")
        st.info("🎨 Adapted Image")
        st.caption("Style normalized")

    with col3:
        st.markdown("#### Difference Map")
        st.info("📊 Difference Map")
        st.caption("|Original - Adapted|")

    # Add explanation
    st.markdown("""
    *The difference map shows the pixel-by-pixel-by-pixel absolute difference between original and adapted images. Brighter areas indicate larger changes made
    during the style adaptation process.*
    """)

def render_adaptation_metrics(adaptation_result):
    """Render adaptation quality metrics"""
    st.subheader("Adaptation Quality Metrics")

    metrics = adaptation_result.quality_metrics

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        psnr = metrics["peak_signal_to_noise_ratio"]
        # Higher PSNR is better
        psnr_color = "green" if psnr > 30 else "orange" if psnr > 25 else "red"
        st.metric(
            label="PSNR",
            value=f"{psnr:.1f} dB",
            help="Peak Signal-to-Noise Ratio (higher = better quality)"
        )
        st.markdown(f"<small style='color: {psnr_color}'>●</small>", unsafe_allow_html=True)

    with col2:
        ssim = metrics["structural_similarity_index"]
        # Higher SSIM is better
        ssim_color = "green" if ssim > 0.9 else "orange" if ssim > 0.8 else "red"
        st.metric(
            label="SSIM",
            value=f"{ssim:.3f}",
            help="Structural Similarity Index (higher = better similarity)"
        )
        st.markdown(f"<small style='color: {ssim_color}'>●</small>", unsafe_allow_html=True)

    with col3:
        mse = metrics["mean_squared_error"]
        # Lower MSE is better
        mse_color = "green" if mse < 0.005 else "orange" if mse < 0.01 else "red"
        st.metric(
            label="MSE",
            value=f"{mse:.4f}",
            help="Mean Squared Error (lower = better)"
        )
        st.markdown(f"<small style='color: {mse_color}'>●</small>", unsafe_allow_html=True)

    with col4:
        aps = metrics["anatomical_preservation_score"]
        # Custom metric - should be high
        aps_color = "green" if aps > 0.95 else "orange" if aps > 0.9 else "red"
        st.metric(
            label="Anatomy Preservation",
            value=f"{aps:.3f}",
            help="Custom score measuring anatomical feature preservation"
        )
        st.markdown(f"<small style='color: {aps_color}'>●</small>", unsafe_allow_html=True)

def render_adaptation_timeline(adaptation_result):
    """Render adaptation process timeline"""
    st.subheader("Adaptation Process Timeline")

    steps = adaptation_result.adaptation_steps
    total_time = adaptation_result.total_execution_time

    # Prepare data for timeline chart
    chart_data = []
    for i, step in enumerate(steps):
        if step["execution_time"] > 0:  # Only show steps with actual processing time
            chart_data.append({
                "step": step["step"],
                "execution_time": step["execution_time"],
                "status": step["status"]
            })

    if not chart_data:
        st.info("No processing steps with measurable execution time.")
        return

    # Create DataFrame
    df = pd.DataFrame(chart_data)

    # Create horizontal bar chart
    fig = go.Figure()

    # Add bars for each step
    for i, row in df.iterrows():
        color = "green" if row["status"] == "complete" else "orange" if row["status"] == "processing" else "gray"
        fig.add_trace(go.Bar(
            x=[row["execution_time"]],
            y=[row["step"]],
            orientation='h',
            name=row["step"],
            text=f"{row['execution_time']}s",
            textposition='auto',
            marker_color=color
        ))

    fig.update_layout(
        title=f"Adaptation Execution Time (Total: {total_time}s)",
        xaxis_title="Execution Time (seconds)",
        yaxis_title="Adaptation Step",
        showlegend=False,
        height=max(300, len(chart_data) * 40),  # Dynamic height based on number of steps
        barmode='stack'
    )

    st.plotly_chart(fig, use_container_width=True)

def render_adaptation_controls():
    """Render adaptation controls"""
    st.subheader("Adaptation Controls")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Adaptation strength/slider
        st.slider(
            "Adaptation Strength",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Control how strongly to adapt the image style (0 = none, 1 = full adaptation)"
        )

    with col2:
        # Preset options
        st.selectbox(
            "Adaptation Preset",
            options=["Conservative", "Moderate", "Aggressive", "Custom"],
            index=1,
            help="Predefined adaptation strength settings"
        )

    with col3:
        # Anatomical preservation priority
        st.checkbox(
            "Prioritize Anatomical Preservation",
            value=True,
            help="When checked, adaptation will prioritize preserving anatomical features over style matching"
        )

    # Action buttons
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🔄 Re-run Adaptation", use_container_width=True):
            st.info("Re-running adaptation with current settings...")
            # In reality, this would trigger a new adaptation process
            st.success("Adaptation completed!")

    with col2:
        if st.button("📥 Save Adapted Image", use_container_width=True):
            st.info("Saving adapted image to storage...")

def adaptation_page():
    """Main style adaptation page function"""
    # Header
    st.header("🎨 Style Adaptation")
    st.markdown("Visualize and review the image style adaptation process")

    # Get request ID from session state (should be set from upload/drift detection)
    if 'current_request_id' not in st.session_state:
        st.warning("No request ID found. Please upload an image and run drift detection first.")
        if st.button("Go to Upload Page"):
            st.switch_page("upload.py")
        return

    request_id = st.session_state.current_request_id

    # Create services
    adaptation_service, drift_service = create_services()

    # Get drift score to determine if adaptation is needed
    try:
        with st.spinner("Checking drift status..."):
            drift_result = drift_service.get_drift_result(request_id)
            drift_score = drift_result.drift_score
    except Exception as e:
        st.error(f"Error getting drift information: {str(e)}")
        # Fallback to a default drift score
        drift_score = 0.5

    # Get adaptation results from service
    try:
        with st.spinner("Generating adaptation results..."):
            adaptation_result = adaptation_service.adapt_image(request_id, drift_score)
    except Exception as e:
        st.error(f"Error generating adaptation: {str(e)}")
        return

    # Page description
    st.markdown("""
    This page shows how the platform adapts incoming medical images to match
    the training data distribution while preserving diagnostic anatomical features.
    """)

    # Show adaptation trigger info
    if adaptation_result.adaptation_applied:
        st.info(f"""
        🔍 **Adaptation Triggered**: Drift score of {drift_score:.3f}
        exceeded threshold, initiating style adaptation process.
        """)
    else:
        st.info(f"""
        🔍 **Adaptation Not Required**: Drift score of {drift_score:.3f}
        is below threshold, image proceeds to inference without adaptation.
        """)

    # Display adaptation steps
    st.subheader("Adaptation Process Steps")
    st.markdown("Each step in the adaptation pipeline is shown below:")

    for step in adaptation_result.adaptation_steps:
        render_adaptation_step(step)

    # Display execution time summary
    st.metric("Total Adaptation Time", f"{adaptation_result.total_execution_time}s")

    # Image comparison section
    st.markdown("<br>", unsafe_allow_html=True)
    render_image_comparison()

    # Quality metrics
    st.markdown("<br>", unsafe_allow_html=True)
    render_adaptation_metrics(adaptation_result)

    # Timeline visualization
    st.markdown("<br>", unsafe_allow_html=True)
    render_adaptation_timeline(adaptation_result)

    # Controls section
    st.markdown("<br>", unsafe_allow_html=True)
    render_adaptation_controls()

    # TODO comments for future integration
    st.markdown("---")
    st.markdown("### 🔧 Future Integration Points")
    st.markdown("""
    - TODO: Connect to actual AdaptationService (replace mock)
    - TODO: Integrate with actual style adaptation algorithms (Histogram normalization, AdaIN, etc.)
    - TODO: Show real image comparisons (original vs adapted vs difference)
    - TODO: Allow users to adjust adaptation parameters in real-time
    - TODO: Save adapted images to object storage for downstream use
    - TODO: Provide before/after slider for image comparison
    - TODO: Add ability to skip certain adaptation steps
    - TODO: Integrate with drift detection to show what triggered adaptation
    - TODO: Show computational resource usage (GPU/CPU/memory) for each step
    - TODO: Get request_id from URL parameters or routing system
    """)