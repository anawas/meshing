# Layer Separation Implementation - Change Report

**Date:** 2026-01-14

## Overview

Implemented a layer separation system that allows independent visibility control of mesh components in both ParaView and the web-based vtk.js viewer. The system exports separate .vtp files for different components (mesh, start sphere, path spheres, end sphere) and provides checkbox controls in the web viewer to toggle layer visibility.

## Problem Statement

The original implementation exported a single combined .vtp file containing both the mesh and spheres. This made it impossible to selectively show/hide individual components in the viewer.

## Solution

Implemented a multi-layer export system with separate .vtp files for each component, enabling independent visibility control through a checkbox UI.

---

## File Changes

### 1. mesh_example.py

**Location:** `mesh_example.py:80-183`

**Changes:**
- Replaced single combined export with separate layer exports
- Created helper function `trimesh_to_pyvista()` to convert trimesh objects to PyVista PolyData
- Separated spheres by role (start, intermediate, end)
- Exported 4 separate files:
  - `mesh.vtp` - simplified mesh
  - `sphere_start.vtp` - start point with metadata
  - `sphere_path.vtp` - intermediate path points with metadata
  - `sphere_end.vtp` - end point with metadata

**Key Code:**
```python
def trimesh_to_pyvista(trimesh_obj):
    """Convert a trimesh object to pyvista PolyData"""
    vertices = trimesh_obj.vertices
    faces = trimesh_obj.faces
    pv_faces = []
    for face in faces:
        pv_faces.extend([3, face[0], face[1], face[2]])
    mesh_pv = pv.PolyData(vertices, pv_faces)
    if hasattr(trimesh_obj.visual, 'vertex_colors'):
        mesh_pv['colors'] = trimesh_obj.visual.vertex_colors[:, :3]
    return mesh_pv
```

**Metadata Preserved:**
- `radius` - sphere radius
- `vertex_index` - original vertex index in mesh
- `path_position` - position in shortest path
- `role_code` - role identifier (1=start, 2=intermediate, 3=end)

---

### 2. webapp/fileLoader.js

**Location:** `webapp/fileLoader.js` (complete rewrite)

**Major Changes:**
- Added layer configuration system
- Replaced single actor/mapper with multi-layer management
- Implemented separate actor/mapper pairs for each layer
- Added layer visibility control functions
- Updated file loading to support multiple files
- Modified cloud download to fetch all layer files in parallel

**New Layer Configuration:**
```javascript
const LAYERS = [
    { id: 'mesh', filename: 'mesh.vtp', label: 'Mesh', defaultVisible: true },
    { id: 'sphere_start', filename: 'sphere_start.vtp', label: 'Start Point', defaultVisible: true },
    { id: 'sphere_path', filename: 'sphere_path.vtp', label: 'Path Points', defaultVisible: true },
    { id: 'sphere_end', filename: 'sphere_end.vtp', label: 'End Point', defaultVisible: true }
];
```

**New Functions:**
- `createLayer(layerId)` - Creates actor/mapper pair for a layer
- `loadLayerData(layerId, fileContents)` - Loads VTP data into a layer
- `setLayerVisibility(layerId, visible)` - Toggle layer visibility
- `getLayerVisibility(layerId)` - Get current visibility state
- `getAllSources()` - Get all visible layer sources
- `downloadLayerFromCloud(layerId, filename)` - Download single layer from cloud
- `downloadAllLayersFromCloud()` - Download all layers in parallel

**Exported API:**
```javascript
return {
    layers,
    LAYERS,
    handleFileSelect,
    downloadAllLayersFromCloud,
    setLayerVisibility,
    getLayerVisibility,
    getAllSources,
    isInitialized: () => isInitialized
};
```

---

### 3. webapp/viewer_vtk.html

**Location:** `viewer_vtk.html:10-22`

**Changes:**
- Added `multiple` attribute to file input
- Added layer controls section with container for checkboxes

**New HTML Structure:**
```html
<input type="file" id="fileInput" accept=".vtp" multiple />

<div id="layerControls" style="margin-top: 15px;">
    <h4>Layers</h4>
    <div id="layerCheckboxes"></div>
</div>
```

---

### 4. webapp/app.js

**Location:** `webapp/app.js` (multiple sections)

**Changes:**

#### State Management (lines 64-68)
- Removed single actor/mapper/source variables
- Kept only `wireframeMode` flag

**Before:**
```javascript
let actor = null;
let mapper = null;
let currentSource = null;
let actorAdded = false;
let wireframeMode = false;
```

**After:**
```javascript
let wireframeMode = false;
```

#### File Loader Setup (lines 148-193)
- Updated dependencies passed to `setupFileLoader`
- Added `createLayerCheckboxes()` function to generate UI
- Changed cloud download function reference

**New Layer Checkbox UI:**
```javascript
function createLayerCheckboxes() {
    const container = document.getElementById('layerCheckboxes');
    container.innerHTML = '';

    fileLoader.LAYERS.forEach(layerDef => {
        const div = document.createElement('div');
        div.style.marginBottom = '5px';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `layer-${layerDef.id}`;
        checkbox.checked = layerDef.defaultVisible;
        checkbox.addEventListener('change', (e) => {
            fileLoader.setLayerVisibility(layerDef.id, e.target.checked);
        });

        const label = document.createElement('label');
        label.htmlFor = checkbox.id;
        label.textContent = layerDef.label;
        label.style.marginLeft = '5px';

        div.appendChild(checkbox);
        div.appendChild(label);
        container.appendChild(div);
    });
}
```

#### Click Handling (lines 199-246)
- Updated to search through all layers for picked actor
- Modified to handle multiple sources
- Added layer lookup logic

**Key Changes:**
```javascript
function handleClick(callData) {
    if (!fileLoader.isInitialized()) return;

    // Pick logic...

    // Find which layer this actor belongs to
    let pickedSource = null;
    for (const layerId in fileLoader.layers) {
        const layer = fileLoader.layers[layerId];
        if (layer.actor === pickedActor && layer.visible) {
            pickedSource = layer.source;
            break;
        }
    }

    if (pickedSource && cellId !== -1) {
        displayMetadata(pickedSource, cellId, pos);
    }
}
```

#### UI Controls (lines 260-280)
- Updated `resetCamera()` to use `fileLoader.isInitialized()`
- Updated `toggleWireframe()` to apply to all layer actors

**Wireframe for All Layers:**
```javascript
window.toggleWireframe = function() {
    if (fileLoader.isInitialized()) {
        wireframeMode = !wireframeMode;
        const mode = wireframeMode ? REPRESENTATION_MODES.WIREFRAME : REPRESENTATION_MODES.SURFACE;

        // Apply wireframe mode to all actors
        for (const layerId in fileLoader.layers) {
            const layer = fileLoader.layers[layerId];
            layer.actor.getProperty().setRepresentation(mode);
        }

        renderWindow.render();
    }
};
```

---

## Feature Summary

### Exported Files
- **mesh.vtp** - Base mesh geometry with vertex colors
- **sphere_start.vtp** - Red start point sphere with metadata
- **sphere_path.vtp** - Purple intermediate spheres with metadata
- **sphere_end.vtp** - Green end point sphere with metadata

### Web Viewer Features
1. **Layer Checkboxes** - Toggle visibility for:
   - Mesh
   - Start Point
   - Path Points
   - End Point

2. **Multiple File Loading** - Select all 4 .vtp files at once from local filesystem

3. **Cloud Download** - Downloads all layers in parallel from S3

4. **Preserved Functionality**:
   - Click on spheres to display metadata
   - Wireframe mode applies to all visible layers
   - Camera reset works with all layers
   - All interaction controls maintained

### ParaView Compatibility
- All .vtp files can be opened separately in ParaView
- Each file maintains its own metadata
- Colors preserved in each layer

---

## Usage Instructions

### 1. Generate Layer Files
```bash
python mesh_example.py
```

**Output:**
```
Exported mesh.vtp
Exported sphere_start.vtp
Exported sphere_path.vtp
Exported sphere_end.vtp

All layers exported successfully!
```

### 2. Load in Web Viewer

**Option A: From Local Files**
1. Click "oder" file input button
2. Select all 4 .vtp files (mesh.vtp, sphere_start.vtp, sphere_path.vtp, sphere_end.vtp)
3. Files load automatically

**Option B: From Cloud**
1. Click "Download from Cloud" button
2. All 4 files download and load in parallel

### 3. Control Layer Visibility
Use checkboxes in the "Layers" section:
- ☑ Mesh - Show/hide base mesh
- ☑ Start Point - Show/hide red start sphere
- ☑ Path Points - Show/hide purple path spheres
- ☑ End Point - Show/hide green end sphere

---

## Technical Details

### Layer Management Architecture

**Data Structure:**
```javascript
layers = {
    'mesh': {
        actor: vtkActor,
        mapper: vtkMapper,
        source: vtkPolyData,
        visible: boolean
    },
    'sphere_start': { ... },
    'sphere_path': { ... },
    'sphere_end': { ... }
}
```

**Advantages:**
- Independent visibility control
- Separate picking per layer
- Easy to extend with new layers
- No redundant data (compared to single combined file)

### Performance Considerations

**Parallel Loading:**
- Cloud downloads use `Promise.all()` for concurrent fetching
- File loading processes multiple files simultaneously
- No blocking between layer loads

**Memory:**
- Each layer has its own actor/mapper (small overhead)
- Sources separated (cleaner than filtering single source)
- No duplicate geometry data

---

## Backward Compatibility

**Breaking Changes:**
- Old `output_scene.vtp` is no longer generated
- Web viewer no longer supports single .vtp file loading
- Cloud download expects 4 separate files in S3

**Migration Path:**
- Re-run `mesh_example.py` to generate new layer files
- Upload all 4 .vtp files to S3 bucket
- No changes needed to metadata structure or format

---

## Future Enhancements

Potential improvements:
1. **Group Controls** - "Show All" / "Hide All" buttons
2. **Layer Colors** - Customize colors for each layer in UI
3. **Layer Opacity** - Adjust transparency per layer
4. **Layer Export Config** - Make layer definitions configurable
5. **Dynamic Layer Loading** - Load layers on-demand based on checkbox state
6. **VTM Export** - Add optional .vtm multiblock export for advanced ParaView features

---

## Testing Checklist

- [x] Python script exports 4 separate .vtp files
- [x] Each file contains correct geometry and metadata
- [x] Web viewer loads multiple files from file input
- [x] Cloud download loads all layers successfully
- [x] Layer checkboxes toggle visibility correctly
- [x] Sphere metadata tooltips work on all sphere layers
- [x] Wireframe mode applies to all layers
- [x] Camera reset works with multiple layers
- [x] Picking works across all visible layers

---

## Files Modified

1. `mesh_example.py` - Lines 80-183 (export logic)
2. `webapp/fileLoader.js` - Complete rewrite (multi-layer system)
3. `webapp/viewer_vtk.html` - Lines 10-22 (layer UI)
4. `webapp/app.js` - Lines 64-68, 148-193, 199-246, 260-280 (layer integration)

**Total Lines Changed:** ~400 lines

---

## Dependencies

No new dependencies added. Uses existing:
- Python: `pyvista`, `trimesh`, `numpy`
- JavaScript: `@kitware/vtk.js` (via CDN)

---

## Conclusion

The layer separation implementation successfully provides independent visibility control for mesh components while maintaining all existing functionality. The system is scalable, performant, and provides a better user experience for analyzing shortest path visualizations.
