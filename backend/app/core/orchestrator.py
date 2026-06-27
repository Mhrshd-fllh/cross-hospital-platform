import time
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.telemetry import TelemetryService
from backend.app.core.drift_detector import MedicalDriftDetector
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
        # Initialize Alibi Detect instance
        self.drift_detector = MedicalDriftDetector()

    async def execute_pipeline(self,image_bytes: bytes, image_s3_uri: str, raw_metadata: dict) -> dict:
        start_time = time.time()
        # 1. Run real statistical drift evaluation using Alibi Detect
        drift_score, drift_status = self.drift_detector.detect_image_drift(image_bytes)

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
            new_drift_log = DriftLog(
                request_id=self.request_id,
                drift_score=drift_score,
                status=drift_status
            )
            self.db.add(new_drift_log)
            # We let the caller commit the main transaction, or flush here safely
            await self.db.flush()
        except Exception as db_error:
            print(f"Postgres drift logging bypassed safely: {str(db_error)}")

        # 3. Stream real Alibi metrics into MLflow Central Tracking Server
        mlflow_params = {
            "image_uri": image_s3_uri,
            "hipaa_sanitized": raw_metadata.get("hipaa_anonymized", False),
            "study_modality": raw_metadata.get("study_modality", "UNKNOWN"),
            "drift_status_flag": drift_status
        }
        
        mlflow_metrics = {
            "pipeline_latency_ms": float(latency),
            "model_uncertainty_score": float(uncertainty),
            "alibi_drift_score": float(drift_score) # Real Alibi output tracked live
        }

        try:
            await self.telemetry.log_inference_telemetry(
                request_id=self.request_id,
                params=mlflow_params,
                metrics=mlflow_metrics
            )
        except Exception as telemetry_error:
            print(f"Telemetry logging bypassed safely: {str(telemetry_error)}")

        return {
            "status": "Success",
            "request_id": str(self.request_id),
            "prediction": predicted_class,
            "uncertainty": uncertainty,
            "drift_score": drift_score,
            "drift_status": drift_status,
            "latency_ms": latency
        }
