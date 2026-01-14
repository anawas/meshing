#!/usr/bin/env python3
"""Convert VTP file to STL format for web viewing"""

import pyvista as pv
import sys

def convert_vtp_to_stl(vtp_file, stl_file):
    """Convert VTP file to STL"""
    print(f"Reading {vtp_file}...")
    mesh = pv.read(vtp_file)

    print(f"Mesh info:")
    print(f"  Points: {mesh.n_points}")
    print(f"  Cells: {mesh.n_cells}")

    print(f"Writing {stl_file}...")
    mesh.save(stl_file)

    print("Conversion complete!")

if __name__ == "__main__":
    vtp_file = "output_scene.vtp"
    stl_file = "output_scene.stl"

    try:
        convert_vtp_to_stl(vtp_file, stl_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
