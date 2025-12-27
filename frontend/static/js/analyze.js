document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const form = document.getElementById('analysisForm');
    const companyInput = document.getElementById('ticker');
    const fileInput = document.getElementById('mainReport');
    const fileZone = document.getElementById('mainDropZone'); // This is the <label>
    const submitBtn = document.getElementById('submitBtn');
    const suggestionsList = document.getElementById('ticker-suggestions');
    const readyIndicator = document.getElementById('companyReadyIndicator');

    // Store original content to restore it later
    // We target the first child div which contains the visual elements
    const originalContent = fileZone ? fileZone.firstElementChild.innerHTML : '';

    if (!form || !companyInput || !fileInput || !fileZone || !submitBtn) {
        console.error("Critical elements missing in DOM");
        return;
    }

    // --- Autocomplete Logic ---
    let debounceTimer;
    let isTickerValid = false;

    companyInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        // INVALIDATE on any typing
        isTickerValid = false;
        if (readyIndicator) readyIndicator.classList.remove('opacity-100');
        validateForm();

        clearTimeout(debounceTimer);

        if (query.length < 2) {
            hideSuggestions();
            return;
        }

        debounceTimer = setTimeout(async () => {
            try {
                const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const matches = await res.json();
                renderSuggestions(matches);
            } catch (err) {
                console.error("Search failed", err);
            }
        }, 300);
    });

    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!companyInput.contains(e.target) && !suggestionsList.contains(e.target)) {
            hideSuggestions();
        }
    });

    function renderSuggestions(matches) {
        suggestionsList.innerHTML = '';
        if (!matches || matches.length === 0) {
            hideSuggestions();
            return;
        }

        matches.forEach(name => {
            const li = document.createElement('li');
            li.className = "px-6 py-3 cursor-pointer hover:bg-white/5 transition-colors text-gray-300 hover:text-primary font-mono text-sm flex items-center gap-2";
            li.innerHTML = `<span class="material-symbols-outlined text-xs opacity-50">show_chart</span> ${name}`;

            li.addEventListener('click', () => {
                companyInput.value = name;

                // VALIDATE on click
                isTickerValid = true;
                if (readyIndicator) readyIndicator.classList.add('opacity-100');

                hideSuggestions();
                validateForm();
            });
            suggestionsList.appendChild(li);
        });

        showSuggestions();
    }

    function showSuggestions() {
        suggestionsList.classList.remove('hidden');
    }

    function hideSuggestions() {
        suggestionsList.classList.add('hidden');
    }
    // -----------------------

    // 1. Drag and Drop Logic
    // Prevent default behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight styles
    ['dragenter', 'dragover'].forEach(eventName => {
        fileZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        fileZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        fileZone.classList.add('border-primary', 'bg-black/40', 'shadow-[inset_0_0_20px_rgba(51,242,13,0.1)]');
        fileZone.classList.remove('bg-black/20');
    }

    function unhighlight(e) {
        fileZone.classList.remove('border-primary', 'bg-black/40', 'shadow-[inset_0_0_20px_rgba(51,242,13,0.1)]');
        fileZone.classList.add('bg-black/20');
    }

    // Handle Drop
    fileZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) {
            fileInput.files = files; // Assign files to input
            handleFiles(files);
        }
    });

    // Handle File Input Change (Click selection)
    fileInput.addEventListener('change', function () {
        if (this.files.length) {
            handleFiles(this.files);
        }
    });

    function handleFiles(files) {
        const file = files[0];
        if (file && (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf'))) {
            updateFileDisplay(file);
        } else {
            alert("Please upload a PDF file only.");
            resetFile();
        }
    }

    function updateFileDisplay(file) {
        const contentDiv = fileZone.firstElementChild;
        if (!contentDiv) return;

        if (file) {
            // Active State
            fileZone.classList.add('border-primary', 'bg-primary/5');
            fileZone.classList.remove('border-gray-700');

            contentDiv.innerHTML = `
                 <div class="flex flex-col items-center justify-center pt-5 pb-6 text-center w-full h-full relative z-20 pointer-events-none">
                    <div class="flex items-center gap-3 text-[#33f20d] font-bold bg-[#33f20d]/10 px-6 py-3 rounded-full border border-[#33f20d]/30 pointer-events-auto">
                        <span class="material-symbols-outlined">description</span>
                        <span class="truncate max-w-[200px]">${file.name}</span>
                        <div id="removeFileBtn" class="ml-2 hover:bg-[#33f20d]/20 rounded-full p-1 transition-colors flex items-center justify-center cursor-pointer">
                            <span class="material-symbols-outlined text-sm text-red-400">close</span>
                        </div>
                    </div>
                    <p class="text-xs text-gray-500 font-mono mt-2">READY TO SCAN</p>
                </div>
            `;

            // Re-attach listener to the new remove button
            // Use setTimeout to ensure DOM is updated
            setTimeout(() => {
                const removeBtn = document.getElementById('removeFileBtn');
                if (removeBtn) {
                    removeBtn.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation(); // Stop bubbling so Label click isn't triggered
                        resetFile();
                    });
                }
            }, 0);

        } else {
            // Default State
            resetUI();
        }
        validateForm();
    }

    function resetFile() {
        fileInput.value = ''; // Clear input
        resetUI();
        validateForm();
    }

    function resetUI() {
        const contentDiv = fileZone.firstElementChild;
        if (!contentDiv) return;

        fileZone.classList.remove('border-primary', 'bg-primary/5');
        fileZone.classList.add('border-gray-700');

        // Restore original HTML content
        contentDiv.innerHTML = originalContent;

        // Ensure "fileInfo" is hidden if it was in the original content
        const fileInfo = document.getElementById('fileInfo');
        if (fileInfo) fileInfo.classList.add('hidden');
    }

    // 2. Validation Logic
    [companyInput, fileInput].forEach(el => {
        // NOTE: We don't use 'input' listener here for companyInput anymore 
        // because we handle it in the debounce logic above, but keeping fileInput checks is fine.
        // Actually, we just need to ensure validateForm is called.
        // It is called in the debounce input handler, so we can leave fileInput here.
        if (el === fileInput) {
            el.addEventListener('change', validateForm);
        }
    });

    function validateForm() {
        // STRICT CHECK: isTickerValid must be true
        const hasCompany = isTickerValid;
        // Check files length
        const hasFile = fileInput.files && fileInput.files.length > 0;

        if (hasCompany && hasFile) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            submitBtn.classList.add('shadow-neon', 'hover:scale-105');
        } else {
            submitBtn.disabled = true;
            submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
            submitBtn.classList.remove('shadow-neon', 'hover:scale-105');
        }
    }

    // 3. Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        submitBtn.disabled = true;
        const btnContent = submitBtn.querySelector('span'); // The span wrapping text
        const originalBtnHTML = btnContent.innerHTML;

        btnContent.innerHTML = `<span class="material-symbols-outlined animate-spin">refresh</span> UPLOADING...`;

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
                btnContent.innerHTML = originalBtnHTML;
            }
        } catch (error) {
            console.error(error);
            alert('Server Error. Check console.');
            submitBtn.disabled = false;
            btnContent.innerHTML = originalBtnHTML;
        }
    });

    // Initial check
    validateForm();
});
