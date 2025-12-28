from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# --- Requests ---
class AnalysisRequest(BaseModel):
    company_name: str
    report_type: Literal["annual", "quarterly"] = "annual"
    # Files are handled via UploadFile in FastAPI, not Pydantic model directly for the file content usually

class QuestionRequest(BaseModel):
    question: str

# --- Components ---
class NewsSentiment(BaseModel):
    score: int = Field(..., description="Sentiment score from -10 to 10")
    positive_count: int
    negative_count: int
    neutral_count: int
    key_themes: List[str]
    headlines: List[Dict[str, str]]
    panic_level: Literal["low", "medium", "high"]
    severity_score: int = 0
    severity_reason: str = ""

class FundamentalMetrics(BaseModel):
    # Quantitative (from CSV)
    market_cap: float = 0.0
    pe_ratio: float = 0.0
    industry_pe: float = 0.0
    roe: float = 0.0
    roce: float = 0.0
    eps: float = 0.0
    pb_ratio: float = 0.0
    dividend_yield: float = 0.0
    debt_to_equity: float = 0.0 # Estimated if not in CSV
    # Returns
    returns_1m: float = 0.0
    returns_3m: float = 0.0
    returns_1y: float = 0.0
    returns_3y: float = 0.0
    returns_5y: float = 0.0
    # Technicals
    fifty_dma: float = 0.0
    two_hundred_dma: float = 0.0
    rsi: float = 0.0
    
    # Qualitative (from RAG/LLM)
    health_score: int = Field(..., ge=0, le=10)
    strengths: List[str]
    concerns: List[str]
    management_outlook: Optional[str] = "Data not available"
    future_plans: Optional[str] = "Data not available"
    
    # Legacy/Computed fallback
    revenue_growth: float = 0.0
    profit_margin: float = 0.0
    
    # Normalized Scores for Radar Chart (Growth, Profitability, Efficiency, Valuation, Dividend, Momentum)
    normalized_scores: Optional[Dict[str, float]] = None

    # Raw math fields (Hidden)
    revenue_current: float = 0.0
    revenue_prior: float = 0.0
    profit_current: float = 0.0
    profit_prior: float = 0.0
    
    sector: str = "Unknown Sector"

class PeerComparison(BaseModel):
    competitive_position: Literal["leader", "average", "laggard"]
    relative_strength: int = Field(..., ge=0, le=10)
    peer_metrics: Dict[str, FundamentalMetrics]
    # Note: Using FundamentalMetrics as value type for simplicity, 
    # though strictly the peer dict in JSON might be simpler.

class ContrarianSignal(BaseModel):
    signal_type: Literal["strong_buy", "buy", "hold", "avoid", "Strong Buy", "Buy", "Hold", "Avoid"]
    signal_strength: int = Field(..., ge=0, le=10)
    confidence: Literal["high", "medium", "low", "High", "Medium", "Low"]
    summary: str
    opportunity_reasons: List[str]
    risk_factors: List[str]
    management_outlook: str
    future_development: str
    future_development: str
    timeframe: str
    entry_strategy: str
    competitive_moats: List[str]

class AnalysisResult(BaseModel):
    company_name: str
    analysis_date: datetime
    news: NewsSentiment
    fundamentals: FundamentalMetrics
    peers: PeerComparison
    signal: ContrarianSignal

# --- Job Status ---
class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    progress: int = Field(..., ge=0, le=100)
    current_step: str
    error: Optional[str] = None
    result: Optional[AnalysisResult] = None

class QuestionResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = None
