from flask import Blueprint, request, jsonify
from twilio.twiml.voice_response import VoiceResponse, Dial
from models.customer import Customer
from services.gemini_service import GeminiService
from services.twilio_service import TwilioService
from datetime import datetime
import uuid
import os
import requests
from config import Config  # <-- Import Config

call_bp = Blueprint('call', __name__)
gemini_service = GeminiService()
twilio_service = TwilioService()

# Ensure the data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

@call_bp.route('/initiate', methods=['POST'])
def initiate_call():
    """
    Endpoint to initiate a call to a customer
    """
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
                # Change: Start in new 'CONNECTING' state
                'call_state': 'CONNECTING', 
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
    Webhook that Twilio calls when the customer answers.
    --- NEW ARCHITECTURE ---
    This is now a "dumb" webhook. It does NO AI calls.
    It just plays a welcome message and redirects to the first AI endpoint.
    """
    try:
        call_sid = request.form.get('CallSid')
        answered_by = request.form.get('AnsweredBy', 'human')
        customer_id = request.args.get('customer_id')
        
        print(f"[DEBUG] handle-answer called: CallSid={call_sid}, customer_id={customer_id}, answered_by={answered_by}")
        
        if answered_by != 'human':
            print(f"Answering machine detected for {call_sid}. Hanging up.")
            collection = Customer.get_collection()
            collection.update_one(
                {'call_history.call_id': call_sid},
                {'$set': {'call_history.$.outcome': 'answering_machine'}}
            )
            twiml = twilio_service.generate_hangup_for_machine_twiml()
            return twiml, 200, {'Content-Type': 'text/xml'}

        # --- THIS IS NOW A FAST WEBHOOK ---
        # 1. Log that we are connecting
        collection = Customer.get_collection()
        collection.update_one(
            {'call_history.call_id': call_sid},
            {'$set': {'call_history.$.call_state': 'GENERATING_GREETING'}}
        )
        
        # 2. Say a generic welcome and redirect to the first "real" endpoint
        # This message is spoken *while* the next webhook is loading
        transition_text = f"Hello, thank you for connecting. Please hold one moment."
        redirect_url = f"{Config.BASE_URL}/api/call/generate-greeting?customer_id={customer_id}"
        
        twiml = twilio_service.generate_say_and_redirect_twiml(
            transition_text,
            redirect_url
        )
        
        print(f"[DEBUG] handle-answer responding fast, redirecting to /generate-greeting")
        return twiml, 200, {'Content-Type': 'text/xml'}
    
    except Exception as e:
        print(f"Error in handle_answer: {str(e)}")
        import traceback
        traceback.print_exc()
        response = VoiceResponse()
        response.say("We're experiencing technical difficulties. Please call us back.")
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}


# --- NEW ENDPOINT (Step 2) ---
@call_bp.route('/generate-greeting', methods=['POST'])
def generate_greeting():
    """
    Webhook called from /handle-answer.
    Performs the (slow) task of generating the verification script.
    """
    try:
        customer_id = request.args.get('customer_id')
        call_sid = request.form.get('CallSid')
        
        print(f"[DEBUG] generate-greeting called: customer_id={customer_id}, call_sid={call_sid}")
        
        customer = Customer.find_by_id(customer_id)
        if not customer:
            print(f"Error: Could not find customer_id {customer_id} in generate-greeting")
            response = VoiceResponse()
            response.say("We're sorry, we're having trouble retrieving your details.")
            response.hangup()
            return str(response), 200, {'Content-Type': 'text/xml'}

        # --- This is the FIRST slow AI call ---
        script = gemini_service.generate_verification_script(customer, Config.BANK_NAME)
        print(f"[DEBUG] Generated verification script: {script[:100]}...")
        
        # Log this first interaction
        interaction_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'customer_response': 'N/A (Agent initiated call)',
            'bot_response': script,
            'intent': 'VERIFICATION_INITIATED',
        }
        
        # Update DB: push log and set state to AWAITING_VERIFICATION
        collection = Customer.get_collection()
        update_result = collection.update_one(
            {'call_history.call_id': call_sid},
            {
                '$push': {'call_history.$.conversation_history': interaction_record},
                '$set': {'call_history.$.call_state': 'AWAITING_VERIFICATION'}
            }
        )
        
        print(f"[DEBUG] DB update result: matched={update_result.matched_count}, modified={update_result.modified_count}")
        
        # Generate TwiML to speak and gather response
        twiml = twilio_service.generate_initial_twiml(
            script,
            customer['customer_id']
        )
        
        print(f"[DEBUG] Generated TwiML: {twiml[:200]}...")
        return twiml, 200, {'Content-Type': 'text/xml'}

    except Exception as e:
        print(f"Error in generate_greeting: {str(e)}")
        import traceback
        traceback.print_exc()
        response = VoiceResponse()
        response.say("We're experiencing technical difficulties. We will call you back.")
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}


# --- (Step 3) ---
@call_bp.route('/process-response', methods=['POST'])
def process_response():
    """
    Process the customer's speech response.
    Handles verification (fast) and main conversation (slow).
    """
    try:
        customer_id = request.args.get('customer_id')
        call_sid = request.form.get('CallSid')
        speech_result = request.form.get('SpeechResult', '')
        
        print(f"[DEBUG] process-response called: customer_id={customer_id}, call_sid={call_sid}")
        print(f"[DEBUG] Speech result: '{speech_result}'")
        
        customer = Customer.find_by_id(customer_id)
        if not customer:
            print(f"Error: Could not find customer_id {customer_id} in process_response")
            response = VoiceResponse()
            response.say("We're sorry, we're having trouble retrieving your details.")
            response.hangup()
            return str(response), 200, {'Content-Type': 'text/xml'}

        # Find the specific call record
        call_record = None
        for call in customer.get('call_history', []):
            if call.get('call_id') == call_sid:
                call_record = call
                break
        
        if not call_record:
            print(f"Error: Could not find call_record for {call_sid}")
            response = VoiceResponse()
            response.say("We're having trouble finding this call record.")
            response.hangup()
            return str(response), 200, {'Content-Type': 'text/xml'}

        # Get current state and history
        current_call_state = call_record.get('call_state', 'CONVERSATION')
        conversation_history = call_record.get('conversation_history', [])
        unclear_count = call_record.get('unclear_count', 0)
        
        print(f"[DEBUG] Current call state: {current_call_state}")
        print(f"[DEBUG] Conversation history length: {len(conversation_history)}")
        print(f"[DEBUG] Unclear count: {unclear_count}")
        
        # --- Universal Empty Speech Handling ---
        if not speech_result or speech_result.strip() == '':
            print("[DEBUG] No speech detected, generating reprompt")
            unclear_count += 1
            
            # Update unclear count
            collection = Customer.get_collection()
            collection.update_one(
                {'call_history.call_id': call_sid},
                {'$set': {'call_history.$.unclear_count': unclear_count}}
            )
            
            # If too many unclear responses, offer transfer
            if unclear_count >= 3:
                twiml = twilio_service.generate_transfer_twiml(
                    "I'm having trouble hearing you clearly. Let me connect you with a specialist who can assist you better."
                )
            else:
                reprompt_text = "I'm sorry, I didn't catch that. Could you please repeat what you said?"
                if current_call_state == 'AWAITING_VERIFICATION':
                    reprompt_text = f"I'm sorry, I didn't catch that. Is this {customer.get('name')}?"
                twiml = twilio_service.generate_followup_twiml(reprompt_text, customer_id)
            return twiml, 200, {'Content-Type': 'text/xml'}
        
        # --- State-Based Logic Branch ---
        
        collection = Customer.get_collection()
        
        # --- Branch 1: Handle Verification Response ---
        if current_call_state == 'AWAITING_VERIFICATION':
            print(f"[DEBUG] Calling Gemini to analyze verification: '{speech_result}'")
            # --- This is the SECOND (and fast) AI call ---
            bot_decision = gemini_service.analyze_verification(speech_result, customer)
            
            intent = bot_decision.get('intent')
            followup_text = bot_decision.get('polite_bot_response')
            
            twiml = ""
            
            if intent == 'CONFIRMED_IDENTITY':
                # --- This is the fix ---
                # Say a transition message and redirect to the next slow webhook
                next_state = 'PRESENTING_DETAILS'
                transition_text = followup_text + " One moment while I pull up your account details."
                redirect_url = f"{Config.BASE_URL}/api/call/present-details?customer_id={customer_id}"
                
                twiml = twilio_service.generate_say_and_redirect_twiml(
                    transition_text,
                    redirect_url
                )
                
                # Update followup_text for logging
                followup_text = transition_text
            
            elif intent in ['DENIED_IDENTITY', 'NOT_INTERESTED']:
                next_state = 'HANGUP'
                twiml = twilio_service.generate_goodbye_twiml(followup_text)
            
            else: # CONFUSION or UNCLEAR
                next_state = 'AWAITING_VERIFICATION' # Stay in this state
                twiml = twilio_service.generate_followup_twiml(followup_text, customer_id)
            
            # Log this verification interaction
            interaction_record = {
                'timestamp': datetime.utcnow().isoformat(),
                'customer_response': speech_result,
                'bot_response': followup_text,
                'intent': intent,
                'state_transition': f"{current_call_state} -> {next_state}"
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
            
        # --- Branch 2: Handle Main Conversation ---
        elif current_call_state in ['CONVERSATION', 'COLLECTING_COMMITMENT', 'OFFERING_SOLUTIONS', 'OFFERING_OPTIONS']:
            print(f"[DEBUG] Calling Gemini for main conversation: state={current_call_state}, speech='{speech_result}'")
            # --- This is the THIRD (and slow) AI call ---
            bot_decision = gemini_service.get_bot_response(
                current_call_state,
                speech_result, 
                customer, 
                conversation_history
            )
            
            print(f"[DEBUG] Bot decision: {bot_decision}")
            
            next_state = bot_decision.get('next_state')
            followup_text = bot_decision.get('polite_bot_response')
            intent = bot_decision.get('intent', 'UNCLEAR')
            should_transfer = bot_decision.get('should_transfer', False)
            
            # Track unclear responses
            if intent == 'UNCLEAR':
                unclear_count += 1
            else:
                unclear_count = 0  # Reset on clear response
            
            # Log this full interaction
            interaction_record = {
                'timestamp': datetime.utcnow().isoformat(),
                'customer_response': speech_result,
                'bot_response': followup_text,
                'intent': intent,
                'state_transition': f"{current_call_state} -> {next_state}",
                'should_transfer': should_transfer
            }
            
            # Update database
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
            
            collection.update_one(
                {'call_history.call_id': call_sid},
                update_data
            )
            
            print(f"[DEBUG] Updated DB with next_state={next_state}, unclear_count={unclear_count}")
            
            # Generate TwiML based on the next_state
            if next_state in ['CONVERSATION', 'COLLECTING_COMMITMENT', 'OFFERING_SOLUTIONS', 'OFFERING_OPTIONS']:
                print(f"[DEBUG] Generating followup TwiML for state: {next_state}")
                twiml = twilio_service.generate_followup_twiml(followup_text, customer_id)
            
            elif next_state == 'PENDING_TRANSFER':
                print(f"[DEBUG] Generating transfer TwiML - Reason: {bot_decision.get('transfer_reason', 'Not specified')}")
                twiml = twilio_service.generate_transfer_twiml(followup_text)
                
            elif next_state == 'HANGUP':
                print(f"[DEBUG] Generating hangup TwiML - Intent: {intent}")
                twiml = twilio_service.generate_goodbye_twiml(followup_text)
                
            else:
                print(f"[DEBUG] Unknown state '{next_state}', generating default hangup")
                twiml = twilio_service.generate_goodbye_twiml("Thank you for your time. We'll follow up with you shortly. Goodbye.")

            print(f"[DEBUG] Final TwiML: {twiml[:200]}...")
            
            return twiml, 200, {'Content-Type': 'text/xml'}
            
        # --- Branch 3: Handle Unknown State ---
        else:
            print(f"Error: Unhandled call state '{current_call_state}' for call {call_sid}")
            response = VoiceResponse()
            response.say("We're sorry, an unexpected error occurred. We will call you back.")
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


# --- (Step 4) ---
@call_bp.route('/present-details', methods=['POST'])
def present_details():
    """
    Webhook called after verification.
    Performs the (slow) task of generating the EMI script and presents it.
    """
    try:
        customer_id = request.args.get('customer_id')
        call_sid = request.form.get('CallSid')
        
        print(f"[DEBUG] present-details called: customer_id={customer_id}, call_sid={call_sid}")
        
        customer = Customer.find_by_id(customer_id)
        if not customer:
            print(f"Error: Could not find customer_id {customer_id} in present-details")
            response = VoiceResponse()
            response.say("We're sorry, we're having trouble retrieving your details.")
            response.hangup()
            return str(response), 200, {'Content-Type': 'text/xml'}

        # --- This is the THIRD (and slow) AI call, now in its own webhook ---
        emi_script = gemini_service.generate_emi_details_script(customer)
        
        # Log this interaction
        next_state = 'CONVERSATION'
        interaction_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'customer_response': 'N/A (Bot presented EMI details)',
            'bot_response': emi_script,
            'intent': 'EMI_DETAILS_PRESENTED',
            'state_transition': f"PRESENTING_DETAILS -> {next_state}"
        }
        
        collection = Customer.get_collection()
        collection.update_one(
            {'call_history.call_id': call_sid},
            {
                '$push': {'call_history.$.conversation_history': interaction_record},
                '$set': {'call_history.$.call_state': next_state}
            }
        )
        
        # Now, generate the TwiML to start the main conversation loop
        twiml = twilio_service.generate_followup_twiml(emi_script, customer_id)
        
        print(f"[DEBUG] Generated TwiML for EMI details: {twiml[:200]}...")
        return twiml, 200, {'Content-Type': 'text/xml'}

    except Exception as e:
        print(f"Error in present_details: {str(e)}")
        import traceback
        traceback.print_exc()
        response = VoiceResponse()
        response.say("We're experiencing a slight delay. One moment.")
        # Redirect back to the main processor to try again
        response.redirect(
            f'{Config.BASE_URL}/api/call/process-response?customer_id={customer_id}',
            method='POST'
        )
        return str(response), 200, {'Content-Type': 'text/xml'}


@call_bp.route('/handle-recording', methods=['POST'])
def handle_recording():
    """
    Webhook to receive the call recording URL when the call is complete
    """
    try:
        call_sid = request.form.get('CallSid')
        recording_url = request.form.get('RecordingUrl')
        
        if not recording_url:
            print(f"No recording URL for {call_sid}")
            return '', 200
        
        collection = Customer.get_collection()
        customer = collection.find_one({'call_history.call_id': call_sid})
        
        if not customer:
            print(f"Error: Could not find customer for call {call_sid} to save recording")
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
        
        print(f"✓ Saved recording for {customer_id} to {audio_filepath}")
        
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
    """
    Webhook to receive call status updates
    """
    try:
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        duration = request.form.get('CallDuration', 0)
        
        print(f"Call {call_sid} status: {call_status} | Duration: {duration}s")
        
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


# --- NEW ENDPOINT FOR THE FIX ---
@call_bp.route('/handle-transfer-status', methods=['POST'])
def handle_transfer_status():
    """
    Webhook called by Twilio after a <Dial> action completes.
    This determines what to do after the agent call ends.
    """
    try:
        call_sid = request.form.get('CallSid')
        dial_status = request.form.get('DialCallStatus')
        
        print(f"[DEBUG] handle-transfer-status called for {call_sid}: Status={dial_status}")
        
        response = VoiceResponse()
        
        if dial_status == 'completed':
            # The agent (dialed party) hung up. The call is over.
            # Say a professional goodbye.
            response.say(
                "Thank you for speaking with our specialist. Have a wonderful day. Goodbye.",
                voice='Polly.Aditi',
                language='en-IN'
            )
            response.hangup()
        
        elif dial_status in ['no-answer', 'busy', 'failed', 'canceled']:
            # The transfer failed to connect.
            response.say(
                "I'm sorry, our specialist is currently unavailable. We will have someone call you back shortly. Thank you for your patience. Goodbye.",
                voice='Polly.Aditi',
                language='en-IN'
            )
            response.hangup()
        
        else:
            # Default case, just hang up.
            response.hangup()

        return str(response), 200, {'Content-Type': 'text/xml'}
    
    except Exception as e:
        print(f"Error in handle_transfer_status: {str(e)}")
        import traceback
        traceback.print_exc()
        response = VoiceResponse()
        response.hangup()
        return str(response), 200, {'Content-Type': 'text/xml'}


@call_bp.route('/customers/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    """
    Get customer details including call history
    """
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
    """
    Get detailed call history for a customer
    """
    try:
        customer = Customer.find_by_id(customer_id)
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        call_history = customer.get('call_history', [])
        
        # Format the response
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