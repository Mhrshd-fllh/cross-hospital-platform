from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional

class FeedbackSubmitSchema(BaseModel):
    """
    Schema validating the structured Human-in-the-loop feedback payload from clinical dashboards.
    """
    request_id: UUID = Field(..., description="The unique image/transaction UUID identifier")
    is_agreed: bool = Field(..., description="True if clinician agrees with AI output, False otherwise")
    corrected_label: Optional[str] = Field(None, max_length=100, description="The correct ground truth label provided by clinician")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
                "is_agreed": False,
                "corrected_label": "Pneumonia"
            }
        }