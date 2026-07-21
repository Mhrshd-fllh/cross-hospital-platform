"""
Production-grade data drift detector using Alibi Detect's MMDDrift and KSDrift
on handcrafted feature groups (histogram, FFT, LBP, sharpness).
Loads a pre‑computed CheXpert baseline.
"""
import os
import numpy as np
from PIL import Image
import io
from pathlib import Path
from alibi_detect.cd import KSDrift, MMDDrift
import logging

logger = logging.getLogger(__name__)

class MedicalDriftDetector:
    """
    Production-grade data drift detector leveraging Alibi Detect's MMDDrift (overall)
    and KSDrift (per feature group) to detect distribution shifts in clinical
    medical images based on handcrafted features.
    """

    def __init__(self, baseline_path: str | None = None):
        """
        Parameters
        ----------
        baseline_path : str | None
            Path to the baseline artifact (.npz) containing reference feature arrays.
            If None, looks for <project_root>/baseline/chexpert_baseline.npz.
        """
        if baseline_path is None:
            # Resolve path relative to this file: <project_root>/baseline/chexpert_baseline.npz
            baseline_path = Path(__file__).resolve().parents[3] / "baseline" / "chexpert_baseline.npz"
        else:
            baseline_path = Path(baseline_path)

        if not baseline_path.is_file():
            raise FileNotFoundError(f"Baseline artifact not found at {baseline_path}")

        # Load baseline feature arrays
        baseline = np.load(baseline_path)
        self.baseline_hist = baseline['histogram']      # shape (N_hist, 64)
        self.baseline_fft  = baseline['fft']            # shape (N_fft, 8)
        self.baseline_lbp  = baseline['lbp']            # shape (N_lbp, 18)
        self.baseline_sharp= baseline['sharpness']      # shape (N_sharp, 3)
        self.baseline_concat = baseline['concat']       # shape (N_concat, 93)

        # Initialize detectors
        # Note: p_val=0.05 matches the original alpha threshold
        self.mmd_detector = MMDDrift(self.baseline_concat, p_val=0.05)
        self.kst_hist = KSDrift(self.baseline_hist, p_val=0.05)
        self.kst_fft  = KSDrift(self.baseline_fft,  p_val=0.05)
        self.kst_lbp  = KSDrift(self.baseline_lbp,  p_val=0.05)
        self.kst_sharp= KSDrift(self.baseline_sharp, p_val=0.05)

    def detect_image_drift(self, image_bytes: bytes) -> dict:
        """
        Extract handcrafted features from the image, run MMDDrift (overall) and
        four KSDrift detectors (one per feature group), and return a dictionary
        with the overall MMD statistic and p‑value, per‑signal p‑values, and a
        human‑readable status.

        Parameters
        ----------
        image_bytes : bytes
            Raw image bytes (e.g., from file upload).

        Returns
        -------
        dict
            {
                'mmd_stat': float,          # MMD distance statistic
                'mmd_pvalue': float,        # p‑value from MMDDrift
                'signal_pvals': {
                    'histogram': float,
                    'fft': float,
                    'lbp': float,
                    'sharpness': float
                },
                'status': str               # 'Normal', 'Warning', 'Critical', or 'Error'
            }
        """
        try:
            # -----------------------------------------------------------------
            # 1. Pre‑process image and extract feature groups
            # -----------------------------------------------------------------
            from backend.app.core.drift_features import load_and_preprocess, extract_all_features

            # Load and preprocess to a (H, W) float32 array in [0, 1]
            img_array = load_and_preprocess(image_bytes)          # shape (H, W)
            features = extract_all_features(img_array)            # dict of ndarrays

            # Extract each feature vector (ensure 2D shape (1, D) for the detectors)
            hist_vec  = features['histogram'].reshape(1, -1)      # (1, 64)
            fft_vec   = features['fft'].reshape(1, -1)            # (1, 8)
            lbp_vec   = features['lbp'].reshape(1, -1)            # (1, 18)
            sharp_vec = features['sharpness'].reshape(1, -1)      # (1, 3)
            concat_vec= features['concat'].reshape(1, -1)         # (1, 93)

            # -----------------------------------------------------------------
            # 2. Run detectors
            # -----------------------------------------------------------------
            mmd_result = self.mmd_detector.predict(concat_vec)
            hist_result = self.kst_hist.predict(hist_vec)
            fft_result  = self.kst_fft.predict(fft_vec)
            lbp_result  = self.kst_lbp.predict(lbp_vec)
            sharp_result= self.kst_sharp.predict(sharp_vec)

            # -----------------------------------------------------------------
            # 3. Extract useful quantities
            # -----------------------------------------------------------------
            # MMDDrift returns: {'data': {'is_drift': bool, 'pval': float, 'distance': float}}
            mmd_pvalue = float(mmd_result['data']['pval'])
            mmd_stat   = float(mmd_result['data'].get('distance', 0.0))

            # KSDrift returns pval as an array (one per feature); we reduce to a single
            # p‑value per group by taking the mean (matches the legacy behaviour).
            def _mean_pval(res):
                pval = res['data']['pval']
                # Ensure we have a 1‑D array; if scalar, just return it
                if np.isscalar(pval):
                    return float(pval)
                return float(np.mean(pval))

            signal_pvals = {
                'histogram': _mean_pval(hist_result),
                'fft':       _mean_pval(fft_result),
                'lbp':       _mean_pval(lbp_result),
                'sharpness': _mean_pval(sharp_result)
            }

            # -----------------------------------------------------------------
            # 4. Determine status (mirroring the legacy logic)
            # -----------------------------------------------------------------
            # Legacy: is_drifted = int(drift_result['data']['is_drift']) == 1
            # where drift_result['data']['is_drift'] came from KSDrift (array) and
            # was considered drifted if any feature was significant? The old code
            # used `int(drift_result['data']['is_drift']) == 1` where is_drift was
            # an array; numpy casts array>0 to True if any element is non‑zero.
            # We'll replicate the same idea: consider the group drifted if ANY
            # feature in that group is significant, but for the overall status we
            # follow the original spec: use the overall MMD p‑value and the derived
            # drift_score (1 - pvalue) with the same thresholds.
            if mmd_pvalue >= 0.05:
                status = "Normal"
            elif mmd_pvalue >= 0.01:  # 0.01 <= pvalue < 0.05
                status = "Warning"
            else:  # pvalue < 0.01
                status = "Critical"

            return {
                'mmd_stat': mmd_stat,
                'mmd_pvalue': mmd_pvalue,
                'signal_pvals': signal_pvals,
                'status': status
            }

        except Exception as exc:
            # Log the error with context; do NOT silently swallow into a normal result.
            logger.exception("Error during drift detection")
            # Return a distinct error status so callers can detect failure.
            return {
                'mmd_stat': float('nan'),
                'mmd_pvalue': float('nan'),
                'signal_pvals': {
                    'histogram': float('nan'),
                    'fft': float('nan'),
                    'lbp': float('nan'),
                    'sharpness': float('nan')
                },
                'status': 'Error'
            }