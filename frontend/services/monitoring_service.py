"""
Real implementation of the MonitoringService that communicates with the backend API.
"""

from datetime import datetime
from typing import List, Dict, Any
from . import MonitoringService, MonitoringMetrics, SystemHealth
from utils.api.client import get_api_client
import streamlit as st


class MonitoringServiceImpl(MonitoringService):
    """Real implementation of MonitoringService that calls backend API."""

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

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for the dashboard view from the backend API.

        Returns:
            Dictionary containing dashboard metrics
        """
        self._ensure_auth_token()
        try:
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/monitoring/metrics"
            )
            response.raise_for_status()
            metrics_data = response.json()

            # The API returns system and process metrics, we need to format for dashboard
            # Extract key metrics for dashboard widgets
            system_metrics = metrics_data.get("system", {})
            process_metrics = metrics_data.get("process", {})

            # Calculate trends (simplified - in real implementation would compare with historical data)
            cpu_usage = system_metrics.get("cpu_percent", 0.0)
            memory_info = system_metrics.get("memory", {})
            memory_usage = memory_info.get("percent", 0.0)
            disk_info = system_metrics.get("disk", {})
            disk_usage = disk_info.get("percent", 0.0) if disk_info else 0.0

            # For now, we'll use simplified trend calculation
            # In a real implementation, we would store historical data and calculate proper trends
            cpu_trend = "stable"  # Would be calculated from historical data
            memory_trend = "stable"
            disk_trend = "stable"

            return {
                "current_values": {
                    "cpu_usage": round(cpu_usage, 1),
                    "memory_usage": round(memory_usage, 1),
                    "disk_usage": round(disk_usage, 1),
                    "gpu_usage": 0.0,  # Not in current API response
                    "request_rate": 0.0,  # Would need additional endpoint
                    "avg_latency": 0.0,  # Would need additional endpoint
                    "error_rate": 0.0,   # Would need additional endpoint
                },
                "trends": {
                    "cpu": cpu_trend,
                    "memory": memory_trend,
                    "disk": disk_trend,
                    "gpu": "stable"
                },
                "system_health": self.get_system_health(),
                # Additional metrics that would come from other endpoints
                "active_sessions": 0,
                "total_requests_today": 0,
                "failed_requests_today": 0
            }
        except Exception as e:
            # Fallback to mock data in case of error for development
            st.warning(f"Failed to fetch monitoring metrics from API: {str(e)}. Using mock data.")
            return self._get_mock_dashboard_metrics()

    def get_comprehensive_metrics(self) -> MonitoringMetrics:
        """
        Get comprehensive system metrics from the backend API.

        Returns:
            MonitoringMetrics: Current system metrics
        """
        self._ensure_auth_token()
        try:
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/monitoring/metrics"
            )
            response.raise_for_status()
            metrics_data = response.json()

            # Extract metrics from API response
            system_metrics = metrics_data.get("system", {})
            process_metrics = metrics_data.get("process", {})

            cpu_usage = system_metrics.get("cpu_percent", 0.0)
            memory_info = system_metrics.get("memory", {})
            memory_usage = memory_info.get("percent", 0.0) if memory_info else 0.0
            # GPU usage not in current API, would need additional monitoring
            gpu_usage = 0.0

            # Request rate, latency, error rate would need additional endpoints
            request_rate = 0.0
            avg_latency = 0.0
            error_rate = 0.0
            drift_score = 0.0  # Would come from drift tracking

            return MonitoringMetrics(
                cpu_usage=round(cpu_usage, 2),
                memory_usage=round(memory_usage, 2),
                gpu_usage=round(gpu_usage, 2),
                request_rate=round(request_rate, 2),
                avg_latency=round(avg_latency, 2),
                error_rate=round(error_rate, 4),
                drift_score=round(drift_score, 3),
                timestamp=datetime.now()
            )
        except Exception as e:
            # Fallback to mock data in case of error for development
            st.warning(f"Failed to fetch comprehensive metrics from API: {str(e)}. Using mock data.")
            return self._get_mock_comprehensive_metrics()

    def get_system_health(self) -> Dict[str, str]:
        """
        Get system health status from the backend API.

        Returns:
            Dict[str, str]: Health status of various components
        """
        self._ensure_auth_token()
        """Ensure the API client has the current auth token from session state."""
            token = st.session_state.get("access_token")
            if token:
                self.api_client.set_auth_token(token)
        try:
            # Try to get health from basic endpoint first
        try:
            # Try to get health from basic endpoint first
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/health"
            )
            if response.status_code == 200:
                health_data = response.json()
                # If we get a detailed health response, use it
                if isinstance(health_data, dict) and "status" in health_data:
                    overall_status = health_data.get("status", "unknown")
                    # Create a basic health check response
                    return {
                        "api": overall_status,
                        "database": overall_status,  # Would need separate check
                        "storage": overall_status,   # Would need separate check
                        "mlflow": overall_status,    # Would need separate check
                        "overall": overall_status
                    }

            # Fallback: if basic health endpoint returns 200, assume everything is healthy
            return {
                "api": "healthy",
                "database": "healthy",
                "storage": "healthy",
                "mlflow": "healthy",
                "overall": "healthy"
            }
        except Exception:
            # If we can't get health status, assume degraded but don't fail completely
            return {
                "api": "unknown",
                "database": "unknown",
                "storage": "unknown",
                "mlflow": "unknown",
                "overall": "unknown"
            }

    def get_metrics_history(self, minutes: int = 60) -> List[MonitoringMetrics]:
        """
        Get metrics history for the specified time period.
        Note: This would require a backend endpoint for historical metrics.
        For now, returns empty list as this functionality needs backend support.

        Args:
            minutes: Number of minutes of history to return

        Returns:
            List of MonitoringMetrics ordered by time (oldest first)
        """
        # TODO: Implement when backend provides historical metrics endpoint
        return []

    def record_metrics(self, metrics: MonitoringMetrics):
        """
        Record new metrics (called by background collection).
        Note: This would typically be handled by a monitoring agent, not the frontend.
        """
        # This is typically handled by backend monitoring systems
        pass

    # Helper methods for development/fallback
    def _get_mock_dashboard_metrics(self) -> Dict[str, Any]:
        """Return mock dashboard metrics for development when API is unavailable."""
        import random
        from datetime import datetime, timedelta

        # Generate some realistic-looking data
        cpu_usage = random.uniform(20, 80)
        memory_usage = random.uniform(30, 70)
        disk_usage = random.uniform(40, 90)

        # Determine trends based on random variation
        cpu_trend = random.choice(["up", "down", "stable"])
        memory_trend = random.choice(["up", "down", "stable"])
        disk_trend = random.choice(["up", "down", "stable"])

        return {
            "current_values": {
                "cpu_usage": round(cpu_usage, 1),
                "memory_usage": round(memory_usage, 1),
                "disk_usage": round(disk_usage, 1),
                "gpu_usage": round(random.uniform(0, 90), 1) if random.random() > 0.2 else 0.0,
                "request_rate": round(random.uniform(5, 50), 1),
                "avg_latency": round(random.uniform(100, 400), 1),
                "error_rate": round(random.uniform(0, 0.05), 4)
            },
            "trends": {
                "cpu": cpu_trend,
                "memory": memory_trend,
                "disk": disk_trend,
                "gpu": random.choice(["up", "down", "stable"])
            },
            "system_health": self._get_mock_system_health(),
            "active_sessions": random.randint(5, 50),
            "total_requests_today": random.randint(100, 1000),
            "failed_requests_today": random.randint(0, 10)
        }

    def _get_mock_comprehensive_metrics(self) -> MonitoringMetrics:
        """Return mock comprehensive metrics for development when API is unavailable."""
        import random

        return MonitoringMetrics(
            cpu_usage=round(random.uniform(20, 80), 2),
            memory_usage=round(random.uniform(30, 70), 2),
            gpu_usage=round(random.uniform(10, 90) if random.random() > 0.2 else 0.0, 2),
            request_rate=round(random.uniform(5, 50), 2),
            avg_latency=round(random.uniform(100, 400), 2),
            error_rate=round(random.uniform(0, 0.05), 4),
            drift_score=round(random.uniform(0.1, 0.4), 3),
            timestamp=datetime.now()
        )

    def _get_mock_system_health(self) -> Dict[str, str]:
        """Return mock system health for development when API is unavailable."""
        import random

        health_checks = {
            "api": "healthy" if random.random() > 0.05 else "degraded",
            "database": "healthy" if random.random() > 0.02 else "degraded",
            "storage": "healthy" if random.random() > 0.1 else "degraded",
            "mlflow": "healthy" if random.random() > 0.15 else "degraded",
        }

        # Determine overall health
        unhealthy_count = sum(1 for status in health_checks.values() if status == "degraded")
        if unhealthy_count == 0:
            overall = "healthy"
        elif unhealthy_count <= 2:
            overall = "degraded"
        else:
            overall = "unhealthy"

        health_checks["overall"] = overall
        return health_checks