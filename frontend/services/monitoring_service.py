"""
Mock implementation of the MonitoringService for development and testing.
Returns simulated data for frontend development.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from . import MonitoringService, MonitoringMetrics, SystemHealth

class MockMonitoringService(MonitoringService):
    """Mock implementation of MonitoringService."""

    def __init__(self):
        # Generate some historical data for trending
        self._metrics_history: List[MonitoringMetrics] = []
        self._generate_initial_history()

    def _generate_initial_history(self):
        """Generate initial historical data."""
        now = datetime.now()
        for i in range(100):  # Last 100 time points
            timestamp = now - timedelta(minutes=i*5)  # 5 minute intervals
            metrics = MonitoringMetrics(
                cpu_usage=random.uniform(20, 80),
                memory_usage=random.uniform(30, 70),
                gpu_usage=random.uniform(10, 90) if random.random() > 0.2 else 0.0,
                request_rate=random.uniform(5, 50),
                avg_latency=random.uniform(100, 400),
                error_rate=random.uniform(0, 0.05),
                drift_score=random.uniform(0.1, 0.4),
                timestamp=timestamp
            )
            # Occasionally inject higher drift
            if random.random() < 0.1:
                metrics.drift_score = random.uniform(0.5, 0.8)
            self._metrics_history.append(metrics)
        # Sort by timestamp (oldest first)
        self._metrics_history.sort(key=lambda x: x.timestamp)

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get metrics for the dashboard view."""
        if not self._metrics_history:
            return self._get_empty_metrics()

        latest = self._metrics_history[-1]

        # Calculate trends (simple: compare to previous)
        if len(self._metrics_history) >= 2:
            previous = self._metrics_history[-2]
            cpu_trend = "up" if latest.cpu_usage > previous.cpu_usage else "down"
            memory_trend = "up" if latest.memory_usage > previous.memory_usage else "down"
            latency_trend = "down" if latest.avg_latency < previous.avg_latency else "up"  # Lower is better
            drift_trend = "up" if latest.drift_score > previous.drift_score else "down"
        else:
            cpu_trend = memory_trend = latency_trend = drift_trend = "stable"

        return {
            "current_values": {
                "cpu_usage": round(latest.cpu_usage, 1),
                "memory_usage": round(latest.memory_usage, 1),
                "gpu_usage": round(latest.gpu_usage, 1),
                "request_rate": round(latest.request_rate, 1),
                "avg_latency": round(latest.avg_latency, 1),
                "error_rate": round(latest.error_rate * 100, 2),  # As percentage
                "drift_score": round(latest.drift_score, 3)
            },
            "trends": {
                "cpu": cpu_trend,
                "memory": memory_trend,
                "latency": latency_trend,
                "drift": drift_trend
            },
            "system_health": self.get_system_health(),
            "alerts": {
                "active": random.randint(0, 5),
                "warnings_24h": random.randint(5, 15),
                "critical_24h": random.randint(0, 3),
                "resolved_24h": random.randint(8, 20)
            }
        }

    def get_comprehensive_metrics(self) -> MonitoringMetrics:
        """Get comprehensive system metrics."""
        if not self._metrics_history:
            return self._get_empty_metrics()
        return self._metrics_history[-1]

    def get_system_health(self) -> Dict[str, str]:
        """Get system health status of components."""
        # Simulate health checks
        health_checks = {
            "api": "healthy" if random.random() > 0.05 else "degraded",
            "database": "healthy" if random.random() > 0.02 else "degraded",
            "storage": "healthy" if random.random() > 0.1 else "degraded",
            "mlflow": "healthy" if random.random() > 0.15 else "degraded",
            "ingestion": "healthy" if random.random() > 0.05 else "degraded",
            "validation": "healthy" if random.random() > 0.05 else "degraded",
            "drift_detection": "healthy" if random.random() > 0.1 else "degraded",
            "adaptation": "healthy" if random.random() > 0.1 else "degraded",
            "inference": "healthy" if random.random() > 0.05 else "degraded"
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

    def get_metrics_history(self, minutes: int = 60) -> List[MonitoringMetrics]:
        """
        Get metrics history for the specified time period.

        Args:
            minutes: Number of minutes of history to return

        Returns:
            List of MonitoringMetrics ordered by time (oldest first)
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [m for m in self._metrics_history if m.timestamp >= cutoff_time]

    def record_metrics(self, metrics: MonitoringMetrics):
        """Record new metrics (called by background collection)."""
        self._metrics_history.append(metrics)
        # Keep only last 1000 entries
        if len(self._metrics_history) > 1000:
            self._metrics_history = self._metrics_history[-1000:]

    def _get_empty_metrics(self) -> MonitoringMetrics:
        """Return empty/default metrics when no data is available."""
        return MonitoringMetrics(
            cpu_usage=0.0,
            memory_usage=0.0,
            gpu_usage=0.0,
            request_rate=0.0,
            avg_latency=0.0,
            error_rate=0.0,
            drift_score=0.0,
            timestamp=datetime.now()
        )

# Factory function
def create_monitoring_service() -> MonitoringService:
    """Create an instance of the mock MonitoringService."""
    return MockMonitoringService()