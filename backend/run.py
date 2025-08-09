#!/usr/bin/env python3
"""
ParchMark Backend Server Startup Script
Starts the FastAPI server with proper configuration and database initialization.
"""

import uvicorn
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def main():
    """
    Main function to start the FastAPI server.
    """
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    print("🚀 Starting ParchMark Backend Server...")
    print(f"📍 Server will be available at: http://{host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🔍 Alternative Docs: http://{host}:{port}/redoc")
    print(f"🏥 Health Check: http://{host}:{port}/health")
    print(f"🐛 Debug Mode: {'Enabled' if debug else 'Disabled'}")
    print(f"📝 Log Level: {log_level.upper()}")
    print("-" * 50)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,  # Auto-reload in debug mode
        log_level=log_level,
        access_log=True
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)
