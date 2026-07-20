"""
Mock implementation of the ValidationService for development and testing.
Returns simulated data for frontend development.
"""

import random
from datetime import datetime, timedelta
from typing import List
from . import ValidationService, ValidationResult

class MockValidationService(ValidationService):
    """Mock implementation of ValidationService."""

    def __init__(self):
        self._validation_results: dict = {}  # request_id -> ValidationResult

    def validate_image(self, request_id: str) -> ValidationResult:
        """Simulate validating an image."""
        # Generate mock validation checks
        checks = [
            {
                "check": "File Format",
                "description": "Verify file is a valid DICOM, JPG, or PNG image",
                "pass": True,
                "details": "File format: DICOM",
                "severity": "error"
            },
            {
                "check": "Image Dimensions",
                "description": "Check image dimensions are within expected range (256x256 to 4096x4096)",
                "pass": True,
                "details": "Dimensions: 1024x1024 pixels",
                "severity": "error"
            },
            {
                "check": "Pixel Data Integrity",
                "description": "Verify pixel data is not corrupted or missing",
                "pass": True,
                "details": "All pixel values present and within valid range",
                "severity": "error"
            },
            {
                "check": "Modality Tag",
                "description": "Verify DICOM Modality tag is present and valid",
                "pass": True,
                "details": "Modality: DX (Digital Radiography)",
                "severity": "error"
            },
            {
                "check": "Patient ID Present",
                "description": "Ensure Patient ID is present in metadata",
                "pass": True,
                "details": "Patient ID: MRN123456",
                "severity": "error"
            },
            {
                "check": "Study Date Valid",
                "description": "Verify study date is present and reasonable",
                "pass": True,
                "details": "Study Date: 2024-01-15",
                "severity": "error"
            },
            {
                "check": "Body Part Examined",
                "description": "Check body part is specified and matches image type",
                "pass": random.choice([True, False]),  # Sometimes fail for demo
                "details": "Body Part Examined: CHEST",
                "severity": "warning"
            },
            {
                "check": "Image Orientation",
                "description": "Verify image orientation tags are present",
                "pass": random.choice([True, False]),
                "details": "Patient Orientation: Missing (using default)",
                "severity": "warning"
            },
            {
                "check": "Pixel Spacing",
                "description": "Check pixel spacing values are present and reasonable",
                "pass": True,
                "details": "Pixel Spacing: 0.15x0.15 mm/pixel",
                "severity": "warning"
            }
        ]

        # Determine overall status
        failed_checks = [c for c in checks if not c["pass"]]
        critical_failures = [c for c in failed_checks if c["severity"] == "error"]

        if len(critical_failures) > 0:
            overall_status = "FAIL"
        elif len(failed_checks) > 0:
            overall_status = "WARNING"
        else:
            overall_status = "PASS"

        result = ValidationResult(
            request_id=request_id,
            passed=(overall_status == "PASS"),
            checks=checks,
            timestamp=datetime.now()
        )

        # Store for retrieval
        self._validation_results[request_id] = result
        return result

    def get_validation_result(self, request_id: str) -> ValidationResult:
        """Get validation result for a request."""
        if request_id in self._validation_results:
            return self._validation_results[request_id]
        else:
            # Generate on demand if not cached
            return self.validate_image(request_id)

# Factory function
def create_validation_service() -> ValidationService:
    """Create an instance of the mock ValidationService."""
    return MockValidationService()