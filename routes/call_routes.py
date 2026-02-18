import asyncio
import audioop
import base64
import json
import logging
import queue
import re
import threading
import time
from typing import Dict, Any, Optional, Iterable

from fastapi import APIRouter, Form, Response, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from config import Config
from models.session import CallSession
from prompts.base import PROMPT_LIBRARY, get_prompt_templates, render_prompt
from services.twilio_service import TwilioService
from services.gemini_service import gemini_service
from services.sarvam_service import sarvam_service
from utils.audio_cache import AudioCache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CallRoutes")

router = APIRouter(prefix="/api/call", tags=["Call Logic"])
twilio_service = TwilioService()


class GenerateDescriptionRequest(BaseModel):
    product_name: str


@router.post("/generate-description")
async def generate_description(req: GenerateDescriptionRequest):
    """Use Gemini to auto-generate a product description from a product name."""
    if not gemini_service.model:
        return {"description": "", "error": "Gemini is not configured"}
    try:
        prompt = f"""You are an expert sales copywriter. A sales agent will read this description 
to a prospect over a phone call, so it must be clear, complete, and informative.

Product: "{req.product_name}"

Write a complete product description in exactly 4-5 sentences:
- Sentence 1: What the product is and what it does
- Sentence 2: Who it is designed for (target audience)  
- Sentence 3-4: Key benefits and specific features that set it apart
- Sentence 5: A compelling closing statement about its value

IMPORTANT: You MUST complete every sentence. Do not stop mid-sentence.
Write in plain text only. No bullet points, no markdown, no headings.
Keep it professional, specific, and persuasive."""

        def _call_gemini():
            return gemini_service.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 500,
                    "temperature": 0.7,
                },
            )

        response = await asyncio.to_thread(_call_gemini)
        text = (response.text or "").strip()
        if not text:
            return {"description": "", "error": "Gemini returned empty response"}
        return {"description": text}
    except Exception as exc:
        logger.error("Generate description failed: %s", exc)
        return {"description": "", "error": str(exc)}

# Constants from stream_routes.py
BYTES_PER_SECOND_MULAW = 8000
RMS_SPEECH_THRESHOLD = 300
SILENCE_TIMEOUT_SECONDS = 0.6
MIN_UTTERANCE_SECONDS = 0.5
MAX_UTTERANCE_SECONDS = 7.0

LANGUAGE_MODE_ALIASES = {
    "en": "en",
    "english": "en",
    "en-in": "en",
    "hi": "hi",
    "hindi": "hi",
    "hi-in": "hi",
    "hi-en": "hi-en",
    "hi_en": "hi-en",
    "en-hi-hybrid": "hi-en",
    "hinglish": "hi-en",
    "bilingual": "hi-en",
}

HINDI_HINT_WORDS = {
    # Common Hindi words in Roman script
    "haan", "nahi", "namaste", "achha", "theek", "paisa", "kal", "aaj", 
    "baad", "baadme", "kripya", "bhai", "sirf", "kyu", "kyun", "kab", 
    "kaise", "mera", "meri", "mujhe", "aap", "hum",
    # Very common Hinglish
    "ji", "bilkul", "kya", "hai", "ho", "hu", "hoon", "bola", "bolo", "bolraha",
    "naa", "na", "thik", "thodi", "abhi", "phir", "matlab", "woh", "yeh",
    "kuch", "kaha", "kahe", "arre", "are", "matlab", "baat", "batao", "samjhe",
    "chahiye", "chahta", "chahti", "karo", "karna", "karenge", "karoge",
    "dena", "denge", "diya", "lena", "lenge", "liya", "paise", "rupaye",
    "bank", "payment", "emi", "loan", "bhugtan", "de", "le", "kar", "karo"
}

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

# Helper functions
def normalize_language_mode(value: Optional[str]) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        raw = (Config.DEFAULT_LANGUAGE or "en").strip().lower()
    return LANGUAGE_MODE_ALIASES.get(raw, "en")

def _to_language_code(value: Optional[str]) -> Optional[str]:
    if not value: return None
    raw = value.strip().lower()
    if raw in ("en", "english", "en-in"): return "en-IN"
    if raw in ("hi", "hindi", "hi-in"): return "hi-IN"
    if raw in ("hi-en", "hi_en", "en-hi-hybrid", "hinglish", "bilingual"): return "en-IN"
    return value

def _resolve_language_mode(session: Optional[dict]) -> str:
    if not session: return "en"
    details = session.get("call_details") or {}
    value = details.get("language_mode") or details.get("language") or details.get("language_code") or "en"
    return normalize_language_mode(value)

def _resolve_initial_language_code(session: Optional[dict], mode: str) -> str:
    details = (session or {}).get("call_details") or {}
    explicit = _to_language_code(
        details.get("greeting_language") or details.get("initial_language") or details.get("preferred_language")
    )
    if explicit: return explicit
    if mode == "hi": return "hi-IN"
    return "en-IN"

def _stt_candidates(mode: str, last_user_language: str) -> Iterable[str]:
    if mode == "en": return ["en-IN"]
    if mode == "hi": return ["hi-IN"]
    first = "hi-IN" if last_user_language == "hi-IN" else "en-IN"
    second = "en-IN" if first == "hi-IN" else "hi-IN"
    return [first, second]

def _detect_user_language(text: str, stt_language: Optional[str]) -> str:
    # Trust Sarvam's STT language detection first
    if stt_language == "hi-IN":
        return "hi-IN"
    
    lowered = text.lower()
    
    # Devanagari script = definitely Hindi
    if DEVANAGARI_RE.search(text):
        return "hi-IN"
    
    # Check for Hindi hint words (even 1 is a strong signal in Indian context)
    tokens = re.findall(r"[a-zA-Z]+", lowered)
    hint_hits = sum(1 for token in tokens if token in HINDI_HINT_WORDS)
    if hint_hits >= 1:  # Lowered threshold from 2 to 1
        return "hi-IN"
    
    return "en-IN"

def _select_response_language(mode: str, user_text: str, stt_language: Optional[str]) -> str:
    if mode == "en": return "en-IN"
    if mode == "hi": return "hi-IN"
    return _detect_user_language(user_text, stt_language)

def _language_instruction(mode: str, response_language: str) -> str:
    if mode == "en": return "LANGUAGE POLICY: Respond only in English."
    if mode == "hi": return "LANGUAGE POLICY: Respond only in Hindi."
    if response_language == "hi-IN": return "LANGUAGE POLICY: This turn must be in Hindi, because the customer spoke Hindi."
    return "LANGUAGE POLICY: This turn must be in English, because the customer spoke English."

def _is_speech_chunk(mulaw_chunk: bytes) -> bool:
    if not mulaw_chunk: return False
    try:
        pcm = audioop.ulaw2lin(mulaw_chunk, 2)
        return audioop.rms(pcm, 2) >= RMS_SPEECH_THRESHOLD
    except Exception: return False

class CallRequest(BaseModel):
    phone_number: str
    call_details: Dict[str, Any] = Field(default_factory=dict)
    call_type: str = "emi_reminder"
    language_mode: Optional[str] = None
    system_prompt_template: Optional[str] = None
    initial_greeting_template: Optional[str] = None

# Routes
@router.post('/initiate')
async def initiate_call(request: CallRequest):
    logger.info(f" [INITIATE] Request for {request.phone_number} | call_type={request.call_type}")
    try:
        prompt_templates, resolved_call_type = get_prompt_templates(request.call_type)
        resolved_language_mode = normalize_language_mode(
            request.language_mode
            or request.call_details.get("language_mode")
            or request.call_details.get("language")
        )

        prompt_context = {
            "name": request.call_details.get('name', 'Customer'),
            "bank_name": request.call_details.get('bank_name', Config.BANK_NAME),
            "amount": request.call_details.get('amount', 'unknown amount'),
            "loan_type": request.call_details.get('loan_type', 'loan'),
            "due_date": request.call_details.get('due_date', 'today'),
            "days_overdue": request.call_details.get('days_overdue', 'unknown')
        }
        prompt_context.update(request.call_details)

        system_template = request.system_prompt_template or prompt_templates["system_prompt"]
        greeting_template = request.initial_greeting_template or prompt_templates["initial_greeting"]

        formatted_system_prompt = render_prompt(system_template, prompt_context)
        formatted_greeting = render_prompt(greeting_template, prompt_context)

        enriched_call_details = dict(request.call_details)
        enriched_call_details["call_type"] = resolved_call_type
        enriched_call_details["requested_call_type"] = request.call_type
        enriched_call_details["language_mode"] = resolved_language_mode

        session_id = CallSession.create(
            phone=request.phone_number,
            system_prompt=formatted_system_prompt,
            initial_greeting=formatted_greeting,
            call_details=enriched_call_details
        )

        # Pre-cache the initial greeting TTS so it's instant when the call connects
        greeting_lang = _resolve_initial_language_code(
            {"call_details": enriched_call_details},
            resolved_language_mode or "en",
        )
        voice = enriched_call_details.get("voice")
        sarvam_service.synthesize_to_mulaw(formatted_greeting, language_code=greeting_lang, voice_override=voice)
        
        result = twilio_service.initiate_call(request.phone_number, session_id)
        
        if result['success']:
            CallSession.update_call_sid(session_id, result['call_sid'])
            return {
                "success": True,
                "session_id": session_id,
                "call_sid": result['call_sid'],
                "call_type": resolved_call_type,
                "language_mode": resolved_language_mode
            }
        else:
            return {"success": False, "error": result['error']}

    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get('/call-types')
async def list_call_types():
    return {
        "success": True,
        "default_call_type": "emi_reminder",
        "supported_call_types": sorted(PROMPT_LIBRARY.keys()),
        "supported_language_modes": ["en", "hi", "hi-en"]
    }

@router.post('/handle-answer')
async def handle_answer(session_id: str):
    logger.info(f" [HANDLE-ANSWER] Session: {session_id}")
    session = CallSession.find_by_session_id(session_id)
    if not session: 
        return Response(status_code=404)

    twiml = twilio_service.generate_stream_twiml(session_id)
    return Response(content=twiml, media_type="application/xml")

@router.post('/status')
async def call_status(CallSid: str = Form(...), CallStatus: str = Form(...)):
    logger.info(f" [STATUS] SID: {CallSid} | Status: {CallStatus}")
    return Response(status_code=200)

@router.get('/tts-audio/{filename}')
async def serve_tts_audio(filename: str):
    audio_data = AudioCache.get_with_wait(filename, timeout=5)
    if audio_data is None: return Response(status_code=404)
    return Response(content=audio_data, media_type='audio/mpeg')

# WebSocket Stream Handler (Merged from stream_routes.py)
@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("[WS] Connected")

    audio_queue: "queue.Queue[Optional[bytes]]" = queue.Queue()
    stream_sid = None
    session_id = None
    stop_event = threading.Event()
    loop = asyncio.get_event_loop()
    hangup_mark_sent = threading.Event()
    language_state = {"last_user_language": "en-IN"}


    min_utterance_bytes = int(BYTES_PER_SECOND_MULAW * MIN_UTTERANCE_SECONDS)
    max_utterance_bytes = int(BYTES_PER_SECOND_MULAW * MAX_UTTERANCE_SECONDS)

    async def send_audio_packet(text: str, language_code: str, voice_override: str = None):
        if not text or not stream_sid or stop_event.is_set(): return
        try:
            tts_start = time.time()
            # Run synchronous TTS in thread pool to avoid blocking event loop
            audio_bytes = await loop.run_in_executor(
                None, sarvam_service.synthesize_to_mulaw, text, language_code, voice_override
            )
            tts_dur = time.time() - tts_start
            if not audio_bytes:
                logger.warning("[LATENCY] TTS returned empty (%.3fs)", tts_dur)
                return
            # Check again after TTS — connection may have closed while synthesizing
            if stop_event.is_set():
                return
            logger.info("[LATENCY] TTS=%.3fs | text=%d chars | audio=%d bytes", tts_dur, len(text), len(audio_bytes))
            payload = base64.b64encode(audio_bytes).decode("utf-8")
            ws_start = time.time()
            await websocket.send_json({
                "event": "media",
                "streamSid": stream_sid,
                "media": {"payload": payload},
            })
            logger.info("[LATENCY] WS-send=%.3fs", time.time() - ws_start)
        except Exception as exc:
            if "close" not in str(exc).lower():
                logger.error("Error sending audio packet: %s", exc)

    async def send_hangup_mark():
        if not stream_sid or hangup_mark_sent.is_set(): return
        try:
            hangup_mark_sent.set()
            await websocket.send_json({
                "event": "mark",
                "streamSid": stream_sid,
                "mark": {"name": "end_call"},
            })
        except Exception as exc:
            logger.error("Error sending hangup mark: %s", exc)

    def stt_processing_thread():
        logger.info("[THREAD] Sarvam STT processor started")
        utterance_buffer = bytearray()
        speech_active = False
        trailing_silence_seconds = 0.0

        def process_utterance(mulaw_audio: bytes):
            if len(mulaw_audio) < min_utterance_bytes: return

            turn_start = time.time()
            audio_duration_s = len(mulaw_audio) / BYTES_PER_SECOND_MULAW

            # --- DB lookup ---
            db_start = time.time()
            session = CallSession.find_by_session_id(session_id) if session_id else None
            db_dur = time.time() - db_start

            mode = _resolve_language_mode(session)
            
            # Check if language already locked (after first turn)
            locked_language = session.get("locked_language") if session else None
            
            if locked_language:
                # Language already locked from first turn — use it
                response_language = locked_language
                candidates = [locked_language]
            else:
                # First turn or no lock — detect language
                candidates = _stt_candidates(mode, language_state["last_user_language"])

            # --- STT ---
            stt_start = time.time()
            user_text, stt_language = sarvam_service.transcribe_mulaw_with_language(mulaw_audio, candidates)
            stt_dur = time.time() - stt_start
            if not user_text:
                logger.info("[LATENCY] STT=%.3fs (no text) | audio=%.2fs", stt_dur, audio_duration_s)
                return

            # Detect and LOCK language on first turn
            if not locked_language:
                response_language = _select_response_language(mode, user_text, stt_language)
                language_state["last_user_language"] = response_language
                # Lock the language in session for all future turns
                if session_id and mode == "hi-en":
                    CallSession.update_session(session_id, {"locked_language": response_language})
                    logger.info("[LANGUAGE LOCKED] %s (based on first response)", response_language)
            
            logger.info("[USER][%s] %s", stt_language or "unknown", user_text)
            logger.info("[LATENCY] DB=%.3fs | STT=%.3fs | audio=%.2fs", db_dur, stt_dur, audio_duration_s)

            base_system_prompt = session.get("system_prompt", "You are a helpful assistant.") if session else "You are a helpful assistant."
            system_prompt = f"{base_system_prompt}\n\n{_language_instruction(mode, response_language)}"
            history = session.get("conversation_history", []) if session else []

            # --- LLM ---
            llm_start = time.time()
            response_generator = gemini_service.get_streaming_response(
                system_prompt=system_prompt,
                conversation_history=history,
                user_input=user_text,
            )

            current_chunk = ""
            full_response_text = ""
            llm_first_chunk_time = None
            MAX_TTS_CHARS = 120

            # Retrieve selected voice from session
            session_voice = (session.get("call_details") or {}).get("voice") if session else None

            # Collect full LLM response — sending ONE TTS call is faster
            # than multiple calls (each has ~1.3s minimum API overhead)
            for chunk in response_generator:
                if not chunk: continue
                if llm_first_chunk_time is None:
                    llm_first_chunk_time = time.time() - llm_start
                full_response_text += chunk

            llm_full_dur = time.time() - llm_start

            # Send the complete response as a single TTS call
            # Only split if response exceeds safety cap (very rare with short prompt)
            clean_response = full_response_text.strip()
            sentence_count = 0
            tts_futures = []
            if clean_response:
                if len(clean_response) <= MAX_TTS_CHARS:
                    sentence_count = 1
                    fut = asyncio.run_coroutine_threadsafe(
                        send_audio_packet(clean_response, response_language, session_voice), loop
                    )
                    tts_futures.append(fut)
                else:
                    # Safety split for unusually long responses
                    remaining = clean_response
                    while remaining:
                        if len(remaining) <= MAX_TTS_CHARS:
                            sentence_count += 1
                            fut = asyncio.run_coroutine_threadsafe(
                                send_audio_packet(remaining, response_language, session_voice), loop
                            )
                            tts_futures.append(fut)
                            remaining = ""
                        else:
                            # Split at last sentence boundary within limit
                            split_at = -1
                            for sep in ('.', '?', '!'):
                                idx = remaining.rfind(sep, 0, MAX_TTS_CHARS)
                                if idx > split_at:
                                    split_at = idx
                            if split_at == -1:
                                split_at = remaining.rfind(' ', 0, MAX_TTS_CHARS)
                            if split_at == -1:
                                split_at = MAX_TTS_CHARS
                            else:
                                split_at += 1  # include the separator
                            piece = remaining[:split_at].strip()
                            if piece:
                                sentence_count += 1
                                fut = asyncio.run_coroutine_threadsafe(
                                    send_audio_packet(piece, response_language, session_voice), loop
                                )
                                tts_futures.append(fut)
                            remaining = remaining[split_at:].strip()

            total_dur = time.time() - turn_start
            logger.info("[BOT][%s] %s", response_language, full_response_text)
            logger.info(
                "[LATENCY] TURN TOTAL=%.3fs | DB=%.3fs | STT=%.3fs | LLM-first=%.3fs | LLM-full=%.3fs | sentences=%d",
                total_dur, db_dur, stt_dur,
                llm_first_chunk_time or 0, llm_full_dur, sentence_count
            )
            if session_id:
                CallSession.append_history(session_id, {"role": "user", "content": user_text})
                CallSession.append_history(session_id, {"role": "assistant", "content": full_response_text})

            lower_text = full_response_text.lower()
            if any(phrase in lower_text for phrase in (
                "goodbye", "good bye", "bye", "have a good day",
                "have a great day", "have a nice day", "take care",
            )):
                # Wait for all TTS audio to be sent before hanging up
                for fut in tts_futures:
                    try:
                        fut.result(timeout=15)
                    except Exception:
                        pass
                # Give Twilio time to play the audio before disconnecting
                time.sleep(1.5)
                asyncio.run_coroutine_threadsafe(send_hangup_mark(), loop)

        while not stop_event.is_set():
            try:
                chunk = audio_queue.get(timeout=0.25)
                if chunk is None: break
                
                chunk_seconds = len(chunk) / BYTES_PER_SECOND_MULAW
                speech_chunk = _is_speech_chunk(chunk)

                if not speech_active and speech_chunk:
                    speech_active = True
                    trailing_silence_seconds = 0.0

                if speech_active:
                    utterance_buffer.extend(chunk)
                    if speech_chunk:
                        trailing_silence_seconds = 0.0
                    else:
                        trailing_silence_seconds += chunk_seconds

                    if len(utterance_buffer) >= max_utterance_bytes or trailing_silence_seconds >= SILENCE_TIMEOUT_SECONDS:
                        process_utterance(bytes(utterance_buffer))
                        utterance_buffer = bytearray()
                        speech_active = False
                        trailing_silence_seconds = 0.0
            except queue.Empty: continue
            except Exception as exc:
                logger.error("[THREAD] STT processing error: %s", exc)

        if utterance_buffer:
            try: process_utterance(bytes(utterance_buffer))
            except Exception: pass

    stt_thread = threading.Thread(target=stt_processing_thread, daemon=True)
    stt_thread.start()

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            event_type = data.get("event")

            if event_type == "start":
                stream_sid = data["start"]["streamSid"]
                session_id = data["start"]["customParameters"].get("session_id")
                logger.info("[WS] Stream started. SID: %s", stream_sid)
                


                if session_id:
                    session = CallSession.find_by_session_id(session_id)
                    if session and session.get("initial_greeting"):
                        mode = _resolve_language_mode(session)
                        greeting_language = _resolve_initial_language_code(session, mode)
                        session_voice = (session.get("call_details") or {}).get("voice")
                        await send_audio_packet(session["initial_greeting"], greeting_language, session_voice)

            elif event_type == "media":
                if not stop_event.is_set():
                    try:
                        chunk = base64.b64decode(data["media"]["payload"])
                        audio_queue.put(chunk)
                        

                                
                    except Exception as exc:
                        logger.error("[WS] Failed to decode media payload: %s", exc)

            elif event_type == "mark":
                if data.get("mark", {}).get("name") == "end_call":
                    logger.info("[WS] Hangup mark received. Closing stream.")
                    await websocket.close()
                    break

            elif event_type == "stop":
                logger.info("[WS] Stream stopped")
                stop_event.set()
                break

    except WebSocketDisconnect:
        logger.info("[WS] Disconnected")
    except Exception as exc:
        logger.error("[WS] Critical websocket error: %s", exc)
    finally:
        stop_event.set()
        audio_queue.put(None)
        if stt_thread.is_alive():
            stt_thread.join(timeout=2)
            

