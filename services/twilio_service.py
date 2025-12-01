from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from config import Config
from language_config import LanguageConfig
from services.google_tts_service import google_tts_service
import uuid
import os
import base64

class TwilioService:
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        self.from_number = Config.TWILIO_PHONE_NUMBER
        
        if not google_tts_service.client:
            raise Exception("Google Cloud TTS is required but not available")
        
        if not os.path.exists('tts_cache'):
            os.makedirs('tts_cache')
        
        print("✓ TwilioService initialized with Google Cloud TTS only")
    
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
                machine_detection='Disable',
                record=True,
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
        text = ' '.join(text.split())
        if text and text[-1] not in '.!?':
            text += '.'
        return text
    
    def _save_audio_file(self, audio_base64, filename):
        try:
            audio_bytes = base64.b64decode(audio_base64)
            filepath = os.path.join('tts_cache', filename)
            
            with open(filepath, 'wb') as f:
                f.write(audio_bytes)
            
            audio_url = f"{Config.BASE_URL}/api/call/tts-audio/{filename}"
            print(f"✓ Audio saved: {filename}")
            return audio_url
        except Exception as e:
            print(f"✗ Error saving audio file: {e}")
            raise Exception(f"Failed to save audio: {e}")
    
    def _create_say_element(self, response, text, language='en', voice_override=None):
        normalized_text = self._normalize_script_for_tts(text)
        try:
            # Pass voice_override to Google TTS
            audio_base64 = google_tts_service.synthesize_speech(normalized_text, language, voice_override)
            filename = f"{uuid.uuid4().hex}.mp3"
            audio_url = self._save_audio_file(audio_base64, filename)
            print(f"[GOOGLE TTS] Playing: {audio_url}")
            response.play(audio_url)
        except Exception as e:
            print(f"✗ CRITICAL: Google TTS failed: {e}")
            raise Exception(f"Google Cloud TTS synthesis failed: {e}")
    
    def generate_initial_twiml(self, script_text, customer_id, language='en', voice_override=None, stt_language=None):
        """Generate initial TwiML - Play audio THEN listen"""
        response = VoiceResponse()
        
        # 1. Play the bot's message (TTS uses 'language')
        self._create_say_element(response, script_text, language, voice_override)
        
        # 2. Listen (STT uses 'stt_language' if provided, else defaults to 'language')
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
        
        print(f"[TWILIO] Generated initial TwiML. TTS: {language} | STT: {target_stt_lang}")
        return str(response)
    
    def generate_followup_twiml(self, followup_text, customer_id, language='en', voice_override=None, stt_language=None):
        """Generate follow-up TwiML"""
        response = VoiceResponse()
        
        # 1. Play audio (TTS uses 'language')
        self._create_say_element(response, followup_text, language, voice_override)
        
        # 2. Listen (STT uses 'stt_language' if provided, else defaults to 'language')
        # CRITICAL FIX: This allows us to speak Hindi but listen in Hybrid mode
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
        
        print(f"[TWILIO] Generated followup TwiML. TTS: {language} | STT: {target_stt_lang}")
        return str(response)
    
    def generate_goodbye_twiml(self, text, language='en', voice_override=None):
        response = VoiceResponse()
        self._create_say_element(response, text, language, voice_override)
        response.hangup()
        return str(response)
    
    def generate_hangup_for_machine_twiml(self):
        response = VoiceResponse()
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
    
    def generate_say_and_redirect_twiml(self, text, redirect_url, language='en', voice_override=None):
        response = VoiceResponse()
        self._create_say_element(response, text, language, voice_override)
        response.redirect(redirect_url, method='POST')
        return str(response)