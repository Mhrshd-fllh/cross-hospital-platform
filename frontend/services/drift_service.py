"""
Mock implementation of the DriftService for development and testing.
Returns simulated data for frontend development.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict
from . import DriftService, DriftResult

class MockDriftService(DriftService):
    """Mock implementation of DriftService."""

    def __init__(self):
        self._drift_results: dict = {}  # request_id -> DriftResult
        self._drift_history: List[DriftResult] = []

    def detect_drift(self, request_id: str) -> DriftResult:
        """Simulate drift detection."""
        # Generate a realistic drift score
        # Most requests have low drift, occasional high drift
        drift_score = random.betavariate(2, 5)  # Skewed toward lower values
        # Occasionally inject higher drift values
        if random.random() < 0.1:  # 10% chance of higher drift
            drift_score = random.uniform(0.4, 0.8)

        # Determine status based on score
        if drift_score < 0.3:
            status = "Low"
        elif drift_score < 0.6:
            status = "Medium"
        elif drift_score < 0.8:
            status = "High"
        else:
            status = "Critical"

        # Generate feature-level drift
        feature_drift = {
            "Histogram": round(random.uniform(0.1, 0.6), 3),
            "FFT": round(random.uniform(0.1, 0.6), 3),
            "LBP": round(random.uniform(0.1, 0.6), 3),
            "Sharpness": round(random.uniform(0.1, 0.6), 3)
        }

        # Generate distribution comparison data (simplified)
        reference_distribution = [random.uniform(0.05, 0.15) for _ in range(10)]
        current_distribution = [random.uniform(0.05, 0.15) for _ in range(10)]

        result = DriftResult(
            request_id=request_id,
            drift_score=drift_score,
            status=status,
            timestamp=datetime.now(),
            feature_drift=feature_drift,
            reference_distribution=reference_distribution,
            current_distribution=current_distribution,
            metric_used="MMD (Maximum Mean Discrepancy)",
            metric_value=round(random.uniform(0.1, 0.8), 4),
            p_value=round(random.uniform(0.001, 0.1), 4),
            reference_hospital="CheXpert (Training)",
            target_hospital="General Hospital"
        )

        # Store for retrieval and history
        self._drift_results[request_id] = result
        self._drift_history.append(result)
        # Keep only last 1000 history entries
        if len(self._drift_history) > 1000:
            self._drift_history = self._drift_history[-1000:]

        return result

    def get_drift_result(self, request_id: str) -> DriftResult:
        """Get drift result for a request."""
        if request_id in self._drift_results:
            return self._drift_results[request_id]
        else:
            # Generate on demand if not cached
            return self.detect_drift(request_id)

    def get_drift_history(self, hospital_id: str, limit: int = 100) -> List[DriftResult]:
        """Get drift detection history for a hospital."""
        # Filter by hospital_id (in a real implementation)
        # For mock, just return recent results
        return self._drift_history[-limit:][::-1]  # Most recent first

# Factory function
def create_drift_service() -> DriftService:
    """Create an instance of the mock DriftService."""
    return MockDriftService()