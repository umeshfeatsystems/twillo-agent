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
import time
from google.cloud import speech
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("StreamRoutes")

router = APIRouter(prefix="/api/call", tags=["Streaming"])

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
    logger.info("🔌 [WS] Connected")
    
    audio_queue = queue.Queue()
    stream_sid = None
    session_id = None
    stop_event = threading.Event()
    loop = asyncio.get_event_loop() 

    # --- HELPER: SEND AUDIO ---
    async def send_audio_packet(text):
        if not text: return
        try:
            # Generate MULAW audio
            audio_bytes = google_tts_service.synthesize_to_mulaw(text)
            if not audio_bytes: return

            payload = base64.b64encode(audio_bytes).decode('utf-8')
            
            await websocket.send_json({
                "event": "media",
                "streamSid": stream_sid,
                "media": {"payload": payload}
            })
        except Exception as e:
            logger.error(f"Error sending audio: {e}")

    # --- HELPER: SEND HANGUP MARK ---
    async def send_hangup_mark():
        logger.info("🚩 [WS] Sending 'end_call' mark...")
        await websocket.send_json({
            "event": "mark",
            "streamSid": stream_sid,
            "mark": {"name": "end_call"}
        })

    # --- SYNC THREAD: GOOGLE STT & AI STREAMING ---
    def stt_processing_thread():
        logger.info("🧵 [THREAD] STT Processor Started")
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

                user_text = result.alternatives[0].transcript.strip()
                if not user_text: continue
                
                logger.info(f"🗣️ [USER] {user_text}")
                start_time = time.time() # Latency Timer

                # 1. Setup Context
                session = CallSession.find_by_session_id(session_id) if session_id else None
                system_prompt = session.get('system_prompt', "You are a helpful assistant.") if session else "You are a helpful assistant."
                history = session.get('conversation_history', []) if session else []

                # 2. Call Streaming API
                response_generator = gemini_service.get_streaming_response(
                    system_prompt=system_prompt,
                    conversation_history=history,
                    user_input=user_text
                )

                # 3. Stream & Sentence Buffer Loop
                current_sentence = ""
                full_response_text = ""
                first_chunk_sent = False

                for chunk in response_generator:
                    current_sentence += chunk
                    full_response_text += chunk
                    
                    # Check for sentence endings to send audio IMMEDIATELY
                    if any(punct in current_sentence for punct in [". ", "? ", "! "]):
                        clean_text = current_sentence.strip()
                        if clean_text:
                            # Send Audio for this sentence
                            asyncio.run_coroutine_threadsafe(
                                send_audio_packet(clean_text), loop
                            )
                            
                            # Log Latency only for the FIRST sentence
                            if not first_chunk_sent:
                                latency = time.time() - start_time
                                logger.info(f"⚡ [TTS] First Sentence Sent. Latency: {latency:.3f}s")
                                first_chunk_sent = True
                                
                        current_sentence = "" # Reset buffer

                # 4. Send any remaining text in buffer
                if current_sentence.strip():
                    asyncio.run_coroutine_threadsafe(
                        send_audio_packet(current_sentence.strip()), loop
                    )

                logger.info(f"🤖 [BOT FULL] {full_response_text}")

                # 5. Update History
                if session_id:
                    CallSession.append_history(session_id, {"role": "user", "content": user_text})
                    CallSession.append_history(session_id, {"role": "assistant", "content": full_response_text})

                # 6. Heuristic Hangup Logic (Since we lost JSON)
                # If bot says "Goodbye" or "Have a great day", we hang up.
                lower_text = full_response_text.lower()
                if "goodbye" in lower_text or "have a great day" in lower_text or "thank you" in lower_text:
                    asyncio.run_coroutine_threadsafe(send_hangup_mark(), loop)

        except Exception as e:
            logger.error(f"❌ [THREAD] STT Error: {e}")
        finally:
            logger.info("🧵 [THREAD] STT Processor Ended")

    stt_thread = threading.Thread(target=stt_processing_thread)
    stt_thread.start()

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data['event'] == 'start':
                stream_sid = data['start']['streamSid']
                session_id = data['start']['customParameters'].get('session_id')
                logger.info(f"🚀 [WS] Stream Started. SID: {stream_sid}")
                
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
                    logger.info("👋 [WS] Hangup mark received. Closing.")
                    await websocket.close()
                    break

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
        stop_event.set()