import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # --- DATABASE ---
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/emi_call_agent')
    
    # --- GEMINI AI ---
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL_ID = "gemini-2.5-flash-native-audio-preview-09-2025"
    
    # --- TWILIO ---
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    
    # --- AGENT SETTINGS ---
    BANK_NAME = os.getenv('BANK_NAME', 'Your Bank')
    
    # --- SERVER ---
    # Ngrok URL (No trailing slash)
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')
    
    @staticmethod
    def validate():
        errors = []
        if not Config.GEMINI_API_KEY: errors.append("GEMINI_API_KEY is missing")
        if not Config.TWILIO_ACCOUNT_SID: errors.append("TWILIO_ACCOUNT_SID is missing")
        if not Config.TWILIO_AUTH_TOKEN: errors.append("TWILIO_AUTH_TOKEN is missing")
        if "localhost" in Config.BASE_URL: errors.append("WARNING: BASE_URL is localhost. Use ngrok.")
        return errors