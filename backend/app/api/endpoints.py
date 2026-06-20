from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.request_schemas import InferenceRequestResponse
from backend.app.crud import inference_crud

router = APIRouter(prefix="/v1/inference", tags=["Inbound PACS APIs"])

@router.post(
    "/ingest", 
    response_model=InferenceRequestResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Ingest medical images from clinical PACS clients"
)
async def ingest_medical_image(
    hospital_id: int = Form(..., description="Target hospital identifier"),
    file: UploadFile = File(..., description="Medical image payload (.dcm, .nii, .jpg)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Asynchronously ingests binary images from hospitals, uploads them to object storage, 
    and logs metadata into PostgreSQL.
    """
    # 1. Enforce acceptable file formats for clinical safety
    allowed_extensions = (".dcm", ".nii", ".jpg", ".jpeg", ".zip")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension. Allowed types: {allowed_extensions}"
        )
        
    try:
        # 2. Read file contents asynchronously
        contents = await file.read()
        
        # 3. Stream the file object into the local S3/MinIO bucket
        s3_uri = await inference_crud.upload_to_minio(contents, file.filename)
        
        # 4. Save metadata track in PostgreSQL database
        db_record = await inference_crud.create_inference_record(db, hospital_id, s3_uri)
        
        return db_record
        
    except Exception as e:
        # Rollback is automatically triggered by the get_db context manager on uncaught exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal pipeline failure during ingestion process: {str(e)}"
        )