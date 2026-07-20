"""
Mock implementation of the IngestionService for development and testing.
Returns simulated data for frontend development.
"""

import uuid
from datetime import datetime
from typing import List
from . import IngestionService, IngestionResult

class MockIngestionService(IngestionService):
    """Mock implementation of IngestionService."""

    def __init__(self):
        # In a real implementation, this would connect to actual backend services
        self._recent_uploads: List[IngestionResult] = []

    def upload_image(self, image_file, metadata: dict) -> IngestionResult:
        """Simulate uploading an image."""
        # Generate a request ID
        request_id = f"REQ-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

        # Create result
        result = IngestionResult(
            request_id=request_id,
            image_location=f"s3://medical-images/{request_id}.dcm",
            metadata=metadata,
            hospital_id=metadata.get('hospital_id', 'unknown'),
            timestamp=datetime.now()
        )

        # Store for retrieval
        self._recent_uploads.append(result)
        # Keep only last 100 entries
        if len(self._recent_uploads) > 100:
            self._recent_uploads = self._recent_uploads[-100:]

        return result

    def get_recent_uploads(self, limit: int = 10) -> List[IngestionResult]:
        """Get recent uploads."""
        return self._recent_uploads[-limit:][::-1]  # Most recent first

# Factory function
def create_ingestion_service() -> IngestionService:
    """Create an instance of the mock IngestionService."""
    return MockIngestionService()