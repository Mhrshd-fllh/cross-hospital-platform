"""
Mock implementation of the SettingsService for development and testing.
Returns simulated data for frontend development.
"""

from datetime import datetime
from typing import Dict, Any
from . import SettingsService

class MockSettingsService(SettingsService):
    """Mock implementation of SettingsService."""

    def __init__(self):
        self._settings = self._generate_mock_settings()

    def _generate_mock_settings(self) -> Dict[str, Any]:
        """Generate mock settings data."""
        return {
            "system": {
                "name": "Cross-Hospital Generalization Platform",
                "version": "1.0.0",
                "environment": "Production",
                "instance_id": "chgp-prod-01",
                "deployment_date": "2024-01-15",
                "last_updated": "2024-06-20"
            },
            "database": {
                "type": "PostgreSQL",
                "version": "15.2",
                "host": "postgres-db.cluster-xyz.us-east-1.rds.amazonaws.com",
                "port": 5432,
                "name": "chgp_db",
                "ssl_mode": "require",
                "backup_frequency": "Daily",
                "retention_period": "30 days"
            },
            "storage": {
                "type": "MinIO",
                "endpoint": "minio-storage.chgp.internal:9000",
                "access_key": "CHGP_MINIO_ACCESS_KEY",
                "secret_key": "**********",  # Masked for security
                "buckets": {
                    "medical-images": {
                        "policy": "private",
                        "versioning": "enabled",
                        "size": "2.4 TB",
                        "object_count": "1,245,678"
                    },
                    "mlflow-artifacts": {
                        "policy": "private",
                        "versioning": "enabled",
                        "size": "180 GB",
                        "object_count": "89,432"
                    }
                }
            },
            "mlflow": {
                "tracking_uri": "http://mlflow-server.chgp.internal:5000",
                "registry_uri": "http://mlflow-server.chgp.internal:5000",
                "experiment_count": 42,
                "registered_models": 12,
                "latest_run": "2024-06-20 14:30:22"
            },
            "processing": {
                "drift_detection": {
                    "method": "MMD (Maximum Mean Discrepancy)",
                    "threshold_warning": 0.3,
                    "threshold_alert": 0.6,
                    "reference_dataset": "CheXpert (v2.1)",
                    "update_frequency": "Monthly"
                },
                "style_adaptation": {
                    "techniques": ["Histogram Normalization", "CLAHE", "AdaIN"],
                    "default_strength": 0.7,
                    "anatomy_preservation_priority": True
                },
                "inference": {
                    "batch_size": 1,
                    "timeout_seconds": 30,
                    "gpu_enabled": True,
                    "max_concurrent_requests": 10
                }
            },
            "alerting": {
                "enabled": True,
                "channels": [
                    {"type": "Slack", "channel": "#alerts-chgp", "enabled": True},
                    {"type": "Email", "address": "ops@hospital.org", "enabled": True},
                    {"type": "Webhook", "url": "https://hooks.example.com/chgp-alerts", "enabled": False}
                ],
                "drift_threshold": 0.6,
                "confidence_threshold": 0.7,
                "cooldown_minutes": 30
            },
            "security": {
                "authentication": "OAuth 2.0 / OpenID Connect",
                "authorization": "RBAC (Role-Based Access Control)",
                "encryption_at_rest": "AES-256",
                "encryption_in_transit": "TLS 1.3",
                "audit_logging": "Enabled",
                "session_timeout": "30 minutes"
            },
            "monitoring": {
                "metrics_collection": "Prometheus",
                "log_aggregation": "ELK Stack",
                "health_checks": "Every 30 seconds",
                "dashboard_refresh": "Every 5 minutes",
                "retention_period": "90 days"
            }
        }

    def get_settings(self) -> Dict[str, Any]:
        """Get all system settings."""
        return self._settings.copy()

    def get_setting(self, section: str, key: str) -> Any:
        """Get a specific setting value."""
        if section in self._settings and key in self._settings[section]:
            return self._settings[section][key]
        return None

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        feature_map = {
            "alerting": lambda: self._settings["alerting"]["enabled"],
            "gpu_acceleration": lambda: self._settings["processing"]["inference"]["gpu_enabled"],
            "audit_logging": lambda: self._settings["security"]["audit_logging"],
            "anonymization": lambda: False  # Placeholder
        }

        if feature in feature_map:
            return feature_map[feature]()
        return False

# Factory function
def create_settings_service() -> SettingsService:
    """Create an instance of the mock SettingsService."""
    return MockSettingsService()