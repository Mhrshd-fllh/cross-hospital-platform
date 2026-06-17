import mlflow
import mlflow.pytorch
import torch
import torchvision.models as models

# Configure central MLflow tracking URI pointing to our local docker container
mlflow.set_tracking_uri("http://localhost:5000")

def freeze_and_save_model(model_name: str, num_classes: int, experiment_name: str, run_name: str):
    """
    Loads the baseline model, freezes all parameters to zero out the learning rate,
    and registers the frozen artifact directly into the MLflow Model Registry.
    """
    mlflow.set_experiment(experiment_name)
    
    with mlflow.start_run(run_name=run_name) as run:
        print(f"--- Starting freezing process for {model_name} ({run_name}) ---")
        
        # 1. Load the baseline architecture based on the medical dataset requirements
        if model_name == "densenet121":
            # DenseNet121 for CheXpert/MIMIC-CXR multi-label chest X-ray classification
            model = models.densenet121(weights=models.DenseNet121_Weights.DEFAULT)
            num_ftrs = model.classifier.in_features
            model.classifier = torch.nn.Linear(num_ftrs, num_classes)
        elif model_name == "resnet50":
            # ResNet50 for Camelyon17 histopathology tumor binary classification
            model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
            num_ftrs = model.fc.in_features
            model.fc = torch.nn.Linear(num_ftrs, num_classes)
            
        # 2. Freeze all layers (weights) to prevent unintended retraining during evaluation
        for param in model.parameters():
            param.requires_grad = False
            
        # Set model to evaluation mode for deterministic inference behavior
        model.eval() 
        
        # 3. Log crucial MLOps metadata and parameters into MLflow
        mlflow.log_param("backbone", model_name)
        mlflow.log_param("num_classes", num_classes)
        mlflow.log_param("status", "frozen_baseline")
        
        # 4. Serialize and register the frozen model artifact into the central registry
        mlflow.pytorch.log_model(
            pytorch_model=model,
            artifact_path="model",
            registered_model_name=run_name
        )
        
        print(f"Successfully registered {run_name} in MLflow Registry.\n")

if __name__ == "__main__":
    # Task 1: Freeze and register Camelyon17 baseline model (Binary classification)
    freeze_and_save_model(
        model_name="resnet50", 
        num_classes=2, 
        experiment_name="Camelyon17_Tumor_Classification", 
        run_name="camelyon17_baseline_frozen"
    )
    
    # Task 2: Freeze and register CheXpert/MIMIC-CXR baseline model (14 multi-label classes)
    freeze_and_save_model(
        model_name="densenet121", 
        num_classes=14, 
        experiment_name="ChestXRay_MultiLabel_Classification", 
        run_name="chexpert_mimic_baseline_frozen"
    )