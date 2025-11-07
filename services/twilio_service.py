from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from config import Config
from language_config import LanguageConfig
import uuid

class TwilioService:
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        self.from_number = Config.TWILIO_PHONE_NUMBER
        
        self.PROSODY_RATE = '95%'
    
    def initiate_call(self, to_number, customer_id):
        """Initiate an outbound call"""
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
        """Normalize script for consistent TTS"""
        text = ' '.join(text.split())
        if text and text[-1] not in '.!?':
            text += '.'
        return text
    
    def _create_say_element(self, response, text, language='en'):
        """
        Create <Say> element with language-specific voice.
        
        Args:
            response: VoiceResponse or Gather object
            text: Text to speak
            language: 'en' or 'hi'
        """
        normalized_text = self._normalize_script_for_tts(text)
        lang_config = LanguageConfig.get_language_config(language)
        
        ssml_text = f'<speak><prosody rate="{self.PROSODY_RATE}">{normalized_text}</prosody></speak>'
        
        response.say(
            ssml_text,
            voice=lang_config['voice'],
            language=lang_config['locale']
        )
    
    def generate_language_selection_twiml(self, customer_id, is_repeat=False):
        """
        Generate IVR menu for language selection.
        
        Args:
            customer_id: Customer ID
            is_repeat: If True, use shorter repeat message
        """
        response = VoiceResponse()
        
        gather = Gather(
            action=f'{Config.BASE_URL}/api/call/language-selected?customer_id={customer_id}',
            method='POST',
            input='dtmf',
            timeout=LanguageConfig.IVR_MENU['timeout'],
            num_digits=LanguageConfig.IVR_MENU['num_digits'],
            finish_on_key=LanguageConfig.IVR_MENU['finish_on_key']
        )
        
        if is_repeat:
            message = LanguageConfig.IVR_INVALID_MESSAGE + " " + LanguageConfig.IVR_REPEAT_MESSAGE
        else:
            message = LanguageConfig.IVR_WELCOME_MESSAGE
        
        ssml_message = f'<speak><prosody rate="85%">{message}</prosody></speak>'
        
        gather.say(
            ssml_message,
            voice='Polly.Aditi',
            language='hi-IN'
        )
        
        response.append(gather)
        
        response.redirect(
            f'{Config.BASE_URL}/api/call/language-selected?customer_id={customer_id}',
            method='POST'
        )
        
        print(f"[TWILIO] Generated language selection TwiML")
        return str(response)
    
    def generate_initial_twiml(self, script_text, customer_id, language='en'):
        """
        Generate TwiML for initial greeting with language support.
        """
        response = VoiceResponse()
        
        lang_config = LanguageConfig.get_language_config(language)
        stt_config = LanguageConfig.get_stt_config(language)
        
        gather = Gather(
            action=f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST',
            input='speech',
            timeout=5,
            speech_timeout='auto',
            language=stt_config['language'],
            speechModel='phone_call',
            hints=stt_config['hints']
        )
        
        self._create_say_element(gather, script_text, language)
        response.append(gather)
        
        response.redirect(
            f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST'
        )
        
        print(f"[TWILIO] Generated initial TwiML in {language}")
        return str(response)
    
    def generate_followup_twiml(self, followup_text, customer_id, language='en'):
        """Generate TwiML for follow-up responses"""
        response = VoiceResponse()
        
        lang_config = LanguageConfig.get_language_config(language)
        stt_config = LanguageConfig.get_stt_config(language)
        
        gather = Gather(
            action=f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST',
            input='speech',
            timeout=5,
            speech_timeout='auto',
            language=stt_config['language'],
            speechModel='phone_call',
            hints=stt_config['hints']
        )
        
        self._create_say_element(gather, followup_text, language)
        response.append(gather)
        
        response.redirect(
            f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST'
        )
        
        print(f"[TWILIO] Generated followup TwiML in {language}")
        return str(response)
    
    def generate_goodbye_twiml(self, text, language='en'):
        """Generate TwiML to end call"""
        response = VoiceResponse()
        self._create_say_element(response, text, language)
        response.hangup()
        print(f"[TWILIO] Generated goodbye TwiML in {language}")
        return str(response)
    
    def generate_hangup_for_machine_twiml(self):
        """Generate TwiML for answering machine detection"""
        response = VoiceResponse()
        response.hangup()
        return str(response)
    
    def generate_transfer_twiml(self, text, language='en'):
        """Generate TwiML to transfer call"""
        response = VoiceResponse()
        
        self._create_say_element(response, text, language)
        
        if not Config.AGENT_PHONE_NUMBER:
            fallback_text = (
                "I apologize, but we're unable to transfer your call at this moment. "
                "We'll have a specialist call you back within the next hour. "
                "Thank you for your patience."
            ) if language == 'en' else (
                "मुझे खेद है, लेकिन हम इस समय आपका कॉल ट्रांसफर नहीं कर पा रहे हैं। "
                "अगले एक घंटे में एक स्पेशलिस्ट आपको वापस कॉल करेंगे। "
                "आपके धैर्य के लिए धन्यवाद।"
            )
            self._create_say_element(response, fallback_text, language)
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
        
        print(f"[TWILIO] Generated transfer TwiML in {language}")
        return str(response)
    
    def generate_say_and_redirect_twiml(self, text, redirect_url, language='en'):
        """
        Generate TwiML to say a message and redirect.
        Used for fast webhooks.
        """
        response = VoiceResponse()
        self._create_say_element(response, text, language)
        response.redirect(redirect_url, method='POST')
        print(f"[TWILIO] Generated Say-and-Redirect TwiML in {language}")
        return str(response)