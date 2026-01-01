from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from config import Config
from services.google_tts_service import google_tts_service
from utils.audio_cache import AudioCache
import uuid
import base64

class TwilioService:
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        self.from_number = Config.TWILIO_PHONE_NUMBER
        if not google_tts_service.client:
            print("⚠ Warning: Google Cloud TTS not initialized.")
        else:
            print("✓ TwilioService initialized")
    
    def initiate_call(self, to_number, session_id):
        try:
            # We still point to handle-answer to start the flow
            callback_url = f"{Config.BASE_URL}/api/call/handle-answer?session_id={session_id}"
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.from_number,
                url=callback_url,
                method='POST',
                status_callback=f"{Config.BASE_URL}/api/call/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                machine_detection='Enable', 
                timeout=30
            )
            return {'success': True, 'call_sid': call.sid}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate_stream_twiml(self, session_id):
        """
        Generates TwiML to connect to the WebSocket Stream.
        """
        response = VoiceResponse()
        
        # Connect to WebSocket
        connect = response.connect()
        
        # Build WSS URL (Handle http/https switch)
        base_domain = Config.BASE_URL.replace("https://", "").replace("http://", "")
        stream_url = f"wss://{base_domain}/api/call/stream"
        
        stream = connect.stream(url=stream_url)
        # Pass Session ID to the WebSocket so we know who it is
        stream.parameter(name="session_id", value=session_id)
        
        return str(response)

    # ... (Keep existing prepare_audio_placeholder, generate_audio_background etc for fallback) ...
    def prepare_audio_placeholder(self):
        filename = f"{uuid.uuid4().hex}.mp3"
        AudioCache.reserve_key(filename)
        return filename

    def generate_audio_background(self, text, filename, language='en', voice_override=None):
        if not text:
            AudioCache.set(filename, b'')
            return
        try:
            audio_base64 = google_tts_service.synthesize_speech(text, language, voice_override)
            if audio_base64:
                AudioCache.set(filename, base64.b64decode(audio_base64))
            else:
                AudioCache.set(filename, b'')
        except Exception:
            AudioCache.set(filename, b'')

    def generate_async_twiml(self, audio_filename, session_id):
        # Legacy HTTP method (Keep in case you want to switch back)
        from twilio.twiml.voice_response import Gather
        response = VoiceResponse()
        gather = Gather(
            action=f'{Config.BASE_URL}/api/call/process-response?session_id={session_id}',
            method='POST',
            input='speech',
            timeout=5,
            speechTimeout='auto',
            bargeIn=True
        )
        audio_url = f"{Config.BASE_URL}/api/call/tts-audio/{audio_filename}"
        gather.play(audio_url)
        response.append(gather)
        return str(response)
    
    def generate_goodbye_twiml(self, text):
        response = VoiceResponse()
        if text: response.say(text)
        response.hangup()
        return str(response)