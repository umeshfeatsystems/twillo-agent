from flask import Blueprint, request, jsonify
from twilio.twiml.voice_response import VoiceResponse, Gather
from models.customer import Customer
from services.gemini_service import GeminiService
from services.twilio_service import TwilioService
from language_config import LanguageConfig
from datetime import datetime
import uuid
import os
import requests
from config import Config

call_bp = Blueprint('call', __name__)
gemini_service = GeminiService()
twilio_service = TwilioService()

if not os.path.exists('data'):
    os.makedirs('data')

@call_bp.route('/initiate', methods=['POST'])
def initiate_call():
    """Endpoint to initiate a call to a customer"""
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        
        if not customer_id:
            return jsonify({'error': 'customer_id is required'}), 400
        
        customer = Customer.find_by_id(customer_id)
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        if customer['bank_details']['pending_emi_amount'] <= 0:
            return jsonify({'error': 'No pending EMI for this customer'}), 400
        
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
                'call_state': 'LANGUAGE_SELECTION',  # NEW: Start with language selection
                'language': None,  # NEW: Track selected language
                'transfer_attempted': False,
                'unclear_count': 0
            }
            
            Customer.update_call_history(customer_id, call_record)
            
            return jsonify({
                'success': True,
                'message': f"Call initiated to {customer['name']}",
                'call_sid': call_result['call_sid'],
                'call_ref': call_result['call_ref']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': call_result['error']
            }), 500
    
    except Exception as e:
        print(f"Error in initiate_call: {str(e)}")
        return jsonify({'error': str(e)}), 500


@call_bp.route('/handle-answer', methods=['POST'])
def handle_answer():
    """
    Webhook when customer answers.
    NEW: Present IVR language menu instead of direct greeting.
    """
    try:
        call_sid = request.form.get('CallSid')
        answered_by = request.form.get('AnsweredBy', 'human')
        customer_id = request.args.get('customer_id')
        
        print(f"[DEBUG] handle-answer called: CallSid={call_sid}, customer_id={customer_id}")
        
        if answered_by != 'human':
            print(f"Answering machine detected for {call_sid}")
            collection = Customer.get_collection()
            collection.update_one(
                {'call_history.call_id': call_sid},
                {'$set': {'call_history.$.outcome': 'answering_machine'}}
            )
            twiml = twilio_service.generate_hangup_for_machine_twiml()
            return twiml, 200, {'Content-Type': 'text/xml'}

        # NEW: Generate IVR menu for language selection
        print("[DEBUG] Presenting language selection menu")
        twiml = twilio_service.generate_language_selection_twiml(customer_id)
        
        return twiml, 200, {'Content-Type': 'text/xml'}
    
    except Exception as e:
        print(f"Error in handle_answer: {str(e)}")
        import traceback
        traceback.print_exc()
        response = VoiceResponse()
        response.say("We're experiencing technical difficulties. Please call us back.")
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}


@call_bp.route('/language-selected', methods=['POST'])
def language_selected():
    """
    NEW ENDPOINT: Handle language selection from IVR menu.
    """
    try:
        customer_id = request.args.get('customer_id')
        call_sid = request.form.get('CallSid')
        digits = request.form.get('Digits', '')
        
        print(f"[DEBUG] language-selected: customer_id={customer_id}, digits='{digits}'")
        
        # Map digit to language
        language = LanguageConfig.get_language_from_digit(digits)
        
        if not language:
            # Invalid selection, repeat menu
            print(f"[DEBUG] Invalid language selection: {digits}")
            twiml = twilio_service.generate_language_selection_twiml(
                customer_id, 
                is_repeat=True
            )
            return twiml, 200, {'Content-Type': 'text/xml'}
        
        print(f"[DEBUG] Language selected: {language}")
        
        # Update call record with selected language
        collection = Customer.get_collection()
        collection.update_one(
            {'call_history.call_id': call_sid},
            {
                '$set': {
                    'call_history.$.language': language,
                    'call_history.$.call_state': 'CONNECTING'
                }
            }
        )
        
        # Say transition message and redirect to greeting generation
        transition_text = LanguageConfig.SUPPORTED_LANGUAGES[language]['name']
        if language == 'hi':
            transition_text = "धन्यवाद। कृपया एक क्षण रुकें।"
        else:
            transition_text = "Thank you. Please hold one moment."
        
        redirect_url = f"{Config.BASE_URL}/api/call/generate-greeting?customer_id={customer_id}"
        
        twiml = twilio_service.generate_say_and_redirect_twiml(
            transition_text,
            redirect_url,
            language=language
        )
        
        return twiml, 200, {'Content-Type': 'text/xml'}
    
    except Exception as e:
        print(f"Error in language_selected: {str(e)}")
        import traceback
        traceback.print_exc()
        response = VoiceResponse()
        response.say("Technical error. कृपया दोबारा कॉल करें। Please call again.")
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}


@call_bp.route('/generate-greeting', methods=['POST'])
def generate_greeting():
    """Generate verification script in the customer's selected language"""
    try:
        customer_id = request.args.get('customer_id')
        call_sid = request.form.get('CallSid')
        
        print(f"[DEBUG] generate-greeting: customer_id={customer_id}, call_sid={call_sid}")
        
        customer = Customer.find_by_id(customer_id)
        if not customer:
            print(f"Error: Customer not found")
            response = VoiceResponse()
            response.say("We're having trouble retrieving your details.")
            response.hangup()
            return str(response), 200, {'Content-Type': 'text/xml'}

        # Get selected language from call record
        call_record = None
        for call in customer.get('call_history', []):
            if call.get('call_id') == call_sid:
                call_record = call
                break
        
        language = call_record.get('language', 'en') if call_record else 'en'
        print(f"[DEBUG] Using language: {language}")
        
        # Generate verification script in selected language
        script = gemini_service.generate_verification_script(
            customer, Config.BANK_NAME, language
        )
        print(f"[DEBUG] Generated script: {script[:100]}...")
        
        # Log interaction
        interaction_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'customer_response': 'N/A (Agent initiated call)',
            'bot_response': script,
            'intent': 'VERIFICATION_INITIATED',
            'language': language
        }
        
        collection = Customer.get_collection()
        collection.update_one(
            {'call_history.call_id': call_sid},
            {
                '$push': {'call_history.$.conversation_history': interaction_record},
                '$set': {'call_history.$.call_state': 'AWAITING_VERIFICATION'}
            }
        )
        
        # Generate TwiML with language-specific settings
        twiml = twilio_service.generate_initial_twiml(
            script, customer_id, language
        )
        
        return twiml, 200, {'Content-Type': 'text/xml'}

    except Exception as e:
        print(f"Error in generate_greeting: {str(e)}")
        import traceback
        traceback.print_exc()
        response = VoiceResponse()
        response.say("We're experiencing technical difficulties.")
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}


@call_bp.route('/process-response', methods=['POST'])
def process_response():
    """Process customer speech with language-aware handling"""
    try:
        customer_id = request.args.get('customer_id')
        call_sid = request.form.get('CallSid')
        speech_result = request.form.get('SpeechResult', '')
        
        print(f"[DEBUG] process-response: speech='{speech_result}'")
        
        customer = Customer.find_by_id(customer_id)
        if not customer:
            response = VoiceResponse()
            response.say("We're having trouble retrieving your details.")
            response.hangup()
            return str(response), 200, {'Content-Type': 'text/xml'}

        # Get call record and language
        call_record = None
        for call in customer.get('call_history', []):
            if call.get('call_id') == call_sid:
                call_record = call
                break
        
        if not call_record:
            response = VoiceResponse()
            response.say("We're having trouble finding this call record.")
            response.hangup()
            return str(response), 200, {'Content-Type': 'text/xml'}

        language = call_record.get('language', 'en')
        current_call_state = call_record.get('call_state', 'CONVERSATION')
        conversation_history = call_record.get('conversation_history', [])
        unclear_count = call_record.get('unclear_count', 0)
        
        print(f"[DEBUG] Language: {language}, State: {current_call_state}")
        
        # Handle empty speech
        if not speech_result or speech_result.strip() == '':
            print("[DEBUG] No speech detected")
            unclear_count += 1
            
            collection = Customer.get_collection()
            collection.update_one(
                {'call_history.call_id': call_sid},
                {'$set': {'call_history.$.unclear_count': unclear_count}}
            )
            
            if unclear_count >= 3:
                twiml = twilio_service.generate_transfer_twiml(
                    "I'm having trouble hearing you. Let me connect you with a specialist." 
                    if language == 'en' else 
                    "मुझे आपको सुनने में परेशानी हो रही है। मैं आपको एक स्पेशलिस्ट से कनेक्ट करता हूँ।",
                    language
                )
            else:
                reprompt = ("I'm sorry, I didn't catch that. Could you please repeat?" 
                    if language == 'en' else 
                    "मुझे खेद है, मैं समझ नहीं पाया। क्या आप दोहरा सकते हैं?")
                twiml = twilio_service.generate_followup_twiml(reprompt, customer_id, language)
            return twiml, 200, {'Content-Type': 'text/xml'}
        
        collection = Customer.get_collection()
        
        # VERIFICATION BRANCH
        if current_call_state == 'AWAITING_VERIFICATION':
            print(f"[DEBUG] Analyzing verification in {language}")
            bot_decision = gemini_service.analyze_verification(
                speech_result, customer, language
            )
            
            intent = bot_decision.get('intent')
            followup_text = bot_decision.get('polite_bot_response')
            
            if intent == 'CONFIRMED_IDENTITY':
                next_state = 'PRESENTING_DETAILS'
                transition = ("One moment while I pull up your account details." 
                    if language == 'en' else 
                    "एक क्षण रुकें जब तक मैं आपके अकाउंट की जानकारी निकालता हूँ।")
                redirect_url = f"{Config.BASE_URL}/api/call/present-details?customer_id={customer_id}"
                twiml = twilio_service.generate_say_and_redirect_twiml(
                    followup_text + " " + transition, redirect_url, language
                )
                followup_text = followup_text + " " + transition
            
            elif intent in ['DENIED_IDENTITY', 'NOT_INTERESTED']:
                next_state = 'HANGUP'
                twiml = twilio_service.generate_goodbye_twiml(followup_text, language)
            
            else:
                next_state = 'AWAITING_VERIFICATION'
                twiml = twilio_service.generate_followup_twiml(followup_text, customer_id, language)
            
            # Log interaction
            interaction_record = {
                'timestamp': datetime.utcnow().isoformat(),
                'customer_response': speech_result,
                'bot_response': followup_text,
                'intent': intent,
                'state_transition': f"{current_call_state} -> {next_state}",
                'language': language
            }
            collection.update_one(
                {'call_history.call_id': call_sid},
                {
                    '$push': {'call_history.$.conversation_history': interaction_record},
                    '$set': {
                        'call_history.$.call_state': next_state,
                        'call_history.$.outcome': intent
                    }
                }
            )
            return twiml, 200, {'Content-Type': 'text/xml'}
            
        # MAIN CONVERSATION BRANCH
        elif current_call_state in ['CONVERSATION', 'COLLECTING_COMMITMENT', 'OFFERING_SOLUTIONS', 'OFFERING_OPTIONS']:
            print(f"[DEBUG] Main conversation in {language}")
            bot_decision = gemini_service.get_bot_response(
                current_call_state, speech_result, customer, 
                conversation_history, language
            )
            
            next_state = bot_decision.get('next_state')
            followup_text = bot_decision.get('polite_bot_response')
            intent = bot_decision.get('intent', 'UNCLEAR')
            should_transfer = bot_decision.get('should_transfer', False)
            
            if intent == 'UNCLEAR':
                unclear_count += 1
            else:
                unclear_count = 0
            
            # Log interaction
            interaction_record = {
                'timestamp': datetime.utcnow().isoformat(),
                'customer_response': speech_result,
                'bot_response': followup_text,
                'intent': intent,
                'state_transition': f"{current_call_state} -> {next_state}",
                'should_transfer': should_transfer,
                'language': language
            }
            
            update_data = {
                '$push': {'call_history.$.conversation_history': interaction_record},
                '$set': {
                    'call_history.$.call_state': next_state,
                    'call_history.$.outcome': intent,
                    'call_history.$.unclear_count': unclear_count
                }
            }
            
            if should_transfer:
                update_data['$set']['call_history.$.transfer_attempted'] = True
            
            collection.update_one({'call_history.call_id': call_sid}, update_data)
            
            # Generate TwiML based on next_state
            if next_state in ['CONVERSATION', 'COLLECTING_COMMITMENT', 'OFFERING_SOLUTIONS', 'OFFERING_OPTIONS']:
                twiml = twilio_service.generate_followup_twiml(followup_text, customer_id, language)
            elif next_state == 'PENDING_TRANSFER':
                twiml = twilio_service.generate_transfer_twiml(followup_text, language)
            elif next_state == 'HANGUP':
                twiml = twilio_service.generate_goodbye_twiml(followup_text, language)
            else:
                twiml = twilio_service.generate_goodbye_twiml(
                    "Thank you for your time. Goodbye." if language == 'en' else 
                    "आपके समय के लिए धन्यवाद। अलविदा।",
                    language
                )

            return twiml, 200, {'Content-Type': 'text/xml'}
            
        else:
            print(f"Error: Unhandled state '{current_call_state}'")
            response = VoiceResponse()
            response.say("An unexpected error occurred." if language == 'en' else 
                "एक अप्रत्याशित त्रुटि हुई।")
            response.hangup()
            return str(response), 200, {'Content-Type': 'text/xml'}
    
    except Exception as e:
        print(f"Error in process_response: {str(e)}")
        import traceback
        traceback.print_exc()
        response = VoiceResponse()
        response.say("Thank you for your response. We will follow up shortly.")
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}


@call_bp.route('/present-details', methods=['POST'])
def present_details():
    """Present EMI details in customer's language"""
    try:
        customer_id = request.args.get('customer_id')
        call_sid = request.form.get('CallSid')
        
        print(f"[DEBUG] present-details: customer_id={customer_id}")
        
        customer = Customer.find_by_id(customer_id)
        if not customer:
            response = VoiceResponse()
            response.say("We're having trouble retrieving your details.")
            response.hangup()
            return str(response), 200, {'Content-Type': 'text/xml'}

        # Get language from call record
        call_record = None
        for call in customer.get('call_history', []):
            if call.get('call_id') == call_sid:
                call_record = call
                break
        
        language = call_record.get('language', 'en') if call_record else 'en'
        
        # Generate EMI script in customer's language
        emi_script = gemini_service.generate_emi_details_script(customer, language)
        
        # Log interaction
        next_state = 'CONVERSATION'
        interaction_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'customer_response': 'N/A (Bot presented EMI details)',
            'bot_response': emi_script,
            'intent': 'EMI_DETAILS_PRESENTED',
            'state_transition': f"PRESENTING_DETAILS -> {next_state}",
            'language': language
        }
        
        collection = Customer.get_collection()
        collection.update_one(
            {'call_history.call_id': call_sid},
            {
                '$push': {'call_history.$.conversation_history': interaction_record},
                '$set': {'call_history.$.call_state': next_state}
            }
        )
        
        twiml = twilio_service.generate_followup_twiml(emi_script, customer_id, language)
        
        return twiml, 200, {'Content-Type': 'text/xml'}

    except Exception as e:
        print(f"Error in present_details: {str(e)}")
        import traceback
        traceback.print_exc()
        response = VoiceResponse()
        response.say("We're experiencing a slight delay.")
        response.redirect(
            f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST'
        )
        return str(response), 200, {'Content-Type': 'text/xml'}


# (Keep all other endpoints unchanged: handle-recording, status, handle-transfer-status, 
# get_customer, get_call_history)

@call_bp.route('/handle-recording', methods=['POST'])
def handle_recording():
    """Receive call recording URL"""
    try:
        call_sid = request.form.get('CallSid')
        recording_url = request.form.get('RecordingUrl')
        
        if not recording_url:
            return '', 200
        
        collection = Customer.get_collection()
        customer = collection.find_one({'call_history.call_id': call_sid})
        
        if not customer:
            return '', 200
            
        customer_id = customer['customer_id']
        customer_dir = os.path.join('data', customer_id)
        if not os.path.exists(customer_dir):
            os.makedirs(customer_dir)
            
        audio_filename = f"{call_sid}.wav"
        audio_filepath = os.path.join(customer_dir, audio_filename)
        
        auth = (Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        with requests.get(f"{recording_url}.wav", auth=auth, stream=True) as r:
            r.raise_for_status()
            with open(audio_filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        collection.update_one(
            {'call_history.call_id': call_sid},
            {'$set': {'call_history.$.recording_url': audio_filepath}}
        )
        
        return '', 200
        
    except Exception as e:
        print(f"Error in handle_recording: {str(e)}")
        return '', 200


@call_bp.route('/status', methods=['POST'])
def call_status():
    """Receive call status updates"""
    try:
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        duration = request.form.get('CallDuration', 0)
        
        collection = Customer.get_collection()
        collection.update_one(
            {'call_history.call_id': call_sid},
            {
                '$set': {
                    'call_history.$.status': call_status,
                    'call_history.$.duration': int(duration)
                }
            }
        )
        
        return '', 200
    
    except Exception as e:
        print(f"Error in call_status: {str(e)}")
        return '', 200


@call_bp.route('/handle-transfer-status', methods=['POST'])
def handle_transfer_status():
    """Handle transfer completion"""
    try:
        call_sid = request.form.get('CallSid')
        dial_status = request.form.get('DialCallStatus')
        
        response = VoiceResponse()
        
        if dial_status == 'completed':
            response.say(
                "Thank you for speaking with our specialist. Goodbye.",
                voice='Polly.Aditi', language='en-IN'
            )
            response.hangup()
        elif dial_status in ['no-answer', 'busy', 'failed', 'canceled']:
            response.say(
                "Our specialist is unavailable. We'll call you back. Goodbye.",
                voice='Polly.Aditi', language='en-IN'
            )
            response.hangup()
        else:
            response.hangup()

        return str(response), 200, {'Content-Type': 'text/xml'}
    
    except Exception as e:
        print(f"Error in handle_transfer_status: {str(e)}")
        response = VoiceResponse()
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}


@call_bp.route('/customers/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get customer details"""
    try:
        customer = Customer.find_by_id(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        customer['_id'] = str(customer['_id'])
        return jsonify(customer), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@call_bp.route('/customers/<customer_id>/call-history', methods=['GET'])
def get_call_history(customer_id):
    """Get call history with language info"""
    try:
        customer = Customer.find_by_id(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
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
                'language': call.get('language', 'en'),  # NEW
                'transfer_attempted': call.get('transfer_attempted', False),
                'unclear_count': call.get('unclear_count', 0),
                'conversation_turns': len(call.get('conversation_history', [])),
                'conversation_history': call.get('conversation_history', [])
            }
            formatted_history.append(formatted_call)
        
        return jsonify({
            'customer_id': customer_id,
            'customer_name': customer.get('name'),
            'total_calls': len(call_history),
            'call_history': formatted_history
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500