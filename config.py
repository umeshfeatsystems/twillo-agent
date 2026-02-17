import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/emi_call_agent")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    BANK_NAME = os.getenv("BANK_NAME", "Your Bank")
    AGENT_PHONE_NUMBER = os.getenv("AGENT_PHONE_NUMBER")

    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

    MACHINE_DETECTION = os.getenv("MACHINE_DETECTION", "Disable")
    ENABLE_RECORDING = os.getenv("ENABLE_RECORDING", "true").lower() == "true"
    MAX_CALL_DURATION = int(os.getenv("MAX_CALL_DURATION", "600"))
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # Sarvam AI (STT + TTS)
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
    SARVAM_BASE_URL = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai")
    SARVAM_TTS_ENDPOINT = os.getenv("SARVAM_TTS_ENDPOINT", "/text-to-speech")
    SARVAM_STT_ENDPOINT = os.getenv("SARVAM_STT_ENDPOINT", "/speech-to-text")
    SARVAM_STT_MODEL = os.getenv("SARVAM_STT_MODEL", "saarika:v2.5")
    SARVAM_TTS_MODEL = os.getenv("SARVAM_TTS_MODEL", "bulbul:v3")
    SARVAM_TTS_SPEAKER = os.getenv("SARVAM_TTS_SPEAKER", "shubh")
    SARVAM_TTS_OUTPUT_CODEC = os.getenv("SARVAM_TTS_OUTPUT_CODEC", "wav")
    SARVAM_TTS_SAMPLE_RATE = int(os.getenv("SARVAM_TTS_SAMPLE_RATE", "8000"))
    SARVAM_TIMEOUT_SECONDS = int(os.getenv("SARVAM_TIMEOUT_SECONDS", "20"))

    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

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

        if not Config.SARVAM_API_KEY:
            errors.append("SARVAM_API_KEY is not set")

        if Config.DEFAULT_LANGUAGE not in ["en", "hi", "hi-en", "en-hi-hybrid"]:
            errors.append(
                f"WARNING: DEFAULT_LANGUAGE must be 'en', 'hi', 'hi-en', or 'en-hi-hybrid'. Current: {Config.DEFAULT_LANGUAGE}"
            )

        if "localhost" in Config.BASE_URL:
            errors.append(
                "WARNING: BASE_URL is set to localhost. Twilio webhooks will not work. Use ngrok for testing."
            )

        if Config.BANK_NAME == "Your Bank":
            errors.append("WARNING: BANK_NAME is not set in .env. Using default 'Your Bank'.")

        return errors

    @staticmethod
    def print_config():
        print("\n" + "=" * 60)
        print("CONFIGURATION (FastAPI)")
        print("=" * 60)
        print(f"MongoDB URI: {Config.MONGODB_URI[:30]}...")
        print(f"Gemini API Key: {'Set' if Config.GEMINI_API_KEY else 'Missing'}")
        print(f"Gemini Model: {Config.GEMINI_MODEL}")
        print(
            f"Twilio Account SID: {Config.TWILIO_ACCOUNT_SID[:10] if Config.TWILIO_ACCOUNT_SID else 'Missing'}..."
        )
        print(f"Twilio Phone: {Config.TWILIO_PHONE_NUMBER if Config.TWILIO_PHONE_NUMBER else 'Missing'}")
        print(f"Bank Name: {Config.BANK_NAME}")
        print(f"Agent Phone: {Config.AGENT_PHONE_NUMBER if Config.AGENT_PHONE_NUMBER else 'Not Set'}")
        print(f"Base URL: {Config.BASE_URL}")
        print(f"Default Language: {Config.DEFAULT_LANGUAGE}")
        if Config.SARVAM_API_KEY:
            print(f"Sarvam AI: ENABLED ({Config.SARVAM_BASE_URL})")
            print(f"Sarvam Endpoints: TTS={Config.SARVAM_TTS_ENDPOINT} | STT={Config.SARVAM_STT_ENDPOINT}")
            print(f"Sarvam STT Model: {Config.SARVAM_STT_MODEL}")
            print(
                f"Sarvam TTS Model: {Config.SARVAM_TTS_MODEL} | Speaker: {Config.SARVAM_TTS_SPEAKER} | "
                f"Codec: {Config.SARVAM_TTS_OUTPUT_CODEC} | SampleRate: {Config.SARVAM_TTS_SAMPLE_RATE}"
            )
        else:
            print("Sarvam AI: MISSING API KEY")
        print("=" * 60 + "\n")
