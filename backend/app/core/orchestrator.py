import time
import os
import numpy as np
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.telemetry import TelemetryService
from backend.app.core.drift_detector import MedicalDriftDetector
from backend.app.core.alerting import AlertingService
from backend.app.models.platform_models import InferenceRequest, DriftLog

class ClinicalPipelineOrchestrator:
    """
    Production orchestrator coordinating image preprocessing, deep learning execution,
    database persistence state updates, and telemetry auditing streams.
    """

    def __init__(self, db_session: AsyncSession, request_id: any):
        self.db = db_session
        self.request_id = request_id
        # Initialize the telemetry tracker locally from core pack
        self.telemetry = TelemetryService()
        # Initialize drift detector
        self.drift_detector = MedicalDriftDetector()
        # Initialize alerting service
        self.alerting = AlertingService()

    async def execute_pipeline(self, image_bytes: bytes, image_s3_uri: str, raw_metadata: dict) -> dict:
        start_time = time.time()
        # 1. Run statistical drift evaluation using the refactored detector (offload CPU-intensive detection to thread pool)
        loop = asyncio.get_running_loop()
        drift_result = await loop.run_in_executor(
            None, self.drift_detector.detect_image_drift, image_bytes
        )

        # Extract results
        mmd_stat = drift_result.get('mmd_stat', float('nan'))
        mmd_pvalue = drift_result.get('mmd_pvalue', float('nan'))
        signal_pvals = drift_result.get('signal_pvals', {
            'histogram': float('nan'),
            'fft': float('nan'),
            'lbp': float('nan'),
            'sharpness': float('nan')
        })
        status = drift_result.get('status', 'Error')

        # -------------------------------------------------------------------------
        # [CORE ML RETRIEVAL BLOCK]
        # Simulated prediction outputs that will eventually link to the weights frozen
        # in your scripts/freeze_and_register.py execution script.
        predicted_class = "Malignant"
        uncertainty = 0.142
        # -------------------------------------------------------------------------

        # Calculate real engine latency down to milliseconds
        latency = int((time.time() - start_time) * 1000)

        # 1. Prepare tracking payload and configurations for MLflow
        mlflow_params = {
            "image_uri": image_s3_uri,
            "hipaa_sanitized": raw_metadata.get("hipaa_anonymized", False),
            "study_modality": raw_metadata.get("study_modality", "UNKNOWN")
        }

        # 2. Persist Drift Metrics directly into PostgreSQL drift_logs table
        try:
            # Compute drift_score for backward compatibility (1 - pvalue, clamped)
            # If pvalue is NaN, set drift_score to 0.0
            if np.isnan(mmd_pvalue):
                drift_score = 0.0
            else:
                drift_score = max(0.0, min(1.0, 1.0 - mmd_pvalue))

            new_drift_log = DriftLog(
                request_id=self.request_id,
                drift_score=drift_score,
                status=status,
                overall_mmd_stat=mmd_stat,
                overall_p_value=mmd_pvalue,
                signal_breakdown=signal_pvals
            )
            self.db.add(new_drift_log)
            # Flush to get the ID for alerting
            await self.db.flush()
            drift_log_id = new_drift_log.id
        except Exception as db_error:
            print(f"Postgres drift logging failed: {str(db_error)}")
            # If we cannot persist, we cannot alert reliably; skip alerting
            drift_log_id = None

        # 3. Check for alert condition and send alert if needed
        if drift_log_id is not None and not np.isnan(mmd_pvalue):
            try:
                await self.alerting.send_alert(
                    drift_log_id=drift_log_id,
                    p_value=mmd_pvalue,
                    session=self.db
                )
            except Exception as alert_error:
                print(f"Alerting failed: {str(alert_error)}")

        # 4. Stream real metrics into MLflow Central Tracking Server
        mlflow_params = {
            "image_uri": image_s3_uri,
            "hipaa_sanitized": raw_metadata.get("hipaa_anonymized", False),
            "study_modality": raw_metadata.get("study_modality", "UNKNOWN"),
            "drift_status_flag": status
        }

        mlflow_metrics = {
            "pipeline_latency_ms": float(latency),
            "model_uncertainty_score": float(uncertainty),
            "mmd_stat": float(mmd_stat) if not np.isnan(mmd_stat) else 0.0,
            "mmd_pvalue": float(mmd_pvalue) if not np.isnan(mmd_pvalue) else 0.0,
            "histogram_pvalue": float(signal_pvals.get('histogram', 0.0)) if not np.isnan(signal_pvals.get('histogram', 0.0)) else 0.0,
            "fft_pvalue": float(signal_pvals.get('fft', 0.0)) if not np.isnan(signal_pvals.get('fft', 0.0)) else 0.0,
            "lbp_pvalue": float(signal_pvals.get('lbp', 0.0)) if not np.isnan(signal_pvals.get('lbp', 0.0)) else 0.0,
            "sharpness_pvalue": float(signal_pvals.get('sharpness', 0.0)) if not np.isnan(signal_pvals.get('sharpness', 0.0)) else 0.0,
            "alibi_drift_score": float(1.0 - mmd_pvalue) if not np.isnan(mmd_pvalue) else 0.0  # backward compatible metric
        }

        try:
            await self.telemetry.log_inference_telemetry(
                request_id=self.request_id,
                params=mlflow_params,
                metrics=mlflow_metrics
            )
        except Exception as telemetry_error:
            print(f"Telemetry logging failed: {str(telemetry_error)}")

        return {
            "status": "Success",
            "request_id": str(self.request_id),
            "prediction": predicted_class,
            "uncertainty": uncertainty,
            "drift_score": drift_score,  # backward compatibility
            "drift_status": status,
            "latency_ms": latency,
            # Additional fields for frontend consumption
            "mmd_stat": mmd_stat,
            "mmd_pvalue": mmd_pvalue,
            "signal_pvals": signal_pvals
        }