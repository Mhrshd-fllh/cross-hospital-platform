"""
API client for communicating with the backend services.
"""
import json
from typing import Dict, Any, Optional, BinaryIO
import requests
from urllib.parse import urljoin

# Base URL for the backend API
API_BASE_URL = "http://localhost:8000"  # Default to local development

class APIClient:
    """Client for interacting with the backend REST API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def set_auth_token(self, token: str):
        """Set authorization token for requests."""
        self.session.headers.update({
            "Authorization": f"Bearer {token}"
        })
    
    def _handle_response(self, response: requests.Response) -> dict:
        """Handle HTTP response and raise appropriate exceptions."""
        try:
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            # Try to get error details from response
            try:
                error_detail = response.json()
                raise Exception(f"API Error: {error_detail.get('detail', str(e))}")
            except:
                raise Exception(f"API Error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    # Ingestion Service Methods
    def upload_medical_image(self, file: BinaryIO, filename: str, metadata: dict) -> dict:
        """Upload a medical image and start the processing pipeline."""
        files = {"file": (filename, file)}
        data = {
            "hospital_id": str(metadata.get("hospital_id", 1)),
            "metadata_json": json.dumps(metadata)
        }
        response = self.session.post(
            urljoin(self.base_url, "/v1/clinical/inference/ingest"),
            files=files,
            data=data
        )
        return self._handle_response(response)
    
    # Feedback Service Methods
    def submit_feedback(self, request_id: str, agreed: bool, corrected_label: Optional[str] = None) -> dict:
        """Submit physician feedback for a prediction."""
        data = {
            "request_id": request_id,
            "is_agreed": agreed,
            "corrected_label": corrected_label
        }
        response = self.session.post(
            urljoin(self.base_url, "/v1/clinical/feedback/submit"),
            json=data
        )
        return self._handle_response(response)
    
    # Additional methods for fetching data will be added as needed
    def get_recent_uploads(self, limit: int = 10) -> list:
        """Get recent uploads (placeholder - would need backend endpoint)."""
        # This would need a backend endpoint to fetch recent uploads
        # For now, we'll return empty list and note that this needs backend support
        return []
    
    def get_drift_result(self, request_id: str) -> dict:
        """Get drift detection results for a request."""
        # This would need a backend endpoint
        return {}
    
    def get_model_registry(self) -> list:
        """Get list of registered models."""
        # This would need a backend endpoint
        return []

# Global API client instance
api_client = APIClient()

def get_api_client() -> APIClient:
    """Get the global API client instance."""
    return api_client
