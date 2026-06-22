import time
import sys
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from backend.app.models.platform_models import InferenceRequest, DriftLog

class ClinicalTelemetryTracker:
    """
    Dedicated backend operation tracker to monitor inference latency, 
    log processing pipeline errors, and handle precise atomic metrics database commits.
    """
    
    def __init__(self, db_session: AsyncSession, request_id: UUID):
        self.db = db_session
        self.request_id = request_id
        self.start_time = None

    def start_timing(self):
        """Starts the high-resolution performance counter."""
        self.start_time = time.perf_counter()

    def get_current_latency_ms(self) -> int:
        """Calculates elapsed time in milliseconds since timing started."""
        if not self.start_time:
            return 0
        return int((time.perf_counter() - self.start_time) * 1000)

    async def log_successful_inference(self, prediction: str, uncertainty: float):
        """
        Atomically updates the inference request table with final model outputs 
        and high-resolution latency.
        """
        latency_ms = self.get_current_latency_ms()
        
        stmt = (
            update(InferenceRequest)
            .where(InferenceRequest.id == self.request_id)
            .values(
                prediction_label=prediction,
                uncertainty_score=uncertainty,
                latency_ms=latency_ms
            )
        )
        await self.db.execute(stmt)
        print(f"[Telemetry] Successfully registered request {self.request_id} metrics. Latency: {latency_ms}ms")

    async def log_pipeline_failure(self, error_message: str):
        """
        Captures pipeline failure points, logging error markers and current 
        latency state directly into the relational database.
        """
        latency_ms = self.get_current_latency_ms()
        print(f"[Telemetry CRITICAL] Pipeline failure on {self.request_id}: {error_message}", file=sys.stderr)
        
        stmt = (
            update(InferenceRequest)
            .where(InferenceRequest.id == self.request_id)
            .values(
                prediction_label=f"ERROR: {error_message[:50]}",
                uncertainty_score=1.0,
                latency_ms=latency_ms
            )
        )
        await self.db.execute(stmt)

    async def register_drift_metric(self, drift_score: float, status: str):
        """
        Directly logs active data drift outputs computed by the platform 
        into the relational public.drift_logs table.
        """
        drift_entry = DriftLog(
            request_id=self.request_id,
            drift_score=drift_score,
            status=status
        )
        self.db.add(drift_entry)
        await self.db.flush()
        print(f"[Telemetry] Drift metrics persisted for {self.request_id}. Status: {status}")