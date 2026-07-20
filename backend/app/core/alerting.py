"""
Alerting service for drift detection.
Reads webhook URL and threshold from environment variables.
"""
import os
import json
import logging
from typing import Dict, Any
import asyncio
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.platform_models import AlertLog, DriftLog

logger = logging.getLogger(__name__)

class AlertingService:
    """
    Sends alerts when drift exceeds a configured threshold.
    """
    def __init__(self):
        self.webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        # Threshold for p-value: if p-value < this, consider it an alert
        self.pvalue_threshold = float(os.getenv("DRIFT_PVALUE_THRESHOLD", "0.05"))
        # If no webhook URL is set, we only log and store in DB
        if not self.webhook_url:
            logger.warning("ALERT_WEBHOOK_URL not set; alerts will be logged and stored only.")

    async def send_alert(self, drift_log_id: int, p_value: float, session: AsyncSession) -> None:
        """
        Evaluate whether to send an alert based on p-value and threshold.
        If alert is triggered, store an AlertLog entry and send a webhook notification.

        Parameters
        ----------
        drift_log_id : int
            ID of the DriftLog entry associated with this alert check.
        p_value : float
            The overall p-value from MMDDrift.
        session : AsyncSession
            Database session for persisting the alert.
        """
        is_alert = p_value < self.pvalue_threshold
        if not is_alert:
            return

        # Determine severity based on p-value (could be more sophisticated)
        if p_value < 0.01:
            severity = "Critical"
        else:
            severity = "Warning"

        # Persist alert
        alert_entry = AlertLog(
            drift_log_id=drift_log_id,
            threshold_used=self.pvalue_threshold,
            severity=severity,
            channel="webhook" if self.webhook_url else "none",
            sent_at=None  # will be set by DB default
        )
        session.add(alert_entry)
        await session.flush()  # Get ID if needed, but we don't need it now

        # Prepare webhook payload (simple text message)
        message = {
            "text": f":rotating_light: *Drift Alert* (severity: {severity})\n"
                    f"Drift log ID: {drift_log_id}\n"
                    f"P-value: {p_value:.6f} (threshold: {self.pvalue_threshold})\n"
                    f"Time: {asyncio.get_event_loop().time()}"
        }

        # Send webhook if configured
        if self.webhook_url:
            try:
                # Use httpx.AsyncClient for async HTTP POST
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.webhook_url,
                        json=message,
                        timeout=10.0
                    )
                    response.raise_for_status()
                logger.info(f"Alert sent to webhook for drift log {drift_log_id}")
            except Exception as e:
                logger.error(f"Failed to send alert webhook: {e}")
                # We still logged the alert in DB, so we don't raise
        else:
            logger.info(f"Alert logged (no webhook) for drift log {drift_log_id}: p={p_value}")