import trimesh as tr
import logging
import os
import networkx as nx
import random
import numpy as np
from mesh_export import export_layer


def weights(a: int, b: int, w: dict) -> float:
    return w["weight"]


def add_marker_metadata(pv_mesh, markers):
    """
    Metadata handler for path markers (cubes) with path information.

    Adds the following cell data arrays:
        - size: Marker size values
        - vertex_index: Original vertex indices
        - path_position: Position in path sequence
        - role_code: Numeric role codes (0=none, 1=start, 2=intermediate, 3=end)

    Args:
        pv_mesh: PyVista PolyData mesh to add metadata to
        markers: List of trimesh marker objects (cubes) with metadata

    Expected metadata on each marker:
        - size: float - Marker size
        - vertex_index: int - Original vertex index in mesh
        - path_position: int - Position in the path
        - role: str - Role identifier ('start', 'intermediate', 'end')
    """
    n_faces_total = pv_mesh.n_cells
    size = np.full(n_faces_total, -1.0, dtype=float)
    vertex_index = np.full(n_faces_total, -1, dtype=int)
    path_position = np.full(n_faces_total, -1, dtype=int)
    role_code = np.full(n_faces_total, 0, dtype=int)

    face_offset = 0
    for marker in markers:
        n_faces_marker = len(marker.faces)
        start_idx = face_offset
        end_idx = face_offset + n_faces_marker

        size[start_idx:end_idx] = marker.metadata.get('size', -1)
        vertex_index[start_idx:end_idx] = marker.metadata.get('vertex_index', -1)
        path_position[start_idx:end_idx] = marker.metadata.get('path_position', -1)

        # Set role code: 0=none, 1=start, 2=intermediate, 3=end
        role = marker.metadata.get('role', 'none')
        if role == 'start':
            role_code[start_idx:end_idx] = 1
        elif role == 'intermediate':
            role_code[start_idx:end_idx] = 2
        elif role == 'end':
            role_code[start_idx:end_idx] = 3

        face_offset += n_faces_marker

    # Add metadata arrays to the PyVista mesh
    pv_mesh.cell_data['size'] = size
    pv_mesh.cell_data['vertex_index'] = vertex_index
    pv_mesh.cell_data['path_position'] = path_position
    pv_mesh.cell_data['role_code'] = role_code

# attach to logger so trimesh messages will be printed to console
tr.util.attach_to_log(level=logging.ERROR)

# there is an open surface in this file
# mesh_filename = "Stanford_Bunny_sample.stl"
mesh_filename = "1.stl"

mesh = tr.load(os.path.join("meshes", mesh_filename))
simplified = mesh.simplify_quadric_decimation(percent=0.98)
print(f"{len(simplified.vertices)=}")
print(f"{simplified.edges[0]}")


# Convert the mesh to a Graph. The vertices of the
# mesh become nodes, edges become the edges connecting the nodes
G = nx.Graph()
nodes = list(map(tuple, simplified.vertices))
G.add_nodes_from(nodes)
for edge in simplified.edges:
    G.add_edge(*edge, weight=random.random()*10.0)
# G.add_edges_from(simplified.edges)

start_vertex = random.choice(range(len(simplified.vertices)-1))
stop_vertex = random.choice(range(len(simplified.vertices)-1))
                             
# Find the shortest path between vertex[start_vertex] and
# vertex[stop_vertex]
# sp has the indexes of the vertices that are part of the
# shortest path
sp: list = nx.shortest_path(G, start_vertex, stop_vertex, weights)

# create a list of cubes for the points on the shortest path
marker_size = 40
markers = [tr.creation.box(extents=[marker_size, marker_size, marker_size]) for i in range(len(sp))]

# move (translate) the cubes to the positions of the points
# and color the start and endpoint differently.
# Also add metadata to each cube
for i,m in enumerate(markers):
    translation = simplified.vertices[sp[i]]
    m.apply_translation(simplified.vertices[sp[i]])

    # Add metadata to the marker
    m.metadata['size'] = random.randrange(10,50)
    m.metadata['vertex_index'] = int(sp[i])
    m.metadata['path_position'] = i
    m.metadata['type'] = 'path_marker'

    m.visual.vertex_colors = [255,0,255,255]
    if i == 0:
        m.visual.vertex_colors = [255,0,0,255]
        m.metadata['role'] = 'start'
    elif i == len(sp)-1:
        m.visual.vertex_colors = [0,255,0,255]
        m.metadata['role'] = 'end'
    else:
        m.metadata['role'] = 'intermediate'

scene = tr.Scene(simplified)
scene.add_geometry(markers)

# We need a camera
camera = scene.camera
camera.z_far = 1000000
camera.z_near = 0.1
# View size aka window size
camera.resolution=(1000,1000)


# Export scene as separate .vtp files for web visualization
try:
    # Export mesh layer
    export_layer(simplified, "mesh.vtp")

    # Export markers layer with metadata
    export_layer(markers, "markers.vtp", metadata_handler=add_marker_metadata)

    print("\nAll layers exported successfully!")

except ImportError as e:
    print(f"Export failed: {e}")
    print("Fallback: exporting as .ply instead")
    # Fallback: export as .ply which can be converted later
    combined_meshes = [simplified] + markers
    combined = tr.util.concatenate(combined_meshes[0])
    combined.export('output_scene.ply')
    print("Exported as output_scene.ply instead")

# Don't care about the surface normals. Otherwise, the
# backside will not be visible.
scene.show(flags={'cull': False})
