"""
Tables component for the Cross-Hospital Generalization Platform.
Provides reusable components for displaying data tables with enhanced formatting.
"""

import streamlit as st
import pandas as pd

def render_dataframe(data, height=None, use_container_width=True, hide_index=True,
                    column_config=None, selected_rows=None, on_select=None):
    """
    Render a dataframe with enhanced formatting options.

    Args:
        data (pd.DataFrame): Data to display
        height (int, optional): Height in pixels
        use_container_width (bool): Whether to use full container width
        hide_index (bool): Whether to hide the index column
        column_config (dict, optional): Configuration for specific columns
        selected_rows (list, optional): List of row indices to pre-select
        on_select (str, optional): What to do when rows are selected ('rerun' or None)
    """
    # Configure selection if requested
    selection_mode = "single-row" if on_select == "rerun" else None
    on_select_action = "rerun" if on_select == "rerun" else None

    st.dataframe(
        data,
        height=height,
        use_container_width=use_container_width,
        hide_index=hide_index,
        column_config=column_config,
        selection_mode=selection_mode,
        on_select=on_select_action
    )

    # Return selected rows if needed
    if on_select == "rerun":
        return st.session_state.get(f"dataframe_selection_{id(data)}", [])
    return None

def render_metric_table(data, title=None, highlight_column=None,
                       highlight_condition=None, highlight_color="#ffebee"):
    """
    Render a table with conditional highlighting.

    Args:
        data (pd.DataFrame): Data to display
        title (str, optional): Title for the table
        highlight_column (str, optional): Column to apply conditional formatting to
        highlight_condition (callable, optional): Function that returns True for cells to highlight
        highlight_color (str): Background color for highlighted cells
    """
    if title:
        st.subheader(title)

    # Apply styling if conditions are met
    if highlight_column and highlight_condition and highlight_column in data.columns:
        def highlight_rows(row):
            if highlight_condition(row[highlight_column]):
                return ['background-color: {}'.format(highlight_color)] * len(row)
            return [''] * len(row)

        styled_df = data.style.apply(highlight_rows, axis=1)
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.dataframe(data, use_container_width=True)

def render_summary_table(data, title=None, col1_label="Metric", col2_label="Value"):
    """
    Render a simple two-column summary table.

    Args:
        data (dict): Dictionary of key-value pairs to display
        title (str, optional): Title for the table
        col1_label (str): Label for first column
        col2_label (str): Label for second column
    """
    if title:
        st.subheader(title)

    # Convert to DataFrame for display
    df = pd.DataFrame(list(data.items()), columns=[col1_label, col2_label])
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_pivot_table(data, index, columns, values, aggfunc='mean',
                      title=None, fill_value=0):
    """
    Render a pivot table.

    Args:
        data (pd.DataFrame): Source data
        index (str or list): Column(s) to use as index
        columns (str or list): Column(s) to use as columns
        values (str): Column to aggregate
        aggfunc (str or callable): Aggregation function
        title (str, optional): Title for the table
        fill_value: Value to replace NaN with
    """
    if title:
        st.subheader(title)

    pivot_df = data.pivot_table(
        index=index,
        columns=columns,
        values=values,
        aggfunc=aggfunc,
        fill_value=fill_value
    )

    st.dataframe(pivot_df, use_container_width=True)

def render_ranking_table(data, rank_column, ascending=True, top_n=None,
                        title=None, show_rank=True):
    """
    Render a ranking table.

    Args:
        data (pd.DataFrame): Data to rank and display
        rank_column (str): Column to rank by
        ascending (bool): Whether to sort in ascending order (True) or descending (False)
        top_n (int, optional): Number of top rows to show
        title (str, optional): Title for the table
        show_rank (bool): Whether to show a rank column
    """
    if title:
        st.subheader(title)

    # Sort the data
    sorted_data = data.sort_values(by=rank_column, ascending=ascending)

    # Take top N if specified
    if top_n is not None:
        sorted_data = sorted_data.head(top_n)

    # Add rank column if requested
    if show_rank:
        sorted_data = sorted_data.reset_index(drop=True)
        sorted_data.insert(0, 'Rank', range(1, len(sorted_data) + 1))

    st.dataframe(sorted_data, use_container_width=True, hide_index=True)

def render_comparison_table(base_data, compare_data, key_column,
                          value_columns, title=None):
    """
    Render a comparison table showing base vs compare values.

    Args:
        base_data (pd.DataFrame): Base data
        compare_data (pd.DataFrame): Comparison data
        key_column (str): Column to join on
        value_columns (list): Columns to compare
        title (str, optional): Title for the table
    """
    if title:
        st.subheader(title)

    # Merge the dataframes
    merged = pd.merge(
        base_data,
        compare_data,
        on=key_column,
        suffixes=('_base', '_compare'),
        how='outer'
    )

    # Calculate differences
    for col in value_columns:
        base_col = f"{col}_base"
        compare_col = f"{col}_compare"
        diff_col = f"{col}_diff"

        if base_col in merged.columns and compare_col in merged.columns:
            merged[diff_col] = merged[compare_col] - merged[base_col]

    # Reorder columns for better readability
    cols = [key_column]
    for col in value_columns:
        cols.extend([f"{col}_base", f"{col}_compare", f"{col}_diff"])

    # Filter to only columns that exist
    cols = [c for c in cols if c in merged.columns]

    st.dataframe(merged[cols], use_container_width=True, hide_index=True)