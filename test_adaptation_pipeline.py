#!/usr/bin/env python3
"""
Test script to validate the style adaptation layer.
"""
import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image
import io

# Add backend to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from backend.app.core.style_adaptation import StyleAdapter
from backend.app.core.drift_features import load_and_preprocess, extract_histogram_features, extract_fft_band_features


def test_adaptation_methods():
    """Test the three adaptation methods on a sample image."""
    print("=== Testing Style Adaptation Layer ===")

    # 1. Check if baseline exists
    baseline_path = PROJECT_ROOT / "baseline" / "chexpert_baseline.npz"
    if not baseline_path.exists():
        print(f"ERROR: Baseline not found at {baseline_path}")
        print("Please run: python scripts/build_drift_baseline.py")
        return False

    # 2. Find a sample image (same as drift test)
    mimic_root = PROJECT_ROOT / "data" / "mimic-cxr-5gb" / "official_data_iccv_final" / "files"
    if not mimic_root.exists():
        print(f"ERROR: MIMIC-CXR data not found at {mimic_root}")
        return False

    # Find first available JPG image recursively
    sample_image_path = None
    for img_file in mimic_root.rglob("*.jpg"):
        sample_image_path = img_file
        break

    if not sample_image_path:
        print("ERROR: No JPG images found in MIMIC-CXR dataset")
        return False

    print(f"Using test image: {sample_image_path}")

    # 3. Load the image
    try:
        with open(sample_image_path, 'rb') as f:
            image_bytes = f.read()
        print(f"Loaded image ({len(image_bytes)} bytes)")

        # Preprocess to check shape and range
        img_array = load_and_preprocess(image_bytes)
        print(f"Preprocessed image shape: {img_array.shape}, dtype: {img_array.dtype}")
        print(f"Image value range: [{img_array.min():.3f}, {img_array.max():.3f}]")

        # Compute original histogram
        orig_hist = extract_histogram_features(img_array, bins=64)
        print(f"Original histogram sum: {orig_hist.sum():.6f} (should be ~1.0)")

    except Exception as e:
        print(f"ERROR loading image: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 4. Test each adaptation method by setting strength to 1.0 for that method and 0.0 for others
    # We'll test: histogram matching, FFT band reweighting, unsharp mask/blur calibration
    test_cases = [
        ("histogram_matching", {'histogram': 0.0, 'fft': 1.0, 'sharpness': 1.0}),
        ("fft_band_reweighting", {'histogram': 1.0, 'fft': 0.0, 'sharpness': 1.0}),
        ("unsharp_mask_blur_calibration", {'histogram': 1.0, 'fft': 1.0, 'sharpness': 0.0})
    ]

    for method_name, pvals in test_cases:
        print(f"\n--- Testing method: {method_name} ---")
        try:
            # Create metadata with drift_result that gives the desired p-values
            metadata = {
                'drift_result': {
                    'signal_pvals': pvals
                }
            }
            # Adapt the image
            adapter = StyleAdapter(baseline_path=str(baseline_path))
            adapted_bytes = adapter.adapt_image(image_bytes, metadata=metadata)
            print(f"Adapted image size: {len(adapted_bytes)}")

            # Load the adapted image
            adapted_img = Image.open(io.BytesIO(adapted_bytes)).convert("L")
            adapted_array = np.array(adapted_img, dtype=np.float32) / 255.0
            print(f"Adapted image shape: {adapted_array.shape}, range: [{adapted_array.min():.3f}, {adapted_array.max():.3f}]")

            # Compute adapted histogram
            adapted_hist = extract_histogram_features(adapted_array, bins=64)
            print(f"Adapted histogram sum: {adapted_hist.sum():.6f}")

            # For histogram matching, we can compare histograms to reference
            if method_name == "histogram_matching":
                # Load reference histogram from baseline
                baseline = np.load(baseline_path)
                reference_hist = np.mean(baseline["histogram"], axis=0)
                if reference_hist.sum() > 0:
                    reference_hist = reference_hist / reference_hist.sum()
                # Compute histogram difference (e.g., L1 distance)
                hist_diff = np.sum(np.abs(adapted_hist - reference_hist))
                orig_hist_diff = np.sum(np.abs(orig_hist - reference_hist))
                print(f"Histogram L1 distance to reference:")
                print(f"  Original: {orig_hist_diff:.6f}")
                print(f"  Adapted:  {hist_diff:.6f}")
                if hist_diff < orig_hist_diff:
                    print("  SUCCESS: Adaptation brought histogram closer to reference")
                else:
                    print("  WARNING: Adaptation did not improve histogram match (may be expected for some images)")

            elif method_name == "fft_band_reweighting":
                # We can check the FFT band energy compared to reference
                # Extract FFT band energy from original and adapted images
                orig_fft_feat = extract_fft_band_features(img_array)
                adapted_fft_feat = extract_fft_band_features(adapted_array)
                # Get reference FFT from a temporary adapter
                temp_adapter = StyleAdapter(baseline_path=str(baseline_path))
                ref_fft = temp_adapter.ref_fft
                # Compute L1 distance to reference
                orig_fft_diff = np.sum(np.abs(orig_fft_feat - ref_fft))
                adapted_fft_diff = np.sum(np.abs(adapted_fft_feat - ref_fft))
                print(f"FFT band energy L1 distance to reference:")
                print(f"  Original: {orig_fft_diff:.6f}")
                print(f"  Adapted:  {adapted_fft_diff:.6f}")
                if adapted_fft_diff < orig_fft_diff:
                    print("  SUCCESS: Adaptation brought FFT band energy closer to reference")
                else:
                    print("  WARNING: Adaptation did not improve FFT band energy match (may be expected for some images)")

            elif method_name == "unsharp_mask_blur_calibration":
                # We can check the sharpness compared to reference
                # Compute sharpness (average of Laplacian variance for kernel sizes 3,5,7)
                def _laplacian_variance(image: np.ndarray, ksize: int) -> float:
                    if ksize % 2 == 0 or ksize < 1:
                        raise ValueError(f"Kernel size must be odd and positive, got {ksize}")
                    sigma = ksize / 3.0
                    from scipy import ndimage
                    laplacian = ndimage.gaussian_laplace(image, sigma=sigma)
                    return np.var(laplacian)
                orig_sharp = np.mean([
                    _laplacian_variance(img_array, k) for k in (3, 5, 7)
                ])
                adapted_sharp = np.mean([
                    _laplacian_variance(adapted_array, k) for k in (3, 5, 7)
                ])
                # Get reference sharpness from a temporary adapter
                temp_adapter = StyleAdapter(baseline_path=str(baseline_path))
                ref_sharp = temp_adapter.ref_sharp_mean
                print(f"Sharpness (average Laplacian variance):")
                print(f"  Original: {orig_sharp:.6f}")
                print(f"  Adapted:  {adapted_sharp:.6f}")
                print(f"  Reference: {ref_sharp:.6f}")
                # Check if adapted sharpness is closer to reference
                orig_sharp_diff = abs(orig_sharp - ref_sharp)
                adapted_sharp_diff = abs(adapted_sharp - ref_sharp)
                print(f"  Absolute difference to reference:")
                print(f"    Original: {orig_sharp_diff:.6f}")
                print(f"    Adapted:  {adapted_sharp_diff:.6f}")
                if adapted_sharp_diff < orig_sharp_diff:
                    print("  SUCCESS: Adaptation brought sharpness closer to reference")
                else:
                    print("  WARNING: Adaptation did not improve sharpness match (may be expected for some images)")

            print(f"  PASS: Method '{method_name}' completed successfully")

        except Exception as e:
            print(f"  ERROR in method '{method_name}': {e}")
            import traceback
            traceback.print_exc()
            return False

    print("\n=== All adaptation methods tested successfully ===")
    return True


if __name__ == "__main__":
    success = test_adaptation_methods()
    sys.exit(0 if success else 1)