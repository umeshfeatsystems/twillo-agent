import os
import base64
from google.cloud import texttospeech
from config import Config
from language_config import LanguageConfig

class GoogleTTSService:
    def __init__(self):
        self.client = None
        # 1. Initialize Memory Cache
        self._audio_cache = {} 
        
        if Config.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(Config.GOOGLE_APPLICATION_CREDENTIALS):
            try:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = Config.GOOGLE_APPLICATION_CREDENTIALS
                self.client = texttospeech.TextToSpeechClient()
                print("✓ Google Cloud TTS client initialized")
            except Exception as e:
                print(f"✗ Failed: {e}")

    def synthesize_to_mulaw(self, text, language='en-IN', voice_override=None):
        """
        Synthesizes text to 8000Hz MULAW audio with Caching.
        """
        if not self.client or not text: return None

        # 2. Check Cache First (Instant Return)
        # Create a unique key based on text and voice
        tts_config = LanguageConfig.get_tts_config(language)
        voice_name = voice_override or tts_config['voice_name']
        cache_key = f"{text}|{voice_name}|{language}"

        if cache_key in self._audio_cache:
            print(f"[CACHE] Served TTS from RAM: '{text[:20]}...'")
            return self._audio_cache[cache_key]

        try:
            # 3. Generate if not in cache
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code=tts_config['language_code'],
                name=voice_name
            )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MULAW,
                sample_rate_hertz=8000
            )

            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # 4. Save to Cache
            self._audio_cache[cache_key] = response.audio_content
            return response.audio_content
            
        except Exception as e:
            print(f"TTS Error: {e}")
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