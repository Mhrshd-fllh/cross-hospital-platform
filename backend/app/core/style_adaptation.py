"""
Style Adaptation Layer for cross-hospital generalization.
Implements three adaptation methods with continuous strength based on drift severity:
1. Histogram matching (for contrast/exposure signal)
2. FFT band reweighting (for frequency domain signal)
3. Unsharp mask/blur calibration (for sharpness signal)
"""
import os
import numpy as np
from PIL import Image
import io
from pathlib import Path
from scipy import fftpack
from scipy import ndimage
from typing import Literal


class StyleAdapter:
    """
    Style adaptation using multiple techniques to match image appearance to a reference
    distribution while preserving anatomical structures. The strength of each adaptation
    is controlled by the corresponding drift signal p-value (strength = 1 - p_value).
    """

    def __init__(self, baseline_path: str | None = None):
        """
        Initialize the style adapter with baseline data.

        Parameters
        ----------
        baseline_path : str | None, optional
            Path to the baseline .npz file containing reference feature arrays.
            If None, uses the BASELINE_PATH environment variable or
            defaults to "/workspace/baseline/chexpert_baseline.npz".
        """
        if baseline_path is None:
            baseline_path = os.getenv(
                "BASELINE_PATH", "/workspace/baseline/chexpert_baseline.npz"
            )
        self.baseline_path = Path(baseline_path)

        # Load baseline feature arrays
        baseline = np.load(self.baseline_path)
        self.baseline_hist = baseline['histogram']      # shape (N_hist, 64)
        self.baseline_fft  = baseline['fft']            # shape (N_fft, 8)
        self.baseline_lbp  = baseline['lbp']            # shape (N_lbp, 18)
        self.baseline_sharp= baseline['sharpness']      # shape (N_sharp, 3)
        self.baseline_concat = baseline['concat']       # shape (N_concat, 93)

        # Compute reference histogram (average and normalize)
        self.ref_hist = np.mean(self.baseline_hist, axis=0)
        if self.ref_hist.sum() > 0:
            self.ref_hist = self.ref_hist / self.ref_hist.sum()
        self.ref_hist = self.ref_hist.astype(np.float32)

        # Compute reference FFT band energies (average, already normalized per image)
        self.ref_fft = np.mean(self.baseline_fft, axis=0)   # shape (8,)
        self.ref_fft = self.ref_fft.astype(np.float32)

        # Compute reference sharpness (average over images and kernel sizes)
        sharp_per_image = np.mean(self.baseline_sharp, axis=1)   # shape (N_sharp,)
        self.ref_sharp_mean = float(np.mean(sharp_per_image))

        # Precompute binning for FFT band reweighting (same as in drift_features)
        self._setup_fft_binning()

    def _setup_fft_binning(self):
        """Setup frequency binning for FFT band reweighting (matches drift_features)."""
        # Parameters from drift_features.extract_fft_band_features
        self.n_bands = 8
        # We'll assume a default image size of 320x320 (as in load_and_preprocess)
        # The binning is done on the frequency radius, which depends on image size.
        # We'll compute the bin edges for a 320x320 image.
        h, w = 320, 320
        freq_y = fftpack.fftfreq(h)[:, None]
        freq_x = fftpack.fftfreq(w)[None, :]
        freq_y = fftpack.fftshift(freq_y)
        freq_x = fftpack.fftshift(freq_x)
        self.radius = np.sqrt(freq_x**2 + freq_y**2)  # shape (h, w)
        self.max_radius = 0.5
        self.min_radius = 1e-5
        self.bin_edges = np.logspace(
            np.log10(self.min_radius), np.log10(self.max_radius), num=self.n_bands + 1
        )
        # Flatten for digitizing
        self.radius_flat = self.radius.ravel()

    def _extract_fft_band_energy(self, magnitude: np.ndarray) -> np.ndarray:
        """
        Extract band energy magnitude spectrum (same as in drift_features).
        Parameters
        ----------
        magnitude : np.ndarray
            Magnitude spectrum (shifted, same shape as self.radius).
        Returns
        -------
        np.ndarray
            Band energy vector of length self.n_bands, normalized to sum to 1.
        """
        magnitude_flat = magnitude.ravel()
        # Digitize radii into bins
        bin_indices = np.digitize(self.radius_flat, self.bin_edges) - 1
        bin_indices = np.clip(bin_indices, 0, self.n_bands - 1)
        # Sum magnitude in each bin
        band_energy = np.zeros(self.n_bands, dtype=np.float32)
        for i in range(self.n_bands):
            mask = bin_indices == i
            band_energy[i] = magnitude_flat[mask].sum()
        # Normalize
        if band_energy.sum() > 0:
            band_energy /= band_energy.sum()
        return band_energy

    def _pvalue_to_strength(self, pval: float) -> float:
        """
        Convert p-value to adaptation strength in [0, 1].
        Strength = 1 - p_value (so higher drift -> higher strength).
        """
        if np.isnan(pval):
            return 0.0
        strength = 1.0 - pval
        return max(0.0, min(1.0, strength))

    def _histogram_matching(self, img_array: np.ndarray) -> np.ndarray:
        """
        Fully adapt image using histogram matching to reference histogram.
        Returns the fully adapted image (to be blended later).
        """
        from .drift_features import extract_histogram_features
        img_hist = extract_histogram_features(img_array, bins=64)
        # Create lookup table from img_hist to ref_hist
        lut = self._create_lookup_table(img_hist, self.ref_hist)
        img_uint8 = (img_array * 255).astype(np.uint8)
        mapped_uint8 = lut[img_uint8]
        mapped_array = mapped_uint8.astype(np.float32) / 255.0
        return mapped_array

    def _create_lookup_table(self, src_hist: np.ndarray, ref_hist: np.ndarray) -> np.ndarray:
        """
        Create a lookup table for histogram matching from source histogram to reference histogram.
        """
        # Bin edges for 64 bins from 0 to 1
        bin_edges = np.linspace(0.0, 1.0, 65)
        # Cumulative distribution function (CDF) of source histogram
        cd_src = np.cumsum(src_hist)
        # Cumulative distribution function of reference histogram
        cd_ref = np.cumsum(ref_hist)

        # Inverse mapping: for each possible input value in [0, 255], compute output value
        lut = np.zeros(256, dtype=np.uint8)
        for i in range(256):
            v = i / 255.0
            bin_idx = np.searchsorted(bin_edges, v, side="right") - 1
            bin_idx = max(0, min(bin_idx, 63))
            bin_low = bin_edges[bin_idx]
            bin_high = bin_edges[bin_idx + 1]
            if bin_high == bin_low:
                p_in_bin = 0.0
            else:
                p_in_bin = (v - bin_low) / (bin_high - bin_low)
            cum_v = cd_src[bin_idx] + p_in_bin * src_hist[bin_idx]

            if cum_v > cd_ref[-1]:
                cum_v = cd_ref[-1]
            ref_bin_idx = np.searchsorted(cd_ref, cum_v, side="right") - 1
            ref_bin_idx = max(0, min(ref_bin_idx, 63))

            # Now, we need to map within the reference bin
            cum_ref_low = cd_ref[ref_bin_idx] if ref_bin_idx > 0 else 0.0
            # The mass of the reference bin is ref_hist[ref_bin_idx]
            cum_ref_bin = ref_hist[ref_bin_idx]
            if cum_ref_bin == 0:
                # If the bin has zero probability, use the bin center
                mapped_v = (bin_edges[ref_bin_idx] + bin_edges[ref_bin_idx + 1]) / 2.0
            else:
                p_in_ref_bin = (cum_v - cum_ref_low) / cum_ref_bin
                mapped_v = bin_edges[ref_bin_idx] + p_in_ref_bin * (
                    bin_edges[ref_bin_idx + 1] - bin_edges[ref_bin_idx]
                )
            lut[i] = int(np.clip(round(mapped_v * 255), 0, 255))
        return lut

    def _fft_band_reweighting(self, img_array: np.ndarray, strength_fft: float) -> np.ndarray:
        """
        Fully adapt image using FFT band reweighting to reference band energies.
        Returns the fully adapted image (to be blended later).
        """
        # Compute FFT2 and shift zero frequency to center
        fft2 = fftpack.fft2(img_array)
        fft_shift = fftpack.fftshift(fft2)
        magnitude = np.abs(fft_shift)
        phase = np.angle(fft_shift)

        # Extract current band energy
        current_band_energy = self._extract_fft_band_energy(magnitude)  # shape (8,)

        # Compute target band energy: blend between current and reference
        target_band_energy = (1 - strength_fft) * current_band_energy + strength_fft * self.ref_fft

        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            band_factors = target_band_energy / current_band_energy
        band_factors = np.nan_to_num(band_factors, nan=1.0)   # if current_band is zero, factor=1 (no change)

        # Create a factor matrix of the same shape as magnitude
        magnitude_flat = magnitude.ravel()
        bin_indices = np.digitize(self.radius_flat, self.bin_edges) - 1
        bin_indices = np.clip(bin_indices, 0, self.n_bands - 1)

        # Factor for each frequency bin
        factor_flat = band_factors[bin_indices]
        factor_map = factor_flat.reshape(magnitude.shape)

        # Adjust magnitude
        adjusted_magnitude = magnitude * factor_map

        # Reconstruct the complex spectrum
        adjusted_fft_shift = adjusted_magnitude * np.exp(1j * phase)
        # Inverse shift
        adjusted_fft = fftpack.ifftshift(adjusted_fft_shift)
        # Inverse FFT
        img_adjusted = np.real(fftpack.ifft2(adjusted_fft))
        # Clip to [0, 1] (since the input was in [0, 1])
        img_adjusted = np.clip(img_adjusted, 0, 1)

        return img_adjusted

    def _laplacian_variance(self, image: np.ndarray, ksize: int) -> float:
        """
        Compute the variance of the Laplacian of the image using Gaussian derivative.
        """
        if ksize % 2 == 0 or ksize < 1:
            raise ValueError(f"Kernel size must be odd and positive, got {ksize}")
        sigma = ksize / 3.0  # heuristic: sigma proportional to kernel size
        laplacian = ndimage.gaussian_laplace(image, sigma=sigma)
        return np.var(laplacian)

    def _unsharp_mask_blur_calibration(self, img_array: np.ndarray, strength_sharp: float) -> np.ndarray:
        """
        Fully adapt image using unsharp mask/blur calibration to reference sharpness.
        Returns the fully adapted image (to be blended later).
        """
        # Compute current sharpness (average of Laplacian variance for kernel sizes 3,5,7)
        current_sharp = np.mean([
            self._laplacian_variance(img_array, k) for k in (3, 5, 7)
        ])
        ref_sharp = self.ref_sharp_mean

        # Avoid division by zero
        if ref_sharp == 0:
            ref_sharp = 1e-7

        delta = ref_sharp - current_sharp  # positive means we need to increase sharpness
        # We'll use the strength_sharp to scale the correction
        max_amount = 2.0   # maximum amount for unsharp mask
        max_sigma = 10.0   # maximum sigma for Gaussian blur

        if delta > 0:
            # sharpen: unsharp mask
            amount = strength_sharp * abs(delta) * max_amount / ref_sharp
            amount = min(amount, max_amount)   # clamp
            # Apply unsharp mask: sharpened = original + amount * (original - blurred)
            blurred = ndimage.gaussian_filter(img_array, sigma=1.0)  # blur kernel for unsharp mask
            adjusted = img_array + amount * (img_array - blurred)
            adjusted = np.clip(adjusted, 0, 1)
            return adjusted
        elif delta < 0:
            # blur: Gaussian blur
            sigma = strength_sharp * abs(delta) * max_sigma / ref_sharp
            sigma = min(sigma, max_sigma)
            adjusted = ndimage.gaussian_filter(img_array, sigma=sigma)
            return adjusted
        else:
            return img_array

    def adapt_image(
        self, image_bytes: bytes, metadata: dict | None = None
    ) -> bytes:
        """
        Adapt the image style using the three methods with strengths based on drift signals.
        Expects metadata to contain 'drift_result' with signal p-values for histogram, fft, sharpness.
        If metadata or drift_result is missing, uses default strengths of 0.0 (no adaptation).

        Parameters
        ----------
        image_bytes : bytes
            Raw image bytes (e.g., PNG, JPEG).
        metadata : dict | None, optional
            Additional metadata (e.g., drift metrics, hospital info). Should contain
            'drift_result' from the drift detector.

        Returns
        -------
        bytes
            The adapted image as PNG bytes (lossless to avoid compression artifacts).
        """
        # Load and preprocess image to grayscale float32 in [0, 1]
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("L")
        except Exception as e:
            raise ValueError(f"Unable to decode image: {e}") from e

        # Resize image to 320x320 to match baseline
        img = img.resize((320, 320), Image.Resampling.BILINEAR)

        img_array = np.array(img, dtype=np.float32) / 255.0
        if img_array.ndim != 2:
            raise ValueError(
                f"Expected 2D grayscale image, got shape {img_array.shape}"
            )

        # Extract drift result from metadata if available
        drift_result = metadata.get('drift_result', {}) if metadata else {}
        signal_pvals = drift_result.get('signal_pvals', {
            'histogram': 1.0,  # no drift -> strength 0
            'fft': 1.0,
            'lbp': 1.0,
            'sharpness': 1.0
        })

        # Compute strengths for each signal
        strength_hist = self._pvalue_to_strength(signal_pvals.get('histogram', 1.0))
        strength_fft = self._pvalue_to_strength(signal_pvals.get('fft', 1.0))
        strength_sharp = self._pvalue_to_strength(signal_pvals.get('sharpness', 1.0))

        # We'll apply each adaptation in sequence, blending by the strength.
        # Start with the original image
        adapted = img_array.copy()

        # 1. Histogram matching
        if strength_hist > 0:
            hist_adapted = self._histogram_matching(adapted)
            adapted = (1 - strength_hist) * adapted + strength_hist * hist_adapted

        # 2. FFT band reweighting
        if strength_fft > 0:
            fft_adapted = self._fft_band_reweighting(adapted, strength_fft)
            adapted = (1 - strength_fft) * adapted + strength_fft * fft_adapted

        # 3. Unsharp mask/blur calibration
        if strength_sharp > 0:
            sharp_adapted = self._unsharp_mask_blur_calibration(adapted, strength_sharp)
            adapted = (1 - strength_sharp) * adapted + strength_sharp * sharp_adapted

        # Encode back to PNG bytes (lossless)
        output_buffer = io.BytesIO()
        Image.fromarray((adapted * 255).astype(np.uint8)).save(
            output_buffer, format="PNG"
        )
        return output_buffer.getvalue()


# Convenience function for functional style
def adapt_image_style(
    image_bytes: bytes, metadata: dict | None = None
) -> bytes:
    """
    Adapt image style using the default style adapter.

    Parameters
    ----------
    image_bytes : bytes
        Raw image bytes.
    metadata : dict | None, optional
        Additional metadata (should contain 'drift_result').

    Returns
    -------
    bytes
        Adapted image as PNG bytes.
    """
    adapter = StyleAdapter()
    return adapter.adapt_image(image_bytes, metadata)