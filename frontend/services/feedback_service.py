"""
Mock implementation of the FeedbackService for development and testing.
Returns simulated data for frontend development.
"""

import random
from datetime import datetime, timedelta
from typing import List, Optional
from . import FeedbackService, FeedbackResult

class MockFeedbackService(FeedbackService):
    """Mock implementation of FeedbackService."""

    def __init__(self):
        self._feedback_store: List[FeedbackResult] = []
        self._generate_initial_feedback()

    def _generate_initial_feedback(self):
        """Generate some initial feedback data."""
        hospitals = ["General Hospital", "City Medical Center", "University Hospital", "Children's Hospital"]
        predictions = ["Normal", "Pneumonia", "Cardiomegaly", "Edema", "Fracture", "Nodule"]
        physicians = ["Dr. Smith", "Dr. Johnson", "Dr. Williams", "Dr. Brown", "Dr. Jones"]

        # Generate 50-100 feedback entries
        num_entries = random.randint(50, 100)
        for i in range(num_entries):
            # Random timestamp in the last 14 days
            days_ago = random.uniform(0, 14)
            timestamp = datetime.now() - timedelta(days=days_ago)

            # Determine agreement (biased toward agreement)
            agreed = random.choices([True, False], weights=[0.75, 0.25])[0]

            feedback = FeedbackResult(
                feedback_id=f"FB-{str(100000 + i).zfill(6)}",
                request_id=f"REQ-{timestamp.strftime('%Y%m%d')}-{str(200000 + i).zfill(6)}",
                hospital=random.choice(hospitals),
                prediction=random.choice(predictions),
                confidence=round(random.uniform(0.6, 0.95), 2),
                agreed=agreed,
                correct_diagnosis=random.choice(predictions) if not agreed else None,
                comments=self._generate_comments(agreed, random.choice(predictions) if not agreed else None),
                physician_name=random.choice(physicians),
                physician_id=f"DR{random.randint(100, 999):03d}",
                ground_truth_available=random.choice([True, False]) if not agreed else False,
                ground_truth=random.choice(predictions) if not agreed and random.choice([True, False]) else "",
                timestamp=timestamp
            )
            self._feedback_store.append(feedback)

        # Sort by timestamp (newest first)
        self._feedback_store.sort(key=lambda x: x.timestamp, reverse=True)

    def _generate_comments(self, agreed: bool, correct_diagnosis: Optional[str]) -> str:
        """Generate realistic feedback comments."""
        if agreed:
            positive_comments = [
                "The AI assessment aligns with my clinical judgment.",
                "Good detection of the abnormality.",
                "The analysis was accurate and helpful.",
                "I agree with the AI's findings.",
                "The detection was spot-on.",
                "This matches what I observed in the image.",
                "The AI correctly identified the pathology.",
                "Confident in this assessment.",
                "Well done on the detection.",
                "The analysis is clinically relevant."
            ]
            return random.choice(positive_comments)
        else:
            # Constructive disagreement comments
            if random.random() < 0.7:  # Most disagreements have specific feedback
                return f"I believe this shows signs of {correct_diagnosis.lower()} which the AI missed. Upon closer review, there are subtle indicators that suggest this diagnosis."
            else:
                return "I disagree with the AI assessment. The clinical presentation suggests a different diagnosis."

    def submit_feedback(self, request_id: str, agreed: bool,
                       correct_diagnosis: Optional[str] = None,
                       comments: Optional[str] = None) -> FeedbackResult:
        """Submit physician feedback."""
        # Generate feedback ID
        feedback_id = f"FB-{str(100000 + len(self._feedback_store)).zfill(6)}"

        # Get request info (in real system, would fetch from database)
        # For mock, we'll create plausible data
        hospitals = ["General Hospital", "City Medical Center", "University Hospital", "Children's Hospital"]
        predictions = ["Normal", "Pneumonia", "Cardiomegaly", "Edema", "Fracture", "Nodule"]
        physicians = ["Dr. Smith", "Dr. Johnson", "Dr. Williams", "Dr. Brown", "Dr. Jones"]

        feedback = FeedbackResult(
            feedback_id=feedback_id,
            request_id=request_id,
            hospital=random.choice(hospitals),
            prediction=random.choice(predictions),
            confidence=round(random.uniform(0.6, 0.95), 2),
            agreed=agreed,
            correct_diagnosis=correct_diagnosis if not agreed else None,
            comments=comments or self._generate_comments(agreed, correct_diagnosis),
            physician_name=random.choice(physicians),
            physician_id=f"DR{random.randint(100, 999):03d}",
            ground_truth_available=bool(correct_diagnosis and not agreed),
            ground_truth=correct_diagnosis if (correct_diagnosis and not agreed) else "",
            timestamp=datetime.now()
        )

        self._feedback_store.insert(0, feedback)  # Add to beginning (most recent)
        return feedback

    def get_feedback_for_request(self, request_id: str) -> List[FeedbackResult]:
        """Get feedback for a specific request."""
        return [fb for fb in self._feedback_store if fb.request_id == request_id]

    def get_recent_feedback(self, limit: int = 50) -> List[FeedbackResult]:
        """Get recent feedback submissions."""
        return self._feedback_store[:min(limit, len(self._feedback_store))]

    def get_feedback_statistics(self) -> Dict[str, Any]:
        """Get feedback statistics."""
        if not self._feedback_store:
            return {
                "total_feedback": 0,
                "agreement_rate": 0.0,
                "disagreement_rate": 0.0,
                "average_response_time_hours": 0.0
            }

        total = len(self._feedback_store)
        agreed_count = sum(1 for fb in self._feedback_store if fb.agreed)
        agreement_rate = agreed_count / total if total > 0 else 0.0

        # Calculate average response time (simplified)
        # In reality, would compare feedback timestamp to request timestamp
        avg_response_hours = random.uniform(2.0, 8.0)

        return {
            "total_feedback": total,
            "agreement_rate": round(agreement_rate, 3),
            "disagreement_rate": round(1.0 - agreement_rate, 3),
            "average_response_time_hours": round(avg_response_hours, 1)
        }

# Factory function
def create_feedback_service() -> FeedbackService:
    """Create an instance of the mock FeedbackService."""
    return MockFeedbackService()