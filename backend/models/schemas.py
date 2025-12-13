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
    headlines: List[str]
    panic_level: Literal["low", "medium", "high"]

class FundamentalMetrics(BaseModel):
    revenue_growth: float
    profit_margin: float
    roe: float
    debt_to_equity: float
    health_score: int = Field(..., ge=0, le=10)
    strengths: List[str]
    concerns: List[str]

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
    timeframe: str
    entry_strategy: str

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
