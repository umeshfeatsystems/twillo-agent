from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from config import Config
from language_config import LanguageConfig
from services.google_tts_service import google_tts_service
from utils.audio_cache import AudioCache
import uuid
import os
import base64

class TwilioService:
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        self.from_number = Config.TWILIO_PHONE_NUMBER
        
        if not google_tts_service.client:
            raise Exception("Google Cloud TTS is required but not available")
        
        # Note: 'tts_cache' directory creation removed as we use in-memory caching
        
        print("✓ TwilioService initialized (In-Memory Caching Enabled)")
    
    def initiate_call(self, to_number, customer_id):
        try:
            call_ref = f"CALL-{uuid.uuid4().hex[:8].upper()}"
            
            callback_url = f"{Config.BASE_URL}/api/call/handle-answer?customer_id={customer_id}&call_ref={call_ref}"
            status_callback_url = f"{Config.BASE_URL}/api/call/status"
            recording_status_callback_url = f"{Config.BASE_URL}/api/call/handle-recording"
            
            print(f"[TWILIO] Initiating call to {to_number}")
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.from_number,
                url=callback_url,
                method='POST',
                status_callback=status_callback_url,
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method='POST',
                machine_detection='Disable', # Keep disabled for lower latency on connect
                record=Config.ENABLE_RECORDING,
                recording_status_callback=recording_status_callback_url,
                recording_status_callback_event=['completed'],
                recording_status_callback_method='POST',
                timeout=30
            )
            
            print(f"[TWILIO] Call created: {call.sid}")
            
            return {
                'success': True,
                'call_sid': call.sid,
                'call_ref': call_ref,
                'status': call.status,
                'to': to_number
            }
        
        except Exception as e:
            print(f"[TWILIO ERROR] Failed to initiate call: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _normalize_script_for_tts(self, text):
        if not text:
            return ""
        text = ' '.join(text.split())
        if text and text[-1] not in '.!?':
            text += '.'
        return text
    
    def _store_audio_memory(self, audio_base64, filename):
        """
        OPTIMIZATION: Store audio in RAM instead of Disk.
        This reduces I/O latency significantly.
        """
        try:
            # Decode base64 to raw bytes once here, so we don't do it on every read
            audio_bytes = base64.b64decode(audio_base64)
            
            # Store in AudioCache
            AudioCache.set(filename, audio_bytes)
            
            # Return the URL that will fetch from memory
            audio_url = f"{Config.BASE_URL}/api/call/tts-audio/{filename}"
            return audio_url
        except Exception as e:
            print(f"✗ Error caching audio: {e}")
            raise Exception(f"Failed to cache audio: {e}")
    
    def _create_say_element(self, response, text, language='en', voice_override=None):
        if not text or not text.strip():
            print("⚠ Warning: Empty text passed to TTS. Playing silence/fallback.")
            response.pause(length=1)
            return

        normalized_text = self._normalize_script_for_tts(text)
        try:
            # Generate Audio (Time taken: TTS Generation)
            audio_base64 = google_tts_service.synthesize_speech(normalized_text, language, voice_override)
            
            filename = f"{uuid.uuid4().hex}.mp3"
            
            # Cache Audio (Time taken: ~0.001s vs ~0.1s disk IO)
            audio_url = self._store_audio_memory(audio_base64, filename)
            
            print(f"[TTS] Served via Memory: {audio_url}")
            response.play(audio_url)
        except Exception as e:
            print(f"✗ CRITICAL: Google TTS failed: {e}")
            response.say("I am having trouble connecting. One moment.")
    
    def generate_initial_twiml(self, script_text, customer_id, language='en', voice_override=None, stt_language=None):
        response = VoiceResponse()
        
        self._create_say_element(response, script_text, language, voice_override)
        
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
        
        response.redirect(f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}', method='POST')
        
        return str(response)
    
    def generate_followup_twiml(self, followup_text, customer_id, language='en', voice_override=None, stt_language=None):
        return self.generate_initial_twiml(followup_text, customer_id, language, voice_override, stt_language)
    
    def generate_goodbye_twiml(self, text, language='en', voice_override=None):
        response = VoiceResponse()
        self._create_say_element(response, text, language, voice_override)
        response.hangup()
        return str(response)
    
    def generate_transfer_twiml(self, text, language='en', voice_override=None):
        response = VoiceResponse()
        self._create_say_element(response, text, language, voice_override)
        
        if not Config.AGENT_PHONE_NUMBER:
            response.hangup()
        else:
            dial = Dial(
                caller_id=Config.TWILIO_PHONE_NUMBER,
                timeout=30,
                action=f'{Config.BASE_URL}/api/call/handle-transfer-status',
                method='POST'
            )
            dial.number(Config.AGENT_PHONE_NUMBER)
            response.append(dial)
        
        return str(response)

    def generate_hangup_for_machine_twiml(self):
        response = VoiceResponse()
        response.hangup()
        return str(response)