"""
Real implementation of the RegistryService that communicates with the backend API.
"""

from datetime import datetime
from typing import List, Optional
from . import RegistryService, ModelMetadata
from utils.api.client import get_api_client
import streamlit as st


class RegistryServiceImpl(RegistryService):
    """Real implementation of RegistryService that calls backend API."""

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

    def get_registered_models(self) -> List[ModelMetadata]:
        """
        Get all registered models from the backend API.

        Returns:
            List of ModelMetadata objects
        """
        self._ensure_auth_token()
        try:
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/models"
            )
            response.raise_for_status()
            models_data = response.json()

            models = []
            for model_data in models_data:
                # For simplicity, we'll take the first version of each model
                # In a more complete implementation, we might want to handle multiple versions
                latest_versions = model_data.get("latest_versions", [])
                if latest_versions:
                    version_info = latest_versions[0]  # Take first version
                    model = ModelMetadata(
                        model_name=model_data.get("name", ""),
                        version=version_info.get("version", "unknown"),
                        task="Unknown",  # Not in current API response
                        hospital="Unknown",  # Not in current API response
                        framework="Unknown",  # Not in current API response
                        training_date="Unknown",  # Not in current API response
                        frozen=version_info.get("stage") in ["Production", "Staged"],
                        input_size="Unknown",  # Not in current API response
                        output_classes=["Unknown"],  # Not in current API response
                        performance={},  # Not directly in current API response
                        size_mb=0.0,  # Not in current API response
                        checksum="",  # Not in current API response
                        tags=[],  # Not in current API response
                        description=model_data.get("description", "")
                    )
                    models.append(model)
            return models
        except Exception as e:
            # Fallback to mock data in case of error for development
            st.warning(f"Failed to fetch models from API: {str(e)}. Using mock data.")
            return self._get_mock_models()

    def get_model(self, model_name: str, version: str) -> Optional[ModelMetadata]:
        """
        Get a specific model version from the backend API.

        Args:
            model_name: Name of the model
            version: Version of the model

        Returns:
            ModelMetadata object if found, None otherwise
        """
        self._ensure_auth_token()
        try:
            response = self.api_client.session.get(
                f"{self.api_client.base_url}/models/{model_name}/{version}"
            )
            response.raise_for_status()
            model_data = response.json()

            # Extract model info from response
            # Note: The API returns detailed model info but not all fields we need
            model = ModelMetadata(
                model_name=model_data.get("name", ""),
                version=model_data.get("version", ""),
                task="Unknown",  # Would need to be enhanced in API
                hospital="Unknown",  # Would need to be enhanced in API
                framework="Unknown",  # Would need to be enhanced in API
                training_date="Unknown",  # Would need to be enhanced in API
                frozen=model_data.get("current_stage") in ["Production", "Staged"],
                input_size="Unknown",  # Would need to be enhanced in API
                output_classes=["Unknown"],  # Would need to be enhanced in API
                performance=model_data.get("metrics", {}),
                size_mb=0.0,  # Would need to be enhanced in API
                checksum="",  # Would need to be enhanced in API
                tags=[],  # Would need to be enhanced in API
                description=model_data.get("description", "")
            )
            return model
        except Exception as e:
            # Fallback to mock data in case of error for development
            st.warning(f"Failed to fetch model {model_name}:{version} from API: {str(e)}. Using mock data.")
            return self._get_mock_model(model_name, version)

    def get_models_by_task(self, task: str) -> List[ModelMetadata]:
        """
        Get models for a specific task.
        Note: This would require backend enhancement to filter by task.
        For now, we get all models and filter locally.
        """
        all_models = self.get_registered_models()
        return [model for model in all_models if model.task.lower() == task.lower()]

    def get_latest_model(self, model_name: str) -> Optional[ModelMetadata]:
        """
        Get the latest version of a model.
        Note: This would be enhanced with proper version sorting in a production system.
        """
        # Get all models and filter by name (would be better with backend endpoint)
        all_models = self.get_registered_models()
        matching_models = [m for m in all_models if m.model_name == model_name]
        if not matching_models:
            return None
        # Simple version sorting - in production would use proper semver
        return max(matching_models, key=lambda x: x.version)

    # Helper methods for development/fallback
    def _get_mock_models(self) -> List[ModelMetadata]:
        """Return mock models for development when API is unavailable."""
        from datetime import datetime
        models = [
            ModelMetadata(
                model_name="CheXpert-Pneumonia-DenseNet121",
                version="v2.1.0",
                task="Pneumonia Detection",
                hospital="CheXpert (Training)",
                framework="PyTorch",
                training_date="2024-06-15",
                frozen=True,
                frozen_date="2024-07-01",
                input_size="224x224x3",
                output_classes=["Normal", "Pneumonia"],
                performance={
                    "auc": 0.924,
                    "sensitivity": 0.89,
                    "specificity": 0.85,
                    "f1_score": 0.87
                },
                size_mb=45.2,
                checksum="a1b2c3d4e5f6...",
                tags=["production", "validated", "chexpert"],
                description="DenseNet121 model trained on CheXpert dataset for pneumonia detection"
            ),
            ModelMetadata(
                model_name="MIMIC-Cardiomegaly-ResNet50",
                version="v1.8.3",
                task="Cardiomegaly Detection",
                hospital="MIMIC-CXR",
                framework="TensorFlow",
                training_date="2024-05-22",
                frozen=True,
                frozen_date="2024-06-10",
                input_size="256x256x3",
                output_classes=["Normal", "Cardiomegaly"],
                performance={
                    "auc": 0.897,
                    "sensitivity": 0.86,
                    "specificity": 0.82,
                    "f1_score": 0.84
                },
                size_mb=92.7,
                checksum="f6e5d4c3b2a1...",
                tags=["production", "validated", "mimic"],
                description="ResNet50 model trained on MIMIC-CXR dataset for cardiomegaly detection"
            ),
            ModelMetadata(
                model_name="NIH-Nodule-EfficientNetB0",
                version="v3.0.1",
                task="Pulmonary Nodule Detection",
                hospital="NIH ChestX-ray",
                framework="PyTorch",
                training_date="2024-04-10",
                frozen=False,
                frozen_date=None,
                input_size="224x224x3",
                output_classes=["Normal", "Nodule"],
                performance={
                    "auc": 0.912,
                    "sensitivity": 0.88,
                    "specificity": 0.84,
                    "f1_score": 0.86
                },
                size_mb=28.9,
                checksum="c3b2a1f6e5d4...",
                tags=["staging", "testing", "nih"],
                description="EfficientNetB0 model for pulmonary nodule detection"
            )
        ]
        return models

    def _get_mock_model(self, model_name: str, version: str) -> Optional[ModelMetadata]:
        """Return a specific mock model for development when API is unavailable."""
        mock_models = self._get_mock_models()
        for model in mock_models:
            if model.model_name == model_name and model.version == version:
                return model
        return None