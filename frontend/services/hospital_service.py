"""
Mock implementation of the HospitalService for development and testing.
Returns simulated data for frontend development.
"""

import random
from datetime import datetime, timedelta
from typing import List, Optional
from . import HospitalService, HospitalInfo

class MockHospitalService(HospitalService):
    """Mock implementation of HospitalService."""

    def __init__(self):
        self._hospitals: List[HospitalInfo] = self._generate_mock_hospitals()

    def _generate_mock_hospitals(self) -> List[HospitalInfo]:
        """Generate mock hospital data."""
        hospitals = [
            HospitalInfo(
                hospital_id="H001",
                name="General Hospital",
                status="online",
                avg_drift=0.23,
                images_processed=1245,
                models_used=3,
                last_activity=datetime.now() - timedelta(hours=2),
                health_score=0.92
            ),
            HospitalInfo(
                hospital_id="H002",
                name="City Medical Center",
                status="online",
                avg_drift=0.31,
                images_processed=987,
                models_used=2,
                last_activity=datetime.now() - timedelta(hours=0.75),  # 45 minutes
                health_score=0.88
            ),
            HospitalInfo(
                hospital_id="H003",
                name="University Hospital",
                status="online",
                avg_drift=0.18,
                images_processed=2156,
                models_used=4,
                last_activity=datetime.now() - timedelta(hours=0.25),  # 15 minutes
                health_score=0.95
            ),
            HospitalInfo(
                hospital_id="H004",
                name="Children's Hospital",
                status="online",
                avg_drift=0.27,
                images_processed=654,
                models_used=2,
                last_activity=datetime.now() - timedelta(hours=3),
                health_score=0.90
            ),
            HospitalInfo(
                hospital_id="H005",
                name="County Hospital",
                status="offline",
                avg_drift=0.45,
                images_processed=321,
                models_used=1,
                last_activity=datetime.now() - timedelta(days=2),
                health_score=0.65
            )
        ]
        return hospitals

    def get_hospitals(self) -> List[HospitalInfo]:
        """Get all hospitals."""
        return self._hospitals.copy()

    def get_hospital(self, hospital_id: str) -> Optional[HospitalInfo]:
        """Get a specific hospital by ID."""
        for hospital in self._hospitals:
            if hospital.hospital_id == hospital_id:
                return hospital
        return None

    def get_hospitals_by_status(self, status: str) -> List[HospitalInfo]:
        """Get hospitals by status."""
        return [hospital for hospital in self._hospitals if hospital.status == status.lower()]

    def update_hospital_status(self, hospital_id: str, status: str) -> bool:
        """Update hospital status."""
        hospital = self.get_hospital(hospital_id)
        if hospital:
            hospital.status = status.lower()
            hospital.last_activity = datetime.now()
            return True
        return False

# Factory function
def create_hospital_service() -> HospitalService:
    """Create an instance of the mock HospitalService."""
    return MockHospitalService()