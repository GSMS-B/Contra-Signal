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
            document.getElementById('companyNameDisplay').textContent = `Analysis: ${company_name}`;
            document.getElementById('analysisDate').textContent = `Date: ${new Date(analysis_date).toLocaleDateString()}`;
        } catch (e) { console.error("Error rendering Header:", e); }

        // --- Signal Card ---
        try {
            const card = document.getElementById('signalCard');
            const type = (signal.signal_type || 'Hold').toLowerCase();

            let cardClass = 'hold';
            if (type.includes('strong buy')) cardClass = 'strong-buy';
            else if (type.includes('buy')) cardClass = 'buy';
            else if (type.includes('avoid')) cardClass = 'avoid';

            card.classList.add(cardClass);

            document.getElementById('signalType').textContent = (signal.signal_type || 'Hold').toUpperCase().replace('_', ' ');
            document.getElementById('signalSummary').textContent = signal.summary || "No summary available.";
            document.getElementById('signalStrength').textContent = `${signal.signal_strength || 5}/10`;
            document.getElementById('confidenceLevel').textContent = signal.confidence || "Low";
        } catch (e) { console.error("Error rendering Signal:", e); }

        // --- News Sentiment ---
        try {
            document.getElementById('newsScore').textContent = news.score > 0 ? `+${news.score}` : news.score;
            document.getElementById('newsScore').style.color = news.score >= 0 ? 'var(--success-color)' : 'var(--danger-color)';

            const newsPercent = ((news.score + 10) / 20) * 100;
            const newsBar = document.getElementById('newsBar');
            newsBar.style.width = `${newsPercent}%`;
            newsBar.className = `metric-fill ${news.score >= 0 ? 'pos' : 'neg'}`;

            document.getElementById('negCount').textContent = news.negative_count;
            document.getElementById('posCount').textContent = news.positive_count; // Fixed ID from news-positive
            document.getElementById('neuCount').textContent = news.neutral_count;

            // Render Headlines
            const headlinesList = document.getElementById('news-headlines');
            headlinesList.innerHTML = '';
            const headlines = Array.isArray(news.headlines) ? news.headlines : [];

            if (headlines.length > 0) {
                headlines.forEach(headline => {
                    const li = document.createElement('li');
                    li.textContent = headline;
                    headlinesList.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.textContent = "No headlines available.";
                li.style.fontStyle = "italic";
                li.style.color = "#666";
                headlinesList.appendChild(li);
            }
        } catch (e) { console.error("Error rendering News:", e); }

        // --- Fundamentals ---
        try {
            document.getElementById('fundScore').textContent = `${fundamentals.health_score}/10`;
            const fundBar = document.getElementById('fundBar');
            fundBar.style.width = `${fundamentals.health_score * 10}%`;

            const fundContainer = document.getElementById('fundMetrics');
            const metrics = [
                { label: 'Revenue Growth', val: `${fundamentals.revenue_growth}%` },
                { label: 'Profit Margin', val: `${fundamentals.profit_margin}%` },
                { label: 'ROE', val: `${fundamentals.roe}%` },
                { label: 'Debt/Equity', val: fundamentals.debt_to_equity }
            ];

            fundContainer.innerHTML = metrics.map(m => `
                <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #f3f4f6;">
                    <span style="color: #6b7280;">${m.label}</span>
                    <span style="font-weight: 600;">${m.val}</span>
                </div>
            `).join('');
        } catch (e) { console.error("Error rendering Fundamentals:", e); }

        // --- Peers ---
        try {
            document.getElementById('compPosition').textContent = (peers.competitive_position || 'Unknown').toUpperCase();
            const peerTable = document.getElementById('peerTableBody');

            // Add Target Row First
            let peerRows = [`
                <tr style="background-color: #EFF6FF; border-bottom: 1px solid #E5E7EB;">
                    <td style="padding: 0.75rem; font-weight: 600;">${company_name} (Target)</td>
                    <td style="padding: 0.75rem;">${fundamentals.revenue_growth}%</td>
                    <td style="padding: 0.75rem;">${fundamentals.profit_margin}%</td>
                    <td style="padding: 0.75rem;">${fundamentals.roe}%</td>
                </tr>
            `];

            // Safely handle missing peers
            const pMetrics = peers.peer_metrics || {};
            for (const [pName, pM] of Object.entries(pMetrics)) {
                peerRows.push(`
                    <tr style="border-bottom: 1px solid #E5E7EB;">
                        <td style="padding: 0.75rem;">${pName}</td>
                        <td style="padding: 0.75rem;">${pM.revenue_growth}%</td>
                        <td style="padding: 0.75rem;">${pM.profit_margin}%</td>
                        <td style="padding: 0.75rem;">${pM.roe}%</td>
                    </tr>
                `);
            }
            peerTable.innerHTML = peerRows.join('');
        } catch (e) { console.error("Error rendering Peers:", e); }

        // --- Thesis ---
        try {
            const oppList = document.getElementById('oppReasons');
            const opps = Array.isArray(signal.opportunity_reasons) ? signal.opportunity_reasons : [];
            oppList.innerHTML = opps.map(r => `<li>${r}</li>`).join('');

            const riskList = document.getElementById('riskFactors');
            const risks = Array.isArray(signal.risk_factors) ? signal.risk_factors : [];
            riskList.innerHTML = risks.map(r => `<li>${r}</li>`).join('');

            document.getElementById('mgmtOutlook').textContent = signal.management_outlook || "No Outlook Available";
            document.getElementById('futureDev').textContent = signal.future_development || "No Future Plans Available";

            document.getElementById('timeframe').textContent = signal.timeframe || "--";
            document.getElementById('entryStrategy').textContent = signal.entry_strategy || "--";
        } catch (e) { console.error("Error rendering Thesis:", e); }
    }

    // 4. Chat Logic
    const chatInput = document.getElementById('questionInput');
    const askBtn = document.getElementById('askBtn');
    const chatHistory = document.getElementById('chatHistory');
    const pills = document.querySelectorAll('.pill');

    async function askQuestion(q) {
        if (!q) return;

        // Add User Message
        appendMessage('user', q);
        chatInput.value = '';

        // API Call
        try {
            const res = await fetch(`/api/ask/${jobId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: q })
            });
            const data = await res.json();

            appendMessage('bot', data.answer);
        } catch (err) {
            appendMessage('bot', 'Sorry, I encountered an error answering that.');
        }
    }

    function appendMessage(role, text) {
        const div = document.createElement('div');
        div.className = `chat-bubble ${role}`;
        div.textContent = text;
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    if (askBtn) askBtn.addEventListener('click', () => askQuestion(chatInput.value));
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') askQuestion(chatInput.value);
        });
    }

    pills.forEach(pill => {
        pill.addEventListener('click', () => askQuestion(pill.textContent));
    });
});
