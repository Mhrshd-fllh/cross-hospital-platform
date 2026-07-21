"""
Great Expectations schema validation for incoming medical image files.
"""
import os
from typing import Tuple
import great_expectations as ge
from great_expectations.core import ExpectationSuite
from great_expectations.dataset import PandasDataset
import numpy as np
from PIL import Image
import io

# Configuration from environment variables with defaults
ALLOWED_EXTENSIONS = {'.dcm', '.nii', '.jpg', '.jpeg', '.zip'}
_canonical_resolution = os.getenv("CANONICAL_RESOLUTION", "320,320")
if not _canonical_resolution:
    _canonical_resolution = "320,320"
CANONICAL_RESOLUTION = tuple(map(int, _canonical_resolution.split(',')))
_min_dimension = os.getenv("MIN_DIMENSION", "64")
if not _min_dimension:
    _min_dimension = "64"
MIN_DIMENSION = int(_min_dimension)
_max_dimension = os.getenv("MAX_DIMENSION", "2048")
if not _max_dimension:
    _max_dimension = "2048"
MAX_DIMENSION = int(_max_dimension)

def validate_image_file(file_bytes: bytes, filename: str) -> Tuple[bool, str]:
    """
    Validate an uploaded image file using Great Expectations.

    Parameters
    ----------
    file_bytes : bytes
        Raw file bytes.
    filename : str
        Original filename (used for extension check).

    Returns
    -------
    Tuple[bool, str]
        (is_valid, error_message). If is_valid is True, error_message is empty.
    """
    # 1. File extension check
    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"

    # 2. Try to open as an image (this will fail for non-image files like .zip, but we allow .zip as per spec)
    # Note: The spec allows .zip, but we cannot validate the contents of a zip here.
    # We'll skip image validation for .zip files and assume they are handled elsewhere.
    if ext == '.zip':
        # For zip files, we only check extension and size (if we wanted to). We'll just pass.
        return True, ""

    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.verify()  # Verify integrity
        # Reopen for further checks because verify() closes the file
        image = Image.open(io.BytesIO(file_bytes))
    except Exception as e:
        return False, f"Corrupt or unreadable image file: {e}"

    # 3. Convert to grayscale and check dimensions
    image = image.convert('L')
    width, height = image.size
    if width < MIN_DIMENSION or height < MIN_DIMENSION:
        return False, f"Image dimensions ({width}x{height}) are below minimum {MIN_DIMENSION}x{MIN_DIMENSION}."
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        return False, f"Image dimensions ({width}x{height}) exceed maximum {MAX_DIMENSION}x{MAX_DIMENSION}."

    # 4. Great Expectations validation: we expect the image to be a 2D array of uint8 in [0,255]
    # Convert to numpy array
    img_array = np.array(image)
    # We expect 2D (grayscale)
    if img_array.ndim != 2:
        return False, f"Expected grayscale (2D) image, got {img_array.ndim}D array."

    # Create a PandasDataset for Great Expectations
    # We'll flatten the image and expect values in [0,255]
    flat = img_array.flatten()
    df = ge.from_pandas(PandasDataset(flat.reshape(-1, 1)), expectation_suite=ExpectationSuite("image_pixel_values"))

    # Define expectations
    df.expect_column_values_to_be_between(column="0", min_value=0, max_value=255)
    # Optionally, we could expect the mean to be in a certain range, but we skip for simplicity.

    # Validate
    results = df.validate()
    if not results.success:
        # Collect error messages
        error_msgs = []
        for result in results.results:
            if not result.success:
                error_msgs.append(result.expectation_config.expectation_type)
        return False, f"Great Expectations validation failed: {', '.join(error_msgs)}"

    return True, ""