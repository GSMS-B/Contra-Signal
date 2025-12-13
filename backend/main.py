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
from backend.agents.news_analyzer import NewsAnalyzer
from backend.agents.fundamental_analyzer import FundamentalAnalyzer
from backend.agents.peer_comparator import PeerComparator
from backend.agents.signal_generator import SignalGenerator
from backend.utils.rag import FinancialRAG

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
# Suppress noisy libraries
logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("chromadb").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

# --- Global State ---
jobs = {}  # In-memory storage: {job_id: JobStatus}
agents = {} # Holds agent instances

# --- Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Agents...")
    agents['news'] = NewsAnalyzer()
    agents['fundamental'] = FundamentalAnalyzer()
    agents['peer'] = PeerComparator()
    agents['signal'] = SignalGenerator()
    logger.info("Agents initialized.")
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
async def process_analysis(job_id: str, company_name: str, report_type: str, file_path: str):
    try:
        job = jobs[job_id]
        job.status = "running"
        job.progress = 10
        
        # 1. News Analysis
        job.current_step = "news"
        logger.info(f"Job {job_id}: Starting News Analysis")
        news_result = agents['news'].analyze(company_name)
        job.progress = 30
        
        import time
        print("[System] Cooling down for 5 seconds to match rate limits...")
        time.sleep(5)

        # 2. Fundamental Analysis
        job.current_step = "fundamentals"
        logger.info(f"Job {job_id}: Starting Fundamental Analysis")
        # Process PDF to RAG
        agents['fundamental'].process_and_store(file_path, company_name, report_type, job_id)
        # Analyze
        fund_result = agents['fundamental'].analyze(company_name)
        job.progress = 60

        print("[System] Cooling down for 5 seconds...")
        time.sleep(5)

        # 3. Peer Comparison
        job.current_step = "peers"
        logger.info(f"Job {job_id}: Starting Peer Comparison")
        peer_result = agents['peer'].analyze(company_name, fund_result)
        job.progress = 80

        print("[System] Cooling down for 5 seconds...")
        time.sleep(5)

        # 4. Signal Generation
        job.current_step = "signal"
        logger.info(f"Job {job_id}: Generating Signal")
        signal_result = agents['signal'].generate_signal(news_result, fund_result, peer_result)
        job.progress = 95

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

@app.post("/api/analyze")
async def start_analysis(
    background_tasks: BackgroundTasks,
    company_name: str = Form(...),
    report_type: str = Form(...),
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

    # Start Task
    background_tasks.add_task(
        process_analysis, 
        job_id, 
        company_name, 
        report_type, 
        file_path
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
