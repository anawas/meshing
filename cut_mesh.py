import trimesh as tr
import logging
import os
import numpy as np

axis_to_idx = {'x': 0, 'y': 1, 'z': 2}

def crop_submesh(mesh: tr.Trimesh, axis='x', vmin=100.0, vmax=200.0):
    ax = axis_to_idx[axis]

    V = mesh.vertices
    F = mesh.faces

    # get vertices that lay inside stripe
    vin = (V[:, ax] >= vmin) & (V[:, ax] <= vmax)
    faces_to_keep = vin[F].all(axis=1)

    if not np.any(faces_to_keep):
        raise ValueError("Kein Face liegt vollständig im gewünschten Intervall.")

    sub = mesh.submesh([np.where(faces_to_keep)[0]], append=True, repair=True)
    return sub

def check_and_repair(strip):
    # strip.rezero()  # Schwerpunkt nach (0,0,0) verschieben
    strip.remove_infinite_values()
    strip.remove_degenerate_faces()
    strip.fill_holes()  # kann bei offenen Netzen helfen
    strip.fix_normals()
    return strip

# attach to logger so trimesh messages will be printed to console
tr.util.attach_to_log(level=logging.ERROR)

# there is an open surface in this file
mesh_filename = "Stanford_Bunny_sample.stl"
# mesh_filename = "0.stl"

fracture = tr.load(os.path.join("meshes", mesh_filename))
simplified = fracture.simplify_quadric_decimation(percent=0.80)

for axes in["x", "y", "z"]:
    ax = axis_to_idx[axes]

    ax_min = float(simplified.bounds[0, ax])
    ax_max = float(simplified.bounds[1, ax])

    print(f" ℹ️ extends for axis {axes}")
    print(f"    - min: {ax_min}")
    print(f"    - max: {ax_max}")
    strip = crop_submesh(simplified, axis=axes, vmin=10, vmax=30)
    strip = check_and_repair(strip)
    strip.export(f"strip_100_150_{axes}_submesh.stl")
