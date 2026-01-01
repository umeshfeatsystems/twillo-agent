from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.gemini_service import gemini_service
from services.google_tts_service import google_tts_service
from models.session import CallSession
import json
import asyncio
import base64
import logging
import queue
import threading
import time  # <--- Added for latency calculation
from google.cloud import speech
from config import Config

# --- 1. CONFIGURE LOGGER WITH TIMESTAMPS ---
# This ensures every log line has a precise time (e.g., 14:30:05.123)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("StreamRoutes")

router = APIRouter(prefix="/api/call", tags=["Streaming"])

# --- AUDIO CONFIGURATION ---
STT_CONFIG = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
    sample_rate_hertz=8000,
    language_code="en-IN",
    model="telephony",
    use_enhanced=False
)

STREAMING_CONFIG = speech.StreamingRecognitionConfig(
    config=STT_CONFIG,
    interim_results=False 
)

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info(" [WS] Connected")
    
    audio_queue = queue.Queue()
    stream_sid = None
    session_id = None
    stop_event = threading.Event()
    loop = asyncio.get_event_loop() 

    # --- HELPER: SEND AUDIO & MARK ---
    async def send_audio_packet(text, should_hangup=False):
        if not text: return
        try:
            # Generate MULAW audio
            audio_bytes = google_tts_service.synthesize_to_mulaw(text)
            if not audio_bytes: return

            # Encode
            payload = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Send Media
            await websocket.send_json({
                "event": "media",
                "streamSid": stream_sid,
                "media": {"payload": payload}
            })

            # Handle Hangup Mark
            if should_hangup:
                logger.info(" [WS] Sending 'end_call' mark...")
                await websocket.send_json({
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "end_call"}
                })
                
        except Exception as e:
            logger.error(f"Error sending audio: {e}")

    # --- SYNC THREAD: GOOGLE STT & AI ---
    def stt_processing_thread():
        logger.info(" [THREAD] STT Processor Started")
        client = speech.SpeechClient()

        def request_generator():
            while not stop_event.is_set():
                try:
                    chunk = audio_queue.get(timeout=1.0)
                    if chunk is None: return
                    yield speech.StreamingRecognizeRequest(audio_content=chunk)
                except queue.Empty:
                    continue

        try:
            responses = client.streaming_recognize(
                config=STREAMING_CONFIG,
                requests=request_generator()
            )

            for response in responses:
                if not response.results: continue
                result = response.results[0]
                if not result.is_final: continue

                # A. GET USER TEXT & START TIMER
                user_text = result.alternatives[0].transcript.strip()
                if not user_text: continue
                
                # <--- START TIMER
                start_time = time.time() 
                logger.info(f"[USER] {user_text}")

                # Get Session & AI Response
                session = CallSession.find_by_session_id(session_id) if session_id else None
                system_prompt = session.get('system_prompt', "You are a helpful assistant.") if session else "You are a helpful assistant."
                history = session.get('conversation_history', []) if session else []

                ai_decision = gemini_service.get_generic_response(
                    system_prompt=system_prompt,
                    conversation_history=history,
                    user_input=user_text
                )
                
                bot_text = ai_decision.get('response_text', "I didn't catch that.")
                should_hangup = ai_decision.get('should_hangup', False)

                # <--- STOP TIMER & CALCULATE LATENCY
                latency = time.time() - start_time
                logger.info(f" [BOT] {bot_text} | Latency: {latency:.3f}s | Hangup: {should_hangup}")

                if session_id:
                    CallSession.append_history(session_id, {"role": "user", "content": user_text})
                    CallSession.append_history(session_id, {"role": "assistant", "content": bot_text})

                # Send Back to Main Loop
                if stream_sid:
                    asyncio.run_coroutine_threadsafe(
                        send_audio_packet(bot_text, should_hangup), 
                        loop
                    )
                    
        except Exception as e:
            logger.error(f"❌ [THREAD] STT Error: {e}")
        finally:
            logger.info(" [THREAD] STT Processor Ended")

    # --- MAIN ASYNC LOOP ---
    stt_thread = threading.Thread(target=stt_processing_thread)
    stt_thread.start()

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data['event'] == 'start':
                stream_sid = data['start']['streamSid']
                session_id = data['start']['customParameters'].get('session_id')
                logger.info(f" [WS] Stream Started. SID: {stream_sid}")
                
                if session_id:
                    session = CallSession.find_by_session_id(session_id)
                    if session and session.get('initial_greeting'):
                        await send_audio_packet(session['initial_greeting'])

            elif data['event'] == 'media':
                if not stop_event.is_set():
                    chunk = base64.b64decode(data['media']['payload'])
                    audio_queue.put(chunk)
            
            elif data['event'] == 'mark':
                if data['mark']['name'] == 'end_call':
                    logger.info(" [WS] 'end_call' mark received. Closing connection.")
                    await websocket.close()
                    break

            elif data['event'] == 'stop':
                logger.info("🛑 [WS] Stream Stopped")
                stop_event.set()
                break
                
    except WebSocketDisconnect:
        logger.info(" [WS] Disconnected")
        stop_event.set()
    except Exception as e:
        logger.error(f"❌ [WS] Critical Error: {e}")
        stop_event.set()
    finally:
        stop_event.set()