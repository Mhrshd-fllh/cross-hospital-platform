"""
Mock implementation of the RegistryService for development and testing.
Returns simulated data for frontend development.
"""

import random
from datetime import datetime, timedelta
from typing import List, Optional
from . import RegistryService, ModelMetadata

class MockRegistryService(RegistryService):
    """Mock implementation of RegistryService."""

    def __init__(self):
        self._models: List[ModelMetadata] = self._generate_mock_models()

    def _generate_mock_models(self) -> List[ModelMetadata]:
        """Generate mock model data."""
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

    def get_registered_models(self) -> List[ModelMetadata]:
        """Get all registered models."""
        return self._models.copy()

    def get_model(self, model_name: str, version: str) -> Optional[ModelMetadata]:
        """Get a specific model version."""
        for model in self._models:
            if model.model_name == model_name and model.version == version:
                return model
        return None

    def get_models_by_task(self, task: str) -> List[ModelMetadata]:
        """Get models for a specific task."""
        return [model for model in self._models if model.task.lower() == task.lower()]

    def get_latest_model(self, model_name: str) -> Optional[ModelMetadata]:
        """Get the latest version of a model."""
        matching_models = [m for m in self._models if m.model_name == model_name]
        if not matching_models:
            return None
        # Sort by version (simplistic - in reality would use proper version comparison)
        return max(matching_models, key=lambda x: x.version)

# Factory function
def create_registry_service() -> RegistryService:
    """Create an instance of the mock RegistryService."""
    return MockRegistryService()