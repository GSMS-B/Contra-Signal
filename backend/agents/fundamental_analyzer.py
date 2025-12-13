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
        # Extract Text
        parser = self.pdf_parser(pdf_path)
        text = parser.extract_text()
        
        # Store in RAG
        self.rag.add_document(text, company_name, report_type, job_id)
        
        # Tables (optional for now, can add to context later)
        # tables = parser.extract_tables()
        # id_tables = self.table_extractor.identify_financial_tables(tables)

    def analyze(self, company_name: str) -> FundamentalMetrics:
        print(f"\n[Fundamental Analyzer] Starting RAG extraction for {company_name}...")
        # Retrieve Context
        context = self.rag.query_context(
            f"What are the revenue growth, profit margin, ROE, debt to equity, and key strengths/concerns for {company_name}?",
            company_name
        )
        print(f"[Fundamental Analyzer] Retrieved {len(context)} characters of context.")

        # Knowledge Fallback Logic
        if not context or len(context) < 100:
            print(f"[Fundamental Analyzer] ⚠️ RAG Context is empty/weak. Switching to GEMINI KNOWLEDGE FALLBACK.")
            prompt = f"""
            You are an expert financial analyst.
            I do not have the specific documents for {company_name}. 
            
            Using your INTERNAL KNOWLEDGE (up to your last training cut-off), estimate the current financial health of {company_name}.
            
            CRITICAL: You MUST provide estimated numbers. Do NOT return 0 or null. Make educated conservative estimates based on public financial trends for this company.
            
            Extract/Estimate:
            1. Revenue Growth (YoY %)
            2. Profit Margin (%)
            3. ROE (%)
            4. Debt-to-Equity Ratio
            
            Return JSON object (no markdown):
            {{
                "revenue_growth": <float>,
                "profit_margin": <float>,
                "roe": <float>,
                "debt_to_equity": <float>,
                "health_score": <int, 0-10>,
                "strengths": ["<strength1>", "<strength2>"],
                "concerns": ["<concern1 - note this is estimated info>", "<concern2>"]
            }}
            """
        else:
            prompt = f"""
            Analyze the fundamentals of {company_name} based on this context:
            {context[:15000]} # Limit context window

            Extract logical conservative estimates. 
            CRITICAL: If a specific percentage is not found, ESTIMATE it based on the text or trends described. Do NOT return 0 unless the report explicitly says 0.
            If absolutely no data is available, return null (which JSON parses as None) or -1, but try to find *something*.
            
            Return JSON object (no markdown):
            {{
                "revenue_growth": <float, percentage e.g. 15.5>,
                "profit_margin": <float, percentage>,
                "roe": <float, percentage>,
                "debt_to_equity": <float>,
                "health_score": <int, 0-10>,
                "strengths": [<list of strings>],
                "concerns": [<list of strings>]
            }}
            """

        try:
            print("[Fundamental Analyzer] Asking Gemini to extract metrics...")
            model_flash = genai.GenerativeModel('models/gemma-3-27b-it')
            response = generate_content_with_retry(model_flash, prompt)
            print(f"[Fundamental Analyzer] Gemini Response:\n{response.text}")
            data = json.loads(response.text.replace("```json", "").replace("```", ""))
            return FundamentalMetrics(**data)
        except Exception as e:
            print(f"!!! [Fundamental Analyzer] ERROR: {e}")
            logger.error(f"Fundamental Analysis failed: {e}")
            # Fallback
            return FundamentalMetrics(
                revenue_growth=0, profit_margin=0, roe=0, debt_to_equity=0,
                health_score=0, strengths=[f"Error: {str(e)}"], concerns=[]
            )
