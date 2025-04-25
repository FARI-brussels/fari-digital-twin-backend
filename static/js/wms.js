document.addEventListener('DOMContentLoaded', function() {
    const wmsForm = document.getElementById('wms-form');
    const layersContainer = document.getElementById('layers-container');
    const layersList = document.getElementById('layers-list');

    wmsForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const wmsUrl = document.getElementById('wms-url').value;
        
        try {
            // Fetch WMS capabilities
            const response = await fetch('/wms/capabilities', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: wmsUrl })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Clear previous layers
            layersList.innerHTML = '';
            
            // Display layers
            data.layers.forEach(layer => {
                const layerElement = createLayerElement(layer);
                layersList.appendChild(layerElement);
            });
            
            // Show layers container
            layersContainer.style.display = 'block';
            
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to load WMS layers. Please check the URL and try again.');
        }
    });
});

function createLayerElement(layer) {
    const div = document.createElement('div');
    div.className = 'layer-item';
    div.innerHTML = `
        <div class="layer-header">
            <span class="layer-name">${layer.name}</span>
            <span class="layer-title">${layer.title}</span>
        </div>
        <div class="layer-description">
            <label for="description-${layer.name}">Description:</label>
            <textarea id="description-${layer.name}" placeholder="Enter layer description..."></textarea>
        </div>
        <button class="save-btn" onclick="saveLayer('${layer.name}')">Send to Database</button>
        <div id="status-${layer.name}" class="status-message"></div>
    `;
    return div;
}

async function saveLayer(layerName) {
    const description = document.getElementById(`description-${layerName}`).value;
    const wmsUrl = document.getElementById('wms-url').value;
    const statusDiv = document.getElementById(`status-${layerName}`);
    const saveBtn = statusDiv.previousElementSibling;
    
    try {
        saveBtn.disabled = true;
        statusDiv.textContent = 'Processing...';
        statusDiv.className = 'status-message';
        
        const response = await fetch('/wms/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                layer_name: layerName,
                description: description,
                wms_url: wmsUrl
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.status === 'success') {
            statusDiv.textContent = 'Layer saved successfully!';
            statusDiv.className = 'status-message success-message';
            console.log('WMS info:', result.wms_info);
        } else {
            throw new Error(result.message || 'Failed to save layer');
        }
        
    } catch (error) {
        console.error('Error:', error);
        statusDiv.textContent = error.message || 'Failed to save layer';
        statusDiv.className = 'status-message error-message';
    } finally {
        saveBtn.disabled = false;
    }
} 