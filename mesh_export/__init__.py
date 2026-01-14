"""
Mesh Export Package

A package for exporting trimesh objects to VTK PolyData format with layer separation
and metadata support.

Main functions:
    - export_layer: Generic function to export any layer with arbitrary filename
    - trimesh_to_pyvista: Convert trimesh to PyVista PolyData (low-level)
"""

from .exporter import (
    export_layer,
    trimesh_to_pyvista
)

__version__ = "2.0.0"

__all__ = [
    'export_layer',
    'trimesh_to_pyvista'
]
