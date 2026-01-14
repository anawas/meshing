"""
Mesh Export Module

Provides functionality to export trimesh objects to VTK PolyData (.vtp) format
with support for metadata and layer separation.
"""

import os
from typing import List, Optional, Any, Union


def trimesh_to_pyvista(trimesh_obj):
    """
    Convert a trimesh object to PyVista PolyData.

    Args:
        trimesh_obj: A trimesh.Trimesh object to convert

    Returns:
        pv.PolyData: PyVista PolyData object

    Raises:
        ImportError: If pyvista is not installed
    """
    try:
        import pyvista as pv
    except ImportError:
        raise ImportError("pyvista is required for exporting. Install with: pip install pyvista")

    vertices = trimesh_obj.vertices
    faces = trimesh_obj.faces

    # PyVista expects faces in format [n_points, v0, v1, v2, ...]
    pv_faces = []
    for face in faces:
        pv_faces.extend([3, face[0], face[1], face[2]])

    mesh_pv = pv.PolyData(vertices, pv_faces)

    # Add vertex colors if available
    if hasattr(trimesh_obj.visual, 'vertex_colors'):
        mesh_pv['colors'] = trimesh_obj.visual.vertex_colors[:, :3]  # RGB only

    return mesh_pv


def export_layer(
    mesh_or_meshes: Union[Any, List[Any]],
    output_path: str,
    combine: bool = True,
    metadata_handler: Optional[callable] = None
) -> str:
    """
    Generic function to export a single mesh or list of meshes to a VTK PolyData file.

    This is the main export function that can handle any layer type. For multiple
    meshes, they will be combined into a single layer.

    Args:
        mesh_or_meshes: Either a single trimesh.Trimesh object or a list of them
        output_path: Path where the .vtp file will be saved (e.g., "output/layer1.vtp")
        combine: If True and input is a list, combine meshes into one (default: True)
        metadata_handler: Optional function to add metadata to the PyVista mesh.
                         Signature: metadata_handler(pv_mesh, original_meshes) -> None

    Returns:
        str: The output path where the file was saved

    Raises:
        ImportError: If required dependencies are not installed
        ValueError: If input is invalid

    Examples:
        # Export a single mesh
        export_layer(mesh, "mesh.vtp")

        # Export multiple spheres combined
        export_layer(spheres, "spheres.vtp")

        # Export with custom metadata
        def add_metadata(pv_mesh, meshes):
            pv_mesh.cell_data['custom'] = [1, 2, 3, ...]

        export_layer(spheres, "custom.vtp", metadata_handler=add_metadata)
    """
    try:
        import trimesh as tr
    except ImportError:
        raise ImportError("trimesh is required. Install with: pip install trimesh")

    # Normalize input to list
    if not isinstance(mesh_or_meshes, list):
        meshes = [mesh_or_meshes]
    else:
        meshes = mesh_or_meshes

    if not meshes:
        raise ValueError("Input mesh or mesh list cannot be empty")

    # Combine meshes if needed
    if len(meshes) > 1 and combine:
        combined_mesh = tr.util.concatenate(meshes)
    else:
        combined_mesh = meshes[0]

    # Convert to PyVista
    pv_mesh = trimesh_to_pyvista(combined_mesh)

    # Apply custom metadata if handler provided
    if metadata_handler:
        metadata_handler(pv_mesh, meshes)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and output_dir != ".":
        os.makedirs(output_dir, exist_ok=True)

    # Save the file
    pv_mesh.save(output_path)
    print(f"Exported {output_path}")

    return output_path


