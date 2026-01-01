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
from google.cloud import speech
from config import Config

# Configure Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StreamRoutes")

router = APIRouter(prefix="/api/call", tags=["Streaming"])

# --- AUDIO CONFIGURATION ---
# Twilio sends audio as 8000Hz MULAW
STT_CONFIG = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
    sample_rate_hertz=8000,
    language_code="en-IN",
    model="telephony",
    use_enhanced=True
)

STREAMING_CONFIG = speech.StreamingRecognitionConfig(
    config=STT_CONFIG,
    interim_results=False # We only care about final sentences
)

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("🔌 [WS] Connected")
    
    # Thread-safe queue for audio chunks (Bridge between Async WS and Sync Google)
    audio_queue = queue.Queue()
    
    # Stream State
    stream_sid = None
    session_id = None
    stop_event = threading.Event()
    loop = asyncio.get_event_loop() # Reference to main loop for sending back data

    # --- 1. HELPER: SEND AUDIO BACK TO TWILIO ---
    async def send_audio_packet(text):
        """Synthesizes text to audio and sends it to Twilio"""
        if not text: return
        try:
            # Generate MULAW audio
            audio_bytes = google_tts_service.synthesize_to_mulaw(text)
            if not audio_bytes: return

            # Encode to Base64
            payload = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Send Media Message
            await websocket.send_json({
                "event": "media",
                "streamSid": stream_sid,
                "media": {"payload": payload}
            })
        except Exception as e:
            logger.error(f"Error sending audio: {e}")

    # --- 2. SYNC THREAD: GOOGLE STT & AI LOGIC ---
    def stt_processing_thread():
        logger.info("🧵 [THREAD] STT Processor Started")
        client = speech.SpeechClient()

        def request_generator():
            """Yields audio chunks from the queue to Google"""
            while not stop_event.is_set():
                # Blocking get with timeout to allow checking stop_event
                try:
                    chunk = audio_queue.get(timeout=1.0)
                    if chunk is None: return
                    yield speech.StreamingRecognizeRequest(audio_content=chunk)
                except queue.Empty:
                    continue

        try:
            # Start Google STT Stream
            responses = client.streaming_recognize(
                config=STREAMING_CONFIG,
                requests=request_generator()
            )

            # Process Results (Blocking Loop)
            for response in responses:
                if not response.results: continue
                
                result = response.results[0]
                if not result.is_final: continue

                # A. GET USER TEXT
                user_text = result.alternatives[0].transcript.strip()
                logger.info(f"🗣️ [USER] {user_text}")
                
                if not user_text: continue

                # B. GET AI RESPONSE (Gemini)
                # Fetch session prompt
                session = CallSession.find_by_session_id(session_id) if session_id else None
                system_prompt = session.get('system_prompt', "You are a helpful assistant.") if session else "You are a helpful assistant."
                history = session.get('conversation_history', []) if session else []

                # Call Gemini (Sync call is fine in this thread)
                ai_decision = gemini_service.get_generic_response(
                    system_prompt=system_prompt,
                    conversation_history=history,
                    user_input=user_text
                )
                
                bot_text = ai_decision.get('response_text', "I didn't catch that.")
                logger.info(f"🤖 [BOT] {bot_text}")

                # C. UPDATE DB (Thread-safe manner? Ideally yes, but skipping strict locking for demo)
                if session_id:
                    CallSession.append_history(session_id, {"role": "user", "content": user_text})
                    CallSession.append_history(session_id, {"role": "assistant", "content": bot_text})

                # D. SEND AUDIO BACK (Must schedule on Main Async Loop)
                if stream_sid:
                    asyncio.run_coroutine_threadsafe(
                        send_audio_packet(bot_text), 
                        loop
                    )
                    
        except Exception as e:
            logger.error(f"❌ [THREAD] STT Error: {e}")
        finally:
            logger.info("🧵 [THREAD] STT Processor Ended")

    # --- 3. MAIN ASYNC LOOP: WEBSOCKET HANDLER ---
    
    # Start the STT thread
    stt_thread = threading.Thread(target=stt_processing_thread)
    stt_thread.start()

    try:
        while True:
            # Receive Message from Twilio
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data['event'] == 'start':
                stream_sid = data['start']['streamSid']
                session_id = data['start']['customParameters'].get('session_id')
                logger.info(f"🚀 [WS] Stream Started. SID: {stream_sid} | Session: {session_id}")
                
                # Send Initial Greeting
                if session_id:
                    session = CallSession.find_by_session_id(session_id)
                    if session and session.get('initial_greeting'):
                        await send_audio_packet(session['initial_greeting'])

            elif data['event'] == 'media':
                # Receive Audio Chunk (Base64) -> Decode -> Push to Queue
                if not stop_event.is_set():
                    chunk = base64.b64decode(data['media']['payload'])
                    audio_queue.put(chunk)

            elif data['event'] == 'stop':
                logger.info("🛑 [WS] Stream Stopped")
                stop_event.set()
                break
                
    except WebSocketDisconnect:
        logger.info("🔌 [WS] Disconnected")
        stop_event.set()
    except Exception as e:
        logger.error(f"❌ [WS] Critical Error: {e}")
        stop_event.set()
    finally:
        # Cleanup
        stop_event.set()
        # stt_thread.join() # Optional: wait for thread to close