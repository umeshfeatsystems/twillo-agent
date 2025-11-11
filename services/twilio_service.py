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
        
        # ONLY Google TTS - no fallback
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
        """Normalize text for TTS"""
        text = ' '.join(text.split())
        if text and text[-1] not in '.!?':
            text += '.'
        return text
    
    def _save_audio_file(self, audio_base64, filename):
        """Save audio to file and return URL"""
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
    
    def _create_say_element(self, response, text, language='en'):
        """Create TTS element using ONLY Google Cloud TTS"""
        normalized_text = self._normalize_script_for_tts(text)
        
        try:
            # Generate audio using Google Cloud TTS
            audio_base64 = google_tts_service.synthesize_speech(normalized_text, language)
            
            # Save audio file
            filename = f"{uuid.uuid4().hex}.mp3"
            audio_url = self._save_audio_file(audio_base64, filename)
            
            # Play the audio
            print(f"[GOOGLE TTS] Playing: {audio_url}")
            response.play(audio_url)
            
        except Exception as e:
            print(f"✗ CRITICAL: Google TTS failed: {e}")
            # Re-raise the exception instead of falling back
            raise Exception(f"Google Cloud TTS synthesis failed: {e}")
    
    def generate_language_selection_twiml(self, customer_id, is_repeat=False):
        """Generate IVR menu using Google TTS only"""
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
        
        try:
            # Generate IVR audio using Google TTS (Hindi)
            audio_base64 = google_tts_service.synthesize_speech(message, 'hi')
            filename = f"ivr_{uuid.uuid4().hex}.mp3"
            audio_url = self._save_audio_file(audio_base64, filename)
            
            print(f"[GOOGLE TTS] IVR audio: {audio_url}")
            gather.play(audio_url)
            
        except Exception as e:
            print(f"✗ CRITICAL: Failed to generate IVR audio: {e}")
            raise Exception(f"IVR generation failed: {e}")
        
        response.append(gather)
        response.redirect(f'{Config.BASE_URL}/api/call/language-selected?customer_id={customer_id}', method='POST')
        
        print(f"[TWILIO] Generated language selection TwiML")
        return str(response)
    
    def generate_initial_twiml(self, script_text, customer_id, language='en'):
        """Generate initial TwiML with speech recognition"""
        response = VoiceResponse()
        
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
        
        response.redirect(f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}', method='POST')
        
        print(f"[TWILIO] Generated initial TwiML in {language}")
        return str(response)
    
    def generate_followup_twiml(self, followup_text, customer_id, language='en'):
        """Generate follow-up TwiML with speech recognition"""
        response = VoiceResponse()
        
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
        
        response.redirect(f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}', method='POST')
        
        print(f"[TWILIO] Generated followup TwiML in {language}")
        return str(response)
    
    def generate_goodbye_twiml(self, text, language='en'):
        """Generate goodbye TwiML"""
        response = VoiceResponse()
        self._create_say_element(response, text, language)
        response.hangup()
        print(f"[TWILIO] Generated goodbye TwiML in {language}")
        return str(response)
    
    def generate_hangup_for_machine_twiml(self):
        """Generate hangup TwiML for answering machines"""
        response = VoiceResponse()
        response.hangup()
        return str(response)
    
    def generate_transfer_twiml(self, text, language='en'):
        """Generate transfer TwiML"""
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
        """Generate say-and-redirect TwiML"""
        response = VoiceResponse()
        self._create_say_element(response, text, language)
        response.redirect(redirect_url, method='POST')
        print(f"[TWILIO] Generated Say-and-Redirect TwiML in {language}")
        return str(response)