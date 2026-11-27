"""
Server launcher for Dawaa'i AI.
Runs Uvicorn on http://127.0.0.1:8000
"""
import uvicorn
import os
import sys

# Ensure project root is in sys.path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"Starting Dawaa'i AI (دوائي) on http://{host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=["app", "static"],
        reload_excludes=[
            "*.db*",
            "*.sqlite*",
            "*.docx*",
            "*.pptx*",
            "*.zip*",
            ".venv*",
            "scratch*",
            "figures*"
        ]
    )
