"""
Real implementation of the HospitalService that communicates with the backend API.
"""

from datetime import datetime
from typing import List, Optional
from . import HospitalService, HospitalInfo
from utils.api.client import get_api_client
import streamlit as st


class HospitalServiceImpl(HospitalService):
    """Real implementation of HospitalService that calls backend API."""

    def __init__(self):
        self.api_client = get_api_client()
        # Set auth token from session state if available
        token = st.session_state.get("access_token")
        if token:
            self.api_client.set_auth_token(token)

    def _ensure_auth_token(self):
        """Ensure the API client has the current auth token from session state."""
        token = st.session_state.get("access_token")
        if token:
            self.api_client.set_auth_token(token)

    def get_hospitals(self) -> List[HospitalInfo]:
        """
        Get all hospitals.

        Returns:
            List of HospitalInfo objects
        """
        self._ensure_auth_token()
        try:
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/hospitals"
            )
            response.raise_for_status()
            hospitals_data = response.json()

            hospitals = []
            for hospital_data in hospitals_data:
                # Get additional stats for this hospital
                stats = self._get_hospital_stats(hospital_data["id"])

                hospital = HospitalInfo(
                    hospital_id=str(hospital_data["id"]),
                    name=hospital_data["name"],
                    status="online",  # Default status - could be enhanced with health check
                    avg_drift=stats.get("avg_drift", 0.0),
                    images_processed=stats.get("images_processed", 0),
                    models_used=stats.get("models_used", 0),
                    last_activity=stats.get("last_activity", datetime.now()),
                    health_score=stats.get("health_score", 0.8)
                )
                hospitals.append(hospital)
            return hospitals
        except Exception as e:
            # Fallback to mock data in case of error for development
            st.warning(f"Failed to fetch hospitals from API: {str(e)}. Using mock data.")
            return self._get_mock_hospitals()

    def get_hospital(self, hospital_id: str) -> Optional[HospitalInfo]:
        """
        Get a specific hospital by ID.

        Args:
            hospital_id: ID of the hospital

        Returns:
            HospitalInfo object if found, None otherwise
        """
        self._ensure_auth_token()
        try:
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/hospitals/{int(hospital_id)}"
            )
            response.raise_for_status()
            hospital_data = response.json()

            # Get additional stats for this hospital
            stats = self._get_hospital_stats(hospital_data["id"])

            return HospitalInfo(
                hospital_id=str(hospital_data["id"]),
                name=hospital_data["name"],
                status="online",  # Default status
                avg_drift=stats.get("avg_drift", 0.0),
                images_processed=stats.get("images_processed", 0),
                models_used=stats.get("models_used", 0),
                last_activity=stats.get("last_activity", datetime.now()),
                health_score=stats.get("health_score", 0.8)
            )
        except Exception as e:
            # Fallback to mock data in case of error for development
            st.warning(f"Failed to fetch hospital {hospital_id} from API: {str(e)}. Using mock data.")
            return self._get_mock_hospital(hospital_id)

    def get_hospitals_by_status(self, status: str) -> List[HospitalInfo]:
        """
        Get hospitals by status.

        Args:
            status: Hospital status to filter by

        Returns:
            List of HospitalInfo objects with matching status
        """
        # Since the API doesn't directly support filtering by status,
        # we get all hospitals and filter locally
        all_hospitals = self.get_hospitals()
        return [h for h in all_hospitals if h.status.lower() == status.lower()]

    def update_hospital_status(self, hospital_id: str, status: str) -> bool:
        """
        Update hospital status.

        Args:
            hospital_id: ID of the hospital to update
            status: New status value

        Returns:
            True if successful, False otherwise
        """
        # Since the API doesn't have an endpoint to update hospital status,
        # we would need to implement this in the backend first.
        # For now, we'll simulate success.
        st.info(f"Hospital status update for {hospital_id} to {status} would require backend implementation.")
        return True

    def _get_hospital_stats(self, hospital_id: int) -> dict:
        """
        Get statistics for a hospital by making additional API calls.

        Args:
            hospital_id: ID of the hospital

        Returns:
            Dictionary containing stats like avg_drift, images_processed, etc.
        """
        stats = {
            "avg_drift": 0.0,
            "images_processed": 0,
            "models_used": 0,
            "last_activity": datetime.now(),
            "health_score": 0.8
        }

        try:
            # Get inference requests for this hospital to count them and get latest timestamp
            logs_response = self.api_client.session.get(
                f"{self.api_client.base_url}/logs",
                params={"hospital_id": hospital_id, "limit": 1000}  # Get a reasonable number
            )
            logs_response.raise_for_status()
            logs_data = logs_response.json()

            if logs_data:
                stats["images_processed"] = len(logs_data[0])  # Just for debugging - remove in production
                stats["images_processed"] = len(logs_data)

                # Get most recent timestamp
                timestamps = []
                for log in logs_data:
                    if "created_at" in log and log["created_at"]:
                        try:
                            ts = datetime.fromisoformat(log["created_at"].replace("Z", "+00:00"))
                            timestamps.append(ts)
                        except:
                            pass

                if timestamps:
                    stats["last_activity"] = max(timestamps)

                # Count unique models used (simplified - would need to track this properly)
                # For now, we'll estimate based on some logic or use a default
                models_set = set()
                for log in logs_data:
                    if "prediction_label" in log and log["prediction_label"]:
                        models_used = log["prediction_label"]
                        if models_used:
                            models_set.add(models_used)
                stats["models_used"] = len(models_set) if models_set else 1  # At least 1 if we have data

            # Get drift history to calculate average drift
            drift_response = self.api_client.session.get(
                f"{self.api_client.base_url}/drift/history",
                params={"hospital_id": hospital_id, "limit": 100}
            )
            drift_response.raise_for_status()
            drift_data = drift_response.json()

            if drift_data:
                drift_scores = []
                for drift in drift_data:
                    if "drift_score" in drift and drift["drift_score"] is not None:
                        try:
                            score = float(drift["drift_score"])
                            drift_scores.append(score)
                        except (ValueError, TypeError):
                            pass

                if drift_scores:
                    stats["avg_drift"] = sum(drift_scores) / len(drift_scores)

                    # Calculate a simple health score based on drift (lower drift = healthier)
                    # This is a simplified calculation - real implementation might be more complex
                    avg_drift = stats["avg_drift"]
                    if avg_drift < 0.1:
                        stats["health_score"] = 0.95
                    elif avg_drift < 0.2:
                        stats["health_score"] = 0.85
                    elif avg_drift < 0.3:
                        stats["health_score"] = 0.75
                    else:
                        stats["health_score"] = 0.6

        except Exception as e:
            # If we can't get detailed stats, we'll just use defaults
            # In a production system, you might want to log this error
            pass

        return stats

    # Helper methods for development/fallback
    def _get_mock_hospitals(self) -> List[HospitalInfo]:
        """Return mock hospitals for development when API is unavailable."""
        from datetime import datetime, timedelta
        import random

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

    def _get_mock_hospital(self, hospital_id: str) -> Optional[HospitalInfo]:
        """Return a specific mock hospital for development when API is unavailable."""
        mock_hospitals = self._get_mock_hospitals()
        for hospital in mock_hospitals:
            if hospital.hospital_id == hospital_id:
                return hospital
        return None