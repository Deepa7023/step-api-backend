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

app = FastAPI(title="STEP Analyzer API", version="FINAL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS_DIR = "jobs"
os.makedirs(JOBS_DIR, exist_ok=True)

# ----------------- helpers -----------------

def now():
    return time.time()

def job_dir(jid):
    p = os.path.join(JOBS_DIR, jid)
    os.makedirs(p, exist_ok=True)
    return p

def status_path(jid):
    return os.path.join(job_dir(jid), "status.json")

def result_path(jid):
    return os.path.join(job_dir(jid), "result.json")

def step_path(jid, name):
    return os.path.join(job_dir(jid), os.path.basename(name))

def write_json(p, d):
    with open(p, "w") as f:
        json.dump(d, f)

def read_json(p):
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)

def set_status(jid, status, extra=None):
    data = {"status": status, "updated_at": now()}
    if extra:
        data.update(extra)
    write_json(status_path(jid), data)

# ----------------- request model -----------------

class Base64Payload(BaseModel):
    filename: str
    content_base64: str

# ----------------- STEP ANALYSIS (CORRECT OCP USAGE) -----------------

def analyze_step_file(step_file: str) -> Dict[str, Any]:
    try:
        from OCP.STEPControl import STEPControl_Reader
        from OCP.IFSelect import IFSelect_RetDone
        from OCP.Bnd import Bnd_Box
        from OCP.BRepBndLib import Add            # ✅ CORRECT
        from OCP.BRepGProp import BRepGProp       # ✅ CORRECT
        from OCP.GProp import GProp_GProps
        from OCP.BRepMesh import BRepMesh_IncrementalMesh
    except Exception as e:
        raise RuntimeError(f"OCP import failed: {e}")

    reader = STEPControl_Reader()
    if reader.ReadFile(step_file) != IFSelect_RetDone:
        raise RuntimeError("Invalid STEP file")

    if reader.TransferRoots() == 0:
        raise RuntimeError("No transferable STEP shapes")

    shape = reader.OneShape()

    try:
        BRepMesh_IncrementalMesh(shape, 0.5)
    except Exception:
        pass

    # ---------- Bounding Box ----------
    bbox = Bnd_Box()
    bbox.SetGap(0.0)
    Add(shape, bbox, True)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()

    # ---------- Volume ----------
    vol_props = GProp_GProps()
    BRepGProp.VolumeProperties(shape, vol_props, False, False, False)

    # ---------- Surface ----------
    surf_props = GProp_GProps()
    BRepGProp.SurfaceProperties(shape, surf_props, False, False)

    return {
        "bbox_L_mm": round(xmax - xmin, 3),
        "bbox_W_mm": round(ymax - ymin, 3),
        "bbox_H_mm": round(zmax - zmin, 3),
        "volume_cm3": round(vol_props.Mass() / 1000.0, 6),
        "surface_area_cm2": round(surf_props.Mass() / 100.0, 6),
    }

# ----------------- background worker -----------------

def process_job(jid, step_file):
    try:
        set_status(jid, "processing")
        result = analyze_step_file(step_file)
        write_json(result_path(jid), result)
        set_status(jid, "done")
    except Exception as e:
        set_status(jid, "error", {"error": str(e)})

# ----------------- API -----------------

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/debug_ocp")
def debug_ocp():
    try:
        from OCP.STEPControl import STEPControl_Reader
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/submit_base64")
def submit_base64(req: Base64Payload):
    jid = str(uuid.uuid4())
    p = step_path(jid, req.filename)

    try:
        raw = base64.b64decode(req.content_base64, validate=True)
    except Exception:
        raise HTTPException(400, "Invalid base64")

    with open(p, "wb") as f:
        f.write(raw)

    set_status(jid, "submitted")
    threading.Thread(target=process_job, args=(jid, p), daemon=True).start()
    return {"job_id": jid, "status": "submitted"}

@app.get("/result/{job_id}")
def result(job_id: str):
    st = read_json(status_path(job_id))
    if not st:
        return {"status": "processing"}
    if st["status"] == "done":
        return {"status": "done", "result": read_json(result_path(job_id))}
    if st["status"] == "error":
        return st
    return {"status": st["status"]}
