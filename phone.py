import os
from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
from dotenv import load_dotenv

load_dotenv()

# Your public ngrok URL (Must be updated every time you restart ngrok)
# Do not include the trailing slash (e.g., https://abc-123.ngrok-free.app)
SERVER_URL = "https://YOUR-NGROK-ID.ngrok-free.app"

def make_outbound_call(to_number):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    print(f"📞 Dialing {to_number}...")
    
    call = client.calls.create(
        to=to_number,
        from_=TWILIO_PHONE_NUMBER,
        # This URL tells Twilio: "Once they answer, connect to our Voice Stream"
        url=f"{SERVER_URL}/voice/incoming" 
    )

    print(f"✅ Call initiated! SID: {call.sid}")

if __name__ == "__main__":
    # Replace with the mobile number you want to call
    TARGET_NUMBER = "+15550001234" 
    make_outbound_call(TARGET_NUMBER)