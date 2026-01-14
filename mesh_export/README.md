# Mesh Export Module

A Python module for exporting trimesh objects to VTK PolyData (.vtp) format with support for arbitrary layer separation and metadata preservation.

## Features

- **Generic layer export** - Export any number of layers with custom filenames
- **Flexible metadata** - Add custom metadata via handler functions
- **Single or multiple meshes** - Export individual meshes or combine multiple into one layer
- **Preserve colors** - Vertex colors are automatically preserved
- **Pure export focus** - No domain-specific logic, just clean export functionality

## Installation

The module requires the following dependencies:

```bash
pip install trimesh pyvista numpy
```

## Usage

### Quick Start

Export mesh and objects as separate layers:

```python
from mesh_export import export_layer

# Export mesh layer
export_layer(mesh, "mesh.vtp")

# Export spheres layer (combined into one file)
export_layer(spheres, "spheres.vtp")
```

### Export Any Number of Layers

The `export_layer()` function is completely generic - call it for each layer you need:

```python
from mesh_export import export_layer

# Export base mesh
export_layer(base_mesh, "layers/base.vtp")

# Export layer 1
export_layer(feature_mesh_1, "layers/features_1.vtp")

# Export layer 2
export_layer(feature_mesh_2, "layers/features_2.vtp")

# Export layer 3 with multiple objects combined
export_layer([obj1, obj2, obj3], "layers/combined.vtp")

# Export layer N...
export_layer(another_layer, "output/layer_n.vtp")
```

### Multiple Objects in One Layer

Combine multiple meshes into a single layer:

```python
from mesh_export import export_layer

# Multiple objects will be combined into one file
markers = [marker1, marker2, marker3, marker4]
export_layer(markers, "markers.vtp")
```

### Custom Metadata

Add your own metadata using a handler function:

```python
from mesh_export import export_layer
import numpy as np

def add_temperature_data(pv_mesh, original_meshes):
    """Add custom metadata to the PyVista mesh."""
    # Add custom cell data
    n_cells = pv_mesh.n_cells
    pv_mesh.cell_data['temperature'] = np.random.rand(n_cells) * 100
    pv_mesh.cell_data['pressure'] = np.random.rand(n_cells) * 50

export_layer(mesh, "simulation.vtp", metadata_handler=add_temperature_data)
```

### Example: Sphere Metadata Handler

Here's an example metadata handler for path visualization with spheres:

```python
from mesh_export import export_layer
import trimesh as tr
import numpy as np

def add_sphere_metadata(pv_mesh, spheres):
    """
    Custom metadata handler for spheres with path information.

    Adds cell data for radius, vertex indices, path positions, and roles.
    """
    n_faces_total = pv_mesh.n_cells
    radius = np.full(n_faces_total, -1.0, dtype=float)
    vertex_index = np.full(n_faces_total, -1, dtype=int)
    path_position = np.full(n_faces_total, -1, dtype=int)
    role_code = np.full(n_faces_total, 0, dtype=int)

    face_offset = 0
    for sphere in spheres:
        n_faces_sphere = len(sphere.faces)
        start_idx = face_offset
        end_idx = face_offset + n_faces_sphere

        radius[start_idx:end_idx] = sphere.metadata.get('radius', -1)
        vertex_index[start_idx:end_idx] = sphere.metadata.get('vertex_index', -1)
        path_position[start_idx:end_idx] = sphere.metadata.get('path_position', -1)

        # Set role code: 0=none, 1=start, 2=intermediate, 3=end
        role = sphere.metadata.get('role', 'none')
        if role == 'start':
            role_code[start_idx:end_idx] = 1
        elif role == 'intermediate':
            role_code[start_idx:end_idx] = 2
        elif role == 'end':
            role_code[start_idx:end_idx] = 3

        face_offset += n_faces_sphere

    pv_mesh.cell_data['radius'] = radius
    pv_mesh.cell_data['vertex_index'] = vertex_index
    pv_mesh.cell_data['path_position'] = path_position
    pv_mesh.cell_data['role_code'] = role_code

# Create spheres with metadata
spheres = []
for i, position in enumerate(path_positions):
    sphere = tr.creation.uv_sphere(radius=10)
    sphere.apply_translation(position)
    sphere.metadata = {
        'radius': 10,
        'vertex_index': i,
        'path_position': i,
        'role': 'intermediate'  # or 'start', 'end'
    }
    spheres.append(sphere)

# Export with custom metadata handler
export_layer(spheres, "path_spheres.vtp", metadata_handler=add_sphere_metadata)
```

## API Reference

### `export_layer(mesh_or_meshes, output_path, combine=True, metadata_handler=None)`

**The main generic export function.** Export a single mesh or list of meshes to a VTK PolyData file.

**Parameters:**
- `mesh_or_meshes` - Either a single `trimesh.Trimesh` object or a list of them
- `output_path` (str) - Path where the .vtp file will be saved (e.g., "output/layer1.vtp")
- `combine` (bool, optional) - If True and input is a list, combine meshes into one (default: True)
- `metadata_handler` (callable, optional) - Function to add metadata to the PyVista mesh
  - Signature: `metadata_handler(pv_mesh, original_meshes) -> None`

**Returns:**
- str: The output path where the file was saved

**Examples:**

```python
# Export a single mesh
export_layer(mesh, "mesh.vtp")

# Export with custom output directory
export_layer(mesh, "output/layers/base_mesh.vtp")

# Export multiple objects combined
export_layer([sphere1, sphere2, sphere3], "spheres.vtp")

# Export with metadata
def my_handler(pv_mesh, meshes):
    pv_mesh.cell_data['custom'] = custom_data

export_layer(spheres, "path.vtp", metadata_handler=my_handler)
```

---

### `trimesh_to_pyvista(trimesh_obj)`

**Low-level conversion function.** Convert a trimesh object to PyVista PolyData for custom processing.

**Parameters:**
- `trimesh_obj` - trimesh.Trimesh object to convert

**Returns:**
- pv.PolyData object

**Example:**

```python
from mesh_export import trimesh_to_pyvista

pv_mesh = trimesh_to_pyvista(mesh)
# Now you can use PyVista operations
pv_mesh.plot()
pv_mesh.save("custom.vtp")
```

## Complete Example

Here's a complete example showing how to export multiple layers with custom metadata:

```python
import trimesh as tr
import networkx as nx
import numpy as np
from mesh_export import export_layer

# Your custom metadata handler (domain-specific)
def add_sphere_metadata(pv_mesh, spheres):
    """Add path-specific metadata to spheres."""
    n_faces_total = pv_mesh.n_cells
    radius = np.full(n_faces_total, -1.0, dtype=float)
    vertex_index = np.full(n_faces_total, -1, dtype=int)
    path_position = np.full(n_faces_total, -1, dtype=int)
    role_code = np.full(n_faces_total, 0, dtype=int)

    face_offset = 0
    for sphere in spheres:
        n_faces_sphere = len(sphere.faces)
        start_idx = face_offset
        end_idx = face_offset + n_faces_sphere

        radius[start_idx:end_idx] = sphere.metadata.get('radius', -1)
        vertex_index[start_idx:end_idx] = sphere.metadata.get('vertex_index', -1)
        path_position[start_idx:end_idx] = sphere.metadata.get('path_position', -1)

        role = sphere.metadata.get('role', 'none')
        if role == 'start':
            role_code[start_idx:end_idx] = 1
        elif role == 'intermediate':
            role_code[start_idx:end_idx] = 2
        elif role == 'end':
            role_code[start_idx:end_idx] = 3

        face_offset += n_faces_sphere

    pv_mesh.cell_data['radius'] = radius
    pv_mesh.cell_data['vertex_index'] = vertex_index
    pv_mesh.cell_data['path_position'] = path_position
    pv_mesh.cell_data['role_code'] = role_code

# Load and simplify mesh
mesh = tr.load("model.stl")
simplified = mesh.simplify_quadric_decimation(percent=0.98)

# Create graph and find path
G = nx.Graph()
G.add_nodes_from(list(map(tuple, simplified.vertices)))
for edge in simplified.edges:
    G.add_edge(*edge)

path = nx.shortest_path(G, start_vertex, end_vertex)

# Create spheres along path
spheres = []
for i, vertex_idx in enumerate(path):
    sphere = tr.creation.uv_sphere(radius=5)
    sphere.apply_translation(simplified.vertices[vertex_idx])
    sphere.visual.vertex_colors = [255, 0, 255, 255]  # Purple

    # Mark start and end differently
    if i == 0:
        role = 'start'
        sphere.visual.vertex_colors = [255, 0, 0, 255]  # Red
    elif i == len(path) - 1:
        role = 'end'
        sphere.visual.vertex_colors = [0, 255, 0, 255]  # Green
    else:
        role = 'intermediate'

    sphere.metadata = {
        'radius': 5,
        'vertex_index': vertex_idx,
        'path_position': i,
        'role': role
    }
    spheres.append(sphere)

# Export layers - can export as many as you need!
export_layer(simplified, "mesh.vtp")
export_layer(spheres, "spheres.vtp", metadata_handler=add_sphere_metadata)

print("All layers exported!")
```

## Custom Metadata Handler Examples

### Simulation Data

```python
import numpy as np

def add_simulation_data(pv_mesh, meshes):
    """Add simulation results as metadata."""
    n_cells = pv_mesh.n_cells

    # Add temperature field
    temperatures = np.random.rand(n_cells) * 100
    pv_mesh.cell_data['temperature'] = temperatures

    # Add stress field
    stress = np.random.rand(n_cells) * 500
    pv_mesh.cell_data['stress'] = stress

    # Add categorical data
    regions = np.random.randint(0, 5, n_cells)
    pv_mesh.cell_data['region'] = regions

export_layer(simulation_mesh, "results.vtp", metadata_handler=add_simulation_data)
```

### Material Properties

```python
def add_material_properties(pv_mesh, meshes):
    """Add material property metadata."""
    n_cells = pv_mesh.n_cells

    # Material ID for each cell
    material_ids = np.ones(n_cells, dtype=int) * 42
    pv_mesh.cell_data['material_id'] = material_ids

    # Density
    densities = np.full(n_cells, 2.7)  # Aluminum
    pv_mesh.cell_data['density'] = densities

export_layer(part, "part_with_materials.vtp", metadata_handler=add_material_properties)
```

## Exporting Multiple Geometry Types

Export different types of geometries as separate layers:

```python
from mesh_export import export_layer

# Base mesh
export_layer(base_mesh, "layers/base.vtp")

# Path markers
export_layer(path_spheres, "layers/path.vtp", metadata_handler=add_sphere_metadata)

# Cylinders for edges
export_layer(edge_cylinders, "layers/edges.vtp")

# Boxes for annotations
export_layer(annotation_boxes, "layers/annotations.vtp")

# Point cloud
export_layer(point_spheres, "layers/points.vtp")
```

## File Format

The exported .vtp files are XML-based VTK PolyData files that can be opened with:
- **ParaView** - 3D visualization application
- **PyVista** - Python library
- **vtk.js** - Web-based visualization
- **Blender** (with VTK plugins)

## Error Handling

The module raises appropriate exceptions:

```python
try:
    export_layer(mesh, "output.vtp")
except ImportError as e:
    print(f"Missing dependency: {e}")
except ValueError as e:
    print(f"Invalid input: {e}")
```

Common errors:
- `ImportError` - pyvista, trimesh, or numpy not installed
- `ValueError` - Empty mesh list

## Design Philosophy

**Pure Export Functionality**: The module focuses solely on exporting trimesh objects to VTK format. It doesn't include domain-specific logic like sphere metadata handlers - those belong in your application code where they can be customized for your specific needs.

**Flexibility First**: `export_layer()` is completely generic. You decide:
- How many layers to export
- What to name each file
- Whether to combine objects or keep them separate
- What metadata to add (via custom handlers)

This makes it suitable for any project, from simple mesh exports to complex multi-layer visualizations.

## Use Cases

- **Path Visualization** - Export mesh + path markers as separate layers
- **Scientific Visualization** - Export simulation results with multiple data layers
- **3D Web Applications** - Prepare layered models for vtk.js viewers
- **Multi-Component Models** - Export assemblies with each part as a layer
- **Annotation Systems** - Export base model + annotation geometries
- **Time Series** - Export multiple time steps as separate layers

## Version

Current version: 2.0.0

## License

This module is part of the meshing project.
