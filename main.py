import os
import json
import uuid
import time
import base64
import binascii
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Folder to store job status/results (survives while container is running)
JOB_DIR = Path(os.environ.get("JOB_DIR", "/tmp/step_jobs"))
JOB_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Request model for submit API
# -----------------------------
class AnalyzeSubmitRequest(BaseModel):
    filename: str
    content_b64: str


def _normalize_b64(b64: str) -> str:
    """Remove data:...base64, prefix, whitespace, and fix padding."""
    s = (b64 or "").strip()
    if s.lower().startswith("data:") and "," in s:
        s = s.split(",", 1)[1]
    s = "".join(s.split())
    pad = len(s) % 4
    if pad != 0:
        s += "=" * (4 - pad)
    return s


def _decode_b64_to_bytes(b64: str) -> bytes:
    s = _normalize_b64(b64)
    try:
        return base64.b64decode(s, validate=True)
    except (binascii.Error, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"content_b64 is not valid base64: {str(e)}")


def _write_job(job_id: str, payload: Dict[str, Any]) -> None:
    (JOB_DIR / f"{job_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def _read_job(job_id: str) -> Optional[Dict[str, Any]]:
    p = JOB_DIR / f"{job_id}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


# -----------------------------
# IMPORTANT: plug your existing STEP analysis here
# -----------------------------
def analyze_step_bytes(step_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Reuse your existing /analyze_base64 logic here.
    It should return the SAME JSON structure you already return today:
    {
      "file": "...",
      "bounding_box_mm": {...},
      "solid_volume": {"mm3":..., "m3":...},
      "surface_area": {"mm2":..., "m2":...},
      "units": {...}
    }
    """
    # ✅ OPTION 1: If you already have a helper function that reads a temp file, use it:
    #   - write bytes to temp .stp
    #   - call your existing OpenCascade read/compute functions
    #
    # Replace the next line with your real implementation:
    raise NotImplementedError("Replace analyze_step_bytes() with your existing OCCT code.")


def _process_job(job_id: str, req: AnalyzeSubmitRequest) -> None:
    """Runs after submit returns 202. Writes status/result to JOB_DIR."""
    try:
        # Update status to processing
        _write_job(job_id, {"status": "processing", "updated_utc": time.time()})

        # Decode base64 and analyze STEP
        step_bytes = _decode_b64_to_bytes(req.content_b64)

        # Optional quick signature check (STEP Part 21 files contain ISO-10303-21 near the top)
        head = step_bytes.lstrip()[:200]
        if b"ISO-10303-21" not in head:
            raise HTTPException(
                status_code=400,
                detail="Decoded bytes do not look like a STEP Part 21 file (missing 'ISO-10303-21')."
            )

        data = analyze_step_bytes(step_bytes, req.filename)

        # Save result
        _write_job(job_id, {"status": "done", "data": data, "updated_utc": time.time()})

    except HTTPException as he:
        _write_job(job_id, {"status": "failed", "error": he.detail, "updated_utc": time.time()})
    except Exception as e:
        _write_job(job_id, {"status": "failed", "error": str(e), "updated_utc": time.time()})


@app.post("/analyze_base64_submit", status_code=202)
async def analyze_base64_submit(req: AnalyzeSubmitRequest, background_tasks: BackgroundTasks):
    """
    Returns immediately with job_id, then processes the STEP in background.
    FastAPI BackgroundTasks are designed to run after returning a response. [1](https://fastapi.tiangolo.com/tutorial/background-tasks/)[2](https://github.com/fastapi/fastapi/blob/master/docs/en/docs/tutorial/background-tasks.md)
    """
    if not req.filename.lower().endswith((".stp", ".step")):
        raise HTTPException(status_code=400, detail="filename must end with .stp or .step")

    job_id = str(uuid.uuid4())
    _write_job(job_id, {"status": "queued", "updated_utc": time.time()})

    # Run heavy processing after response
    background_tasks.add_task(_process_job, job_id, req)

    return {"job_id": job_id}


@app.get("/analyze_result/{job_id}")
async def analyze_result(job_id: str):
    """
    Poll this endpoint until status becomes done/failed.
    """
    job = _read_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_id not found")
    return job
``
