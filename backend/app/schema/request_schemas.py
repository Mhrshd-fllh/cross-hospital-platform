from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class InferenceRequestResponse(BaseModel):
    """
    Schema for successful inference request ingestion response.
    """

    request_id: UUID = Field(..., description="Unique generated UUID for the clinical transaction")
    hospital_id: int = Field(..., description="Unique identifier for the hospital")
    image_s3_uri: int = Field(..., description="S3 URI of the image to be processed")

    created_at: datetime

    class Config:
        from_attributes = True