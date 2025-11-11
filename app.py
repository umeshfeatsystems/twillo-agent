from flask import Flask, jsonify
from config import Config
from utils.db import db_instance
from routes.call_routes import call_bp
import sys

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Validate configuration
    config_errors = Config.validate()
    if config_errors:
        print("\n" + "="*60)
        print("⚠ CONFIGURATION ERRORS")
        print("="*60)
        for error in config_errors:
            if "WARNING" in error:
                print(f"⚠️  {error}")
            elif "CRITICAL" in error:
                print(f"❌ {error}")
            else:
                print(f"❌ {error}")
        print("="*60)
        
        # Exit if critical errors (CRITICAL or non-WARNING)
        critical_errors = [e for e in config_errors if "WARNING" not in e]
        if critical_errors:
            print("\n💡 SETUP INSTRUCTIONS:")
            print("   1. Set required environment variables in .env file")
            print("   2. Download your Google Cloud service account key JSON")
            print("   3. Place it in: ./credentials/google-cloud-tts.json")
            print("   4. Set GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-cloud-tts.json in .env")
            print("\n   See .env.example for reference\n")
            sys.exit(1)
    
    # Print configuration
    Config.print_config()
    
    # Initialize database connection
    try:
        db_instance.connect()
        print("✓ MongoDB connected successfully\n")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        print("   Make sure MongoDB is running and MONGODB_URI is correct\n")
        sys.exit(1)
    
    # Initialize Google TTS (critical check)
    try:
        from services.google_tts_service import google_tts_service
        if not google_tts_service.client:
            raise Exception("Google TTS client not initialized")
        print("✓ Google Cloud TTS initialized successfully\n")
    except Exception as e:
        print(f"❌ CRITICAL: Google Cloud TTS initialization failed: {str(e)}")
        print("\n💡 Google Cloud TTS Setup:")
        print("   1. Go to Google Cloud Console")
        print("   2. Enable Cloud Text-to-Speech API")
        print("   3. Create a service account")
        print("   4. Download the JSON key")
        print("   5. Save it as ./credentials/google-cloud-tts.json")
        print("   6. Enable billing on your Google Cloud project\n")
        sys.exit(1)
    
    # Register blueprints
    app.register_blueprint(call_bp, url_prefix='/api/call')
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        # Check MongoDB connection
        try:
            db = db_instance.get_db()
            db.command('ping')
            mongodb_status = 'connected'
        except Exception as e:
            mongodb_status = 'disconnected'
        
        # Check Google TTS
        try:
            from services.google_tts_service import google_tts_service
            google_tts_status = 'enabled' if google_tts_service.client else 'disabled'
        except:
            google_tts_status = 'error'
        
        return jsonify({
            'status': 'healthy',
            'service': 'EMI Recovery Agent',
            'version': '2.0.0',
            'mongodb': mongodb_status,
            'google_tts': google_tts_status,
            'tts_mode': 'Google Cloud Only (No Fallback)'
        }), 200
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'message': 'EMI Recovery Agent API',
            'version': '2.0.0',
            'description': 'Intelligent recovery agent with Google Cloud TTS',
            'tts_mode': 'Google Cloud Only',
            'endpoints': {
                'health': '/health',
                'initiate_call': 'POST /api/call/initiate',
                'get_customer': 'GET /api/call/customers/<customer_id>',
                'get_call_history': 'GET /api/call/customers/<customer_id>/call-history',
                'webhooks': {
                    '1_handle_answer': 'POST /api/call/handle-answer',
                    '2_language_selected': 'POST /api/call/language-selected',
                    '3_generate_greeting': 'POST /api/call/generate-greeting',
                    '4_process_response': 'POST /api/call/process-response',
                    '5_present_details': 'POST /api/call/present-details',
                    'status': 'POST /api/call/status',
                    'recording': 'POST /api/call/handle-recording'
                }
            }
        }), 200
    
    return app

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 STARTING EMI RECOVERY AGENT v2.0")
    print("="*60)
    
    app = create_app()
    
    print("="*60)
    print("📞 Twilio Phone:", Config.TWILIO_PHONE_NUMBER)
    print("🔗 Base URL:", Config.BASE_URL)
    print("🎯 Agent Phone:", Config.AGENT_PHONE_NUMBER or "Not configured")
    print("🎤 TTS Mode: Google Cloud Only (No Twilio Fallback)")
    print("="*60)
    print("\n💡 To test:")
    print("   1. Make sure ngrok is running: ngrok http 5000")
    print("   2. Update BASE_URL in .env with ngrok URL")
    print("   3. Ensure Google Cloud credentials are properly set")
    print("   4. Run: python test_call.py")
    print("\n🔊 Watching for incoming calls...\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)