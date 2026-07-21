import time
import os
import numpy as np
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.telemetry import TelemetryService
from backend.app.core.drift_detector import MedicalDriftDetector
from backend.app.core.alerting import AlertingService
from backend.app.core.style_adaptation import StyleAdapter
from backend.app.models.platform_models import InferenceRequest, DriftLog
from backend.app.core.model_service import ModelService

logger = logging.getLogger(__name__)

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
        # Initialize style adapter
        self.style_adapter = StyleAdapter()
        # Initialize model service (singleton)
        self.model_service = ModelService()

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

        # 2. Apply style adaptation (after drift detection, before inference)
        try:
            adapted_image_bytes = self.style_adapter.adapt_image(
                image_bytes, metadata={**raw_metadata, "drift_result": drift_result}
            )
        except Exception as adapt_error:
            logger.warning(f"Style adaptation failed: {adapt_error}. Using original image.")
            adapted_image_bytes = image_bytes

        # -------------------------------------------------------------------------
        # [CORE ML RETRIEVAL BLOCK] - Real model inference
        # -------------------------------------------------------------------------
        try:
            # Preprocess image for the model (expects 224x224 RGB, ImageNet normalized)
            model_input = self._preprocess_for_model(adapted_image_bytes)
            # Run inference
            model_output = self.model_service.predict(model_input)  # shape (1, num_classes)
            # Assuming model_output are probabilities (softmax already applied)
            probs = model_output[0]  # shape (num_classes,)
            predicted_class_idx = int(np.argmax(probs))
            # Map index to label - we could load label mapping from model metadata or env;
            # for now use generic class indices as strings.
            predicted_label = str(predicted_class_idx)
            # Uncertainty: predictive entropy
            epsilon = 1e-10
            log_probs = np.log(probs + epsilon)
            entropy = -np.sum(probs * log_probs)
            uncertainty = float(entropy)
            logger.info(f"Model inference completed. Predicted class: {predicted_label}, uncertainty: {uncertainty:.4f}")
        except Exception as model_error:
            logger.exception("Model inference failed")
            # Fallback to safe defaults
            predicted_label = "Unknown"
            uncertainty = 0.0

        # Calculate real engine latency down to milliseconds
        latency = int((time.time() - start_time) * 1000)

        # 2. Persist Drift Metrics directly into PostgreSQL drift_logs table
        try:
            # Compute drift_score for backward compatibility (1 - pvalue, clamped)
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
            logger.exception("Postgres drift logging failed")
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
                logger.exception("Alerting failed")

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
            logger.exception("Telemetry logging failed")

        return {
            "status": "Success",
            "request_id": str(self.request_id),
            "prediction": predicted_label,
            "uncertainty": uncertainty,
            "drift_score": drift_score,  # backward compatibility
            "drift_status": status,
            "latency_ms": latency,
            # Additional fields for frontend consumption
            "mmd_stat": mmd_stat,
            "mmd_pvalue": mmd_pvalue,
            "signal_pvals": signal_pvals
        }

    def _preprocess_for_model(self, image_bytes: bytes) -> np.ndarray:
        """
        Preprocess raw image bytes to match model input expectations:
        - Convert to RGB (stack grayscale 3 times)
        - Resize to 224x224
        - Convert to float32 and scale to [0,1]
        - Apply ImageNet normalization
        - Return shape (1, 3, 224, 224) as float32 (channel-first)
        """
        from PIL import Image
        import io

        try:
            img = Image.open(io.BytesIO(image_bytes)).convert('L')  # ensure grayscale
        except Exception as e:
            raise ValueError(f"Unable to decode image for model preprocessing: {e}")

        # Stack to 3 channels (RGB-like)
        img = Image.merge("RGB", (img, img, img))
        # Resize to model expected size
        img = img.resize((224, 224), Image.Resampling.BILINEAR)
        img_array = np.array(img, dtype=np.float32) / 255.0  # (H, W, C)

        # ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_array = (img_array - mean) / std

        # Transpose to channel-first and add batch dimension
        img_array = np.transpose(img_array, (2, 0, 1))  # (C, H, W)
        img_array = np.expand_dims(img_array, axis=0)    # (1, C, H, W)
        return img_array