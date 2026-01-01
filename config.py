import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/emi_call_agent')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    BANK_NAME = os.getenv('BANK_NAME', 'Your Bank')
    AGENT_PHONE_NUMBER = os.getenv('AGENT_PHONE_NUMBER')
    
    # Updated default port to 8000 for FastAPI
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')
    
    MACHINE_DETECTION = os.getenv('MACHINE_DETECTION', 'Disable')
    ENABLE_RECORDING = os.getenv('ENABLE_RECORDING', 'true').lower() == 'true'
    MAX_CALL_DURATION = int(os.getenv('MAX_CALL_DURATION', '600'))
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # NEW DEFAULT: Hybrid mode
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'en-hi-hybrid')
    
    @staticmethod
    def validate():
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
        
        if not Config.GOOGLE_APPLICATION_CREDENTIALS:
            errors.append("CRITICAL: GOOGLE_APPLICATION_CREDENTIALS is not set. This is REQUIRED.")
        elif not os.path.exists(Config.GOOGLE_APPLICATION_CREDENTIALS):
            errors.append(f"CRITICAL: Google Cloud credentials file not found at: {Config.GOOGLE_APPLICATION_CREDENTIALS}")
        
        # Updated validation to include hybrid
        if Config.DEFAULT_LANGUAGE not in ['en', 'hi', 'en-hi-hybrid']:
            errors.append(f"WARNING: DEFAULT_LANGUAGE must be 'en', 'hi', or 'en-hi-hybrid'. Current: {Config.DEFAULT_LANGUAGE}")
        
        if 'localhost' in Config.BASE_URL:
             errors.append("WARNING: BASE_URL is set to localhost. Twilio webhooks won't work! Use ngrok for testing.")
        
        if Config.BANK_NAME == 'Your Bank':
            errors.append("WARNING: BANK_NAME is not set in .env. Using default 'Your Bank'.")

        return errors
    
    @staticmethod
    def print_config():
        print("\n" + "="*60)
        print("CONFIGURATION (FastAPI)")
        print("="*60)
        print(f"MongoDB URI: {Config.MONGODB_URI[:30]}...")
        print(f"Gemini API Key: {' Set' if Config.GEMINI_API_KEY else '✗ Missing'}")
        print(f"Twilio Account SID: {Config.TWILIO_ACCOUNT_SID[:10] if Config.TWILIO_ACCOUNT_SID else '✗ Missing'}...")
        print(f"Twilio Phone: {Config.TWILIO_PHONE_NUMBER if Config.TWILIO_PHONE_NUMBER else '✗ Missing'}")
        print(f"Bank Name: {Config.BANK_NAME}")
        print(f"Agent Phone: {Config.AGENT_PHONE_NUMBER if Config.AGENT_PHONE_NUMBER else '✗ Not Set'}")
        print(f"Base URL: {Config.BASE_URL}")
        print(f"Default Language: {Config.DEFAULT_LANGUAGE}")
        
        if Config.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(Config.GOOGLE_APPLICATION_CREDENTIALS):
            print(f"Google TTS:  ENABLED (credentials found)")
        else:
            print(f"Google TTS: ✗ CRITICAL ERROR - Credentials missing")
        
        print("="*60 + "\n")