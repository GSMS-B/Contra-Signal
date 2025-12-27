---
title: Contra Signal
emoji: 📉
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# 🎯 ContraSignal: AI-Powered Contrarian Investment Intelligence

---

## 📋 Problem Statement

### The Market Inefficiency Crisis

In  today's hyper-connected financial markets, negative news spreads instantly, triggering widespread panic selling among retail investors. When adverse headlines break—regulatory challenges, temporary operational setbacks, or controversial announcements—stock prices often plummet indiscriminately, regardless of underlying business fundamentals. This creates a critical disconnect: **fundamentally strong companies with robust financials experience severe price drops driven by short-term sentiment rather than actual deterioration in business quality.**

### The Core Challenges

**Information Overload & Emotional Trading**
Retail investors face 50+ news articles daily per stock, making it impossible to distinguish meaningful signals from temporary noise. Without professional analytical tools, they react emotionally—panic-selling on negative headlines without assessing whether the news fundamentally impacts long-term business value.

**Time & Expertise Barriers**
Professional-grade analysis that combines news sentiment evaluation, fundamental financial assessment, and peer benchmarking takes trained analysts 4-6 hours per company. Retail investors lack both the time and expertise to perform this comprehensive analysis before market sentiment shifts.

**Missed Contrarian Opportunities**
Historical data reveals that 60-70% of panic-selling episodes in fundamentally strong companies present exceptional buying opportunities—the essence of Warren Buffett's principle: *"Be greedy when others are fearful."* However, identifying these opportunities requires simultaneously analyzing multiple data dimensions that existing tools address in isolation.

### The Solution Gap

Current market tools fall into two inadequate categories:

- **News Aggregators**: Display headlines without intelligent sentiment analysis or fundamental context
- **Fundamental Screeners**: Analyze company financials in isolation, ignoring real-time market sentiment and news catalysts

**No existing solution answers:** *"Is this bad news creating a buying opportunity in a fundamentally strong company, or is the market reaction justified?"*

---

## 💡 Our Solution

**ContraSignal** is an AI-powered contrarian investment intelligence system that identifies panic-selling opportunities by detecting divergence between negative market sentiment and strong fundamental business health.

### Core Innovation: Multi-Modal Divergence Detection

ContraSignal employs a **multi-agent AI architecture** that simultaneously:

1. **Analyzes Real-Time News Sentiment** - Evaluates recent news coverage to quantify market fear and panic levels
2. **Assesses Fundamental Strength** - Processes financial reports using Retrieval Augmented Generation (RAG) to extract and analyze key business metrics
3. **Benchmarks Against Peers** - Validates whether the target company genuinely outperforms competitors in financial health
4. **Generates Contrarian Signals** - Identifies opportunities where market fear exceeds fundamental risk, providing actionable investment signals with confidence scores and detailed reasoning

### Technical Approach

**Agentic AI Framework**: Four specialized AI agents orchestrated to provide comprehensive analysis:
- News Sentinel Agent (sentiment analysis and panic detection)
- Fundamental Analyzer Agent (financial report deep-dive using RAG)
- Peer Comparator Agent (competitive benchmarking)
- Contrarian Signal Generator (opportunity synthesis and recommendation)

**Technology Stack**: 
- Large Language Models for natural language understanding and reasoning
- Retrieval Augmented Generation (RAG) for processing lengthy financial documents
- Vector databases for semantic document storage
- RESTful API framework for backend services
- Document processing libraries for PDF extraction and analysis
- News aggregation APIs and financial data sources

### Key Differentiator

While traditional tools analyze news OR fundamentals in isolation, ContraSignal is the first system to **automatically detect and quantify divergence** between market sentiment and business fundamentals—the cornerstone of contrarian investing. It compresses 4-6 hours of professional analyst work into 60 seconds of AI-powered analysis, democratizing sophisticated investment intelligence for retail investors.

---

## 🎯 Impact & Innovation

**Value Proposition**: Transform market panic into investment opportunity by filtering noise from signal, helping investors make rational, evidence-based decisions when others react emotionally.

**Innovation**: First AI system to combine real-time sentiment analysis, fundamental financial assessment, and peer benchmarking into unified contrarian opportunity detection—automating what institutional investors do manually and making it accessible to everyone.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- [Git](https://git-scm.com/)

### Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/GSMS-B/Contra-Signal.git
    cd Contra-Signal
    ```

2.  **Environment Configuration (CRITICAL)**
    *   This project uses sensitive API keys that are **not** stored in the repository.
    *   We provide a template file `.env.template` with the required variable names.

    **Step-by-Step:**
    *   Copy the template to create your local `.env` file:
        *   **Windows (PowerShell):** `copy .env.template .env`
        *   **Mac/Linux:** `cp .env.template .env`
    *   Open the new `.env` file in your editor.
    *   Replace the placeholder text with your actual API keys:
        ```ini
        # .env
        NEWS_API_KEY=your_actual_news_api_key_here
        GEMINI_API_KEY=your_actual_gemini_key_here
        ```
        *   **Get NewsAPI Key:** [https://newsapi.org/](https://newsapi.org/)
        *   **Get Gemini Key:** [https://aistudio.google.com/](https://aistudio.google.com/)

    > **Note:** The `.env` file is ignored by git to keep your secrets safe.

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Application**
    ```bash
    python run.py
    ```
5.**Live Demo**

Access the **Contra-Signal** app here: [https://gsms-b-contra-signal.hf.space/](https://gsms-b-contra-signal.hf.space/)
