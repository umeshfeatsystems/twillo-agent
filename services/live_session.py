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
        self.customer_id = None

    def _build_system_instruction(self, customer_id):
        customer = Customer.find_by_id(customer_id)
        name = customer.get('name', 'Rohan') if customer else "Rohan"
        amount = customer.get('bank_details', {}).get('pending_emi_amount', 15000) if customer else 15000
        
        return f"""
        You are Amit, a bank recovery agent. 
        You are talking to {name} about a pending amount of Rs. {amount}.
        
        INSTRUCTIONS:
        - Your goal is to get a "Promise to Pay" date.
        - Speak naturally in Hinglish (Hindi + English).
        - Keep your responses short (under 10 seconds).
        - Listen patiently.
        
        STARTING LINE:
        "Namaste {name} ji, main Amit baat kar raha hoon bank se. Kya meri baat {name} ji se ho rahi hai?"
        """

    async def connect_and_stream(self):
        try:
            # 1. Wait for Twilio Start
            while True:
                msg = await self.twilio_ws.receive_text()
                data = json.loads(msg)
                if data['event'] == 'start':
                    logger.info(f"✅ Twilio Stream Started: {data['start']['streamSid']}")
                    self.stream_sid = data['start']['streamSid']
                    self.customer_id = data['start']['customParameters'].get('customer_id')
                    break
                elif data['event'] == 'stop':
                    return

            sys_instr = self._build_system_instruction(self.customer_id)
            
            # 2. Config
            # Note: If 'gemini-2.5-...' fails, try 'gemini-2.0-flash-exp'
            config = {
                "response_modalities": ["AUDIO"], 
                "system_instruction": types.Content(parts=[types.Part(text=sys_instr)]),
            }
            
            # 3. Connect
            async with self.client.aio.live.connect(model=Config.GEMINI_MODEL_ID, config=config) as session:
                logger.info("✅ Connected to Gemini Live API")
                
                # 4. Trigger the greeting (Send text command to start)
                await session.send(input="Start conversation.", end_of_turn=True)
                
                # 5. Start parallel tasks
                receive_task = asyncio.create_task(self._twilio_rx(session), name="Twilio-Receive")
                send_task = asyncio.create_task(self._gemini_rx(session), name="Gemini-Receive")
                
                # 6. Keep Alive Loop
                # We wait until one of the tasks FAILS or FINISHES.
                done, pending = await asyncio.wait(
                    [receive_task, send_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in done:
                    if task.exception():
                        logger.error(f"❌ Task '{task.get_name()}' Error: {task.exception()}")
                    else:
                        logger.info(f"ℹ️ Task '{task.get_name()}' finished normally.")

                for task in pending: task.cancel()

        except Exception as e:
            logger.error(f"❌ Session Error: {e}")
        finally:
            try: await self.twilio_ws.close()
            except: pass

    async def _twilio_rx(self, session):
        """
        User Audio -> Gemini
        """
        try:
            async for msg in self.twilio_ws.iter_text():
                data = json.loads(msg)
                
                if data['event'] == 'media':
                    chunk = base64.b64decode(data['media']['payload'])
                    pcm_data = self.transcoder.process_twilio_to_gemini(chunk)
                    
                    if pcm_data:
                        # [CORRECTED] Pass types.Blob DIRECTLY to input
                        # Do NOT wrap it in types.Part()
                        await session.send(
                            input=types.Blob(
                                data=pcm_data, 
                                mime_type="audio/pcm;rate=16000"
                            ),
                            end_of_turn=False 
                        )
                        
                elif data['event'] == 'stop':
                    logger.info("🛑 Twilio Stop Event")
                    break
        except Exception as e:
            logger.error(f"❌ Twilio RX Error: {e}")

    async def _gemini_rx(self, session):
        """
        Gemini Audio -> Twilio
        """
        try:
            async for res in session.receive():
                if res.server_content and res.server_content.model_turn:
                    for part in res.server_content.model_turn.parts:
                        if part.inline_data:
                            # Convert 24k -> 8k
                            mulaw = self.transcoder.process_gemini_to_twilio(part.inline_data.data)
                            b64 = base64.b64encode(mulaw).decode('utf-8')
                            
                            await self.twilio_ws.send_text(json.dumps({
                                "event": "media", 
                                "streamSid": self.stream_sid, 
                                "media": {"payload": b64}
                            }))
            
            logger.warning("⚠️ Gemini Server closed the connection (Fin received)")
            
        except Exception as e:
            logger.error(f"❌ Gemini RX Error: {e}")