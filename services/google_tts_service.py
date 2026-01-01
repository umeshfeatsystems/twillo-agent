import os
import base64
from google.cloud import texttospeech
from config import Config
from language_config import LanguageConfig

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
        else:
            print(f"✗ CRITICAL: Google Cloud credentials not found at {Config.GOOGLE_APPLICATION_CREDENTIALS}")
    
    def synthesize_to_mulaw(self, text, language='en-IN', voice_override=None):
        """
        Synthesizes text to 8000Hz MULAW audio (Required for Twilio Media Streams).
        Returns: Raw Bytes (not base64)
        """
        if not self.client: 
            print("Error: TTS Client not active")
            return None

        try:
            # 1. Config
            tts_config = LanguageConfig.get_tts_config(language)
            voice_name = voice_override or tts_config['voice_name']
            
            # 2. Input
            synthesis_input = texttospeech.SynthesisInput(text=text)

            # 3. Voice Selection
            voice = texttospeech.VoiceSelectionParams(
                language_code=tts_config['language_code'],
                name=voice_name
            )

            # 4. Audio Config (CRITICAL FOR STREAMING)
            # Twilio Media Streams strictly requires Encoding=MULAW, SampleRate=8000Hz
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MULAW,
                sample_rate_hertz=8000
            )

            # 5. Call API
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            return response.audio_content
            
        except Exception as e:
            print(f"TTS Mulaw Error: {e}")
            return None

    def synthesize_speech(self, text, language='en', voice_override=None):
        """
        Legacy MP3 synthesis for HTTP/Fallback routes.
        """
        if not self.client: return None
        
        try:
            tts_config = LanguageConfig.get_tts_config(language)
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice_name = voice_override or tts_config['voice_name']
            if 'en-IN' in voice_name: lang_code = 'en-IN'
            elif 'hi-IN' in voice_name: lang_code = 'hi-IN'
            else: lang_code = tts_config['language_code']

            voice = texttospeech.VoiceSelectionParams(
                language_code=lang_code,
                name=voice_name
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=tts_config['speaking_rate'],
                effects_profile_id=['telephony-class-application']
            )
            
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            return base64.b64encode(response.audio_content).decode('utf-8')
            
        except Exception as e:
            print(f"Error synthesizing speech: {e}")
            return None

google_tts_service = GoogleTTSService()