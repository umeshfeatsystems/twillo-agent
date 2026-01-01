from fastapi import APIRouter, BackgroundTasks, Form, Request, Response
from pydantic import BaseModel
from typing import Dict, Any
from services.twilio_service import TwilioService
from models.session import CallSession
from prompts import SYSTEM_PROMPT_TEMPLATE, INITIAL_GREETING_TEMPLATE
from config import Config
from utils.audio_cache import AudioCache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CallRoutes")

router = APIRouter(prefix="/api/call", tags=["Call Logic"])
twilio_service = TwilioService()

class CallRequest(BaseModel):
    phone_number: str
    call_details: Dict[str, Any] 

@router.post('/initiate')
async def initiate_call(request: CallRequest):
    logger.info(f" [INITIATE] Request for {request.phone_number}")
    try:
        formatted_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            name=request.call_details.get('name', 'Customer'),
            bank_name=request.call_details.get('bank_name', Config.BANK_NAME),
            amount=request.call_details.get('amount', 'unknown amount'),
            loan_type=request.call_details.get('loan_type', 'loan'),
            due_date=request.call_details.get('due_date', 'today'),
            days_overdue=request.call_details.get('days_overdue', 'unknown')
        )
        formatted_greeting = INITIAL_GREETING_TEMPLATE.format(
            name=request.call_details.get('name', 'Customer'),
            bank_name=request.call_details.get('bank_name', Config.BANK_NAME)
        )

        session_id = CallSession.create(
            phone=request.phone_number,
            system_prompt=formatted_system_prompt,
            initial_greeting=formatted_greeting,
            call_details=request.call_details
        )
        
        result = twilio_service.initiate_call(request.phone_number, session_id)
        
        if result['success']:
            CallSession.update_call_sid(session_id, result['call_sid'])
            return {"success": True, "session_id": session_id, "call_sid": result['call_sid']}
        else:
            return {"success": False, "error": result['error']}

    except Exception as e:
        return {"success": False, "error": str(e)}

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