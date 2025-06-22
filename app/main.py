from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.config import settings
from app.api.v1.endpoints import crop
# We will create the logging setup later in app/core/logging.py
# from app.core.logging import setup_logging
from rich.console import Console

console = Console()

# We will call setup_logging() here later
# setup_logging()

# Create FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version="1.0.0"
)

# Add CORS (Cross-Origin Resource Sharing) middleware
# This allows web pages from any domain to make requests to your API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add Prometheus monitoring if enabled in settings
if settings.PROMETHEUS_ENABLED:
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app)

# Include the API router from the 'crop' endpoint file
# All routes defined in crop.router will be added to the app.
app.include_router(crop.router, prefix=settings.API_V1_STR, tags=["Face Segmentation"])

@app.on_event("startup")
async def startup_event():
    """
    Event handler that runs when the application starts.
    """
    console.print(f"[bold green]🚀 {settings.PROJECT_NAME} Started[/bold green]")
    console.print(f"[bold blue]OpenAPI docs available at: /docs[/bold blue]")

@app.get("/health", tags=["Health Check"])
async def health_check():
    """
    Simple health check endpoint to confirm the service is running.
    """
    return {"status": "healthy", "service": settings.PROJECT_NAME}