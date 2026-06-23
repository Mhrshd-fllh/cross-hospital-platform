import mlflow
import mlflow.pytorch
import torch
import torchvision.models as models
from mlflow.tracking import MlflowClient

# Connect to the central MLflow Tracking Server
mlflow.set_tracking_uri("http://localhost:5000")
client = MlflowClient()

def register_frozen_model_with_metadata(model_name: str, num_classes: int, experiment_name: str, model_registry_name: str, dataset_metadata: dict):
    """
    Freezes the backbone, logs parameters/metrics, and explicitly registers 
    the model in the MLflow Model Registry with production tags and statistical metadata.
    """
    mlflow.set_experiment(experiment_name)
    
    with mlflow.start_run() as run:
        run_id = run.info.run_id
        print(f"--- Registering {model_registry_name} (Run ID: {run_id}) ---")
        
        # 1. Initialize and freeze the specific architecture
        if model_name == "densenet121":
            model = models.densenet121(weights=models.DenseNet121_Weights.DEFAULT)
            model.classifier = torch.nn.Linear(model.classifier.in_features, num_classes)
        elif model_name == "resnet50":
            model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
            model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
            
        for param in model.parameters():
            param.requires_grad = False
        model.eval()
        
        # 2. Log baseline structural parameters
        mlflow.log_param("architecture", model_name)
        mlflow.log_param("num_classes", num_classes)
        mlflow.log_param("framework", "pytorch")
        
        # 3. Log the model artifact and register it in the Model Registry
        model_info = mlflow.pytorch.log_model(
            pytorch_model=model,
            artifact_path="model",
            registered_model_name=model_registry_name
        )
        
        # 4. Fetch the latest version to apply statistical and production tags
        latest_version_info = client.get_latest_versions(model_registry_name, stages=["None"])[0]
        current_version = latest_version_info.version
        
        # Set descriptive tags on the specific model version
        client.set_model_version_tag(model_registry_name, current_version, "status", "frozen_baseline")
        for key, value in dataset_metadata.items():
            client.set_model_version_tag(model_registry_name, current_version, key, str(value))
            
        print(f"Successfully registered version {current_version} for {model_registry_name}.\n")

if __name__ == "__main__":
    # Statistical metadata for Camelyon17 (Histopathology)
    camelyon17_meta = {
        "source_dataset": "Camelyon17",
        "modality": "Digital Histopathology (WSI)",
        "resolution": "96x96 pixels",
        "target_task": "Lymph node tumor binary classification"
    }
    register_frozen_model_with_metadata(
        model_name="resnet50",
        num_classes=2,
        experiment_name="Camelyon17_Tumor_Classification",
        model_registry_name="camelyon17_frozen_registry",
        dataset_metadata=camelyon17_meta
    )
    
    # Statistical metadata for CheXpert / MIMIC-CXR (Radiology)
    chexpert_meta = {
        "source_dataset": "CheXpert / MIMIC-CXR",
        "modality": "Chest X-Ray (CR/DX)",
        "resolution": "Variable (Preprocessed to 224x224)",
        "target_task": "14 Multi-label lung pathology classification"
    }
    register_frozen_model_with_metadata(
        model_name="densenet121",
        num_classes=14,
        experiment_name="ChestXRay_MultiLabel_Classification",
        model_registry_name="chexpert_mimic_frozen_registry",
        dataset_metadata=chexpert_meta
    )