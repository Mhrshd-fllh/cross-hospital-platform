"""
Production inference page for the Cross-Hospital Generalization Platform.
Displays the inference pipeline and results for processed medical images.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Import services
from frontend.services.inference_service import InferenceService
from frontend.services.adaptation_service import AdaptationService
from frontend.services.drift_service import DriftService
from frontend.services.registry_service import RegistryService

def create_services():
    """Create instances of the services."""
    inference_service = InferenceService()
    adaptation_service = AdaptationService()
    drift_service = DriftService()
    registry_service = RegistryService()
    return inference_service, adaptation_service, drift_service, registry_service

def get_status_badge(status: str) -> str:
    """Generate HTML for status badge."""
    if status == "completed":
        return '''
        <span style="
            background-color: #28a745;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        ">COMPLETED</span>
        '''
    elif status == "processing":
        return '''
        <span style="
            background-color: #ffc107;
            color: #212529;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        ">PROCESSING</span>
        '''
    else:
        return '''
        <span style="
            background-color: #dc3545;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        ">FAILED</span>
        '''

def render_inference_pipeline_viz(inference_result):
    """Render the inference pipeline visualization"""
    st.subheader("Inference Pipeline Progress")

    # Get timing data
    timing = inference_result.timing
    adaptation_applied = inference_result.adaptation_applied

    # Define pipeline stages with actual timing
    stages = [
        {"name": "Upload", "completed": True, "time": 0.5},  # Estimated
        {"name": "Validation", "completed": True, "time": 0.3},  # Estimated
        {"name": "Drift Detection", "completed": True, "time": 0.4},  # Estimated
        {"name": "Style Adaptation", "completed": adaptation_applied, "time": timing.get("adaptation", 0.0)},
        {"name": "Model Retrieval", "completed": True, "time": timing.get("model_loading", 0.0)},
        {"name": "Inference", "completed": True, "time": timing.get("inference", 0.0)},
        {"name": "Logging", "completed": True, "time": 0.2},  # Estimated
        {"name": "Dashboard Update", "completed": False, "time": 0.1},  # Estimated
        {"name": "Feedback Collection", "completed": False, "time": 0.0}  # Not yet
    ]

    # Create a visual pipeline
    cols = st.columns(len(stages))

    for i, (col, stage) in enumerate(zip(cols, stages)):
        with col:
            if stage["completed"]:
                st.success(f"✅ {stage['name']}")
                if stage["time"] > 0:
                    st.caption(f"{stage['time']}s")
            else:
                if i == len(stages) - 2:  # Dashboard Update
                    st.info(f"🔄 {stage['name']}")
                elif i == len(stages) - 1:  # Feedback Collection
                    st.warning(f"⏳ {stage['name']}")
                else:
                    st.error(f"❌ {stage['name']}")

    # Show timing breakdown
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Timing Breakdown")

    # Remove estimated times for cleaner view
    actual_timing = {k: v for k, v in timing.items() if k != "total" and v > 0}

    if actual_timing:
        fig = go.Figure(data=[
            go.Bar(
                x=list(actual_timing.keys()),
                y=list(actual_timing.values()),
                marker_color='#1f77b4'
            )
        ])

        fig.update_layout(
            title=f"Inference Timing Breakdown (Total: {timing['total']}s)",
            xaxis_title="Pipeline Stage",
            yaxis_title="Time (seconds)",
            xaxis_tickangle=-45
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timing data available for visualization.")

def render_prediction_results(inference_result):
    """Render prediction results"""
    st.subheader("Prediction Results")

    # Main prediction
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"### Predicted Condition")
        st.markdown(f"# {inference_result.prediction}")

        # Confidence badge
        confidence = inference_result.confidence
        if confidence >= 0.9:
            conf_color = "green"
            conf_text = "Very High"
        elif confidence >= 0.8:
            conf_color = "blue"
            conf_text = "High"
        elif confidence >= 0.7:
            conf_color = "orange"
            conf_text = "Medium"
        else:
            conf_color = "red"
            conf_text = "Low"

        st.markdown(f"<span style='color: {conf_color}; font-weight: bold;'>Confidence: {confidence:.1%} ({conf_text})</span>", unsafe_allow_html=True)

    with col2:
        st.metric(
            label="Uncertainty",
            value=f"{inference_result.uncertainty['total']:.1%}",
            help="Total uncertainty (aleatoric + epistemic)"
        )

    with col3:
        st.metric(
            label="Processing Time",
            value=f"{inference_result.timing['total']:.1f}s",
            help="Total inference processing time"
        )

    # Detailed confidence scores
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Class Probabilities")

    # Prepare data for bar chart
    classes = list(inference_result.confidence_scores.keys())
    probabilities = list(inference_result.confidence_scores.values())

    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=classes,
            y=probabilities,
            marker_color=['green' if c == inference_result.prediction else 'lightblue' for c in classes],
            text=[f"{p:.1%}" for p in probabilities],
            textposition='auto'
        )
    ])

    fig.update_layout(
        title="Prediction Probabilities by Class",
        xaxis_title="Disease Class",
        yaxis_title="Probability",
        yaxis=dict(tickformat='.0%'),
        showlegend=False,
        height=400
    )

    # Add threshold lines
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray", annotation_text="Decision Threshold (0.5)")

    st.plotly_chart(fig, use_container_width=True)

    # Uncertainty breakdown
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Uncertainty Analysis")

    unc = inference_result.uncertainty
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Aleatoric Uncertainty", f"{unc['aleatoric']:.1%}",
                 help="Uncertainty due to data noise")
    with col2:
        st.metric("Epistemic Uncertainty", f"{unc['epistemic']:.1%}",
                 help="Uncertainty due to model limitations")
    with col3:
        st.metric("Total Uncertainty", f"{unc['total']:.1%}",
                 help="Combined uncertainty estimate")

def render_inference_details(inference_result):
    """Render detailed inference information"""
    st.subheader("Inference Details")

    # Basic information
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Request Information")
        info_data = {
            "Request ID": inference_result.request_id,
            "Timestamp": inference_result.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "Hospital": "General Hospital",  # Would come from request metadata in reality
            "Status": inference_result.status if hasattr(inference_result, 'status') else "completed"
        }

        for key, value in info_data.items():
            st.text(f"{key}: {value}")

    with col2:
        st.markdown("### Model Information")
        model_data = {
            "Model Used": inference_result.model_used,
            "Adaptation Applied": "Yes" if inference_result.adaptation_applied else "No",
            "Drift Score": f"{inference_result.drift_score:.3f}" if inference_result.drift_score > 0 else "0.000 (No adaptation needed)"
        }

        for key, value in model_data.items():
            st.text(f"{key}: {value}")

    # Timing breakdown
    st.markdown("### Processing Time Breakdown")
    timing = inference_result.timing

    timing_data = [
        {"Stage": "Preprocessing", "Time (s)": timing.get("preprocessing", 0)},
        {"Stage": "Adaptation", "Time (s)": timing.get("adaptation", 0)},
        {"Stage": "Model Loading", "Time (s)": timing.get("model_loading", 0)},
        {"Stage": "Inference", "Time (s)": timing.get("inference", 0)},
        {"Stage": "Postprocessing", "Time (s)": timing.get("postprocessing", 0)},
        {"Stage": "Total", "Time (s)": timing.get("total", 0)}
    ]

    df = pd.DataFrame(timing_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Time (s)": st.column_config.NumberColumn(
                "Time (s)",
                help": Processing time for each stage",
                format="%.2f"
            )
        }
    )

def render_inference_controls():
    """Render inference controls"""
    st.subheader("Inference Controls")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Confidence threshold
        st.slider(
            "Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05,
            help="Minimum confidence required for automatic acceptance"
        )

    with col2:
        # Uncertainty threshold
        st.slider(
            "Uncertainty Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.05,
            help="Maximum uncertainty allowed for automatic acceptance"
        )

    with col3:
        # Enable/disable features
        st.checkbox("Enable Test Time Augmentation", value=False,
                   help="Apply augmentations at inference time for robustness")
        st.checkbox("Enable Monte Carlo Dropout", value=False,
                   help="Use dropout at inference for uncertainty estimation")

    # Action buttons
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🔄 Run New Inference", use_container_width=True):
            st.info("Starting new inference process...")
            # In reality, this would trigger a new inference request
            st.success("New inference completed!")

    with col2:
        if st.button("📥 Download Report", use_container_width=True):
            st.info("Generating comprehensive report...")
            # In reality, this would generate a PDF report

def inference_page():
    """Main production inference page function"""
    # Header
    st.header("🚀 Production Inference")
    st.markdown("View inference pipeline execution and results for processed medical images")

    # Get request ID from session state (should be set from upload/adaptation/drift)
    if 'current_request_id' not in st.session_state:
        st.warning("No request ID found. Please upload an image and complete preprocessing steps first.")
        if st.button("Go to Upload Page"):
            st.switch_page("upload.py")
        return

    request_id = st.session_state.current_request_id

    # Create services
    inference_service, adaptation_service, drift_service, registry_service = create_services()

    # Get inference results from service
    try:
        with st.spinner("Running inference..."):
            # In a real implementation, we would get the adapted image path from adaptation service
            # For now, we'll pass None and let the mock service handle it
            inference_result = inference_service.run_inference(request_id, "auto_select", None)
    except Exception as e:
        st.error(f"Error running inference: {str(e)}")
        return

    # Page description
    st.markdown("""
    This page shows the complete inference pipeline execution, from uploaded image
    through preprocessing, adaptation, model inference, and result generation.
    """)

    # Show current status
    status = "completed"  # In reality, this would come from the result
    if status == "completed":
        st.success("✅ Inference completed successfully")
    elif status == "processing":
        st.info("🔄 Inference in progress...")
    else:
        st.error("❌ Inference failed")

    st.markdown("<br>", unsafe_allow_html=True)

    # Pipeline visualization
    render_inference_pipeline_viz(inference_result)

    # Prediction results
    st.markdown("<br>", unsafe_allow_html=True)
    render_prediction_results(inference_result)

    # Detailed information
    st.markdown("<br>", unsafe_allow_html=True)
    render_inference_details(inference_result)

    # Controls
    st.markdown("<br>", unsafe_allow_html=True)
    render_inference_controls()

    # TODO comments for future integration
    st.markdown("---")
    st.markdown("### 🔧 Future Integration Points")
    st.markdown("""
    - TODO: Connect to actual InferenceService (replace mock)
    - TODO: Integrate with actual Docker-based inference service
    - TODO: Show real-time inference progress (live updates)
    - TODO: Integrate with actual MLflow model loading
    - TODO: Show actual image processing steps (original → adapted → prediction)
    - TODO: Allow users to input custom images for inference
    - TODO: Provide explanation tools (saliency maps, attention visualization)
    - TODO: Integrate with feedback service for immediate feedback collection
    - TODO: Add ability to review and override predictions (with appropriate workflow)
    - TODO: Show computational resource usage during inference
    - TODO: Integrate with alerting system for low-confidence or high-uncertainty predictions
    - TODO: Get request_id from URL parameters or routing system
    - TODO: Pass actual adapted image path from adaptation service
    """)