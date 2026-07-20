"""
Charts component for the Cross-Hospital Generalization Platform.
Provides reusable components for creating various types of charts using Plotly.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def render_line_chart(data, x, y, title=None, color=None, height=400, **kwargs):
    """
    Render a line chart.

    Args:
        data (pd.DataFrame): Data to plot
        x (str): Column name for x-axis
        y (str): Column name for y-axis (can be list for multiple lines)
        title (str, optional): Chart title
        color (str, optional): Column name for color encoding
        height (int): Chart height in pixels
        **kwargs: Additional arguments to pass to px.line
    """
    fig = px.line(data, x=x, y=y, color=color, title=title, height=height, **kwargs)
    st.plotly_chart(fig, use_container_width=True)

def render_bar_chart(data, x, y, title=None, color=None, height=400, horizontal=False, **kwargs):
    """
    Render a bar chart.

    Args:
        data (pd.DataFrame): Data to plot
        x (str): Column name for x-axis
        y (str): Column name for y-axis
        title (str, optional): Chart title
        color (str, optional): Column name for color encoding
        height (int): Chart height in pixels
        horizontal (bool): Whether to orient bars horizontally
        **kwargs: Additional arguments to pass to px.bar
    """
    if horizontal:
        fig = px.bar(data, x=y, y=x, color=color, title=title, height=height, **kwargs)
    else:
        fig = px.bar(data, x=x, y=y, color=color, title=title, height=height, **kwargs)
    st.plotly_chart(fig, use_container_width=True)

def render_pie_chart(data, names, values, title=None, height=400, **kwargs):
    """
    Render a pie chart.

    Args:
        data (pd.DataFrame): Data to plot
        names (str): Column name for slice labels
        values (str): Column name for slice values
        title (str, optional): Chart title
        height (int): Chart height in pixels
        **kwargs: Additional arguments to pass to px.pie
    """
    fig = px.pie(data, names=names, values=values, title=title, height=height, **kwargs)
    st.plotly_chart(fig, use_container_width=True)

def render_scatter_plot(data, x, y, title=None, color=None, size=None, height=400, **kwargs):
    """
    Render a scatter plot.

    Args:
        data (pd.DataFrame): Data to plot
        x (str): Column name for x-axis
        y (str): Column name for y-axis
        title (str, optional): Chart title
        color (str, optional): Column name for color encoding
        size (str, optional): Column name for point size
        height (int): Chart height in pixels
        **kwargs: Additional arguments to pass to px.scatter
    """
    fig = px.scatter(data, x=x, y=y, color=color, size=size, title=title, height=height, **kwargs)
    st.plotly_chart(fig, use_container_width=True)

def render_histogram(data, x, title=None, color=None, height=400, **kwargs):
    """
    Render a histogram.

    Args:
        data (pd.DataFrame): Data to plot
        x (str): Column name for values
        title (str, optional): Chart title
        color (str, optional): Column name for color encoding
        height (int): Chart height in pixels
        **kwargs: Additional arguments to pass to px.histogram
    """
    fig = px.histogram(data, x=x, color=color, title=title, height=height, **kwargs)
    st.plotly_chart(fig, use_container_width=True)

def render_area_chart(data, x, y, title=None, color=None, height=400, **kwargs):
    """
    Render an area chart.

    Args:
        data (pd.DataFrame): Data to plot
        x (str): Column name for x-axis
        y (str): Column name for y-axis
        title (str, optional): Chart title
        color (str, optional): Column name for color encoding
        height (int): Chart height in pixels
        **kwargs: Additional arguments to pass to px.area
    """
    fig = px.area(data, x=x, y=y, color=color, title=title, height=height, **kwargs)
    st.plotly_chart(fig, use_container_width=True)

def render_heatmap(data, x, y, z, title=None, height=500, **kwargs):
    """
    Render a heatmap.

    Args:
        data (pd.DataFrame): Data to plot
        x (str): Column name for x-axis
        y (str): Column name for y-axis
        z (str): Column name for values
        title (str, optional): Chart title
        height (int): Chart height in pixels
        **kwargs: Additional arguments to pass to px.density_heatmap or go.Heatmap
    """
    # For simplicity, we'll use density_heatmap if x and y are continuous
    # Otherwise we'd need to pivot the data for go.Heatmap
    try:
        fig = px.density_heatmap(data, x=x, y=y, z=z, title=title, height=height, **kwargs)
    except:
        # Fallback to regular heatmap if needed
        fig = go.Figure(data=go.Heatmap(
            z=data[z].values,
            x=data[x].unique(),
            y=data[y].unique(),
            colorscale='Viridis'
        ))
        fig.update_layout(title=title, height=height)
    st.plotly_chart(fig, use_container_width=True)

def render_multi_line_chart(data, x, y_list, title=None, height=400, **kwargs):
    """
    Render a multi-line chart (multiple y-values sharing the same x-axis).

    Args:
        data (pd.DataFrame): Data to plot
        x (str): Column name for x-axis
        y_list (list): List of column names for y-axis values
        title (str, optional): Chart title
        height (int): Chart height in pixels
        **kwargs: Additional arguments to pass to go.Figure
    """
    fig = go.Figure()

    for i, y_col in enumerate(y_list):
        fig.add_trace(go.Scatter(
            x=data[x],
            y=data[y_col],
            mode='lines',
            name=y_col,
            line=dict(width=2)
        ))

    fig.update_layout(
        title=title,
        xaxis_title=x,
        yaxis_title="Value",
        height=height,
        **kwargs
    )

    st.plotly_chart(fig, use_container_width=True)

def render_gauge(value, title, min_val=0, max_val=100, thresholds=None, height=250):
    """
    Render a gauge chart.

    Args:
        value (float): The value to display
        title (str): Title for the gauge
        min_val (float): Minimum value of the gauge
        max_val (float): Maximum value of the gauge
        thresholds (list, optional): List of threshold values for color changes
        height (int): Chart height in pixels
    """
    # Default thresholds (green, yellow, red)
    if thresholds is None:
        thresholds = [min_val + (max_val - min_val) * 0.6,  # Yellow threshold
                     min_val + (max_val - min_val) * 0.8]   # Red threshold

    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 20}},
        gauge = {
            'axis': {'range': [min_val, max_val], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [min_val, thresholds[0]], 'color': "lightgreen"},
                {'range': [thresholds[0], thresholds[1]], 'color': "yellow"},
                {'range': [thresholds[1], max_val], 'color': "lightcoral"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': thresholds[1]
            }
        }
    ))

    fig.update_layout(height=height)
    st.plotly_chart(fig, use_container_width=True)