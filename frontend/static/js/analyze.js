document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('analysisForm');
    const fileInput = document.getElementById('mainReport');
    const fileZone = document.getElementById('mainDropZone');
    const addPeerBtn = document.getElementById('addPeerBtn');
    const peersContainer = document.getElementById('peersList');
    const submitBtn = document.getElementById('submitBtn');

    // Drag and Drop
    fileZone.addEventListener('click', () => fileInput.click());

    fileZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileZone.classList.add('border-primary');
    });

    fileZone.addEventListener('dragleave', () => {
        fileZone.classList.remove('border-primary');
    });

    fileZone.addEventListener('drop', (e) => {
        e.preventDefault();
        fileZone.classList.remove('border-primary');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            updateFileName(fileInput.files[0].name);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            updateFileName(fileInput.files[0].name);
        }
    });

    function updateFileName(name) {
        // Show file info in the separate div, NOT overwriting the dropzone
        const infoDiv = document.getElementById('mainFileInfo');
        infoDiv.style.display = 'block';
        infoDiv.innerHTML = `<p class="text-sm text-gray-600">Selected: <strong>${name}</strong></p>`;

        // Add visual cue to dropzone
        fileZone.style.borderColor = 'var(--primary-color)';
        fileZone.style.backgroundColor = '#EFF6FF';

        validateForm();
    }

    // Dynamic Peers
    addPeerBtn.addEventListener('click', () => {
        if (peersContainer.children.length >= 3) return;

        const div = document.createElement('div');
        div.className = 'flex gap-2 mb-2 peer-entry';
        div.innerHTML = `
            <input type="text" name="peers" placeholder="Competitor Name" class="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
            <button type="button" class="text-red-500 hover:text-red-700 remove-peer">&times;</button>
        `;
        peersContainer.appendChild(div);

        // Add remove listener
        div.querySelector('.remove-peer').addEventListener('click', () => {
            div.remove();
        });
    });

    // Form Validation
    const companyInput = document.getElementById('companyName');
    [companyInput, fileInput].forEach(el => {
        el.addEventListener('input', validateForm);
        el.addEventListener('change', validateForm);
    });

    function validateForm() {
        // Simple check
        const isValid = companyInput.value.trim() && fileInput.files.length > 0;

        if (isValid) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('bg-gray-400', 'cursor-not-allowed');
            submitBtn.classList.add('bg-blue-600', 'hover:bg-blue-700');
        } else {
            submitBtn.disabled = true;
            submitBtn.classList.add('bg-gray-400', 'cursor-not-allowed');
            submitBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
        }
    }

    // Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        submitBtn.disabled = true;
        submitBtn.textContent = 'Uploading...';

        const formData = new FormData(form);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (response.ok) {
                window.location.href = `/progress/${data.job_id}`;
            } else {
                alert('Analysis failed: ' + (data.detail || 'Unknown error'));
                submitBtn.disabled = false;
                submitBtn.textContent = 'Start Analysis';
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Start Analysis';
        }
    });

    // Initial check
    validateForm();
});
