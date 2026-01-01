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
                print("Google Cloud TTS client initialized successfully")
            except Exception as e:
                print(f"✗ CRITICAL: Failed to initialize Google TTS: {e}")
                print(f"✗ Check if credentials file exists at: {Config.GOOGLE_APPLICATION_CREDENTIALS}")
                raise Exception("Google Cloud TTS is required but failed to initialize")
        else:
            error_msg = f"✗ CRITICAL: Google Cloud credentials not found at {Config.GOOGLE_APPLICATION_CREDENTIALS}"
            print(error_msg)
            raise Exception(error_msg)
    
    def synthesize_speech(self, text, language='en', voice_override=None):
        """
        Synthesize speech using Google Cloud TTS.
        """
        if not self.client:
            raise Exception("Google TTS client not initialized")
        
        try:
            # 1. Get default config for the content language
            tts_config = LanguageConfig.get_tts_config(language)
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # 2. Determine Voice Name
            if voice_override:
                voice_name = voice_override
            else:
                voice_name = tts_config['voice_name']

            # 3. AUTO-DETECT Language Code from Voice Name
            # This is the fail-safe. If we are using an 'en-IN' voice (Sadaltager),
            # we MUST tell Google the request is 'en-IN', even if the text is Hindi.
            if 'en-IN' in voice_name:
                lang_code = 'en-IN'
            elif 'hi-IN' in voice_name:
                lang_code = 'hi-IN'
            else:
                lang_code = tts_config['language_code']

            # 4. Build Parameters
            voice = texttospeech.VoiceSelectionParams(
                language_code=lang_code,
                name=voice_name
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=tts_config['speaking_rate'],
                pitch=0.0,
                effects_profile_id=['telephony-class-application']
            )
            
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
            print(f"Google TTS synthesized: {len(text)} chars | Voice: {voice_name} | Code: {lang_code}")
            return audio_base64
            
        except Exception as e:
            print(f"✗ Error synthesizing speech: {e}")
            raise Exception(f"Google TTS synthesis failed: {e}")

google_tts_service = GoogleTTSService()