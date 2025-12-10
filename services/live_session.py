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

    def _build_system_instruction(self, customer_id):
        customer = Customer.find_by_id(customer_id)
        name = customer.get('name', 'Rohan') if customer else "Rohan"
        amount = customer.get('bank_details', {}).get('pending_emi_amount', 15000) if customer else 15000
        
        return f"""You are Amit, a friendly bank recovery agent speaking with {name} about Rs. {amount} pending EMI.

CRITICAL INSTRUCTIONS:
1. ALWAYS speak in English (natural Hindi-English mix) - this is MANDATORY
2. Keep each response under 8 seconds
3. Be conversational and listen actively
4. Never hang up unless user says goodbye/bye
5. Respond immediately when user speaks

OPENING LINE (say now in English):
"Namaste {name} ji, main Amit bol raha hoon bank se. Aapka Rs. {amount} ka EMI pending hai. Kya aap abhi baat kar sakte hain?"

IMPORTANT: Always respond in English. Listen carefully and reply naturally."""

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
                "response_modalities": ["AUDIO"],
                "system_instruction": types.Content(
                    parts=[types.Part(text=sys_instr)]
                ),
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {"voice_name": "Puck"}
                    }
                },
                "realtime_input_config": {
                    "automatic_activity_detection": {
                        "disabled": False,
                        "start_of_speech_sensitivity": "START_SENSITIVITY_HIGH",
                        "end_of_speech_sensitivity": "END_SENSITIVITY_LOW",
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500
                    }
                }
            }
            
            async with self.client.aio.live.connect(model=Config.GEMINI_MODEL_ID, config=config) as session:
                logger.info("✅ Connected to Gemini Live API")
                self.session_start_time = time.time()
                
                # Send trigger to make bot speak first
                await session.send(
                    input="You are on a call. Greet the customer now in English as instructed.", 
                    end_of_turn=True
                )
                
                await asyncio.gather(
                    self._twilio_rx(session),
                    self._gemini_rx(session)
                )

        except Exception as e:
            logger.error(f"❌ Session Error: {e}", exc_info=True)
        finally:
            self.is_active = False
            logger.info("🔴 Closing session...")
            try: 
                await self.twilio_ws.close()
            except: 
                pass

    async def _twilio_rx(self, session):
        """User Audio -> Gemini using send_realtime_input at 16kHz"""
        buffer = bytearray()
        min_chunk = 160  # 160 bytes µ-law = 20ms at 8kHz -> 40ms at 16kHz after resampling
        audio_sent_count = 0
        
        try:
            async for msg in self.twilio_ws.iter_text():
                if not self.is_active:
                    logger.info(f"📊 Total audio chunks sent to Gemini: {audio_sent_count}")
                    break
                    
                data = json.loads(msg)
                
                if data['event'] == 'media':
                    elapsed = time.time() - self.session_start_time
                    if elapsed < 1.0:
                        continue

                    chunk = base64.b64decode(data['media']['payload'])
                    
                    if len(chunk) > 0:
                        buffer.extend(chunk)
                    
                    if len(buffer) >= min_chunk:
                        # CRITICAL: Use the new 16kHz resampling method
                        pcm_data = self.transcoder.process_twilio_to_gemini_16k(bytes(buffer))
                        
                        if pcm_data and len(pcm_data) > 0:
                            try:
                                await session.send_realtime_input(
                                    audio=types.Blob(
                                        data=pcm_data,
                                        mime_type="audio/pcm;rate=16000"  # CHANGED FROM 8000 to 16000
                                    )
                                )
                                audio_sent_count += 1
                                if audio_sent_count == 1:
                                    logger.info(f"🎤 First audio chunk sent to Gemini (size: {len(pcm_data)} bytes)")
                                if audio_sent_count % 50 == 0:
                                    logger.debug(f"📤 Sent {audio_sent_count} audio chunks to Gemini")
                            except Exception as e:
                                logger.error(f"Error sending audio: {e}")
                        
                        buffer.clear()
                        
                elif data['event'] == 'stop':
                    self.is_active = False
                    logger.info(f"📊 Total audio chunks sent to Gemini: {audio_sent_count}")
                    break
                    
        except Exception as e:
            logger.error(f"❌ Twilio RX Error: {e}", exc_info=True)
            self.is_active = False
            logger.info(f"📊 Total audio chunks sent to Gemini: {audio_sent_count}")

    async def _gemini_rx(self, session):
        """Gemini Audio (24kHz) -> Twilio (8kHz µ-law)"""
        audio_received = False
        audio_sent_count = 0
        
        try:
            async for response in session.receive():
                if not self.is_active:
                    break
                
                if response.data:
                    audio_received = True
                    if audio_sent_count == 0:
                        logger.info("🔊 First audio response from Gemini received!")
                    
                    mulaw = self.transcoder.process_gemini_to_twilio(response.data)
                    
                    if mulaw and len(mulaw) > 0:
                        b64 = base64.b64encode(mulaw).decode('utf-8')
                        await self.twilio_ws.send_text(json.dumps({
                            "event": "media",
                            "streamSid": self.stream_sid,
                            "media": {"payload": b64}
                        }))
                        audio_sent_count += 1
                        if audio_sent_count % 20 == 0:
                            logger.debug(f"📢 Sent {audio_sent_count} audio chunks to Twilio")
                
                if response.server_content and response.server_content.turn_complete:
                    logger.debug("✓ Turn complete - waiting for user response")
                    # Don't close - just log that turn is complete
            
            logger.info(f"📊 Total audio chunks sent to Twilio: {audio_sent_count}")
            
            if audio_received:
                logger.info("Session ended - Gemini stream closed")
            else:
                logger.warning("⚠️ No audio received from Gemini before closure")
            
            # DON'T signal other task to stop - let it continue listening
            
        except Exception as e:
            logger.error(f"❌ Gemini RX Error: {e}", exc_info=True)
            self.is_active = False