import os
import uuid
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import UPLOAD_DIR, STATIC_DIR, TEMPLATES_DIR
from backend.models.schemas import (
    AnalysisRequest, JobStatus, AnalysisResult, 
    NewsSentiment, FundamentalMetrics, PeerComparison, ContrarianSignal,
    QuestionRequest, QuestionResponse
)
# from backend.agents.news_analyzer import NewsAnalyzer
# from backend.agents.fundamental_analyzer import FundamentalAnalyzer
# from backend.agents.peer_comparator import PeerComparator
# from backend.agents.signal_generator import SignalGenerator
# from backend.utils.rag import FinancialRAG

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
# Suppress noisy libraries
logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("chromadb").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

# --- Global State ---
# --- Global State ---
jobs = {}  # In-memory storage: {job_id: JobStatus}
agents = {} # Holds agent instances

# --- Lazy Loading Agents ---
def get_agent(name: str):
    """
    Lazily loads agents to prevent deployment timeouts (e.g. on Render).
    Heavy imports like Torch/ChromaDB happen here, not at startup.
    """
    if name in agents:
        return agents[name]
    
    logger.info(f"Lazy loading agent: {name}...")
    
    if name == 'news':
        from backend.agents.news_analyzer import NewsAnalyzer
        agents['news'] = NewsAnalyzer()
        
    elif name == 'fundamental':
        from backend.agents.fundamental_analyzer import FundamentalAnalyzer
        agents['fundamental'] = FundamentalAnalyzer()
        
    elif name == 'peer':
        from backend.agents.peer_comparator import PeerComparator
        agents['peer'] = PeerComparator()
        
    elif name == 'signal':
        from backend.agents.signal_generator import SignalGenerator
        agents['signal'] = SignalGenerator()
        
    return agents[name]

# --- Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init Ticker Database
    from backend.utils.ticker_db import get_ticker_db
    # Assuming CSV is at backend/data/stocks.csv
    try:
        db = get_ticker_db()
        # Adjust path relative to project root or use config
        base_dir = os.path.dirname(__file__)
        data_dir = os.path.join(base_dir, "data")
        csv_path = os.path.join(data_dir, "stocks.csv")
        
        # DEBUG: Print directory contents to verify deployment structure
        logger.info(f"Checking data directory: {data_dir}")
        if os.path.exists(data_dir):
            logger.info(f"Files in data dir: {os.listdir(data_dir)}")
        else:
            logger.error(f"Data directory NOT FOUND at {data_dir}")
            
        logger.info(f"Attempting to load stock data from: {csv_path}")
        if os.path.exists(csv_path):
            db.load_data(csv_path)
            # Verify load
            details = db.get_company_details("Reliance Industries") # Test check
            logger.info(f"Sanity Check - Reliance Loaded: {bool(details)}")
        else:
            logger.error(f"CRITICAL: stocks.csv NOT FOUND at {csv_path}")

    except Exception as e:
        logger.error(f"Failed to load ticker database: {e}")

    logger.info("Server starting... Agents will be loaded lazily on first use.")
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static & Templates ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- Background Task ---
# --- Background Task ---
from typing import List
def process_analysis(job_id: str, company_name: str, report_type: str, file_path: str, manual_competitors: List[str] = []):
    try:
        job = jobs[job_id]
        job.status = "running"
        job.progress = 10
        
        if job.status == "cancelled": return

        # 1. News Analysis
        job.current_step = "news"
        logger.info(f"Job {job_id}: Starting News Analysis")
        news_agent = get_agent('news')
        news_result = news_agent.analyze(company_name)
        job.progress = 30
        
        if job.status == "cancelled": return

        import time
        # print("[System] Cooling down for 5 seconds to match rate limits...")
        # time.sleep(5)

        # 2. Fundamental Analysis
        job.current_step = "fundamentals"
        logger.info(f"Job {job_id}: Starting Fundamental Analysis")
        # Process PDF to RAG
        fund_agent = get_agent('fundamental')
        # Inject CSV Data here if needed, but for now just process PDF
        # We might need to pass the ticker DB for verification later, but keeping it simple for now
        fund_agent.process_and_store(file_path, company_name, report_type, job_id)
        # Analyze
        fund_result = fund_agent.analyze(company_name)
        job.progress = 60

        if job.status == "cancelled": return

        # print("[System] Cooling down for 5 seconds...")
        # time.sleep(5)

        # 3. Peer Comparison
        job.current_step = "peers"
        logger.info(f"Job {job_id}: Starting Peer Comparison")
        peer_agent = get_agent('peer')
        peer_result = peer_agent.analyze(company_name, fund_result, manual_competitors)
        job.progress = 80

        if job.status == "cancelled": return

        # print("[System] Cooling down for 5 seconds...")
        # time.sleep(5)

        # 4. Signal Generation
        job.current_step = "signal"
        logger.info(f"Job {job_id}: Generating Signal")
        signal_agent = get_agent('signal')
        signal_result = signal_agent.generate_signal(news_result, fund_result, peer_result)
        job.progress = 95
        
        if job.status == "cancelled": return

        # Compile Result
        final_result = AnalysisResult(
            company_name=company_name,
            analysis_date=datetime.now(),
            news=news_result,
            fundamentals=fund_result,
            peers=peer_result,
            signal=signal_result
        )

        job.result = final_result
        job.status = "completed"
        job.progress = 100
        job.current_step = "done"
        logger.info(f"Job {job_id}: Completed")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job.status = "failed"
        job.error = str(e)

# --- Routes ---

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/analyze")
async def analyze_page(request: Request):
    return templates.TemplateResponse("analyze.html", {"request": request})

@app.get("/favicon.ico")
async def favicon():
    file_path = os.path.join(STATIC_DIR, "favicon.png")
    if os.path.exists(file_path):
        from fastapi.responses import FileResponse
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/progress/{job_id}")
async def analyzing_page(request: Request, job_id: str):
    if job_id not in jobs:
         # Optionally handle 404, but page might handle it via JS API call
         pass
    return templates.TemplateResponse("progress.html", {"request": request})

@app.get("/results/{job_id}")
async def results_page(request: Request, job_id: str):
    if job_id not in jobs or jobs[job_id].status != "completed":
        # In real app, handle gracefully
        pass
    return templates.TemplateResponse("results.html", {"request": request})

@app.get("/api/search")
async def search_companies(q: str):
    """
    Search for companies by name.
    """
    if not q:
        return []
    
    from backend.utils.ticker_db import get_ticker_db
    db = get_ticker_db()
    results = db.search_names(q)
    return results

@app.post("/api/analyze")
@app.post("/api/analyze")
async def start_analysis(
    background_tasks: BackgroundTasks,
    company_name: str = Form(...),
    report_type: str = Form(...),
    manual_competitors_list: str = Form(None), # Comma separated list
    main_report: UploadFile = File(...)
):
    job_id = str(uuid.uuid4())
    
    # Save file
    file_ext = os.path.splitext(main_report.filename)[1]
    file_path = os.path.join(UPLOAD_DIR, f"{job_id}{file_ext}")
    
    with open(file_path, "wb") as f:
        content = await main_report.read()
        f.write(content)

    # Init Job
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="queued",
        progress=0,
        current_step="queued"
    )

    # Parse competitors
    competitors = []
    if manual_competitors_list:
        competitors = [c.strip() for c in manual_competitors_list.split(',') if c.strip()]

    # Start Task
    background_tasks.add_task(
        process_analysis, 
        job_id, 
        company_name, 
        report_type, 
        file_path,
        competitors # List passed to worker
    )

    return {"job_id": job_id}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.post("/api/ask/{job_id}")
async def ask_question(job_id: str, request: QuestionRequest):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # In a real app, we'd use the job's context
    # Here we instantiate a fresh RAG query or use the existing RAG instance
    # Ideally RAG should persist or be accessible. 
    # Our FinancialRAG uses persistent ChromaDB, so:
    
    from backend.utils.rag import FinancialRAG # LAZY IMPORT
    rag = FinancialRAG() # Re-init connects to existing DB
    job = jobs[job_id]
    
    # Simple context usage
    context = rag.query_context(request.question, job.result.company_name) if job.result else ""
    
    # Simple direct generation for Q&A
    import google.generativeai as genai
    model = genai.GenerativeModel('models/gemma-3-27b-it')
    
    prompt = f"""
    Context about {job.result.company_name}:
    {context}
    
    User Question: {request.question}
    
    Answer the question based on the context provided.
    """
    
    try:
        resp = model.generate_content(prompt)
        return QuestionResponse(answer=resp.text)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"!!! [Q&A] ERROR: {e}")
        return QuestionResponse(answer=f"I'm sorry, I encountered an error: {str(e)}")

@app.post("/api/cancel/{job_id}")
async def cancel_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Mark as cancelled. The background thread checks this status.
    jobs[job_id].status = "cancelled"
    return {"status": "cancelled"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    # uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
