import vtkXMLPolyDataReader from '@kitware/vtk.js/IO/XML/XMLPolyDataReader';
import vtkActor from '@kitware/vtk.js/Rendering/Core/Actor';
import vtkMapper from '@kitware/vtk.js/Rendering/Core/Mapper';

// ============================================================================
// Layer Configuration
// ============================================================================

const LAYERS = [
    { id: 'mesh', filename: 'mesh.vtp', label: 'Mesh', defaultVisible: true },
    { id: 'markers', filename: 'markers.vtp', label: 'Path Markers', defaultVisible: true }
];

// ============================================================================
// File Loading
// ============================================================================

const API_ENDPOINT = 'https://xhx5lqfvq1.execute-api.eu-central-1.amazonaws.com/prod/download-url';

export function setupFileLoader(dependencies) {
    const { renderer, picker, renderWindow } = dependencies;

    // Store layer data: { id -> { actor, mapper, source, visible } }
    const layers = {};
    let isInitialized = false;

    function createLayer(layerId) {
        const mapper = vtkMapper.newInstance();
        const actor = vtkActor.newInstance();
        actor.setMapper(mapper);

        layers[layerId] = {
            actor,
            mapper,
            source: null,
            visible: true
        };

        return layers[layerId];
    }

    function loadLayerData(layerId, fileContents) {
        const vtkreader = vtkXMLPolyDataReader.newInstance();
        vtkreader.parseAsArrayBuffer(fileContents);

        const source = vtkreader.getOutputData(0);

        // Create layer if it doesn't exist
        if (!layers[layerId]) {
            createLayer(layerId);
        }

        const layer = layers[layerId];
        layer.source = source;
        layer.mapper.setInputData(source);
        layer.mapper.modified();

        // Add actor to renderer if not already added
        if (!renderer.getActors().includes(layer.actor)) {
            renderer.addActor(layer.actor);
        }

        // Add to pick list
        picker.addPickList(layer.actor);

        return layer;
    }

    function setLayerVisibility(layerId, visible) {
        const layer = layers[layerId];
        if (!layer) return;

        layer.visible = visible;
        layer.actor.setVisibility(visible);
        renderWindow.render();
    }

    function getLayerVisibility(layerId) {
        return layers[layerId]?.visible ?? false;
    }

    function getAllSources() {
        // Return all sources for click detection
        return Object.values(layers)
            .filter(layer => layer.source && layer.visible)
            .map(layer => layer.source);
    }

    async function downloadLayerFromCloud(layerId, filename) {
        try {
            // Step 1: Get signed URL from API
            const response = await fetch(`${API_ENDPOINT}?key=${filename}`);
            if (!response.ok) {
                throw new Error(`Failed to get signed URL for ${filename}: ${response.statusText}`);
            }

            const data = await response.json();
            const signedUrl = data.signedUrl;

            // Step 2: Download the file from S3 using signed URL
            const fileResponse = await fetch(signedUrl);
            if (!fileResponse.ok) {
                throw new Error(`Failed to download ${filename}: ${fileResponse.statusText}`);
            }

            const fileContents = await fileResponse.arrayBuffer();

            // Step 3: Load the layer
            loadLayerData(layerId, fileContents);

        } catch (error) {
            console.error(`Error downloading layer ${layerId}:`, error);
            throw error;
        }
    }

    async function downloadAllLayersFromCloud() {
        try {
            // Download all layers in parallel
            await Promise.all(
                LAYERS.map(layer => downloadLayerFromCloud(layer.id, layer.filename))
            );

            isInitialized = true;

            // Reset camera to show all layers
            renderer.resetCamera();
            renderWindow.render();

            console.log('All layers loaded successfully');
        } catch (error) {
            console.error('Error downloading layers from cloud:', error);
            alert(`Failed to download model from cloud: ${error.message}`);
        }
    }

    function handleFileSelect(event) {
        const files = event.target.files;
        if (!files || files.length === 0) return;

        // Load all selected files
        const loadPromises = Array.from(files).map(file => {
            return new Promise((resolve, reject) => {
                // Extract layer ID from filename (e.g., 'mesh.vtp' -> 'mesh')
                const layerId = file.name.replace('.vtp', '');

                const reader = new FileReader();
                reader.onload = function(e) {
                    try {
                        loadLayerData(layerId, e.target.result);
                        resolve();
                    } catch (error) {
                        reject(error);
                    }
                };
                reader.onerror = reject;
                reader.readAsArrayBuffer(file);
            });
        });

        Promise.all(loadPromises)
            .then(() => {
                isInitialized = true;
                // Reset file input so the same files can be selected again
                event.target.value = '';

                // Reset camera to show all layers
                renderer.resetCamera();
                renderWindow.render();

                console.log('All files loaded successfully');
            })
            .catch(error => {
                console.error('Error loading files:', error);
                alert(`Failed to load files: ${error.message}`);
            });
    }

    // Setup file input listener (allow multiple files)
    const fileInput = document.getElementById('fileInput');
    fileInput.setAttribute('multiple', 'multiple');
    fileInput.addEventListener('change', handleFileSelect);

    // Initialize picker
    picker.initializePickList();

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
}
