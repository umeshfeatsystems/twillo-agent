from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from config import Config
import uuid

class TwilioService:
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        self.from_number = Config.TWILIO_PHONE_NUMBER
        
    def initiate_call(self, to_number, customer_id):
        call_ref = f"CALL-{uuid.uuid4().hex[:8].upper()}"
        callback_url = f"{Config.BASE_URL}/api/call/handle-answer?customer_id={customer_id}"
        
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.from_number,
                url=callback_url,
                method='POST',
                # [FIX] REMOVED machine_detection='Enable' 
                # This ensures a direct connection immediately.
            )
            return {'success': True, 'call_sid': call.sid, 'call_ref': call_ref}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate_stream_twiml(self, customer_id):
        response = VoiceResponse()
        # [OPTIONAL] You can remove this .say() if you want it to be instant silence before AI speaks
        response.say("Connecting you now.") 
        
        connect = Connect()
        stream_url = f"{Config.BASE_URL.replace('https', 'wss').replace('http', 'wss')}/voice/stream"
        
        stream = Stream(url=stream_url)
        stream.parameter(name="customer_id", value=customer_id)
        
        connect.append(stream)
        response.append(connect)
        
        return str(response)

    def generate_hangup_for_machine_twiml(self):
        # This is no longer used but kept for safety
        response = VoiceResponse()
        response.hangup()
        return str(response)