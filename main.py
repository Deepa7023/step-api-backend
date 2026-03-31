import os, json, uuid, time, base64, binascii
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel

app = FastAPI()

JOB_DIR = Path(os.environ.get("JOB_DIR", "/tmp/step_jobs"))
JOB_DIR.mkdir(parents=True, exist_ok=True)

class AnalyzeSubmitRequest(BaseModel):
    filename: str
    content_b64: str

def _normalize_b64(b64: str) -> str:
    s = (b64 or "").strip()
    if s.lower().startswith("data:") and "," in s:
        s = s.split(",", 1)[1]
    s = "".join(s.split())
    pad = len(s) % 4
    if pad:
        s += "=" * (4 - pad)
    return s

def _decode_b64(b64: str) -> bytes:
    s = _normalize_b64(b64)
    try:
        return base64.b64decode(s, validate=True)
    except (binascii.Error, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"content_b64 is not valid base64: {e}")

def _job_path(job_id: str) -> Path:
    return JOB_DIR / f"{job_id}.json"

def _write_job(job_id: str, payload: Dict[str, Any]) -> None:
    _job_path(job_id).write_text(json.dumps(payload), encoding="utf-8")

def _read_job(job_id: str) -> Optional[Dict[str, Any]]:
    p = _job_path(job_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

def analyze_step_bytes(step_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    TODO: Paste your existing OCCT/OpenCascade analysis here.
    It must return the same structure as /analyze_base64 returns.
    """
    raise NotImplementedError("Implement using your existing OCCT code")

def _process_job(job_id: str, req: AnalyzeSubmitRequest) -> None:
    try:
        _write_job(job_id, {"status": "processing", "updated_utc": time.time()})

        step_bytes = _decode_b64(req.content_b64)

        head = step_bytes.lstrip()[:200]
        if b"ISO-10303-21" not in head:
            _write_job(job_id, {"status": "failed", "error": "Not a STEP file (missing ISO-10303-21)", "updated_utc": time.time()})
            return

        data = analyze_step_bytes(step_bytes, req.filename)
        _write_job(job_id, {"status": "done", "data": data, "updated_utc": time.time()})

    except Exception as e:
        _write_job(job_id, {"status": "failed", "error": str(e), "updated_utc": time.time()})

@app.post("/analyze_base64_submit", status_code=202)
async def analyze_base64_submit(req: AnalyzeSubmitRequest, background_tasks: BackgroundTasks):
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
``
