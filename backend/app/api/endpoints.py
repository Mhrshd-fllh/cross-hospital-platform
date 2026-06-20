from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.request_schemas import InferenceRequestResponse
from backend.app.crud import inference_crud
from backend.app.core.orchestrator import ClinicalPipelineOrchestrator

router = APIRouter(prefix="/v1/inference", tags=["Inbound PACS APIs"])

@router.post(
    "/ingest", 
    response_model=dict, # Expanding response schema to include the end-to-end tracking JSON
    status_code=status.HTTP_201_CREATED,
    summary="Ingest and route medical image through the orchestrated pipeline"
)
async def ingest_medical_image(
    hospital_id: int = Form(..., description="Target hospital identifier"),
    file: UploadFile = File(..., description="Medical image payload (.dcm, .nii, .jpg)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Asynchronously ingests images from PACS, registers base records, and hands over control 
    to the Orchestrator for structured drift checks and deep learning prediction execution.
    """
    allowed_extensions = (".dcm", ".nii", ".jpg", ".jpeg", ".zip")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension. Allowed types: {allowed_extensions}"
        )
        
    try:
        # 1. Persist the file payload to MinIO Object storage
        contents = await file.read()
        s3_uri = await inference_crud.upload_to_minio(contents, file.filename)
        
        # 2. Open basic metadata record inside PostgreSQL database
        db_record = await inference_crud.create_inference_record(db, hospital_id, s3_uri)
        
        # 3. Instantiate the Orchestrator and execute the step-by-step pipeline asynchronously
        orchestrator = ClinicalPipelineOrchestrator(db_session=db, request_id=db_record.id)
        pipeline_result = await orchestrator.execute_pipeline(image_s3_uri=s3_uri)
        
        return pipeline_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline integration failure: {str(e)}"
        )