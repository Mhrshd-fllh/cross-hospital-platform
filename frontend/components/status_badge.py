"""
Status badge component for the Cross-Hospital Generalization Platform.
Provides reusable components for displaying status indicators with color coding.
"""

import streamlit as st

def render_status_badge(status, text=None, color_map=None):
    """
    Render a status badge.

    Args:
        status (str): The status value (used to determine color)
        text (str, optional): The text to display (defaults to status if not provided)
        color_map (dict, optional): Mapping of status values to colors
    """
    # Default color map
    if color_map is None:
        color_map = {
            "healthy": "green",
            "online": "green",
            "active": "green",
            "pass": "green",
            "normal": "green",
            "degraded": "orange",
            "warning": "orange",
            "warning": "orange",
            "error": "red",
            "offline": "red",
            "inactive": "red",
            "fail": "red",
            "critical": "red",
            "pending": "blue",
            "processing": "blue",
            "info": "blue",
            "unknown": "gray",
            "disabled": "gray"
        }

    # Determine text to display
    display_text = text if text is not None else str(status).title()

    # Determine color (default to gray if status not in map)
    color = color_map.get(status.lower(), "gray") if isinstance(color_map, dict) else "gray"

    # Render the badge
    st.markdown(f"""
    <span style="
        background-color: {color};
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: capitalize;
    ">
        {display_text}
    </span>
    """, unsafe_allow_html=True)

def render_status_badge_with_icon(status, text=None, icon_map=None, color_map=None):
    """
    Render a status badge with an icon.

    Args:
        status (str): The status value (used to determine color and icon)
        text (str, optional): The text to display (defaults to status if not provided)
        icon_map (dict, optional): Mapping of status values to icons (emoji or text)
        color_map (dict, optional): Mapping of status values to colors
    """
    # Default color map
    if color_map is None:
        color_map = {
            "healthy": "green",
            "online": "green",
            "active": "green",
            "pass": "green",
            "normal": "green",
            "degraded": "orange",
            "warning": "orange",
            "error": "red",
            "offline": "red",
            "inactive": "red",
            "fail": "red",
            "critical": "red",
            "pending": "blue",
            "processing": "blue",
            "info": "blue",
            "unknown": "gray",
            "disabled": "gray"
        }

    # Default icon map
    if icon_map is None:
        icon_map = {
            "healthy": "✅",
            "online": "✅",
            "active": "✅",
            "pass": "✅",
            "normal": "✅",
            "degraded": "⚠️",
            "warning": "⚠️",
            "error": "❌",
            "offline": "❌",
            "inactive": "❌",
            "fail": "❌",
            "critical": "❌",
            "pending": "⏳",
            "processing": "🔄",
            "info": "ℹ️",
            "unknown": "❓",
            "disabled": "⚫"
        }

    # Determine text to display
    display_text = text if text is not None else str(status).title()

    # Determine color and icon (default to gray/question mark if status not in maps)
    color = color_map.get(status.lower(), "gray") if isinstance(color_map, dict) else "gray"
    icon = icon_map.get(status.lower(), "❓") if isinstance(icon_map, dict) else "❓"

    # Render the badge with icon
    st.markdown(f"""
    <span style="
        background-color: {color};
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: capitalize;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    ">
        <span>{icon}</span>
        <span>{display_text}</span>
    </span>
    """, unsafe_allow_html=True)

def render_health_indicator(label, value, thresholds=None, format_func=None):
    """
    Render a health indicator with color coding based on value thresholds.

    Args:
        label (str): Label for the indicator
        value (float or int): The value to evaluate
        thresholds (dict, optional): Dictionary with 'warning' and 'critical' thresholds
                                   Format: {'warning': value, 'critical': value}
                                   Values above warning are warning, above critical are critical
                                   For inverted metrics (like response time), reverse the logic
        format_func (function, optional): Function to format the value for display
    """
    # Default thresholds (for metrics where lower is better)
    if thresholds is None:
        thresholds = {'warning': 70, 'critical': 90}

    # Default format function
    if format_func is None:
        format_func = lambda x: f"{x}"

    formatted_value = format_func(value)

    # Determine color based on thresholds
    # Assuming lower is better (like response time, error rate)
    # For metrics where higher is better (like success rate), this would need to be inverted
    if value >= thresholds.get('critical', float('inf')):
        color = "red"
    elif value >= thresholds.get('warning', float('inf')):
        color = "orange"
    else:
        color = "green"

    # Render the indicator
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0.5rem 0;
    ">
        <span style="
            background-color: {color};
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            font-weight: 600;
        ">
            {formatted_value}
        </span>
        <span>{label}</span>
    </div>
    """, unsafe_allow_html=True)