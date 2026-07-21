"""
Real implementation of the AlertService that communicates with the backend API.
"""

from datetime import datetime
from typing import List, Optional
from . import AlertService, Alert
from utils.api.client import get_api_client
import streamlit as st


class AlertServiceImpl(AlertService):
    """Real implementation of AlertService that calls backend API."""

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

    def get_active_alerts(self) -> List[Alert]:
        """
        Get currently active (unresolved) alerts.

        Returns:
            List of Alert objects
        """
        self._ensure_auth_token()
        try:
            # Get alerts and filter for unresolved ones
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/alerts"
            )
            response.raise_for_status()
            alerts_data = response.json()

            alerts = []
            for alert_data in alerts_data:
                alert = Alert(
                    alert_id=str(alert_data.get("id", "")),
                    timestamp=alert_data.get("sent_at", ""),
                    hospital="",  # Hospital info not in alert endpoint, would need to join
                    type="",      # Type not in alert endpoint
                    message="",   # Message not in alert endpoint
                    severity=alert_data.get("severity", "info"),
                    acknowledged=False,  # Not tracked in current API
                    resolved=False       # We'll consider alerts returned as active/unresolved
                )
                alerts.append(alert)
            return alerts
        except Exception as e:
            # Fallback to mock data in case of error for development
            st.warning(f"Failed to fetch alerts from API: {str(e)}. Using mock data.")
            return self._get_mock_active_alerts()

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """
        Get alert history.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of Alert objects (most recent first)
        """
        self._ensure_auth_token()
        try:
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/alerts",
                params={"limit": limit}
            )
            response.raise_for_status()
            alerts_data = response.json()

            alerts = []
            for alert_data in alerts_data:
                alert = Alert(
                    alert_id=str(alert_data.get("id", "")),
                    timestamp=alert_data.get("sent_at", ""),
                    hospital="",  # Hospital info not in alert endpoint
                    type="",      # Type not in alert endpoint
                    message="",   # Message not in alert endpoint
                    severity=alert_data.get("severity", "info"),
                    acknowledged=False,  # Not tracked in current API
                    resolved=False       # We don't have resolution info from this endpoint
                )
                alerts.append(alert)
            return alerts
        except Exception as e:
            # Fallback to mock data in case of error for development
            st.warning(f"Failed to fetch alert history from API: {str(e)}. Using mock data.")
            return self._get_mock_alert_history(limit)

    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: ID of the alert to acknowledge

        Returns:
            bool: True if successful
        """
        self._ensure_auth_token()
        try:
            response = self.api_client.session.post(
                f"{self.api_client.base_url}/alerts/{alert_id}/ack"
            )
            response.raise_for_status()
            return True
        except Exception as e:
            st.error(f"Failed to acknowledge alert: {str(e)}")
            return False

    def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an alert.

        Args:
            alert_id: ID of the alert to resolve

        Returns:
            bool: True if successful
        """
        self._ensure_auth_token()
        try:
            response = self.api_client.session.post(
                f"{self.api_client.base_url}/alerts/{alert_id}/resolve"
            )
            response.raise_for_status()
            return True
        except Exception as e:
            st.error(f"Failed to resolve alert: {str(e)}")
            return False

    # Helper methods for development/fallback
    def _get_mock_active_alerts(self) -> List[Alert]:
        """Return mock active alerts for development when API is unavailable."""
        import random
        from datetime import datetime, timedelta

        hospitals = ["General Hospital", "City Medical Center", "University Hospital", "Children's Hospital"]
        alert_types = [
            {"type": "Drift Warning", "message": "Data drift detected exceeding warning threshold", "severity": "warning"},
            {"type": "Drift Alert", "message": "Significant data drift detected requiring attention", "severity": "critical"},
            {"type": "Model Performance Degradation", "message": "Model confidence scores below acceptable threshold", "severity": "warning"},
            {"type": "Processing Error", "message": "Failed to process incoming request", "severity": "error"},
            {"type": "Low Confidence Prediction", "message": "Prediction generated with low confidence score", "severity": "warning"},
            {"type": "System Resource High", "message": "System resource utilization exceeding thresholds", "severity": "warning"},
            {"type": "Feedback Required", "message": "Physician feedback needed for recent predictions", "severity": "info"}
        ]

        alerts = []
        num_alerts = random.randint(5, 15)
        for i in range(num_alerts):
            hours_ago = random.uniform(0, 24)
            timestamp = datetime.now() - timedelta(hours=hours_ago)

            # Only include unresolved alerts (simulate by making older alerts more likely to be resolved)
            is_resolved = hours_ago > 6 and random.random() > 0.3

            if not is_resolved:  # Only return active/unresolved alerts
                alert_type = random.choice(alert_types)
                alert = Alert(
                    alert_id=f"ALT-{str(100000 + i).zfill(6)}",
                    timestamp=timestamp,
                    hospital=random.choice(hospitals),
                    type=alert_type["type"],
                    message=alert_type["message"],
                    severity=alert_type["severity"],
                    acknowledged=hours_ago > 2 and random.random() > 0.5,
                    resolved=False
                )
                alerts.append(alert)

        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        return alerts

    def _get_mock_alert_history(self, limit: int) -> List[Alert]:
        """Return mock alert history for development when API is unavailable."""
        import random
        from datetime import datetime, timedelta

        hospitals = ["General Hospital", "City Medical Center", "University Hospital", "Children's Hospital"]
        alert_types = [
            {"type": "Drift Warning", "message": "Data drift detected exceeding warning threshold", "severity": "warning"},
            {"type": "Drift Alert", "message": "Significant data drift detected requiring attention", "severity": "critical"},
            {"type": "Model Performance Degradation", "message": "Model confidence scores below acceptable threshold", "severity": "warning"},
            {"type": "Processing Error", "message": "Failed to process incoming request", "severity": "error"},
            {"type": "Low Confidence Prediction", "message": "Prediction generated with low confidence score", "severity": "warning"},
            {"type": "System Resource High", "message": "System resource utilization exceeding thresholds", "severity": "warning"},
            {"type": "Feedback Required", "message": "Physician feedback needed for recent predictions", "severity": "info"}
        ]

        alerts = []
        num_alerts = min(limit, random.randint(15, 25))
        for i in range(num_alerts):
            hours_ago = random.uniform(0, 48)
            timestamp = datetime.now() - timedelta(hours=hours_ago)

            alert_type = random.choice(alert_types)
            # Determine if acknowledged/resolved based on age
            is_acknowledged = hours_ago > 2 and random.random() > 0.3
            is_resolved = hours_ago > 6 and random.random() > 0.5

            alert = Alert(
                alert_id=f"ALT-{str(100000 + i).zfill(6)}",
                timestamp=timestamp,
                hospital=random.choice(hospitals),
                type=alert_type["type"],
                message=alert_type["message"],
                severity=alert_type["severity"],
                acknowledged=is_acknowledged,
                resolved=is_resolved
            )
            alerts.append(alert)

        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        return alerts[:limit]