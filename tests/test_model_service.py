import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from backend.app.core.model_service import ModelService

@pytest.fixture
def mock_model():
    mock = MagicMock()
    # predict returns a numpy array of shape (1, num_classes) with probabilities summing to 1
    mock.predict.return_value = np.array([[0.1, 0.7, 0.2]])  # 3 classes
    return mock

def test_model_service_singleton():
    # Ensure singleton behavior
    s1 = ModelService()
    s2 = ModelService()
    assert s1 is s2

def test_model_service_loads_model(monkeypatch):
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([[0.5, 0.5]])
    with patch("mlflow.pyfunc.load_model", return_value=mock_model) as mock_load:
        service = ModelService()
        # Access the model via predict to trigger load if needed
        result = service.predict(np.zeros((1, 224, 224, 3)))
        mock_load.assert_called_once()
        assert isinstance(result, np.ndarray)
        assert result.shape == (1, 2)

def test_model_service_predict_returns_probabilities(monkeypatch):
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([[0.2, 0.3, 0.5]])
    with patch("mlflow.pyfunc.load_model", return_value=mock_model):
        service = ModelService()
        inp = np.zeros((1, 224, 224, 3))
        out = service.predict(inp)
        assert np.allclose(out, np.array([[0.2, 0.3, 0.5]]))
        # Ensure the model's predict was called with the input
        mock_model.predict.assert_called_once_with(inp)