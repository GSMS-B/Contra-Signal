document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('analysisForm');
    const companyInput = document.getElementById('ticker'); // Changed ID from companyName
    const fileInput = document.getElementById('mainReport');
    const fileZone = document.getElementById('mainDropZone');
    const submitBtn = document.getElementById('submitBtn');
    const fileInfo = document.getElementById('fileInfo');

    // Drag and Drop Logic
    fileZone.addEventListener('click', (e) => {
        // Prevent recursive clicking if clicking on the input itself (though it's hidden)
        if (e.target !== fileInput) {
            fileInput.click();
        }
    });

    fileZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileZone.classList.add('border-primary', 'bg-black/40');
        fileZone.classList.remove('bg-black/20');
    });

    fileZone.addEventListener('dragleave', () => {
        fileZone.classList.remove('border-primary', 'bg-black/40');
        fileZone.classList.add('bg-black/20');
    });

    fileZone.addEventListener('drop', (e) => {
        e.preventDefault();
        fileZone.classList.remove('border-primary', 'bg-black/40');
        fileZone.classList.add('bg-black/20');
        
        if (e.dataTransfer.files.length) {
            // Only accept PDF
            const file = e.dataTransfer.files[0];
            if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
                fileInput.files = e.dataTransfer.files;
                updateFileName(file.name);
            } else {
                alert("Please upload a PDF file only.");
            }
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            updateFileName(fileInput.files[0].name);
        }
    });

    function updateFileName(name) {
        // Show file info
        fileInfo.classList.remove('hidden');
        fileInfo.textContent = `SELECTED: ${name}`;
        
        // Visual cue on dropzone
        fileZone.classList.add('border-primary');
        validateForm();
    }

    // Form Validation (Simple check as requested)
    [companyInput, fileInput].forEach(el => {
        el.addEventListener('input', validateForm);
        el.addEventListener('change', validateForm);
    });

    function validateForm() {
        const hasCompany = companyInput.value.trim().length > 0;
        const hasFile = fileInput.files.length > 0;
        
        if (hasCompany && hasFile) {
            submitBtn.disabled = false;
        } else {
            submitBtn.disabled = true;
        }
    }

    // Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Visual feedback
        submitBtn.disabled = true;
        const btnContent = submitBtn.querySelector('span'); // The span with text and icon
        const originalContent = btnContent.innerHTML;
        btnContent.innerHTML = `<span class="material-symbols-outlined animate-spin">refresh</span> UPLOADING...`;

        const formData = new FormData(form);
        // Ensure company_name is set (input name="company_name" in HTML handles this automatically)
        
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                // Redirect to progress page
                window.location.href = `/progress/${data.job_id}`;
            } else {
                alert('Analysis initiation failed: ' + (data.detail || 'Unknown error'));
                submitBtn.disabled = false;
                btnContent.innerHTML = originalContent;
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Network or Server Error.');
            submitBtn.disabled = false;
            btnContent.innerHTML = originalContent;
        }
    });

    // Initial check
    validateForm();
});
