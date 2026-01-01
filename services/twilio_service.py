from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from config import Config
from language_config import LanguageConfig
from services.google_tts_service import google_tts_service
from utils.audio_cache import AudioCache
import uuid
import base64

class TwilioService:
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        self.from_number = Config.TWILIO_PHONE_NUMBER
        
        # We still need TTS to generate speech
        if not google_tts_service.client:
            print("Warning: Google Cloud TTS not initialized. Calls may fail if TTS is needed.")
        else:
            print("TwilioService initialized (Generic Pipeline Enabled)")
    
    def initiate_call(self, to_number, session_id):
        try:
            # The callback now passes session_id
            callback_url = f"{Config.BASE_URL}/api/call/handle-answer?session_id={session_id}"
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.from_number,
                url=callback_url,
                method='POST',
                status_callback=f"{Config.BASE_URL}/api/call/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                machine_detection='Enable', # Enable to detect voicemail vs human
                timeout=30
            )
            return {'success': True, 'call_sid': call.sid}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def prepare_audio_placeholder(self):
        filename = f"{uuid.uuid4().hex}.mp3"
        AudioCache.reserve_key(filename)
        return filename

    def generate_audio_background(self, text, filename, language='en', voice_override=None):
        if not text or not text.strip():
            AudioCache.set(filename, b'')
            return

        try:
            # 1. Normalize Text
            text = ' '.join(text.split())
            if text and text[-1] not in '.!?':
                text += '.'
                
            # 2. Call Google TTS
            # Note: You can customize language/voice here if you pass them from the session
            audio_base64 = google_tts_service.synthesize_speech(text, language, voice_override)
            
            # 3. Store in Cache (Releases the lock for the waiting request)
            audio_bytes = base64.b64decode(audio_base64)
            AudioCache.set(filename, audio_bytes)
            print(f"[BG TASK] Audio generated: {filename}")
            
        except Exception as e:
            print(f"[BG TASK] TTS Generation Failed: {e}")
            AudioCache.set(filename, b'')

    def generate_async_twiml(self, audio_filename, session_id):
        response = VoiceResponse()
        
        gather = Gather(
            action=f'{Config.BASE_URL}/api/call/process-response?session_id={session_id}',
            method='POST',
            input='speech',
            
            # 1. INCREASE WAIT TIME: Give user 10s to start speaking (prevents early silence errors)
            timeout=10, 
            
            # 2. TUNE END OF SPEECH: 'auto' is slow. '1.0' is snappier.
            # If users get cut off, increase to '1.5'. If laggy, decrease to '0.8'.
            speechTimeout='1.0',
            
            language='en-IN',
            speechModel='phone_call', 
            enhanced=True,            
            bargeIn=True
        )
        
        # Play audio INSIDE gather (Barge-In)
        audio_url = f"{Config.BASE_URL}/api/call/tts-audio/{audio_filename}"
        gather.play(audio_url)

        response.append(gather)
        
        # Fallback loop (Only redirects if user was TRULY silent for 10s)
        response.redirect(f'{Config.BASE_URL}/api/call/process-response?session_id={session_id}', method='POST')
        
        return str(response)

    def generate_goodbye_twiml(self, text):
        response = VoiceResponse()
        if text:
            try:
                audio_base64 = google_tts_service.synthesize_speech(text)
                filename = f"{uuid.uuid4().hex}.mp3"
                AudioCache.set(filename, base64.b64decode(audio_base64))
                response.play(f"{Config.BASE_URL}/api/call/tts-audio/{filename}")
            except:
                response.say(text)
        
        response.hangup()
        return str(response)

    def generate_transfer_twiml(self, text, transfer_number=None):
        """Transfers the call to an agent."""
        response = VoiceResponse()
        
        # Announce transfer
        if text:
            try:
                audio_base64 = google_tts_service.synthesize_speech(text)
                filename = f"{uuid.uuid4().hex}.mp3"
                AudioCache.set(filename, base64.b64decode(audio_base64))
                response.play(f"{Config.BASE_URL}/api/call/tts-audio/{filename}")
            except:
                response.say(text)

        # Dial the number
        target_number = transfer_number or Config.AGENT_PHONE_NUMBER
        if target_number:
            dial = Dial(caller_id=self.from_number)
            dial.number(target_number)
            response.append(dial)
        else:
            response.say("Transfer number not configured. Goodbye.")
            response.hangup()
            
        return str(response)

    def generate_hangup_for_machine_twiml(self):
        """Hangs up immediately if a machine is detected."""
        response = VoiceResponse()
        response.hangup()
        return str(response)