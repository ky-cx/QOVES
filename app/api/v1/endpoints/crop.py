from fastapi import APIRouter, HTTPException, Depends, status
from app.models.schemas import CropSubmitRequest, JobResponse, CropResult
from app.workers.celery_worker import process_face_segmentation, celery_app
# The CacheService and get_db dependency will be created in later steps
# from app.services.cache_service import CacheService
# from app.core.dependencies import get_db
from sqlalchemy.orm import Session
import uuid
import hashlib
from rich.console import Console

console = Console()
router = APIRouter()

# This is a placeholder for the real dependencies we will create later.
# This allows the code to be syntactically correct for now.
class PlaceholderDB:
    def query(self, *args, **kwargs): return self
    def filter(self, *args, **kwargs): return self
    def first(self, *args, **kwargs): return None
    def commit(self): pass
    def add(self, *args, **kwargs): pass

def get_db():
    return PlaceholderDB()

class CacheService:
    def __init__(self, db: Session): self.db = db
    async def get_cached_result(self, h): return None
    async def store_job(self, *args): pass
    async def get_job_status(self, job_id):
        task = celery_app.AsyncResult(job_id)
        if task.state == 'SUCCESS':
            return {"status": "completed", "result": task.result}
        elif task.state == 'FAILURE':
            return {"status": "failed", "error": str(task.info)}
        return {"status": task.state}


@router.post("/submit", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_crop_job(
    request: CropSubmitRequest,
    # db: Session = Depends(get_db) # We will uncomment this later
):
    """
    Submit a face segmentation job for asynchronous processing.
    """
    db: Session = get_db() # Using placeholder for now

    try:
        # Create a unique hash for the image content to use as a cache key.
        # Note: A more robust method would be a perceptual hash.
        image_hash = hashlib.md5(request.image.encode()).hexdigest()
        
        # Check cache first
        cache_service = CacheService(db)
        cached_result = await cache_service.get_cached_result(image_hash)
        
        if cached_result:
            console.print(f"[bold blue]Cache hit for image hash: {image_hash}[/bold blue]")
            # If the result is already in the cache, we can respond immediately
            # or handle it as a completed job. For simplicity, we'll still queue it,
            # but a production system might return the result directly.
            # Here, we will just note the cache hit and proceed.
            pass

        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        job_data = {
            "job_id": job_id,
            "request": request.dict(),
            "image_hash": image_hash
        }
        
        # Send the task to the Celery worker queue
        process_face_segmentation.apply_async(args=[job_data], task_id=job_id)
        
        # Store job info in the database (will be fully implemented with CacheService)
        await cache_service.store_job(job_id, "pending", image_hash)
        
        console.print(f"[bold yellow]Submitted job {job_id} to the queue.[/bold yellow]")
        
        return JobResponse(id=job_id, status="pending")
        
    except Exception as e:
        console.print(f"[bold red]Error submitting job: {str(e)}[/bold red]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while submitting the job."
        )


@router.get("/status/{job_id}")
async def get_job_status(
    job_id: str,
    # db: Session = Depends(get_db) # We will uncomment this later
):
    """
    Get the status and result of a processing job.
    """
    db: Session = get_db() # Using placeholder for now
    
    try:
        cache_service = CacheService(db)
        status_info = await cache_service.get_job_status(job_id) # This uses Celery backend

        if status_info['status'] == 'PENDING':
             return JobResponse(id=job_id, status="pending")
        elif status_info['status'] == 'SUCCESS':
            return CropResult(**status_info["result"])
        elif status_info['status'] == 'FAILURE':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Job failed: {status_info.get('error', 'Unknown error')}"
            )
        else: # Other states like 'STARTED', 'RETRY'
            return JobResponse(id=job_id, status=status_info['status'])

    except Exception as e:
        console.print(f"[bold red]Error getting job status for {job_id}: {str(e)}[/bold red]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching the job status."
        )