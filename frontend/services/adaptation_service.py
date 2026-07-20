"""
Mock implementation of the AdaptationService for development and testing.
Returns simulated data for frontend development.
"""

import random
from datetime import datetime
from typing import List, Dict
from . import AdaptationService, AdaptationResult

class MockAdaptationService(AdaptationService):
    """Mock implementation of AdaptationService."""

    def __init__(self):
        self._adaptation_results: dict = {}  # request_id -> AdaptationResult

    def adapt_image(self, request_id: str, drift_score: float) -> AdaptationResult:
        """Simulate image adaptation based on drift score."""
        # Only adapt if drift is above threshold
        adaptation_applied = drift_score > 0.3

        # Define adaptation steps
        adaptation_steps = [
            {
                "step": "Original Image",
                "description": "Input image as received from hospital",
                "status": "complete",
                "execution_time": 0.0,
                "details": "Raw DICOM/JPG image from General Hospital"
            }
        ]

        total_time = 0.0

        if adaptation_applied:
            # Add adaptation steps
            steps_data = [
                ("Contrast Normalization", "Normalize image contrast to match training distribution",
                 random.uniform(0.1, 0.5), "Applied CLAHE (Contrast Limited Adaptive Histogram Equalization)"),
                ("Histogram Normalization", "Match histogram distribution to reference dataset",
                 random.uniform(0.05, 0.3), "Histogram matching to CheXpert training set statistics"),
                ("Intensity Normalization", "Normalize intensity values to standard range",
                 random.uniform(0.05, 0.2), "Z-score normalization followed by clipping to [0,1] range"),
                ("AdaIN-style Adaptation", "Adaptive Instance Normalization for style transfer",
                 random.uniform(0.2, 0.8), "Matched mean and variance to reference style distribution")
            ]

            for step_name, description, exec_time, details in steps_data:
                adaptation_steps.append({
                    "step": step_name,
                    "description": description,
                    "status": "complete",
                    "execution_time": round(exec_time, 2),
                    "details": details
                })
                total_time += exec_time

        # Add result steps
        adaptation_steps.extend([
            {
                "step": "Adapted Image",
                "description": "Final adapted image ready for inference",
                "status": "complete",
                "execution_time": 0.0,
                "details": "Image processed to reduce domain shift while preserving anatomy"
            },
            {
                "step": "Difference Map",
                "description": "Visualization of changes made during adaptation",
                "status": "complete",
                "execution_time": round(random.uniform(0.1, 0.4), 2),
                "details": "Pixel-wise absolute difference between original and adapted images"
            }
        ])

        # Calculate total execution time
        total_time = sum(step["execution_time"] for step in adaptation_steps if step["execution_time"] > 0)

        # Generate quality metrics
        quality_metrics = {
            "structural_similarity": round(random.uniform(0.85, 0.98), 3),
            "mean_squared_error": round(random.uniform(0.001, 0.01), 4),
            "peak_signal_noise_ratio": round(random.uniform(25, 35), 1),
            "anatomical_preservation_score": round(random.uniform(0.90, 0.99), 3)
        }

        result = AdaptationResult(
            request_id=request_id,
            adapted_image_location=f"s3://adapted-images/{request_id}.dcm" if adaptation_applied else None,
            adaptation_steps=adaptation_steps,
            total_execution_time=round(total_time, 2),
            quality_metrics=quality_metrics,
            adaptation_applied=adaptation_applied,
            drift_score_that_triggered=drift_score if adaptation_applied else 0.0,
            timestamp=datetime.now()
        )

        # Store for retrieval
        self._adaptation_results[request_id] = result
        return result

    def get_adaptation_result(self, request_id: str) -> AdaptationResult:
        """Get adaptation result for a request."""
        if request_id in self._adaptation_results:
            return self._adaptation_results[request_id]
        else:
            # For demo, we need a drift score - in reality this would come from drift detection
            # For now, return a default result with no adaptation
            return self.adapt_image(request_id, 0.1)  # Low drift, no adaptation

# Factory function
def create_adaptation_service() -> AdaptationService:
    """Create an instance of the mock AdaptationService."""
    return MockAdaptationService()