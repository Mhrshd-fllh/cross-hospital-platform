# cross-hospital-platform

A cross-hospital platform for medical image ingestion, drift detection, style adaptation, and feedback collection.

## Features

- Medical image ingestion via PACS integration
- Data drift detection using handcrafted features (histogram, FFT, LBP, sharpness)
- Style adaptation for cross-hospital generalization (histogram matching, FFT band reweighting, unsharp mask/blur calibration)
- Real-time alerting on drift detection
- Feedback loop for physician validation
- Telemetry logging to MLflow
- HIPAA-compliant image processing

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (for full stack deployment)
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd cross-hospital-platform
   ```

2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Set up environment variables:
   Copy the `.env` file to `.env.local` and adjust the values as needed for your environment.

4. Start the infrastructure services (PostgreSQL, MinIO, MLflow):
   ```bash
   docker-compose up -d
   ```

5. Generate the drift baseline (see below).

### Running the Baseline Calibration Script

To generate the drift baseline from CheXpert images, run the following script:

```bash
python scripts/build_drift_baseline.py
```

This will:
1. Sample CheXpert images (balanced by view and finding)
2. Extract handcrafted features (histogram, FFT, LBP, sharpness)
3. Save the baseline artifact to `baseline/chexpert_baseline.npz`
4. Save metadata to `baseline/chexpert_baseline_meta.json`

The script prints progress and a summary of the sample sizes.

### Configuration

The script can be configured by modifying the following variables in `scripts/build_drift_baseline.py`:
- `TOTAL_SAMPLES`: Total number of images to sample (default: 2000)
- `NUM_STRATA`: Number of strata (default: 4 for 2 views x 2 classes)
- `SEED`: Random seed for reproducibility (default: 42)

### Style Adaptation Configuration

The style adaptation method can be configured via the `ADAPTATION_METHOD` environment variable:
- `histogram_matching`: Match histogram to reference (default)
- `adaptive_histogram_equalization`: Apply CLAHE
- `adaptive_instance_normalization`: Match mean and standard deviation to reference

Set the variable in your `.env` file or environment, e.g.:
```
ADAPTATION_METHOD=histogram_matching
```

## Running the Tests

To run the unit tests, execute:

```bash
pytest
```

This will run all tests in the `backend/app/core/` and `backend/app/api/` directories.

## Test Coverage

- Feature extraction functions (`test_drift_features.py`)
- Drift detector (`test_drift_detector.py`)
- Style adaptation (`test_adaptation_pipeline.py`)
- API endpoints (`test_endpoints.py`)

## Environment Variables

The following environment variables are used by the application:

| Setting | Default | Description |
|---------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://platform_user:platform_password@localhost:5432/cross_hospital_platform` | Database connection URL |
| `MINIO_ENDPOINT_URL_LOCAL` | `http://localhost:9000` | MinIO endpoint for local development |
| `MINIO_ENDPOINT_URL_INTERNAL` | `http://minio-storage:9000` | MinIO endpoint for internal Docker communication |
| `MLFLOW_TRACKING_URI_LOCAL` | `http://localhost:5000` | MLflow tracking URI for local development |
| `MLFLOW_TRACKING_URI_INTERNAL` | `http://mlflow-server:5000` | MLflow tracking URI for internal Docker communication |
| `MLFLOW_S3_ENDPOINT_URL` | `http://minio-storage:9000` | S3 endpoint for MLflow artifact storage |
| `ALERT_WEBHOOK_URL` | *(unset)* | Webhook URL for drift alerts (e.g., Slack webhook) |
| `DRIFT_PVALUE_THRESHOLD` | `0.05` | P-value threshold for triggering drift alerts |
| `ADAPTATION_METHOD` | `histogram_matching` | Style adaptation method (histogram_matching, adaptive_histogram_equalization, adaptive_instance_normalization) |
| `CANONICAL_RESOLUTION` | `320,320` | Target image resolution for preprocessing |
| `MIN_DIMENSION` | `64` | Minimum allowed image dimension |
| `MAX_DIMENSION` | `2048` | Maximum allowed image dimension |

Note: When running inside Docker containers, the `_INTERNAL` variants of the URLs are used. When running scripts directly on the host, the `_LOCAL` variants are used.

## Project Structure

- `backend/`: Contains the FastAPI application
  - `app/`: Main application code
    - `api/`: API endpoints
    - `core`: Core functionality (drift detection, feature extraction, style adaptation, telemetry, alerting, validation)
    - `crud`: Database operations
    - `models`: Database models
    - `schemas`: Pydantic models for API requests/responses
- `scripts/`: Utility scripts (baseline creation, model freezing)
- `baseline/`: Stores the drift baseline artifact
- `data/`: Stores downloaded datasets (CheXpert, MIMIC-CXR)

## Frontend Implementation

A Streamlit-based frontend has been implemented in the `frontend/` directory, providing a complete user interface for the Cross-Hospital Generalization Platform.

### Features

- **Complete Workflow UI**: Upload → Validation → Drift Detection → Style Adaptation → Inference
- **Model Registry Browser**: View and select from available models (including CheXpert-trained models)
- **Interactive Visualizations**: Drift analysis charts, feature importance, distribution comparisons
- **Real-time Monitoring**: System metrics, health checks, and alerting dashboard
- **Hospital Management**: Facility status, statistics, and activity tracking
- **Feedback Collection**: Physician feedback interface for model predictions
- **Settings View**: Read-only system configuration display
- **Reusable Component Library**: Custom Streamlit components for metrics, charts, tables, upload widgets, etc.
- **Mock Service Layer**: All backend services are mocked for frontend development, simulating interactions with PostgreSQL, MinIO, and MLflow

### Key Components

- **Pages**: 13 pages covering all aspects of the platform (dashboard, upload, validation, drift, adaptation, models, inference, monitoring, hospitals, logs, alerts, feedback, settings)
- **Components**: 12 reusable UI components (navbar, sidebar, status badges, metric cards, model cards, charts, tables, timelines, upload widgets, image previews, feedback widgets, alert widgets, drift indicators)
- **Services**: 12 mock service implementations that mirror the backend service interfaces
- **Data Models**: Shared Pydantic models for data consistency between frontend and backend

### Technology Stack

- **Framework**: Streamlit for reactive web application
- **Visualization**: Plotly for interactive charts and graphs
- **State Management**: Streamlit session state for workflow continuity
- **Styling**: Custom CSS via Streamlit's markdown capabilities

### Development Status

The frontend is implemented as a separate branch (`feature/frontend`) and consists of 43 Python files organized in a modular structure. All backend interactions are currently simulated through mock services, allowing for independent frontend development and testing.

To run the frontend locally:
```bash
streamlit run frontend/app.py
```

Note: The frontend is designed to work with the backend services. For full functionality, ensure the backend is running and properly configured.
## Development

### Making Changes

1. Create a new branch for your feature or bugfix.
2. Make your changes.
3. Add or update tests as needed.
4. Run the test suite to ensure everything passes.
5. Submit a pull request.

### Code Style

We follow the PEP 8 style guide for Python code.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.