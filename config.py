import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ============================================
    # MongoDB Configuration
    # ============================================
    # MongoDB connection string
    # Format: mongodb://username:password@host:port/database
    # For local: mongodb://localhost:27017/emi_call_agent
    # For Atlas: mongodb+srv://username:password@cluster.mongodb.net/dbname
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/emi_call_agent')
    
    # ============================================
    # Google Gemini AI Configuration
    # ============================================
    # Get your API key from: https://makersuite.google.com/app/apikey
    # This is used for:
    # - Generating conversational scripts
    # - Analyzing customer responses
    # - Determining intent and next actions
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # ============================================
    # Twilio Configuration
    # ============================================
    # Get these from: https://console.twilio.com/
    
    # Twilio Account SID (starts with AC...)
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    
    # Twilio Auth Token (keep this secret!)
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    
    # Your Twilio phone number (must be purchased/verified in Twilio)
    # Format: +1234567890 (with country code)
    # This is the number that will show up when calling customers
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

    # ============================================
    # Agent Configuration
    # ============================================
    # Change: Added BANK_NAME
    # This is the name your bot will use to introduce itself.
    # Set this in your .env file
    BANK_NAME = os.getenv('BANK_NAME', 'Your Bank')
    
    # Phone number of human agent for transfers
    # IMPORTANT: This number must be verified in your Twilio account
    # Format: +1234567890 (with country code)
    # If not set, transfers will gracefully fail with a message
    AGENT_PHONE_NUMBER = os.getenv('AGENT_PHONE_NUMBER')
    
    # ============================================
    # Flask Configuration
    # ============================================
    # Secret key for Flask sessions (change in production!)
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # ============================================
    # Webhook Configuration
    # ============================================
    # Base URL for Twilio webhooks
    # Development: Use ngrok URL (e.g., https://abc123.ngrok.io)
    # Production: Use your actual domain (e.g., https://api.yourcompany.com)
    # 
    # IMPORTANT: Update this when using ngrok!
    # Example: BASE_URL = 'https://abc123.ngrok.io'
    # 
    # Twilio will call these endpoints:
    # - {BASE_URL}/api/call/handle-answer (when call is answered)
    # - {BASE_URL}/api/call/process-response (for conversation flow)
    # - {BASE_URL}/api/call/status (for call status updates)
    # - {BASE_URL}/api/call/handle-recording (for call recordings)
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    
    # ============================================
    # Feature Flags (Optional)
    # ============================================
    # Enable/disable machine detection
    # Set to 'Enable' in production, 'Disable' for testing
    # When enabled, Twilio will detect answering machines
    MACHINE_DETECTION = os.getenv('MACHINE_DETECTION', 'Disable')
    
    # Call recording enabled by default
    # Set to 'false' to disable recordings
    ENABLE_RECORDING = os.getenv('ENABLE_RECORDING', 'true').lower() == 'true'
    
    # Maximum call duration in seconds (default: 10 minutes)
    MAX_CALL_DURATION = int(os.getenv('MAX_CALL_DURATION', '600'))
    
    # ============================================
    # Validation
    # ============================================
    @staticmethod
    def validate():
        """Validate that all required configuration is present"""
        errors = []
        
        if not Config.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is not set")
        
        if not Config.TWILIO_ACCOUNT_SID:
            errors.append("TWILIO_ACCOUNT_SID is not set")
        
        if not Config.TWILIO_AUTH_TOKEN:
            errors.append("TWILIO_AUTH_TOKEN is not set")
        
        if not Config.TWILIO_PHONE_NUMBER:
            errors.append("TWILIO_PHONE_NUMBER is not set")
        
        if not Config.MONGODB_URI:
            errors.append("MONGODB_URI is not set")
        
        if Config.BASE_URL == 'http://localhost:5000':
            errors.append("WARNING: BASE_URL is set to localhost. Twilio webhooks won't work! Use ngrok for testing.")
        
        if Config.BANK_NAME == 'Your Bank':
            errors.append("WARNING: BANK_NAME is not set in .env. Using default 'Your Bank'.")

        return errors
    
    @staticmethod
    def print_config():
        """Print configuration (for debugging)"""
        print("\n" + "="*60)
        print("📋 CONFIGURATION")
        print("="*60)
        print(f"MongoDB URI: {Config.MONGODB_URI[:30]}...")
        print(f"Gemini API Key: {'✓ Set' if Config.GEMINI_API_KEY else '✗ Missing'}")
        print(f"Twilio Account SID: {Config.TWILIO_ACCOUNT_SID[:10] if Config.TWILIO_ACCOUNT_SID else '✗ Missing'}...")
        print(f"Twilio Phone: {Config.TWILIO_PHONE_NUMBER if Config.TWILIO_PHONE_NUMBER else '✗ Missing'}")
        # Change: Added BANK_NAME to print
        print(f"Bank Name: {Config.BANK_NAME}")
        print(f"Agent Phone: {Config.AGENT_PHONE_NUMBER if Config.AGENT_PHONE_NUMBER else '✗ Not Set (transfers disabled)'}")
        print(f"Base URL: {Config.BASE_URL}")
        print(f"Machine Detection: {Config.MACHINE_DETECTION}")
        print(f"Recording: {'Enabled' if Config.ENABLE_RECORDING else 'Disabled'}")
        print("="*60 + "\n")