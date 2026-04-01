\import os
import uuid
import time
import json
import base64
import threading
from typing import Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# =========================================================
# FastAPI App
# =========================================================
app = FastAPI(title="STEP Analyzer API (Async Safe for Copilot)", version="2.0")

# CORS (keep permissive while testing; tighten later if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# Job storage (Render Free: ephemeral, but fine for short jobs)
# =========================================================
JOBS_DIR = os.getenv("JOBS_DIR", "jobs")
os.makedirs(JOBS_DIR, exist_ok=True)

# Optional: TTL cleanup (seconds)
JOB_TTL_SECONDS = int(os.getenv("JOB_TTL_SECONDS", "3600"))  # 1 hour default


def _job_dir(job_id: str) -> str:
    d = os.path.join(JOBS_DIR, job_id)
    os.makedirs(d, exist_ok=True)
    return d


def _write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def _read_json(path: str) -> Optional[dict]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _now() -> float:
    return time.time()


def _status_path(job_id: str) -> str:
    return os.path.join(_job_dir(job_id), "status.json")


def _result_path(job_id: str) -> str:
    return os.path.join(_job_dir(job_id), "result.json")


def _input_step_path(job_id: str, filename: str) -> str:
    safe = filename or "uploaded.step"
    # avoid path traversal
    safe = os.path.basename(safe)
    return os.path.join(_job_dir(job_id), safe)


def _set_status(job_id: str, status: str, extra: Optional[dict] = None) -> None:
    payload = {"status": status, "updated_at": _now()}
    if extra:
        payload.update(extra)
    _write_json(_status_path(job_id), payload)


def _cleanup_old_jobs() -> None:
    """Best-effort cleanup; safe on free tier."""
    try:
        for job_id in os.listdir(JOBS_DIR):
            d = os.path.join(JOBS_DIR, job_id)
            if not os.path.isdir(d):
                continue
            st = _read_json(os.path.join(d, "status.json"))
            if not st:
                continue
            updated = st.get("updated_at", 0)
            if _now() - float(updated) > JOB_TTL_SECONDS:
                # remove directory contents
                for root, dirs, files in os.walk(d, topdown=False):
                    for name in files:
                        try:
                            os.remove(os.path.join(root, name))
                        except Exception:
                            pass
                    for name in dirs:
                        try:
                            os.rmdir(os.path.join(root, name))
                        except Exception:
                            pass
                try:
                    os.rmdir(d)
                except Exception:
                    pass
    except Exception:
        pass


# =========================================================
# Request Models
# =========================================================
class AnalyzeBase64Request(BaseModel):
    filename: str
    content_base64: str


class SubmitBase64Request(BaseModel):
    filename: str
    content_base64: str


# =========================================================
# STEP Analysis Core (OCP / OpenCascade)
# =========================================================
def analyze_step_file(step_path: str) -> Dict[str, Any]:
    """
    Returns:
      bbox_L_mm, bbox_W_mm, bbox_H_mm  (mm)
      volume_cm3 (cm^3)
      surface_area_cm2 (cm^2)
    Notes:
      - STEP model units can vary. This assumes model units are millimeters.
      - If your files are in meters, you must scale results accordingly.
    """
    try:
        # OCP imports inside function to avoid import error crashing /health
        from OCP.STEPControl import STEPControl_Reader
        from OCP.IFSelect import IFSelect_RetDone
        from OCP.BRepBndLib import brepbndlib_Add
        from OCP.Bnd import Bnd_Box
        from OCP.BRepGProp import brepgprop_VolumeProperties, brepgprop_SurfaceProperties
        from OCP.GProp import GProp_GProps
        from OCP.BRepMesh import BRepMesh_IncrementalMesh

    except Exception as e:
        raise RuntimeError(
            "OCP/OpenCascade not available. Ensure 'OCP' is installed in requirements."
        ) from e

    # Read STEP
    reader = STEPControl_Reader()
    status = reader.ReadFile(step_path)
    if status != IFSelect_RetDone:
        raise RuntimeError("Failed to read STEP file.")

    ok = reader.TransferRoots()
    if ok == 0:
        raise RuntimeError("STEP transfer roots failed.")

    shape = reader.OneShape()

    # Mesh (helps surface props accuracy for some shapes)
    try:
        # deflection value might need tuning; smaller = more accurate, slower
        BRepMesh_IncrementalMesh(shape, 0.5)
    except Exception:
        pass

    # Bounding box
    bbox = Bnd_Box()
    bbox.SetGap(0.0)
    brepbndlib_Add(shape, bbox)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()

    L = float(xmax - xmin)
    W = float(ymax - ymin)
    H = float(zmax - zmin)

    # Volume / surface area (units depend on model; assuming mm)
    props_vol = GProp_GProps()
    brepgprop_VolumeProperties(shape, props_vol)
    volume_mm3 = float(props_vol.Mass())  # "Mass" gives volume for volume props

    props_surf = GProp_GProps()
    brepgprop_SurfaceProperties(shape, props_surf)
    area_mm2 = float(props_surf.Mass())   # "Mass" gives area for surface props

    # Convert to requested units
    volume_cm3 = volume_mm3 / 1000.0   # 1 cm^3 = 1000 mm^3
    area_cm2 = area_mm2 / 100.0        # 1 cm^2 = 100 mm^2

    return {
        "bbox_L_mm": round(L, 3),
        "bbox_W_mm": round(W, 3),
        "bbox_H_mm": round(H, 3),
        "volume_cm3": round(volume_cm3, 6),
        "surface_area_cm2": round(area_cm2, 6),
    }


# =========================================================
# Background Worker (Async jobs)
# =========================================================
def _process_job(job_id: str, step_path: str) -> None:
    try:
        _set_status(job_id, "processing")
        result = analyze_step_file(step_path)
        _write_json(_result_path(job_id), result)
        _set_status(job_id, "done")
    except Exception as e:
        _set_status(job_id, "error", {"error": str(e)})


# =========================================================
# Health endpoint
# =========================================================
@app.get("/health")
def health():
    # optional cleanup every health call (very light)
    _cleanup_old_jobs()
    return {"status": "ok", "time": _now()}


# =========================================================
# SYNC endpoints (still available)
# =========================================================
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    step_path = _input_step_path(job_id, file.filename)
    data = await file.read()
    with open(step_path, "wb") as f:
        f.write(data)

    try:
        result = analyze_step_file(step_path)
        return {"status": "done", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze_base64")
def analyze_base64(req: AnalyzeBase64Request):
    job_id = str(uuid.uuid4())
    step_path = _input_step_path(job_id, req.filename)

    try:
        data = base64.b64decode(req.content_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 content")

    with open(step_path, "wb") as f:
        f.write(data)

    try:
        result = analyze_step_file(step_path)
        return {"status": "done", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
# ASYNC endpoints (for Copilot Free tier)
# =========================================================
@app.post("/submit_base64")
def submit_base64(req: SubmitBase64Request):
    """
    FAST endpoint:
      - saves the file
      - starts background analysis
      - returns job_id immediately (< 2 sec)
    """
    job_id = str(uuid.uuid4())
    step_path = _input_step_path(job_id, req.filename)

    try:
        data = base64.b64decode(req.content_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 content")

    # Save file
    with open(step_path, "wb") as f:
        f.write(data)

    # Mark submitted and start thread
    _set_status(job_id, "submitted")
    t = threading.Thread(target=_process_job, args=(job_id, step_path), daemon=True)
    t.start()

    return {"job_id": job_id, "status": "submitted"}


@app.get("/result/{job_id}")
def get_result(job_id: str):
    """
    FAST polling endpoint:
      Returns:
        {status: processing}
        {status: done, result: {...}}
        {status: error, error: "..."}
    """
    d = os.path.join(JOBS_DIR, job_id)
    if not os.path.exists(d):
        raise HTTPException(status_code=404, detail="job_id not found")

    status = _read_json(os.path.join(d, "status.json"))
    if not status:
        return {"status": "processing"}

    st = status.get("status", "processing")

    if st == "done":
        result = _read_json(os.path.join(d, "result.json")) or {}
        return {"status": "done", "result": result}

    if st == "error":
        return {"status": "error", "error": status.get("error", "unknown")}

    # submitted / processing
    return {"status": "processing"}
