"""
Real implementation of the ValidationService that communicates with the backend API.
"""
import streamlit as st
from datetime import datetime
from typing import Optional
from . import ValidationService, ValidationResult
from utils.api.client import get_api_client

class ValidationServiceImpl(ValidationService):
    """Real implementation of ValidationService that calls backend API."""

    def _get_client(self):
        """Get API client with auth token from session state."""
        client = get_api_client()
        token = getattr(st.session_state, "token", None) if hasattr(st, "session_state") else None
        if token:
            client.set_auth_token(token)
        return client

    def _map_to_validation_result(self, data: dict, request_id: str) -> ValidationResult:
        """Convert API response to ValidationResult dataclass."""
        # Extract validation checklist from response
        checklist = data.get("validation_checklist", {})
        # Convert checklist dict to list of check dicts as expected by ValidationResult
        checks = []
        for check_name, passed in checklist.items():
            checks.append({
                "check": check_name.replace("_", " ").title(),
                "description": f"Validation check for {check_name}",
                "pass": bool(passed),
                "details": f"{check_name}: {'PASS' if passed else 'FAIL'}",
                "severity": "error" if not passed else "success"
            })

        # Determine overall passed status
        passed = all(check["pass"] for check in checks) if checks else False

        return ValidationResult(
            request_id=request_id,
            passed=passed,
            checks=checks,
            timestamp=datetime.now()
        )

    def validate_image(self, request_id: str) -> ValidationResult:
        """
        Validate an uploaded image and its metadata by retrieving validation results.

        Args:
            request_id: ID of the request to validate

        Returns:
            ValidationResult: Validation results
        """
        # In this implementation, validation results are retrieved via GET endpoint
        return self.get_validation_result(request_id)

    def get_validation_result(self, request_id: str) -> ValidationResult:
        """
        Get validation result for a request from the backend API.

        Args:
            request_id: ID of the request

        Returns:
            ValidationResult: Validation results
        """
        client = self._get_client()
        try:
            response = client.session.get(
                f"{client.base_url}/validation/{request_id}"
            )
            # Handle response using client's error handling
            data = client._handle_response(response)
            return self._map_to_validation_result(data, request_id)
        except Exception as e:
            # Raise a more informative error
            raise Exception(f"Failed to fetch validation result for request {request_id}: {str(e)}")