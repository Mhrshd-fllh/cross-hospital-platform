"""
Mock implementation of the AlertService for development and testing.
Returns simulated data for frontend development.
"""

import random
from datetime import datetime, timedelta
from typing import List, Optional
from . import AlertService, Alert

class MockAlertService(AlertService):
    """Mock implementation of AlertService."""

    def __init__(self):
        self._alerts: List[Alert] = []
        self._acknowledged_alerts: set = set()
        self._resolved_alerts: set = set()
        self._generate_initial_alerts()

    def _generate_initial_alerts(self):
        """Generate some initial alert data."""
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

        # Generate 15-25 alerts
        num_alerts = random.randint(15, 25)
        for i in range(num_alerts):
            # Random timestamp in the last 48 hours
            hours_ago = random.uniform(0, 48)
            timestamp = datetime.now() - timedelta(hours=hours_ago)

            alert_type = random.choice(alert_types)

            # Determine if alert is acknowledged/resolved based on age and randomness
            is_acknowledged = hours_ago > 2 and random.random() > 0.3  # Older alerts more likely to be acknowledged
            is_resolved = hours_ago > 6 and random.random() > 0.5  # Much older alerts more likely to be resolved

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
            self._alerts.append(alert)

            # Track acknowledged/resolved alerts
            if is_acknowledged:
                self._acknowledged_alerts.add(alert.alert_id)
            if is_resolved:
                self._resolved_alerts.add(alert.alert_id)

        # Sort by timestamp (newest first)
        self._alerts.sort(key=lambda x: x.timestamp, reverse=True)

    def get_active_alerts(self) -> List[Alert]:
        """Get currently active (unresolved) alerts."""
        return [alert for alert in self._alerts if not alert.resolved]

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """
        Get alert history.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of Alert objects (most recent first)
        """
        return self._alerts[:min(limit, len(self._alerts))]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: ID of the alert to acknowledge

        Returns:
            bool: True if successful
        """
        # Find the alert
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                if not alert.acknowledged:
                    alert.acknowledged = True
                    self._acknowledged_alerts.add(alert_id)
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an alert.

        Args:
            alert_id: ID of the alert to resolve

        Returns:
            bool: True if successful
        """
        # Find the alert
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                if not alert.resolved:
                    alert.resolved = True
                    self._resolved_alerts.add(alert_id)
                return True
        return False

    def get_alerts_by_severity(self, severity: str) -> List[Alert]:
        """Get alerts by severity level."""
        return [alert for alert in self._alerts if alert.severity == severity.lower()]

    def get_alerts_by_hospital(self, hospital: str) -> List[Alert]:
        """Get alerts for a specific hospital."""
        return [alert for alert in self._alerts if alert.hospital == hospital]

# Factory function
def create_alert_service() -> AlertService:
    """Create an instance of the mock AlertService."""
    return MockAlertService()