"""
Model registry page for the Cross-Hospital Generalization Platform.
Displays registered MLflow models and their metadata.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import services
from frontend.services.registry_service import RegistryService

def create_registry_service():
    """Create an instance of the registry service."""
    return RegistryService()

def get_status_badge(frozen: bool) -> str:
    """Generate HTML for model status badge."""
    if frozen:
        return '''
        <span style="
            background-color: #28a745;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        ">FROZEN</span>
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
        ">ACTIVE</span>
        '''

def render_model_card(model):
    """Render a model card display"""
    # Create card container
    with st.container():
        # Use columns for layout
        col1, col2 = st.columns([1, 3])

        with col1:
            # Model icon/placeholder
            st.markdown("""
            <div style="
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                height: 80px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 1rem;
            ">
                <span style="font-size: 2rem;">🤖</span>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Model info
            st.markdown(f"""
            <div style="padding-left: 1rem;">
                <h3 style="margin: 0 0 0.5rem 0;">{model.model_name}</h3>
                <div style="display: flex; gap: 1rem; margin-bottom: 0.5rem; flex-wrap: wrap;">
                    <span style="background-color: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 0.9em;">{model.version}</span>
                    {get_status_badge(model.frozen)}
                    <span style="background-color: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 0.9em;">{model.task}</span>
                    <span style="background-color: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 0.9em;">{model.framework}</span>
                </div>
                <p style="margin: 0.5rem 0; color: #6c757d; font-size: 0.9em;">
                    {model.description}
                </p>
                <div style="display: flex; gap: 1rem; margin-top: 0.5rem; font-size: 0.9em; color: #495057;">
                    <span><strong>Hospital:</strong> {model.hospital}</span>
                    <span><strong>Training Date:</strong> {model.training_date}</span>
                    <span><strong>Size:</strong> {model.size_mb} MB</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Add a button to select this model
        if st.button(f"Select {model.model_name}", key=f"select_{model.model_name}_{model.version}", use_container_width=True):
            st.session_state.selected_model = model
            st.success(f"Selected {model.model_name} v{model.version}")
            # In reality, this would set the active model for inference

        st.markdown("---")

def render_model_details(model):
    """Render detailed model information"""
    st.subheader(f"Model Details: {model.model_name} v{model.version}")

    # Basic information
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Basic Information")
        info_data = {
            "Model Name": model.model_name,
            "Version": model.version,
            "Task": model.task,
            "Hospital": model.hospital,
            "Framework": model.framework,
            "Training Date": model.training_date,
            "Frozen Status": "Frozen" if model.frozen else "Not Frozen",
            "Frozen Date": model.frozen_date if model.frozen_date else "N/A",
            "Model Size": f"{model.size_mb} MB",
            "Checksum": model.checksum
        }

        for key, value in info_data.items():
            st.text(f"{key}: {value}")

    with col2:
        st.markdown("### Technical Specifications")
        tech_data = {
            "Input Size": model.input_size,
            "Output Classes": ", ".join(model.output_classes),
            "Number of Output Classes": len(model.output_classes)
        }

        for key, value in tech_data.items():
            st.text(f"{key}: {value}")

        st.markdown("### Tags")
        tags_html = ""
        for tag in model.tags:
            tags_html += f'<span style="background-color: #e9ecef; padding: 2px 6px; border-radius: 4px; margin-right: 5px; display: inline-block;">{tag}</span> '
        st.markdown(tags_html, unsafe_allow_html=True)

    # Performance metrics
    st.markdown("### Performance Metrics")
    perf = model.performance

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("AUC", f"{perf['auc']:.3f}")
    with col2:
        st.metric("Sensitivity", f"{perf['sensitivity']:.2f}")
    with col3:
        st.metric("Specificity", f"{perf['specificity']:.2f}")
    with col4:
        st.metric("F1 Score", f"{perf['f1_score']:.2f}")

    # Performance interpretation
    st.markdown("### Performance Interpretation")
    auc = perf['auc']
    if auc >= 0.9:
        st.success("Excellent discrimination performance (AUC ≥ 0.9)")
    elif auc >= 0.8:
        st.info("Good discrimination performance (AUC ≥ 0.8)")
    elif auc >= 0.7:
        st.warning("Fair discrimination performance (AUC ≥ 0.7)")
    else:
        st.error("Poor discrimination performance (AUC < 0.7)")

def render_models_table(models):
    """Render models as a table"""
    # Prepare data for table
    table_data = []
    for model in models:
        table_data.append({
            "Model Name": model.model_name,
            "Version": model.version,
            "Task": model.task,
            "Hospital": model.hospital,
            "Framework": model.framework,
            "Frozen": "Yes" if model.frozen else "No",
            "Size (MB)": model.size_mb,
            "AUC": f"{model.performance['auc']:.3f}",
            "Training Date": model.training_date
        })

    df = pd.DataFrame(table_data)

    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Frozen": st.column_config.TextColumn(
                "Frozen",
                help="Whether the model is frozen (immutable)"
            ),
            "AUC": st.column_config.NumberColumn(
                "AUC",
                help="Area Under the ROC Curve",
                format="%.3f"
            )
        }
    )

    # Allow model selection from table
    selected_indices = st.multiselect(
        "Select models to view details",
        options=range(len(models)),
        format_func=lambda x: f"{models[x].model_name} v{models[x].version}",
        placeholder="Choose models..."
    )

    if selected_indices:
        selected_model_idx = selected_indices[0]  # Take first selected
        selected_model = models[selected_model_idx]
        render_model_details(selected_model)

def model_registry_page():
    """Main model registry page function"""
    # Header
    st.header("📦 Model Registry")
    st.markdown("Browse and manage registered MLflow models for inference")

    # Create registry service
    registry_service = create_registry_service()

    # Get model data from service
    try:
        with st.spinner("Loading model registry..."):
            models = registry_service.get_registered_models()
    except Exception as e:
        st.error(f"Error loading model registry: {str(e)}")
        return

    # Page description
    st.markdown("""
    The model registry contains frozen AI models that are available for inference
    through the CHGP platform. Models are versioned, tracked, and can be selected
    for specific diagnostic tasks.
    """)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Models", len(models))
    with col2:
        frozen_count = sum(1 for m in models if m.frozen)
        st.metric("Frozen Models", frozen_count)
    with col3:
        avg_size = sum(m.size_mb for m in models) / len(models) if models else 0
        st.metric("Avg Model Size", f"{avg_size:.1f} MB")
    with col4:
        # Most recent training date
        if models:
            dates = [datetime.strptime(m.training_date, '%Y-%m-%d') for m in models]
            most_recent = max(dates).strftime('%Y-%m-%d')
            st.metric("Most Recent Training", most_recent)
        else:
            st.metric("Most Recent Training", "N/A")

    st.markdown("---")

    # Tabs for different views
    tab1, tab2 = st.tabs(["📋 Model List", "🃏 Model Cards"])

    with tab1:
        st.subheader("Registered Models")
        render_models_table(models)

    with tab2:
        st.subheader("Model Cards")
        st.markdown("Visual representation of registered models:")

        # Display models in a grid
        cols = st.columns(2)  # Two columns for model cards
        for i, model in enumerate(models):
            with cols[i % 2]:
                render_model_card(model)

    # Selected model details (if any)
    if 'selected_model' in st.session_state:
        st.markdown("---")
        st.subsection("Selected Model Details")
        render_model_details(st.session_state.selected_model)

        # Action buttons for selected model
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("Use for Inference", type="primary", use_container_width=True):
                st.success(f"Model {st.session_state.selected_model.model_name} v{st.session_state.selected_model.version} selected for inference!")
                # In reality, this would set the active model in the inference service

        with col2:
            if st.button("Clear Selection", use_container_width=True):
                if 'selected_model' in st.session_state:
                    del st.session_state.selected_model
                st.experimental_rerun()

    # TODO comments for future integration
    st.markdown("---")
    st.markdown("### 🔧 Future Integration Points")
    st.markdown("""
    - TODO: Connect to actual RegistryService (replace mock)
    - TODO: Integrate with actual MLflow tracking server
    - TODO: Show real-time model loading/status from inference service
    - TODO: Allow users to register new models (with appropriate permissions)
    - TODO: Show model lineage and version history
    - TODO: Provide model explanation/interpretability tools
    - TODO: Add ability to download model artifacts or Docker images
    - TODO: Integrate with inference service to show currently loaded model
    - TODO: Add model validation and testing controls
    - TODO: Show deployment status (staging, production, archived)
    """)