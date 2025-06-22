from fastapi import APIRouter, HTTPException, Depends, status
from app.models.schemas import CropSubmitRequest, JobResponse, CropResult
from app.core.celery_app import celery_app # Import from the correct central location
import uuid
import hashlib
from rich.console import Console

console = Console()
router = APIRouter()


@router.post("/submit", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_crop_job(request: CropSubmitRequest):
    """
    Submit a face segmentation job for asynchronous processing.
    """
    try:
        job_id = str(uuid.uuid4())
        image_hash = hashlib.md5(request.image.encode()).hexdigest()
        
        job_data = {
            "job_id": job_id,
            "request": request.dict(),
            "image_hash": image_hash
        }
        
        # In a real system with a DB, we would check the cache here.
        # For now, we always queue the job.
        
        from app.workers.celery_worker import process_face_segmentation
        process_face_segmentation.apply_async(args=[job_data], task_id=job_id)
        
        console.print(f"[bold yellow]Submitted job {job_id} to the queue.[/bold yellow]")
        
        return JobResponse(id=job_id, status="pending")
        
    except Exception as e:
        console.print(f"[bold red]Error submitting job: {str(e)}[/bold red]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while submitting the job."
        )


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status and result of a processing job.
    """
    try:
        task = celery_app.AsyncResult(job_id)

        if task.state == 'PENDING':
             # The task is waiting to be executed or is unknown
             return JobResponse(id=job_id, status="pending")
        
        elif task.state == 'SUCCESS':
            # --- THIS IS THE KEY FIX ---
            # The result of the task is stored in task.result
            result_data = task.result
            if result_data and "svg" in result_data and "mask_contours" in result_data:
                return CropResult(**result_data)
            else:
                # This can happen if the task succeeded but returned an unexpected format
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Task succeeded but result is invalid."
                )

        elif task.state == 'FAILURE':
            # The task failed with an exception
            # task.info contains the exception information
            error_info = str(task.info) 
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Job failed: {error_info}"
            )
            
        else: # Other states like 'STARTED', 'RETRY'
            return JobResponse(id=job_id, status=task.state.lower())

    except Exception as e:
        console.print(f"[bold red]Error getting job status for {job_id}: {str(e)}[/bold red]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching the job status."
        )
