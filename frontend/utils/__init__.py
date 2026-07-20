"""
Utility functions for the Cross-Hospital Generalization Platform frontend.
"""

import streamlit as st
import base64
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import json

def format_timestamp(timestamp: Union[datetime, str, None],
                    format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a timestamp for display.

    Args:
        timestamp: datetime object, ISO string, or None
        format_str: Format string for strftime

    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        return "N/A"

    if isinstance(timestamp, str):
        try:
            # Try to parse ISO format
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            return timestamp  # Return as-is if not a valid ISO string

    if isinstance(timestamp, datetime):
        return timestamp.strftime(format_str)

    return str(timestamp)

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string.

    Args:
        json_str: JSON string to parse
        default: Default value to return if parsing fails

    Returns:
        Parsed JSON object or default value
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Safely serialize object to JSON string.

    Args:
        obj: Object to serialize
        default: Default JSON string to return if serialization fails

    Returns:
        JSON string or default value
    """
    try:
        return json.dumps(obj)
    except (TypeError, ValueError):
        return default

def get_download_link(data: bytes, filename: str, text: str = "Download") -> str:
    """
    Generate a download link for binary data.

    Args:
        data: Binary data to download
        filename: Name of the file to download
        text: Link text to display

    Returns:
        HTML string for download link
    """
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:file/octet-stream;base64,{b64}" download="{filename}">{text}</a>'
    return href

def get_image_download_link(image_data: bytes, filename: str, text: str = "Download Image") -> str:
    """
    Generate a download link for image data.

    Args:
        image_data: Binary image data
        filename: Name of the file to download
        text: Link text to display

    Returns:
        HTML string for download link
    """
    return get_download_link(image_data, filename, text)

def get_csv_download_link(dataframe: pd.DataFrame, filename: str, text: str = "Download CSV") -> str:
    """
    Generate a download link for a pandas DataFrame as CSV.

    Args:
        dataframe: Pandas DataFrame to convert to CSV
        filename: Name of the file to download
        text: Link text to display

    Returns:
        HTML string for download link
    """
    csv = dataframe.to_csv(index=False)
    return get_download_link(csv.encode(), filename, text)

def get_json_download_link(data: Dict[Any, Any], filename: str, text: str = "Download JSON") -> str:
    """
    Generate a download link for JSON data.

    Args:
        data: Dictionary to convert to JSON
        filename: Name of the file to download
        text: Link text to display

    Returns:
        HTML string for download link
    """
    json_str = safe_json_dumps(data)
    return get_download_link(json_str.encode(), filename, text)

def show_spinner_while_loading(func):
    """
    Decorator to show a spinner while a function is executing.

    Args:
        func: Function to decorate

    Returns:
        Wrapped function
    """
    def wrapper(*args, **kwargs):
        with st.spinner("Loading..."):
            return func(*args, **kwargs)
    return wrapper

def show_error_message(message: str, details: Optional[str] = None):
    """
    Show an error message to the user.

    Args:
        message: Main error message
        details: Optional detailed error information
    """
    st.error(message)
    if details:
        with st.expander("See details"):
            st.code(details)

def show_success_message(message: str):
    """
    Show a success message to the user.

    Args:
        message: Success message to display
    """
    st.success(message)

def show_warning_message(message: str):
    """
    Show a warning message to the user.

    Args:
        message: Warning message to display
    """
    st.warning(message)

def show_info_message(message: str):
    """
    Show an info message to the user.

    Args:
        message: Info message to display
    """
    st.info(message)

def create_empty_state(message: str, icon: str = "📭",
                      button_text: Optional[str] = None,
                      button_callback: Optional[callable] = None) -> bool:
    """
    Create an empty state display.

    Args:
        message: Message to display
        icon: Icon to display
        button_text: Optional button text
        button_callback: Optional callback function for button

    Returns:
        True if button was clicked, False otherwise
    """
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 3rem;
        color: #6c757d;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">{icon}</div>
        <h3>{message}</h3>
    </div>
    """, unsafe_allow_html=True)

    if button_text and button_callback:
        return st.button(button_text, on_click=button_callback)
    return False

def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email string to validate

    Returns:
        True if valid email format, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        suffix: Suffix to append when truncating

    Returns:
        Truncated text string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def get_status_color(status: str) -> str:
    """
    Get color for a status value.

    Args:
        status: Status string (e.g., 'healthy', 'warning', 'error')

    Returns:
        Hex color code
    """
    status_colors = {
        'healthy': '#4caf50',
        'normal': '#4caf50',
        'online': '#4caf50',
        'active': '#4caf50',
        'pass': '#4caf50',
        'completed': '#4caf50',
        'warning': '#ff9800',
        'degraded': '#ff9800',
        'pending': '#ff9800',
        'processing': '#2196f3',
        'error': '#f44336',
        'offline': '#f44336',
        'inactive': '#f44336',
        'fail': '#f44336',
        'failed': '#f44336',
        'critical': '#d32f2f',
        'unknown': '#9e9e9e',
        'disabled': '#9e9e9e'
    }
    return status_colors.get(status.lower(), '#9e9e9e')

def get_status_icon(status: str) -> str:
    """
    Get icon for a status value.

    Args:
        status: Status string

    Returns:
        Emoji icon string
    """
    status_icons = {
        'healthy': '✅',
        'normal': '✅',
        'online': '✅',
        'active': '✅',
        'pass': '✅',
        'completed': '✅',
        'warning': '⚠️',
        'degraded': '⚠️',
        'pending': '⚠️',
        'processing': '🔄',
        'error': '❌',
        'offline': '❌',
        'inactive': '❌',
        'fail': '❌',
        'failed': '❌',
        'critical': '🚨',
        'unknown': '❓',
        'disabled': '⚫'
    }
    return status_icons.get(status.lower(), '❓')

def safe_get_nested(data: Dict[Any, Any], keys: List[Any], default: Any = None) -> Any:
    """
    Safely get a nested value from a dictionary.

    Args:
        data: Dictionary to search
        keys: List of keys representing the path to the value
        default: Default value to return if any key is missing

    Returns:
        Value at the nested path or default
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
    """
    Pluralize a word based on count.

    Args:
        count: Number of items
        singular: Singular form of the word
        plural: Plural form of the word (defaults to singular + 's')

    Returns:
        Properly pluralized word string
    """
    if plural is None:
        plural = singular + 's'
    return plural if count != 1 else singular

# Constants
DEFAULT_PAGE_SIZE = 20
MAX_FILE_SIZE_MB = 50
SUPPORTED_IMAGE_FORMATS = ['jpg', 'jpeg', 'png', 'dicom', 'dcm', 'tiff', 'tif']
SUPPORTED_DOCUMENT_FORMATS = ['pdf', 'txt', 'json', 'csv']