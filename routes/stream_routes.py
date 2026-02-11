import asyncio
import audioop
import base64
import json
import logging
import queue
import re
import threading
import time
from typing import Iterable, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from models.session import CallSession
from services.gemini_service import gemini_service
from services.sarvam_service import sarvam_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("StreamRoutes")

router = APIRouter(prefix="/api/call", tags=["Streaming"])

BYTES_PER_SECOND_MULAW = 8000
RMS_SPEECH_THRESHOLD = 300
SILENCE_TIMEOUT_SECONDS = 0.8
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
    "haan",
    "nahi",
    "namaste",
    "achha",
    "theek",
    "paisa",
    "kal",
    "aaj",
    "baad",
    "baadme",
    "kripya",
    "kripya",
    "bhai",
    "sirf",
    "kyu",
    "kyun",
    "kab",
    "kaise",
    "mera",
    "meri",
    "mujhe",
    "aap",
    "hum",
    "nahi",
}

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def _normalize_language_mode(value: Optional[str]) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return "en"
    return LANGUAGE_MODE_ALIASES.get(raw, "en")


def _to_language_code(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = value.strip().lower()
    if raw in ("en", "english", "en-in"):
        return "en-IN"
    if raw in ("hi", "hindi", "hi-in"):
        return "hi-IN"
    if raw in ("hi-en", "hi_en", "en-hi-hybrid", "hinglish", "bilingual"):
        return "en-IN"
    return value


def _resolve_language_mode(session: Optional[dict]) -> str:
    if not session:
        return "en"
    details = session.get("call_details") or {}
    value = details.get("language_mode") or details.get("language") or details.get("language_code") or "en"
    return _normalize_language_mode(value)


def _resolve_initial_language_code(session: Optional[dict], mode: str) -> str:
    details = (session or {}).get("call_details") or {}
    explicit = _to_language_code(
        details.get("greeting_language") or details.get("initial_language") or details.get("preferred_language")
    )
    if explicit:
        return explicit
    if mode == "hi":
        return "hi-IN"
    return "en-IN"


def _stt_candidates(mode: str, last_user_language: str) -> Iterable[str]:
    if mode == "en":
        return ["en-IN"]
    if mode == "hi":
        return ["hi-IN"]
    # hi-en mode: try last detected language first for lower latency.
    first = "hi-IN" if last_user_language == "hi-IN" else "en-IN"
    second = "en-IN" if first == "hi-IN" else "hi-IN"
    return [first, second]


def _detect_user_language(text: str, stt_language: Optional[str]) -> str:
    if stt_language in ("en-IN", "hi-IN"):
        # STT language is a strong signal.
        if stt_language == "hi-IN":
            return "hi-IN"

    lowered = text.lower()
    if DEVANAGARI_RE.search(text):
        return "hi-IN"

    tokens = re.findall(r"[a-zA-Z]+", lowered)
    hint_hits = sum(1 for token in tokens if token in HINDI_HINT_WORDS)
    if hint_hits >= 2:
        return "hi-IN"
    return "en-IN"


def _select_response_language(mode: str, user_text: str, stt_language: Optional[str]) -> str:
    if mode == "en":
        return "en-IN"
    if mode == "hi":
        return "hi-IN"
    return _detect_user_language(user_text, stt_language)


def _language_instruction(mode: str, response_language: str) -> str:
    if mode == "en":
        return "LANGUAGE POLICY: Respond only in English."
    if mode == "hi":
        return "LANGUAGE POLICY: Respond only in Hindi."
    if response_language == "hi-IN":
        return "LANGUAGE POLICY: This turn must be in Hindi, because the customer spoke Hindi."
    return "LANGUAGE POLICY: This turn must be in English, because the customer spoke English."


def _is_speech_chunk(mulaw_chunk: bytes) -> bool:
    if not mulaw_chunk:
        return False
    try:
        pcm = audioop.ulaw2lin(mulaw_chunk, 2)
        return audioop.rms(pcm, 2) >= RMS_SPEECH_THRESHOLD
    except Exception:
        return False


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

    async def send_audio_packet(text: str, language_code: str):
        if not text or not stream_sid:
            return

        try:
            audio_bytes = sarvam_service.synthesize_to_mulaw(text, language_code=language_code)
            if not audio_bytes:
                logger.warning("No audio generated for bot text chunk.")
                return

            payload = base64.b64encode(audio_bytes).decode("utf-8")
            await websocket.send_json(
                {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {"payload": payload},
                }
            )
        except Exception as exc:
            logger.error("Error sending audio packet: %s", exc)

    async def send_hangup_mark():
        if not stream_sid or hangup_mark_sent.is_set():
            return
        try:
            hangup_mark_sent.set()
            await websocket.send_json(
                {
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "end_call"},
                }
            )
        except Exception as exc:
            logger.error("Error sending hangup mark: %s", exc)

    def stt_processing_thread():
        logger.info("[THREAD] Sarvam STT processor started")
        utterance_buffer = bytearray()
        speech_active = False
        trailing_silence_seconds = 0.0

        def process_utterance(mulaw_audio: bytes):
            if len(mulaw_audio) < min_utterance_bytes:
                return

            session = CallSession.find_by_session_id(session_id) if session_id else None
            mode = _resolve_language_mode(session)
            candidates = _stt_candidates(mode, language_state["last_user_language"])
            user_text, stt_language = sarvam_service.transcribe_mulaw_with_language(mulaw_audio, candidates)
            if not user_text:
                return

            response_language = _select_response_language(mode, user_text, stt_language)
            language_state["last_user_language"] = response_language

            logger.info("[USER][%s] %s", stt_language or "unknown", user_text)
            start_time = time.time()

            base_system_prompt = (
                session.get("system_prompt", "You are a helpful assistant.")
                if session
                else "You are a helpful assistant."
            )
            system_prompt = f"{base_system_prompt}\n\n{_language_instruction(mode, response_language)}"
            history = session.get("conversation_history", []) if session else []

            response_generator = gemini_service.get_streaming_response(
                system_prompt=system_prompt,
                conversation_history=history,
                user_input=user_text,
            )

            current_sentence = ""
            full_response_text = ""
            first_chunk_sent = False

            for chunk in response_generator:
                if not chunk:
                    continue
                current_sentence += chunk
                full_response_text += chunk

                if current_sentence.rstrip().endswith((".", "?", "!")):
                    clean_text = current_sentence.strip()
                    if clean_text:
                        asyncio.run_coroutine_threadsafe(
                            send_audio_packet(clean_text, response_language),
                            loop,
                        )
                        if not first_chunk_sent:
                            logger.info("[TTS] First sentence latency: %.3fs", time.time() - start_time)
                            first_chunk_sent = True
                    current_sentence = ""

            if current_sentence.strip():
                asyncio.run_coroutine_threadsafe(
                    send_audio_packet(current_sentence.strip(), response_language),
                    loop,
                )

            logger.info("[BOT][%s] %s", response_language, full_response_text)

            if session_id:
                CallSession.append_history(session_id, {"role": "user", "content": user_text})
                CallSession.append_history(session_id, {"role": "assistant", "content": full_response_text})

            lower_text = full_response_text.lower()
            if "goodbye" in lower_text or "have a great day" in lower_text or "thank you" in lower_text:
                asyncio.run_coroutine_threadsafe(send_hangup_mark(), loop)

        while not stop_event.is_set():
            try:
                chunk = audio_queue.get(timeout=0.25)
                if chunk is None:
                    break

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

                    if len(utterance_buffer) >= max_utterance_bytes:
                        process_utterance(bytes(utterance_buffer))
                        utterance_buffer = bytearray()
                        speech_active = False
                        trailing_silence_seconds = 0.0
                        continue

                    if trailing_silence_seconds >= SILENCE_TIMEOUT_SECONDS:
                        process_utterance(bytes(utterance_buffer))
                        utterance_buffer = bytearray()
                        speech_active = False
                        trailing_silence_seconds = 0.0
                        continue
            except queue.Empty:
                continue
            except Exception as exc:
                logger.error("[THREAD] STT processing error: %s", exc)

        if utterance_buffer:
            try:
                process_utterance(bytes(utterance_buffer))
            except Exception as exc:
                logger.error("[THREAD] Final buffer processing failed: %s", exc)

        logger.info("[THREAD] Sarvam STT processor ended")

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
                        await send_audio_packet(session["initial_greeting"], greeting_language)

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
        stop_event.set()
    except Exception as exc:
        logger.error("[WS] Critical websocket error: %s", exc)
        stop_event.set()
    finally:
        stop_event.set()
        audio_queue.put(None)
        if stt_thread.is_alive():
            stt_thread.join(timeout=2)
