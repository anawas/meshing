import vtkXMLPolyDataReader from '@kitware/vtk.js/IO/XML/XMLPolyDataReader';

// ============================================================================
// File Loading
// ============================================================================

const API_ENDPOINT = 'https://xhx5lqfvq1.execute-api.eu-central-1.amazonaws.com/prod/download-url';
const S3_KEY = 'output_scene.vtp';

export function setupFileLoader(dependencies) {
    const { mapper, renderer, actor, picker, renderWindow, setCurrentSource, setActorAdded } = dependencies;
    let actorAdded = false;

    function handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function(e) {
            loadData(e.target.result, file.name);
            // Reset file input so the same file can be selected again
            event.target.value = '';
        };
        reader.readAsArrayBuffer(file);
    }

    function loadData(fileContents, fileName) {
        const vtkreader = vtkXMLPolyDataReader.newInstance();
        vtkreader.parseAsArrayBuffer(fileContents);

        const currentSource = vtkreader.getOutputData(0);
        mapper.setInputData(currentSource);
        setCurrentSource(currentSource);

        // Notify VTK that the mapper has been modified
        mapper.modified();

        if (!actorAdded) {
            renderer.addActor(actor);
            actorAdded = true;
            setActorAdded(true);
        }

        picker.initializePickList();
        picker.addPickList(actor);

        renderer.resetCamera();
        renderWindow.render();
    }

    async function downloadFromCloud() {
        try {
            // Step 1: Get signed URL from API
            const response = await fetch(`${API_ENDPOINT}?key=${S3_KEY}`);
            if (!response.ok) {
                throw new Error(`Failed to get signed URL: ${response.statusText}`);
            }

            const data = await response.json();
            const signedUrl = data.signedUrl;

            // Step 2: Download the file from S3 using signed URL
            const fileResponse = await fetch(signedUrl);
            if (!fileResponse.ok) {
                throw new Error(`Failed to download file: ${fileResponse.statusText}`);
            }

            const fileContents = await fileResponse.arrayBuffer();

            // Step 3: Load and display the model
            loadData(fileContents, S3_KEY);
        } catch (error) {
            console.error('Error downloading from cloud:', error);
            alert(`Failed to download model from cloud: ${error.message}`);
        }
    }

    // Setup file input listener
    const fileInput = document.getElementById('fileInput');
    fileInput.addEventListener('change', handleFileSelect);

    return {
        handleFileSelect,
        loadData,
        downloadFromCloud
    };
}
