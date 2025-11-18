import os
import base64
from google.cloud import texttospeech
from config import Config
from language_config import LanguageConfig  # <-- Make sure this is imported

class GoogleTTSService:
    def __init__(self):
        self.client = None
        if Config.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(Config.GOOGLE_APPLICATION_CREDENTIALS):
            try:
                # Set environment variable for Google Cloud SDK
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = Config.GOOGLE_APPLICATION_CREDENTIALS
                self.client = texttospeech.TextToSpeechClient()
                print("✓ Google Cloud TTS client initialized successfully")
            except Exception as e:
                print(f"✗ CRITICAL: Failed to initialize Google TTS: {e}")
                print(f"✗ Check if credentials file exists at: {Config.GOOGLE_APPLICATION_CREDENTIALS}")
                raise Exception("Google Cloud TTS is required but failed to initialize")
        else:
            error_msg = f"✗ CRITICAL: Google Cloud credentials not found at {Config.GOOGLE_APPLICATION_CREDENTIALS}"
            print(error_msg)
            raise Exception(error_msg)
    
    def synthesize_speech(self, text, language='en'):
        """
        Synthesize speech using Google Cloud TTS.
        Returns base64 encoded audio or raises exception.
        """
        if not self.client:
            raise Exception("Google TTS client not initialized")
        
        try:
            # --- START OF MODIFICATION ---
            
            # 1. Get the full TTS configuration dictionary
            tts_config = LanguageConfig.get_tts_config(language)
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # 2. Use the tts_config to build the voice parameters
            voice = texttospeech.VoiceSelectionParams(
                language_code=tts_config['language_code'],
                name=tts_config['voice_name']
            )
            
            # 3. Use the tts_config to build the audio parameters
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=tts_config['speaking_rate'], # <-- Now correctly fetched
                pitch=0.0,
                effects_profile_id=['telephony-class-application']
            )
            
            # --- END OF MODIFICATION ---
            
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
            print(f"✓ Google TTS synthesized: {len(text)} chars in {language}")
            return audio_base64
            
        except Exception as e:
            print(f"✗ Error synthesizing speech: {e}")
            raise Exception(f"Google TTS synthesis failed: {e}")

# This line remains the same, creating a single instance for your app
google_tts_service = GoogleTTSService()