import google.generativeai as genai
import json
import logging
from backend.config import GEMINI_API_KEY
from backend.utils.rag import FinancialRAG
from backend.utils.pdf_parser import PDFParser
from backend.utils.table_extractor import FinancialTableExtractor
from backend.models.schemas import FundamentalMetrics
from backend.utils.ai_helper import generate_content_with_retry

logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)

class FundamentalAnalyzer:
    def __init__(self):
        self.rag = FinancialRAG()
        self.pdf_parser = PDFParser
        self.table_extractor = FinancialTableExtractor()

    def process_and_store(self, pdf_path: str, company_name: str, report_type: str, job_id: str):
        import time
        t_start = time.time()
        
        # Extract Text
        print(f"[Fundamental Analyzer] Starting PDF Extraction for {pdf_path}...")
        parser = self.pdf_parser(pdf_path)
        text = parser.extract_text()
        t_pdf = time.time()
        print(f"[Fundamental Analyzer] PDF Extraction took {t_pdf - t_start:.2f}s. Length: {len(text)} chars.")
        
        # Store in RAG
        print(f"[Fundamental Analyzer] Starting RAG Ingestion...")
        self.rag.add_document(text, company_name, report_type, job_id)
        t_rag = time.time()
        print(f"[Fundamental Analyzer] RAG Ingestion took {t_rag - t_pdf:.2f}s.")
        print(f"[Fundamental Analyzer] Total Process Time: {t_rag - t_start:.2f}s.")
        
        # Tables (optional for now, can add to context later)
        # tables = parser.extract_tables()
        # id_tables = self.table_extractor.identify_financial_tables(tables)

    def analyze(self, company_name: str) -> FundamentalMetrics:
        print(f"\n[Fundamental Analyzer] Starting Mixed Analysis for {company_name}...")
        
        # 1. Fetch Reliable CSV Data
        # Import here to avoid circular dependency if any
        from backend.utils.ticker_db import get_ticker_db
        db = get_ticker_db()
        csv_data = db.get_company_details(company_name) or {}
        
        print(f"[Fundamental Analyzer] CSV Data Found: {bool(csv_data)}")
        
        # 2. Retrieve Qualitative Context via RAG
        context = self.rag.query_context(
            f"What is the management outlook, future growth plans, strategic direction, and key risks for {company_name}?",
            company_name
        )
        print(f"[Fundamental Analyzer] Retrieved {len(context)} characters of context.")

        # 3. LLM Extraction for Qualitative Fields & Missing Quantitative
        # We explicitly ask for the missing CSV metrics (Debt, Growth, Margin) here
        prompt = f"""
        You are a financial analyst. I have some quantitative data but I am missing key metrics.
        
        Context from Annual/Quarterly Report:
        {context[:32000]} 
        
        Task:
        1. IDENTIFY THE SECTOR (e.g., IT, Pharma, Banking, Oil & Gas).
        2. SEARCH the text for "Financial Highlights" or "Consolidated Results" tables.
        3. EXTRACT the following missing metrics. 
           - **Raw Financials (Crucial)**: Extract the actual numbers for Current Year and Previous Year Revenue/Sales and Net Profit to calculate growth accurately.
           - **Debt-to-Equity**: Look for "D/E ratio" or "Gearing".
        
        4. Qualitative extraction:
           - "Management Outlook": Tone? Future guidance?
           - "Future Plans": Capex, expansions?
           - "Strengths" & "Concerns": Key risks/moats.
           - "Health Score": 0-10.
        
        CRITICAL: 
        - If a number is NOT found, return 0.0.
        - Normalize numbers to CRORES if possible, or keep consistent units (e.g., both in Millions) so division works.
        
        Return JSON object (no markdown):
        {{
            "sector": "<string>",
            "revenue_current": <float, latest year sales>,
            "revenue_prior": <float, previous year sales>,
            "profit_current": <float, latest year net profit>,
            "profit_prior": <float, previous year net profit>,
            "revenue_growth_pct": <float, optional valid % if found explicitly>,
            "debt_to_equity": <float>,
            "management_outlook": "<paragraph>",
            "future_plans": "<paragraph>",
            "strengths": ["<strength1>", "<strength2>"],
            "concerns": ["<concern1>", "<concern2>"],
            "health_score": <int, 0-10>
        }}
        """
        
        llm_data = {
            "sector": "Unknown Sector",
            "revenue_current": 0.0, "revenue_prior": 0.0,
            "profit_current": 0.0, "profit_prior": 0.0,
            "revenue_growth_pct": 0.0,
            "debt_to_equity": 0.0,
            "management_outlook": "Data not available in report.",
            "future_plans": "Data not available in report.",
            "strengths": [],
            "concerns": [],
            "health_score": 5
        }

        try:
            if context and len(context) > 100:
                print("[Fundamental Analyzer] Asking Gemini for qualitative insights + math inputs...")
                model_flash = genai.GenerativeModel('models/gemma-3-27b-it')
                response = generate_content_with_retry(model_flash, prompt)
                extracted = json.loads(response.text.replace("```json", "").replace("```", ""))
                llm_data.update(extracted)
            else:
                print("[Fundamental Analyzer] RAG Context empty. Using defaults.")
                
        except Exception as e:
            logger.error(f"Qualitative analysis failed: {e}")
            llm_data["strengths"].append(f"AI Extraction Error: {str(e)}")

        # --- MATH VERIFICATION ---
        # Calculate Growth if raw numbers exist
        calc_rev_growth = 0.0
        if llm_data['revenue_current'] > 0 and llm_data['revenue_prior'] > 0:
            calc_rev_growth = ((llm_data['revenue_current'] - llm_data['revenue_prior']) / llm_data['revenue_prior']) * 100
        elif llm_data['revenue_growth_pct'] != 0:
             calc_rev_growth = llm_data['revenue_growth_pct']
             
        # Calculate Margin
        calc_margin = 0.0
        if llm_data['profit_current'] > 0 and llm_data['revenue_current'] > 0:
            calc_margin = (llm_data['profit_current'] / llm_data['revenue_current']) * 100

        # 4. Merge Data (CSV takes precedence for numbers, BUT fill gaps with LLM)
        metrics = FundamentalMetrics(
            # CSV Quantitative
            market_cap=csv_data.get('Market Cap (Cr.)', 0.0),
            pe_ratio=csv_data.get('PE Ratio', 0.0),
            industry_pe=csv_data.get('Industry PE', 0.0),
            roe=csv_data.get('ROE', 0.0),
            roce=csv_data.get('ROCE', 0.0),
            eps=csv_data.get('EPS', 0.0),
            pb_ratio=csv_data.get('PB Ratio', 0.0),
            dividend_yield=csv_data.get('Dividend', 0.0),
            
            # Fill voids with LLM data
            debt_to_equity=float(llm_data.get('debt_to_equity', 0.0)),
            sector=llm_data.get('sector', 'Unknown Sector'),
            
            # Returns
            returns_1m=csv_data.get('1M Returns', 0.0),
            returns_3m=csv_data.get('3M Returns', 0.0),
            returns_1y=csv_data.get('1 Yr Returns', 0.0),
            returns_3y=csv_data.get('3 Yr Returns', 0.0),
            returns_5y=csv_data.get('5 Yr Returns', 0.0),
            
            # Technicals
            fifty_dma=csv_data.get('50 DMA', 0.0),
            two_hundred_dma=csv_data.get('200 DMA', 0.0),
            rsi=csv_data.get('RSI', 0.0),
            
            # LLM Qualitative
            health_score=llm_data.get('health_score', 5),
            strengths=llm_data.get('strengths', []),
            concerns=llm_data.get('concerns', []),
            management_outlook=llm_data.get('management_outlook'),
            future_plans=llm_data.get('future_plans'),
            
            # Computed Math
            revenue_growth=round(calc_rev_growth, 2),
            profit_margin=round(calc_margin, 2),
            
            # Hidden Raw
            revenue_current=llm_data.get('revenue_current', 0.0),
            revenue_prior=llm_data.get('revenue_prior', 0.0),
            profit_current=llm_data.get('profit_current', 0.0),
            profit_prior=llm_data.get('profit_prior', 0.0)
        )
        
        return metrics
