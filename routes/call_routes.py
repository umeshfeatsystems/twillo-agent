from fastapi import APIRouter, Request, Response, Form, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from models.customer import Customer
from services.gemini_service import GeminiService
from services.twilio_service import TwilioService
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
    filepath = os.path.join('tts_cache', filename)
    if not os.path.exists(filepath): 
        return Response(status_code=404)
    return FileResponse(filepath, media_type='audio/mpeg')

@router.post('/handle-answer')
async def handle_answer(customer_id: str, CallSid: str = Form(...), AnsweredBy: str = Form('human')):
    """Handle call answer - Use standard gather/say instead of streaming for now"""
    if AnsweredBy != 'human':
        return Response(content=twilio_service.generate_hangup_for_machine_twiml(), media_type="application/xml")
    
    # For now, fall back to the standard flow (not streaming)
    # This ensures calls work while we debug streaming
    customer = Customer.find_by_id(customer_id)
    call_record = next((c for c in customer.get('call_history', []) if c['call_id'] == CallSid), None)
    language = call_record.get('language', Config.DEFAULT_LANGUAGE) if call_record else Config.DEFAULT_LANGUAGE

    voice_override = LanguageConfig.HYBRID_VOICE_NAME if language == 'en-hi-hybrid' else None
    script = gemini_service.generate_verification_script(customer, Config.BANK_NAME, language)
    
    Customer.get_collection().update_one(
        {'call_history.call_id': CallSid},
        {
            '$push': {'call_history.$.conversation_history': {
                'timestamp': datetime.utcnow().isoformat(),
                'bot_response': script,
                'intent': 'VERIFICATION_INITIATED'
            }},
            '$set': {'call_history.$.call_state': 'AWAITING_VERIFICATION'}
        }
    )
    
    twiml = twilio_service.generate_initial_twiml(script, customer_id, language, voice_override=voice_override, stt_language=language)
    return Response(content=twiml, media_type="application/xml")

# WEBSOCKET ENDPOINT - Properly configured for Twilio Media Streams
@router.websocket('/media-stream')
async def media_stream_endpoint(
    websocket: WebSocket,
    customer_id: str = Query(...),
    call_sid: str = Query(...)
):
    """
    Handle Twilio Media Streams WebSocket connection
    Twilio will connect to: wss://yourdomain/api/call/media-stream?customer_id=X&call_sid=Y
    """
    
    print(f"\n{'='*60}")
    print(f"[WEBSOCKET] Incoming connection request")
    print(f"[WEBSOCKET] Customer ID: {customer_id}")
    print(f"[WEBSOCKET] Call SID: {call_sid}")
    print(f"{'='*60}\n")
    
    # Accept the WebSocket connection
    try:
        await websocket.accept()
        print(f"✓ [WEBSOCKET] Connection accepted for {call_sid}")
    except Exception as e:
        print(f"✗ [WEBSOCKET] Failed to accept connection: {e}")
        return
    
    # Get customer data
    customer = Customer.find_by_id(customer_id)
    if not customer:
        print(f"✗ [WEBSOCKET] Customer not found: {customer_id}")
        await websocket.close(code=1008, reason="Customer not found")
        return
    
    call_record = next((c for c in customer.get('call_history', []) if c['call_id'] == call_sid), None)
    session_language = call_record.get('language', Config.DEFAULT_LANGUAGE) if call_record else Config.DEFAULT_LANGUAGE
    
    print(f"✓ [WEBSOCKET] Session initialized - Language: {session_language}")
    
    # Store session
    active_streams[call_sid] = {
        'websocket': websocket,
        'customer_id': customer_id,
        'language': session_language,
        'state': 'AWAITING_VERIFICATION',
        'buffer': b'',
        'transcript_buffer': '',
        'stream_sid': None,
        'call_sid': call_sid
    }
    
    try:
        # Wait for Twilio to send 'start' event
        print(f"[WEBSOCKET] Waiting for Twilio 'start' event...")
        
        async for message in websocket.iter_text():
            try:
                data = json.loads(message)
                event = data.get('event')
                
                if event == 'start':
                    stream_sid = data.get('start', {}).get('streamSid')
                    active_streams[call_sid]['stream_sid'] = stream_sid
                    print(f"✓ [WEBSOCKET] Stream started - StreamSid: {stream_sid}")
                    
                    # Send initial greeting
                    greeting = gemini_service.generate_verification_script(
                        customer, 
                        Config.BANK_NAME, 
                        session_language
                    )
                    print(f"[BOT] Sending greeting: {greeting[:50]}...")
                    # For now, just log - TTS streaming needs more setup
                    
                elif event == 'media':
                    # Receive audio from caller
                    payload = data.get('media', {}).get('payload', '')
                    if payload and active_streams.get(call_sid):
                        audio_chunk = base64.b64decode(payload)
                        active_streams[call_sid]['buffer'] += audio_chunk
                        
                        # Process every 1 second of audio (8000 bytes at 8kHz mulaw)
                        if len(active_streams[call_sid]['buffer']) >= 8000:
                            print(f"[AUDIO] Received {len(active_streams[call_sid]['buffer'])} bytes")
                            # TODO: Process with STT
                            active_streams[call_sid]['buffer'] = b''
                
                elif event == 'stop':
                    print(f"[WEBSOCKET] Stream stopped by Twilio")
                    break
                
                elif event == 'connected':
                    print(f"✓ [WEBSOCKET] Twilio connected event received")
                
                else:
                    print(f"[WEBSOCKET] Unknown event: {event}")
                    
            except json.JSONDecodeError as e:
                print(f"✗ [WEBSOCKET] JSON decode error: {e}")
                continue
            except Exception as e:
                print(f"✗ [WEBSOCKET] Error processing message: {e}")
                continue
    
    except WebSocketDisconnect:
        print(f"[WEBSOCKET] Client disconnected: {call_sid}")
    except Exception as e:
        print(f"✗ [WEBSOCKET] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if call_sid in active_streams:
            del active_streams[call_sid]
        print(f"[WEBSOCKET] Session cleaned up for {call_sid}")
        try:
            await websocket.close()
        except:
            pass

@router.post('/generate-greeting')
async def generate_greeting(customer_id: str, CallSid: str = Form(...)):
    try:
        customer = Customer.find_by_id(customer_id)
        call_record = next((c for c in customer.get('call_history', []) if c['call_id'] == CallSid), None)
        language = call_record.get('language', Config.DEFAULT_LANGUAGE) if call_record else Config.DEFAULT_LANGUAGE

        voice_override = LanguageConfig.HYBRID_VOICE_NAME if language == 'en-hi-hybrid' else None
        script = gemini_service.generate_verification_script(customer, Config.BANK_NAME, language)
        
        Customer.get_collection().update_one(
            {'call_history.call_id': CallSid},
            {
                '$push': {'call_history.$.conversation_history': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'bot_response': script,
                    'intent': 'VERIFICATION_INITIATED'
                }},
                '$set': {'call_history.$.call_state': 'AWAITING_VERIFICATION'}
            }
        )
        
        twiml = twilio_service.generate_initial_twiml(script, customer_id, language, voice_override=voice_override, stt_language=language)
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        print(f"Error generating greeting: {e}")
        return Response(content=str(VoiceResponse().hangup()), media_type="application/xml")

@router.post('/process-response')
async def process_response(customer_id: str, CallSid: str = Form(...), SpeechResult: str = Form(None)):
    try:
        speech_result = SpeechResult if SpeechResult else ''
        customer = Customer.find_by_id(customer_id)
        call_record = next((c for c in customer.get('call_history', []) if c['call_id'] == CallSid), None)
        
        session_language = call_record.get('language', Config.DEFAULT_LANGUAGE)
        current_state = call_record.get('call_state', 'CONVERSATION')
        conversation_history = call_record.get('conversation_history', [])
        
        voice_override = LanguageConfig.HYBRID_VOICE_NAME 
        
        if current_state == 'AWAITING_VERIFICATION':
            bot_decision = gemini_service.analyze_verification(speech_result, customer, session_language)
            intent = bot_decision.get('intent')
            followup_text = bot_decision.get('polite_bot_response')
            detected_lang = bot_decision.get('detected_language')
            confidence = bot_decision.get('confidence', 0.0)

            # ONLY switch if confidence is high (>0.7) and languages are truly different
            if (detected_lang and 
                detected_lang != session_language and 
                detected_lang != 'en-hi-hybrid' and
                confidence > 0.7):
                print(f"🔀 High confidence language switch: {session_language} → {detected_lang} (confidence: {confidence:.2f})")
                session_language = detected_lang
                Customer.get_collection().update_one(
                    {'call_history.call_id': CallSid},
                    {'$set': {'call_history.$.language': session_language}}
                )
            else:
                print(f"🔒 Language maintained: {session_language} (detected: {detected_lang}, confidence: {confidence:.2f})")

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
                
            Customer.get_collection().update_one(
                {'call_history.call_id': CallSid},
                {
                    '$push': {'call_history.$.conversation_history': {
                        'timestamp': datetime.utcnow().isoformat(),
                        'customer_response': speech_result,
                        'bot_response': followup_text,
                        'intent': intent
                    }},
                    '$set': {'call_history.$.call_state': next_state}
                }
            )
            return Response(content=twiml, media_type="application/xml")

        else:
            bot_decision = gemini_service.get_bot_response(
                current_state, speech_result, customer, 
                conversation_history, session_language
            )
            
            intent = bot_decision.get('intent')
            followup_text = bot_decision.get('polite_bot_response')
            next_state = bot_decision.get('next_state')
            new_lang = bot_decision.get('switch_language_to')

            if intent == 'SWITCH_LANGUAGE' and new_lang:
                print(f"🔀 Explicitly switching language to: {new_lang}")
                Customer.get_collection().update_one(
                    {'call_history.call_id': CallSid},
                    {'$set': {'call_history.$.language': new_lang}}
                )
                session_language = new_lang
                next_state = 'CONVERSATION'

            Customer.get_collection().update_one(
                {'call_history.call_id': CallSid},
                {
                    '$push': {'call_history.$.conversation_history': {
                        'timestamp': datetime.utcnow().isoformat(),
                        'customer_response': speech_result,
                        'bot_response': followup_text,
                        'intent': intent,
                        'generative': True 
                    }},
                    '$set': {'call_history.$.call_state': next_state}
                }
            )

            if next_state == 'HANGUP':
                twiml = twilio_service.generate_goodbye_twiml(followup_text, session_language, voice_override=voice_override)
            elif next_state == 'PENDING_TRANSFER':
                twiml = twilio_service.generate_transfer_twiml(followup_text, session_language, voice_override=voice_override)
            else:
                twiml = twilio_service.generate_followup_twiml(
                    followup_text, customer_id, session_language, 
                    voice_override=voice_override, stt_language=session_language
                )
            
            return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        print(f"Error: {e}")
        return Response(content=str(VoiceResponse().hangup()), media_type="application/xml")

@router.post('/handle-recording')
async def handle_recording(CallSid: str = Form(...), RecordingUrl: str = Form(None)):
    try:
        if not RecordingUrl:
            return Response(status_code=200)
        
        collection = Customer.get_collection()
        customer = collection.find_one({'call_history.call_id': CallSid})
        
        if not customer:
            return Response(status_code=200)
            
        customer_id = customer['customer_id']
        customer_dir = os.path.join('data', customer_id)
        if not os.path.exists(customer_dir):
            os.makedirs(customer_dir)
            
        audio_filename = f"{CallSid}.wav"
        audio_filepath = os.path.join(customer_dir, audio_filename)
        
        auth = (Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        with requests.get(f"{RecordingUrl}.wav", auth=auth, stream=True) as r:
            r.raise_for_status()
            with open(audio_filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        collection.update_one(
            {'call_history.call_id': CallSid},
            {'$set': {'call_history.$.recording_url': audio_filepath}}
        )
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