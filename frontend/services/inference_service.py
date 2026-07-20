"""
Mock implementation of the InferenceService for development and testing.
Returns simulated data for frontend development.
"""

import random
from datetime import datetime
from typing import Dict, Any
from . import InferenceService, InferenceResult

class MockInferenceService(InferenceService):
    """Mock implementation of InferenceService."""

    def __init__(self):
        # Predefined predictions for variety
        self._predictions = ["Normal", "Pneumonia", "Cardiomegaly", "Edema", "Fracture", "Nodule"]
        self._models = [
            "CheXpert-Pneumonia-DenseNet121 v2.1.0",
            "MIMIC-Cardiomegaly-ResNet50 v1.8.3",
            "NIH-Nodule-EfficientNetB0 v3.0.1"
        ]

    def run_inference(self, request_id: str, model_name: str,
                     adapted_image_path: str = None) -> InferenceResult:
        """Simulate running inference on an image."""
        # Simulate processing time
        import time
        time.sleep(0.1)  # Simulate network delay

        # Generate prediction (weighted toward Normal)
        prediction = random.choices(
            self._predictions,
            weights=[0.4, 0.25, 0.15, 0.1, 0.05, 0.05]
        )[0]

        # Generate confidence scores for all classes
        base_confidence = random.uniform(0.6, 0.9)
        confidence_scores = {}
        remaining = 1.0 - base_confidence

        for i, pred in enumerate(self._predictions):
            if pred == prediction:
                confidence_scores[pred] = base_confidence + random.uniform(0.05, 0.15)
            else:
                # Distribute remaining confidence among other classes
                if i < len(self._predictions) - 1:
                    share = remaining * random.uniform(0.5, 2.0) / (len(self._predictions) - 1)
                    confidence_scores[pred] = share
                    remaining -= share
                else:
                    # Last class gets whatever is left
                    confidence_scores[pred] = max(0, remaining)

        # Normalize to ensure sum is 1.0
        total = sum(confidence_scores.values())
        if total > 0:
            confidence_scores = {k: v/total for k, v in confidence_scores.items()}

        # Get confidence for the predicted class
        prediction_confidence = confidence_scores[prediction]

        # Generate uncertainty metrics
        uncertainty = {
            "aleatoric": round(random.uniform(0.01, 0.08), 3),  # Data uncertainty
            "epistemic": round(random.uniform(0.02, 0.1), 3),   # Model uncertainty
            "total": round(random.uniform(0.05, 0.15), 3)
        }

        # Generate timing metrics
        timing = {
            "preprocessing": round(random.uniform(0.1, 0.5), 2),
            "adaptation": round(random.uniform(0.2, 1.0), 2) if adapted_image_path else 0.0,
            "model_loading": round(random.uniform(0.05, 0.2), 2),
            "inference": round(random.uniform(0.3, 0.8), 2),
            "postprocessing": round(random.uniform(0.05, 0.2), 2),
            "total": 0  # Will calculate
        }
        timing["total"] = sum(timing.values())

        result = InferenceResult(
            request_id=request_id,
            prediction=prediction,
            confidence=prediction_confidence,
            confidence_scores=confidence_scores,
            uncertainty=uncertainty,
            timing=timing,
            model_used=random.choice(self._models),
            adaptation_applied=bool(adapted_image_path),
            drift_score=round(random.uniform(0.1, 0.6), 3) if random.random() > 0.4 else 0.0,
            timestamp=datetime.now()
        )

        return result

    def get_inference_result(self, request_id: str) -> InferenceResult:
        """Get inference result for a request."""
        # In a real implementation, this would retrieve from a database/cache
        # For mock, we'll generate a new one (not ideal but works for demo)
        return self.run_inference(request_id, "unknown_model", None)

# Factory function
def create_inference_service() -> InferenceService:
    """Create an instance of the mock InferenceService."""
    return MockInferenceService()