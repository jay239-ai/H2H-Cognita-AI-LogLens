import os
import sys
import subprocess

def start():
    """Entry point for the NetPulse platform."""
    # Ensure project root is in PYTHONPATH
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.environ["PYTHONPATH"] = project_root
    
    print("🛰️  Starting NetPulse Experience Intelligence Platform...")
    
    # Start the backend API
    try:
        from api.main import app
        import uvicorn
        port = int(os.getenv("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"❌ Failed to start NetPulse: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start()
