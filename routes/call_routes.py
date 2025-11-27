from fastapi import APIRouter, Request, Response, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from twilio.twiml.voice_response import VoiceResponse
from models.customer import Customer
from services.gemini_service import GeminiService
from services.twilio_service import TwilioService
from config import Config
from language_config import LanguageConfig
from datetime import datetime
import os
import requests
import traceback
from pydantic import BaseModel, validator
from typing import Optional

# Initialize Router
router = APIRouter(prefix="/api/call", tags=["Call Logic"])

# Services
gemini_service = GeminiService()
twilio_service = TwilioService()

# Ensure directories exist
if not os.path.exists('data'):
    os.makedirs('data')

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
        
        if customer['bank_details']['pending_emi_amount'] <= 0:
            return JSONResponse({'error': 'No pending EMI for this customer'}, status_code=400)
        
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
                'transcription': [], 
                'conversation_history': [], 
                'duration': 0,
                'recording_url': None,
                'call_state': 'CONNECTING',
                'language': target_language, # This stores 'en-hi-hybrid'
                'transfer_attempted': False,
                'unclear_count': 0,
                'context': {}
            }
            
            Customer.update_call_history(customer_id, call_record)
            
            return {
                'success': True,
                'message': f"Call initiated to {customer['name']}",
                'call_sid': call_result['call_sid'],
                'call_ref': call_result['call_ref'],
                'language': target_language
            }
        else:
            return JSONResponse({'success': False, 'error': call_result['error']}, status_code=500)
    
    except ValueError as ve:
        return JSONResponse({'error': str(ve)}, status_code=400)
    except Exception as e:
        print(f"Error in initiate_call: {str(e)}")
        return JSONResponse({'error': str(e)}, status_code=500)

@router.get('/tts-audio/{filename}')
async def serve_tts_audio(filename: str):
    try:
        filepath = os.path.join('tts_cache', filename)
        if not os.path.exists(filepath):
            return Response(status_code=404)
        return FileResponse(filepath, media_type='audio/mpeg')
    except Exception as e:
        return Response(status_code=500)

@router.post('/handle-answer')
async def handle_answer(
    customer_id: str,
    call_ref: str = None, 
    CallSid: str = Form(...),
    AnsweredBy: str = Form('human')
):
    try:
        print(f"[DEBUG] handle-answer called: CallSid={CallSid}, customer_id={customer_id}, call_ref={call_ref}")
        
        if AnsweredBy != 'human':
            print(f"Answering machine detected for {CallSid}")
            collection = Customer.get_collection()
            collection.update_one(
                {'call_history.call_id': CallSid},
                {'$set': {'call_history.$.outcome': 'answering_machine'}}
            )
            twiml = twilio_service.generate_hangup_for_machine_twiml()
            return Response(content=twiml, media_type="application/xml")

        redirect_url = f"{Config.BASE_URL}/api/call/generate-greeting?customer_id={customer_id}"
        response = VoiceResponse()
        response.redirect(redirect_url, method='POST')
        return Response(content=str(response), media_type="application/xml")
    
    except Exception as e:
        print(f"Error in handle_answer: {str(e)}")
        traceback.print_exc()
        response = VoiceResponse()
        response.say("We're experiencing technical difficulties. Please call us back.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

@router.post('/generate-greeting')
async def generate_greeting(
    customer_id: str,
    CallSid: str = Form(...)
):
    try:
        print(f"[DEBUG] generate-greeting: customer_id={customer_id}, call_sid={CallSid}")
        
        customer = Customer.find_by_id(customer_id)
        if not customer:
            print("Error: Customer not found")
            response = VoiceResponse()
            response.say("We're having trouble retrieving your details.")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")

        call_record = None
        for call in customer.get('call_history', []):
            if call.get('call_id') == CallSid:
                call_record = call
                break
        
        language = call_record.get('language', Config.DEFAULT_LANGUAGE) if call_record else Config.DEFAULT_LANGUAGE
        print(f"[DEBUG] Session Language State: {language}")

        # Determine Voice Override for Hybrid Mode
        voice_override = None
        if language == 'en-hi-hybrid':
            voice_override = LanguageConfig.HYBRID_VOICE_NAME

        script = gemini_service.generate_verification_script(
            customer, Config.BANK_NAME, language
        )
        
        interaction_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'customer_response': 'N/A (Agent initiated call)',
            'bot_response': script,
            'intent': 'VERIFICATION_INITIATED',
            'language': language 
        }
        
        collection = Customer.get_collection()
        collection.update_one(
            {'call_history.call_id': CallSid},
            {
                '$push': {'call_history.$.conversation_history': interaction_record},
                '$set': {'call_history.$.call_state': 'AWAITING_VERIFICATION'}
            }
        )
        
        twiml = twilio_service.generate_initial_twiml(
            script, customer_id, language, voice_override=voice_override
        )
        
        return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        print(f"Error in generate_greeting: {str(e)}")
        traceback.print_exc()
        response = VoiceResponse()
        response.say("We're experiencing technical difficulties.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

@router.post('/process-response')
async def process_response(
    customer_id: str,
    CallSid: str = Form(...),
    SpeechResult: str = Form(None)
):
    try:
        speech_result = SpeechResult if SpeechResult else ''
        print(f"[DEBUG] process-response: speech='{speech_result}'")
        
        customer = Customer.find_by_id(customer_id)
        if not customer:
            response = VoiceResponse()
            response.say("We're having trouble retrieving your details.")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")

        call_record = None
        for call in customer.get('call_history', []):
            if call.get('call_id') == CallSid:
                call_record = call
                break
        
        if not call_record:
            response = VoiceResponse()
            response.say("We're having trouble finding this call record.")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")

        session_language = call_record.get('language', Config.DEFAULT_LANGUAGE)
        current_call_state = call_record.get('call_state', 'CONVERSATION')
        conversation_history = call_record.get('conversation_history', [])
        unclear_count = call_record.get('unclear_count', 0)
        stored_context = call_record.get('context', {})
        
        # Determine Voice Override
        voice_override = None
        if session_language == 'en-hi-hybrid':
            voice_override = LanguageConfig.HYBRID_VOICE_NAME

        print(f"[DEBUG] Session Language: {session_language}, State: {current_call_state}")
        
        if not speech_result or speech_result.strip() == '':
            print("[DEBUG] No speech detected")
            unclear_count += 1
            
            collection = Customer.get_collection()
            collection.update_one(
                {'call_history.call_id': CallSid},
                {'$set': {'call_history.$.unclear_count': unclear_count}}
            )
            
            reprompt_lang = 'en' if session_language == 'en-hi-hybrid' else session_language
            
            if unclear_count >= 3:
                twiml = twilio_service.generate_transfer_twiml(
                    "I'm having trouble hearing you. Let me connect you with a specialist." 
                    if reprompt_lang == 'en' else 
                    "मुझे आपको सुनने में प्रॉब्लम हो रही है। मैं आपको एक स्पेशलिस्ट से कनेक्ट करती हूं।",
                    reprompt_lang,
                    voice_override=voice_override
                )
            else:
                reprompt = (
                    "I'm sorry, I didn't catch that. Could you please repeat?" if reprompt_lang == 'en' else 
                    "सॉरी, मुझे समझ नहीं आया। क्या आप दोहरा सकते हैं?"
                )
                twiml = twilio_service.generate_followup_twiml(
                    reprompt, customer_id, session_language, voice_override=voice_override
                )
            
            return Response(content=twiml, media_type="application/xml")
        
        collection = Customer.get_collection()
        
        # --- VERIFICATION STATE ---
        if current_call_state == 'AWAITING_VERIFICATION':
            bot_decision = gemini_service.analyze_verification(
                speech_result, customer, session_language
            )
            
            intent = bot_decision.get('intent')
            followup_text = bot_decision.get('polite_bot_response')
            response_language = bot_decision.get('detected_language', 'en')
            
            print(f"[DEBUG] Verification Intent: {intent}, Responding in: {response_language}")

            if intent == 'CONFIRMED_IDENTITY':
                # --- FAST PATH: Immediate EMI Presentation ---
                next_state = 'CONVERSATION'
                
                # 1. Fetch EMI Script immediately
                # Use detected language (e.g. 'hi') so the script matches what user just spoke
                emi_script = gemini_service.generate_emi_details_script(customer, response_language)
                
                # 2. Combine "Thank you" and "EMI Details" into one speech
                # e.g., "Great, thank you. Regarding your Home Loan..."
                combined_text = f"{followup_text} {emi_script}"
                
                # 3. Generate TwiML immediately (No redirect)
                twiml = twilio_service.generate_followup_twiml(
                    combined_text, customer_id, response_language, voice_override=voice_override
                )
                
                # Log the combined response
                followup_text = combined_text
            
            elif intent in ['DENIED_IDENTITY', 'NOT_INTERESTED']:
                next_state = 'HANGUP'
                twiml = twilio_service.generate_goodbye_twiml(
                    followup_text, response_language, voice_override=voice_override
                )
            
            else:
                next_state = 'AWAITING_VERIFICATION'
                twiml = twilio_service.generate_followup_twiml(
                    followup_text, customer_id, session_language, voice_override=voice_override
                )
            
            interaction_record = {
                'timestamp': datetime.utcnow().isoformat(),
                'customer_response': speech_result,
                'bot_response': followup_text,
                'intent': intent,
                'state_transition': f"{current_call_state} -> {next_state}",
                'language': session_language,
                'detected_language': response_language
            }
            collection.update_one(
                {'call_history.call_id': CallSid},
                {
                    '$push': {'call_history.$.conversation_history': interaction_record},
                    '$set': {
                        'call_history.$.call_state': next_state,
                        'call_history.$.outcome': intent
                    }
                }
            )
            return Response(content=twiml, media_type="application/xml")
            
        # --- MAIN CONVERSATION ---
        elif current_call_state in ['CONVERSATION', 'COLLECTING_COMMITMENT', 'OFFERING_SOLUTIONS', 'OFFERING_OPTIONS']:
            
            bot_decision = gemini_service.get_bot_response(
                current_call_state, speech_result, customer, 
                conversation_history, session_language
            )
            
            next_state = bot_decision.get('next_state')
            followup_text = bot_decision.get('polite_bot_response')
            intent = bot_decision.get('intent', 'UNCLEAR')
            should_transfer = bot_decision.get('should_transfer', False)
            response_context = bot_decision.get('context', {})
            response_language = bot_decision.get('detected_language', 'en')
            
            print(f"[DEBUG] Converastion Intent: {intent}, Responding in: {response_language}")

            stored_context.update(response_context)
            
            if intent == 'UNCLEAR':
                unclear_count += 1
            else:
                unclear_count = 0
            
            interaction_record = {
                'timestamp': datetime.utcnow().isoformat(),
                'customer_response': speech_result,
                'bot_response': followup_text,
                'intent': intent,
                'state_transition': f"{current_call_state} -> {next_state}",
                'should_transfer': should_transfer,
                'language': session_language,
                'detected_language': response_language,
                'context': response_context
            }
            
            update_data = {
                '$push': {'call_history.$.conversation_history': interaction_record},
                '$set': {
                    'call_history.$.call_state': next_state,
                    'call_history.$.outcome': intent,
                    'call_history.$.unclear_count': unclear_count,
                    'call_history.$.context': stored_context
                }
            }
            
            if should_transfer:
                update_data['$set']['call_history.$.transfer_attempted'] = True
            
            collection.update_one({'call_history.call_id': CallSid}, update_data)
            
            if next_state in ['CONVERSATION', 'COLLECTING_COMMITMENT', 'OFFERING_SOLUTIONS', 'OFFERING_OPTIONS']:
                # Pass response_language for STT bias in next turn, but force Voice if Hybrid
                twiml = twilio_service.generate_followup_twiml(
                    followup_text, customer_id, response_language, voice_override=voice_override
                )
                
            elif next_state == 'PENDING_TRANSFER':
                twiml = twilio_service.generate_transfer_twiml(
                    followup_text, response_language, voice_override=voice_override
                )
            elif next_state == 'HANGUP':
                twiml = twilio_service.generate_goodbye_twiml(
                    followup_text, response_language, voice_override=voice_override
                )
            else:
                twiml = twilio_service.generate_goodbye_twiml(
                    "Thank you for your time. Goodbye." if response_language == 'en' else 
                    "आपके टाइम के लिए थैंक्यू। अलविदा।",
                    response_language,
                    voice_override=voice_override
                )

            return Response(content=twiml, media_type="application/xml")
            
        else:
            response = VoiceResponse()
            response.say("An unexpected error occurred.")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")
    
    except Exception as e:
        print(f"Error in process_response: {str(e)}")
        traceback.print_exc()
        response = VoiceResponse()
        response.say("Thank you for your response. We will follow up shortly.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

# Keep the present_details route for direct API access if needed, but it's skipped in standard flow
@router.post('/present-details')
async def present_details(
    customer_id: str,
    detected_lang: str = None, 
    CallSid: str = Form(...)
):
    try:
        print(f"[DEBUG] present-details: customer_id={customer_id}, detected_lang={detected_lang}")
        
        customer = Customer.find_by_id(customer_id)
        if not customer:
            response = VoiceResponse()
            response.say("We're having trouble retrieving your details.")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")

        call_record = None
        for call in customer.get('call_history', []):
            if call.get('call_id') == CallSid:
                call_record = call
                break
        
        session_language = call_record.get('language', Config.DEFAULT_LANGUAGE) if call_record else Config.DEFAULT_LANGUAGE
        lang_to_use = detected_lang if detected_lang else session_language
        
        voice_override = None
        if session_language == 'en-hi-hybrid':
            voice_override = LanguageConfig.HYBRID_VOICE_NAME
        
        emi_script = gemini_service.generate_emi_details_script(customer, lang_to_use)
        
        next_state = 'CONVERSATION'
        interaction_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'customer_response': 'N/A (Bot presented EMI details)',
            'bot_response': emi_script,
            'intent': 'EMI_DETAILS_PRESENTED',
            'state_transition': f"PRESENTING_DETAILS -> {next_state}",
            'language': session_language
        }
        
        collection = Customer.get_collection()
        collection.update_one(
            {'call_history.call_id': CallSid},
            {
                '$push': {'call_history.$.conversation_history': interaction_record},
                '$set': {'call_history.$.call_state': next_state}
            }
        )
        
        twiml = twilio_service.generate_followup_twiml(
            emi_script, customer_id, lang_to_use, voice_override=voice_override
        )
        
        return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        print(f"Error in present_details: {str(e)}")
        traceback.print_exc()
        response = VoiceResponse()
        response.say("We're experiencing a slight delay.")
        response.redirect(
            f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST'
        )
        return Response(content=str(response), media_type="application/xml")

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
            response.say("Thank you for speaking with our specialist. Goodbye.", voice='Polly.Aditi', language='en-IN')
            response.hangup()
        elif DialCallStatus in ['no-answer', 'busy', 'failed', 'canceled']:
            response.say("Our specialist is unavailable. We'll call you back. Goodbye.", voice='Polly.Aditi', language='en-IN')
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

@router.get('/customers/{customer_id}/call-history')
async def get_call_history(customer_id: str):
    try:
        customer = Customer.find_by_id(customer_id)
        if not customer:
            return JSONResponse({'error': 'Customer not found'}, status_code=404)
        
        call_history = customer.get('call_history', [])
        formatted_history = []
        
        for call in call_history:
            formatted_call = {
                'call_id': call.get('call_id'),
                'call_ref': call.get('call_ref'),
                'timestamp': call.get('timestamp'),
                'status': call.get('status'),
                'duration': call.get('duration'),
                'outcome': call.get('outcome'),
                'call_state': call.get('call_state'),
                'language': call.get('language', Config.DEFAULT_LANGUAGE),
                'transfer_attempted': call.get('transfer_attempted', False),
                'unclear_count': call.get('unclear_count', 0),
                'conversation_turns': len(call.get('conversation_history', [])),
                'conversation_history': call.get('conversation_history', []),
                'context': call.get('context', {})
            }
            formatted_history.append(formatted_call)
        
        return {
            'customer_id': customer_id,
            'customer_name': customer.get('name'),
            'total_calls': len(call_history),
            'call_history': formatted_history
        }
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)