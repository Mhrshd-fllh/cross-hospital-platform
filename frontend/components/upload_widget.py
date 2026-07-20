"""
Upload widget component for the Cross-Hospital Generalization Platform.
Provides reusable components for file upload with drag-and-drop support.
"""

import streamlit as st
import os
from pathlib import Path

def render_upload_widget(label="Upload Files", accepted_types=None, multiple=False,
                        help_text=None, key=None):
    """
    Render a file upload widget with drag-and-drop support.

    Args:
        label (str): Label for the upload widget
        accepted_types (list, optional): List of accepted file extensions (e.g., ['jpg', 'png', 'dicom'])
        multiple (bool): Whether to allow multiple file selection
        help_text (str, optional): Help text to display below the widget
        key (str, optional): Unique key for the widget

    Returns:
        Uploaded file(s) or None if no file uploaded
    """
    # Set default accepted types if not provided
    if accepted_types is None:
        accepted_types = ['jpg', 'jpeg', 'png', 'dicom', 'dcm']

    # Normalize accepted types (remove dots if present)
    normalized_types = []
    for ext in accepted_types:
        if isinstance(ext, str):
            ext = ext.lower().lstrip('.')
            if ext:
                normalized_types.append(ext)

    # Upload widget
    uploaded_files = st.file_uploader(
        label=label,
        type=normalized_types,
        accept_multiple_files=multiple,
        help=help_text,
        key=key
    )

    # Show file info if uploaded
    if uploaded_files:
        if multiple:
            if uploaded_files:
                st.caption(f"{len(uploaded_files)} file(s) selected:")
                for file in uploaded_files:
                    file_size = len(file.getvalue()) if hasattr(file, 'getvalue') else 0
                    size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
                    st.caption(f"• {file.name} ({size_str})")
        else:
            if uploaded_files:
                file_size = len(uploaded_files.getvalue()) if hasattr(uploaded_files, 'getvalue') else 0
                size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
                st.caption(f"Selected: {uploaded_files.name} ({size_str})")

    return uploaded_files

def render_image_upload_widget(label="Upload Medical Image", key=None):
    """
    Render a specialized upload widget for medical images.

    Args:
        label (str): Label for the upload widget
        key (str, optional): Unique key for the widget

    Returns:
        Uploaded file or None if no file uploaded
    """
    return render_upload_widget(
        label=label,
        accepted_types=['jpg', 'jpeg', 'png', 'dicom', 'dcm', 'tiff', 'tif'],
        multiple=False,
        help_text="Supported formats: JPG, JPEG, PNG, DICOM, TIFF",
        key=key
    )

def render_multi_image_upload_widget(label="Upload Medical Images", key=None):
    """
    Render an upload widget for multiple medical images.

    Args:
        label (str): Label for the upload widget
        key (str, optional): Unique key for the widget

    Returns:
        List of uploaded files or empty list if none uploaded
    """
    files = render_upload_widget(
        label=label,
        accepted_types=['jpg', 'jpeg', 'png', 'dicom', 'dcm', 'tiff', 'tif'],
        multiple=True,
        help_text="Supported formats: JPG, JPEG, PNG, DICOM, TIFF (multiple files allowed)",
        key=key
    )

    return files if files else []

def render_upload_with_preview(label="Upload Image", preview_height=200, key=None):
    """
    Render an upload widget with image preview capability.

    Args:
        label (str): Label for the upload widget
        preview_height (int): Height of the preview area in pixels
        key (str, optional): Unique key for the widget

    Returns:
        Tuple of (uploaded_file, preview_data) where preview_data is None if no image or not previewable
    """
    uploaded_file = render_upload_widget(
        label=label,
        accepted_types=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
        multiple=False,
        help_text="Supported image formats: JPG, JPEG, PNG, GIF, BMP, WebP",
        key=key
    )

    preview_data = None
    if uploaded_file and uploaded_file.type.startswith('image/'):
        # For now, we'll just return the file - actual preview would be handled in the calling code
        # In a full implementation, we might read and encode the image data here
        pass

    return uploaded_file, preview_data

def render_upload_progress_bar(progress_value, text=None):
    """
    Render an upload progress bar.

    Args:
        progress_value (float): Progress value between 0.0 and 1.0
        text (str, optional): Text to display alongside the progress bar
    """
    st.progress(progress_value)
    if text:
        st.caption(text)

def validate_file_size(uploaded_file, max_size_mb=10):
    """
    Validate that an uploaded file is within the size limit.

    Args:
        uploaded_file: The uploaded file object from Streamlit
        max_size_mb (float): Maximum allowed size in megabytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    if uploaded_file is None:
        return True, "No file uploaded"

    # Get file size
    file_size_bytes = len(uploaded_file.getvalue()) if hasattr(uploaded_file, 'getvalue') else 0
    file_size_mb = file_size_bytes / (1024 * 1024)

    if file_size_mb > max_size_mb:
        return False, f"File size ({file_size_mb:.1f} MB) exceeds maximum allowed size ({max_size_mb} MB)"
    else:
        return True, f"File size: {file_size_mb:.1f} MB"