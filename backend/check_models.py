import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

print(f"Checking models for API Key: {api_key[:5]}...{api_key[-4:]}")

try:
    print("\n--- Available Generative Models ---")
    found_any = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            found_any = True
    
    if not found_any:
        print("No models found that support 'generateContent'.")
        
except Exception as e:
    print(f"Error listing models: {e}")
