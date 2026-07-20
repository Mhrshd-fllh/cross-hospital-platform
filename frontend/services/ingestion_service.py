"""
Real implementation of the IngestionService that communicates with the backend API.
"""

from datetime import datetime
from typing import List
import json
from . import IngestionService, IngestionResult
from utils.api.client import get_api_client

class IngestionServiceImpl(IngestionService):
    """Real implementation of IngestionService that calls backend API."""
    
    # Class-level cache to store API responses by request_id
    _cache = {}

    def __init__(self):
        self.api_client = get_api_client()

    def upload_image(self, image_file, metadata: dict) -> IngestionResult:
        """Upload an image via the backend API and return results."""
        # Call the backend API to upload and process the image
        api_response = self.api_client.upload_medical_image(
            file=image_file,
            filename=getattr(image_file, 'name', 'uploaded_file'),
            metadata=metadata
        )
        
        # Store the full API response in the cache for other services to use
        request_id = str(api_response.get("request_id", ""))
        if request_id:
            self._cache[request_id] = api_response
        
        # Convert API response to IngestionResult
        result = IngestionResult(
            request_id=request_id,
            image_location=api_response.get("image_s3_uri", ""),
            metadata=metadata,
            hospital_id=metadata.get('hospital_id', 'unknown'),
            timestamp=datetime.now()
        )
        
        return result

    def get_recent_uploads(self, limit: int = 10) -> List[IngestionResult]:
        """Get recent uploads.
        
        Note: This would require a backend endpoint to fetch recent uploads.
        For now, returning empty list as this functionality needs backend support.
        """
        # TODO: Implement when backend provides GET /recent-uploads endpoint
        return []

    @classmethod
    def get_cached_data(cls, request_id: str) -> dict:
        """Get cached API response data for a request_id."""
        return cls._cache.get(request_id, {})

