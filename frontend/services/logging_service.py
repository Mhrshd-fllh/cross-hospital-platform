"""
Mock implementation of the LoggingService for development and testing.
Returns simulated data for frontend development.
"""

import random
from datetime import datetime, timedelta
from typing import List, Optional
from . import LoggingService, LogEntry

class MockLoggingService(LoggingService):
    """Mock implementation of LoggingService."""

    def __init__(self):
        self._logs: List[LogEntry] = self._generate_mock_logs()

    def _generate_mock_logs(self) -> List[LogEntry]:
        """Generate mock log data."""
        logs = []
        hospitals = ["General Hospital", "City Medical Center", "University Hospital", "Children's Hospital", "County Hospital"]
        models = ["CheXpert-Pneumonia-DenseNet121", "MIMIC-Cardiomegaly-ResNet50", "NIH-Nodule-EfficientNetB0"]
        predictions = ["Normal", "Pneumonia", "Cardiomegaly", "Edema", "Fracture", "Nodule"]
        statuses = ["completed", "processing", "failed", "pending"]

        # Generate 50-100 log entries for the last 24 hours
        num_entries = random.randint(50, 100)

        for i in range(num_entries):
            # Random timestamp in the last 24 hours
            hours_ago = random.uniform(0, 24)
            timestamp = datetime.now() - timedelta(hours=hours_ago)

            # Determine status based on time (more recent = more likely to be processing)
            if hours_ago < 0.5:  # Last 30 minutes
                status = random.choices(["processing", "pending", "completed"], weights=[0.3, 0.2, 0.5])[0]
            elif hours_ago < 2:  # Last 2 hours
                status = random.choices(["processing", "completed", "failed"], weights=[0.1, 0.8, 0.1])[0]
            else:  # Older than 2 hours
                status = random.choices(["completed", "failed"], weights=[0.95, 0.05])[0]

            # Generate processing stages
            stages = []
            base_time = 0
            stage_names = ["Upload", "Validation", "Drift Detection", "Style Adaptation", "Model Retrieval", "Inference", "Logging"]

            for j, stage_name in enumerate(stage_names):
                # Determine if stage was completed based on overall status
                if status == "failed" and j >= 5:  # Fail during inference or later
                    stage_status = "failed"
                elif status in ["processing", "pending"] and j >= 4:  # Still processing
                    stage_status = "processing" if status == "processing" else "pending"
                else:
                    stage_status = "completed"

                # Random duration for each stage (more realistic times)
                if stage_name == "Upload":
                    duration_ms = random.randint(50, 200)
                elif stage_name == "Validation":
                    duration_ms = random.randint(100, 300)
                elif stage_name == "Drift Detection":
                    duration_ms = random.randint(200, 500)
                elif stage_name == "Style Adaptation":
                    # Skip if drift check failed or not needed
                    if status == "failed" and j >= 3:
                        duration_ms = 0
                        stage_status = "skipped"
                    elif status in ["processing", "pending"] and j >= 3:
                        duration_ms = 0
                        stage_status = "pending"
                    else:
                        duration_ms = random.randint(300, 1000)
                elif stage_name == "Model Retrieval":
                    duration_ms = random.randint(50, 150)
                elif stage_name == "Inference":
                    if status == "failed":
                        duration_ms = 0
                        stage_status = "failed"
                    elif status in ["processing", "pending"]:
                        duration_ms = 0
                        stage_status = "pending"
                    else:
                        duration_ms = random.randint(400, 1200)
                else:  # Logging
                    duration_ms = random.randint(20, 100)

                stages.append({
                    "name": stage_name,
                    "status": stage_status,
                    "duration_ms": duration_ms
                })
                base_time += duration_ms

            # Generate metadata
            patient_id = f"MRN{random.randint(100000, 999999)}"
            study_date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
            modality = random.choice(["DX", "CT", "MR", "US"])
            body_part = random.choice(["CHEST", "LUNGS", "HEART"])
            image_size = f"{random.choice([256, 512, 1024])}x{random.choice([256, 512, 1024])}"
            image_format = random.choice(["DICOM", "JPEG", "PNG"])

            # Generate errors if failed
            errors = []
            if status == "failed":
                error_scenarios = [
                    {"stage": "Inference", "error": "Model inference timeout", "code": "INFER_TIMEOUT"},
                    {"stage": "Inference", "error": "GPU memory allocation failed", "code": "GPU_OOM"},
                    {"stage": "Drift Detection", "error": "Reference dataset unavailable", "code": "DATA_UNAVAILABLE"},
                    {"stage": "Validation", "error": "Invalid DICOM format", "code": "INVALID_FORMAT"}
                ]
                num_errors = random.randint(1, 2)
                errors = random.sample(error_scenarios, min(num_errors, len(error_scenarios)))

            log_entry = LogEntry(
                timestamp=timestamp,
                request_id=f"REQ-{timestamp.strftime('%Y%m%d')}-{str(100000 + i).zfill(6)}",
                hospital=random.choice(hospitals),
                prediction=random.choice(predictions) if status == "completed" else None,
                confidence=random.uniform(0.7, 0.95) if status == "completed" else None,
                latency_ms=random.randint(100, 800) if status == "completed" else None,
                drift_score=random.uniform(0.1, 0.5) if status == "completed" else None,
                model_used=random.choice(models) if status == "completed" else None,
                status=status,
                metadata={
                    "patient_id": patient_id,
                    "study_date": study_date,
                    "modality": modality,
                    "body_part": body_part,
                    "image_size": image_size,
                    "image_format": image_format
                },
                processing_stages=stages,
                errors=errors
            )

            logs.append(log_entry)

        # Sort by timestamp descending (newest first)
        logs.sort(key=lambda x: x.timestamp, reverse=True)

        return logs

    def get_logs(self, limit: int = 100) -> List[LogEntry]:
        """Get recent logs."""
        return self._logs[:limit]

    def get_log_by_id(self, request_id: str) -> Optional[LogEntry]:
        """Get a specific log entry by request ID."""
        for log in self._logs:
            if log.request_id == request_id:
                return log
        return None

    def get_logs_by_hospital(self, hospital: str, limit: int = 100) -> List[LogEntry]:
        """Get logs for a specific hospital."""
        filtered_logs = [log for log in self._logs if log.hospital == hospital]
        return filtered_logs[:limit]

    def get_logs_by_status(self, status: str, limit: int = 100) -> List[LogEntry]:
        """Get logs by status."""
        filtered_logs = [log for log in self._logs if log.status == status.lower()]
        return filtered_logs[:limit]

# Factory function
def create_logging_service() -> LoggingService:
    """Create an instance of the mock LoggingService."""
    return MockLoggingService()