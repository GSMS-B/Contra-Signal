import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "frontend", "templates")

# Creates upload dir if not exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

if not NEWS_API_KEY:
    print("WARNING: NEWS_API_KEY not found in .env")
if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not found in .env")
if not OPENROUTER_API_KEY:
    print("WARNING: OPENROUTER_API_KEY not found in .env")
if not HF_TOKEN:
    print("WARNING: HF_TOKEN not found in .env, downloading public models anonymously.")
