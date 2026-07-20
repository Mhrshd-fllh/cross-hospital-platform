"""
Image preview component for the Cross-Hospital Generalization Platform.
Provides reusable components for displaying medical images with zoom, pan, and comparison capabilities.
"""

import streamlit as st
from PIL import Image
import io
import base64

def render_image_preview(image_data, caption=None, width=None, use_column_width=False):
    """
    Render a simple image preview.

    Args:
        image_data: Image data (can be PIL Image, bytes, file path, or uploaded file object)
        caption (str, optional): Caption to display below the image
        width (int, optional): Width in pixels (if None, uses container width)
        use_column_width (bool): Whether to use full column width
    """
    try:
        # Handle different input types
        if isinstance(image_data, str):
            # File path
            image = Image.open(image_data)
        elif isinstance(image_data, bytes):
            # Raw bytes
            image = Image.open(io.BytesIO(image_data))
        elif hasattr(image_data, 'read'):
            # File-like object (including Streamlit's UploadedFile)
            image = Image.open(image_data)
            # Reset file pointer for potential later use
            if hasattr(image_data, 'seek'):
                image_data.seek(0)
        elif isinstance(image_data, Image.Image):
            # Already a PIL Image
            image = image_data
        else:
            st.error("Unsupported image data format")
            return

        # Display the image
        if use_column_width:
            st.image(image, caption=caption, use_column_width=True)
        elif width:
            st.image(image, caption=caption, width=width)
        else:
            st.image(image, caption=caption)

    except Exception as e:
        st.error(f"Error displaying image: {str(e)}")

def render_image_comparison(original_image, modified_image, caption1="Original",
                          caption2="Modified", show_slider=False):
    """
    Render a side-by-side image comparison.

    Args:
        original_image: Original image data
        modified_image: Modified image data
        caption1 (str): Caption for original image
        caption2 (str): Caption for modified image
        show_slider (bool): Whether to show a slider for blending (not fully implemented in basic version)
    """
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{caption1}**")
        render_image_preview(original_image, use_column_width=True)

    with col2:
        st.markdown(f"**{caption2}**")
        render_image_preview(modified_image, use_column_width=True)

    if show_slider:
        # Note: A true slider-based comparison would require more advanced components
        # This is a placeholder for future enhancement
        st.caption("💡 Slide comparison feature coming soon")

def render_image_grid(images, captions=None, cols=3):
    """
    Render a grid of images.

    Args:
        images (list): List of image data
        captions (list, optional): List of captions for each image
        cols (int): Number of columns in the grid
    """
    if not images:
        st.info("No images to display")
        return

    # Prepare captions
    if captions is None:
        captions = [""] * len(images)
    elif len(captions) != len(images):
        # Pad or truncate to match
        if len(captions) < len(images):
            captions.extend([""] * (len(images) - len(captions)))
        else:
            captions = captions[:len(images)]

    # Create rows
    for i in range(0, len(images), cols):
        row_images = images[i:i+cols]
        row_captions = captions[i:i+cols]
        columns = st.columns(len(row_images))

        for j, (img, caption) in enumerate(zip(row_images, row_captions)):
            with columns[j]:
                if caption:
                    st.markdown(f"**{caption}**")
                render_image_preview(img, use_column_width=True)

def render_image_with_overlay(base_image, overlay_image=None, opacity=0.5):
    """
    Render an image with an optional overlay (e.g., heatmap, segmentation mask).

    Args:
        base_image: Base image data
        overlay_image: Overlay image data (same dimensions as base)
        opacity (float): Opacity of the overlay (0.0 to 1.0)
    """
    # Note: This would require image processing to blend the images
    # For now, we'll show them side by side with a note
    st.info("💡 Image overlay feature requires advanced image processing - coming soon")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Base Image**")
        render_image_preview(base_image, use_column_width=True)

    with col2:
        if overlay_image:
            st.markdown("**Overlay**")
            render_image_preview(overlay_image, use_column_width=True)
        else:
            st.info("No overlay provided")

def render_image_zoom_pan(image_data, zoom_level=1.0):
    """
    Render an image with zoom and pan capabilities.

    Args:
        image_data: Image data
        zoom_level (float): Initial zoom level (1.0 = original size)
    """
    # Note: True zoom/pan would require frontend JavaScript components
    # For now, we'll display the image and note the feature
    st.info("💡 Zoom and pan features require advanced image viewer - coming soon")
    render_image_preview(image_data, use_column_width=True)

def render_dicom_viewer_placeholder():
    """
    Render a placeholder for a DICOM viewer with typical controls.
    """
    st.info("🏥 DICOM Viewer - Feature Coming Soon")

    # Show typical DICOM viewer controls as placeholders
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.slider("Window Width", 0, 4000, 400, disabled=True)
    with col2:
        st.slider("Window Level", -1000, 1000, 40, disabled=True)
    with col3:
        st.selectbox("Modality", ["CT", "MR", "X-Ray", "Ultrasound"], index=0, disabled=True)
    with col4:
        st.selectbox("Series", ["Series 1", "Series 2", "Series 3"], index=0, disabled=True)

    # Show a placeholder image
    st.image("https://via.placeholder.com/400x300?text=DICOM+Image+Placeholder",
             caption="DICOM Image Placeholder", use_column_width=True)

def render_medical_image_info(image_data):
    """
    Display metadata information about a medical image.

    Args:
        image_data: Image data (will attempt to extract metadata if DICOM)
    """
    st.subheader("Image Information")

    # In a real implementation, this would extract DICOM metadata
    # For now, we'll show placeholder information
    info = {
        "Filename": "sample_image.dcm",
        "Format": "DICOM",
        "Dimensions": "512 x 512 pixels",
        "Bits Allocated": "16",
        "Modality": "CT",
        "Study Date": "2024-01-15",
        "Patient ID": "MRN123456",
        "Study Description": "Chest CT with Contrast"
    }

    for key, value in info.items():
        st.text(f"{key}: {value}")

# Helper function to create a placeholder image for demonstration
def create_placeholder_image(width=400, height=300, color=(200, 200, 200), text="Image"):
    """
    Create a placeholder image for demonstration purposes.

    Args:
        width (int): Image width in pixels
        height (int): Image height in pixels
        color (tuple): Background color as (R, G, B)
        text (str): Text to display in the center

    Returns:
        PIL Image: The generated placeholder image
    """
    from PIL import Image, ImageDraw, ImageFont

    # Create image
    image = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(image)

    # Try to use a default font, fallback to default if not available
    try:
        # Try to get a font (this might fail on some systems)
        font = ImageFont.truetype("arial.ttf", size=20)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text position
    text_width, text_height = draw.textsize(text, font=font)
    position = ((width - text_width) // 2, (height - text_height) // 2)

    # Draw text
    draw.text(position, text, fill=(255, 255, 255), font=font)

    return image