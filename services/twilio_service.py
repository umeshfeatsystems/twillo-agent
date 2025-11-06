from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from config import Config
import uuid

class TwilioService:
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        self.from_number = Config.TWILIO_PHONE_NUMBER
        
        # ============================================
        # TTS OPTIMIZATION CONFIG
        # ============================================
        # Use consistent voice settings across ALL responses
        self.VOICE_CONFIG = {
            'voice': 'Polly.Aditi',  # Indian English female voice
            'language': 'en-IN',
            # NEW: Add prosody control for consistency
            'rate': '95%',  # Slightly slower for clarity (was default 100%)
            # Using SSML for advanced control would be ideal, but keeping it simple
        }
        
        # STT (Speech Recognition) optimization
        self.STT_CONFIG = {
            'input': 'speech',
            'timeout': 5,
            'speech_timeout': 'auto',
            'language': 'en-IN',
            'speechModel': 'phone_call',  # Optimized for phone audio
            # Enhanced hints for better recognition
            'hints': (
                'yes, no, speaking, this is him, this is her, wrong number, '
                'payment, pay, tomorrow, today, later, week, month, '
                'manager, supervisor, agent, transfer, help, '
                'lost job, financial problem, extension, dispute, '
                'paid already, will pay, cannot pay'
            )
        }
    
    def initiate_call(self, to_number, customer_id):
        """Initiate an outbound call to the customer"""
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
        """
        Normalize script text for consistent TTS delivery.
        Ensures consistent punctuation and formatting.
        """
        # Remove extra spaces
        text = ' '.join(text.split())
        
        # Ensure sentences end with proper punctuation
        if text and text[-1] not in '.!?':
            text += '.'
        
        # Add natural pauses with commas (if not present)
        # Example: "Hello this is a call from" -> "Hello, this is a call from"
        # This is already handled in templates, but double-check
        
        return text
    
    def _create_say_element(self, response, text):
        """
        Create a <Say> element with consistent voice configuration.
        This ensures ALL spoken text sounds the same.
        """
        normalized_text = self._normalize_script_for_tts(text)
        
        # Use SSML for better prosody control
        ssml_text = f'<speak><prosody rate="{self.VOICE_CONFIG["rate"]}">{normalized_text}</prosody></speak>'
        
        response.say(
            ssml_text,
            voice=self.VOICE_CONFIG['voice'],
            language=self.VOICE_CONFIG['language']
        )
    
    def generate_initial_twiml(self, script_text, customer_id):
        """Generate TwiML for initial greeting with optimized voice"""
        response = VoiceResponse()
        
        gather = Gather(
            action=f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST',
            **self.STT_CONFIG
        )
        
        # Use consistent voice configuration
        self._create_say_element(gather, script_text)
        
        response.append(gather)
        
        # Fallback
        response.redirect(
            f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST'
        )
        
        twiml_str = str(response)
        print(f"[TWILIO] Generated initial TwiML ({len(twiml_str)} chars)")
        return twiml_str
    
    def generate_followup_twiml(self, followup_text, customer_id):
        """Generate TwiML for follow-up responses with optimized voice"""
        response = VoiceResponse()
        
        gather = Gather(
            action=f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST',
            **self.STT_CONFIG
        )
        
        # Use consistent voice configuration
        self._create_say_element(gather, followup_text)
        
        response.append(gather)
        
        # Fallback
        response.redirect(
            f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST'
        )
        
        twiml_str = str(response)
        print(f"[TWILIO] Generated followup TwiML ({len(twiml_str)} chars)")
        return twiml_str
    
    def generate_goodbye_twiml(self, text):
        """Generate TwiML to end call with optimized voice"""
        response = VoiceResponse()
        self._create_say_element(response, text)
        response.hangup()
        
        print(f"[TWILIO] Generated goodbye TwiML")
        return str(response)
    
    def generate_hangup_for_machine_twiml(self):
        """Generate TwiML for answering machine detection"""
        response = VoiceResponse()
        response.hangup()
        return str(response)
    
    def generate_transfer_twiml(self, text):
        """Generate TwiML to transfer call with optimized voice"""
        response = VoiceResponse()
        
        self._create_say_element(response, text)
        
        if not Config.AGENT_PHONE_NUMBER:
            fallback_text = (
                "I apologize, but we're unable to transfer your call at this moment. "
                "We'll have a specialist call you back within the next hour. "
                "Thank you for your patience."
            )
            self._create_say_element(response, fallback_text)
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
        
        print(f"[TWILIO] Generated transfer TwiML")
        return str(response)
    
    def generate_say_and_redirect_twiml(self, text, redirect_url):
        """
        Generate TwiML to say a message and redirect.
        Used for "fast" webhooks with consistent voice.
        """
        response = VoiceResponse()
        
        self._create_say_element(response, text)
        
        response.redirect(redirect_url, method='POST')
        
        print(f"[TWILIO] Generated Say-and-Redirect TwiML")
        return str(response)