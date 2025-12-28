document.addEventListener('DOMContentLoaded', () => {
    // ID from URL path: /progress/{job_id}
    const jobId = window.location.pathname.split('/').pop();

    if (!jobId) {
        alert("Invalid Job ID");
        return;
    }

    const progressCircle = document.getElementById('progress-circle');
    const percentageText = document.getElementById('progress-percentage-text');
    const statusPhase = document.getElementById('status-phase');
    const statusHeadline = document.getElementById('status-headline');
    const statusDetail = document.getElementById('status-detail');

    // Token Counter Simulation
    const tokenCounter = document.getElementById('token-counter');
    const timeElapsed = document.getElementById('time-elapsed');
    let startTime = Date.now();
    let tokenCount = 0;

    // Simulate token count increasing
    setInterval(() => {
        tokenCount += Math.floor(Math.random() * 550);
        if (tokenCounter) tokenCounter.innerText = (tokenCount / 1000).toFixed(1) + 'K';

        const seconds = Math.floor((Date.now() - startTime) / 1000);
        if (timeElapsed) timeElapsed.innerText = seconds + 's';
    }, 200);

    const steps = {
        'news': document.getElementById('step-news'),
        'fundamentals': document.getElementById('step-fundamentals'),
        'signal': document.getElementById('step-signal')
        // Peers is usually part of fundamentals or signal in this simplified view
    };

    function updateStep(element, status) {
        if (!element) return;

        const iconContainer = element.querySelector('.step-icon');
        const icon = element.querySelector('.icon-content');
        const labelText = element.querySelector('.step-label');
        const statusText = element.querySelector('.step-status');
        const progressBar = element.querySelector('.progress-bar');

        // Reset base classes
        iconContainer.className = 'step-icon size-6 flex items-center justify-center rounded-full border transition-all duration-300';
        labelText.className = 'text-xs font-mono step-label transition-colors duration-300';
        statusText.className = 'text-xs font-mono step-status transition-colors duration-300';

        if (status === 'pending') {
            iconContainer.classList.add('border-white/20', 'text-gray-500');
            icon.textContent = 'lock_clock';
            labelText.classList.add('text-gray-500');
            statusText.classList.add('text-gray-500');
            statusText.textContent = 'PENDING';
            progressBar.style.width = '0%';
        } else if (status === 'active') {
            iconContainer.classList.add('border-[#33f20d]', 'text-[#33f20d]', 'animate-pulse');
            icon.textContent = 'sync';
            labelText.classList.add('text-white', 'font-bold');
            statusText.classList.add('text-white');
            statusText.textContent = 'IN PROGRESS';
            progressBar.style.width = '60%'; // Indeterminate visual
            progressBar.classList.add('animate-pulse');
        } else if (status === 'complete') {
            iconContainer.classList.add('bg-[#33f20d]', 'border-[#33f20d]', 'text-black');
            icon.textContent = 'check';
            labelText.classList.add('text-gray-300');
            statusText.classList.add('text-[#33f20d]');
            statusText.textContent = 'COMPLETE';
            progressBar.style.width = '100%';
            progressBar.classList.remove('animate-pulse');
        }
    }

    // Polling Function
    async function checkProgress() {
        try {
            const response = await fetch(`/api/status/${jobId}`);
            if (!response.ok) throw new Error("Status check failed");

            const data = await response.json();

            // Update Ring (283 is circumference)
            const circumference = 283;
            const offset = circumference - (data.progress / 100) * circumference;
            progressCircle.style.strokeDashoffset = offset;

            // Update Text
            percentageText.innerText = `${data.progress}%`;
            statusPhase.innerText = data.current_step.toUpperCase();

            // Update Steps based on progress/state
            // Logic derived from main.py process_analysis function
            // 0-30: News
            // 30-60: Fundamentals
            // 60-80: Peers (Merged into fundamentals visually or signal)
            // 80-100: Signal

            if (data.progress < 30) {
                updateStep(steps['news'], 'active');
                updateStep(steps['fundamentals'], 'pending');
                updateStep(steps['signal'], 'pending');
                statusHeadline.innerText = "Analyzing News Sentiment...";
                statusDetail.innerText = "Scanning global sources for contrarian signals.";
            } else if (data.progress < 60) {
                updateStep(steps['news'], 'complete');
                updateStep(steps['fundamentals'], 'active');
                updateStep(steps['signal'], 'pending');
                statusHeadline.innerText = "Processing Fundamentals...";
                statusDetail.innerText = "Ingesting RAG documents and analyzing financial ratios.";
            } else if (data.progress < 90) {
                updateStep(steps['news'], 'complete');
                updateStep(steps['fundamentals'], 'complete');
                updateStep(steps['signal'], 'active');
                statusHeadline.innerText = "Generating Signal...";
                statusDetail.innerText = "Synthesizing data points to detect market anomalies.";
            } else {
                // All complete
                updateStep(steps['news'], 'complete');
                updateStep(steps['fundamentals'], 'complete');
                updateStep(steps['signal'], 'complete');
            }

            if (data.status === 'completed') {
                statusHeadline.innerText = "Analysis Complete.";
                setTimeout(() => {
                    window.location.href = `/results/${jobId}`;
                }, 1000);
            } else if (data.status === 'failed') {
                statusHeadline.innerText = "Analysis Failed";
                statusDetail.innerText = data.error || "Unknown error occurred.";
                statusDetail.classList.add('text-red-500');
                progressCircle.style.stroke = '#ff2a4d';
            } else {
                // Continue polling
                setTimeout(checkProgress, 1000); // 1 second poll
            }

        } catch (error) {
            console.error("Polling error:", error);
            // Retry anyway
            setTimeout(checkProgress, 3000);
        }
    }

    const abortBtn = document.getElementById('abortBtn');

    if (abortBtn) {
        abortBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            if (confirm("Are you sure you want to stop the analysis?")) {
                try {
                    await fetch(`/api/cancel/${jobId}`, { method: 'POST' });
                    window.location.href = '/';
                } catch (err) {
                    console.error("Cancellation failed", err);
                    alert("Could not cancel job.");
                }
            }
        });
    }

    // Start
    checkProgress();
});
