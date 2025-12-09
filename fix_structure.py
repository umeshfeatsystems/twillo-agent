import os

# This script forces the correct content into your files to fix the ImportErrors.

files = {
    # 1. THE MODEL (Fixes 'cannot import Customer')
    "models/customer.py": """
from datetime import datetime
from utils.db import db_instance

class Customer:
    collection_name = 'customers'
    
    @staticmethod
    def get_collection():
        if db_instance._db is None: db_instance.connect()
        return db_instance._db[Customer.collection_name]
    
    @staticmethod
    def find_by_id(customer_id):
        return Customer.get_collection().find_one({'customer_id': customer_id})
    
    @staticmethod
    def update_call_history(customer_id, call_record):
        Customer.get_collection().update_one(
            {'customer_id': customer_id},
            {'$push': {'call_history': call_record}}
        )
""",

    # 2. THE UTILS (Database Connection)
    "utils/db.py": """
from pymongo import MongoClient
from config import Config

class Database:
    _instance = None
    _client = None
    _db = None
    
    def connect(self):
        if self._client is None:
            self._client = MongoClient(Config.MONGODB_URI)
            self._db = self._client.get_default_database()
            print("✓ MongoDB Connected")

db_instance = Database()
""",

    # 3. THE LIVE SESSION (Fixes 'multilingual_script_templates' error)
    "services/live_session.py": """
import asyncio
import json
import base64
import logging
from google import genai
from google.genai import types
from config import Config
from core.audio_transcoder import AudioTranscoder
from models.customer import Customer

logger = logging.getLogger("LIVE_SESSION")

class LiveSession:
    def __init__(self, twilio_ws):
        self.twilio_ws = twilio_ws
        self.transcoder = AudioTranscoder()
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
        self.stream_sid = None
        self.is_active = True

    def _build_system_instruction(self, customer_id):
        # Fetch Data
        customer = Customer.find_by_id(customer_id)
        if not customer: return "System: Customer not found."
        
        details = customer.get('bank_details', {})
        amount = details.get('pending_emi_amount', 0)
        name = customer.get('name', 'Customer')
        
        return f\"\"\"
        You are Amit, a Recovery Agent for {Config.BANK_NAME}.
        Speak to {name} about pending amount Rs. {amount}.
        Speak naturally in Hinglish. Keep it short.
        \"\"\"

    async def connect_and_stream(self):
        try:
            # Wait for Twilio Start
            msg = await self.twilio_ws.receive_text()
            data = json.loads(msg)
            if data['event'] != 'start': return
            
            self.stream_sid = data['start']['streamSid']
            c_id = data['start']['customParameters'].get('customer_id')
            
            # Connect Gemini
            sys_instr = self._build_system_instruction(c_id)
            config = {"response_modalities": ["AUDIO"], "system_instruction": types.Content(parts=[types.Part(text=sys_instr)])}
            
            async with self.client.aio.live.connect(model=Config.GEMINI_MODEL_ID, config=config) as session:
                await session.send(input="Start call.", end_of_turn=True)
                await asyncio.gather(self._twilio_rx(session), self._gemini_rx(session))
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            try: await self.twilio_ws.close()
            except: pass

    async def _twilio_rx(self, session):
        try:
            async for msg in self.twilio_ws.iter_text():
                data = json.loads(msg)
                if data['event'] == 'media':
                    chunk = base64.b64decode(data['media']['payload'])
                    pcm = self.transcoder.process_twilio_to_gemini(chunk)
                    await session.send_realtime_input(audio=types.Blob(data=pcm, mime_type="audio/pcm;rate=16000"))
                elif data['event'] == 'stop': break
        except: pass

    async def _gemini_rx(self, session):
        try:
            async for res in session.receive():
                if res.server_content and res.server_content.model_turn:
                    for part in res.server_content.model_turn.parts:
                        if part.inline_data:
                            mulaw = self.transcoder.process_gemini_to_twilio(part.inline_data.data)
                            b64 = base64.b64encode(mulaw).decode('utf-8')
                            await self.twilio_ws.send_text(json.dumps({"event": "media", "streamSid": self.stream_sid, "media": {"payload": b64}}))
        except: pass
"""
}

def repair():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Repaired: {path}")

if __name__ == "__main__":
    repair()