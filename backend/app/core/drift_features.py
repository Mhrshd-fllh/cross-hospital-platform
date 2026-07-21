"""
Feature extraction module for drift detection.
Implements handcrafted features: intensity histogram, FFT band energy,
LBP texture, and Laplacian variance sharpness.
"""

import numpy as np
from PIL import Image
import io
from scipy import fftpack
from skimage.feature import local_binary_pattern
from scipy import ndimage


def load_and_preprocess(image_bytes: bytes, target_size: tuple[int, int] = (320, 320)) -> np.ndarray:
    """
    Decode image bytes, convert to grayscale, resize, and normalize to [0, 1].

    Parameters
    ----------
    image_bytes : bytes
        Raw image bytes (e.g., from file upload).
    target_size : tuple[int, int], default (320, 320)
        Desired output size (width, height).

    Returns
    -------
    np.ndarray
        Grayscale image as float32 array in range [0, 1], shape (H, W).

    Raises
    ------
    ValueError
        If the image cannot be decoded or is empty.
    """
    try:
        # Open image with PIL and convert to grayscale
        img = Image.open(io.BytesIO(image_bytes)).convert('L')
    except Exception as e:
        raise ValueError(f"Unable to decode image: {e}") from e

    # Resize
    img_resized = img.resize(target_size, Image.Resampling.BILINEAR)
    # Convert to numpy array and normalize to [0, 1]
    img_array = np.clip(np.array(img_resized, dtype=np.float32) / 255.0, 0.0, 1.0)
    return img_array


def _validate_image(image: np.ndarray) -> None:
    """Validate that the input is a 2D grayscale float32 array."""
    if image.ndim != 2:
        raise ValueError(f"Expected 2D grayscale image, got shape {image.shape}")
    if not np.issubdtype(image.dtype, np.floating):
        raise ValueError(f"Expected floating point image, got dtype {image.dtype}")
    # Note: image values are expected to be in [0, 1] due to preprocessing in load_and_preprocess.


def extract_histogram_features(image: np.ndarray, bins: int = 64) -> np.ndarray:
    """
    Compute intensity histogram of the grayscale image.

    Parameters
    ----------
    image : np.ndarray
        Grayscale image as float32 array in [0, 1], shape (H, W).
    bins : int, default 64
        Number of bins for the histogram.

    Returns
    -------
    np.ndarray
        Histogram counts (length = bins), normalized to sum to 1.
    """
    _validate_image(image)
    # Flatten image and compute histogram
    hist, _ = np.histogram(image, bins=bins, range=(0.0, 1.0), density=False)
    # Normalize to get a probability distribution
    hist = hist.astype(np.float32)
    if hist.sum() > 0:
        hist /= hist.sum()
    return hist


def extract_fft_band_features(image: np.ndarray, n_bands: int = 8) -> np.ndarray:
    """
    Compute energy in frequency bands of the 2D Fourier spectrum.

    The image is transformed via FFT, the magnitude spectrum is computed,
    and the frequency radius is binned into `n_bands` logarithmically spaced
    bins from DC to Nyquist.

    Parameters
    ----------
    image : np.ndarray
        Grayscale image as float32 array in [0, 1], shape (H, W).
    n_bands : int, default 8
        Number of frequency bands.

    Returns
    -------
    np.ndarray
        Energy sum per band (length = n_bands), normalized to sum to 1.
    """
    _validate_image(image)
    # Compute FFT2 and shift zero frequency to center
    fft2 = fftpack.fft2(image)
    fft_shift = fftpack.fftshift(fft2)
    magnitude = np.abs(fft_shift)
    # Compute frequency coordinates
    h, w = image.shape
    # Frequency bins in cycles/pixel
    freq_y = fftpack.fftfreq(h)[:, None]
    freq_x = fftpack.fftfreq(w)[None, :]
    freq_y = fftpack.fftshift(freq_y)
    freq_x = fftpack.fftshift(freq_x)
    # Radius from DC
    radius = np.sqrt(freq_x**2 + freq_y**2)
    # Max radius (Nyquist) is 0.5
    max_radius = 0.5
    # Create bins logarithmically from a small epsilon to max_radius
    # Avoid log(0) by starting at min radius > 0
    min_radius = 1e-5
    bins = np.logspace(np.log10(min_radius), np.log10(max_radius), num=n_bands + 1)
    # Digitize radii into bins
    # Flatten arrays for histogram
    radii_flat = radius.ravel()
    magnitude_flat = magnitude.ravel()
    # Which bin each pixel belongs to (0 to n_bands-1)
    bin_indices = np.digitize(radii_flat, bins) - 1
    # Ensure indices are within [0, n_bands-1]
    bin_indices = np.clip(bin_indices, 0, n_bands - 1)
    # Sum magnitude in each bin
    band_energy = np.zeros(n_bands, dtype=np.float32)
    for i in range(n_bands):
        mask = bin_indices == i
        band_energy[i] = magnitude_flat[mask].sum()
    # Normalize
    if band_energy.sum() > 0:
        band_energy /= band_energy.sum()
    return band_energy


def extract_lbp_features(image: np.ndarray, radius: int = 2, n_points: int = 16) -> np.ndarray:
    """
    Compute Local Binary Pattern (LBP) histogram.

    Parameters
    ----------
    image : np.ndarray
        Grayscale image as float32 array in [0, 1], shape (H, W).
    radius : int, default 2
        Radius of the circle for LBP.
    n_points : int, default 16
        Number of points on the circle.

    Returns
    -------
    np.ndarray
        Histogram of LBP codes (length = n_points + 2), normalized to sum to 1.
        The +2 accounts for uniform patterns and the catch-all bin.
    """
    _validate_image(image)
    # Convert to uint8 for skimage LBP (expects uint8)
    img_uint8 = (image * 255).astype(np.uint8)
    lbp = local_binary_pattern(img_uint8, n_points, radius, method='uniform')
    # The maximum possible value for uniform LBP is n_points + 2
    n_bins = n_points + 2
    hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins), density=False)
    hist = hist.astype(np.float32)
    if hist.sum() > 0:
        hist /= hist.sum()
    return hist


def extract_sharpness_features(image: np.ndarray, kernel_sizes: tuple[int, ...] = (3, 5, 7)) -> np.ndarray:
    """
    Compute Laplacian variance (sharpness) for multiple kernel sizes.

    For each kernel size, we compute the Laplacian of the image using a
    discrete approximation (via Gaussian derivative) and then compute the
    variance of the Laplacian response. The variance is a measure of
    edge strength (higher = sharper).

    Parameters
    ----------
    image : np.ndarray
        Grayscale image as float32 array in [0, 1], shape (H, W).
    kernel_sizes : tuple[int, ...], default (3, 5, 7)
        Sizes of the Laplacian kernel (must be odd and positive).

    Returns
    -------
    np.ndarray
        Variance of Laplacian for each kernel size (length = len(kernel_sizes)).
    """
    _validate_image(image)
    features = []
    for ksize in kernel_sizes:
        if ksize % 2 == 0 or ksize < 1:
            raise ValueError(f"Kernel size must be odd and positive, got {ksize}")
        # Compute Laplacian using Gaussian derivatives for better noise robustness
        # We'll use scipy.ndimage.gaussian_laplace
        sigma = ksize / 3.0  # heuristic: sigma proportional to kernel size
        laplacian = ndimage.gaussian_laplace(image, sigma=sigma)
        var = np.var(laplacian)
        features.append(np.float32(var))
    return np.array(features, dtype=np.float32)


def extract_all_features(image: np.ndarray) -> dict[str, np.ndarray]:
    """
    Extract all feature groups and return a dictionary.

    Parameters
    ----------
    image : np.ndarray
        Grayscale image as float32 array in [0, 1], shape (H, W).

    Returns
    -------
    dict[str, np.ndarray]
        Keys: 'histogram', 'fft', 'lbp', 'sharpness', 'concat'.
        'concat' is the concatenation of the four feature vectors.
    """
    hist = extract_histogram_features(image)
    fft_feat = extract_fft_band_features(image)
    lbp_feat = extract_lbp_features(image)
    sharp_feat = extract_sharpness_features(image)
    concat = np.concatenate([hist, fft_feat, lbp_feat, sharp_feat])
    return {
        'histogram': hist,
        'fft': fft_feat,
        'lbp': lbp_feat,
        'sharpness': sharp_feat,
        'concat': concat
    }