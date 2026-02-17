import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import Config
from routes.call_routes import router as call_router

from services.gemini_service import gemini_service
from services.sarvam_service import sarvam_service
from utils.db import db_instance


def create_app() -> FastAPI:
    config_errors = Config.validate()
    if config_errors:
        print("\n" + "=" * 60)
        print("CONFIGURATION ERRORS")
        print("=" * 60)
        for error in config_errors:
            if "WARNING" in error:
                print(f"  {error}")
            else:
                print(f"  {error}")
        print("=" * 60)

        critical_errors = [e for e in config_errors if "WARNING" not in e]
        if critical_errors:
            print("System exiting due to critical configuration errors.")
            sys.exit(1)

    Config.print_config()

    try:
        db_instance.connect()
        print("MongoDB connected successfully")
    except Exception as exc:
        print(f"MongoDB connection failed: {str(exc)}")
        sys.exit(1)

    try:
        if not sarvam_service.enabled:
            raise Exception("Sarvam service is not configured")
        print("Sarvam STT/TTS initialized successfully\n")
    except Exception as exc:
        print(f"CRITICAL: Sarvam initialization failed: {str(exc)}")
        sys.exit(1)

    app = FastAPI(
        title="EMI Recovery Agent API",
        version="2.1.0",
        description="Intelligent recovery agent with Sarvam STT/TTS and Gemini",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(call_router)


    @app.get("/health")
    async def health_check():
        try:
            db = db_instance.get_db()
            db.command("ping")
            mongodb_status = "connected"
        except Exception:
            mongodb_status = "disconnected"

        try:
            sarvam_status = "enabled" if sarvam_service.enabled else "disabled"
        except Exception:
            sarvam_status = "error"

        try:
            gemini_status = "enabled" if gemini_service.model else "disabled"
        except Exception:
            gemini_status = "error"

        twilio_status = "enabled" if (Config.TWILIO_ACCOUNT_SID and Config.TWILIO_AUTH_TOKEN) else "disabled"

        return {
            "status": "healthy",
            "service": "EMI Recovery Agent",
            "version": "2.1.0",
            "framework": "FastAPI",
            "mongodb": mongodb_status,
            "sarvam": sarvam_status,
            "gemini": gemini_status,
            "twilio": twilio_status,
        }

    @app.get("/")
    async def root():
        return {
            "message": "EMI Recovery Agent API (FastAPI)",
            "version": "2.1.0",
            "docs_url": "/docs",
            "endpoints": {"health": "/health", "initiate_call": "POST /api/call/initiate"},
        }

    return app


app = create_app()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("STARTING EMI RECOVERY AGENT (FastAPI)")
    print("=" * 60)
    print("Swagger UI: http://localhost:8000/docs")
    print("Base URL:   http://localhost:8000")
    print("=" * 60 + "\n")

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
