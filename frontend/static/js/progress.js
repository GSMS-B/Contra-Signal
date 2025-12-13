document.addEventListener('DOMContentLoaded', () => {
    const pathParts = window.location.pathname.split('/');
    const jobId = pathParts[pathParts.length - 1];
    const companyName = sessionStorage.getItem('analyzing_company') || 'Company';

    document.getElementById('pageTitle').textContent = `Analyzing ${companyName}...`;

    const tips = [
        "Warren Buffett loves to buy quality companies when they are on the operating table.",
        "The best opportunities come when panic selling hits strong businesses.",
        "Price is what you pay. Value is what you get.",
        "Be fearful when others are greedy, and greedy when others are fearful."
    ];
    document.getElementById('didYouKnow').textContent = tips[Math.floor(Math.random() * tips.length)];

    if (!jobId) {
        alert('No Job ID found');
        window.location.href = '/analyze';
        return;
    }

    const steps = {
        'news': document.getElementById('step_news'),
        'fundamentals': document.getElementById('step_fundamentals'),
        'peers': document.getElementById('step_peers'),
        'signal': document.getElementById('step_signal')
    };

    // Poll status
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${jobId}`);
            const data = await response.json();

            console.log(`[Polling] Status: ${data.status}, Progress: ${data.progress}%`);

            // Update Progress Bar
            document.getElementById('progressBar').style.width = `${data.progress}%`;

            // Update Steps
            // Logic: Mark all previous steps as done, current as active
            const stepOrder = ['news', 'fundamentals', 'peers', 'signal'];
            let currentFound = false;

            stepOrder.forEach(stepKey => {
                const el = steps[stepKey];
                if (!el) return;

                if (data.status === 'completed') {
                    markComplete(el);
                } else if (data.status === 'failed') {
                    el.classList.add('error'); // Add error style if needed
                } else {
                    // Running
                    if (stepKey === data.current_step) {
                        markActive(el);
                        currentFound = true;
                    } else if (!currentFound) {
                        markComplete(el);
                    } else {
                        markPending(el);
                    }
                }
            });

            if (data.status === 'completed') {
                clearInterval(pollInterval);
                setTimeout(() => {
                    window.location.href = `/results/${jobId}`;
                }, 1000);
            } else if (data.status === 'failed') {
                clearInterval(pollInterval);
                alert(`Analysis failed: ${data.error}`);
                window.location.href = '/analyze';
            }

        } catch (error) {
            console.error('Polling error', error);
        }
    }, 2000);

    function markComplete(el) {
        el.className = 'step-item completed';
        el.querySelector('.step-icon').textContent = '✓';
    }

    function markActive(el) {
        el.className = 'step-item active';
        el.querySelector('.step-icon').textContent = '⏳';
    }

    function markPending(el) {
        el.className = 'step-item pending';
        el.querySelector('.step-icon').textContent = '○';
    }
});
