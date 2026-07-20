"""
Data models for the Cross-Hospital Generalization Platform frontend.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class SeverityLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class Status(str, Enum):
    """Status values."""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

class ValidationStatus(str, Enum):
    """Validation status values."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"

@dataclass
class Alert:
    """Alert model."""
    alert_id: str
    timestamp: datetime
    hospital: str
    type: str
    message: str
    severity: SeverityLevel
    acknowledged: bool = False
    resolved: bool = False

@dataclass
class FeedbackResult:
    """Feedback result model."""
    feedback_id: str
    request_id: str
    hospital: str
    prediction: str
    confidence: float
    agreed: bool
    correct_diagnosis: Optional[str] = None
    comments: Optional[str] = None
    physician_name: Optional[str] = None
    physician_id: Optional[str] = None
    ground_truth_available: bool = False
    ground_truth: Optional[str] = None
    timestamp: datetime = None

@dataclass
class MonitoringMetrics:
    """System monitoring metrics."""
    cpu_usage: float
    memory_usage: float
    gpu_usage: float
    request_rate: float
    avg_latency: float
    error_rate: float
    drift_score: float
    timestamp: datetime

@dataclass
class SystemHealth:
    """System health status."""
    overall: str
    components: Dict[str, str]

@dataclass
class HospitalInfo:
    """Hospital information."""
    name: str
    status: Status
    avg_drift: float
    images_processed: int
    models_used: int
    last_activity: datetime
    health_score: float

@dataclass
class ModelInfo:
    """Model registry information."""
    model_id: str
    name: str
    version: str
    task: str
    hospital: str
    framework: str
    training_date: datetime
    is_frozen: bool
    performance_metrics: Dict[str, float]
    description: str

@dataclass
class RequestLog:
    """Request log entry."""
    timestamp: datetime
    request_id: str
    hospital: str
    prediction: str
    confidence: float
    latency: float
    drift_score: float
    model_used: str
    status: str
    validation_passed: bool
    metadata: Dict[str, Any]