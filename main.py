# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
import base64

# ---- OpenCascade via OCP (cadquery-ocp) ----
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib            # static methods have _s suffix in OCP
from OCP.BRepGProp import BRepGProp              # static methods have _s suffix in OCP
from OCP.GProp import GProp_GProps

app = FastAPI(title="STEP Geometry API", version="1.0")


# --------------------------
# Core OCCT helper routines
# --------------------------
def read_step_shape(path: str):
    """Read a STEP file and return a TopoDS_Shape."""
    reader = STEPControl_Reader()
    status = reader.ReadFile(path)
    if status != IFSelect_RetDone:
        raise ValueError("Failed to read STEP file (IFSelect_RetDone not returned).")
    if not reader.TransferRoots():
        raise ValueError("STEP transfer failed.")
    # OneShape() returns the unified shape of all transferred roots
    return reader.OneShape()


def compute_bbox(shape):
    """Compute axis-aligned bounding box in mm using OCCT."""
    bbox = Bnd_Box()
    bbox.SetGap(0.0)  # avoid tolerance enlargement
    # In OCP, static OCCT methods are exposed with the `_s` suffix.
    BRepBndLib.Add_s(shape, bbox, True)  # useTriangulation=True
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    return {
        "xmin": xmin, "ymin": ymin, "zmin": zmin,
        "xmax": xmax, "ymax": ymax, "zmax": zmax,
        "length_mm": xmax - xmin,
        "width_mm":  ymax - ymin,
