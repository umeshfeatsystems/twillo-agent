from fastapi import APIRouter, Request, Response, Form, HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from models.customer import Customer
from services.gemini_service import GeminiService
from services.twilio_service import TwilioService
from utils.audio_cache import AudioCache
from config import Config
from language_config import LanguageConfig
from datetime import datetime
import os
import requests
from pydantic import BaseModel, validator
from typing import Optional
import json
import base64
import asyncio

router = APIRouter(prefix="/api/call", tags=["Call Logic"])

gemini_service = GeminiService()
twilio_service = TwilioService()

if not os.path.exists('data'):
    os.makedirs('data')

# Store active streaming sessions
active_streams = {}

class InitiateCallRequest(BaseModel):
    customer_id: str
    language: Optional[str] = None 

    @validator('language')
    def validate_language(cls, v):
        if v and v.lower() == 'hybrid':
            return 'en-hi-hybrid'
        if v is not None and not LanguageConfig.is_valid_language(v):
            valid_langs = list(LanguageConfig.SUPPORTED_LANGUAGES.keys())
            valid_langs.append('hybrid') 
            raise ValueError(f"Unsupported language '{v}'. Supported: {valid_langs}")
        return v

# --- BACKGROUND TASKS ---
def bg_log_conversation(customer_id: str, call_sid: str, turn_data: dict, next_state: str = None, language: str = None):
    """
    Background task to update DB without blocking the audio response.
    """
    try:
        update_fields = {
            '$push': {'call_history.$.conversation_history': turn_data}
        }
        
        if next_state:
            update_fields['$set'] = {'call_history.$.call_state': next_state}
            
        if language:
            if '$set' not in update_fields:
                update_fields['$set'] = {}
            update_fields['$set']['call_history.$.language'] = language

        Customer.get_collection().update_one(
            {'call_history.call_id': call_sid},
            update_fields
        )
        print(f"✓ [BG TASK] Logged interaction for {call_sid}")
    except Exception as e:
        print(f"✗ [BG TASK] Error logging conversation: {e}")

# --- ROUTES ---

@router.post('/initiate')
async def initiate_call(request: InitiateCallRequest):
    try:
        customer_id = request.customer_id
        target_language = request.language if request.language else Config.DEFAULT_LANGUAGE
        
        customer = Customer.find_by_id(customer_id)
        if not customer:
            return JSONResponse({'error': 'Customer not found'}, status_code=404)
        
        call_result = twilio_service.initiate_call(
            customer['phone'],
            customer['customer_id']
        )
        
        if call_result['success']:
            call_record = {
                'call_id': call_result['call_sid'],
                'call_ref': call_result['call_ref'],
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'initiated',
                'outcome': 'pending',
                'conversation_history': [], 
                'duration': 0,
                'call_state': 'CONNECTING',
                'language': target_language,
                'unclear_count': 0,
                'context': {},
                'partial_transcript': ''
            }
            Customer.update_call_history(customer_id, call_record)
            return {'success': True, 'call_sid': call_result['call_sid']}
        else:
            return JSONResponse({'success': False, 'error': call_result['error']}, status_code=500)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@router.get('/tts-audio/{filename}')
async def serve_tts_audio(filename: str):
    """
    OPTIMIZED: Serves audio directly from RAM (AudioCache).
    Zero disk I/O.
    """
    audio_data = AudioCache.get(filename)
    if audio_data is None:
        print(f"✗ Audio Cache Miss: {filename}")
        return Response(status_code=404)
        
    # Return raw bytes with correct MIME type
    return Response(content=audio_data, media_type='audio/mpeg')

@router.post('/handle-answer')
async def handle_answer(background_tasks: BackgroundTasks, customer_id: str, CallSid: str = Form(...), AnsweredBy: str = Form('human')):
    """Handle call answer"""
    if AnsweredBy != 'human':
        return Response(content=twilio_service.generate_hangup_for_machine_twiml(), media_type="application/xml")
    
    customer = Customer.find_by_id(customer_id)
    # Note: We still do one DB read here to get state, avoiding it is risky for logic.
    call_record = next((c for c in customer.get('call_history', []) if c['call_id'] == CallSid), None)
    language = call_record.get('language', Config.DEFAULT_LANGUAGE) if call_record else Config.DEFAULT_LANGUAGE

    voice_override = LanguageConfig.HYBRID_VOICE_NAME if language == 'en-hi-hybrid' else None
    script = gemini_service.generate_verification_script(customer, Config.BANK_NAME, language)
    
    # OFFLOAD DB WRITE
    turn_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'bot_response': script,
        'intent': 'VERIFICATION_INITIATED'
    }
    background_tasks.add_task(bg_log_conversation, customer_id, CallSid, turn_data, 'AWAITING_VERIFICATION')
    
    twiml = twilio_service.generate_initial_twiml(script, customer_id, language, voice_override=voice_override, stt_language=language)
    return Response(content=twiml, media_type="application/xml")

@router.post('/process-response')
async def process_response(
    background_tasks: BackgroundTasks,
    customer_id: str, 
    CallSid: str = Form(...), 
    SpeechResult: str = Form(None)
):
    """
    OPTIMIZED:
    1. DB Updates moved to background_tasks
    2. Logic flow streamlined
    """
    try:
        speech_result = SpeechResult if SpeechResult else ''
        customer = Customer.find_by_id(customer_id)
        call_record = next((c for c in customer.get('call_history', []) if c['call_id'] == CallSid), None)
        
        session_language = call_record.get('language', Config.DEFAULT_LANGUAGE)
        current_state = call_record.get('call_state', 'CONVERSATION')
        conversation_history = call_record.get('conversation_history', [])
        
        voice_override = LanguageConfig.HYBRID_VOICE_NAME if session_language == 'en-hi-hybrid' else None
        
        # --- LOGIC BRANCHING ---
        if current_state == 'AWAITING_VERIFICATION':
            bot_decision = gemini_service.analyze_verification(speech_result, customer, session_language)
            intent = bot_decision.get('intent')
            followup_text = bot_decision.get('polite_bot_response')
            detected_lang = bot_decision.get('detected_language')
            confidence = bot_decision.get('confidence', 0.0)

            # Language Switch Logic
            new_lang_state = None
            if (detected_lang and 
                detected_lang != session_language and 
                detected_lang != 'en-hi-hybrid' and
                confidence > 0.7):
                print(f"🔀 High confidence language switch: {session_language} → {detected_lang}")
                session_language = detected_lang
                new_lang_state = detected_lang

            # Verification Logic
            if intent == 'CONFIRMED_IDENTITY':
                next_state = 'CONVERSATION'
                emi_script = gemini_service.generate_emi_details_script(customer, session_language)
                combined_text = f"{followup_text}... ... {emi_script}"
                
                twiml = twilio_service.generate_followup_twiml(
                    combined_text, customer_id, session_language, 
                    voice_override=voice_override, stt_language=session_language
                )
                followup_text = combined_text 

            elif intent == 'DENIED_IDENTITY':
                next_state = 'HANGUP'
                twiml = twilio_service.generate_goodbye_twiml(followup_text, session_language, voice_override=voice_override)
            else:
                next_state = 'AWAITING_VERIFICATION'
                twiml = twilio_service.generate_followup_twiml(followup_text, customer_id, session_language, voice_override=voice_override, stt_language=session_language)
                
            # OFFLOAD DB WRITE
            turn_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'customer_response': speech_result,
                'bot_response': followup_text,
                'intent': intent
            }
            background_tasks.add_task(bg_log_conversation, customer_id, CallSid, turn_data, next_state, new_lang_state)
            
            return Response(content=twiml, media_type="application/xml")

        else:
            # Main Conversation Loop
            bot_decision = gemini_service.get_bot_response(
                current_state, speech_result, customer, 
                conversation_history, session_language
            )
            
            intent = bot_decision.get('intent')
            followup_text = bot_decision.get('polite_bot_response')
            next_state = bot_decision.get('next_state')
            new_lang = bot_decision.get('switch_language_to')
            
            new_lang_state = None
            if intent == 'SWITCH_LANGUAGE' and new_lang:
                print(f"🔀 Explicitly switching language to: {new_lang}")
                session_language = new_lang
                new_lang_state = new_lang
                next_state = 'CONVERSATION'

            # Generate TwiML immediately
            if next_state == 'HANGUP':
                twiml = twilio_service.generate_goodbye_twiml(followup_text, session_language, voice_override=voice_override)
            elif next_state == 'PENDING_TRANSFER':
                twiml = twilio_service.generate_transfer_twiml(followup_text, session_language, voice_override=voice_override)
            else:
                twiml = twilio_service.generate_followup_twiml(
                    followup_text, customer_id, session_language, 
                    voice_override=voice_override, stt_language=session_language
                )

            # OFFLOAD DB WRITE
            turn_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'customer_response': speech_result,
                'bot_response': followup_text,
                'intent': intent,
                'generative': True 
            }
            background_tasks.add_task(bg_log_conversation, customer_id, CallSid, turn_data, next_state, new_lang_state)

            return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        print(f"Error: {e}")
        return Response(content=str(VoiceResponse().hangup()), media_type="application/xml")

# WebSocket Endpoint for streaming (Placeholder for Phase 2, kept compatible)
@router.websocket('/media-stream')
async def media_stream_endpoint(websocket: WebSocket, customer_id: str = Query(...), call_sid: str = Query(...)):
    await websocket.accept()
    # ... (Rest of existing WebSocket logic if needed, or leave as is) ...
    # Since we are focusing on Approach A, I'm leaving the existing WebSocket stub 
    # but cleaning it up slightly to avoid errors if triggered.
    try:
        async for message in websocket.iter_text():
            pass # No-op for now
    except:
        pass

@router.post('/handle-recording')
async def handle_recording(CallSid: str = Form(...), RecordingUrl: str = Form(None)):
    try:
        if not RecordingUrl:
            return Response(status_code=200)
        
        # This one operation is non-blocking to the call flow (happens after call), 
        # so standard request is fine, but cleaner to offload.
        collection = Customer.get_collection()
        collection.update_one(
            {'call_history.call_id': CallSid},
            {'$set': {'call_history.$.recording_url': RecordingUrl}} # Store URL, don't download file
        )
        # Note: We stopped downloading the recording to disk to save space/IO.
        # Twilio stores it for 30 days anyway.
        return Response(status_code=200)
    except Exception as e:
        print(f"Error in handle_recording: {str(e)}")
        return Response(status_code=200)

@router.post('/status')
async def call_status(CallSid: str = Form(...), CallStatus: str = Form(...), CallDuration: int = Form(0)):
    try:
        collection = Customer.get_collection()
        collection.update_one(
            {'call_history.call_id': CallSid},
            {
                '$set': {
                    'call_history.$.status': CallStatus,
                    'call_history.$.duration': int(CallDuration)
                }
            }
        )
        return Response(status_code=200)
    except Exception as e:
        print(f"Error in call_status: {str(e)}")
        return Response(status_code=200)

@router.post('/handle-transfer-status')
async def handle_transfer_status(CallSid: str = Form(...), DialCallStatus: str = Form(...)):
    try:
        response = VoiceResponse()
        if DialCallStatus == 'completed':
            response.say("Thank you for speaking with our specialist. Goodbye.")
            response.hangup()
        elif DialCallStatus in ['no-answer', 'busy', 'failed', 'canceled']:
            response.say("Our specialist is unavailable. We'll call you back. Goodbye.")
            response.hangup()
        else:
            response.hangup()
        return Response(content=str(response), media_type="application/xml")
    except Exception as e:
        print(f"Error in handle_transfer_status: {str(e)}")
        response = VoiceResponse()
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

@router.get('/customers/{customer_id}')
async def get_customer(customer_id: str):
    try:
        customer = Customer.find_by_id(customer_id)
        if not customer:
            return JSONResponse({'error': 'Customer not found'}, status_code=404)
        customer['_id'] = str(customer['_id'])
        return customer
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)