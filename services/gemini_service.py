import google.generativeai as genai
from config import Config
import json
from datetime import datetime
from script_templates import ScriptTemplates

class GeminiService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # Use ONLY flash model for all operations (fast & efficient)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Response cache to avoid redundant calls
        self._response_cache = {}
    
    # ============================================
    # STEP 1: VERIFICATION SCRIPT (NO AI - INSTANT)
    # ============================================
    def generate_verification_script(self, customer_data, bank_name):
        """
        Generate verification script using TEMPLATES (no AI call).
        Returns instantly with consistent voice quality.
        """
        script = ScriptTemplates.get_verification_script(
            bank_name=bank_name,
            customer_name=customer_data['name'],
            variation=0  # Use first variation for consistency
        )
        print(f"[TEMPLATE] Generated verification script (0ms): {script}")
        return script
    
    # ============================================
    # STEP 2: VERIFICATION ANALYSIS (FAST AI - ~500ms)
    # ============================================
    def analyze_verification(self, customer_response, customer_data):
        """
        Analyzes verification response using AI.
        Optimized with smaller prompt and stricter output format.
        """
        print(f"[GEMINI/FAST] analyze_verification: '{customer_response}'")
        
        # Simple, focused prompt for faster response
        prompt = f"""Classify this response to "Am I speaking with {customer_data['name']}?":
Response: "{customer_response}"

Return JSON only:
{{"intent": "CONFIRMED_IDENTITY|DENIED_IDENTITY|NOT_INTERESTED|CONFUSION|UNCLEAR"}}

Rules:
- CONFIRMED_IDENTITY: yes, speaking, this is him/her, correct
- DENIED_IDENTITY: no, wrong number, not here
- NOT_INTERESTED: not interested, stop calling, don't call
- CONFUSION: who are you, what's this about
- UNCLEAR: unclear/gibberish"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,  # Low temperature for consistency
                    'max_output_tokens': 50  # Minimal output
                }
            )
            response_text = response.text.strip()
            
            # Parse JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            intent = result.get('intent', 'UNCLEAR')
            
            # Use template for response (no AI generation)
            polite_response = ScriptTemplates.get_verification_response(
                intent=intent,
                bank_name=Config.BANK_NAME,
                customer_name=customer_data['name']
            )
            
            print(f"[GEMINI/FAST] Intent: {intent}, Response: {polite_response}")
            
            return {
                "intent": intent,
                "polite_bot_response": polite_response
            }
            
        except Exception as e:
            print(f"[GEMINI ERROR] Verification failed: {str(e)}")
            return {
                "intent": "UNCLEAR",
                "polite_bot_response": ScriptTemplates.get_verification_response(
                    'UNCLEAR', Config.BANK_NAME, customer_data['name']
                )
            }
    
    # ============================================
    # STEP 3: EMI SCRIPT (NO AI - INSTANT)
    # ============================================
    def generate_emi_details_script(self, customer_data):
        """
        Generate EMI script using TEMPLATES (no AI call).
        Returns instantly with consistent voice quality.
        """
        has_history = len(customer_data.get('call_history', [])) > 1
        
        script = ScriptTemplates.get_emi_script(
            customer_data=customer_data,
            has_history=has_history
        )
        
        print(f"[TEMPLATE] Generated EMI script (0ms): {script[:100]}...")
        return script
    
    # ============================================
    # STEP 4: CONVERSATION LOGIC (OPTIMIZED AI - ~800ms)
    # ============================================
    def get_bot_response(self, call_state, customer_response, customer_data, conversation_history):
        """
        Analyzes customer response using AI for intent classification.
        Uses templates for response generation (no AI for script writing).
        """
        print(f"[GEMINI/OPTIMIZED] get_bot_response: state={call_state}, response='{customer_response}'")
        
        # Build minimal conversation context (last 3 turns only)
        history_str = ""
        for turn in conversation_history[-3:]:
            history_str += f"A: {turn.get('bot_response', '')[:50]}...\n"
            history_str += f"C: {turn.get('customer_response', '')}\n"
        
        unclear_count = sum(1 for turn in conversation_history if turn.get('intent') == 'UNCLEAR')
        
        # Optimized prompt for INTENT CLASSIFICATION ONLY (not response generation)
        prompt = f"""You are classifying customer intent in an EMI recovery call.

Customer: {customer_data['name']}
Loan: {customer_data['bank_details']['loan_type']}
Pending: ₹{customer_data['bank_details']['pending_emi_amount']}
Due: {customer_data['bank_details']['due_date']}
State: {call_state}
Unclear count: {unclear_count}

Recent conversation:
{history_str}

Customer's response: "{customer_response}"

Return JSON only:
{{
    "intent": "classification",
    "next_state": "state",
    "should_transfer": false,
    "context": {{}}
}}

Intents:
WILL_PAY_NOW, WILL_PAY_LATER, ALREADY_PAID, FACING_FINANCIAL_ISSUES, DISPUTE_AMOUNT, 
REQUEST_EXTENSION, REQUEST_PAYMENT_PLAN, DEMANDS_SUPERVISOR, ANGRY_ABUSIVE, 
CONFUSION_WRONG_PERSON, UNCLEAR, SMALL_TALK

States:
CONVERSATION, COLLECTING_COMMITMENT, OFFERING_SOLUTIONS, OFFERING_OPTIONS, 
PENDING_TRANSFER, HANGUP

Rules:
- If unclear_count >= 2: set next_state to OFFERING_OPTIONS
- If DEMANDS_SUPERVISOR appears 2+ times in history: set should_transfer=true
- Extract dates/amounts to context if customer commits to payment
- Set next_state to PENDING_TRANSFER only if should_transfer=true

Return ONLY JSON, no explanation."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.2,
                    'max_output_tokens': 150
                }
            )
            response_text = response.text.strip()
            
            # Parse JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            intent = result.get('intent', 'UNCLEAR')
            next_state = result.get('next_state', 'CONVERSATION')
            should_transfer = result.get('should_transfer', False)
            context = result.get('context', {})
            
            # Generate response using TEMPLATES (no AI)
            if next_state == 'OFFERING_OPTIONS':
                polite_response = ScriptTemplates.get_offer_options()
            else:
                polite_response = ScriptTemplates.get_conversation_response(
                    intent=intent,
                    customer_data=customer_data,
                    context=context,
                    variation=0
                )
            
            print(f"[GEMINI/OPTIMIZED] Intent: {intent}, State: {next_state}, Transfer: {should_transfer}")
            
            return {
                "intent": intent,
                "next_state": next_state,
                "polite_bot_response": polite_response,
                "should_transfer": should_transfer,
                "transfer_reason": result.get('transfer_reason', None) if should_transfer else None
            }
            
        except Exception as e:
            print(f"[GEMINI ERROR] Conversation failed: {str(e)}")
            if 'response' in locals():
                print(f"[GEMINI ERROR] Raw: {response.text[:200]}")
            
            # Intelligent fallback based on unclear count
            if unclear_count >= 2:
                return {
                    "intent": "UNCLEAR",
                    "next_state": "OFFERING_OPTIONS",
                    "polite_bot_response": ScriptTemplates.get_offer_options(),
                    "should_transfer": False,
                    "transfer_reason": None
                }
            elif unclear_count >= 3:
                return {
                    "intent": "UNCLEAR",
                    "next_state": "PENDING_TRANSFER",
                    "polite_bot_response": ScriptTemplates.get_conversation_response(
                        'DEMANDS_SUPERVISOR', customer_data
                    ),
                    "should_transfer": True,
                    "transfer_reason": "Multiple unclear exchanges"
                }
            else:
                return {
                    "intent": "UNCLEAR",
                    "next_state": "CONVERSATION",
                    "polite_bot_response": "I'm sorry, could you please repeat that?",
                    "should_transfer": False,
                    "transfer_reason": None
                }