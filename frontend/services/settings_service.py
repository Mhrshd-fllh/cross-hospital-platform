"""
Real implementation of the SettingsService that communicates with the backend API.
"""

from typing import Dict, Any, Optional
from . import SettingsService
from utils.api.client import get_api_client
import streamlit as st


class SettingsServiceImpl(SettingsService):
    """Real implementation of SettingsService that calls backend API."""

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

    def get_settings(self) -> Dict[str, Any]:
        """
        Get all system settings from the backend API.

        Returns:
            Dictionary containing all system settings
        """
        self._ensure_auth_token()
        try:
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/settings"
            )
            response.raise_for_status()
            settings_data = response.json()
            return settings_data
        except Exception as e:
            # Fallback to mock data in case of error for development
            st.warning(f"Failed to fetch settings from API: {str(e)}. Using mock data.")
            return self._get_mock_settings()

    def get_setting(self, section: str, key: str) -> Any:
        """
        Get a specific setting value from the backend API.

        Args:
            section: Settings section (e.g., 'system', 'database', 'processing')
            key: Specific setting key within the section

        Returns:
            Setting value if found, None otherwise
        """
        # Get all settings and extract the specific value
        # In a more optimized implementation, we might have a dedicated endpoint
        settings = self.get_settings()
        if section in settings and key in settings[section]:
            return settings[section][key]
        return None

    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled based on settings.

        Args:
            feature: Feature name to check (e.g., 'alerting', 'gpu_acceleration')

        Returns:
            True if feature is enabled, False otherwise
        """
        # Map feature names to their corresponding settings paths
        feature_map = {
            "alerting": ("alerting", "enabled"),
            "gpu_acceleration": ("processing", "inference", "gpu_enabled"),
            "audit_logging": ("security", "audit_logging"),
            "anonymization": ("privacy", "enabled"),  # Assuming this might exist
            "ssl_enforced": ("database", "ssl_mode"),  # Special handling
            "versioning": ("storage", "buckets", "medical-images", "versioning")  # Example path
        }

        if feature in feature_map:
            path = feature_map[feature]
            # Navigate through the nested dictionary
            value = None
            try:
                settings = self.get_settings()
                current = settings
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        return False  # Path doesn't exist
                # Handle special cases
                if feature == "ssl_enforced":
                    # SSL is enabled if mode is not 'disable'
                    return isinstance(value, str) and value.lower() != "disable"
                else:
                    return bool(value)
            except:
                return False
        return False

    # Helper methods for development/fallback
    def _get_mock_settings(self) -> Dict[str, Any]:
        """Return mock settings for development when API is unavailable."""
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

# Factory function
def create_settings_service() -> SettingsService:
    """Create an instance of the SettingsService."""
    return SettingsServiceImpl()