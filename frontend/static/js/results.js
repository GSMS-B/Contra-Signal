
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
            // Use sector + name fallback
            const sector = fundamentals.sector || "Unknown Sector";
            let displayName = company_name;
            if (company_name.includes('(')) {
                displayName = company_name.split('(')[0];
            }
            document.getElementById('companyName').textContent = `${sector} | ${displayName}`;

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
                needle.style.transform = `translateX(-50%) rotate(${rotation}deg)`;
            }

            const textElem = document.getElementById('marketPsycheText');
            if (score <= -3) { textElem.textContent = "Fear"; textElem.classList.add('danger-text'); }
            else if (score >= 3) { textElem.textContent = "Greed"; textElem.classList.add('neon-text'); }
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
            // FIX: Make positive text white for visibility on green
            document.getElementById('newsPosText').classList.add('text-white');
            document.getElementById('newsPosText').classList.remove('text-black'); // ensure

            document.getElementById('newsNegBar').style.width = `${negPct}%`;
            document.getElementById('newsNegText').textContent = `${negPct}%`;

            document.getElementById('newsNeuBar').style.width = `${neuPct}%`;
            document.getElementById('newsNeuText').textContent = `${neuPct}%`;

            // Headlines Capsules (Top 5)
            const headlinesGrid = document.getElementById('newsHeadlinesGrid');
            headlinesGrid.innerHTML = '';

            const headlines = Array.isArray(news.headlines) ? news.headlines : [];

            // Helper for class and text
            const getHeadlineData = (item) => {
                let sentiment = 'neutral';
                let text = '';

                if (typeof item === 'string') {
                    text = item;
                    // Fallback heuristic for legacy data
                    const lower = text.toLowerCase();
                    if (lower.includes('gain') || lower.includes('up') || lower.includes('rally') || lower.includes('high') || lower.includes('growth')) sentiment = 'positive';
                    else if (lower.includes('loss') || lower.includes('down') || lower.includes('crash') || lower.includes('risk') || lower.includes('miss')) sentiment = 'negative';
                } else {
                    text = item.title;
                    sentiment = (item.sentiment || 'neutral').toLowerCase();
                }

                let colorClass = 'text-gray-400 border-white/5 bg-[#1e293b]';
                if (sentiment === 'positive') colorClass = 'text-black bg-primary/80 border-primary/20 font-bold';
                else if (sentiment === 'negative') colorClass = 'text-white bg-danger/80 border-danger/20 font-bold';

                return { text, colorClass };
            };

            // Show top 5 in capsules
            headlines.slice(0, 5).forEach(h => {
                const { text, colorClass } = getHeadlineData(h);
                const span = document.createElement('span');
                span.className = `px-3 py-1.5 rounded-full border text-xs font-mono hover:scale-105 cursor-default transition-all ${colorClass}`;
                span.textContent = text.length > 50 ? text.substring(0, 50) + '...' : text;
                headlinesGrid.appendChild(span);
            });

            // "View All" Logic
            const viewAllBtn = document.getElementById('viewAllHeadlinesBtn');
            const modal = document.getElementById('headlinesModal');
            const modalList = document.getElementById('allHeadlinesList');
            const closeBtn = document.getElementById('closeHeadlinesModal');
            const modalBg = document.getElementById('headlinesModalBg');

            if (headlines.length > 5) {
                viewAllBtn.classList.remove('hidden');

                viewAllBtn.onclick = () => {
                    modalList.innerHTML = ''; // Clear
                    headlines.forEach(h => {
                        const { text, colorClass } = getHeadlineData(h);
                        const div = document.createElement('div');
                        div.className = "mb-2";
                        // Render full width capsule in modal
                        div.innerHTML = `<div class="p-3 rounded-xl border text-sm font-mono ${colorClass}">${text}</div>`;
                        modalList.appendChild(div);
                    });
                    modal.classList.remove('hidden');
                };

                const closeModal = () => modal.classList.add('hidden');
                closeBtn.onclick = closeModal;
                modalBg.onclick = closeModal;
            } else {
                viewAllBtn.classList.add('hidden');
            }

        } catch (e) { console.error("Error rendering News:", e); }

        // --- Peer Comparison (Radar SVG - 6 Axes) ---
        try {
            // Axes: Growth(0), Profitability(60), Efficiency(120), Valuation(180), Dividend(240), Momentum(300)
            const scores = fundamentals.normalized_scores || {
                "Growth": 50, "Profitability": 50, "Efficiency": 50, "Valuation": 50, "Dividend Yield": 0, "Momentum": 50
            };

            // Normalize values 0-100 for the chart radius (max 80px)
            const p1 = Math.min(Math.max(scores["Growth"] || 0, 10), 100);
            const p2 = Math.min(Math.max(scores["Profitability"] || 0, 10), 100);
            const p3 = Math.min(Math.max(scores["Efficiency"] || 0, 10), 100);
            const p4 = Math.min(Math.max(scores["Valuation"] || 0, 10), 100);
            const p5 = Math.min(Math.max(scores["Dividend Yield"] || 0, 10), 100);
            const p6 = Math.min(Math.max(scores["Momentum"] || 0, 10), 100);

            // Angles: 0, 60, 120, 180, 240, 300
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
                getPoint(p2, 60),
                getPoint(p3, 120),
                getPoint(p4, 180),
                getPoint(p5, 240),
                getPoint(p6, 300)
            ].join(' ');

            const poly = document.getElementById('peerRadarPolygon');
            if (poly) {
                poly.setAttribute('points', points);
            }

        } catch (e) { console.error("Error rendering Peer Radar:", e); }


        // --- NEW: Detailed Metrics Grid ---
        try {
            const grid = document.getElementById('metricsGrid');
            if (grid) {
                grid.innerHTML = ''; // Clear loading state

                const createCard = (title, value, sub = '') => {
                    const card = document.createElement('div');
                    card.className = "metric-card";

                    let valColor = "text-white";
                    if (title.includes('Return') || title.includes('Growth')) {
                        const num = parseFloat(value);
                        if (num > 0) valColor = "text-primary";
                        else if (num < 0) valColor = "text-danger";
                    }

                    card.innerHTML = `
                        <span class="metric-title">${title}</span>
                        <div class="flex items-baseline gap-1">
                            <span class="metric-value ${valColor}">${value !== undefined && value !== null ? value : '--'}</span>
                            <span class="metric-sub">${sub}</span>
                        </div>
                    `;
                    return card;
                };

                const f = fundamentals;

                // Row 1: Valuation
                grid.appendChild(createCard("Market Cap", f.market_cap ? f.market_cap.toLocaleString() : '--', " Cr"));
                grid.appendChild(createCard("P/E Ratio", f.pe_ratio));
                grid.appendChild(createCard("Ind. P/E", f.industry_pe));
                grid.appendChild(createCard("P/B Ratio", f.pb_ratio));

                // Row 2: Profitability
                grid.appendChild(createCard("Div. Yield", f.dividend_yield, "%"));
                grid.appendChild(createCard("EPS", f.eps));
                grid.appendChild(createCard("ROE", f.roe, "%"));
                grid.appendChild(createCard("ROCE", f.roce, "%"));

                // Row 3: Returns
                grid.appendChild(createCard("1Y Return", f.returns_1y, "%"));
                grid.appendChild(createCard("3Y Return", f.returns_3y, "%"));
                grid.appendChild(createCard("5Y Return", f.returns_5y, "%"));
                // Debt/Eq removed per user request
            }

        } catch (e) { console.error("Error rendering Detailed Metrics:", e); }

        // --- NEW: Peer Comparison Table ---
        try {
            const tbody = document.getElementById('peerTableBody');
            tbody.innerHTML = '';

            const peerMap = peers.peer_metrics || {};
            const rows = [];

            // Target Row
            rows.push({
                name: company_name,
                mc: fundamentals.market_cap,
                pe: fundamentals.pe_ratio,
                roe: fundamentals.roe,
                roce: fundamentals.roce,
                ret: fundamentals.returns_1y,
                dy: fundamentals.dividend_yield,
                isTarget: true
            });

            // Peers
            for (const [pName, pM] of Object.entries(peerMap)) {
                rows.push({
                    name: pName,
                    mc: pM.market_cap,
                    pe: pM.pe_ratio,
                    roe: pM.roe,
                    roce: pM.roce,
                    ret: pM.returns_1y,
                    dy: pM.dividend_yield,
                    isTarget: false
                });
            }

            rows.forEach(r => {
                const tr = document.createElement('tr');
                tr.className = r.isTarget ? "bg-primary/5 border-b border-primary/20" : "border-b border-white/5 hover:bg-white/5 transition-colors";

                tr.innerHTML = `
                    <td class="p-3 font-medium ${r.isTarget ? 'text-primary' : 'text-white'}">
                        ${r.name} ${r.isTarget ? '<span class="text-[10px] uppercase bg-primary/20 px-1 rounded ml-1">You</span>' : ''}
                    </td>
                    <td class="p-3 text-right text-gray-400">${r.mc ? r.mc.toLocaleString() : '--'}</td>
                    <td class="p-3 text-right text-gray-300">${r.pe || '--'}</td>
                    <td class="p-3 text-right font-bold text-white">${r.roe || '--'}%</td>
                    <td class="p-3 text-right text-gray-300">${r.roce || '--'}%</td>
                    <td class="p-3 text-right font-bold ${r.ret > 0 ? 'text-green-400' : 'text-red-400'}">${r.ret || '--'}%</td>
                `;
                tbody.appendChild(tr);
            });

        } catch (e) { console.error("Error rendering Peer Table:", e); }

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
