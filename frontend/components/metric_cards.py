"""
Metric card component for the Cross-Hospital Generalization Platform.
Provides a reusable component for displaying key metrics with optional delta indicators.
"""

import streamlit as st

def render_metric_card(title, value, delta=None, delta_color="normal", help_text=None):
    """
    Render a metric card component.

    Args:
        title (str): The title of the metric
        value: The value to display (can be string, number, etc.)
        delta (str, optional): The delta value to display (e.g., "+5%", "-10")
        delta_color (str): Color of the delta ("normal", "inverse", "off")
        help_text (str, optional): Help text to show on hover
    """
    # Use Streamlit's built-in metric component with custom styling
    st.metric(
        label=title,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text
    )

def render_metric_card_custom(title, value, delta=None, delta_color="#ffffff",
                             bg_color="#1f77b4", icon=None, help_text=None):
    """
    Render a custom metric card with more styling options.

    Args:
        title (str): The title of the metric
        value: The value to display
        delta (str, optional): The delta value to display
        delta_color (str): Color of the delta text
        bg_color (str): Background color of the card
        icon (str, optional): Emoji or icon to display
        help_text (str, optional): Help text to show on hover
    """
    # Determine delta display
    delta_html = ""
    if delta is not None:
        delta_html = f'<div style="font-size: 0.9rem; color: {delta_color}; margin-top: 0.5rem;">{delta}</div>'

    # Determine icon display
    icon_html = f'<div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>' if icon else ''

    # Create the card
    st.markdown(f"""
    <div style="
        background-color: {bg_color};
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        {icon_html}
        <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">
            {title}
        </div>
        <div style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0;">
            {value}
        </div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

    # Add help text if provided (using Streamlit's tooltip would be better but requires more complex implementation)
    if help_text:
        st.caption(help_text)

def render_metric_grid(metrics, columns=3):
    """
    Render a grid of metric cards.

    Args:
        metrics (list): List of dictionaries with keys: title, value, delta, delta_color, help_text
        columns (int): Number of columns in the grid
    """
    cols = st.columns(columns)
    for i, metric in enumerate(metrics):
        with cols[i % columns]:
            render_metric_card(
                title=metric.get("title", ""),
                value=metric.get("value", ""),
                delta=metric.get("delta"),
                delta_color=metric.get("delta_color", "normal"),
                help_text=metric.get("help_text")
            )