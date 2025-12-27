import uvicorn
import os

if __name__ == "__main__":
    # Render and other PaaS provide PORT via environment variable
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    # 0.0.0.0 is required for the app to be accessible externally (outside the container)
    if host == "0.0.0.0":
        print(f"\n🚀 App running! Access locally at: http://127.0.0.1:{port}\n")
    
    uvicorn.run("backend.main:app", host=host, port=port, log_level="info")
