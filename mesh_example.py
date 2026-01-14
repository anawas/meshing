import trimesh as tr
import logging
import os
import networkx as nx
import random


def weights(a: int, b: int, w: dict) -> float:
    return w["weight"]

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

# create a list of spheres for the points on the shortest path
sphere_radius = 20
spheres = [tr.creation.uv_sphere(sphere_radius) for i in range(len(sp))]

# move (translate) the spheres to the positions of the points
# and color the start and endpoint differently.
# Also add metadata to each sphere
for i,m in enumerate(spheres):
    translation = simplified.vertices[sp[i]]
    m.apply_translation(simplified.vertices[sp[i]])

    # Add metadata to the sphere
    m.metadata['radius'] = sphere_radius
    m.metadata['vertex_index'] = int(sp[i])
    m.metadata['path_position'] = i
    m.metadata['type'] = 'path_sphere'

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
scene.add_geometry(spheres)

# We need a camera
camera = scene.camera
camera.z_far = 1000000
camera.z_near = 0.1
# View size aka window size
camera.resolution=(1000,1000)


# Export scene as .vtp for web visualization
# First, combine all geometry into a single mesh
combined_meshes = [simplified] + spheres
combined = tr.util.concatenate(combined_meshes)

# Export to .vtp using trimesh (will try to use available backend)
try:
    import pyvista as pv
    import numpy as np

    # Convert trimesh to pyvista
    vertices = combined.vertices
    faces = combined.faces
    # pyvista expects faces in format [n_points, v0, v1, v2, ...]
    pv_faces = []
    for face in faces:
        pv_faces.extend([3, face[0], face[1], face[2]])

    mesh_pv = pv.PolyData(vertices, pv_faces)

    # Add vertex colors if available
    if hasattr(combined.visual, 'vertex_colors'):
        mesh_pv['colors'] = combined.visual.vertex_colors[:, :3]  # RGB only

    # Add metadata as cell data
    # Track which cells belong to which geometry
    n_faces_total = len(faces)

    # Initialize metadata arrays with default values
    # Use integer codes instead of strings for VTP compatibility
    # mesh_type_code: 0=mesh, 1=path_sphere
    # role_code: 0=none, 1=start, 2=intermediate, 3=end
    mesh_type_code = np.full(n_faces_total, 0, dtype=int)
    radius = np.full(n_faces_total, -1.0, dtype=float)
    vertex_index = np.full(n_faces_total, -1, dtype=int)
    path_position = np.full(n_faces_total, -1, dtype=int)
    role_code = np.full(n_faces_total, 0, dtype=int)

    # Calculate face counts for each mesh
    face_offset = len(simplified.faces)
    mesh_type_code[:face_offset] = 0  # mesh

    # Add metadata for each sphere
    for i, sphere in enumerate(spheres):
        n_faces_sphere = len(sphere.faces)
        start_idx = face_offset
        end_idx = face_offset + n_faces_sphere

        mesh_type_code[start_idx:end_idx] = 1  # path_sphere
        radius[start_idx:end_idx] = sphere.metadata.get('radius', -1)
        vertex_index[start_idx:end_idx] = sphere.metadata.get('vertex_index', -1)
        path_position[start_idx:end_idx] = sphere.metadata.get('path_position', -1)

        # Set role code
        role = sphere.metadata.get('role', 'none')
        if role == 'start':
            role_code[start_idx:end_idx] = 1
        elif role == 'intermediate':
            role_code[start_idx:end_idx] = 2
        elif role == 'end':
            role_code[start_idx:end_idx] = 3

        face_offset += n_faces_sphere

    # Add the metadata arrays to the mesh
    mesh_pv.cell_data['mesh_type_code'] = mesh_type_code
    mesh_pv.cell_data['radius'] = radius
    mesh_pv.cell_data['vertex_index'] = vertex_index
    mesh_pv.cell_data['path_position'] = path_position
    mesh_pv.cell_data['role_code'] = role_code

    mesh_pv.save('output_scene.vtp')
    print("Scene exported to output_scene.vtp with metadata")
except ImportError:
    print("pyvista not installed. Install with: pip install pyvista")
    # Fallback: export as .ply which can be converted later
    combined.export('output_scene.ply')
    print("Exported as output_scene.ply instead")

# Don't care about the surface normals. Otherwise, the
# backside will not be visible.
scene.show(flags={'cull': False})
