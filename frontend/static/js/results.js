
document.addEventListener('DOMContentLoaded', async () => {
    // 1. Get Job ID
    const pathParts = window.location.pathname.split('/');
    const jobId = pathParts[pathParts.length - 1];

    if (!jobId) {
        alert('Invalid Job ID');
        return;
    }

    // 2. Fetch Data
    try {
        const response = await fetch(`/api/status/${jobId}`);
        const jobData = await response.json();

        if (jobData.status !== 'completed' || !jobData.result) {
            console.error('Job status check failed:', jobData);
            alert('Analysis not ready or failed.');
            return;
        }

        console.log("--------------------------------------------------");
        console.log("✅ DATA RECEIVED FROM BACKEND:");
        console.log(jobData.result);
        console.log("--------------------------------------------------");

        renderResults(jobData.result);

    } catch (error) {
        console.error('Error fetching results:', error);
        alert('Failed to load results.');
    }

    // 3. Render Logic
    function renderResults(data) {
        const { company_name, analysis_date, news, fundamentals, peers, signal } = data;

        // --- Header ---
        try {
            document.getElementById('companyTicker').textContent = company_name.toUpperCase();
            document.getElementById('companyName').textContent = "Unknown Sector"; // Default fallback
            // Use regex to try to find a ticker in the name if possible, otherwise leave generic
            if (company_name.includes('(')) {
                const match = company_name.match(/\((.*?)\)/);
                if (match) {
                    document.getElementById('companyTicker').textContent = match[1];
                    document.getElementById('companyName').textContent = company_name.split('(')[0];
                }
            }

            document.getElementById('analysisDate').textContent = new Date(analysis_date).toLocaleDateString() + " " + new Date(analysis_date).toLocaleTimeString();

            // Contrarian Score
            document.getElementById('contrarianScore').textContent = signal.signal_strength * 10; // Convert 1-10 to 1-100

            const sigType = (signal.signal_type || 'Hold');
            const sigElem = document.getElementById('signalType');
            sigElem.textContent = sigType.toUpperCase().replace('_', ' ');

            // Color code signal
            if (sigType.toLowerCase().includes('buy')) sigElem.style.color = '#33f20d';
            else if (sigType.toLowerCase().includes('avoid')) sigElem.style.color = '#ef4444';
            else sigElem.style.color = '#fbbf24';

        } catch (e) { console.error("Error rendering Header:", e); }

        // --- Market Psyche (Gauge) ---
        try {
            const score = news.score; // -10 to +10
            // Map -10 -> -90deg, +10 -> +90deg
            const rotation = (score * 9);
            const needle = document.getElementById('marketGaugeNeedle');
            if (needle) {
                // Initial rotation is -90 (pointing left? No, standard is 0 up).
                // CSS set initial to -90 (left). We want fear (left) to greed (right).
                // If CSS start is -90deg (bottom-left?), let's adjust.
                // Standard semi-circle gauge: 
                // Left (-10) = -90deg, Right (+10) = +90deg.
                // 0 = 0deg (Vertical).
                needle.style.transform = `translateX(-50%) rotate(${rotation}deg)`;
            }

            const textElem = document.getElementById('marketPsycheText');
            if (score < -3) { textElem.textContent = "Fear"; textElem.classList.add('danger-text'); }
            else if (score > 3) { textElem.textContent = "Greed"; textElem.classList.add('neon-text'); }
            else { textElem.textContent = "Neutral"; textElem.style.color = "gray"; }

            document.getElementById('marketPsycheSignal').textContent = `Sentiment Score: ${score}/10`;

        } catch (e) { console.error("Error rendering Gauge:", e); }

        // --- News Sentiment Analysis ---
        try {
            const total = news.positive_count + news.negative_count + news.neutral_count || 1;

            const posPct = Math.round((news.positive_count / total) * 100);
            const negPct = Math.round((news.negative_count / total) * 100);
            const neuPct = Math.round((news.neutral_count / total) * 100);

            document.getElementById('newsPosBar').style.width = `${posPct}%`;
            document.getElementById('newsPosText').textContent = `${posPct}%`;

            document.getElementById('newsNegBar').style.width = `${negPct}%`;
            document.getElementById('newsNegText').textContent = `${negPct}%`;

            document.getElementById('newsNeuBar').style.width = `${neuPct}%`;
            document.getElementById('newsNeuText').textContent = `${neuPct}%`;

            // Headlines Capsules
            const headlinesGrid = document.getElementById('newsHeadlinesGrid');
            headlinesGrid.innerHTML = '';

            const headlines = Array.isArray(news.headlines) ? news.headlines : [];
            // We don't have sentiment per headline in the schema, using random assignment for visual variety or neutral default?
            // User requested coloring: Green (Pos), Red (Neg), Gray (Neu).
            // Since we don't have granular analysis per headline here, we will infer or cycle colors.
            // A "Senior" way is to do simple sentiment keyword matching on the headline itself.

            headlines.slice(0, 8).forEach(h => {
                let colorClass = 'text-gray-400 border-white/5 bg-[#1e293b]'; // Default
                const lower = h.toLowerCase();
                if (lower.includes('gain') || lower.includes('up') || lower.includes('rally') || lower.includes('high') || lower.includes('growth')) {
                    colorClass = 'text-primary border-primary/20 bg-primary/10';
                } else if (lower.includes('loss') || lower.includes('down') || lower.includes('crash') || lower.includes('risk') || lower.includes('miss')) {
                    colorClass = 'text-danger border-danger/20 bg-danger/10';
                }

                const span = document.createElement('span');
                span.className = `px-3 py-1.5 rounded-full border text-xs font-mono hover:bg-white/5 cursor-default transition-colors ${colorClass}`;
                span.textContent = h.length > 40 ? h.substring(0, 40) + '...' : h;
                headlinesGrid.appendChild(span);
            });

        } catch (e) { console.error("Error rendering News:", e); }

        // --- Peer Comparison (Radar SVG) ---
        try {
            // Draw a polygon based on the 5 metrics: 
            // 1. Growth, 2. Margin, 3. ROE, 4. Debt (inverted), 5. Strength

            // Normalize values 0-100 for the chart radius (max 80px)
            const p1 = Math.min(Math.max(fundamentals.revenue_growth * 2, 20), 100); // Growth
            const p2 = Math.min(Math.max(fundamentals.profit_margin * 2, 20), 100); // Margin
            const p3 = Math.min(Math.max(fundamentals.roe * 2, 20), 100); // ROE
            const p4 = 100 - Math.min(Math.max(parseFloat(fundamentals.debt_to_equity) * 20, 0), 100); // Low Debt = High Score
            const p5 = fundamentals.health_score * 10; // Strength

            // Angles: 0(Top), 72, 144, 216, 288
            // Center (100, 100), Max Radius 80.
            function getPoint(val, angleDeg) {
                const angleRad = (angleDeg - 90) * Math.PI / 180;
                const r = (val / 100) * 80;
                const x = 100 + r * Math.cos(angleRad);
                const y = 100 + r * Math.sin(angleRad);
                return `${x},${y}`;
            }

            const points = [
                getPoint(p1, 0),
                getPoint(p2, 72),
                getPoint(p3, 144),
                getPoint(p4, 216),
                getPoint(p5, 288)
            ].join(' ');

            const poly = document.getElementById('peerRadarPolygon');
            if (poly) {
                poly.setAttribute('points', points);
            }

        } catch (e) { console.error("Error rendering Peer Radar:", e); }

        // --- Fundamental Strength ---
        try {
            document.getElementById('fundHealthScore').textContent = `${fundamentals.health_score}/10`;
            document.getElementById('fundGrowth').textContent = `${fundamentals.revenue_growth}%`;
            document.getElementById('fundMargin').textContent = `${fundamentals.profit_margin}%`;
            document.getElementById('fundROE').textContent = `${fundamentals.roe}%`;
            document.getElementById('fundDebt').textContent = fundamentals.debt_to_equity;
        } catch (e) { console.error("Error rendering Fundamentals:", e); }

        // --- Investment Thesis ---
        try {
            // Opportunity
            const oppList = document.getElementById('thesisOpportunity');
            oppList.innerHTML = '';
            (signal.opportunity_reasons || []).forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                oppList.appendChild(li);
            });

            // Management Outlook
            document.getElementById('thesisOutlook').textContent = signal.management_outlook || "N/A";

            // Future
            document.getElementById('thesisFuture').textContent = signal.future_development || "N/A";

            // Risks
            const risksList = document.getElementById('thesisRisks');
            risksList.innerHTML = '';
            (signal.risk_factors || []).forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                risksList.appendChild(li);
            });

            // Competitive Moats
            const moatsList = document.getElementById('moatsList');
            if (moatsList) {
                moatsList.innerHTML = '';
                const moats = signal.competitive_moats || ["Analysis pending..."];
                moats.forEach(item => {
                    const li = document.createElement('li');
                    li.className = "flex gap-3 text-sm text-gray-300";
                    li.innerHTML = `
                        <span class="material-symbols-outlined text-primary text-[16px] mt-0.5">check_circle</span>
                        <span>${item}</span>
                    `;
                    moatsList.appendChild(li);
                });
            }

        } catch (e) { console.error("Error rendering Thesis/Moats:", e); }
    }

    // 4. Chat Interactions
    // Use the existing element IDs
    const chatInput = document.getElementById('questionInput');
    const askBtn = document.getElementById('askBtn');
    const chatHistory = document.getElementById('chatHistory');
    const downloadBtn = document.getElementById('downloadReportBtn');

    if (downloadBtn) {
        downloadBtn.addEventListener('click', () => window.print());
    }

    async function askQuestion(q) {
        if (!q) return;

        appendMessage('user', q);
        chatInput.value = '';

        try {
            // Show typing indicator?
            // appendMessage('bot', 'Typing...');

            const res = await fetch(`/api/ask/${jobId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: q })
            });
            const data = await res.json();

            // Remove typing indicator logic if added
            appendMessage('bot', data.answer);
        } catch (err) {
            console.error(err);
            appendMessage('bot', 'Connection error.');
        }
    }

    function appendMessage(role, text) {
        // Create matching bubbles based on Bento template style
        // Template uses:
        // Bot: w-8 h-8 rounded-full bg-[#1e293b] ...
        // User: flex-row-reverse ...

        const wrapper = document.createElement('div');
        wrapper.className = `flex gap-4 ${role === 'user' ? 'flex-row-reverse' : ''}`;

        const iconDiv = document.createElement('div');
        iconDiv.className = `w-8 h-8 rounded-full ${role === 'user' ? 'bg-primary' : 'bg-[#1e293b]'} flex items-center justify-center shrink-0 border border-white/10`;
        const iconSpan = document.createElement('span');
        iconSpan.className = `material-symbols-outlined text-[16px] ${role === 'user' ? 'text-black' : 'text-primary'}`;
        iconSpan.textContent = role === 'user' ? 'person' : 'smart_toy';
        iconDiv.appendChild(iconSpan);

        const contentDiv = document.createElement('div');
        contentDiv.className = `flex flex-col gap-1 max-w-[80%] ${role === 'user' ? 'items-end' : ''}`;

        const nameSpan = document.createElement('span');
        nameSpan.className = "text-xs text-gray-500 font-mono";
        nameSpan.textContent = role === 'user' ? "You" : "Contra.AI";

        const msgBubble = document.createElement('div');
        if (role === 'user') {
            msgBubble.className = "bg-primary/10 border border-primary/20 p-4 rounded-2xl rounded-tr-none text-sm text-white leading-relaxed shadow-glow-sm";
        } else {
            msgBubble.className = "bg-[#1e293b]/50 border border-white/5 p-4 rounded-2xl rounded-tl-none text-sm text-gray-200 leading-relaxed shadow-sm";
        }

        const p = document.createElement('p');
        p.textContent = text;
        msgBubble.appendChild(p);

        contentDiv.appendChild(nameSpan);
        contentDiv.appendChild(msgBubble);

        wrapper.appendChild(iconDiv);
        wrapper.appendChild(contentDiv);

        chatHistory.appendChild(wrapper);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    if (askBtn) askBtn.addEventListener('click', () => askQuestion(chatInput.value));
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') askQuestion(chatInput.value);
        });
    }
});
