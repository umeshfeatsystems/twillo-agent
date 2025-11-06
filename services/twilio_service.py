from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial, Redirect
from config import Config
from datetime import datetime
import uuid

class TwilioService:
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        self.from_number = Config.TWILIO_PHONE_NUMBER
    
    def initiate_call(self, to_number, customer_id):
        """Initiate an outbound call to the customer"""
        try:
            call_ref = f"CALL-{uuid.uuid4().hex[:8].upper()}"
            
            callback_url = f"{Config.BASE_URL}/api/call/handle-answer?customer_id={customer_id}&call_ref={call_ref}"
            status_callback_url = f"{Config.BASE_URL}/api/call/status"
            recording_status_callback_url = f"{Config.BASE_URL}/api/call/handle-recording"
            
            print(f"[TWILIO] Initiating call to {to_number}")
            print(f"[TWILIO] Callback URL: {callback_url}")
            
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
    
    def generate_initial_twiml(self, script_text, customer_id):
        """
        Generate TwiML for the initial greeting.
        """
        response = VoiceResponse()
        
        # Create a Gather to capture speech
        gather = Gather(
            input='speech',
            action=f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST',
            timeout=5,
            speech_timeout='auto',
            language='en-IN',
            # --- STT FIX #1 ---
            speechModel='phone_call',  # Use model trained for phone audio
            # --- STT FIX #2 ---
            hints='yes, no, speaking, this is him, this is her, wrong number, Rajesh Kumar, who is this, I am Rajesh, yes I am, this is Rajesh'
        )
        
        gather.say(
            script_text,
            voice='Polly.Aditi',
            language='en-IN'
        )
        
        response.append(gather)
        
        # Fallback if no input is detected
        response.redirect(
            f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST'
        )
        
        twiml_str = str(response)
        print(f"[TWILIO] Generated initial TwiML ({len(twiml_str)} chars)")
        return twiml_str
    
    def generate_followup_twiml(self, followup_text, customer_id):
        """
        Generate TwiML for follow-up responses in the conversation.
        """
        response = VoiceResponse()

        # Create Gather for next response
        gather = Gather(
            input='speech',
            action=f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST',
            timeout=5,
            speech_timeout='auto',
            language='en-IN',
            # --- STT FIX #1 ---
            speechModel='phone_call',  # Use model trained for phone audio
            # --- STT FIX #2 ---
            hints='yes, no, payment, pay, tomorrow, today, later, manager, transfer, help, problem, lost my job, supervisor, agent, speak to manager, speak to an agent, partial payment, payment plan, extension'
        )

        gather.say(
            followup_text,
            voice='Polly.Aditi',
            language='en-IN'
        )
        
        response.append(gather)
        
        # Fallback if no response
        response.redirect(
            f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST'
        )
        
        twiml_str = str(response)
        print(f"[TWILIO] Generated followup TwiML ({len(twiml_str)} chars)")
        return twiml_str
    
    def generate_goodbye_twiml(self, text):
        """Generate TwiML to end the call with a specific message"""
        response = VoiceResponse()
        response.say(
            text,
            voice='Polly.Aditi',
            language='en-IN'
        )
        response.hangup()
        
        twiml_str = str(response)
        print(f"[TWILIO] Generated goodbye TwiML")
        return twiml_str
    
    def generate_hangup_for_machine_twiml(self):
        """Generate TwiML for when an answering machine is detected"""
        response = VoiceResponse()
        response.hangup()
        return str(response)

    # --- THIS IS THE MODIFIED FUNCTION ---
    def generate_transfer_twiml(self, text):
        """
        Generate TwiML to say a message and then transfer the call to a human agent.
        """
        response = VoiceResponse()
        
        response.say(
            text,
            voice='Polly.Aditi',
            language='en-IN'
        )
        
        if not Config.AGENT_PHONE_NUMBER:
            response.say(
                "I apologize, but we're unable to transfer your call at this moment. We'll have a specialist call you back within the next hour. Thank you for your patience.",
                voice='Polly.Aditi',
                language='en-IN'
            )
            response.hangup()
        else:
            dial = Dial(
                caller_id=Config.TWILIO_PHONE_NUMBER,
                timeout=30,
                # --- THIS IS THE FIX ---
                # Point 'action' to our new logic-handling webhook
                action=f'{Config.BASE_URL}/api/call/handle-transfer-status',
                method='POST'
            )
            dial.number(Config.AGENT_PHONE_NUMBER)
            response.append(dial)
            
            # --- THIS IS THE FIX ---
            # We REMOVE the TwiML after the <Dial>.
            # The 'action' webhook now handles all post-dial logic.
        
        twiml_str = str(response)
        print(f"[TWILIO] Generated transfer TwiML (with new action webhook)")
        return twiml_str
    
    def generate_say_and_redirect_twiml(self, text, redirect_url):
        """
        Generate TwiML to say a message and then immediately redirect.
        This is a "Fast" webhook.
        """
        response = VoiceResponse()
        
        response.say(
            text,
            voice='Polly.Aditi',
            language='en-IN'
        )
        
        response.redirect(
            redirect_url,
            method='POST'
        )
        
        twiml_str = str(response)
        print(f"[TWILIO] Generated Say-and-Redirect TwiML (Music: False)")
        return twiml_str