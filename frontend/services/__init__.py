"""
Service layer for the Cross-Hospital Generalization Platform.
Provides abstracted interfaces to backend services.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Data Models
@dataclass
class IngestionResult:
    request_id: str
    image_location: str
    metadata: Dict[str, Any]
    hospital_id: str
    timestamp: datetime

@dataclass
class ValidationResult:
    request_id: str
    passed: bool
    checks: List[Dict[str, Any]]
    timestamp: datetime

@dataclass
class DriftResult:
    request_id: str
    drift_score: float
    status: str  # Low, Medium, High, Critical
    metric_used: str
    metric_value: float
    p_value: float
    timestamp: datetime

@dataclass
class AdaptationResult:
    request_id: str
    adapted_image_location: str
    adaptation_steps: List[Dict[str, Any]]
    quality_metrics: Dict[str, float]
    timestamp: datetime

@dataclass
class ModelMetadata:
    model_name: str
    version: str
    task: str
    hospital: str
    framework: str
    training_date: str
    frozen: bool
    input_size: str
    output_classes: List[str]
    performance: Dict[str, float]

@dataclass
class InferenceResult:
    request_id: str
    prediction: str
    confidence: float
    uncertainty: Dict[str, float]
    timing: Dict[str, float]
    model_used: str
    adaptation_applied: bool
    drift_score: float
    timestamp: datetime

@dataclass
class FeedbackResult:
    feedback_id: str
    request_id: str
    agreed: bool
    correct_diagnosis: Optional[str]
    comments: Optional[str]
    timestamp: datetime

@dataclass
class Alert:
    alert_id: str
    timestamp: datetime
    hospital: str
    type: str
    message: str
    severity: str  # info, warning, critical, error
    acknowledged: bool
    resolved: bool

@dataclass
class HospitalInfo:
    hospital_id: str
    name: str
    status: str
    avg_drift: float
    images_processed: int
    models_used: int
    last_activity: str
    health_score: float

@dataclass
class LogEntry:
    timestamp: datetime
    request_id: str
    hospital: str
    latency_ms: int
    drift_score: float
    model_used: str
    status: str

@dataclass
class MonitoringMetrics:
    cpu_usage: float
    memory_usage: float
    gpu_usage: float
    request_rate: float
    avg_latency: float
    error_rate: float
    drift_score: float
    timestamp: datetime

# Additional Models for Hospital and Settings Services
@dataclass
class Hospital:
    hospital_id: str
    name: str
    status: str  # online, offline, unknown
    avg_drift: float
    images_processed: int
    models_used: int
    last_activity: datetime
    health_score: float

@dataclass
class SystemSettings:
    system: Dict[str, Any]
    database: Dict[str, Any]
    storage: Dict[str, Any]
    mlflow: Dict[str, Any]
    processing: Dict[str, Any]
    alerting: Dict[str, Any]
    security: Dict[str, Any]
    monitoring: Dict[str, Any]

# Service Interfaces
class IngestionService:
    """Service for ingesting medical images and metadata."""

    def upload_image(self, image_file, metadata: Dict[str, Any]) -> IngestionResult:
        """
        Upload a medical image and associated metadata.

        Args:
            image_file: The image file to upload
            metadata: Dictionary containing hospital, patient_id, etc.

        Returns:
            IngestionResult: Information about the uploaded image
        """
        raise NotImplementedError

    def get_recent_uploads(self, limit: int = 10) -> List[IngestionResult]:
        """
        Get recent image uploads.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of recent IngestionResult objects
        """
        raise NotImplementedError

class ValidationService:
    """Service for validating medical images and metadata."""

    def validate_image(self, request_id: str) -> ValidationResult:
        """
        Validate an uploaded image and its metadata.

        Args:
            request_id: ID of the request to validate

        Returns:
            ValidationResult: Validation results
        """
        raise NotImplementedError

    def get_validation_result(self, request_id: str) -> ValidationResult:
        """
        Get validation result for a request.

        Args:
            request_id: ID of the request

        Returns:
            ValidationResult: Validation results
        """
        raise NotImplementedError

class DriftService:
    """Service for detecting data drift in medical images."""

    def detect_drift(self, request_id: str) -> DriftResult:
        """
        Detect drift for an image request.

        Args:
            request_id: ID of the request to analyze

        Returns:
            DriftResult: Drift detection results
        """
        raise NotImplementedError

    def get_drift_history(self, hospital_id: str, limit: int = 100) -> List[DriftResult]:
        """
        Get drift detection history for a hospital.

        Args:
            hospital_id: ID of the hospital
            limit: Maximum number of results to return

        Returns:
            List of DriftResult objects
        """
        raise NotImplementedError

class AdaptationService:
    """Service for adapting medical image style."""

    def adapt_image(self, request_id: str, drift_info: DriftResult) -> AdaptationResult:
        """
        Adapt the style of a medical image based on drift information.

        Args:
            request_id: ID of the request to adapt
            drift_info: Drift information from DriftService

        Returns:
            AdaptationResult: Adaptation results
        """
        raise NotImplementedError

    def get_adaptation_result(self, request_id: str) -> AdaptationResult:
        """
        Get adaptation result for a request.

        Args:
            request_id: ID of the request

        Returns:
            AdaptationResult: Adaptation results
        """
        raise NotImplementedError

class RegistryService:
    """Service for managing MLflow model registry."""

    def get_registered_models(self) -> List[ModelMetadata]:
        """
        Get all registered models.

        Returns:
            List of ModelMetadata objects
        """
        raise NotImplementedError

    def get_model_by_name(self, model_name: str, version: Optional[str] = None) -> ModelMetadata:
        """
        Get a specific model by name and version.

        Args:
            model_name: Name of the model
            version: Version of the model (optional, defaults to latest)

        Returns:
            ModelMetadata: Model information
        """
        raise NotImplementedError

    def get_model_versions(self, model_name: str) -> List[ModelMetadata]:
        """
        Get all versions of a specific model.

        Args:
            model_name: Name of the model

        Returns:
            List of ModelMetadata objects
        """
        raise NotImplementedError

class InferenceService:
    """Service for running medical image inference."""

    def run_inference(self, request_id: str, model_info: ModelMetadata) -> InferenceResult:
        """
        Run inference on an adapted image.

        Args:
            request_id: ID of the request
            model_info: Information about the model to use

        Returns:
            InferenceResult: Inference results
        """
        raise NotImplementedError

    def get_inference_result(self, request_id: str) -> InferenceResult:
        """
        Get inference result for a request.

        Args:
            request_id: ID of the request

        Returns:
            InferenceResult: Inference results
        """
        raise NotImplementedError

class MonitoringService:
    """Service for monitoring system performance and metrics."""

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for the dashboard view.

        Returns:
            Dictionary containing dashboard metrics
        """
        raise NotImplementedError

    def get_comprehensive_metrics(self) -> MonitoringMetrics:
        """
        Get comprehensive system metrics.

        Returns:
            MonitoringMetrics: Current system metrics
        """
        raise NotImplementedError

    def get_system_health(self) -> Dict[str, str]:
        """
        Get system health status.

        Returns:
            Dictionary with health status of various components
        """
        raise NotImplementedError

class FeedbackService:
    """Service for collecting and managing physician feedback."""

    def submit_feedback(self, request_id: str, agreed: bool,
                       correct_diagnosis: Optional[str] = None,
                       comments: Optional[str] = None) -> FeedbackResult:
        """
        Submit physician feedback for a prediction.

        Args:
            request_id: ID of the request
            agreed: Whether the physician agreed with the prediction
            correct_diagnosis: Correct diagnosis if disagreed
            comments: Additional comments

        Returns:
            FeedbackResult: Information about the submitted feedback
        """
        raise NotImplementedError

    def get_feedback_for_request(self, request_id: str) -> List[FeedbackResult]:
        """
        Get feedback for a specific request.

        Args:
            request_id: ID of the request

        Returns:
            List of FeedbackResult objects
        """
        raise NotImplementedError

    def get_recent_feedback(self, limit: int = 50) -> List[FeedbackResult]:
        """
        Get recent feedback submissions.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of recent FeedbackResult objects
        """
        raise NotImplementedError

class AlertService:
    """Service for managing system alerts and notifications."""

    def get_active_alerts(self) -> List[Alert]:
        """
        Get currently active alerts.

        Returns:
            List of Alert objects
        """
        raise NotImplementedError

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """
        Get alert history.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of Alert objects
        """
        raise NotImplementedError

    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: ID of the acknowledge to acknowledge

        Returns:
            bool: True if successful
        """
        raise NotImplementedError

    def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an alert.

        Args:
            alert_id: ID of the alert to resolve

        Returns:
            bool: True if successful
        """
        raise NotImplementedError

class StorageService:
    """Service for managing file storage (MinIO/S3)."""

    def upload_file(self, file_data, path: str) -> str:
        """
        Upload a file to storage.

        Args:
            file_data: Data to upload
            path: Storage path

        Returns:
            str: URL or path to the uploaded file
        """
        raise NotImplementedError

    def download_file(self, path: str) -> bytes:
        """
        Download a file from storage.

        Args:
            path: Storage path

        Returns:
            bytes: File data
        """
        raise NotImplementedError

    def file_exists(self, path: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            path: Storage path

        Returns:
            bool: True if file exists
        """
        raise NotImplementedError

class HospitalService:
    """Service for managing hospital information."""

    def get_hospitals(self) -> List[HospitalInfo]:
        """
        Get all hospitals.

        Returns:
            List of HospitalInfo objects
        """
        raise NotImplementedError

    def get_hospital(self, hospital_id: str) -> Optional[HospitalInfo]:
        """
        Get a specific hospital by ID.

        Args:
            hospital_id: ID of the hospital

        Returns:
            HospitalInfo object if found, None otherwise
        """
        raise NotImplementedError

    def get_hospitals_by_status(self, status: str) -> List[HospitalInfo]:
        """
        Get hospitals by status.

        Args:
            status: Hospital status to filter by

        Returns:
            List of HospitalInfo objects with matching status
        """
        raise NotImplementedError

    def update_hospital_status(self, hospital_id: str, status: str) -> bool:
        """
        Update hospital status.

        Args:
            hospital_id: ID of the hospital to update
            status: New status value

        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

class LoggingService:
    """Service for collecting and managing system logs."""

    def get_logs(self, limit: int = 100) -> List[LogEntry]:
        """
        Get recent logs.

        Args:
            limit: Maximum number of log entries to return

        Returns:
            List of LogEntry objects
        """
        raise NotImplementedError

    def get_log_by_id(self, request_id: str) -> Optional[LogEntry]:
        """
        Get a specific log entry by request ID.

        Args:
            request_id: ID of the request to retrieve logs for

        Returns:
            LogEntry object if found, None otherwise
        """
        raise NotImplementedError

    def get_logs_by_hospital(self, hospital: str, limit: int = 100) -> List[LogEntry]:
        """
        Get logs for a specific hospital.

        Args:
            hospital: Hospital name to filter by
            limit: Maximum number of log entries to return

        Returns:
            List of LogEntry objects for the specified hospital
        """
        raise NotImplementedError

    def get_logs_by_status(self, status: str, limit: int = 100) -> List[LogEntry]:
        """
        Get logs by status.

        Args:
            status: Log status to filter by (e.g., 'completed', 'failed', 'processing')
            limit: Maximum number of log entries to return

        Returns:
            List of LogEntry objects with the specified status
        """
        raise NotImplementedError

class SettingsService:
    """Service for managing system settings and configuration."""

    def get_settings(self) -> Dict[str, Any]:
        """
        Get all system settings.

        Returns:
            Dictionary containing all system settings
        """
        raise NotImplementedError

    def get_setting(self, section: str, key: str) -> Any:
        """
        Get a specific setting value.

        Args:
            section: Settings section (e.g., 'system', 'database', 'processing')
            key: Specific setting key within the section

        Returns:
            Setting value if found, None otherwise
        """
        raise NotImplementedError

    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature: Feature name to check (e.g., 'alerting', 'gpu_acceleration')

        Returns:
            True if feature is enabled, False otherwise
        """
        raise NotImplementedError

# Factory functions for creating service instances
def create_ingestion_service() -> IngestionService:
    """Create an instance of the IngestionService."""
    from .ingestion_service import IngestionServiceImpl
    return IngestionServiceImpl()

def create_validation_service() -> ValidationService:
    """Create an instance of the ValidationService."""
    from .validation_service import ValidationServiceImpl
    return ValidationServiceImpl()

def create_drift_service() -> DriftService:
    """Create an instance of the DriftService."""
    from .drift_service import DriftServiceImpl
    return DriftServiceImpl()

def create_adaptation_service() -> AdaptationService:
    """Create an instance of the AdaptationService."""
    from .adaptation_service import AdaptationServiceImpl
    return AdaptationServiceImpl()

def create_registry_service() -> RegistryService:
    """Create an instance of the RegistryService."""
    from .registry_service import RegistryServiceImpl
    return RegistryServiceImpl()

def create_inference_service() -> InferenceService:
    """Create an instance of the InferenceService."""
    from .inference_service import InferenceServiceImpl
    return InferenceServiceImpl()

def create_monitoring_service() -> MonitoringService:
    """Create an instance of the MonitoringService."""
    from .monitoring_service import MonitoringServiceImpl
    return MonitoringServiceImpl()

def create_feedback_service() -> FeedbackService:
    """Create an instance of the FeedbackService."""
    from .feedback_service import FeedbackServiceImpl
    return FeedbackServiceImpl()

def create_alert_service() -> AlertService:
    """Create an instance of the AlertService."""
    from .alert_service import AlertServiceImpl
    return AlertServiceImpl()

def create_storage_service() -> StorageService:
    """Create an instance of the StorageService."""
    from .storage_service import StorageServiceImpl
    return StorageServiceImpl()

def create_hospital_service() -> HospitalService:
    """Create an instance of the HospitalService."""
    from .hospital_service import HospitalServiceImpl
    return HospitalServiceImpl()

def create_logging_service() -> LoggingService:
    """Create an instance of the LoggingService."""
    from .logging_service import LoggingServiceImpl
    return LoggingServiceImpl()

def create_settings_service() -> SettingsService:
    """Create an instance of the SettingsService."""
    from .settings_service import SettingsServiceImpl
    return SettingsServiceImpl()