from typing import Any, List
import base64
from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import get_logger

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.translation_job import JobStatus
from app.schemas.translation import TranslationJob, TranslationJobCreate, TranslationResponse
from app.services.translation import translation_service

router = APIRouter()
logger = get_logger("app.api.translations")


@router.post("/", response_model=TranslationResponse)
async def create_translation_job(
    *,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...),
    glossary_id: int = Form(None),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new translation job.
    """
    try:
        file_content = await file.read()
        
        # Create job input
        job_in = TranslationJobCreate(
            source_language=source_lang,
            target_language=target_lang,
            glossary_id=glossary_id,
            file=file_content
        )
        
        # Create job
        job = await translation_service.create_translation_job(
            db=db,
            obj_in=job_in,
            user_id=current_user.id,
            filename=file.filename
        )
        
        # Start processing asynchronously
        await translation_service.process_translation_job(db=db, job_id=job.id)
        
        return TranslationResponse(
            status=200,
            job_id=job.id,
            message="Translation job created successfully"
        )
    except Exception as e:
        logger.error("Error creating translation job", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error creating translation job: {str(e)}")


@router.get("/", response_model=List[TranslationJob])
async def read_translation_jobs(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve translation jobs.
    """
    if deps.is_superuser(current_user):
        jobs = await translation_service.get_multi(db, skip=skip, limit=limit)
    else:
        jobs = await translation_service.get_multi_by_user(
            db=db, user_id=current_user.id, skip=skip, limit=limit
        )
    return jobs


@router.get("/{id}", response_model=TranslationJob)
async def read_translation_job(
    *,
    db: AsyncSession = Depends(get_db),
    id: int = Path(..., title="The ID of the translation job to get"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get translation job by ID.
    """
    job = await translation_service.get(db=db, id=id)
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    if not deps.is_superuser(current_user) and (job.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return job


@router.post("/{id}/cancel", response_model=TranslationJob)
async def cancel_translation_job(
    *,
    db: AsyncSession = Depends(get_db),
    id: int = Path(..., title="The ID of the translation job to cancel"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Cancel a translation job.
    """
    job = await translation_service.get(db=db, id=id)
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    if not deps.is_superuser(current_user) and (job.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Can only cancel jobs that are pending or processing
    if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job with status {job.status}")
    
    job = await translation_service.update_status(db=db, job_id=id, status=JobStatus.FAILED, 
                                                error_message="Cancelled by user")
    return job
