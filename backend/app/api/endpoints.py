import json
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.schema.feedback_schemas import FeedbackSubmitSchema
from backend.app.models.platform_models import InferenceRequest, FeedbackLog
from backend.app.crud import inference_crud
from backend.app.core.orchestrator import ClinicalPipelineOrchestrator

router = APIRouter(prefix="/v1/clinical", tags=["Clinical Ingestion & Feedback"])

@router.post(
    "/inference/ingest", 
    status_code=status.HTTP_201_CREATED,
    summary="Ingest medical image and run end-to-end telemetry tracked pipeline"
)
async def ingest_medical_image(
    hospital_id: int = Form(..., description="Target hospital identifier"),
    metadata_json: str = Form("{}", description="Raw clinical stringified JSON metadata"),
    file: UploadFile = File(..., description="Medical image payload (.dcm, .nii, .jpg)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests PACS medical file, executes HIPAA cleaning, saves data drift parameters, 
    and logs model telemetry results dynamically with zero mock blocks.
    """
    allowed_extensions = (".dcm", ".nii", ".jpg", ".jpeg", ".zip")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format extension."
        )
        
    try:
        raw_metadata = json.loads(metadata_json)
        contents = await file.read()
        
        # 1. Persistent storage upload to MinIO
        s3_uri = await inference_crud.upload_to_minio(contents, file.filename)
        
        # 2. Database transaction blueprint record allocation
        db_record = await inference_crud.create_inference_record(db, hospital_id, s3_uri)
        
        # 3. Handover transaction lock to production orchestrator
        orchestrator = ClinicalPipelineOrchestrator(db_session=db, request_id=db_record.id)
        pipeline_result = await orchestrator.execute_pipeline(image_s3_uri=s3_uri, raw_metadata=raw_metadata)
        
        return pipeline_result
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid stringified metadata_json payload format.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline transaction failed: {str(e)}")


@router.post(
    "/feedback/submit",
    status_code=status.HTTP_200_OK,
    summary="Submit diagnostic validation feedback from physicians"
)
async def submit_physician_feedback(
    feedback_data: FeedbackSubmitSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Feedback Loop API (Task 3-2): Collects ground-truth audits from pathologists/radiologists,
    mapping clinical disagreements securely against unique image tracking records.
    """
    # 1. Ensure the underlying inference request transaction actually exists
    query = select(InferenceRequest).where(InferenceRequest.id == feedback_data.request_id)
    result = await db.execute(query)
    inference_request = result.scalar_one_or_none()
    
    if not inference_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference request matching UUID {feedback_data.request_id} not found."
        )
        
    # 2. Enforce validation constraint: corrected_label is mandatory if physician disagrees
    if not feedback_data.is_agreed and not feedback_data.corrected_label:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A 'corrected_label' must be provided when the physician disagrees with the prediction."
        )
        
    try:
        # 3. Instantiating the relational feedback entity mapping to logs_feedback physical table
        feedback_entry = FeedbackLog(
            request_id=feedback_data.request_id,
            is_agreed=feedback_data.is_agreed,
            corrected_label=feedback_data.corrected_label if not feedback_data.is_agreed else None
        )
        
        db.add(feedback_entry)
        await db.flush() # Buffer to catch unique or foreign constraints violations
        await db.commit() # Safely commit across postgres database
        
        return {
            "status": "Feedback Logged",
            "request_id": feedback_data.request_id,
            "saved_as_ground_truth": not feedback_data.is_agreed
        }
        
    except Exception as db_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback log violation: Ensure feedback for this request has not been submitted previously."
        )