import os
import json
import uuid
import time
import base64
import binascii
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# ----------------------------
# OpenCascade (OCP) imports
# ----------------------------
OCP_AVAILABLE = True
try:
    from OCP.STEPControl import STEPControl_Reader
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
except Exception:
    OCP_AVAILABLE = False


app = FastAPI(title="STEP Geometry API", version="3.0")

# ----------------------------
# Config
# ----------------------------
JOB_DIR = Path(os.environ.get("JOB_DIR", "/tmp/step_jobs"))
JOB_DIR.mkdir(parents=True, exist_ok=True)

MAX_DECODED_BYTES = int(os.environ.get("MAX_STEP_BYTES", str(80 * 1024 * 1024)))  # 80MB default


# ----------------------------
# Models
# ----------------------------
class AnalyzeBase64Request(BaseModel):
    filename: str
    # IMPORTANT: allow string OR dict/record (Copilot may send a file record)
    content_b64: Any


# ----------------------------
# Health & root
# ----------------------------
@app.get("/")
def root():
    return {"service": "step-api-backend", "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok"}


# ----------------------------
# Job storage helpers
# ----------------------------
def _job_path(job_id: str) -> Path:
    return JOB_DIR / f"{job_id}.json"

def _write_job(job_id: str, payload: Dict[str, Any]) -> None:
    _job_path(job_id).write_text(json.dumps(payload), encoding="utf-8")

def _read_job(job_id: str) -> Optional[Dict[str, Any]]:
    p = _job_path(job_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


# ----------------------------
# Base64 helpers (tolerant)
# ----------------------------
def _normalize_b64(b64: str) -> str:
    """
    - Strip data URI prefix if present
    - Remove whitespace/newlines
    - Fix missing padding
    """
    s = (b64 or "").strip()
    if s.lower().startswith("data:") and "," in s:
        s = s.split(",", 1)[1]
    s = "".join(s.split())
    pad = len(s) % 4
    if pad:
        s += "=" * (4 - pad)
    return s


def _extract_b64_maybe(obj: Any) -> str:
    """
    Accepts:
      - base64 string
      - dict with contentBytes / $content / content_b64 / content
      - stringified JSON containing those keys
    Returns the base64 string (or empty string).
    """
    if obj is None:
        return ""

    # dict/record case
    if isinstance(obj, dict):
        for k in ("content_b64", "contentBytes", "$content", "content", "data"):
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                return v
        return ""

    # string case (might be base64 or a JSON string)
    if isinstance(obj, str):
        s = obj.strip()
        if not s:
            return ""
        if s.startswith("{") and s.endswith("}"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, dict):
                    return _extract_b64_maybe(parsed)
            except Exception:
                pass
        return s

    # unknown
    return ""


def _decode_b64_to_bytes(content_b64_any: Any) -> bytes:
    raw = _extract_b64_maybe(content_b64_any)
    s = _normalize_b64(raw)
    try:
        data = base64.b64decode(s, validate=True)
    except (binascii.Error, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"content_b64 is not valid base64: {str(e)}")

    if len(data) > MAX_DECODED_BYTES:
        raise HTTPException(status_code=413, detail=f"Decoded STEP too large (max {MAX_DECODED_BYTES} bytes).")

    return data


def _basic_step_signature_check(data: bytes) -> None:
    """
    STEP Part 21 text files normally contain ISO-10303-21 near the top.
    This catches placeholder/truncated payloads early.
    """
    head = data.lstrip()[:200]
    if b"ISO-10303-21" not in head:
        raise HTTPException(
            status_code=400,
            detail="Decoded bytes do not look like a STEP Part 21 file (missing 'ISO-10303-21')."
        )


# ----------------------------
# OpenCascade geometry routines
# ----------------------------
def _ensure_ocp():
    if not OCP_AVAILABLE:
        raise HTTPException(status_code=500, detail="OpenCascade (OCP) not available in runtime environment.")

def _read_step_shape(step_path: str):
    _ensure_ocp()
    reader = STEPControl_Reader()
    status = reader.ReadFile(step_path)
    if status != IFSelect_RetDone:
        raise ValueError("Failed to read STEP file (IFSelect_RetDone not returned).")
    if not reader.TransferRoots():
        raise ValueError("STEP transfer failed (TransferRoots returned False).")
    return reader.OneShape()

def _compute_bbox_mm(shape) -> Dict[str, float]:
    bbox = Bnd_Box()
    bbox.SetGap(0.0)
    BRepBndLib.Add_s(shape, bbox, True)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    return {
        "xmin": float(xmin), "ymin": float(ymin), "zmin": float(zmin),
        "xmax": float(xmax), "ymax": float(ymax), "zmax": float(zmax),
        "length_mm": float(xmax - xmin),
        "width_mm": float(ymax - ymin),
        "height_mm": float(zmax - zmin),
    }

def _compute_volume_area(shape):
    vol_props = GProp_GProps()
    area_props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, vol_props)
    BRepGProp.SurfaceProperties_s(shape, area_props)
    return float(vol_props.Mass()), float(area_props.Mass())


def analyze_step_bytes(step_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Writes STEP bytes to a temp file, reads via OCCT, returns bbox/volume/area.
    """
    _ensure_ocp()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".step") as tmp:
            tmp.write(step_bytes)
            tmp_path = tmp.name

        shape = _read_step_shape(tmp_path)
        bbox = _compute_bbox_mm(shape)
        vol_mm3, area_mm2 = _compute_volume_area(shape)

        return {
            "file": filename,
            "bounding_box_mm": bbox,
            "solid_volume": {"mm3": vol_mm3, "m3": vol_mm3 * 1e-9},
            "surface_area": {"mm2": area_mm2, "m2": area_mm2 * 1e-6},
            "units": {"length": "mm", "area": "mm2/m2", "volume": "mm3/m3"},
        }

    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass


# ----------------------------
# Existing endpoint: upload multipart
# ----------------------------
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    name = (file.filename or "").lower()
    if not (name.endswith(".stp") or name.endswith(".step")):
        raise HTTPException(status_code=400, detail="Only .stp/.step files supported.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".step") as tmp:
            tmp_path = tmp.name
            total = 0
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_DECODED_BYTES:
                    raise HTTPException(status_code=413, detail="STEP too large.")
                tmp.write(chunk)

        shape = _read_step_shape(tmp_path)
        bbox = _compute_bbox_mm(shape)
        vol_mm3, area_mm2 = _compute_volume_area(shape)

        return JSONResponse({
            "file": file.filename,
            "bounding_box_mm": bbox,
            "solid_volume": {"mm3": vol_mm3, "m3": vol_mm3 * 1e-9},
            "surface_area": {"mm2": area_mm2, "m2": area_mm2 * 1e-6},
            "units": {"length": "mm", "area": "mm2/m2", "volume": "mm3/m3"}
        })

    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass


# ----------------------------
# Existing endpoint: base64 (sync)
# ----------------------------
@app.post("/analyze_base64")
def analyze_base64(req: AnalyzeBase64Request):
    if not req.filename.lower().endswith((".stp", ".step")):
        raise HTTPException(status_code=400, detail="filename must end with .stp or .step")

    step_bytes = _decode_b64_to_bytes(req.content_b64)
    _basic_step_signature_check(step_bytes)
    return analyze_step_bytes(step_bytes, req.filename)


# ----------------------------
# NEW: Async job submit + poll
# ----------------------------
def _process_job(job_id: str, req: AnalyzeBase64Request) -> None:
    """
    Runs after /analyze_base64_submit returns.
    BackgroundTasks is intended for "return now, work later".
    """
    try:
        _write_job(job_id, {"status": "processing", "updated_utc": time.time()})

        step_bytes = _decode_b64_to_bytes(req.content_b64)
        _basic_step_signature_check(step_bytes)

        data = analyze_step_bytes(step_bytes, req.filename)
        _write_job(job_id, {"status": "done", "data": data, "updated_utc": time.time()})

    except HTTPException as he:
        _write_job(job_id, {"status": "failed", "error": he.detail, "updated_utc": time.time()})
    except Exception as e:
        _write_job(job_id, {"status": "failed", "error": str(e), "updated_utc": time.time()})


@app.post("/analyze_base64_submit", status_code=202)
async def analyze_base64_submit(req: AnalyzeBase64Request, background_tasks: BackgroundTasks):
    """
    Returns quickly with job_id, then processes STEP in background.
    FastAPI BackgroundTasks is the official way to run tasks after returning a response. [3](https://learn.microsoft.com/en-us/answers/questions/93882/getting-the-server-didnot-receive-the-response-fro)[4](https://stackoverflow.com/questions/77174588/microsoft-power-apps-bad-gateway-error-on-app-that-was-working)
    """
    if not req.filename.lower().endswith((".stp", ".step")):
        raise HTTPException(status_code=400, detail="filename must end with .stp or .step")

    job_id = str(uuid.uuid4())
    _write_job(job_id, {"status": "queued", "updated_utc": time.time()})

    background_tasks.add_task(_process_job, job_id, req)
    return {"job_id": job_id}


@app.get("/analyze_result/{job_id}")
async def analyze_result(job_id: str):
    job = _read_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_id not found")
    return job
