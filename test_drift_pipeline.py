#!/usr/bin/env python3
"""
Test script to validate the drift detection pipeline using a MIMIC-CXR image
and the CheXpert baseline.
"""

import os
import sys
from pathlib import Path

# Add backend to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from backend.app.core.drift_detector import MedicalDriftDetector
from backend.app.core.drift_features import load_and_preprocess, extract_all_features
import numpy as np
from PIL import Image
import io

def test_drift_detection():
    """Test drift detection on a sample MIMIC-CXR image."""

    print("=== Testing Drift Detection Pipeline ===")

    # 1. Initialize drift detector with CheXpert baseline
    baseline_path = PROJECT_ROOT / "baseline" / "chexpert_baseline.npz"
    if not baseline_path.exists():
        print(f"ERROR: Baseline not found at {baseline_path}")
        print("Please run: python scripts/build_drift_baseline.py")
        return False

    print(f"Loading baseline from: {baseline_path}")
    detector = MedicalDriftDetector(baseline_path=str(baseline_path))
    print("✓ Baseline loaded successfully")

    # 2. Find a sample MIMIC-CXR image
    mimic_root = PROJECT_ROOT / "data" / "mimic-cxr-5gb" / "official_data_iccv_final" / "files"
    if not mimic_root.exists():
        print(f"ERROR: MIMIC-CXR data not found at {mimic_root}")
        return False

    # Find first available JPG image
    sample_image_path = None
    for patient_dir in mimic_root.iterdir():
        if patient_dir.is_dir():
            for study_dir in patient_dir.iterdir():
                if study_dir.is_dir():
                    for img_file in study_dir.glob("*.jpg"):
                        sample_image_path = img_file
                        break
                if sample_image_path:
                    break
        if sample_image_path:
            break

    if not sample_image_path:
        print("ERROR: No JPG images found in MIMIC-CXR dataset")
        return False

    print(f"Using test image: {sample_image_path}")

    # 3. Load and process the image
    try:
        with open(sample_image_path, 'rb') as f:
            image_bytes = f.read()

        print(f"Loaded image ({len(image_bytes)} bytes)")

        # Preprocess and extract features (for verification)
        img_array = load_and_preprocess(image_bytes)
        print(f"Preprocessed image shape: {img_array.shape}, dtype: {img_array.dtype}")
        print(f"Image value range: [{img_array.min():.3f}, {img_array.max():.3f}]")

        features = extract_all_features(img_array)
        print("\nExtracted feature shapes:")
        for name, feat in features.items():
            print(f"  {name}: {feat.shape}")

        # 4. Run drift detection
        print("\n=== Running Drift Detection ===")
        result = detector.detect_image_drift(image_bytes)

        print(f"MMD Statistic: {result['mmd_stat']:.6f}")
        print(f"MMD P-value: {result['mmd_pvalue']:.6f}")
        print(f"Status: {result['status']}")
        print("\nSignal P-values:")
        for signal, pval in result['signal_pvals'].items():
            print(f"  {signal}: {pval:.6f}")

        # 5. Interpret results
        print("\n=== Interpretation ===")
        if result['status'] == 'Normal':
            print("✓ No significant drift detected (p-value >= 0.05)")
        elif result['status'] == 'Warning':
            print("⚠ Warning: Moderate drift detected (0.05 > p-value >= 0.01)")
        elif result['status'] == 'Critical':
            print("❌ Critical: Severe drift detected (p-value < 0.01)")
        else:
            print(f"? Error in detection: {result['status']}")

        return True

    except Exception as e:
        print(f"ERROR processing image: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_drift_detection()
    sys.exit(0 if success else 1)