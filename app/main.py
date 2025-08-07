from fastapi import FastAPI, Depends, HTTPException, Request as FastAPIRequest
import logging
import uuid
import time
import os

from .config import settings
from .schemas import ProcessFolderRequest, ClassifiedDocumentsResponse
from .services.workflow_service import WorkflowService
from .services.ai_provider_interface import AIProviderInterface
from .services.openai_provider import OpenAIProvider
from .logging_config import setup_logging

# Setup logging once on application startup
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Document Processing Microservice",
    description="A service to cluster, classify, and sequence documents from a folder.",
    version="1.2.0"
)

# --- Middleware for Request ID and Latency Logging ---
@app.middleware("http")
async def log_requests_middleware(request: FastAPIRequest, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    # Make request_id available to the rest of the application
    request.state.request_id = request_id

    log_extra = {
        'request_id': request_id,
        'path': request.url.path,
        'method': request.method,
        'client_ip': request.client.host if request.client else "N/A"
    }
    logger.info("request_started", extra=log_extra)

    response = await call_next(request)

    process_time_ms = (time.perf_counter() - start_time) * 1000
    log_extra['total_latency_ms'] = round(process_time_ms, 2)
    log_extra['status_code'] = response.status_code
    
    logger.info("request_finished", extra=log_extra)
    
    return response

# --- Dependency Injection ---
def get_ai_provider() -> AIProviderInterface:
    if settings.AI_PROVIDER.lower() == "openai":
        return OpenAIProvider()
    raise ValueError(f"Unsupported AI_PROVIDER configured: {settings.AI_PROVIDER}")

# --- API Endpoints ---
@app.post("/v1/documents/process-folder", response_model=ClassifiedDocumentsResponse, tags=["Document Processing"])
async def process_document_folder(
    request: ProcessFolderRequest,
    fastapi_req: FastAPIRequest,
    ai_provider: AIProviderInterface = Depends(get_ai_provider)
):
    """
    Accepts a folder path, processes all documents within it to cluster,
    classify, and sequence them, and returns a structured JSON result.
    """
    request_id = fastapi_req.state.request_id
    log_extra = {'request_id': request_id}
    logger.info(f"Initiating processing for folder: {request.folder_path}", extra=log_extra)
    
    try:
        workflow = WorkflowService(ai_provider)
        result = workflow.process_folder(request, request_id)
        return result
    except FileNotFoundError as e:
        logger.error(f"File or folder not found during processing", extra=log_extra, exc_info=True)
        raise HTTPException(status_code=404, detail=f"The specified path was not found: {e}")
    except Exception:
        logger.critical("An unhandled exception occurred during document processing.", extra=log_extra, exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred. Please check logs for Request ID: {request_id}")

@app.get("/health", tags=["Health"])
def health_check():
    """Provides a simple health check endpoint."""
    return {"status": "ok", "service": "Document Processor"}