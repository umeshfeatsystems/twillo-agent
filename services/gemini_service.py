import google.generativeai as genai
from config import Config
from multilingual_script_templates import MultilingualScriptTemplates
from language_config import LanguageConfig
import json
import re

class GeminiService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Intent patterns for English
        self.INTENT_PATTERNS_EN = {
            'WILL_PAY_NOW': [
                r'\b(will|gonna|going to|can|would like to)\s+(pay|make payment|settle|clear)',
                r'\b(pay|paying|payment)\s+(now|immediately|right now|today|right away)',
            ],
            'WILL_PAY_LATER': [
                r'\b(will pay|gonna pay)\s+(tomorrow|next week|later|soon|by)',
            ],
            'ALREADY_PAID': [
                r'\b(already paid|paid already|payment done|cleared|settled)',
            ],
            'FACING_FINANCIAL_ISSUES': [
                r'\b(lost.*?job|no job|unemployed)',
                r'\b(financial.*?(problem|issue|crisis))',
            ],
        }
        
        # Intent patterns for Hindi (Romanized and Devanagari)
        self.INTENT_PATTERNS_HI = {
            'WILL_PAY_NOW': [
                r'\b(अभी|आज|तुरंत|अब).*?(भुगतान|पे|देंगे|करेंगे)',
                r'\b(payment|pay).*?(abhi|aaj|turant|kar|dunga)',
            ],
            'WILL_PAY_LATER': [
                r'\b(कल|बाद में|जल्द).*?(भुगतान|पे|देंगे)',
                r'\b(kal|baad|later).*?(pay|payment)',
            ],
            'ALREADY_PAID': [
                r'\b(पहले ही|already).*?(भुगतान|paid|कर दिया)',
                r'\b(payment.*?(ho gaya|done|kar diya))',
            ],
        }
    
    def _match_intent_heuristic(self, text, language='en'):
        """Pattern-based intent matching as fallback"""
        text_lower = text.lower().strip()
        patterns = self.INTENT_PATTERNS_EN if language == 'en' else self.INTENT_PATTERNS_HI
        
        for intent, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, text_lower):
                    return intent, 0.8
        
        return None, 0.0
    
    def generate_verification_script(self, customer_data, bank_name, language='en'):
        """Generate verification script in specified language"""
        script = MultilingualScriptTemplates.get_verification_script(
            language=language,
            bank_name=bank_name,
            customer_name=customer_data['name'],
            variation=0
        )
        print(f"[TEMPLATE/{language.upper()}] Verification script: {script}")
        return script
    
    def analyze_verification(self, customer_response, customer_data, language='en'):
        """
        Analyze verification response with multi-lingual support.
        
        Args:
            customer_response: Customer's speech
            customer_data: Customer details
            language: 'en' or 'hi'
        """
        print(f"[GEMINI/VERIFICATION/{language.upper()}] Analyzing: '{customer_response}'")
        
        response_lower = customer_response.lower().strip()
        
        # Language-specific positive/negative indicators
        if language == 'en':
            positive_words = ['yes', 'yeah', 'yep', 'correct', 'speaking', 'this is', 'i am']
            negative_words = ['no', 'wrong', 'not me', 'incorrect']
            not_interested = ['not interested', 'stop calling', "don't call"]
        else:  # Hindi
            positive_words = ['हाँ', 'हां', 'जी', 'बोल रहा', 'बोल रही', 'yes', 'ha', 'ji']
            negative_words = ['नहीं', 'गलत', 'नही', 'no', 'nahi', 'galat']
            not_interested = ['रुचि नहीं', 'call mat', 'बंद करो', 'not interested']
        
        # Quick heuristic check
        if any(word in response_lower for word in positive_words):
            intent = 'CONFIRMED_IDENTITY'
        elif any(word in response_lower for word in negative_words):
            intent = 'DENIED_IDENTITY'
        elif any(phrase in response_lower for phrase in not_interested):
            intent = 'NOT_INTERESTED'
        else:
            # Use AI for ambiguous cases
            prompt_template = {
                'en': f"""Classify this response to "Am I speaking with {customer_data['name']}?":
Response: "{customer_response}"

Return JSON only:
{{"intent": "CONFIRMED_IDENTITY|DENIED_IDENTITY|NOT_INTERESTED|CONFUSION|UNCLEAR"}}

Examples:
- "yes", "yeah", "speaking" → CONFIRMED_IDENTITY
- "no", "wrong number" → DENIED_IDENTITY
- "not interested" → NOT_INTERESTED
- "who is this" → CONFUSION
- unclear → UNCLEAR""",
                
                'hi': f"""इस जवाब को वर्गीकृत करें "क्या मैं {customer_data['name']} जी से बात कर रहा हूँ?":
जवाब: "{customer_response}"

केवल JSON लौटाएं:
{{"intent": "CONFIRMED_IDENTITY|DENIED_IDENTITY|NOT_INTERESTED|CONFUSION|UNCLEAR"}}

उदाहरण:
- "हाँ", "जी", "बोल रहा हूँ" → CONFIRMED_IDENTITY
- "नहीं", "गलत नंबर" → DENIED_IDENTITY
- "रुचि नहीं", "कॉल मत करो" → NOT_INTERESTED
- "कौन बोल रहा है" → CONFUSION
- अस्पष्ट → UNCLEAR"""
            }
            
            try:
                response = self.model.generate_content(
                    prompt_template[language],
                    generation_config={'temperature': 0.1, 'max_output_tokens': 50}
                )
                result = json.loads(self._extract_json(response.text))
                intent = result.get('intent', 'UNCLEAR')
            except Exception as e:
                print(f"[ERROR] Verification AI failed: {e}")
                intent = 'UNCLEAR'
        
        polite_response = MultilingualScriptTemplates.get_verification_response(
            language, intent, Config.BANK_NAME, customer_data['name']
        )
        
        print(f"[VERIFICATION/{language.upper()}] Intent: {intent}")
        return {
            "intent": intent,
            "polite_bot_response": polite_response
        }
    
    def generate_emi_details_script(self, customer_data, language='en'):
        """Generate EMI script in specified language"""
        has_history = len(customer_data.get('call_history', [])) > 1
        script = MultilingualScriptTemplates.get_emi_script(
            language, customer_data, has_history
        )
        print(f"[TEMPLATE/{language.upper()}] EMI script: {script[:100]}...")
        return script
    
    def get_bot_response(self, call_state, customer_response, customer_data, 
                        conversation_history, language='en'):
        """
        Enhanced NLU with multi-lingual support.
        
        Args:
            call_state: Current call state
            customer_response: Customer's speech
            customer_data: Customer details
            conversation_history: Conversation history
            language: 'en' or 'hi'
        """
        print(f"[GEMINI/NLU/{language.upper()}] State={call_state}, Input='{customer_response}'")
        
        # Try heuristic matching first
        heuristic_intent, confidence = self._match_intent_heuristic(customer_response, language)
        
        if confidence >= 0.8:
            print(f"[HEURISTIC/{language.upper()}] Matched: {heuristic_intent}")
            return self._build_response(
                heuristic_intent, call_state, customer_data,
                conversation_history, customer_response, language
            )
        
        # Build context
        history_str = self._build_conversation_context(conversation_history, language)
        unclear_count = sum(1 for t in conversation_history if t.get('intent') == 'UNCLEAR')
        
        # Language-specific prompts
        if language == 'en':
            prompt = f"""You are an NLU engine for EMI recovery. Classify customer intent.

Customer: {customer_data['name']}
Loan: {customer_data['bank_details']['loan_type']}
Pending: ₹{customer_data['bank_details']['pending_emi_amount']}
Due: {customer_data['bank_details']['due_date']}
State: {call_state}
Unclear count: {unclear_count}

Recent conversation:
{history_str}

Customer's response: "{customer_response}"

Intents: WILL_PAY_NOW, WILL_PAY_LATER, ALREADY_PAID, FACING_FINANCIAL_ISSUES, 
DISPUTE_AMOUNT, REQUEST_EXTENSION, REQUEST_PAYMENT_PLAN, DEMANDS_SUPERVISOR, 
POLITE_EXIT, ANGRY_ABUSIVE, CONFUSION_WRONG_PERSON, SMALL_TALK, UNCLEAR

Return JSON:
{{
    "intent": "classified_intent",
    "confidence": 0.0-1.0,
    "next_state": "state",
    "should_transfer": false
}}"""
        
        else:  # Hindi
            prompt = f"""आप ईएमआई रिकवरी के लिए एक NLU इंजन हैं। ग्राहक के इरादे को वर्गीकृत करें।

ग्राहक: {customer_data['name']}
ऋण: {customer_data['bank_details']['loan_type']}
बकाया: ₹{customer_data['bank_details']['pending_emi_amount']}
नियत तिथि: {customer_data['bank_details']['due_date']}
अवस्था: {call_state}
अस्पष्ट गिनती: {unclear_count}

हाल की बातचीत:
{history_str}

ग्राहक की प्रतिक्रिया: "{customer_response}"

इरादे: WILL_PAY_NOW (अभी भुगतान करेंगे), WILL_PAY_LATER (बाद में भुगतान करेंगे), 
ALREADY_PAID (पहले ही भुगतान किया), FACING_FINANCIAL_ISSUES (वित्तीय समस्याएं), 
DISPUTE_AMOUNT (राशि विवाद), REQUEST_EXTENSION (समय बढ़ाने की मांग), 
REQUEST_PAYMENT_PLAN (भुगतान योजना), DEMANDS_SUPERVISOR (सुपरवाइजर से बात), 
POLITE_EXIT (विनम्र बाहर निकलना), ANGRY_ABUSIVE (गुस्सा/अपमानजनक), 
CONFUSION_WRONG_PERSON (गलत व्यक्ति), SMALL_TALK (छोटी बातचीत), UNCLEAR (अस्पष्ट)

JSON लौटाएं:
{{
    "intent": "classified_intent",
    "confidence": 0.0-1.0,
    "next_state": "state",
    "should_transfer": false
}}"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={'temperature': 0.3, 'max_output_tokens': 200}
            )
            
            result = json.loads(self._extract_json(response.text))
            intent = result.get('intent', 'UNCLEAR')
            ai_confidence = result.get('confidence', 0.5)
            
            print(f"[AI/{language.upper()}] Intent: {intent}, Confidence: {ai_confidence}")
            
            # Confidence-based fallback
            if ai_confidence < 0.6 and heuristic_intent:
                print(f"[FALLBACK/{language.upper()}] Using heuristic: {heuristic_intent}")
                intent = heuristic_intent
            
            return self._build_response(
                intent, call_state, customer_data, conversation_history,
                customer_response, language, result.get('next_state'),
                result.get('should_transfer', False), result.get('context', {})
            )
            
        except Exception as e:
            print(f"[ERROR/{language.upper()}] AI failed: {e}")
            
            if heuristic_intent:
                return self._build_response(
                    heuristic_intent, call_state, customer_data,
                    conversation_history, customer_response, language
                )
            
            return self._build_fallback_response(unclear_count, customer_data, language)
    
    def _extract_json(self, text):
        """Extract JSON from response"""
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return text
    
    def _build_conversation_context(self, history, language='en'):
        """Build conversation context"""
        context = ""
        for turn in history[-3:]:
            if language == 'en':
                context += f"Agent: {turn.get('bot_response', '')[:50]}...\n"
                context += f"Customer: {turn.get('customer_response', '')}\n"
            else:
                context += f"एजेंट: {turn.get('bot_response', '')[:50]}...\n"
                context += f"ग्राहक: {turn.get('customer_response', '')}\n"
        return context
    
    def _build_response(self, intent, call_state, customer_data, 
                       conversation_history, customer_response, language='en',
                       next_state=None, should_transfer=False, context=None):
        """Build structured response in specified language"""
        
        if not next_state:
            unclear_count = sum(1 for t in conversation_history if t.get('intent') == 'UNCLEAR')
            
            if intent == 'POLITE_EXIT':
                next_state = 'HANGUP'
            elif intent in ['WILL_PAY_NOW', 'WILL_PAY_LATER', 'ALREADY_PAID']:
                next_state = 'HANGUP'
            elif intent in ['DEMANDS_SUPERVISOR', 'ANGRY_ABUSIVE']:
                next_state = 'PENDING_TRANSFER'
                should_transfer = True
            elif unclear_count >= 2:
                next_state = 'OFFERING_OPTIONS'
            else:
                next_state = 'CONVERSATION'
        
        # Generate response using multi-lingual templates
        if next_state == 'OFFERING_OPTIONS':
            polite_response = MultilingualScriptTemplates.get_script(
                'offer_options', language
            )
        else:
            polite_response = MultilingualScriptTemplates.get_conversation_response(
                language=language,
                intent=intent,
                customer_data=customer_data,
                context=context or {},
                variation=0
            )
        
        print(f"[RESPONSE/{language.upper()}] Intent={intent}, NextState={next_state}")
        
        return {
            "intent": intent,
            "next_state": next_state,
            "polite_bot_response": polite_response,
            "should_transfer": should_transfer,
            "transfer_reason": f"Customer requested: {intent}" if should_transfer else None
        }
    
    def _build_fallback_response(self, unclear_count, customer_data, language='en'):
        """Build safe fallback response"""
        if unclear_count >= 2:
            return {
                "intent": "UNCLEAR",
                "next_state": "OFFERING_OPTIONS",
                "polite_bot_response": MultilingualScriptTemplates.get_script(
                    'offer_options', language
                ),
                "should_transfer": False,
                "transfer_reason": None
            }
        else:
            fallback_text = (
                "I'm sorry, could you please repeat that?" if language == 'en' else
                "मुझे खेद है, क्या आप दोहरा सकते हैं?"
            )
            return {
                "intent": "UNCLEAR",
                "next_state": "CONVERSATION",
                "polite_bot_response": fallback_text,
                "should_transfer": False,
                "transfer_reason": None
            }