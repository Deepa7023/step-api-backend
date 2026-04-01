import os
import uuid
import time
import json
import base64
import threading
from typing import Dict, Any

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

def now() -> float:
    return time.time()

def job_dir(jid: str) -> str:
    p = os.path.join(JOBS_DIR, jid)
    os.makedirs(p, exist_ok=True)
    return p

def status_path(jid: str) -> str:
    return os.path.join(job_dir(jid), "status.json")

def result_path(jid: str) -> str:
    return os.path.join(job_dir(jid), "result.json")

def step_path(jid: str, name: str) -> str:
    return os.path.join(job_dir(jid), os.path.basename(name))

def write_json(p: str, d: dict) -> None:
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)

def read_json(p: str):
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def set_status(jid: str, status: str, extra: dict | None = None) -> None:
    data = {"status": status, "updated_at": now()}
    if extra:
        data.update(extra)
    write_json(status_path(jid), data)

# ----------------- request model -----------------

class Base64Payload(BaseModel):
    filename: str
    content_base64: str

# ----------------- OCP helper: robust bbox add -----------------
def add_shape_to_bbox(shape, bbox) -> None:
    """
    Robust wrapper for OCCT BRepBndLib::Add across different OCP bindings.
    OCCT canonical API is BRepBndLib::Add(shape, box, useTriangulation). [1](https://dev.opencascade.org/project/build123d)
    Some Python wrappers expose this as brepbndlib.Add(...). [2](https://build123d.readthedocs.io/en/latest/import_export.html)
    """
    # Variant 1: class BRepBndLib with static Add
    try:
        from OCP.BRepBndLib import BRepBndLib
        BRepBndLib.Add(shape, bbox, True)
        return
    except Exception:
        pass

    # Variant 2: pythonocc-style wrapper class 'brepbndlib' with method Add
    try:
        from OCP.BRepBndLib import brepbndlib
        brepbndlib.Add(shape, bbox, True)
        return
    except Exception:
        pass

    # Variant 3: pythonocc free function name
    try:
        from OCP.BRepBndLib import brepbndlib_Add
        brepbndlib_Add(shape, bbox, True)
        return
    except Exception:
        pass

    # Variant 4: module-level Add (some builds expose this)
    try:
        from OCP.BRepBndLib import Add
        Add(shape, bbox, True)
        return
    except Exception as e:
        raise RuntimeError(f"No compatible BRepBndLib Add symbol found in this OCP build: {e}")

# ----------------- STEP ANALYSIS -----------------

def analyze_step_file(step_file: str) -> Dict[str, Any]:
    try:
        from OCP.STEPControl import STEPControl_Reader
        from OCP.IFSelect import IFSelect_RetDone
        from OCP.Bnd import Bnd_Box
        from OCP.BRepGProp import BRepGProp
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
    add_shape_to_bbox(shape, bbox)
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

def process_job(jid: str, step_file: str) -> None:
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
        from OCP.STEPControl import STEPControl_Reader  # noqa: F401
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
