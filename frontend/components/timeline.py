"""
Timeline component for the Cross-Hospital Generalization Platform.
Provides reusable components for displaying timelines and process flows.
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime

def render_timeline(
    events: List[Dict[str, Any]],
    orientation: str = "vertical",
    show_connectors: bool = True,
    key: Optional[str] = None
) -> None:
    """
    Render a timeline of events.

    Args:
        events (List[Dict]): List of event dictionaries with keys:
                           - 'title': str (required)
                           - 'description': str (optional)
                           - 'timestamp': str or datetime (optional)
                           - 'status': str (optional) - 'completed', 'pending', 'failed', 'processing'
                           - 'icon': str (optional) - emoji or text icon
                           - 'color': str (optional) - hex color or color name
        orientation (str): 'vertical' or 'horizontal'
        show_connectors (bool): Whether to show connecting lines between events
        key (str, optional): Unique key for the component
    """
    if not events:
        st.info("No timeline events to display")
        return

    # Define default status colors
    status_colors = {
        'completed': '#4caf50',  # Green
        'pending': '#ffc107',    # Yellow
        'processing': '#2196f3', # Blue
        'failed': '#f44336',     # Red
        'cancelled': '#9e9e9e',  # Gray
        'skipped': '#9e9e9e'     # Gray
    }

    if orientation == "vertical":
        render_vertical_timeline(events, show_connectors, status_colors, key)
    else:
        render_horizontal_timeline(events, show_connectors, status_colors, key)

def render_vertical_timeline(
    events: List[Dict[str, Any]],
    show_connectors: bool,
    status_colors: Dict[str, str],
    key: Optional[str] = None
) -> None:
    """Render a vertical timeline."""
    for i, event in enumerate(events):
        # Extract event data with defaults
        title = event.get('title', f'Event {i+1}')
        description = event.get('description', '')
        timestamp = event.get('timestamp', '')
        status = event.get('status', 'pending')
        icon = event.get('icon', '⚪')
        color = event.get('color', status_colors.get(status, '#9e9e9e'))

        # Format timestamp if it's a datetime object
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M")
        else:
            timestamp_str = str(timestamp) if timestamp else ""

        # Determine connector styling
        connector_style = ""
        if show_connectors and i < len(events) - 1:  # Not the last event
            connector_style = """
            <div style="
                position: absolute;
                left: 12px;
                width: 2px;
                height: 50%;
                background-color: #e0e0e0;
                top: 50%;
            ">
            </div>
            """

        # Create the timeline item
        st.markdown(f"""
        <div style="
            position: relative;
            padding: 1rem 0;
            min-height: 60px;
        ">
            {connector_style if show_connectors else ''}
            <div style="
                position: relative;
                padding-left: 30px;
            ">
                <!-- Event Icon -->
                <div style="
                    position: absolute;
                    left: 0;
                    top: 50%;
                    transform: translateY(-50%);
                    width: 24px;
                    height: 24px;
                    background-color: {color};
                    color: white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1rem;
                ">
                    {icon}
                </div>

                <!-- Event Content -->
                <div style="
                    background-color: #f8f9fa;
                    border-radius: 0.5rem;
                    padding: 1rem;
                    margin-left: 24px;
                    min-height: 24px;
                ">
                    {f'<h4 style="margin: 0 0 0.5rem 0; color: #212529;">{title}</h4>' if title else ''}
                    {f'<p style="margin: 0 0 0.5rem 0; color: #6c757d; font-size: 0.9rem;">{description}</p>' if description else ''}
                    {f'<div style="font-size: 0.875rem; color: #6c757d;">{timestamp_str}</div>' if timestamp_str else ''}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_horizontal_timeline(
    events: List[Dict[str, Any]],
    show_connectors: bool,
    status_colors: Dict[str, str],
    key: Optional[str] = None
) -> None:
    """Render a horizontal timeline."""
    if not events:
        return

    # Create columns for each event
    cols = st.columns(len(events))

    for i, (col, event) in enumerate(zip(cols, events)):
        with col:
            # Extract event data with defaults
            title = event.get('title', f'Event {i+1}')
            description = event.get('description', '')
            timestamp = event.get('timestamp', '')
            status = event.get('status', 'pending')
            icon = event.get('icon', '⚪')
            color = event.get('color', status_colors.get(status, '#9e9e9e'))

            # Format timestamp if it's a datetime object
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.strftime("%m/%d %H:%M")
            else:
                timestamp_str = str(timestamp) if timestamp else ""

            # Create the timeline item
            st.markdown(f"""
            <div style="
                text-align: center;
                padding: 1rem;
                background-color: #f8f9fa;
                border-radius: 0.5rem;
            ">
                <!-- Event Icon -->
                <div style="
                    margin: 0 auto 0.5rem;
                    width: 40px;
                    height: 40px;
                    background-color: {color};
                    color: white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.5rem;
                ">
                    {icon}
                </div>

                <!-- Event Title -->
                <div style="
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                    color: #212529;
                ">
                    {title}
                </div>

                <!-- Event Description -->
                {f'<div style="font-size: 0.875rem; color: #6c757d; margin-bottom: 0.5rem;">{description}</div>' if description else ''}

                <!-- Event Timestamp -->
                {f'<div style="font-size: 0.75rem; color: #6c757d;">{timestamp_str}</div>' if timestamp_str else ''}
            </div>
            """, unsafe_allow_html=True)

            # Add connector between events (except for the last one)
            if show_connectors and i < len(events) - 1:
                st.markdown(f"""
                <div style="
                    text-align: center;
                    margin: 0.5rem 0;
                    color: #e0e0e0;
                    font-size: 1.5rem;
                ">
                    →
                </div>
                """, unsafe_allow_html=True)

def render_process_timeline(
    steps: List[Dict[str, Any]],
    current_step: int = 0,
    key: Optional[str] = None
) -> None:
    """
    Render a process timeline showing progress through steps.

    Args:
        steps (List[Dict]): List of step dictionaries with keys:
                          - 'name': str (required)
                          - 'description': str (optional)
                          - 'status': str (optional) - 'completed', 'current', 'pending', 'failed'
        current_step (int): Index of the current step (0-based)
        key (str, optional): Unique key for the component
    """
    if not steps:
        st.info("No process steps to display")
        return

    # Define status colors and icons
    status_config = {
        'completed': {'color': '#4caf50', 'icon': '✅'},
        'current': {'color': '#2196f3', 'icon': '🔄'},
        'pending': {'color': '#ffc107', 'icon': '⏳'},
        'failed': {'color': '#f44336', 'icon': '❌'}
    }

    # Create horizontal layout
    cols = st.columns(len(steps))

    for i, (col, step) in enumerate(zip(cols, steps)):
        with col:
            # Determine step status
            if i < current_step:
                status = 'completed'
            elif i == current_step:
                status = 'current'
            elif i > current_step:
                status = 'pending'
            else:
                status = 'pending'  # Default

            # Override with explicit status if provided
            if 'status' in step and step['status'] in status_config:
                status = step['status']

            config = status_config.get(status, status_config['pending'])
            color = config['color']
            icon = config['icon']

            # Extract step data
            name = step.get('name', f'Step {i+1}')
            description = step.get('description', '')

            # Create the step indicator
            st.markdown(f"""
            <div style="
                text-align: center;
                padding: 1rem;
            ">
                <!-- Step Icon -->
                <div style="
                    margin: 0 auto 0.75rem;
                    width: 50px;
                    height: 50px;
                    background-color: {color};
                    color: white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.5rem;
                ">
                    {icon}
                </div>

                <!-- Step Name -->
                <div style="
                    font-weight: 600;
                    margin-bottom: 0.25rem;
                    color: #212529;
                ">
                    {name}
                </div>

                <!-- Step Description -->
                {f'<div style="font-size: 0.875rem; color: #6c757d;">{description}</div>' if description else ''}

                <!-- Status Indicator for completed steps -->
                {f'<div style="margin-top: 0.5rem; font-size: 0.75rem; color: {color};">{"Completed" if status == "completed" else "In Progress" if status == "current" else "Pending"}</div>' if status in ['completed', 'current'] else ''}
            </div>
            """, unsafe_allow_html=True)

            # Add connector between steps (except for the last one)
            if i < len(steps) - 1:
                st.markdown(f"""
                <div style="
                    text-align: center;
                    margin: 0.5rem 0;
                    color: #e0e0e0;
                    font-size: 1.5rem;
                ">
                    →
                </div>
                """, unsafe_allow_html=True)

def render_pipeline_timeline(
    pipeline_stages: List[str],
    active_stages: List[bool],
    stage_descriptions: Optional[List[str]] = None,
    key: Optional[str] = None
) -> None:
    """
    Render a pipeline timeline showing stages of a process.

    Args:
        pipeline_stages (List[str]): Names of pipeline stages
        active_stages (List[bool]): Boolean list indicating which stages are active/completed
        stage_descriptions (List[str], optional): Descriptions for each stage
        key (str, optional): Unique key for the component
    """
    if not pipeline_stages:
        st.info("No pipeline stages to display")
        return

    # Ensure we have the right number of descriptions
    if stage_descriptions is None:
        stage_descriptions = [""] * len(pipeline_stages)
    elif len(stage_descriptions) < len(pipeline_stages):
        stage_descriptions.extend([""] * (len(pipeline_stages) - len(stage_descriptions)))

    # Create the timeline
    st.markdown("""
    <div style="
        display: flex;
        align-items: center;
    ">
    """, unsafe_allow_html=True)

    for i, (stage, is_active, description) in enumerate(zip(pipeline_stages, active_stages, stage_descriptions)):
        # Determine colors based on activity
        if is_active:
            line_color = "#4caf50"  # Green for active/completed
            circle_color = "#4caf50"
            circle_bg = "white"
            text_color = "#212529"
        else:
            line_color = "#e0e0e0"  # Gray for inactive
            circle_color = "#e0e0e0"
            circle_bg = "#e0e0e0"
            text_color = "#6c757d"

        # Draw the line (except for the first stage)
        if i > 0:
            st.markdown(f"""
            <div style="
                flex: 1;
                height: 4px;
                background-color: {line_color};
                margin: 0 0.5rem;
            ">
            </div>
            """, unsafe_allow_html=True)

        # Draw the stage node
        st.markdown(f"""
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
        ">
            <div style="
                width: 30px;
                height: 30px;
                background-color: {circle_bg};
                border: 2px solid {circle_color};
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.875rem;
                font-weight: 600;
                color: {circle_color};
            ">
                {i+1}
            </div>
            {f'<div style="margin-top: 0.5rem; font-size: 0.875rem; color: {text_color}; word-break: break-all; max-width: 120px; text-align: center;">{stage}</div>' if stage else ''}
            {f'<div style="margin-top: 0.25rem; font-size: 0.75rem; color: #6c757d;">{description}</div>' if description else ''}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

def render_horizontal_process_bar(
    steps: List[str],
    current_step_index: int,
    step_statuses: Optional[List[str]] = None,
    key: Optional[str] = None
) -> None:
    """
    Render a horizontal process bar showing progress through steps.

    Args:
        steps (List[str]): List of step names
        current_step_index (int): Index of the current step (0-based, -1 if none)
        step_statuses (List[str], optional): Status for each step ('completed', 'current', 'pending', 'failed')
        key (str, optional): Unique key for the component
    """
    if not steps:
        return

    # Default statuses if not provided
    if step_statuses is None:
        step_statuses = ['pending'] * len(steps)
        if 0 <= current_step_index < len(steps):
            step_statuses[current_step_index] = 'current'
        # Mark previous steps as completed
        for i in range(current_step_index):
            if i < len(step_statuses):
                step_statuses[i] = 'completed'

    # Define status colors
    status_colors = {
        'completed': '#4caf50',
        'current': '#2196f3',
        'pending': '#e0e0e0',
        'failed': '#f44336'
    }

    # Create the process bar
    st.markdown("""
    <div style="
        display: flex;
        align-items: center;
    ">
    """, unsafe_allow_html=True)

    for i, (step, status) in enumerate(zip(steps, step_statuses)):
        # Determine colors
        if status == 'completed':
            bg_color = "#4caf50"
            text_color = "white"
        elif status == 'current':
            bg_color = "#2196f3"
            text_color = "white"
        elif status == 'failed':
            bg_color = "#f44336"
            text_color = "white"
        else:  # pending
            bg_color = "#e0e0e0"
            text_color = "#6c757d"

        # Draw the step container
        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            background-color: {bg_color};
            color: {text_color};
            padding: 0.5rem 1rem;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            font-weight: 500;
            white-space: nowrap;
        ">
            {step}
        </div>
        """, unsafe_allow_html=True)

        # Add separator between steps (except for the last one)
        if i < len(steps) - 1:
            st.markdown(f"""
            <div style="
                width: 2px;
                height: 24px;
                background-color: #e0e0e0;
                margin: 0 0.25rem;
            ">
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)