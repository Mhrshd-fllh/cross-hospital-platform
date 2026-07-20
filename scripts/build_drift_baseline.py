#!/usr/bin/env python3
"""
Build a drift baseline from CheXpert X-ray images.

Extracts histogram, FFT band energy, LBP texture, and Laplacian sharpness
features from a stratified sample of CheXpert images (balanced by view and
presence of findings) and saves the reference arrays as an .npz artifact.

The resulting file can be mounted into the backend container as a volume
and used by MedicalDriftDetector.
"""
import os
import sys
import json
import random
from pathlib import Path
import numpy as np
import csv

# Add the project root to sys.path so we can import from backend.app
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # cross-hospital-platform directory
sys.path.append(str(PROJECT_ROOT))

from backend.app.core.drift_features import (
    load_and_preprocess,
    extract_all_features,
)

def _parse_csv_rows(csv_path: Path):
    """Yield (image_path, view, is_normal) rows from a CheXpert CSV."""
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Clean up path: remove leading 'CheXpert-v1.0-small/' if present
            img_path_rel = row['Path'].strip()
            if img_path_rel.startswith('CheXpert-v1.0-small/'):
                img_path_rel = img_path_rel[len('CheXpert-v1.0-small/'):]
            # Construct absolute path under the CheXpert root
            img_path = CHEXPERT_ROOT / img_path_rel
            # Determine view (Frontal/Lateral)
            view = row['Frontal/Lateral'].strip()
            if view not in ('Frontal', 'Lateral'):
                # Fallback: try to infer from path? but skip for now
                continue
            # Determine normal vs abnormal based on No Finding column
            # Values: '1.0' = no finding, '0.0' = finding present, '-1.0' = uncertain
            try:
                no_finding = float(row['No Finding'])
            except ValueError:
                # If missing or malformed, treat as abnormal
                no_finding = 0.0
            is_normal = (no_finding == 1.0)
            yield img_path, view, is_normal

def main():
    global CHEXPERT_dockerROOT
    CHEXPERT_ROOT = PROJECT_ROOT / 'data' / 'chexpert-5gb'
    if not CHEXPERT_ROOT.is_dir():
        print(f'Error: CheXpert root not found at {CHEXPERT_ROOT}', file=sys.stderr)
        sys.exit(1)

    # Configuration
    TOTAL_SAMPLES = 2000
    NUM_STRATA = 4  # 2 views x 2 classes
    TARGET_PER_STRATA = TOTAL_SAMPLES // NUM_STRATA  # 500
    SEED = 42
    random.seed(SEED)
    np.random.seed(SEED)

    # Collect paths per stratum
    strata = {
        ('Frontal', True): [],
        ('Frontal', False): [],
        ('Lateral', True): [],
        ('Lateral', False): [],
    }

    csv_files = [
        CHEXPERT_ROOT / 'train.csv',
        CHEXPERT_ROOT / 'valid.csv',
    ]

    print("Scanning CSV files for image paths...")
    for csv_path in csv_files:
        if not csv_path.is_file():
            print(f"Warning: {csv_path} not found, skipping.")
            continue
        for img_path, view, is_normal in _parse_csv_rows(csv_path):
            key = (view, is_normal)
            if key in strata:
                strata[key].append(img_path)
            else:
                # Should not happen
                pass

    # Print availability
    print("Number of images per stratum:")
    for key, paths in strata.items():
        print(f"  {key}: {len(paths)}")

    # Sample from each stratum
    selected = []
    for key, paths in strata.items():
        n_available = len(paths)
        if n_available == 0:
            print(f"Warning: stratum {key} has no images.")
            continue
        n_to_take = min(TARGET_PER_STRATA, n_available)
        chosen = random.sample(paths, n_to_take)
        selected.extend([(img_path, key[0], key[1]) for img_path in chosen])
        print(f"  Selected {n_to_take} from {key} (available {n_available})")

    random.shuffle(selected)
    print(f"Total selected images: {len(selected)}")

    # Prepare containers for features
    feats_hist = []
    feats_fft = []
    feats_lbp = []
    feats_sharp = []
    feats_concat = []

    # Process each image
    print("Extracting features...")
    for idx, (img_path, view, is_normal) in enumerate(selected):
        if idx % 100 == 0:
            print(f"  Processed {idx}/{len(selected)}")
        if not img_path.is_file():
            print(f"Warning: image file not found: {img_path}")
            continue
        try:
            with open(img_path, 'rb') as f:
                img_bytes = f.read()
            img_array = load_and_preprocess(img_bytes)  # returns (H, W) float32 in [0,1]
            features = extract_all_features(img_array)
            feats_hist.append(features['histogram'])
            feats_fft.append(features['fft'])
            feats_lbp.append(features['lbp'])
            feats_sharp.append(features['sharpness'])
            feats_concat.append(features['concat'])
        except Exception as e:
            print(f"Warning: failed to process {img_path}: {e}")
            continue

    if len(feats_concat) == 0:
        print("Error: no images processed successfully.", file=sys.stderr)
        sys.exit(1)

    # Convert to numpy arrays
    ref_hist = np.stack(feats_hist, axis=0)
    ref_fft = np.stack(feats_fft, axis=0)
    ref_lbp = np.stack(feats_lbp, axis=0)
    ref_sharp = np.stack(feats_sharp, axis=0)
    ref_concat = np.stack(feats_concat, axis=0)

    print("Feature shapes:")
    print(f"  histogram: {ref_hist.shape}")
    print(f"  fft: {ref_fft.shape}")
    print(f"  lbp: {ref_lbp.shape}")
    print(f"  sharpness: {ref_sharp.shape}")
    print(f"  concat: {ref_concat.shape}")

    # Save artifact
    artifact_dir = PROJECT_ROOT / 'baseline'
    artifact_dir.mkdir(exist_ok=True)
    artifact_path = artifact_dir / 'chexpert_baseline.npz'
    np.savez(
        artifact_path,
        histogram=ref_hist,
        fft=ref_fft,
        lbp=ref_lbp,
        sharpness=ref_sharp,
        concat=ref_concat,
    )
    print(f"Saved baseline artifact to {artifact_path}")

    # Also save a small metadata JSON for reference
    meta = {
        'num_samples': int(len(feats_concat)),
        'strata_counts': {
            f"{v}_{'normal' if n else 'abnormal'}": len([s for s in selected if s[1]==v and s[2]==n])
            for v in ['Frontal', 'Lateral'] for n in [True, False]
        },
        'feature_dimensions': {
            'histogram': int(ref_hist.shape[1]),
            'fft': int(ref_fft.shape[1]),
            'lbp': int(ref_lbp.shape[1]),
            'sharpness': int(ref_sharp.shape[1]),
            'concat': int(ref_concat.shape[1]),
        },
        'chexpert_root': str(CHEXPERT_ROOT),
        'seed': SEED,
    }
    meta_path = artifact_dir / 'chexpert_baseline_meta.json'
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"Saved metadata to {meta_path}")

if __name__ == '__main__':
    main()