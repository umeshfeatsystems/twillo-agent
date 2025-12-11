from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from config import Config
from language_config import LanguageConfig
from services.google_tts_service import google_tts_service
from utils.audio_cache import AudioCache
import uuid
import os
import base64
import asyncio

class TwilioService:
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        self.from_number = Config.TWILIO_PHONE_NUMBER
        if not google_tts_service.client:
            raise Exception("Google Cloud TTS is required")
        print("✓ TwilioService initialized (Async Pipeline Enabled)")
    
    def initiate_call(self, to_number, customer_id):
        # ... (Same as before, no changes needed here) ...
        try:
            call_ref = f"CALL-{uuid.uuid4().hex[:8].upper()}"
            callback_url = f"{Config.BASE_URL}/api/call/handle-answer?customer_id={customer_id}&call_ref={call_ref}"
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.from_number,
                url=callback_url,
                method='POST',
                status_callback=f"{Config.BASE_URL}/api/call/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                machine_detection='Disable',
                record=Config.ENABLE_RECORDING,
                recording_status_callback=f"{Config.BASE_URL}/api/call/handle-recording",
                timeout=30
            )
            return {'success': True, 'call_sid': call.sid, 'call_ref': call_ref}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # --- NEW ASYNC HELPERS ---

    def prepare_audio_placeholder(self):
        """
        Creates a filename and reserves it in the cache.
        Returns the filename immediately.
        """
        filename = f"{uuid.uuid4().hex}.mp3"
        AudioCache.reserve_key(filename)
        return filename

    def generate_audio_background(self, text, filename, language='en', voice_override=None):
        """
        The actual heavy lifting - to be run in BackgroundTasks
        """
        if not text or not text.strip():
            # If empty, set empty bytes to release the lock
            AudioCache.set(filename, b'')
            return

        try:
            # 1. Normalize
            text = ' '.join(text.split())
            if text and text[-1] not in '.!?':
                text += '.'
                
            # 2. Call Google TTS (Heavy Operation)
            # Pass voice_override properly
            audio_base64 = google_tts_service.synthesize_speech(text, language, voice_override)
            
            # 3. Store in Cache (Releases the lock for the waiting request)
            audio_bytes = base64.b64decode(audio_base64)
            AudioCache.set(filename, audio_bytes)
            print(f"✓ [BG TASK] Audio generated: {filename}")
            
        except Exception as e:
            print(f"✗ [BG TASK] TTS Generation Failed: {e}")
            # Release lock so request doesn't hang forever
            AudioCache.set(filename, b'')

    def generate_async_twiml(self, audio_filename, customer_id, language='en', stt_language=None):
        """
        Generates TwiML pointing to the FUTURE audio file.
        """
        response = VoiceResponse()
        
        # Play the audio (Twilio will fetch this, and we will block until ready)
        audio_url = f"{Config.BASE_URL}/api/call/tts-audio/{audio_filename}"
        response.play(audio_url)
        
        # Gather input
        target_stt_lang = stt_language if stt_language else language
        stt_config = LanguageConfig.get_stt_config(target_stt_lang)
        
        gather = Gather(
            action=f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST',
            input='speech',
            timeout=4,
            speech_timeout='auto',
            language=stt_config['language'],
            speechModel='phone_call',
            enhanced=True,
            hints=stt_config['hints']
        )
        response.append(gather)
        
        # Fallback loop
        response.redirect(f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}', method='POST')
        
        return str(response)

    # ... (Keep other simple helpers like goodbye/transfer unchanged) ...
    def generate_goodbye_twiml(self, text, language='en', voice_override=None):
        # For goodbye, sync is fine
        response = VoiceResponse()
        self._create_say_element(response, text, language, voice_override)
        response.hangup()
        return str(response)

    def generate_transfer_twiml(self, text, language='en', voice_override=None):
        response = VoiceResponse()
        self._create_say_element(response, text, language, voice_override)
        if Config.AGENT_PHONE_NUMBER:
            dial = Dial(caller_id=Config.TWILIO_PHONE_NUMBER)
            dial.number(Config.AGENT_PHONE_NUMBER)
            response.append(dial)
        else:
            response.hangup()
        return str(response)
        
    def _create_say_element(self, response, text, language='en', voice_override=None):
        """Legacy synchronous helper for simple responses"""
        if not text: return
        try:
            audio_base64 = google_tts_service.synthesize_speech(text, language, voice_override)
            filename = f"{uuid.uuid4().hex}.mp3"
            AudioCache.set(filename, base64.b64decode(audio_base64))
            response.play(f"{Config.BASE_URL}/api/call/tts-audio/{filename}")
        except:
            response.say("Goodbye.")

    def generate_hangup_for_machine_twiml(self):
        response = VoiceResponse()
        response.hangup()
        return str(response)