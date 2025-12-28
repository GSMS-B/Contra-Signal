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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not NEWS_API_KEY:
    print("WARNING: NEWS_API_KEY not found in .env")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in .env")
