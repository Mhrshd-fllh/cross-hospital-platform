"""
Real implementation of the FeedbackService that communicates with the backend API.
"""

import streamlit as st
from datetime import datetime
from typing import List, Optional
from . import FeedbackService, FeedbackResult
from utils.api.client import get_api_client


class FeedbackServiceImpl(FeedbackService):
    """Real implementation of FeedbackService that calls backend API."""

    def _get_client(self):
        """Get API client with auth token from session state."""
        client = get_api_client()
        token = getattr(st.session_state, "access_token", None) if hasattr(st, "session_state") else None
        if token:
            client.set_auth_token(token)
        return client

    def _map_to_feedback_result(self, data: dict) -> FeedbackResult:
        """Convert API response to FeedbackResult dataclass."""
        return FeedbackResult(
            feedback_id=str(data.get("feedback_id", "")),
            request_id=str(data.get("request_id", "")),
            agreed=bool(data.get("is_agreed", False)),
            correct_diagnosis=data.get("corrected_label"),
            comments=None,  # Not in current API response
            timestamp=data.get("submitted_at", datetime.now())
        )

    def submit_feedback(self, request_id: str, agreed: bool,
                       correct_diagnosis: Optional[str] = None,
                       comments: Optional[str] = None) -> FeedbackResult:
        """
        Submit physician feedback for a prediction.

        Args:
            request_id: ID of the request
            agreed: Whether the physician agreed with the prediction
            correct_diagnosis: Correct diagnosis if disagreed
            comments: Additional comments (not currently supported by API)

        Returns:
            FeedbackResult: Information about the submitted feedback
        """
        client = self._get_client()
        try:
            # Prepare data according to API schema
            data = {
                "request_id": request_id,
                "is_agreed": agreed,
                "corrected_label": correct_diagnosis if not agreed else None
            }

            response = client.session.post(
                f"{client.base_url}/feedback/submit",
                json=data
            )

            # Handle response using client's error handling
            response_data = client._handle_response(response)

            # Map response to FeedbackResult
            return FeedbackResult(
                feedback_id="",  # Not returned by current API
                request_id=request_id,
                agreed=agreed,
                correct_diagnosis=correct_diagnosis,
                comments=comments,
                timestamp=datetime.now()
            )
        except Exception as e:
            raise Exception(f"Failed to submit feedback for request {request_id}: {str(e)}")

    def get_feedback_for_request(self, request_id: str) -> List[FeedbackResult]:
        """
        Get feedback for a specific request from the backend API.

        Args:
            request_id: ID of the request

        Returns:
            List of FeedbackResult objects
        """
        client = self._get_client()
        try:
            response = client.session.get(
                f"{client.base_url}/feedback/{request_id}"
            )

            # Handle response using client's error handling
            response_data = client._handle_response(response)

            # Convert list of feedback entries to FeedbackResult objects
            feedback_results = []
            for item in response_data:
                feedback_results.append(self._map_to_feedback_result(item))

            return feedback_results
        except Exception as e:
            # Return empty list on error for graceful degradation
            print(f"Warning: Failed to fetch feedback for request {request_id}: {str(e)}")
            return []

    def get_recent_feedback(self, limit: int = 50) -> List[FeedbackResult]:
        """
        Get recent feedback submissions.
        Note: This would require a backend endpoint that doesn't currently exist.
        For now, returns empty list as this functionality needs backend support.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of recent FeedbackResult objects
        """
        # TODO: Implement when backend provides GET /feedback endpoint with pagination
        return []