import google.generativeai as genai
from config import Config
import json
from datetime import datetime
from script_templates import ScriptTemplates
import re

class GeminiService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # Use flash model for speed
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # ============================================
        # INTENT PATTERNS - Fallback heuristics
        # ============================================
        self.INTENT_PATTERNS = {
            'WILL_PAY_NOW': [
                r'\b(will|gonna|going to|can|would like to)\s+(pay|make payment|settle|clear)',
                r'\b(pay|paying|payment)\s+(now|immediately|right now|today|right away)',
                r'\b(i\s+will\s+pay)',
                r'\b(let me pay)',
                r'\b(making payment|do payment)',
            ],
            'WILL_PAY_LATER': [
                r'\b(will pay|gonna pay)\s+(tomorrow|next week|later|soon|by)',
                r'\b(pay\s+(in|within|by|after))',
                r'\b(give me.*?(day|week|time))',
                r'\b(need.*?(time|days))',
            ],
            'ALREADY_PAID': [
                r'\b(already paid|paid already|payment done|cleared|settled)',
                r'\b(made.*?payment)',
                r'\b(transferred|transfer.*?done)',
            ],
            'FACING_FINANCIAL_ISSUES': [
                r'\b(lost.*?job|no job|unemployed)',
                r'\b(financial.*?(problem|issue|crisis|difficulty))',
                r'\b(cannot afford|cant afford)',
                r'\b(no money|don\'t have money)',
                r'\b(tough time|difficult situation)',
            ],
            'DISPUTE_AMOUNT': [
                r'\b(wrong amount|incorrect|not correct|dispute)',
                r'\b(this is not right|doesn\'t match)',
                r'\b(why.*?much|too much|high)',
            ],
            'REQUEST_EXTENSION': [
                r'\b(extension|extend|postpone|defer)',
                r'\b(more time|extra time|additional time)',
                r'\b(delay.*?payment)',
            ],
            'REQUEST_PAYMENT_PLAN': [
                r'\b(installment|instalment|emi|part payment)',
                r'\b(split|divide|break.*?payment)',
                r'\b(pay.*?(part|portion|some))',
            ],
            'DEMANDS_SUPERVISOR': [
                r'\b(manager|supervisor|senior|boss|speak.*?someone)',
                r'\b(escalate|transfer.*?call)',
                r'\b(talk.*?(agent|person|human))',
            ],
            'ANGRY_ABUSIVE': [
                r'\b(shut up|stop calling|don\'t call|harassment|harass)',
                r'\b(annoying|irritating|bothering)',
                # Note: Add profanity patterns if needed
            ],
            'POLITE_EXIT': [
                r'\b(thank you|thanks|that\'s all|nothing else)',
                r'\b(okay.*?(thanks|bye)|ok.*?bye)',
                r'\b(i\'m good|all good|all set)',
                r'\b(goodbye|bye|take care)',
            ],
            'CONFUSION_WRONG_PERSON': [
                r'\b(wrong number|wrong person)',
                r'\b(who.*?this|who.*?calling)',
                r'\b(don\'t know.*?loan)',
            ],
        }
    
    # ============================================
    # HEURISTIC INTENT MATCHING (Fallback)
    # ============================================
    def _match_intent_heuristic(self, text):
        """
        Pattern-based intent matching as a fallback.
        Returns (intent, confidence_score)
        """
        text_lower = text.lower().strip()
        
        # Check each intent pattern
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent, 0.8  # High confidence for pattern match
        
        return None, 0.0
    
    # ============================================
    # STEP 1: VERIFICATION SCRIPT (NO AI)
    # ============================================
    def generate_verification_script(self, customer_data, bank_name):
        """Template-based verification (instant)"""
        script = ScriptTemplates.get_verification_script(
            bank_name=bank_name,
            customer_name=customer_data['name'],
            variation=0
        )
        print(f"[TEMPLATE] Verification script: {script}")
        return script
    
    # ============================================
    # STEP 2: VERIFICATION ANALYSIS
    # ============================================
    def analyze_verification(self, customer_response, customer_data):
        """Analyzes verification with fallback logic"""
        print(f"[GEMINI/VERIFICATION] Analyzing: '{customer_response}'")
        
        # Quick heuristic check first
        response_lower = customer_response.lower().strip()
        
        # Positive confirmations
        if any(word in response_lower for word in ['yes', 'yeah', 'yep', 'correct', 'speaking', 'this is', 'i am']):
            intent = 'CONFIRMED_IDENTITY'
        # Negative responses
        elif any(word in response_lower for word in ['no', 'wrong', 'not me', 'incorrect']):
            intent = 'DENIED_IDENTITY'
        # Not interested
        elif any(phrase in response_lower for phrase in ['not interested', 'stop calling', 'don\'t call']):
            intent = 'NOT_INTERESTED'
        else:
            # Use AI for ambiguous cases
            prompt = f"""Classify this response to "Am I speaking with {customer_data['name']}?":
Response: "{customer_response}"

Return JSON only:
{{"intent": "CONFIRMED_IDENTITY|DENIED_IDENTITY|NOT_INTERESTED|CONFUSION|UNCLEAR"}}

Examples:
- "yes", "yeah", "speaking", "this is him/her", "correct" → CONFIRMED_IDENTITY
- "no", "wrong number", "not me" → DENIED_IDENTITY
- "not interested", "stop calling" → NOT_INTERESTED
- "who is this", "what's this about" → CONFUSION
- unclear/gibberish → UNCLEAR"""

            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={'temperature': 0.1, 'max_output_tokens': 50}
                )
                result = json.loads(self._extract_json(response.text))
                intent = result.get('intent', 'UNCLEAR')
            except Exception as e:
                print(f"[ERROR] Verification AI failed: {e}")
                intent = 'UNCLEAR'
        
        polite_response = ScriptTemplates.get_verification_response(
            intent, Config.BANK_NAME, customer_data['name']
        )
        
        print(f"[VERIFICATION] Intent: {intent}")
        return {
            "intent": intent,
            "polite_bot_response": polite_response
        }
    
    # ============================================
    # STEP 3: EMI SCRIPT (TEMPLATE-BASED)
    # ============================================
    def generate_emi_details_script(self, customer_data):
        """Template-based EMI script (instant)"""
        has_history = len(customer_data.get('call_history', [])) > 1
        script = ScriptTemplates.get_emi_script(customer_data, has_history)
        print(f"[TEMPLATE] EMI script: {script[:100]}...")
        return script
    
    # ============================================
    # STEP 4: MAIN CONVERSATION - ENHANCED NLU
    # ============================================
    def get_bot_response(self, call_state, customer_response, customer_data, conversation_history):
        """
        Enhanced intent classification with:
        1. Pre-processing heuristics
        2. AI-based classification with better prompts
        3. Semantic understanding examples
        4. Fallback pattern matching
        """
        print(f"[GEMINI/NLU] State={call_state}, Input='{customer_response}'")
        
        customer_lower = customer_response.lower().strip()
        
        # ============================================
        # PHASE 1: Heuristic Pre-Classification
        # ============================================
        heuristic_intent, confidence = self._match_intent_heuristic(customer_response)
        
        if confidence >= 0.8:
            print(f"[HEURISTIC] Matched intent: {heuristic_intent} (confidence: {confidence})")
            # Use heuristic result directly for high-confidence matches
            return self._build_response(
                heuristic_intent, call_state, customer_data, 
                conversation_history, customer_response
            )
        
        # ============================================
        # PHASE 2: AI-Based Classification (Enhanced)
        # ============================================
        
        # Build context
        history_str = self._build_conversation_context(conversation_history)
        unclear_count = sum(1 for turn in conversation_history if turn.get('intent') == 'UNCLEAR')
        
        # ENHANCED PROMPT with semantic examples
        prompt = f"""You are an NLU engine for EMI recovery. Classify customer intent with semantic understanding.

Customer: {customer_data['name']}
Loan: {customer_data['bank_details']['loan_type']}
Pending: ₹{customer_data['bank_details']['pending_emi_amount']}
Due: {customer_data['bank_details']['due_date']}
State: {call_state}
Unclear count: {unclear_count}

Recent conversation:
{history_str}

Customer's response: "{customer_response}"

**CRITICAL: Understand SEMANTIC MEANING, not just exact words**

Intent Classification with Examples:

1. WILL_PAY_NOW - Customer commits to immediate payment
   Examples: "I'll pay now", "paying it right now", "let me pay immediately", "will do payment today", "making payment now"

2. WILL_PAY_LATER - Customer commits to future payment
   Examples: "will pay tomorrow", "I'll pay next week", "give me 2 days", "pay by Friday"

3. ALREADY_PAID - Customer claims payment already made
   Examples: "I already paid", "payment is done", "I made the transfer yesterday"

4. FACING_FINANCIAL_ISSUES - Customer has money problems
   Examples: "lost my job", "financial problems", "can't afford", "no money right now"

5. DISPUTE_AMOUNT - Customer questions the amount
   Examples: "this is wrong", "amount is incorrect", "why so much", "I don't owe this"

6. REQUEST_EXTENSION - Customer needs more time
   Examples: "can I get extension", "need more time", "postpone payment"

7. REQUEST_PAYMENT_PLAN - Customer wants installments
   Examples: "can I pay in parts", "split the payment", "installment option"

8. DEMANDS_SUPERVISOR - Customer wants escalation
   Examples: "speak to manager", "transfer to agent", "talk to someone senior"

9. POLITE_EXIT - Customer politely ends conversation
   Examples: "thank you that's all", "okay bye", "nothing else", "I'm good thanks"

10. ANGRY_ABUSIVE - Customer is upset/angry
    Examples: "stop calling", "this is harassment", "shut up"

11. CONFUSION_WRONG_PERSON - Wrong number/person
    Examples: "wrong number", "who is this", "I don't have a loan"

12. SMALL_TALK - Off-topic conversation
    Examples: "how are you", "nice weather", unrelated chatter

13. UNCLEAR - Cannot determine intent
    Use this ONLY if truly ambiguous after considering all semantic meanings

Return JSON:
{{
    "intent": "classified_intent",
    "confidence": 0.0-1.0,
    "next_state": "state",
    "should_transfer": false,
    "context": {{}}
}}

**Rules:**
- Match semantic meaning, NOT exact phrases
- "will pay it right now" = "will pay now" = WILL_PAY_NOW
- "going to pay today" = "paying today" = WILL_PAY_NOW  
- Extract dates/amounts to context if customer commits
- If confidence < 0.6, use UNCLEAR
- If unclear_count >= 2, set next_state to OFFERING_OPTIONS
- If DEMANDS_SUPERVISOR appears 2+ times, set should_transfer=true

Return ONLY JSON."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,  # Slightly higher for better semantic understanding
                    'max_output_tokens': 200
                }
            )
            
            result = json.loads(self._extract_json(response.text))
            intent = result.get('intent', 'UNCLEAR')
            ai_confidence = result.get('confidence', 0.5)
            
            print(f"[AI] Intent: {intent}, Confidence: {ai_confidence}")
            
            # ============================================
            # PHASE 3: Confidence-Based Fallback
            # ============================================
            if ai_confidence < 0.6 and heuristic_intent:
                print(f"[FALLBACK] Using heuristic intent: {heuristic_intent}")
                intent = heuristic_intent
            
            return self._build_response(
                intent, call_state, customer_data, 
                conversation_history, customer_response,
                result.get('next_state'), result.get('should_transfer', False),
                result.get('context', {})
            )
            
        except Exception as e:
            print(f"[ERROR] AI classification failed: {e}")
            
            # Final fallback: use heuristic or UNCLEAR
            if heuristic_intent:
                return self._build_response(
                    heuristic_intent, call_state, customer_data,
                    conversation_history, customer_response
                )
            
            return self._build_fallback_response(unclear_count, customer_data)
    
    # ============================================
    # HELPER METHODS
    # ============================================
    def _extract_json(self, text):
        """Extract JSON from response text"""
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return text
    
    def _build_conversation_context(self, history):
        """Build minimal conversation context"""
        context = ""
        for turn in history[-3:]:
            context += f"Agent: {turn.get('bot_response', '')[:50]}...\n"
            context += f"Customer: {turn.get('customer_response', '')}\n"
        return context
    
    def _build_response(self, intent, call_state, customer_data, 
                       conversation_history, customer_response,
                       next_state=None, should_transfer=False, context=None):
        """Build structured response"""
        
        # Determine next state if not provided by AI
        if not next_state:
            unclear_count = sum(1 for t in conversation_history if t.get('intent') == 'UNCLEAR')
            
            if intent == 'POLITE_EXIT':
                next_state = 'HANGUP'
            elif intent in ['WILL_PAY_NOW', 'WILL_PAY_LATER', 'ALREADY_PAID']:
                next_state = 'HANGUP'  # Can close after commitment
            elif intent in ['DEMANDS_SUPERVISOR', 'ANGRY_ABUSIVE']:
                next_state = 'PENDING_TRANSFER'
                should_transfer = True
            elif unclear_count >= 2:
                next_state = 'OFFERING_OPTIONS'
            else:
                next_state = 'CONVERSATION'
        
        # Generate response using templates
        if next_state == 'OFFERING_OPTIONS':
            polite_response = ScriptTemplates.get_offer_options()
        else:
            polite_response = ScriptTemplates.get_conversation_response(
                intent=intent,
                customer_data=customer_data,
                context=context or {},
                variation=0
            )
        
        print(f"[RESPONSE] Intent={intent}, NextState={next_state}, Transfer={should_transfer}")
        
        return {
            "intent": intent,
            "next_state": next_state,
            "polite_bot_response": polite_response,
            "should_transfer": should_transfer,
            "transfer_reason": f"Customer requested: {intent}" if should_transfer else None
        }
    
    def _build_fallback_response(self, unclear_count, customer_data):
        """Build safe fallback response"""
        if unclear_count >= 2:
            return {
                "intent": "UNCLEAR",
                "next_state": "OFFERING_OPTIONS",
                "polite_bot_response": ScriptTemplates.get_offer_options(),
                "should_transfer": False,
                "transfer_reason": None
            }
        else:
            return {
                "intent": "UNCLEAR",
                "next_state": "CONVERSATION",
                "polite_bot_response": "I'm sorry, could you please repeat that?",
                "should_transfer": False,
                "transfer_reason": None
            }