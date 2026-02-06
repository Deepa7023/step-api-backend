#!/usr/bin/env python3
"""
Simple STEP File Generator
Creates basic geometric shapes as STEP files for testing the API
"""

try:
    from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeSphere
    from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
    from OCC.Core.IFSelect import IFSelect_RetDone
    import sys
    
    OCCT_AVAILABLE = True
except ImportError:
    OCCT_AVAILABLE = False
    print("Error: pythonocc-core not installed")
    print("Install with: conda install -c conda-forge pythonocc-core")
    sys.exit(1)


def create_box(length=100, width=50, height=25):
    """Create a simple box"""
    return BRepPrimAPI_MakeBox(length, width, height).Shape()


def create_cylinder(radius=25, height=100):
    """Create a cylinder"""
    return BRepPrimAPI_MakeCylinder(radius, height).Shape()


def create_sphere(radius=50):
    """Create a sphere"""
    return BRepPrimAPI_MakeSphere(radius).Shape()


def write_step_file(shape, filename):
    """Write shape to STEP file"""
    step_writer = STEPControl_Writer()
    step_writer.Transfer(shape, STEPControl_AsIs)
    status = step_writer.Write(filename)
    
    if status != IFSelect_RetDone:
        raise Exception(f"Failed to write STEP file: {filename}")
    
    print(f"✅ Created: {filename}")


def main():
    """Generate sample STEP files"""
    print("Generating sample STEP files...")
    print()
    
    # Create a box
    box_shape = create_box(100, 50, 25)
    write_step_file(box_shape, "sample_box.step")
    
    # Create a cylinder
    cylinder_shape = create_cylinder(25, 100)
    write_step_file(cylinder_shape, "sample_cylinder.step")
    
    # Create a sphere
    sphere_shape = create_sphere(50)
    write_step_file(sphere_shape, "sample_sphere.step")
    
    print()
    print("Sample files generated successfully!")
    print()
    print("Test them with:")
    print("  python test_api.py sample_box.step")
    print("  ./test_curl.sh sample_cylinder.step")


if __name__ == "__main__":
    main()
