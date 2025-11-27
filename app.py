from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import Config
from utils.db import db_instance
from routes.call_routes import router as call_router
import sys
import uvicorn
import os

def create_app() -> FastAPI:
    # 1. Validate Config
    config_errors = Config.validate()
    if config_errors:
        print("\n" + "="*60)
        print("⚠ CONFIGURATION ERRORS")
        print("="*60)
        for error in config_errors:
            if "WARNING" in error:
                print(f"⚠️  {error}")
            else:
                print(f"❌ {error}")
        print("="*60)
        
        critical_errors = [e for e in config_errors if "WARNING" not in e]
        if critical_errors:
            print("System exiting due to critical configuration errors.")
            sys.exit(1)

    # 2. Check Services
    Config.print_config()
    
    # Check MongoDB
    try:
        db_instance.connect()
        print("✓ MongoDB connected successfully")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        sys.exit(1)
        
    # Check Google TTS
    try:
        from services.google_tts_service import google_tts_service
        if not google_tts_service.client:
            raise Exception("Google TTS client not initialized")
        print("✓ Google Cloud TTS initialized successfully\n")
    except Exception as e:
        print(f"❌ CRITICAL: Google Cloud TTS initialization failed: {str(e)}")
        sys.exit(1)

    # 3. Create App
    app = FastAPI(
        title="EMI Recovery Agent API",
        version="2.0.0",
        description="Intelligent recovery agent with Google Cloud TTS and FastAPI"
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include Routes
    app.include_router(call_router)

    # Health Check
    @app.get("/health")
    async def health_check():
        # Check MongoDB
        try:
            db = db_instance.get_db()
            db.command('ping')
            mongodb_status = 'connected'
        except:
            mongodb_status = 'disconnected'
            
        # Check TTS
        try:
            from services.google_tts_service import google_tts_service
            tts_status = 'enabled' if google_tts_service.client else 'disabled'
        except:
            tts_status = 'error'
            
        return {
            'status': 'healthy',
            'service': 'EMI Recovery Agent',
            'version': '2.0.0',
            'framework': 'FastAPI',
            'mongodb': mongodb_status,
            'google_tts': tts_status
        }

    @app.get("/")
    async def root():
        return {
            'message': 'EMI Recovery Agent API (FastAPI)',
            'version': '2.0.0',
            'docs_url': '/docs',
            'endpoints': {
                'health': '/health',
                'initiate_call': 'POST /api/call/initiate'
            }
        }
    
    return app

app = create_app()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 STARTING EMI RECOVERY AGENT (FastAPI)")
    print("="*60)
    print("👉 Swagger UI: http://localhost:8000/docs")
    print("👉 Base URL:   http://localhost:8000")
    print("="*60 + "\n")
    
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)