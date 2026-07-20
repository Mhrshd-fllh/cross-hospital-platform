"""
Model card component for the Cross-Hospital Generalization Platform.
Provides reusable components for displaying model information and metadata.
"""

import streamlit as st
from typing import Optional, List, Dict, Any

def render_model_card(
    model_name: str,
    version: str,
    task: str,
    hospital: str,
    framework: str,
    training_date: str,
    frozen: bool = False,
    frozen_date: Optional[str] = None,
    input_size: Optional[str] = None,
    output_classes: Optional[List[str]] = None,
    performance: Optional[Dict[str, float]] = None,
    size_mb: Optional[float] = None,
    checksum: Optional[str] = None,
    tags: Optional[List[str]] = None,
    description: Optional[str] = None,
    show_details_button: bool = True,
    key: Optional[str] = None
) -> None:
    """
    Render a model card displaying key information about a registered model.

    Args:
        model_name (str): Name of the model
        version (str): Version of the model
        task (str): Task the model performs (e.g., "Pneumonia Detection")
        hospital (str): Hospital or dataset the model was trained on
        framework (str): Framework used (e.g., "PyTorch", "TensorFlow")
        training_date (str): Date the model was trained
        frozen (bool): Whether the model is frozen (immutable)
        frozen_date (str, optional): Date the model was frozen
        input_size (str, optional): Input size (e.g., "224x224x3")
        output_classes (List[str], optional): List of output class names
        performance (Dict[str, float], optional): Performance metrics (auc, sensitivity, etc.)
        size_mb (float, optional): Model size in megabytes
        checksum (str, optional): Model checksum/hash
        tags (List[str], optional): Tags associated with the model
        description (str, optional): Description of the model
        show_details_button (bool): Whether to show a details button
        key (str, optional): Unique key for the component
    """
    # Determine badge colors
    if frozen:
        status_text = "FROZEN"
        status_color = "#28a745"  # Green
        status_bg = "rgba(40, 167, 69, 0.1)"
    else:
        status_text = "ACTIVE"
        status_color = "#ffc107"  # Yellow
        status_bg = "rgba(255, 193, 7, 0.1)"

    # Truncate description if too long
    display_description = description
    if description and len(description) > 100:
        display_description = description[:97] + "..."

    # Create the card
    card_html = f"""
    <div style="
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    ">
        <div style="display: flex; align-items: flex-start;">
            <!-- Model Icon -->
            <div style="
                flex-shrink: 0;
                width: 60px;
                height: 60px;
                background-color: #f8f9fa;
                border-radius: 0.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 1.5rem;
            ">
                <span style="font-size: 2.5rem;">🤖</span>
            </div>

            <!-- Model Info -->
            <div style="flex-grow: 1;">
                <h3 style="margin: 0 0 0.5rem 0; color: #212529;">
                    {model_name}
                </h3>
                <div style="display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1rem;">
                    <span style="
                        background-color: #e9ecef;
                        color: #495057;
                        padding: 0.25rem 0.5rem;
                        border-radius: 0.25rem;
                        font-size: 0.875rem;
                    ">
                        v{version}
                    </span>
                    <span style="
                        background-color: {status_bg};
                        color: {status_color};
                        padding: 0.25rem 0.5rem;
                        border-radius: 0.25rem;
                        font-size: 0.875rem;
                        font-weight: 600;
                    ">
                        {status_text}
                    </span>
                    <span style="
                        background-color: #e9ecef;
                        color: #495057;
                        padding: 0.25rem 0.5rem;
                        border-radius: 0.25rem;
                        font-size: 0.875rem;
                    ">
                        {task}
                    </span>
                    <span style="
                        background-color: #e9ecef;
                        color: #495057;
                        padding: 0.25rem 0.5rem;
                        border-radius: 0.25rem;
                        font-size: 0.875rem;
                    ">
                        {framework}
                    </span>
                </div>

                {f'<p style="margin: 0 0 1rem 0; color: #6c757d; font-size: 0.9rem; line-height: 1.4;">{display_description}</p>' if display_description else ''}

                <div style="display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.875rem; color: #6c757d;">
                    <div><strong>Hospital:</strong> {hospital}</div>
                    <div><strong>Training Date:</strong> {training_date}</div>
                    {f'<div><strong>Frozen Date:</strong> {frozen_date}</div>' if frozen_date else ''}
                    {f'<div><strong>Size:</strong> {size_mb} MB</div>' if size_mb else ''}
                </div>

                {f'<div style="margin-top: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">' + ''.join([f'<span style="background-color: #e9ecef; color: #495057; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem;">{tag}</span>' for tag in (tags or [])]) + '</div>' if tags else ''}

                {f'<div style="margin-top: 1rem;">' + '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); gap: 0.5rem;">' + ''.join([f'<div style="text-align: center;"><div style="font-size: 0.75rem; color: #6c757d;">{k.upper()}</div><div style="font-size: 1rem; font-weight: 600; color: {"#28a745" if v >= 0.9 else "#ffc107" if v >= 0.8 else "#dc3545"}">{v:.3f}</div></div>' for k, v in (performance or {}).items()]) + '</div></div>' if performance else ''}
            </div>
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)

    # Details button
    if show_details_button:
        button_key = f"{key}_details" if key else None
        if st.button("View Details", key=button_key, use_container_width=True):
            # In a real implementation, this would open a modal or expand the card
            # For now, we'll just show a message
            st.info(f"Showing detailed information for {model_name} v{version}")

def render_model_card_compact(
    model_name: str,
    version: str,
    task: str,
    frozen: bool = False,
    performance_score: Optional[float] = None,
    performance_metric: str = "AUC",
    key: Optional[str] = None
) -> None:
    """
    Render a compact model card for use in lists or grids.

    Args:
        model_name (str): Name of the model
        version (str): Version of the model
        task (str): Task the model performs
        frozen (bool): Whether the model is frozen
        performance_score (float, optional): Primary performance score to display
        performance_metric (str): Name of the performance metric (e.g., "AUC", "F1")
        key (str, optional): Unique key for the component
    """
    # Determine badge colors
    if frozen:
        status_text = "FROZEN"
        status_color = "#28a745"  # Green
    else:
        status_text = "ACTIVE"
        status_color = "#ffc107"  # Yellow

    # Performance display
    perf_display = ""
    if performance_score is not None:
        perf_color = "#28a745" if performance_score >= 0.9 else "#ffc107" if performance_score >= 0.8 else "#dc3545"
        perf_display = f"""
        <div style="margin-top: 0.5rem; display: flex; align-items: center;">
            <span style="font-size: 0.875rem; color: #6c757d; margin-right: 0.5rem;">
                {performance_metric}:
            </span>
            <span style="
                font-size: 1.1rem;
                font-weight: 600;
                color: {perf_color};
            ">
                {performance_score:.3f}
            </span>
        </div>
        """

    # Create the compact card
    card_html = f"""
    <div style="
        border: 1px solid #e0e0e0;
        border-radius: 0.375rem;
        padding: 1rem;
        text-align: center;
        background-color: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    ">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
        <div style="font-weight: 600; margin-bottom: 0.25rem;">
            {model_name}
        </div>
        <div style="font-size: 0.875rem; color: #6c757d; margin-bottom: 0.5rem;">
            v{version}
        </div>
        <div style="
            background-color: #f8f9fa;
            color: #495057;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
        ">
            {task}
        </div>
        <div style="
            display: inline-block;
            background-color: {'rgba(40, 167, 69, 0.1)' if frozen else 'rgba(255, 193, 7, 0.1)'};
            color: {'#28a745' if frozen else '#ffc107'};
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            font-weight: 600;
        ">
            {status_text}
        </div>
        {perf_display}
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)

def render_model_comparison_card(
    models: List[Dict[str, Any]],
    compare_fields: Optional[List[str]] = None
) -> None:
    """
    Render a comparison card showing multiple models side by side.

    Args:
        models (List[Dict]): List of model dictionaries with their attributes
        compare_fields (List[str], optional): Fields to compare (defaults to common metrics)
    """
    if not models:
        st.info("No models to compare")
        return

    # Default fields to compare
    if compare_fields is None:
        compare_fields = ["model_name", "version", "task", "hospital", "framework",
                         "training_date", "frozen", "size_mb", "auc"]

    # Create comparison table
    import pandas as pd

    # Prepare data for DataFrame
    comparison_data = []
    for model in models:
        row = {}
        for field in compare_fields:
            if field in model:
                value = model[field]
                # Format certain fields
                if field == "frozen":
                    value = "Yes" if value else "No"
                elif field == "size_mb" and value is not None:
                    value = f"{value:.1f} MB"
                elif field.endswith("_date") and value:
                    # Keep date as is for now
                    pass
                row[field] = value
            else:
                row[field] = None
        comparison_data.append(row)

    df = pd.DataFrame(comparison_data)

    # Configure column display
    column_config = {}
    for field in compare_fields:
        if field == "auc":
            column_config[field] = st.column_config.NumberColumn(
                "AUC",
                format="%.3f",
                help="Area Under Curve"
            )
        elif field == "size_mb":
            column_config[field] = st.column_config.TextColumn(
                "Size",
                help="Model size in MB"
            )
        elif field == "frozen":
            column_config[field] = st.column_config.TextColumn(
                "Frozen",
                help="Whether model is frozen"
            )

    # Display the comparison table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )

def render_model_tag(tag: str, color: Optional[str] = None) -> None:
    """
    Render a single model tag.

    Args:
        tag (str): Tag text
        color (str, optional): Background color (defaults to light gray)
    """
    if color is None:
        color = "#e9ecef"  # Light gray

    st.markdown(f"""
    <span style="
        background-color: {color};
        color: #495057;
        padding: 0.125rem 0.375rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
    ">
        {tag}
    </span>
    """, unsafe_allow_html=True)

def render_model_status_indicator(frozen: bool) -> None:
    """
    Render a model status indicator (frozen/active).

    Args:
        frozen (bool): Whether the model is frozen
    """
    if frozen:
        st.markdown(f"""
        <span style="
            background-color: rgba(40, 167, 69, 0.1);
            color: #28a745;
            padding: 0.125rem 0.375rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 600;
        ">
            FROZEN
        </span>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <span style="
            background-color: rgba(255, 193, 7, 0.1);
            color: #ffc107;
            padding: 0.125rem 0.375rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 600;
        ">
            ACTIVE
        </span>
        """, unsafe_allow_html=True)