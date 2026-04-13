"""
STEP File Processor using Open CASCADE Technology (OCCT)
Handles reading, analysis, and extraction of data from STEP files

UPDATED:
- Adds slider detection (heuristic, confidence + reasons)
- Adds cavity recommendation (heuristic, confidence + reasons)
"""

import logging
from typing import Dict, Any, List, Tuple
import os

try:
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import (
        brepgprop_VolumeProperties,
        brepgprop_SurfaceProperties,
        brepgprop_LinearProperties
    )
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib_Add
    from OCC.Core.BRepCheck import BRepCheck_Analyzer
    from OCC.Core.TopoDS import TopoDS_Shape
    from OCC.Extend.TopologyUtils import TopologyExplorer

    from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
    from OCC.Core.TDocStd import TDocStd_Document
    from OCC.Core.XCAFDoc import (
        XCAFDoc_DocumentTool_ShapeTool,
        XCAFDoc_DocumentTool_ColorTool,
        XCAFDoc_DocumentTool_LayerTool,
        XCAFDoc_DocumentTool_MaterialTool
    )
    from OCC.Core.TCollection import TCollection_ExtendedString
    from OCC.Core.TDF import TDF_LabelSequence

    OCCT_AVAILABLE = True
except ImportError:
    OCCT_AVAILABLE = False

logger = logging.getLogger(__name__)


class STEPProcessor:
    """Process STEP files and extract various data points"""

    def __init__(self):
        """Initialize the STEP processor"""
        if not OCCT_AVAILABLE:
            logger.warning("pythonocc-core not available. Install it for STEP processing.")
        self.occt_available = OCCT_AVAILABLE

    def is_available(self) -> bool:
        """Check if OCCT is available"""
        return self.occt_available

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Comprehensive analysis of STEP file

        Args:
            file_path: Path to STEP file

        Returns:
            Dictionary with all analysis results
        """
        if not self.occt_available:
            raise RuntimeError("pythonocc-core not installed")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read the STEP file
        shape, metadata = self._read_step_file(file_path)

        # Gather all data
        result = {
            "file_info": {
                "file_size_bytes": os.path.getsize(file_path),
                "file_path": os.path.basename(file_path)
            },
            "metadata": metadata,
            "geometry": self._extract_geometric_properties(shape),
            "topology": self._extract_topology_info(shape),
            "validation": self._validate_shape(shape),
            "assembly": self._extract_assembly_structure(file_path)
        }

        # ✅ NEW: Slider Detection (heuristic)
        result["slider_detection"] = self._detect_slider_likely(
            result.get("geometry", {}) or {},
            result.get("topology", {}) or {},
            pull_direction="Z+"
        )

        # ✅ NEW: Cavity Recommendation (heuristic)
        result["cavity_recommendation"] = self._recommend_cavity_count(
            result.get("geometry", {}) or {},
            result.get("topology", {}) or {},
            result.get("slider_detection", {}) or {}
        )

        return result

    def get_geometric_properties(self, file_path: str) -> Dict[str, Any]:
        """Extract only geometric properties"""
        shape, _ = self._read_step_file(file_path)
        return self._extract_geometric_properties(shape)

    def get_topology_info(self, file_path: str) -> Dict[str, Any]:
        """Extract only topology information"""
        shape, _ = self._read_step_file(file_path)
        return self._extract_topology_info(shape)

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate STEP file"""
        shape, _ = self._read_step_file(file_path)
        return self._validate_shape(shape)

    def _read_step_file(self, file_path: str) -> Tuple[TopoDS_Shape, Dict[str, Any]]:
        """
        Read STEP file and return shape and metadata

        Args:
            file_path: Path to STEP file

        Returns:
            Tuple of (shape, metadata)
        """
        step_reader = STEPControl_Reader()
        status = step_reader.ReadFile(file_path)

        if status != IFSelect_RetDone:
            raise ValueError(f"Failed to read STEP file: {file_path}")

        # Transfer roots
        step_reader.PrintCheckLoad(False, IFSelect_RetDone)
        nb_roots = step_reader.NbRootsForTransfer()
        step_reader.PrintCheckTransfer(False, IFSelect_RetDone)

        logger.info(f"Found {nb_roots} roots in STEP file")

        # Transfer all roots
        step_reader.TransferRoots()
        shape = step_reader.OneShape()

        # Extract basic metadata
        metadata = {
            "nb_roots": nb_roots,
            "transfer_status": "success"
        }

        return shape, metadata

    def _extract_geometric_properties(self, shape: TopoDS_Shape) -> Dict[str, Any]:
        """
        Extract geometric properties (volume, surface area, bounding box)

        Args:
            shape: TopoDS_Shape to analyze

        Returns:
            Dictionary with geometric properties
        """
        properties: Dict[str, Any] = {}

        # Volume calculation
        try:
            props = GProp_GProps()
            brepgprop_VolumeProperties(shape, props)
            volume = props.Mass()
            center_of_mass = props.CentreOfMass()

            properties["volume"] = {"value": volume, "unit": "cubic_units"}
            properties["center_of_mass"] = {
                "x": center_of_mass.X(),
                "y": center_of_mass.Y(),
                "z": center_of_mass.Z()
            }
        except Exception as e:
            logger.warning(f"Could not calculate volume: {e}")
            properties["volume"] = None

        # Surface area calculation
        try:
            props = GProp_GProps()
            brepgprop_SurfaceProperties(shape, props)
            surface_area = props.Mass()

            properties["surface_area"] = {"value": surface_area, "unit": "square_units"}
        except Exception as e:
            logger.warning(f"Could not calculate surface area: {e}")
            properties["surface_area"] = None

        # Bounding box
        try:
            bbox = Bnd_Box()
            brepbndlib_Add(shape, bbox)

            xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()

            properties["bounding_box"] = {
                "min": {"x": xmin, "y": ymin, "z": zmin},
                "max": {"x": xmax, "y": ymax, "z": zmax},
                "dimensions": {
                    "length_x": xmax - xmin,
                    "length_y": ymax - ymin,
                    "length_z": zmax - zmin
                }
            }
        except Exception as e:
            logger.warning(f"Could not calculate bounding box: {e}")
            properties["bounding_box"] = None

        return properties

    def _extract_topology_info(self, shape: TopoDS_Shape) -> Dict[str, Any]:
        """
        Extract topology information (counts of solids, faces, edges, vertices)

        Args:
            shape: TopoDS_Shape to analyze

        Returns:
            Dictionary with topology counts
        """
        topology = {
            "solids": 0,
            "compounds": 0,
            "shells": 0,
            "faces": 0,
            "edges": 0,
            "vertices": 0
        }

        # Count topology elements
        explorer = TopologyExplorer(shape)

        topology["solids"] = explorer.number_of_solids()
        topology["compounds"] = explorer.number_of_compounds()
        topology["shells"] = explorer.number_of_shells()
        topology["faces"] = explorer.number_of_faces()
        topology["edges"] = explorer.number_of_edges()
        topology["vertices"] = explorer.number_of_vertices()

        # Additional details
        topology["details"] = {
            "has_free_edges": len(list(explorer.edges())) != topology["edges"],
            "shape_type": shape.ShapeType()
        }

        return topology

    # ---------------------------------------------------------------------
    # ✅ NEW: Slider Detection (Heuristic, explainable)
    # ---------------------------------------------------------------------
    def _detect_slider_likely(
        self,
        geometry: Dict[str, Any],
        topology: Dict[str, Any],
        pull_direction: str = "Z+"
    ) -> Dict[str, Any]:
        """
        Detect likelihood of slider requirement based on CAD geometry & topology.
        This is heuristic (confidence-based). It does not claim absolute undercut detection.
        """

        reasons: List[str] = []
        score = 0.0

        # Geometry inputs
        vol = (geometry.get("volume") or {}).get("value")
        dims = ((geometry.get("bounding_box") or {}).get("dimensions") or {})
        lx = dims.get("length_x")
        ly = dims.get("length_y")
        lz = dims.get("length_z")

        # Rule 1: Volume-to-bounding-box ratio (fill ratio)
        if vol and lx and ly and lz and lx > 0 and ly > 0 and lz > 0:
            bbox_vol = lx * ly * lz
            fill_ratio = vol / bbox_vol if bbox_vol > 0 else None

            if fill_ratio is not None:
                if fill_ratio < 0.25:
                    score += 0.45
                    reasons.append(
                        f"Low volume-to-bounding-box ratio ({fill_ratio:.2f}) indicates recessed/complex geometry."
                    )
                elif fill_ratio < 0.40:
                    score += 0.25
                    reasons.append(
                        f"Moderate volume-to-bounding-box ratio ({fill_ratio:.2f})."
                    )

        # Topology inputs
        faces = int(topology.get("faces", 0) or 0)
        solids = int(topology.get("solids", 0) or 0)
        shells = int(topology.get("shells", 0) or 0)

        # Rule 2: Face count indicates complexity
        if faces > 200:
            score += 0.35
            reasons.append(f"High face count ({faces}) suggests complex features.")
        elif faces > 120:
            score += 0.20
            reasons.append(f"Moderately high face count ({faces}).")

        # Rule 3: Multi solid/shell indicates complex/assembly-like structure
        if solids > 1 or shells > 1:
            score += 0.25
            reasons.append(f"Multiple solids/shells detected (solids={solids}, shells={shells}).")

        confidence = max(0.0, min(score, 1.0))
        slider_likely = confidence >= 0.55

        return {
            "slider_likely": slider_likely,
            "confidence": round(confidence, 2),
            "reasons": reasons,
            "pull_direction": pull_direction,
            "note": "Heuristic result based on geometry/topology; not a guaranteed undercut analysis."
        }

    # ---------------------------------------------------------------------
    # ✅ NEW: Cavity Recommendation (Heuristic, explainable)
    # ---------------------------------------------------------------------
    def _recommend_cavity_count(
        self,
        geometry: Dict[str, Any],
        topology: Dict[str, Any],
        slider_detection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recommend a cavity count using CAD-only heuristics.
        No machine library constraints are assumed here.
        Output is a suggestion with reasons and a feasible range.
        """

        reasons: List[str] = []
        score = 0.0

        dims = ((geometry.get("bounding_box") or {}).get("dimensions") or {})
        lx = dims.get("length_x") or 0.0
        ly = dims.get("length_y") or 0.0
        lz = dims.get("length_z") or 0.0

        max_dim = max(lx, ly, lz)
        faces = int(topology.get("faces", 0) or 0)

        slider_likely = bool(slider_detection.get("slider_likely", False))
        slider_conf = float(slider_detection.get("confidence", 0.0) or 0.0)

        # Size heuristic (relative)
        # Larger parts generally favor lower cavities; smaller parts allow more cavities.
        # NOTE: Units depend on STEP file model units; we treat it as relative sizing.
        if max_dim <= 0:
            reasons.append("Bounding box dimensions not available; cavity recommendation is limited.")
        else:
            if max_dim > 300:
                # Very large envelope
                score -= 0.50
                reasons.append("Large overall part envelope suggests fewer cavities for tool feasibility and stability.")
            elif max_dim > 180:
                score -= 0.25
                reasons.append("Medium-large part envelope suggests limiting cavity count to reduce tool size/handling risk.")
            elif max_dim > 80:
                score += 0.10
                reasons.append("Medium part envelope can support multi-cavity depending on tooling constraints.")
            else:
                score += 0.35
                reasons.append("Small part envelope generally supports multi-cavity tooling for output efficiency.")

        # Complexity heuristic
        if faces > 250:
            score -= 0.35
            reasons.append("Very high geometric complexity suggests fewer cavities to reduce tuning and rejection risk.")
        elif faces > 150:
            score -= 0.20
            reasons.append("High complexity suggests limiting cavities for robustness.")
        elif faces > 80:
            score -= 0.05
            reasons.append("Moderate complexity; cavity choice should consider tooling stability.")
        else:
            score += 0.10
            reasons.append("Low complexity supports multi-cavity if tooling limits allow.")

        # Slider penalty
        if slider_likely:
            score -= 0.35
            reasons.append(
                f"Slider likely (confidence={slider_conf:.2f}); multi-cavity tools become harder to balance and maintain."
            )

        # Convert score to a recommended cavity
        # score range approx [-1, +1]
        # Map to suggestion bands: 1 / 2 / 4 cavities
        if score <= -0.25:
            recommended = 1
        elif score <= 0.25:
            recommended = 2
        else:
            recommended = 4

        # Feasible range suggestion (CAD-only)
        # If slider likely or high complexity -> cap max cavity.
        max_cavity = 4
        if slider_likely or faces > 200:
            max_cavity = 2

        feasible_range = [1, 2] if max_cavity == 2 else [1, 2, 4]

        return {
            "recommended_cavities": recommended,
            "feasible_cavity_options": feasible_range,
            "reasons": reasons,
            "note": (
                "This recommendation is CAD-only heuristic. Final cavity selection must be validated "
                "against machine platen size, die envelope, shot capacity, and plant tooling standards."
            )
        }

    def _validate_shape(self, shape: TopoDS_Shape) -> Dict[str, Any]:
        """
        Validate shape quality and check for issues

        Args:
            shape: TopoDS_Shape to validate

        Returns:
            Dictionary with validation results
        """
        validation = {
            "is_valid": False,
            "is_done": False,
            "issues": []
        }

        try:
            analyzer = BRepCheck_Analyzer(shape)
            validation["is_valid"] = analyzer.IsValid()

            if not validation["is_valid"]:
                validation["issues"].append("Shape contains geometric or topological errors")

            validation["is_done"] = True

        except Exception as e:
            logger.error(f"Validation error: {e}")
            validation["issues"].append(f"Validation failed: {str(e)}")

        # Additional quality checks
        try:
            explorer = TopologyExplorer(shape)

            # Check for degenerate edges
            degenerate_count = 0
            for edge in explorer.edges():
                if edge.Degenerated():
                    degenerate_count += 1

            if degenerate_count > 0:
                validation["issues"].append(f"Found {degenerate_count} degenerate edges")

            validation["quality_metrics"] = {
                "degenerate_edges": degenerate_count,
                "total_edges": explorer.number_of_edges()
            }

        except Exception as e:
            logger.warning(f"Quality check error: {e}")

        return validation

    def _extract_assembly_structure(self, file_path: str) -> Dict[str, Any]:
        """
        Extract assembly structure and metadata using XCAF

        Args:
            file_path: Path to STEP file

        Returns:
            Dictionary with assembly information
        """
        assembly_info = {
            "is_assembly": False,
            "parts": [],
            "layers": [],
            "colors": []
        }

        try:
            # Create XCAF document
            doc = TDocStd_Document(TCollection_ExtendedString("MDTV-XCAF"))

            # Read STEP file with XCAF
            reader = STEPCAFControl_Reader()
            reader.SetColorMode(True)
            reader.SetLayerMode(True)
            reader.SetNameMode(True)

            status = reader.ReadFile(file_path)

            if status == IFSelect_RetDone:
                reader.Transfer(doc)

                # Get shape tool
                shape_tool = XCAFDoc_DocumentTool_ShapeTool(doc.Main())

                # Get free shapes (top-level components)
                labels = TDF_LabelSequence()
                shape_tool.GetFreeShapes(labels)

                assembly_info["is_assembly"] = labels.Length() > 1
                assembly_info["part_count"] = labels.Length()

                parts = []
                for i in range(1, labels.Length() + 1):
                    label = labels.Value(i)
                    name = label.EntryDumpToString()

                    parts.append({
                        "label": name,
                        "index": i
                    })

                assembly_info["parts"] = parts

        except Exception as e:
            logger.warning(f"Could not extract assembly structure: {e}")
            assembly_info["error"] = str(e)

        return assembly_info
