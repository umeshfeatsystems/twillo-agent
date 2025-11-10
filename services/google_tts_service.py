import os
import base64
from google.cloud import texttospeech
from config import Config

class GoogleTTSService:
    def __init__(self):
        self.client = None
        if Config.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(Config.GOOGLE_APPLICATION_CREDENTIALS):
            try:
                self.client = texttospeech.TextToSpeechClient()
                print("✓ Google Cloud TTS client initialized")
            except Exception as e:
                print(f"✗ Failed to initialize Google TTS: {e}")
                self.client = None
    
    def synthesize_speech(self, text, language='en'):
        if not self.client:
            return None
        
        try:
            from language_config import LanguageConfig
            lang_config = LanguageConfig.get_language_config(language)
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code=lang_config['google_language'],
                name=lang_config['google_voice']
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.1,
                pitch=0.0,
                effects_profile_id=['telephony-class-application']
            )
            
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
            return audio_base64
            
        except Exception as e:
            print(f"Error synthesizing speech: {e}")
            return None

google_tts_service = GoogleTTSService()