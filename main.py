
"""
STEP File Analysis API
FastAPI backend for processing STEP files and extracting
geometric, topology, and validation data.
"""

import os
import tempfile
import logging
from typing import Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .step_processor import STEPProcessor


# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("step-api")

# ------------------------------------------------------------------------------
# FastAPI App
# ------------------------------------------------------------------------------
app = FastAPI(
    title="STEP File Analysis API",
    description="API for analyzing STEP files and extracting geometric, topology, and metadata",
    version="1.1.0"
)

# ------------------------------------------------------------------------------
# CORS Configuration
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# STEP Processor
# ------------------------------------------------------------------------------
processor = STEPProcessor()
SUPPORTED_EXTENSIONS = {".step", ".stp"}

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
def validate_step_file(filename: str) -> str:
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {ext}. Only STEP/STP files supported."
        )
    return ext


def save_temp_file(content: bytes, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        return tmp.name


def cleanup_temp_file(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.unlink(path)
    except Exception as exc:
        logger.warning("Failed to delete temp file: %s", exc)

# ------------------------------------------------------------------------------
# Health Endpoints
# ------------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "STEP File Analysis API",
        "version": "1.1.0"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "occt_available": processor.is_available(),
        "supported_formats": ["STEP", "STP"]
    }

# ------------------------------------------------------------------------------
# Full STEP Analysis
# ------------------------------------------------------------------------------
@app.post("/analyze")
async def analyze_step_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    ext = validate_step_file(file.filename)
    content = await file.read()
    temp_path = None

    try:
        temp_path = save_temp_file(content, ext)
        logger.info(
            "Processing STEP file: %s (%d bytes)",
            file.filename,
            len(content)
        )

        result = processor.analyze_file(temp_path)
        result.setdefault("file_info", {})
        result["file_info"]["original_filename"] = file.filename

        return result

    except Exception as exc:
        logger.exception("Error processing STEP file")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc)
        )

    finally:
        cleanup_temp_file(temp_path)

# ------------------------------------------------------------------------------
# Geometry Only
# ------------------------------------------------------------------------------
@app.post("/analyze/geometry")
async def analyze_geometry_only(file: UploadFile = File(...)) -> Dict[str, Any]:
    ext = validate_step_file(file.filename)
    content = await file.read()
    temp_path = None

    try:
        temp_path = save_temp_file(content, ext)
        return processor.get_geometric_properties(temp_path)

    except Exception as exc:
        logger.exception("Error processing geometry")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc)
        )

    finally:
        cleanup_temp_file(temp_path)

# ------------------------------------------------------------------------------
# Topology Only
# ------------------------------------------------------------------------------
@app.post("/analyze/topology")
async def analyze_topology_only(file: UploadFile = File(...)) -> Dict[str, Any]:
    ext = validate_step_file(file.filename)
    content = await file.read()
    temp_path = None

    try:
        temp_path = save_temp_file(content, ext)
        return processor.get_topology_info(temp_path)

    except Exception as exc:
        logger.exception("Error processing topology")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc)
        )

    finally:
        cleanup_temp_file(temp_path)

# ------------------------------------------------------------------------------
# Validation Only
# ------------------------------------------------------------------------------
@app.post("/validate")
async def validate_step_file_endpoint(file: UploadFile = File(...)) -> Dict[str, Any]:
    ext = validate_step_file(file.filename)
    content = await file.read()
    temp_path = None

    try:
        temp_path = save_temp_file(content, ext)
        return processor.validate_file(temp_path)

    except Exception as exc:
        logger.exception("Error validating STEP file")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc)
        )

    finally:
        cleanup_temp_file(temp_path)
