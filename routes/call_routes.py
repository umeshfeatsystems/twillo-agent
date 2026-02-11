from fastapi import APIRouter, Form, Response
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from services.twilio_service import TwilioService
from models.session import CallSession
from prompts import PROMPT_LIBRARY, get_prompt_templates, render_prompt
from config import Config
from utils.audio_cache import AudioCache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CallRoutes")

router = APIRouter(prefix="/api/call", tags=["Call Logic"])
twilio_service = TwilioService()

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


def normalize_language_mode(value: Optional[str]) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        raw = (Config.DEFAULT_LANGUAGE or "en").strip().lower()
    return LANGUAGE_MODE_ALIASES.get(raw, "en")


class CallRequest(BaseModel):
    phone_number: str
    call_details: Dict[str, Any] = Field(default_factory=dict)
    call_type: str = "emi_reminder"
    language_mode: Optional[str] = None
    system_prompt_template: Optional[str] = None
    initial_greeting_template: Optional[str] = None

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
    """
    Called when the user picks up.
    Returns TwiML to connect to the WebSocket stream.
    """
    logger.info(f" [HANDLE-ANSWER] Session: {session_id}")
    
    session = CallSession.find_by_session_id(session_id)
    if not session: 
        return Response(status_code=404)

    # Return Streaming TwiML
    twiml = twilio_service.generate_stream_twiml(session_id)
    return Response(content=twiml, media_type="application/xml")

@router.post('/status')
async def call_status(CallSid: str = Form(...), CallStatus: str = Form(...)):
    logger.info(f" [STATUS] SID: {CallSid} | Status: {CallStatus}")
    return Response(status_code=200)

# Keep the TTS audio route for legacy/fallback support if needed
@router.get('/tts-audio/{filename}')
async def serve_tts_audio(filename: str):
    audio_data = AudioCache.get_with_wait(filename, timeout=5)
    if audio_data is None: return Response(status_code=404)
    return Response(content=audio_data, media_type='audio/mpeg')
