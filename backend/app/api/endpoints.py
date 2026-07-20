import json
import asyncio
import os
import mlflow
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from backend.app.core.database import get_db
from backend.app.core.schema_validator import validate_image_file
from backend.app.schema.feedback_schemas import FeedbackSubmitSchema
from backend.app.models.platform_models import InferenceRequest, FeedbackLog, Hospital, DriftLog, AlertLog
from backend.app.crud import inference_crud
from backend.app.core.orchestrator import ClinicalPipelineOrchestrator
from mlflow.tracking import MlflowClient

router = APIRouter(prefix="/v1/clinical", tags=["Clinical Ingestion & Feedback"])

# Existing endpoints
@router.post(
    "/inference/ingest",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest medical image and run end-to-end telemetry tracked pipeline"
)
async def ingest_medical_image(
    hospital_id: int = Form(..., description="Target hospital identifier"),
    metadata_json: str = Form("{}", description="Raw cellular stringified JSON metadata"),
    file: UploadFile = File(..., description="Medical image payload (.dcm, .nii, .jpg)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingesting PACS medical file, executes HIPAA cleaning, saves data drift parameters,
    and logs model telemetry results dynamically with zero mock blocks.
    """
    try:
        raw_metadata = json.loads(metadata_json)
        contents = await file.read()

        # Validate the uploaded file (offload CPU-bound validation to thread pool)
        loop = asyncio.get_running_loop()
        is_valid, error_msg = await loop.run_in_executor(
            None, validate_image_file, contents, file.filename
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # 1. Persistent storage upload to MinIO
        s3_uri = await inference_crud.upload_to_minio(contents, file.filename)

        # 2. Database transaction blueprint record allocation
        db_record = await inference_crud.create_inference_record(db, hospital_id, s3_uri)

        # 3. Handover transaction lock to production orchestrator
        orchestrator = ClinicalPipelineOrchestrator(db_session=db, request_id=db_record.id)

        pipeline_result = await orchestrator.execute_pipeline(
            image_bytes=contents,
            image_s3_uri=s3_uri,
            raw_metadata=raw_metadata
        )

        return pipeline_result

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid stringified metadata_json payload format.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline transaction failed: {str(e)}")


@router.post(
    "/feedback/submit",
    status_code=status.HTTP_200_OK,
    summary="Submit diagnostic validation feedback from physicians"
)
async def submit_physician_feedback(
    feedback_data: FeedbackSubmitSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Feedback Loop API (Task 3-2): Collects ground-truth audits from pathologists/radiologists,
    mapping clinical disagreements securely against unique image tracking records.
    """
    # 1. Ensure the underlying inference request transaction actually exists
    query = select(InferenceRequest).where(InferenceRequest.id == feedback_data.request_id)
    result = await db.execute(query)
    inference_request = result.scalar_one_or_none()

    if not inference_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference request matching UUID {feedback_data.request_id} not found."
        )

    # 2. Enforce validation constraint: corrected_label is mandatory if physician disagrees
    if not feedback_data.is_agreed and not feedback_data.corrected_label:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A 'corrected_label' must be provided when the physician disagrees with the prediction."
        )

    try:
        # 3. Instantiating the relational feedback entity mapping to logs_feedback physical table
        feedback_entry = FeedbackLog(
            request_id=feedback_data.request_id,
            is_agreed=feedback_data.is_agreed,
            corrected_label=feedback_data.corrected_label if not feedback_data.is_agreed else None
        )

        db.add(feedback_entry)
        await db.flush() # Buffer to catch unique or foreign constraints violations
        await db.commit() # Safely commit across postgres database

        return {
            "status": "Feedback Logged",
            "request_id": feedback_data.request_id,
            "saved_as_ground_truth": not feedback_data.is_agreed
        }

    except Exception as db_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback log violation: Ensure feedback for this request has not been submitted previously."
        )


# Milestone 1 Endpoints

# 1.1 Hospital Endpoints
@router.get(
    "/hospitals",
    tags=["Hospitals"],
    summary="List all hospitals"
)
async def list_hospitals(db: AsyncSession = Depends(get_db)):
    """
    Get a list of all hospitals.
    """
    query = select(Hospital)
    result = await db.execute(query)
    hospitals = result.scalars().all()
    return [
        {
            "id": hospital.id,
            "name": hospital.name,
            "location": hospital.location,
            "created_at": hospital.created_at.isoformat() if hospital.created_at else None
        }
        for hospital in hospitals
    ]


@router.get(
    "/hospitals/{hospital_id}",
    tags=["Hospitals"],
    summary="Get hospital details"
)
async def get_hospital(hospital_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get details of a specific hospital by ID.
    """
    query = select(Hospital).where(Hospital.id == hospital_id)
    result = await db.execute(query)
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return {
        "id": hospital.id,
        "name": hospital.name,
        "location": hospital.location,
        "created_at": hospital.created_at.isoformat() if hospital.created_at else None
    }


# 1.2 Model Registry Endpoints
@router.get(
    "/models",
    tags=["Model Registry"],
    summary="List all registered models"
)
async def list_models():
    """
    Get a list of all models registered in MLflow.
    """
    try:
        # Set MLflow tracking URI from environment
        tracking_uri = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://mlflow_server:5000")
        mlflow.set_tracking_uri(tracking_uri)
        client = MlflowClient()

        # Get all registered models
        models = client.list_registered_models()
        return [
            {
                "name": model.name,
                "creation_timestamp": model.creation_timestamp,
                "last_updated_timestamp": model.last_updated_timestamp,
                "description": model.description,
                "latest_versions": [
                    {
                        "version": mv.version,
                        "stage": mv.current_stage,
                        "status": mv.status,
                        "creation_timestamp": mv.creation_timestamp
                    }
                    for mv in model.latest_versions
                ]
            }
            for model in models
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch models from MLflow: {str(e)}")


@router.get(
    "/models/{name}/{version}",
    tags=["Model Registry"],
    summary="Get details of a specific model version"
)
async def get_model_version(name: str, version: str):
    """
    Get details of a specific model version from MLflow.
    """
    try:
        tracking_uri = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://mlflow_server:5000")
        mlflow.set_tracking_uri(tracking_uri)
        client = MlflowClient()

        # Get model version
        model_version = client.get_model_version(name=name, version=version)
        # Get run data for this version
        run = client.get_run(model_version.run_id)

        return {
            "name": model_version.name,
            "version": model_version.version,
            "description": model_version.description,
            "stage": model_version.current_stage,
            "status": model_version.status,
            "creation_timestamp": model_version.creation_timestamp,
            "last_updated_timestamp": model_version.last_updated_timestamp,
            "run_id": model_version.run_id,
            "metrics": run.data.metrics,
            "params": run.data.params,
            "tags": run.data.tags
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Model version not found: {str(e)}")


# 1.3 Settings Endpoint
@router.get(
    "/settings",
    tags=["Settings"],
    summary="Get full settings hierarchy"
)
async def get_settings():
    """
    Get the full hierarchy of application settings.
    Returns configuration from environment variables and defaults.
    """
    # Define settings structure - in a real app, this might come from a config file or database
    settings = {
        "app": {
            "name": os.getenv("APP_NAME", "Cross-Hospital Generalization Platform"),
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "debug": os.getenv("DEBUG", "false").lower() == "true"
        },
        "database": {
            "url": os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/dbname"),
            "echo": os.getenv("DB_ECHO", "false").lower() == "true"
        },
        "mlflow": {
            "tracking_uri": os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://mlflow_server:5000"),
            "experiment_name": os.getenv("MLFLOW_EXPERIMENT_NAME", "Clinical_Inference_Pipeline")
        },
        "minio": {
            "endpoint_url": os.getenv("MINIO_ENDPOINT_URL_LOCAL", "http://localhost:9000"),
            "access_key": os.getenv("AWS_ACCESS_KEY_ID", "minio_admin"),
            "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY", "minio_admin_password"),
            "bucket_name": os.getenv("MINIO_BUCKET_NAME", "medical-images")
        },
        "alerting": {
            "webhook_url": os.getenv("ALERT_WEBHOOK_URL", ""),
            "drift_threshold_warning": float(os.getenv("DRIFT_THRESHOLD_WARNING", "0.05")),
            "drift_threshold_critical": float(os.getenv("DRIFT_THRESHOLD_CRITICAL", "0.01"))
        },
        "feature_flags": {
            "style_adaptation_enabled": os.getenv("STYLE_ADAPTATION_ENABLED", "true").lower() == "true",
            "drift_detection_enabled": os.getenv("DRIFT_DETECTION_ENABLED", "true").lower() == "true",
            "telemetry_enabled": os.getenv("TELEMETRY_ENABLED", "true").lower() == "true"
        }
    }
    return settings


# 1.4 Alerts Endpoints
@router.get(
    "/alerts",
    tags=["Alerts"],
    summary="List all alerts"
)
async def list_alerts(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a paginated list of all alerts.
    """
    query = select(AlertLog).order_by(desc(AlertLog.sent_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    alerts = result.scalars().all()
    return [
        {
            "id": alert.id,
            "drift_log_id": alert.drift_log_id,
            "threshold_used": alert.threshold_used,
            "severity": alert.severity,
            "channel": alert.channel,
            "sent_at": alert.sent_at.isoformat() if alert.sent_at else None
        }
        for alert in alerts
    ]


@router.get(
    "/alerts/{alert_id}",
    tags=["Alerts"],
    summary="Get alert details"
)
async def get_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get details of a specific alert by ID.
    """
    query = select(AlertLog).where(AlertLog.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "id": alert.id,
        "drift_log_id": alert.drift_log_id,
        "threshold_used": alert.threshold_used,
        "severity": alert.severity,
        "channel": alert.channel,
        "sent_at": alert.sent_at.isoformat() if alert.sent_at else None
    }


@router.post(
    "/alerts/{alert_id}/ack",
    tags=["Alerts"],
    summary="Acknowledge an alert"
)
async def acknowledge_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """
    Acknowledge an alert by ID.
    In a real system, this might update an acknowledgment flag or add a note.
    For now, we'll return success since we don't have an acknowledgment field.
    """
    query = select(AlertLog).where(AlertLog.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # In a real implementation, we would update an acknowledged flag or add acknowledgment info
    # Since our model doesn't have that yet, we'll just return success
    # TODO: Add acknowledged field to AlertLog model in a future milestone
    return {
        "status": "acknowledged",
        "alert_id": alert_id,
        "message": "Alert acknowledged successfully"
    }


@router.post(
    "/alerts/{alert_id}/resolve",
    tags=["Alerts"],
    summary="Resolve an alert"
)
async def resolve_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """
    Resolve an alert by ID.
    In a real system, this might update a resolved flag or add resolution notes.
    For now, we'll return success since we don't have a resolution field.
    """
    query = select(AlertLog).where(AlertLog.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # In a real implementation, we would update a resolved flag or add resolution info
    # Since our model doesn't have that yet, we'll just return success
    # TODO: Add resolved field to AlertLog model in a future milestone
    return {
        "status": "resolved",
        "alert_id": alert_id,
        "message": "Alert resolved successfully"
    }


# 1.5 Inference Logs Endpoints
@router.get(
    "/logs",
    tags=["Inference Logs"],
    summary="Get paginated inference logs"
)
async def get_inference_logs(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    hospital_id: Optional[int] = Query(None, description="Filter by hospital ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a paginated list of inference requests (logs).
    Optionally filter by hospital ID.
    """
    query = select(InferenceRequest)
    if hospital_id is not None:
        query = query.where(InferenceRequest.hospital_id == hospital_id)
    query = query.order_by(desc(InferenceRequest.created_at)).offset(offset).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        {
            "request_id": log.id,
            "hospital_id": log.hospital_id,
            "image_s3_uri": log.image_s3_uri,
            "prediction_label": log.prediction_label,
            "uncertainty_score": log.uncertainty_score,
            "latency_ms": log.latency_ms,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]


@router.get(
    "/logs/{request_id}",
    tags=["Inference Logs"],
    summary="Get a single inference log by request ID"
)
async def get_inference_log(request_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get details of a specific inference request by its UUID.
    """
    query = select(InferenceRequest).where(InferenceRequest.id == request_id)
    result = await db.execute(query)
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Inference log not found")

    # Get associated drift log if exists
    drift_query = select(DriftLog).where(DriftLog.request_id == request_id).order_by(desc(DriftLog.checked_at)).limit(1)
    drift_result = await db.execute(drift_query)
    drift_log = drift_result.scalar_one_or_none()

    # Get feedback if exists
    feedback_query = select(FeedbackLog).where(FeedbackLog.request_id == request_id)
    feedback_result = await db.execute(feedback_query)
    feedback_log = feedback_result.scalar_one_or_none()

    response = {
        "request_id": log.id,
        "hospital_id": log.hospital_id,
        "image_s3_uri": log.image_s3_uri,
        "prediction_label": log.prediction_label,
        "uncertainty_score": log.uncertainty_score,
        "latency_ms": log.latency_ms,
        "created_at": log.created_at.isoformat() if log.created_at else None
    }

    if drift_log:
        response["drift"] = {
            "drift_score": drift_log.drift_score,
            "status": drift_log.status,
            "overall_mmd_stat": drift_log.overall_mmd_stat,
            "overall_p_value": drift_log.overall_p_value,
            "signal_breakdown": drift_log.signal_breakdown,
            "checked_at": drift_log.checked_at.isoformat() if drift_log.checked_at else None
        }

    if feedback_log:
        response["feedback"] = {
            "is_agreed": feedback_log.is_agreed,
            "corrected_label": feedback_log.corrected_label,
            "submitted_at": feedback_log.submitted_at.isoformat() if feedback_log.submitted_at else None
        }

    return response


# 1.6 Monitoring / Metrics Endpoint
@router.get(
    "/monitoring/metrics",
    tags=["Monitoring"],
    summary="Get real-time system metrics"
)
async def get_monitoring_metrics():
    """
    Get real-time system metrics (simplified version).
    In a production system, this might connect to Prometheus or collect system stats.
    """
    # For now, we'll return some basic metrics from the system and application
    import psutil
    import time

    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Get process metrics
        process = psutil.Process()
        process_memory = process.memory_info()

        return {
            "timestamp": time.time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                }
            },
            "process": {
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "num_threads": process.num_threads(),
                "cpu_percent": process.cpu_percent()
            }
        }
    except Exception as e:
        # Fallback if psutil is not available or fails
        return {
            "timestamp": time.time(),
            "system": {
                "cpu_percent": 0.0,
                "memory": {"total": 0, "available": 0, "percent": 0.0, "used": 0, "free": 0},
                "disk": {"total": 0, "used": 0, "free": 0, "percent": 0.0}
            },
            "process": {
                "memory_rss": 0,
                "memory_vms": 0,
                "num_threads": 0,
                "cpu_percent": 0.0
            },
            "error": f"Failed to collect metrics: {str(e)}"
        }


# 1.7 Drift History Endpoint
@router.get(
    "/drift/history",
    tags=["Drift"],
    summary="Get drift history with optional filters"
)
async def get_drift_history(
    hospital_id: Optional[int] = Query(None, description="Filter by hospital ID"),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical drift logs, optionally filtered by hospital ID.
    """
    # Join DriftLog with InferenceRequest to filter by hospital
    query = select(DriftLog, InferenceRequest).join(
        InferenceRequest, DriftLog.request_id == InferenceRequest.id
    )
    if hospital_id is not None:
        query = query.where(InferenceRequest.hospital_id == hospital_id)
    query = query.order_by(desc(DriftLog.checked_at)).limit(limit)

    result = await db.execute(query)
    drift_records = result.all()

    return [
        {
            "drift_log_id": drift_log.id,
            "request_id": inference_request.id,
            "hospital_id": inference_request.hospital_id,
            "drift_score": drift_log.drift_score,
            "status": drift_log.status,
            "overall_mmd_stat": drift_log.overall_mmd_stat,
            "overall_p_value": drift_log.overall_p_value,
            "signal_breakdown": drift_log.signal_breakdown,
            "checked_at": drift_log.checked_at.isoformat() if drift_log.checked_at else None,
            "image_s3_uri": inference_request.image_s3_uri,
            "prediction_label": inference_request.prediction_label
        }
        for drift_log, inference_request in drift_records
    ]


# 1.8 Recent Uploads Endpoint
@router.get(
    "/uploads/recent",
    tags=["Uploads"],
    summary="Get recent uploads"
)
async def get_recent_uploads(
    limit: int = Query(50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent inference requests (uploads), ordered by most recent first.
    """
    query = select(InferenceRequest).order_by(desc(InferenceRequest.created_at)).limit(limit)
    result = await db.execute(query)
    uploads = result.scalars().all()

    return [
        {
            "request_id": upload.id,
            "hospital_id": upload.hospital_id,
            "image_s3_uri": upload.image_s3_uri,
            "created_at": upload.created_at.isoformat() if upload.created_at else None
        }
        for upload in uploads
    ]


# 1.9 Feedback per Request Endpoint
@router.get(
    "/feedback/{request_id}",
    tags=["Feedback"],
    summary="Get feedback for a specific request"
)
async def get_feedback_for_request(request_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get all feedback entries for a specific request ID.
    """
    query = select(FeedbackLog).where(FeedbackLog.request_id == request_id)
    result = await db.execute(query)
    feedback_logs = result.scalars().all()

    return [
        {
            "feedback_id": feedback_log.id,
            "request_id": feedback_log.request_id,
            "is_agreed": feedback_log.is_agreed,
            "corrected_label": feedback_log.corrected_label,
            "submitted_at": feedback_log.submitted_at.isoformat() if feedback_log.submitted_at else None
        }
        for feedback_log in feedback_logs
    ]


# 1.10 Validation Results Endpoint
@router.get(
    "/validation/{request_id}",
    tags=["Validation"],
    summary="Get validation results for a request"
)
async def get_validation_results(request_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get validation checklist results for a specific request.
    In a real system, this would store validation results during ingestion.
    For now, we'll return a placeholder since we don't have a validation table.
    """
    # Check if the request exists
    query = select(InferenceRequest).where(InferenceRequest.id == request_id)
    result = await db.execute(query)
    inference_request = result.scalar_one_or_none()
    if not inference_request:
        raise HTTPException(status_code=404, detail="Request not found")

    # Placeholder validation results - in reality, these would be computed during ingestion
    # and stored in a validation table or in the inference request itself
    return {
        "request_id": request_id,
        "validation_checklist": {
  "file_format_valid": True,
  "dimensions_valid": True,
  "intensity_range_valid": True,
  "no_corruption_detected": True,
  "hipaa_compliant": True,
  "metadata_complete": True
}
    }


# 1.11 Adaptation Output Endpoint (optional)
@router.get(
    "/adaptation/{request_id}",
    tags=["Adaptation"],
    summary="Get adaptation output for a request"
)
async def get_adaptation_output(request_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get the adapted image URI and step details for a specific request.
    In a real system, this would store the adapted image and adaptation steps.
    For now, we'll return a placeholder since we don't store adapted images.
    """
    # Check if the request exists
    query = select(InferenceRequest).where(InferenceRequest.id == request_id)
    result = await db.execute(query)
    inference_request = result.scalar_one_or_none()
    if not inference_request:
        raise HTTPException(status_code=404, detail="Request not found")

    # Placeholder - in reality, we would have stored the adapted image during processing
    # and perhaps the adaptation parameters/steps used
    return {
        "request_id": request_id,
        "adapted_image_uri": f"s3://medical-images/adapted/{request_id}.png",  # Placeholder
        "adaptation_steps": [
            {
                "step": "histogram_matching",
                "applied": True,
                "strength": 0.5
            },
            {
                "step": "fft_band_reweighting",
                "applied": True,
                "strength": 0.3
            },
            {
                "step": "unsharp_mask_blur_calibration",
                "applied": True,
                "strength": 0.2
            }
        ],
        "note": "Adapted image storage not implemented in this milestone"
    }


# 1.12 Health Check (existing) - already in main.py