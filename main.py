from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import time
from config import init_setup
init_setup()

from api.visual_by_graph import router as visual_router
from api.data_sheet import router as data_sheet_router
from api.comment_filter import router as comment_router
from api.auth_router import router as auth_router
from api.security import get_current_user
from fastapi import Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
import secure

# Initialize secure headers (Helmet equivalent)
secure_headers = secure.Secure()

app = FastAPI(
    title="Social Media Performance Tracker API",
    description="FastAPI backend to get YouTube stats and download them in various formats."
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors, especially JSON decode errors.
    """
    errors = exc.errors()
    for error in errors:
        if error.get("type") == "json_invalid":
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid JSON format. If you are entering multiple links, please enter only one URL."}
            )
    
    return JSONResponse(
        status_code=422,
        content={"detail": errors}
    )

@app.middleware("http")
async def log_and_secure_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    # Helmet-style security headers
    secure_headers.set_headers(response)
    
    # Winston-style structured logging (Morgan format)
    logger.info(f"[{request.method}] {request.url.path} - HTTP {response.status_code} - {process_time:.2f}ms")
    
    return response

# Add CORS Middleware to allow requests from the frontend client
client_url = os.getenv("CLIENT_URL", "http://localhost:5173").rstrip("/")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[client_url, f"{client_url}/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routers from our /api modular structure
app.include_router(auth_router)
app.include_router(visual_router, dependencies=[Depends(get_current_user)])
app.include_router(data_sheet_router, dependencies=[Depends(get_current_user)])
app.include_router(comment_router, dependencies=[Depends(get_current_user)])

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Social Media Performance Tracker API!",
        "docs_url": "/docs"  # FastAPI uniquely provides Swagger UI out of the box
    }
