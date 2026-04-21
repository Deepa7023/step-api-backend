"""
STEP File Analysis API
Production-grade FastAPI backend for STEP file analysis
with clear, precise, HPDC-ready output.
"""

import os
import tempfile
import logging
from typing import Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware

from .step_processor import STEPProcessor


# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
MAX_FILE_SIZE_MB = 50
SUPPORTED_EXTENSIONS = {".step", ".stp"}

DEFAULT_ALLOY = "AlSi9Cu3"
ALLOY_DENSITIES = {
    "AlSi9Cu3": 2.70,
    "ADC12": 2.74,
    "A380": 2.75
}


# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("step-api")


# ------------------------------------------------------------------------------
# FastAPI App
# ------------------------------------------------------------------------------
app = FastAPI(
    title="STEP File Analysis API",
    description="Analyze STEP CAD files and return HPDC-ready summaries",
    version="2.1.0"
)


# ------------------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


# ------------------------------------------------------------------------------
# STEP Processor
# ------------------------------------------------------------------------------
processor = STEPProcessor()


# ------------------------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------------------------
def validate_step_file(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing."
        )

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Only STEP/STP files are allowed."
        )

    return ext


def enforce_file_size(file: UploadFile) -> None:
    file.file.seek(0, os.SEEK_END)
    size_mb = file.file.tell() / (1024 * 1024)
    file.file.seek(0)

    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {MAX_FILE_SIZE_MB} MB limit."
        )


def save_temp_file(file: UploadFile, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        return tmp.name


def cleanup_temp_file(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.unlink(path)
    except Exception as exc:
        logger.warning("Failed to clean temp file: %s", exc)


# ------------------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Incoming request: %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("Response status: %s", response.status_code)
    return response


# ------------------------------------------------------------------------------
# Health Endpoints
# ------------------------------------------------------------------------------
@app.get("/", status_code=status.HTTP_200_OK)
async def root() -> Dict[str, str]:
    return {
        "service": "STEP File Analysis API",
        "status": "healthy",
        "version": "2.1.0"
    }


@app.get("/health", status_code=status.HTTP_200_OK)
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "occt_available": processor.is_available(),
        "supported_formats": list(SUPPORTED_EXTENSIONS)
    }


# ------------------------------------------------------------------------------
# STEP Analysis Endpoint
# ------------------------------------------------------------------------------
@app.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_step(file: UploadFile = File(...)) -> Dict[str, Any]:
    ext = validate_step_file(file)
    enforce_file_size(file)

    temp_path = None

    try:
        temp_path = save_temp_file(file, ext)
        logger.info("Processing STEP file: %s", file.filename)

        raw = processor.analyze_file(temp_path)

        volume_mm3 = raw["geometry"]["volume_mm3"]
        volume_cm3 = round(volume_mm3 / 1000.0, 2)

        surface_area_cm2 = round(
            raw["geometry"]["surface_area_mm2"] / 100.0, 2
        )

        bounding_box_mm = {
            "x": round(raw["geometry"]["bounding_box_mm"]["x"], 2),
            "y": round(raw["geometry"]["bounding_box_mm"]["y"], 2),
            "z": round(raw["geometry"]["bounding_box_mm"]["z"], 2),
        }

        alloy = DEFAULT_ALLOY
        density_g_cm3 = ALLOY_DENSITIES[alloy]
        weight_kg = round((volume_cm3 * density_g_cm3) / 1000.0, 2)

        projected_area_cm2 = round(surface_area_cm2 * 0.85, 1)
        estimated_tonnage_tons = int(projected_area_cm2 * 1.10)

        faces = raw["topology"]["faces"]
        complexity_class = (
            "Low" if faces < 300
            else "Medium" if faces < 800
            else "High"
        )

        suitable_for_hpdc = estimated_tonnage_tons <= 2000

        response = {
            "file": {
                "name": file.filename,
                "format": "STEP",
                "valid": True
            },
            "geometry": {
                "volume_mm3": round(volume_mm3, 1),
                "volume_cm3": volume_cm3,
                "surface_area_cm2": surface_area_cm2,
                "bounding_box_mm": bounding_box_mm
            },
            "mass_estimate": {
                "alloy": alloy,
                "density_g_cm3": density_g_cm3,
                "weight_kg": weight_kg
            },
            "hpdc_summary": {
                "projected_area_cm2": projected_area_cm2,
                "estimated_tonnage_tons": estimated_tonnage_tons,
                "complexity_class": complexity_class,
                "suitable_for_hpdc": suitable_for_hpdc
            },
            "topology": {
                "solids": raw["topology"]["solids"],
                "faces": faces,
                "edges": raw["topology"]["edges"]
            },
            "confidence": {
                "geometry_confidence": "High",
                "hpdc_estimation_confidence": "Medium"
            }
        }

        return response

    except HTTPException:
        raise

    except Exception:
        logger.exception("STEP analysis failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze STEP file."
        )

    finally:
        cleanup_temp_file(temp_path)
