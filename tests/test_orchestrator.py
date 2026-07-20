import asyncio
import numpy as np
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.core.orchestrator import ClinicalPipelineOrchestrator
from backend.app.models.platform_models import InferenceRequest, DriftLog

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session

@pytest.fixture
def orchestrator(mock_db_session):
    # Create orchestrator with a fake request_id
    return ClinicalPipelineOrchestrator(db_session=mock_db_session, request_id="test-request-id")

@pytest.mark.asyncio
async def test_execute_pipeline_success(orchestrator, mock_db_session):
    # Mock drift detector
    with patch.object(orchestrator.drift_detector, 'detect_image_drift') as mock_drift, \
         patch.object(orchestrator.style_adapter, 'adapt_image') as mock_adapt, \
         patch.object(orchestrator.model_service, 'predict') as mock_predict, \
         patch.object(orchestrator.telemetry, 'log_inference_telemetry') as mock_telemetry, \
         patch.object(orchestrator.alerting, 'send_alert') as mock_alert:

        # Configure mocks
        mock_drift.return_value = {
            'mmd_stat': 0.05,
            'mmd_pvalue': 0.2,
            'signal_pvals': {'histogram': 0.8, 'fft': 0.9, 'lbp': 0.85, 'sharpness': 0.95},
            'status': 'Normal'
        }
        # Return unchanged bytes (adapt_image returns same bytes)
        mock_adapt.side_effect = lambda x, metadata=None: x
        # Model predicts class 1 with high probability
        mock_predict.return_value = np.array([[0.1, 0.8, 0.1]])  # 3 classes
        # DB flush returns None but we need to set id on the added DriftLog object
        async def mock_add_and_flush(obj):
            # Simulate assigning an ID
            obj.id = 1
        mock_db_session.add.side_effect = mock_add_and_flush
        mock_db_session.flush = AsyncMock()

        # Inputs
        image_bytes = b"fake image bytes"
        image_s3_uri = "s3://bucket/image.png"
        raw_metadata = {"hipaa_anonymized": True, "study_modality": "XRAY"}

        result = await orchestrator.execute_pipeline(
            image_bytes=image_bytes,
            image_s3_uri=image_s3_uri,
            raw_metadata=raw_metadata
        )

        # Assertions
        assert result["status"] == "Success"
        assert result["request_id"] == "test-request-id"
        # prediction label should be "1" (index of max probability)
        assert result["prediction"] == "1"
        # uncertainty should be entropy of [0.1,0.8,0.1]
        expected_entropy = -np.sum([0.1*np.log(0.1+1e-10), 0.8*np.log(0.8+1e-10), 0.1*np.log(0.1+1e-10)])
        assert abs(result["uncertainty"] - expected_entropy) < 1e-6
        # drift_score = 1 - pvalue = 0.8
        assert abs(result["drift_score"] - 0.8) < 1e-6
        assert result["drift_status"] == "Normal"
        assert result["latency_ms"] >= 0

        # Ensure mocks were called
        mock_drift.assert_called_once_with(image_bytes)
        mock_adapt.assert_called_once()
        mock_predict.assert_called_once()
        mock_db_session.add.assert_called()
        mock_db_session.flush.assert_awaited()
        mock_telemetry.assert_awaited_once()
        # Alert should not be called because pvalue > 0.05 (normal)
        mock_alert.assert_not_called()

@pytest.mark.asyncio
async def test_execute_pipeline_alert_triggered(orchestrator, mock_db_session):
    with patch.object(orchestrator.drift_detector, 'detect_image_drift') as mock_drift, \
         patch.object(orchestrator.style_adapter, 'adapt_image') as mock_adapt, \
         patch.object(orchestrator.model_service, 'predict') as mock_predict, \
         patch.object(orchestrator.telemetry, 'log_inference_telemetry') as mock_telemetry, \
         patch.object(orchestrator.alerting, 'send_alert') as mock_alert:

        # Drift detection indicates critical (pvalue low)
        mock_drift.return_value = {
            'mmd_stat': 0.5,
            'mmd_pvalue': 0.001,  # <0.01 -> critical
            'signal_pvals': {'histogram': 0.01, 'fft': 0.02, 'lbp': 0.01, 'sharpness': 0.01},
            'status': 'Critical'
        }
        mock_adapt.side_effect = lambda x, metadata=None: x
        mock_predict.return_value = np.array([[0.2, 0.7, 0.1]])
        async def mock_add_and_flush(obj):
            obj.id = 2
        mock_db_session.add.side_effect = mock_add_and_flush
        mock_db_session.flush = AsyncMock()

        image_bytes = b"fake"
        image_s3_uri = "s3://bucket/image.png"
        raw_metadata = {}

        result = await orchestrator.execute_pipeline(image_bytes, image_s3_uri, raw_metadata)

        assert result["drift_status"] == "Critical"
        # Alert should be called because pvalue < 0.05
        mock_alert.assert_awaited_once()
        # Check that the drift_log_id passed is the ID we set (2)
        args, kwargs = mock_alert.call_args
        assert kwargs.get("drift_log_id") == 2 or args[0] == 2