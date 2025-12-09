import asyncio
import json
import base64
import logging
import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google import genai
from google.genai import types
from config import Config

try:
    from core.audio_transcoder import AudioTranscoder
except ImportError:
    try:
        from services.audio import AudioTranscoder
    except ImportError:
        import core.audio_transcoder as AudioTranscoder

try:
    from customer import Customer
except ImportError:
    try:
        from models.customer import Customer
    except ImportError:
        import customer
        Customer = customer.Customer

logger = logging.getLogger("LIVE_SESSION")

class LiveSession:
    def __init__(self, twilio_ws):
        self.twilio_ws = twilio_ws
        self.transcoder = AudioTranscoder()
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
        self.stream_sid = None
        self.customer_id = None
        self.session_start_time = 0
        self.is_active = True
        self.audio_sent_count = 0

    def _build_system_instruction(self, customer_id):
        customer = Customer.find_by_id(customer_id)
        name = customer.get('name', 'Rohan') if customer else "Rohan"
        amount = customer.get('bank_details', {}).get('pending_emi_amount', 15000) if customer else 15000
        
        return f"""You are Amit, a friendly bank recovery agent speaking with {name} about Rs. {amount} pending EMI.

CRITICAL INSTRUCTIONS:
1. ALWAYS speak in Hinglish (natural Hindi-English mix) - this is MANDATORY
2. Keep each response under 8 seconds
3. Be conversational and listen actively
4. Never hang up unless user says goodbye/bye
5. Start immediately with your greeting

OPENING LINE (say now in Hinglish):
"Namaste {name} ji, main Amit bol raha hoon bank se. Aapka Rs. {amount} ka EMI pending hai. Kya aap abhi baat kar sakte hain?"

IMPORTANT: Respond naturally in Hinglish to everything the user says."""

    async def connect_and_stream(self):
        try:
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
            
            config = {
                "generation_config": {
                    "response_modalities": ["AUDIO"],
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {"voice_name": "Puck"}
                        }
                    }
                },
                "system_instruction": sys_instr
            }
            
            async with self.client.aio.live.connect(model=Config.GEMINI_MODEL_ID, config=config) as session:
                logger.info("✅ Connected to Gemini Live API")
                self.session_start_time = time.time()
                
                await asyncio.sleep(0.5)
                await session.send(input="start", end_of_turn=True)
                
                await asyncio.gather(
                    self._twilio_rx(session),
                    self._gemini_rx(session)
                )

        except Exception as e:
            logger.error(f"❌ Session Error: {e}", exc_info=True)
        finally:
            self.is_active = False
            try: 
                await self.twilio_ws.close()
            except: 
                pass

    async def _twilio_rx(self, session):
        """User Audio -> Gemini"""
        buffer = bytearray()
        chunk_size = 640
        silence_count = 0
        max_silence = 50
        
        try:
            async for msg in self.twilio_ws.iter_text():
                if not self.is_active:
                    break
                    
                data = json.loads(msg)
                
                if data['event'] == 'media':
                    elapsed = time.time() - self.session_start_time
                    if elapsed < 1.5:
                        continue

                    chunk = base64.b64decode(data['media']['payload'])
                    
                    if len(chunk) > 0:
                        buffer.extend(chunk)
                        silence_count = 0
                    else:
                        silence_count += 1
                    
                    if len(buffer) >= chunk_size:
                        pcm_data = self.transcoder.process_twilio_to_gemini_8k(bytes(buffer))
                        
                        if pcm_data and len(pcm_data) > 0:
                            try:
                                await session.send(
                                    input={"mime_type": "audio/pcm", "data": pcm_data},
                                    end_of_turn=False
                                )
                                self.audio_sent_count += 1
                                if self.audio_sent_count % 50 == 0:
                                    logger.debug(f"Sent {self.audio_sent_count} audio chunks")
                            except Exception as e:
                                logger.error(f"Error sending audio: {e}")
                        
                        buffer.clear()
                    
                    if silence_count > max_silence and len(buffer) > 0:
                        pcm_data = self.transcoder.process_twilio_to_gemini_8k(bytes(buffer))
                        if pcm_data:
                            await session.send(
                                input={"mime_type": "audio/pcm", "data": pcm_data},
                                end_of_turn=True
                            )
                        buffer.clear()
                        silence_count = 0
                        
                elif data['event'] == 'stop':
                    self.is_active = False
                    break
                    
        except Exception as e:
            logger.error(f"❌ Twilio RX Error: {e}", exc_info=True)
            self.is_active = False

    async def _gemini_rx(self, session):
        """Gemini Audio -> Twilio"""
        audio_received = False
        
        try:
            async for res in session.receive():
                if not self.is_active:
                    break
                
                if res.data:
                    audio_received = True
                    mulaw = self.transcoder.process_gemini_to_twilio(res.data)
                    
                    if mulaw and len(mulaw) > 0:
                        b64 = base64.b64encode(mulaw).decode('utf-8')
                        await self.twilio_ws.send_text(json.dumps({
                            "event": "media",
                            "streamSid": self.stream_sid,
                            "media": {"payload": b64}
                        }))
                
                elif res.server_content and res.server_content.model_turn:
                    for part in res.server_content.model_turn.parts:
                        if part.inline_data and part.inline_data.data:
                            audio_received = True
                            mulaw = self.transcoder.process_gemini_to_twilio(part.inline_data.data)
                            
                            if mulaw and len(mulaw) > 0:
                                b64 = base64.b64encode(mulaw).decode('utf-8')
                                await self.twilio_ws.send_text(json.dumps({
                                    "event": "media",
                                    "streamSid": self.stream_sid,
                                    "media": {"payload": b64}
                                }))
                
                if res.server_content and res.server_content.turn_complete:
                    logger.debug("Turn complete")
            
            if audio_received:
                logger.info("Session ended normally")
            else:
                logger.warning("⚠️ No audio received from Gemini before closure")
            
        except Exception as e:
            logger.error(f"❌ Gemini RX Error: {e}", exc_info=True)
            self.is_active = False