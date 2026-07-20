"""
Drift indicator component for the Cross-Hospital Generalization Platform.
Provides reusable components for displaying drift scores and status indicators.
"""

import streamlit as st
from typing import Optional, Union

def render_drift_indicator(
    drift_score: float,
    label: Optional[str] = None,
    show_score: bool = True,
    show_status: bool = True,
    size: str = "medium",
    thresholds: Optional[dict] = None
) -> None:
    """
    Render a drift score indicator with color-coded status.

    Args:
        drift_score (float): Drift score value (typically 0-1, but can be higher)
        label (str, optional): Label to display (defaults to "Drift Score")
        show_score (bool): Whether to show the numeric score
        show_status (bool): Whether to show the status text (Low/Medium/High/Critical)
        size (str): Size of the indicator ("small", "medium", "large")
        thresholds (dict, optional): Custom thresholds for status levels
                                   Default: {"low": 0.3, "medium": 0.6, "high": 0.8}
    """
    # Default thresholds
    if thresholds is None:
        thresholds = {"low": 0.3, "medium": 0.6, "high": 0.8}

    # Determine status based on thresholds
    if drift_score < thresholds["low"]:
        status = "Low"
        color = "#4caf50"  # Green
    elif drift_score < thresholds["medium"]:
        status = "Medium"
        color = "#ff9800"  # Orange
    elif drift_score < thresholds["high"]:
        status = "High"
        color = "#f44336"  # Red
    else:
        status = "Critical"
        color = "#d32f2f"  # Dark Red

    # Set size properties
    size_props = {
        "small": {"font_size": "0.875rem", "padding": "0.25rem 0.5rem", "radius": "0.25rem"},
        "medium": {"font_size": "1rem", "padding": "0.5rem 0.75rem", "radius": "0.375rem"},
        "large": {"font_size": "1.25rem", "padding": "0.75rem 1rem", "radius": "0.5rem"}
    }
    props = size_props.get(size, size_props["medium"])

    # Prepare display text
    display_parts = []
    if label:
        display_parts.append(f"<span style='font-size: {props['font_size']}; opacity: 0.8;'>{label}</span>")

    if show_score:
        display_parts.append(f"<span style='font-size: {props['font_size']}; font-weight: 600;'>{drift_score:.3f}</span>")

    if show_status:
        display_parts.append(f"<span style='background-color: {color}; color: white; padding: 0.125rem 0.5rem; border-radius: {props['radius']}; font-size: {props['font_size']}; font-weight: 600; text-transform: capitalize;'>{status}</span>")

    # Combine with appropriate spacing
    if len(display_parts) == 1:
        content = display_parts[0]
    else:
        # Join with appropriate separators
        content = " ".join(display_parts)

    # Render the component
    st.markdown(f"""
    <span style="
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: {props['padding']};
        border-radius: {props['radius']};
        background-color: rgba(0, 0, 0, 0.02);
    ">
        {content}
    </span>
    """, unsafe_allow_html=True)

def render_drift_badge(
    drift_score: float,
    size: str = "small"
) -> None:
    """
    Render a simple badge showing just the drift score with color coding.

    Args:
        drift_score (float): Drift score value
        size (str): Size of the badge ("small", "medium", "large")
    """
    # Determine color based on score
    if drift_score < 0.3:
        color = "#4caf50"  # Green
    elif drift_score < 0.6:
        color = "#ff9800"  # Orange
    elif drift_score < 0.8:
        color = "#f44336"  # Red
    else:
        color = "#d32f2f"  # Dark Red

    # Set size properties
    size_props = {
        "small": {"font_size": "0.75rem", "padding": "0.2rem 0.4rem", "radius": "0.2rem"},
        "medium": {"font_size": "0.875rem", "padding": "0.3rem 0.5rem", "radius": "0.25rem"},
        "large": {"font_size": "1rem", "padding": "0.4rem 0.6rem", "radius": "0.3rem"}
    }
    props = size_props.get(size, size_props["small"])

    # Render the badge
    st.markdown(f"""
    <span style="
        background-color: {color};
        color: white;
        padding: {props['padding']};
        border-radius: {props['radius']};
        font-size: {props['font_size']};
        font-weight: 600;
    ">
        {drift_score:.3f}
    </span>
    """, unsafe_allow_html=True)

def render_drift_trend_indicator(
    current_score: float,
    previous_score: Optional[float] = None,
    label: Optional[str] = "Drift Trend"
) -> None:
    """
    Render a drift indicator showing trend compared to previous value.

    Args:
        current_score (float): Current drift score
        previous_score (float, optional): Previous drift score for comparison
        label (str, optional): Label to display
    """
    # Determine base color from current score
    if current_score < 0.3:
        base_color = "#4caf50"  # Green
    elif current_score < 0.6:
        base_color = "#ff9800"  # Orange
    elif current_score < 0.8:
        base_color = "#f44336"  # Red
    else:
        base_color = "#d32f2f"  # Dark Red

    # Determine trend indicator
    trend_html = ""
    if previous_score is not None:
        if current_score > previous_score + 0.05:  # Significant increase
            trend_html = "<span style='color: #f44336; margin-left: 0.25rem;'>↑</span>"
        elif current_score < previous_score - 0.05:  # Significant decrease
            trend_html = "<span style='color: #4caf50; margin-left: 0.25rem;'>↓</span>"
        else:  # Stable
            trend_html = "<span style='color: #ff9800; margin-left: 0.25rem;'>→</span>"

    # Format the display
    score_text = f"{current_score:.3f}"
    if label:
        display = f"{label}: {score_text}{trend_html}"
    else:
        display = f"{score_text}{trend_html}"

    # Render
    st.markdown(f"""
    <span style="
        display: inline-flex;
        align-items: center;
        background-color: rgba(0, 0, 0, 0.02);
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
    ">
        <span style="color: {base_color}; font-weight: 600;">{display}</span>
    </span>
    """, unsafe_allow_html=True)

def render_drift_gauge(
    drift_score: float,
    label: str = "Drift Score",
    max_value: float = 1.0,
    show_thresholds: bool = True
) -> None:
    """
    Render a gauge-style drift indicator.

    Args:
        drift_score (float): Current drift score
        label (str): Label for the gauge
        max_value (float): Maximum value for the gauge scale
        show_thresholds (bool): Whether to show threshold markers
    """
    # Calculate percentage for gauge
    percentage = min(100, (drift_score / max_value) * 100)

    # Determine color based on score
    if drift_score < 0.3:
        color = "#4caf50"  # Green
    elif drift_score < 0.6:
        color = "#ff9800"  # Orange
    elif drift_score < 0.8:
        color = "#f44336"  # Red
    else:
        color = "#d32f2f"  # Dark Red

    # Determine status text
    if drift_score < 0.3:
        status = "Low"
    elif drift_score < 0.6:
        status = "Medium"
    elif drift_score < 0.8:
        status = "High"
    else:
        status = "Critical"

    # Render the gauge
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
    ">
        <div style="
            position: relative;
            width: 100px;
            height: 100px;
            margin: 0 auto 0.5rem;
        ">
            <!-- Background circle -->
            <svg width="100" height="100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="#e0e0e0" stroke-width="8"/>
                <!-- Progress arc -->
                <path d="M 50,5
                         L 50,2
                         A 48,48 0 {1 if percentage > 50 else 0} 1
                         {50 + 48 * (percentage/100) if percentage <= 50 else 100 - (50 - 48 * ((percentage-50)/100))},{
                             2 + 48 * (1 - abs((percentage/100) - 0.5) * 2) if percentage <= 50 else
                             98 - 48 * (abs((percentage/100) - 0.5) * 2)
                         }
                       fill=\"none\" stroke=\"{color}\" stroke-width=\"8\"/>
                <!-- Center circle -->
                <circle cx="50" cy="50" r="15" fill="white" stroke="{color}" stroke-width="2"/>
            </svg>
        </div>
        <div style="font-weight: 600; margin-bottom: 0.25rem;">
            {drift_score:.3f}
        </div>
        <div style="font-size: 0.875rem; color: #666;">
            {status}
        </div>
        {f'<div style="font-size: 0.75rem; color: #999; margin-top: 0.25rem;">Thresholds: Low(<0.3) Medium(<0.6) High(<0.8)</div>' if show_thresholds else ''}
    </div>
    """, unsafe_allow_html=True)

def render_drift_sparkline(
    scores: list,
    labels: Optional[list] = None,
    height: int = 50,
    current_color: str = "#1f77b4"
) -> None:
    """
    Render a simple sparkline showing drift score trend.

    Args:
        scores (list): List of drift score values
        labels (list, optional): Labels for each point (e.g., timestamps)
        height (int): Height of the chart in pixels
        current_color (str): Color for the line
    """
    if not scores or len(scores) == 0:
        st.info("No data available")
        return

    # Simple implementation using Streamlit's built-in charting
    import pandas as pd

    # Create DataFrame
    df_data = {"score": scores}
    if labels and len(labels) == len(scores):
        df_data["index"] = list(range(len(scores)))
        df = pd.DataFrame(df_data).set_index("index")
    else:
        df = pd.DataFrame(df_data)

    # Style the chart
    st.line_chart(
        df,
        height=height,
        use_container_width=True
    )

    # Add current value indicator
    current_score = scores[-1] if scores else 0
    if current_score < 0.3:
        status_color = "#4caf50"
    elif current_score < 0.6:
        status_color = "#ff9800"
    elif current_score < 0.8:
        status_color = "#f44336"
    else:
        status_color = "#d32f2f"

    st.markdown(f"""
    <div style="text-align: right; font-size: 0.875rem; margin-top: -0.5rem;">
        <span style="color: {status_color}; font-weight: 600;">
            {current_score:.3f}
        </span>
    </div>
    """, unsafe_allow_html=True)