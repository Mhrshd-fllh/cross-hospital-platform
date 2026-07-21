"""
Real implementation of the LoggingService that communicates with the backend API.
"""

from datetime import datetime
from typing import List, Optional
from . import LoggingService, LogEntry
from utils.api.client import get_api_client
import streamlit as st


class LoggingServiceImpl(LoggingService):
    """Real implementation of LoggingService that calls backend API."""

    def __init__(self):
        self.api_client = get_api_client()
        # Set auth token from session state if available
        token = st.session_state.get("access_token")
        if token:
            self.api_client.set_auth_token(token)

    def _ensure_auth_token(self):
        """Ensure the API client has the current auth token from session state."""
        token = st.session_state.get("access_token")
        if token:
            self.api_client.set_auth_token(token)

    def get_logs(self, limit: int = 100) -> List[LogEntry]:
        """
        Get recent logs from the backend API.

        Args:
            limit: Maximum number of log entries to return

        Returns:
            List of LogEntry objects
        """
        self._ensure_auth_token()
        try:
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/logs",
                params={"limit": limit}
            )
            response.raise_for_status()
            logs_data = response.json()

            logs = []
            for log_data in logs_data:
                # Convert API response to LogEntry
                log_entry = self._map_to_log_entry(log_data)
                logs.append(log_entry)

            return logs
        except Exception as e:
            # Fallback to mock data in case of error for development
            st.warning(f"Failed to fetch logs from API: {str(e)}. Using mock data.")
            return self._get_mock_logs(limit)

    def get_log_by_id(self, request_id: str) -> Optional[LogEntry]:
        """
        Get a specific log entry by request ID from the backend API.

        Args:
            request_id: ID of the request to retrieve logs for

        Returns:
            LogEntry object if found, None otherwise
        """
        self._ensure_auth_token()
        try:
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/logs/{request_id}"
            )
            response.raise_for_status()
            log_data = response.json()

            return self._map_to_log_entry(log_data)
        except Exception as e:
            # Fallback to mock data in case of error for development
            st.warning(f"Failed to fetch log {request_id} from API: {str(e)}. Using mock data.")
            return self._get_mock_log_by_id(request_id)

    def get_logs_by_hospital(self, hospital: str, limit: int = 100) -> List[LogEntry]:
        """
        Get logs for a specific hospital.

        Args:
            hospital: Hospital name to filter by
            limit: Maximum number of log entries to return

        Returns:
            List of LogEntry objects for the specified hospital
        """
        # First get the hospital ID from the hospital name
        hospital_id = self._get_hospital_id_by_name(hospital)
        if hospital_id is None:
            return []

        self._ensure_auth_token()
        try:
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/logs",
                params={"hospital_id": hospital_id, "limit": limit}
            )
            response.raise_for_status()
            logs_data = response.json()

            logs = []
            for log_data in logs_data:
                log_entry = self._map_to_log_entry(log_data)
                logs.append(log_entry)

            return logs
        except Exception as e:
            # Fallback to mock data in case of error for development
            st.warning(f"Failed to fetch logs for hospital {hospital} from API: {str(e)}. Using mock data.")
            return self._get_mock_logs(limit)

    def get_logs_by_status(self, status: str, limit: int = 100) -> List[LogEntry]:
        """
        Get logs by status.

        Args:
            status: Log status to filter by (e.g., 'completed', 'failed', 'processing')
            limit: Maximum number of log entries to return

        Returns:
            List of LogEntry objects with the specified status
        """
        # Since the API doesn't directly support filtering by status,
        # we get logs and filter locally
        all_logs = self.get_logs(limit=1000)  # Get more to filter from
        filtered_logs = [log for log in all_logs if log.status.lower() == status.lower()]
        return filtered_logs[:limit]

    def _map_to_log_entry(self, log_data: dict) -> LogEntry:
        """
        Convert API response to LogEntry dataclass.

        Args:
            log_data: Dictionary containing log data from API

        Returns:
            LogEntry object
        """
        # Extract basic information
        request_id = str(log_data.get("id", ""))
        hospital_id = log_data.get("hospital_id")
        prediction = log_data.get("prediction_label")
        latency_ms = log_data.get("latency_ms")
        created_at_str = log_data.get("created_at")

        # Convert timestamp
        try:
            if created_at_str:
                timestamp = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            else:
                timestamp = datetime.now()
        except:
            timestamp = datetime.now()

        # Get hospital name from ID (we'd need to make another call or cache)
        hospital = f"Hospital {hospital_id}" if hospital_id else "Unknown"

        # Try to get drift information - this would require additional API calls
        # For now, we'll use a default or try to get from drift endpoint if feasible
        drift_score = 0.0  # Default

        # Model used - not directly available in logs endpoint
        model_used = "Unknown"

        # Status - determine from available data
        status = "completed" if prediction is not None else "pending"

        # Create basic metadata (limited since we don't have all fields from API)
        metadata = {
            "patient_id": "Unknown",
            "study_date": "Unknown",
            "modality": "Unknown",
            "body_part": "Unknown",
            "image_size": "Unknown",
            "image_format": "Unknown"
        }

        # Create simplified processing stages
        processing_stages = [
            {"name": "Upload", "status": "completed", "duration_ms": 50},
            {"name": "Validation", "status": "completed", "duration_ms": 100},
            {"name": "Drift Detection", "status": "completed", "duration_ms": 200},
            {"name": "Style Adaptation", "status": "skipped" if drift_score < 0.1 else "completed", "duration_ms": 0 if drift_score < 0.1 else 500},
            {"name": "Model Retrieval", "status": "completed", "duration_ms": 50},
            {"name": "Inference", "status": "completed" if prediction else "pending", "duration_ms": 400 if prediction else 0},
            {"name": "Logging", "status": "completed", "duration_ms": 20}
        ]

        # No errors in basic log view
        errors = []

        return LogEntry(
            timestamp=timestamp,
            request_id=request_id,
            hospital=hospital,
            prediction=prediction or "Unknown",
            confidence=0.85,  # Default confidence since not in API
            latency_ms=latency_ms or 0,
            drift_score=drift_score,
            model_used=model_used,
            status=status,
            metadata=metadata,
            processing_stages=processing_stages,
            errors=errors
        )

    def _get_hospital_id_by_name(self, hospital_name: str) -> Optional[int]:
        """
        Get hospital ID by name by fetching all hospitals and matching.

        Args:
            hospital_name: Name of the hospital

        Returns:
            Hospital ID if found, None otherwise
        """
        try:
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/hospitals"
            )
            response.raise_for_status()
            hospitals_data = response.json()

            for hospital_data in hospitals_data:
                if hospital_data.get("name", "").lower() == hospital_name.lower():
                    return hospital_data.get("id")
            return None
        except:
            return None

    # Helper methods for development/fallback
    def _get_mock_logs(self, limit: int) -> List[LogEntry]:
        """Return mock logs for development when API is unavailable."""
        from datetime import datetime, timedelta
        import random

        logs = []
        hospitals = ["General Hospital", "City Medical Center", "University Hospital", "Children's Hospital", "County Hospital"]
        models = ["CheXpert-Pneumonia-DenseNet121", "MIMIC-Cardiomegaly-ResNet50", "NIH-Nodule-EfficientNetB0"]
        predictions = ["Normal", "Pneumonia", "Cardiomegaly", "Edema", "Fracture", "Nodule"]
        statuses = ["completed", "processing", "failed", "pending"]

        # Generate 50-100 log entries for the last 24 hours
        num_entries = min(limit, random.randint(50, 100))

        for i in range(num_entries):
            # Random timestamp in the last 24 hours
            hours_ago = random.uniform(0, 24)
            timestamp = datetime.now() - timedelta(hours=hours_ago)

            # Determine status based on time (more recent = more likely to be processing)
            if hours_ago < 0.5:  # Last 30 minutes
                status = random.choices(["processing", "pending", "completed"], weights=[0.3, 0.2, 0.5])[0]
            elif hours_ago < 2:  # Last 2 hours
                status = random.choices(["processing", "completed", "completed"], weights=[0.95])
            else:completed", "completed", "failed"], weights=[0.1, 0.8, 0.1])[0]
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

        return logs[:limit]

    def _get_mock_log_by_id(self, request_id: str) -> Optional[LogEntry]:
        """Return a specific mock log entry for development when API is unavailable."""
        mock_logs = self._get_mock_logs(100)  # Get a good sample
        for log in mock_logs:
            if log.request_id == request_id:
                return log
        return None