import os
import uuid
import time
import json
import base64
import threading
from typing import Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# -----------------------------
# App
# -----------------------------
app = FastAPI(title="STEP Analyzer API (Async Safe for Copilot)", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Job storage (ephemeral on Render Free)
# -----------------------------
JOBS_DIR = os.getenv("JOBS_DIR", "jobs")
os.makedirs(JOBS_DIR, exist_ok=True)

JOB_TTL_SECONDS = int(os.getenv("JOB_TTL_SECONDS", "3600"))  # 1 hour


def now_ts() -> float:
    return time.time()


def job_dir(job_id: str) -> str:
    d = os.path.join(JOBS_DIR, job_id)
    os.makedirs(d, exist_ok=True)
    return d


def status_path(job_id: str) -> str:
    return os.path.join(job_dir(job_id), "status.json")


def result_path(job_id: str) -> str:
    return os.path.join(job_dir(job_id), "result.json")


def safe_step_path(job_id: str, filename: str) -> str:
    name = filename or "uploaded.step"
    name = os.path.basename(name)  # prevent traversal
    return os.path.join(job_dir(job_id), name)


def write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def read_json(path: str) -> Optional[dict]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def set_status(job_id: str, status: str, extra: Optional[dict] = None) -> None:
    payload = {"status": status, "updated_at": now_ts()}
    if extra:
        payload.update(extra)
    write_json(status_path(job_id), payload)


def cleanup_old_jobs() -> None:
    """Best-effort cleanup (safe for Render Free)."""
    try:
        for jid in os.listdir(JOBS_DIR):
            d = os.path.join(JOBS_DIR, jid)
            if not os.path.isdir(d):
                continue
            st = read_json(os.path.join(d, "status.json"))
            if not st:
                continue
            updated_at = float(st.get("updated_at", 0))
            if now_ts() - updated_at > JOB_TTL_SECONDS:
                # delete folder content
                for root, dirs, files in os.walk(d, topdown=False):
                    for fn in files:
                        try:
                            os.remove(os.path.join(root, fn))
                        except Exception:
                            pass
                    for dn in dirs:
                        try:
                            os.rmdir(os.path.join(root, dn))
                        except Exception:
                            pass
                try:
                    os.rmdir(d)
                except Exception:
                    pass
    except Exception:
        pass


# -----------------------------
# Request models
# -----------------------------
class Base64Payload(BaseModel):
    filename: str
    content_base64: str


# -----------------------------
# STEP analysis (OCP/OpenCascade)
# -----------------------------
def analyze_step_file(step_path: str) -> Dict[str, Any]:
    """
    Returns:
      bbox_L_mm, bbox_W_mm, bbox_H_mm  (mm)
      volume_cm3 (cm^3)
      surface_area_cm2 (cm^2)

    Assumption: STEP units are mm (common). If your STEP is in meters,
    you must scale the results in your workflow.
    """
    try:
        from OCP.STEPControl import STEPControl_Reader
        from OCP.IFSelect import IFSelect_RetDone
        from OCP.BRepBndLib import brepbndlib_Add
        from OCP.Bnd import Bnd_Box
        from OCP.BRepGProp import brepgprop_VolumeProperties, brepgprop_SurfaceProperties
        from OCP.GProp import GProp_GProps
        from OCP.BRepMesh import BRepMesh_IncrementalMesh
    except Exception as e:
        raise RuntimeError(
            "OCP/OpenCascade not available. Ensure requirements.txt includes OCP."
        ) from e

    reader = STEPControl_Reader()
    status = reader.ReadFile(step_path)
    if status != IFSelect_RetDone:
        raise RuntimeError("Failed to read STEP file")

    transferred = reader.TransferRoots()
    if transferred == 0:
        raise RuntimeError("STEP transfer roots failed")

    shape = reader.OneShape()

    # optional mesh to improve properties for some geometry
    try:
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

    # Volume and area (assuming mm units)
    props_vol = GProp_GProps()
    brepgprop_VolumeProperties(shape, props_vol)
    volume_mm3 = float(props_vol.Mass())

    props_surf = GProp_GProps()
    brepgprop_SurfaceProperties(shape, props_surf)
    area_mm2 = float(props_surf.Mass())

    # Convert to cm3, cm2
    volume_cm3 = volume_mm3 / 1000.0
    area_cm2 = area_mm2 / 100.0

    return {
        "bbox_L_mm": round(L, 3),
        "bbox_W_mm": round(W, 3),
        "bbox_H_mm": round(H, 3),
        "volume_cm3": round(volume_cm3, 6),
        "surface_area_cm2": round(area_cm2, 6),
    }


# -----------------------------
# Background worker
# -----------------------------
def process_job(job_id: str, step_path: str) -> None:
    try:
        set_status(job_id, "processing")
        result = analyze_step_file(step_path)
        write_json(result_path(job_id), result)
        set_status(job_id, "done")
    except Exception as e:
        set_status(job_id, "error", {"error": str(e)})


# -----------------------------
# Routes
# -----------------------------
@app.get("/health")
def health():
    cleanup_old_jobs()
    return {"status": "ok", "time": now_ts()}


# --- Sync endpoints (optional) ---
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    path = safe_step_path(job_id, file.filename)
    data = await file.read()
    with open(path, "wb") as f:
        f.write(data)

    try:
        result = analyze_step_file(path)
        return {"status": "done", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze_base64")
def analyze_base64(req: Base64Payload):
    job_id = str(uuid.uuid4())
    path = safe_step_path(job_id, req.filename)

    try:
        data = base64.b64decode(req.content_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 content")

    with open(path, "wb") as f:
        f.write(data)

    try:
        result = analyze_step_file(path)
        return {"status": "done", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Async endpoints (USE THESE IN COPILOT FLOW) ---
@app.post("/submit_base64")
def submit_base64(req: Base64Payload):
    """
    FAST: save file + start background thread + return job_id immediately
    """
    job_id = str(uuid.uuid4())
    path = safe_step_path(job_id, req.filename)

    try:
        data = base64.b64decode(req.content_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 content")

    with open(path, "wb") as f:
        f.write(data)

    set_status(job_id, "submitted")

    t = threading.Thread(target=process_job, args=(job_id, path), daemon=True)
    t.start()

    return {"job_id": job_id, "status": "submitted"}


@app.get("/result/{job_id}")
def get_result(job_id: str):
    """
    FAST polling:
      {status: processing}
      {status: done, result: {...}}
      {status: error, error: "..."}
    """
    d = os.path.join(JOBS_DIR, job_id)
    if not os.path.exists(d):
        raise HTTPException(status_code=404, detail="job_id not found")

    st = read_json(os.path.join(d, "status.json"))
    if not st:
        return {"status": "processing"}

    status = st.get("status", "processing")

    if status == "done":
        res = read_json(os.path.join(d, "result.json")) or {}
        return {"status": "done", "result": res}

    if status == "error":
        return {"status": "error", "error": st.get("error", "unknown")}

    return {"status": "processing"}
