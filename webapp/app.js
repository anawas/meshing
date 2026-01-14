import '@kitware/vtk.js/Rendering/Profiles/Geometry';
import vtkFullScreenRenderWindow from '@kitware/vtk.js/Rendering/Misc/FullScreenRenderWindow';
import vtkActor from '@kitware/vtk.js/Rendering/Core/Actor';
import vtkMapper from '@kitware/vtk.js/Rendering/Core/Mapper';
import vtkInteractorStyleManipulator from '@kitware/vtk.js/Interaction/Style/InteractorStyleManipulator';
import Presets from '@kitware/vtk.js/Interaction/Style/InteractorStyleManipulator/Presets';
import vtkCellPicker from '@kitware/vtk.js/Rendering/Core/CellPicker';
import { setupFileLoader } from './fileLoader.js';

// ============================================================================
// Constants
// ============================================================================

const ROLE_CODES = {
    NONE: 0,
    START: 1,
    INTERMEDIATE: 2,
    END: 3
};

const ROLE_LABELS = {
    [ROLE_CODES.START]: 'Startpunkt',
    [ROLE_CODES.END]: 'Endpunkt',
    [ROLE_CODES.INTERMEDIATE]: 'Zwischenpunkt'
};

const REPRESENTATION_MODES = {
    WIREFRAME: 1,
    SURFACE: 2
};

const TOOLTIP_OFFSET = 5;
const PICKER_TOLERANCE = 0.1;

// ============================================================================
// VTK.js Setup
// ============================================================================

const fullScreenRenderer = vtkFullScreenRenderWindow.newInstance({
    container: document.getElementById('container')
});
const renderer = fullScreenRenderer.getRenderer();
const renderWindow = fullScreenRenderer.getRenderWindow();
const interactor = renderWindow.getInteractor();

// Configure interaction style
const interactorStyle = vtkInteractorStyleManipulator.newInstance();
interactor.setInteractorStyle(interactorStyle);

const interactorStyleDefinitions = [
    { type: 'rotate', options: { button: 1 } },
    { type: 'roll', options: { button: 1, shift: true } },
    { type: 'pan', options: { button: 3 } },
    { type: 'zoom', options: { dragEnabled: false, scrollEnabled: true } }
];

Presets.applyDefinitions(interactorStyleDefinitions, interactorStyle);

// Setup cell picker
const picker = vtkCellPicker.newInstance();
picker.setPickFromList(1);
picker.setTolerance(PICKER_TOLERANCE);

// ============================================================================
// State
// ============================================================================

let actor = null;
let mapper = null;
let currentSource = null;
let actorAdded = false;
let wireframeMode = false;

// Setup mapper and actor
mapper = vtkMapper.newInstance();
actor = vtkActor.newInstance();
actor.setMapper(mapper);

// ============================================================================
// Helper Functions
// ============================================================================

function hideMetadata() {
    const metadataDiv = document.getElementById('metadata');
    metadataDiv.style.display = 'none';
}

function getRoleLabel(roleCode) {
    return ROLE_LABELS[roleCode] || 'Unbekannt';
}

function isSphere(vertexIndex, cellId) {
    if (!vertexIndex) return false;
    return vertexIndex.getData()[cellId] >= 0;
}

function getCellValue(array, cellId) {
    return array ? array.getData()[cellId] : null;
}

function positionTooltip(element, mousePos) {
    // Convert VTK.js device pixels to CSS pixels
    const dpr = window.devicePixelRatio || 1;
    const cssX = mousePos.x / dpr;
    const cssY = mousePos.y / dpr;

    // VTK.js uses bottom-left origin, CSS uses top-left, so invert Y
    let left = cssX + TOOLTIP_OFFSET;
    let top = window.innerHeight - cssY + TOOLTIP_OFFSET;

    // Keep tooltip within viewport
    const rect = element.getBoundingClientRect();

    if (left + rect.width > window.innerWidth) {
        left = cssX - rect.width - TOOLTIP_OFFSET;
    }

    if (top + rect.height > window.innerHeight) {
        top = window.innerHeight - cssY - rect.height - TOOLTIP_OFFSET;
    }

    element.style.left = `${left}px`;
    element.style.top = `${top}px`;
}

function buildMetadataText(cellId, cellData) {
    const radius = cellData.getArrayByName('radius');
    const vertexIndex = cellData.getArrayByName('vertex_index');
    const pathPosition = cellData.getArrayByName('path_position');
    const roleCode = cellData.getArrayByName('role_code');

    let text = '<strong>Metadaten:</strong>';

    const vIndex = getCellValue(vertexIndex, cellId);
    if (vIndex !== null) {
        text += `<br>Vertex Index: ${vIndex}`;
    }

    const position = getCellValue(pathPosition, cellId);
    if (position !== null) {
        text += `<br>Position im Pfad: ${position}`;
    }

    const rad = getCellValue(radius, cellId);
    if (rad !== null) {
        text += `<br>Radius: ${rad}`;
    }

    const role = getCellValue(roleCode, cellId);
    if (role !== null) {
        text += `<br>Rolle: ${getRoleLabel(role)}`;
    }

    return text;
}

// ============================================================================
// File Loading Setup
// ============================================================================

const fileLoader = setupFileLoader({
    mapper,
    renderer,
    actor,
    picker,
    renderWindow,
    setCurrentSource: (source) => { currentSource = source; },
    setActorAdded: (added) => { actorAdded = added; }
});

// Expose downloadFromCloud to window for HTML button onclick
window.downloadFromCloud = fileLoader.downloadFromCloud;

// ============================================================================
// Interaction Handlers
// ============================================================================

function handleClick(callData) {
    if (!actorAdded || !currentSource) return;

    const pos = callData.position;
    const point = [pos.x, pos.y, 0.0];

    picker.pick(point, renderer);

    if (picker.getActors().length > 0) {
        const cellId = picker.getCellId();
        if (cellId !== -1) {
            displayMetadata(cellId, pos);
        }
    } else {
        hideMetadata();
    }
}

function displayMetadata(cellId, mousePos) {
    const cellData = currentSource.getCellData();
    const metadataDiv = document.getElementById('metadata');

    const vertexIndex = cellData.getArrayByName('vertex_index');

    // Only show metadata for spheres (vertex_index >= 0)
    if (!isSphere(vertexIndex, cellId)) {
        hideMetadata();
        return;
    }

    metadataDiv.innerHTML = buildMetadataText(cellId, cellData);
    metadataDiv.style.display = 'block';
    positionTooltip(metadataDiv, mousePos);
}

// Register click handler
interactor.onLeftButtonPress((callData) => {
    const isDragging = callData.controlKey || callData.shiftKey;
    if (!isDragging) {
        handleClick(callData);
    }
});

// ============================================================================
// UI Controls
// ============================================================================

window.resetCamera = function() {
    if (actorAdded) {
        renderer.resetCamera();
        renderWindow.render();
    }
};

window.toggleWireframe = function() {
    if (actorAdded) {
        wireframeMode = !wireframeMode;
        const mode = wireframeMode ? REPRESENTATION_MODES.WIREFRAME : REPRESENTATION_MODES.SURFACE;
        actor.getProperty().setRepresentation(mode);
        renderWindow.render();
    }
};

// ============================================================================
// Initialization
// ============================================================================
// File input listener is set up in fileLoader.js
