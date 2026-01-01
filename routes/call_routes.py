from fastapi import APIRouter, BackgroundTasks, Form, Request, Response, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from services.twilio_service import TwilioService
from services.gemini_service import gemini_service
from models.session import CallSession
from prompts import SYSTEM_PROMPT_TEMPLATE, INITIAL_GREETING_TEMPLATE
from datetime import datetime
from utils.audio_cache import AudioCache
from config import Config
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CallRoutes")

router = APIRouter(prefix="/api/call", tags=["Generic Call Logic"])
twilio_service = TwilioService()

# --- INPUT MODEL ---
class CallRequest(BaseModel):
    phone_number: str
    call_details: Dict[str, Any] 

@router.post('/initiate')
async def initiate_call(request: CallRequest):
    logger.info(f"[INITIATE] Request for {request.phone_number}")
    try:
        # 1. Prepare Prompt
        formatted_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            name=request.call_details.get('name', 'Customer'),
            amount=request.call_details.get('amount', 'unknown amount'),
            bank_name=request.call_details.get('bank_name', Config.BANK_NAME),
            loan_type=request.call_details.get('loan_type', 'loan'),
            due_date=request.call_details.get('due_date', 'today')
        )

        formatted_greeting = INITIAL_GREETING_TEMPLATE.format(
            name=request.call_details.get('name', 'Customer')
        )

        # 2. Create Session
        session_id = CallSession.create(
            phone=request.phone_number,
            system_prompt=formatted_system_prompt,
            initial_greeting=formatted_greeting,
            call_details=request.call_details
        )
        logger.info(f"[SESSION] Created Session: {session_id}")
        
        # 3. Trigger Call
        result = twilio_service.initiate_call(request.phone_number, session_id)
        
        if result['success']:
            CallSession.update_call_sid(session_id, result['call_sid'])
            logger.info(f"[TWILIO] Call Initiated. SID: {result['call_sid']}")
            return {"success": True, "session_id": session_id, "call_sid": result['call_sid']}
        else:
            logger.error(f"[TWILIO] Failed: {result['error']}")
            return {"success": False, "error": result['error']}

    except Exception as e:
        logger.error(f"[INITIATE] Error: {e}")
        return {"success": False, "error": str(e)}

@router.post('/handle-answer')
async def handle_answer(background_tasks: BackgroundTasks, session_id: str):
    logger.info(f"[HANDLE-ANSWER] Call Answered for Session: {session_id}")
    
    session = CallSession.find_by_session_id(session_id)
    if not session: 
        logger.error("Session Not Found")
        return Response(status_code=404)

    greeting_text = session['initial_greeting']
    logger.info(f"[BOT] Greeting: {greeting_text}")
    
    # Prepare Audio
    audio_filename = twilio_service.prepare_audio_placeholder()
    
    # Schedule Generation
    background_tasks.add_task(twilio_service.generate_audio_background, greeting_text, audio_filename)
    
    # Log History
    CallSession.append_history(session_id, {"role": "assistant", "content": greeting_text})

    return Response(content=twilio_service.generate_async_twiml(audio_filename, session_id), media_type="application/xml")

@router.post('/process-response')
async def process_response(background_tasks: BackgroundTasks, session_id: str, SpeechResult: str = Form('')):
    logger.info(f"[USER SPEECH] Session {session_id} | Said: '{SpeechResult}'")
    
    session = CallSession.find_by_session_id(session_id)
    if not session: return Response(status_code=404)

    # 1. AI Processing
    ai_decision = gemini_service.get_generic_response(
        system_prompt=session['system_prompt'], 
        conversation_history=session.get('conversation_history', []),
        user_input=SpeechResult
    )
    
    bot_text = ai_decision['response_text']
    logger.info(f"[AI DECISION] Response: '{bot_text}' | Hangup: {ai_decision['should_hangup']}")

    # 2. Audio Generation
    audio_filename = twilio_service.prepare_audio_placeholder()
    background_tasks.add_task(twilio_service.generate_audio_background, bot_text, audio_filename)
    
    # 3. Update History
    CallSession.append_history(session_id, {"role": "user", "content": SpeechResult})
    CallSession.append_history(session_id, {"role": "assistant", "content": bot_text})

    # 4. Return TwiML
    if ai_decision['should_hangup']:
        return Response(content=twilio_service.generate_goodbye_twiml(bot_text), media_type="application/xml")
    
    return Response(content=twilio_service.generate_async_twiml(audio_filename, session_id), media_type="application/xml")

# --- MISSING STATUS ENDPOINT FIXED HERE ---
@router.post('/status')
async def call_status(CallSid: str = Form(...), CallStatus: str = Form(...)):
    """
    Twilio hits this endpoint to report status changes (ringing, answered, completed).
    """
    logger.info(f"[STATUS] SID: {CallSid} | Status: {CallStatus}")
    
    # Ideally, update your Session DB status here
    # CallSession.update_status(CallSid, CallStatus)
    
    return Response(status_code=200)

@router.get('/tts-audio/{filename}')
async def serve_tts_audio(filename: str):
    """
    Blocking endpoint that waits for audio to be generated.
    """
    logger.info(f"[AUDIO REQUEST] Fetching: {filename}")
    
    # INCREASED TIMEOUT to 10s to prevent 404s
    audio_data = AudioCache.get_with_wait(filename, timeout=10)
    
    if audio_data is None:
        logger.error(f"[AUDIO MISS] Timeout/Redacted: {filename}")
        return Response(status_code=404)
        
    logger.info(f"[AUDIO SERVED] Sending bytes for: {filename}")
    return Response(content=audio_data, media_type='audio/mpeg')