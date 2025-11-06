from flask import Flask, jsonify
from config import Config
from utils.db import db_instance
from routes.call_routes import call_bp  # Make sure this import is present
import sys

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Validate configuration
    config_errors = Config.validate()
    if config_errors:
        print("\n" + "="*60)
        print("❌ CONFIGURATION ERRORS")
        print("="*60)
        for error in config_errors:
            if "WARNING" in error:
                print(f"⚠️  {error}")
            else:
                print(f"❌ {error}")
        print("="*60)
        
        # Exit if critical errors (non-WARNING)
        critical_errors = [e for e in config_errors if "WARNING" not in e]
        if critical_errors:
            print("\n💡 Please set the required environment variables in .env file")
            print("   See .env.example for reference\n")
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
    
    # --- THIS IS THE CRITICAL LINE ---
    # This line connects all routes from call_routes.py
    app.register_blueprint(call_bp, url_prefix='/api/call')
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        # Check MongoDB connection
        try:
            db = db_instance.get_db()
            # Try to ping the database
            db.command('ping')
            mongodb_status = 'connected'
        except Exception as e:
            mongodb_status = 'disconnected'
        
        return jsonify({
            'status': 'healthy',
            'service': 'EMI Recovery Agent',
            'version': '2.0.0',
            'mongodb': mongodb_status
        }), 200
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'message': 'EMI Recovery Agent API',
            'version': '2.0.0',
            'description': 'Intelligent recovery agent that handles most scenarios before transferring',
            'endpoints': {
                'health': '/health',
                'initiate_call': 'POST /api/call/initiate',
                'get_customer': 'GET /api/call/customers/<customer_id>',
                'get_call_history': 'GET /api/call/customers/<customer_id>/call-history',
                'webhooks': {
                    # --- FIXED DOCUMENTATION ---
                    '1_handle_answer': 'POST /api/call/handle-answer (Fast)',
                    '2_generate_greeting': 'POST /api/call/generate-greeting (Slow AI Call 1)',
                    '3_process_response': 'POST /api/call/process-response (Handles ALL user speech)',
                    '4_present_details': 'POST /api/call/present-details (Slow AI Call 2)',
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
    print("="*60)
    print("\n💡 To test:")
    print("   1. Make sure ngrok is running: ngrok http 5000")
    print("   2. Update BASE_URL in .env with ngrok URL")
    print("   3. Run: python test_call.py")
    print("\n🔍 Watching for incoming calls...\n")
    
    # Added use_reloader=False to prevent the app from restarting on launch
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)