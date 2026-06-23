from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from backend.app.models.platform_models import FeedbackLog, InferenceRequest
from backend.app.schemas.feedback import FeedbackCreate
from fastapi import HTTPException, status

async def submit_feedback_log(db: AsyncSession, feedback_data: FeedbackCreate) -> FeedbackLog:
    """
    Submits and persists a physician's feedback (Ground Truth validation) for a specific inference request.
    Enforces referential integrity by checking the existence of the source UUID.
    """
    # 1. Verify if the inference request actually exists first
    result = await db.execute(select(InferenceRequest).filter(InferenceRequest.id == feedback_data.request_id))
    inference_request = result.scalars().first()
    
    if not inference_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inference request with ID {feedback_data.request_id} not found."
        )

    # 2. Check if feedback for this request has already been submitted (Unique constraint safeguard)
    feedback_result = await db.execute(select(FeedbackLog).filter(FeedbackLog.request_id == feedback_data.request_id))
    existing_feedback = feedback_result.scalars().first()
    
    if existing_feedback:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Feedback has already been logged for request ID {feedback_data.request_id}."
        )

    # 3. Handle strict constraints: If they disagree, a corrected_label MUST be provided
    if not feedback_data.is_agreed and not feedback_data.corrected_label:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A 'corrected_label' must be supplied if the physician disagrees with the prediction."
        )

    # 4. Initialize the ORM model object instance
    db_feedback = FeedbackLog(
        request_id=feedback_data.request_id,
        is_agreed=feedback_data.is_agreed,
        corrected_label=feedback_data.corrected_label if not feedback_data.is_agreed else None
    )

    db.add(db_feedback)
    await db.flush()  # Secure the record placement into PostgreSQL within the parent transaction
    return db_feedback