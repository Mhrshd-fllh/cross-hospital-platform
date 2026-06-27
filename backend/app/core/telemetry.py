import os
import asyncio
import mlflow
from typing import Dict, Any

class TelemetryService:
    """
    Production-ready Telemetry service to log live model metrics, 
    parameters, and inference outputs directly to the MLflow Tracking Server.
    """
    
    def __init__(self):
        # Fetch internal Docker network URI for MLflow or fallback to local
        self.tracking_uri = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://mlflow_server:5000")
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment("Clinical_Inference_Pipeline")

    def _log_to_mlflow(self, run_name: str, params: Dict[str, Any], metrics: Dict[str, Any]):
        """
        Synchronous worker method executed inside a separate thread pool to avoid blocking ASGI.
        """
        with mlflow.start_run(run_name=run_name):
            # Log operational parameters (e.g., S3 paths, compliance flags)
            mlflow.log_params(params)
            
            # Log performance metrics (e.g., pipeline latency, confidence intervals)
            mlflow.log_metrics(metrics)

    async def log_inference_telemetry(self, request_id: str, params: Dict[str, Any], metrics: Dict[str, Any]):
        """
        Non-blocking wrapper leveraging the asyncio event loop executor 
        to offload blocking MLflow client network operations.
        """
        loop = asyncio.get_running_loop()
        run_name = f"Inference_{str(request_id)[:8]}"
        
        await loop.run_in_executor(
            None, 
            self._log_to_mlflow, 
            run_name, 
            params, 
            metrics
        )
