import uuid
from aiobotocore.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.platform_models import InferenceRequest
import os

# Fetch object storage configurations from environment variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT_URL_INTERNAL") if os.getenv("RUNNING_IN_DOCKER") else os.getenv("MINIO_ENDPOINT_URL_LOCAL", "http://localhost:9000")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minio_admin_password")
BUCKET_NAME = "medical-images"

async def upload_to_minio(file_bytes: bytes, file_name: str) -> str:
    """
    Uploads raw medical image bytes asynchronously to the MinIO storage bucket.
    Returns the final S3 URI string.
    """
    session = get_session()
    # Using async aiobotocore context for non-blocking I/O operations
    async with session.create_client(
        's3',
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name="us-east-1"
    ) as s3_client:
        # Generate a unique path inside the bucket to avoid collision
        unique_file_name = f"{uuid.uuid4()}_{file_name}"
        await s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=unique_file_name,
            Body=file_bytes
        )
        return f"s3://{BUCKET_NAME}/{unique_file_name}"

async def create_inference_record(db: AsyncSession, hospital_id: int, s3_uri: str) -> InferenceRequest:
    """
    Persists the transaction, generating the foundational request ID for subsequent drift detection.
    """
    # Create the unified database record matching the initial physical schema
    db_record = InferenceRequest(
        id=uuid.uuid4(),
        hospital_id=hospital_id,
        image_s3_uri=s3_uri,
        prediction_label=None, # Will be filled downstream in the pipeline during model execution
        uncertainty_score=None,
        latency_ms=None
    )
    db.add(db_record)
    await db.flush() # Secure the record generation within the ongoing async transaction
    return db_record