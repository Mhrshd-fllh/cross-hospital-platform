import os
import mlflow
import numpy as np
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class ModelService:
    """
    Singleton service for loading and serving an MLflow model.
    The model is loaded once on first use and reused for subsequent predictions.
    """
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ModelService, cls).__new__(cls)
                    cls._instance._model = None
                    cls._instance._model_uri = None
                    cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        """Load the MLflow model from the URI specified in environment."""
        model_uri = os.getenv("MLFLOW_MODEL_URI")
        if not model_uri:
            raise RuntimeError("MLFLOW_MODEL_URI environment variable not set")
        try:
            self._model = mlflow.pyfunc.load_model(model_uri)
            self._model_uri = model_uri
            logger.info(f"Successfully loaded MLflow model from {model_uri}")
        except Exception as e:
            logger.exception(f"Failed to load MLflow model from {model_uri}")
            raise e

    def predict(self, input_data: np.ndarray) -> np.ndarray:
        """
        Run prediction on the provided input data.
        :param input_data: NumPy array of shape (batch, ...) as expected by the model.
        :return: Model predictions as NumPy array.
        """
        if self._model is None:
            raise RuntimeError("Model not loaded")
        try:
            # mlflow.pyfunc.predict returns a pandas DataFrame or numpy array depending on model flavor.
            # We convert to numpy array for consistency.
            pred = self._model.predict(input_data)
            if hasattr(pred, "to_numpy"):
                pred = pred.to_numpy()
            return np.array(pred)
        except Exception as e:
            logger.exception("Model prediction failed")
            raise e