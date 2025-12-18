import uvicorn
import os

if __name__ == "__main__":
    # Render and other PaaS provide PORT via environment variable
    port = int(os.environ.get("PORT", 8000))
    
    # 0.0.0.0 is required for the app to be accessible externally (outside the container)
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, log_level="info")
