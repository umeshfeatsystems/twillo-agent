import google.generativeai as genai
from config import Config
import json
import re
from datetime import datetime

class GeminiService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # --- NEW HYBRID MODEL SETUP ---
        # Use a FAST model for simple, time-sensitive tasks (like verification)
        self.fast_model = genai.GenerativeModel('gemini-2.5-flash')
        
        # --- THE FIX ---
        # We MUST use the flash model for conversation too.
        # The 'pro' model is too slow (21s) and fails Twilio's 15s timeout.
        self.accurate_model = genai.GenerativeModel('gemini-2.5-flash')
        # --- END THE FIX ---

    # --- NEW: Step 1 of Greeting ---
    def generate_verification_script(self, customer_data, bank_name):
        """
        Generate Step 1: Verification script.
        Asks to confirm the customer's identity.
        """
        prompt = f"""
        You are a professional, calm, and clear bank representative.
        Generate a 1-sentence script to greet a customer and verify their identity.
        
        Bank Name: "{bank_name}"
        Customer Name: "{customer_data['name']}"
        
        Requirements:
        - Sound polite and professional, not robotic.
        - Must include the Bank Name.
        - Must ask to speak to the Customer Name.
        
        Example 1: "Hi, I'm calling from {bank_name}. May I please speak with {customer_data['name']}?"
        Example 2: "Hello, this is a call from {bank_name}. Am I speaking with {customer_data['name']}?"
        
        Return ONLY the script text, no formatting, no asterisks, no extra text.
        """
        try:
            # --- Uses FAST model ---
            response = self.fast_model.generate_content(prompt)
            script = response.text.strip().replace("*", "").replace("#", "")
            print(f"[GEMINI/FAST] Generated verification script: {script[:100]}...")
            return script
        except Exception as e:
            print(f"[GEMINI ERROR/FAST] Failed to generate verification script: {str(e)}")
            # Fallback script
            return f"Hello, this is a call from {bank_name}. Am I speaking with {customer_data['name']}?"

    # --- NEW: Analyze Step 1 Response ---
    def analyze_verification(self, customer_response, customer_data):
        """
        Analyzes the customer's response to the verification (Step 1).
        """
        print(f"[GEMINI/FAST] analyze_verification called: response='{customer_response}'")
        
        prompt = f"""
        You are an intent classifier for a bank call. The agent just asked, "Am I speaking with {customer_data['name']}?"
        Analyze the customer's response: "{customer_response}"
        
        Return your analysis in this EXACT JSON format:
        {{
            "intent": "classification",
            "polite_bot_response": "response text"
        }}
        
        Intent options:
        - CONFIRMED_IDENTITY: Customer said "Yes", "Speaking", "This is him/her", etc.
        - DENIED_IDENTITY: Customer said "No", "Wrong number", "He/she is not here", etc.
        - NOT_INTERESTED: Customer said "Not interested", "Stop calling", "Remove me", etc.
        - CONFUSION: Customer said "What is this about?", "Who are you?", "What bank?", etc.
        - UNCLEAR: Cannot understand the response.
        
        Guidelines:
        - For CONFIRMED_IDENTITY: Respond with a brief confirmation (e.g., "Great, thank you."). The app will append the EMI details.
        - For DENIED_IDENTITY: Respond politely and end the call (e.g., "I apologize for the disturbance. We will update our records. Goodbye.")
        - For NOT_INTERESTED: Respond politely and end the call (e.g., "I understand. I will note that you do not wish to be contacted. Have a good day.")
        - For CONFUSION: Re-state who you are and what you need (e.g., "This is a call from {Config.BANK_NAME} for {customer_data['name']}. Is he/she available?")
        - For UNCLEAR: Ask them to repeat (e.g., "I'm sorry, I didn't quite catch that. Is this {customer_data['name']} speaking?")
        
        Examples:
        
        Customer: "Yes, this is him."
        {{
            "intent": "CONFIRMED_IDENTITY",
            "polite_bot_response": "Great, thank you."
        }}
        
        Customer: "No, wrong number."
        {{
            "intent": "DENIED_IDENTITY",
            "polite_bot_response": "I apologize for the disturbance. We will update our records. Goodbye."
        }}
        
        Customer: "I'm not interested, stop calling me!"
        {{
            "intent": "NOT_INTERESTED",
            "polite_bot_response": "I understand. I will note that you do not wish to be contacted. Have a good day."
        }}
        
        Customer: "What is this about?"
        {{
            "intent": "CONFUSION",
            "polite_bot_response": "This is a call from {Config.BANK_NAME} for {customer_data['name']}. Is he or she available?"
        }}
        
        Return ONLY the JSON object, nothing else.
        """
        try:
            # --- Uses FAST model ---
            response = self.fast_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            print(f"[GEMINI/FAST] Verification analysis: {result}")
            return result
            
        except Exception as e:
            print(f"[GEMINI ERROR/FAST] Verification parsing failed: {str(e)}")
            # Fallback
            return {
                "intent": "UNCLEAR",
                "polite_bot_response": f"I'm sorry, I didn't quite catch that. Is this {customer_data['name']} speaking?"
            }

    # --- NEW: Step 2 of Greeting ---
    def generate_emi_details_script(self, customer_data):
        """
        Generate Step 2: EMI details script.
        Plays only after identity is confirmed.
        """
        last_call_context = ""
        if customer_data.get('call_history') and len(customer_data['call_history']) > 1: # Check for *previous* calls
            last_call_history = customer_data['call_history'][-2] # Get the one before the current call
            outcome = last_call_history.get('outcome', 'pending')
            if outcome not in ['pending', 'initiated', 'GREETING', 'VERIFICATION_INITIATED', 'CONFIRMED_IDENTITY', 'DENIED_IDENTITY']:
                last_call_context = f"\nNote: Our records show the last call outcome was '{outcome}'. Acknowledge this briefly."

        prompt = f"""
        You are a professional, empathetic recovery agent. The customer has just confirmed their identity.
        Generate a brief, conversational script (2-3 sentences) to state the reason for the call.
        
        Customer Name: {customer_data['name']}
        Pending EMI Amount: 鈧箋{customer_data['bank_details']['pending_emi_amount']}
        Due Date: {customer_data['bank_details']['due_date']}
        Loan Type: {customer_data['bank_details']['loan_type']}
        {last_call_context}
        
        Requirements:
        - Be polite and respectful.
        - State the loan type, pending amount, and due date.
        - Ask an open-ended question to understand their situation.
        - Sound helpful, not aggressive.
        
        Example 1: "I'm reaching out regarding your {customer_data['bank_details']['loan_type']}. Our records show a pending installment of 鈧箋{customer_data['bank_details']['pending_emi_amount']} which was due on {customer_data['bank_details']['due_date']}. I'd like to help resolve this - could you tell me how you'd like to proceed with this payment?"
        Example 2 (with context): "So, {customer_data['name']}, I'm calling about your {customer_data['bank_details']['loan_type']}. I see we last spoke and you were facing some issues. Our records still show the pending amount of 鈧箋{customer_data['bank_details']['pending_emi_amount']} from {customer_data['bank_details']['due_date']}. I was hoping we could find a solution today. What's the current situation?"
        
        Return ONLY the script text, no formatting, no asterisks, no extra text.
        """
        try:
            # --- Uses ACCURATE (but fast) model ---
            response = self.accurate_model.generate_content(prompt)
            script = response.text.strip().replace("*", "").replace("#", "")
            print(f"[GEMINI/ACCURATE_FAST] Generated EMI details script: {script[:100]}...")
            return script
        except Exception as e:
            print(f"[GEMINI ERROR/ACCURATE_FAST] Failed to generate EMI script: {str(e)}")
            # Fallback script
            return f"I'm reaching out regarding your {customer_data['bank_details']['loan_type']}. Our records show a pending installment of 鈧箋{customer_data['bank_details']['pending_emi_amount']} which was due on {customer_data['bank_details']['due_date']}. I'd like to help resolve this - could you tell me how you'd like to proceed with this payment?"

    # --- UPDATED: Main Conversation Logic ---
    def get_bot_response(self, call_state, customer_response, customer_data, conversation_history):
        """
        Analyzes customer response and generates appropriate recovery agent response.
        Acts like a skilled recovery agent - handles objections, offers solutions, and only transfers when absolutely necessary.
        """
        
        print(f"[GEMINI/ACCURATE_FAST] get_bot_response called: state={call_state}, response='{customer_response}'")
        
        # Build conversation history for context
        history_str = ""
        for turn in conversation_history[-5:]:  # Only last 5 turns
            history_str += f"Agent: {turn.get('bot_response', '')}\n"
            history_str += f"Customer: {turn.get('customer_response', '')}\n"
        
        # Count how many times we've been unclear or customer has been difficult
        unclear_count = sum(1 for turn in conversation_history if turn.get('intent') == 'UNCLEAR')
        
        prompt = f"""
        You are a skilled recovery agent for a bank handling an EMI payment reminder call.
        Your goal is to RESOLVE the situation yourself - only transfer to supervisor in extreme cases.
        
        Customer Name: {customer_data['name']}
        Pending Amount: 鈧箋{customer_data['bank_details']['pending_emi_amount']}
        Due Date: {customer_data['bank_details']['due_date']}
        Loan Type: {customer_data['bank_details']['loan_type']}
        Current Call State: {call_state}
        Unclear responses count: {unclear_count}

        Recent conversation:
        {history_str}
        
        Customer's latest response: "{customer_response}"
        
        As a recovery agent, you should:
        1. Handle objections professionally (financial hardship, disputes, confusion)
        2. Offer payment solutions (partial payment, extension, payment plan)
        3. Build rapport and show empathy
        4. Try to get a payment commitment
        5. **NEW RULE**: If you are confused (UNCLEAR intent) twice, you MUST offer clear options.
        
        Analyze and respond in this EXACT JSON format:
        {{
            "intent": "classification",
            "next_state": "state",
            "polite_bot_response": "response text",
            "should_transfer": false,
            "transfer_reason": null
        }}
        
        Intent options: 
        - WILL_PAY_NOW, WILL_PAY_LATER, ALREADY_PAID
        - FACING_FINANCIAL_ISSUES, DISPUTE_AMOUNT, REQUEST_EXTENSION
        - REQUEST_PAYMENT_PLAN, ANGRY_ABUSIVE, DEMANDS_SUPERVISOR
        - CONFUSION_WRONG_PERSON, UNCLEAR, SMALL_TALK
        
        Next_state options:
        - CONVERSATION: Continue conversation (default - keep trying to resolve)
        - COLLECTING_COMMITMENT: Getting specific payment date/amount
        - OFFERING_SOLUTIONS: Presenting payment options
        - **NEW**: OFFERING_OPTIONS: Use this state if you are confused and need to give the user simple choices.
        - PENDING_TRANSFER: Only if must transfer (set should_transfer: true)
        - HANGUP: End call (payment committed or resolved)
        
        Guidelines:
        - Be empathetic but firm
        - If financial hardship: offer payment plan or partial payment
        - If confusion: clarify details patiently
        - If demands supervisor repeatedly (2+ times): transfer
        - **NEW GUIDELINE (Confusion Handling)**:
            - If intent is UNCLEAR and unclear_count < 2: Try to rephrase and ask again (next_state: CONVERSATION).
            - If intent is UNCLEAR and unclear_count >= 2: You MUST set next_state to 'OFFERING_OPTIONS' and give clear, simple choices.
        - If current_call_state is 'OFFERING_OPTIONS': Listen carefully for keywords like 'payment', 'help', or 'agent' and act accordingly.
        
        Examples:
        
        Customer: "I will pay tomorrow"
        {{
            "intent": "WILL_PAY_LATER",
            "next_state": "HANGUP",
            "polite_bot_response": "Thank you for confirming, {customer_data['name']}. I've noted that you'll make the payment tomorrow. We'll send a payment link to your registered number. Have a great day!",
            "should_transfer": false,
            "transfer_reason": null
        }}
        
        Customer: "I lost my job last month, I don't have money right now"
        {{
            "intent": "FACING_FINANCIAL_ISSUES",
            "next_state": "OFFERING_SOLUTIONS",
            "polite_bot_response": "I'm really sorry to hear about your job situation, {customer_data['name']}. I understand this is a difficult time. We have a few options that might help - like a temporary payment holiday or breaking this into smaller installments. Would either of these work for you?",
            "should_transfer": false,
            "transfer_reason": null
        }}
        
        Customer: "I SAID CONNECT ME TO YOUR MANAGER! Are you deaf?" (second demand, angry)
        {{
            "intent": "DEMANDS_SUPERVISOR",
            "next_state": "PENDING_TRANSFER",
            "polite_bot_response": "I completely understand, {customer_data['name']}. I'll transfer you to a supervisor right away. Please hold for just a moment.",
            "should_transfer": true,
            "transfer_reason": "Customer repeatedly demanded supervisor"
        }}

        **NEW EXAMPLE (Handling Confusion)**
        Customer: "I don't know, maybe, what about the weather?" (unclear_count is 2)
        {{
            "intent": "UNCLEAR",
            "next_state": "OFFERING_OPTIONS",
            "polite_bot_response": "I'm sorry, I'm not sure I understand. To make this easier, you can simply say 'make a payment', 'request help', or 'speak to an agent'. What would you like to do?",
            "should_transfer": false,
            "transfer_reason": null
        }}
        
        **NEW EXAMPLE (Handling Response to Options)**
        (Current state is 'OFFERING_OPTIONS')
        Customer: "I just need to speak to an agent, please."
        {{
            "intent": "DEMANDS_SUPERVISOR",
            "next_state": "PENDING_TRANSFER",
            "polite_bot_response": "Of course. I'll connect you with a specialist right now. Please hold.",
            "should_transfer": true,
            "transfer_reason": "Customer selected 'speak to an agent' option"
        }}
        
        Return ONLY the JSON object, nothing else.
        """
        
        try:
            # --- Uses ACCURATE (but fast) model ---
            response = self.accurate_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up the response - remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            print(f"[GEMINI/ACCURATE_FAST] Conversation analysis: {result}")
            
            # Validate response structure
            if 'next_state' not in result or 'polite_bot_response' not in result:
                raise ValueError("Invalid response structure")
            
            # Override: only transfer if should_transfer is explicitly true
            if result.get('should_transfer', False) and result.get('next_state') != 'PENDING_TRANSFER':
                result['next_state'] = 'PENDING_TRANSFER'
            
            return result
            
        except Exception as e:
            print(f"[GEMINI ERROR/ACCURATE_FAST] Conversation parsing failed: {str(e)}")
            if 'response' in locals():
                print(f"[GEMINI ERROR/ACCURATE_FAST] Raw response: {response.text}")
            
            # Fallback: try to help one more time before giving up
            if unclear_count >= 3:
                return {
                    "intent": "UNCLEAR",
                    "next_state": "PENDING_TRANSFER",
                    "polite_bot_response": "I apologize, I'm having difficulty understanding your situation clearly. Let me connect you with a specialist who can better assist you. Please hold for a moment.",
                    "should_transfer": True,
                    "transfer_reason": "Multiple unclear exchanges"
                }
            else:
                # --- NEW FALLBACK: Offer options instead of a vague reprompt ---
                return {
                    "intent": "UNCLEAR",
                    "next_state": "OFFERING_OPTIONS",
                    "polite_bot_response": "I'm sorry, I'm having a little trouble understanding. To make this simple, you can say 'make a payment', 'request help', or 'speak to an agent'. How can I help?",
                    "should_transfer": False,
                    "transfer_reason": None
                }   