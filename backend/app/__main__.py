"""Entry point for running the application as a module."""

import os

import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Run the FastAPI application with uvicorn."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    # Check both ENVIRONMENT and DEBUG for backward compatibility
    reload = os.getenv("ENVIRONMENT") == "development" or os.getenv("DEBUG", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    # Only show startup messages if not in container (containers log differently)
    if os.getenv("ENVIRONMENT") != "production":
        print("🚀 Starting ParchMark Backend Server...")
        print(f"📍 Server will be available at: http://{host}:{port}")
        print(f"📚 API Documentation: http://{host}:{port}/docs")
        print(f"🔍 Alternative Docs: http://{host}:{port}/redoc")
        print(f"🏥 Health Check: http://{host}:{port}/health")
        print(f"🐛 Debug Mode: {'Enabled' if reload else 'Disabled'}")
        print(f"📝 Log Level: {log_level.upper()}")
        print("-" * 50)

    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()
