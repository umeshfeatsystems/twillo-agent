import google.generativeai as genai
from config import Config
from multilingual_script_templates import MultilingualScriptTemplates
from language_config import LanguageConfig
import json
import re
from datetime import datetime, timedelta

class GeminiService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        self.INTENT_PATTERNS_EN = {
            'WILL_PAY_NOW': [
                r'\b(will|gonna|going to|can|would like to)\s+(pay|make payment|settle|clear)',
                r'\b(pay|paying|payment)\s+(now|immediately|right now|today|right away)',
                r'\b(yes|yeah|yep|sure|ok|okay)\b.*\b(pay|payment)',
            ],
            'WILL_PAY_LATER': [
                r'\b(will pay|gonna pay)\s+(tomorrow|next week|later|soon|by)',
                r'\b(pay|payment)\s+(tomorrow|next|later|soon)',
            ],
            'ALREADY_PAID': [
                r'\b(already paid|paid already|payment done|cleared|settled)',
                r'\b(paid|done|completed)\s+(already|yesterday|last|before)',
            ],
            'FACING_FINANCIAL_ISSUES': [
                r'\b(lost.*?job|no job|unemployed)',
                r'\b(financial.*?(problem|issue|crisis))',
                r'\b(difficult|hard|tough)\s+(time|situation)',
            ],
        }
        
        self.INTENT_PATTERNS_HI = {
            'WILL_PAY_NOW': [
                r'\b(अभी|आज|तुरंत|अब).*?(भुगतान|पे|देंगे|करेंगे|कर रही|कर रहा|भर रही|भर रहा)',
                r'\b(payment|pay).*?(abhi|aaj|turant|kar|dunga|dungi|rahi|raha)',
                r'\b(हां|हा|जी).*?(भुगतान|payment|pay|कर|भर)',
                r'\b(मै|मैं).*?(भर|pay).*?(दूँगी|दूंगा)',
            ],
            'WILL_PAY_LATER': [
                r'\b(कल|बाद में|जल्द).*?(भुगतान|पे|देंगे)',
                r'\b(kal|baad|later).*?(pay|payment|kar dunga)',
            ],
            'ALREADY_PAID': [
                r'\b(पहले ही|already).*?(भुगतान|paid|कर दिया)',
                r'\b(payment.*?(ho gaya|done|kar diya))',
                r'\b(किया|दिया|हो गया).*?(पहले|already)',
            ],
        }
    
    def _match_intent_heuristic(self, text, language='en'):
        text_lower = text.lower().strip()
        patterns = self.INTENT_PATTERNS_EN if language == 'en' else self.INTENT_PATTERNS_HI
        
        for intent, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return intent, 0.85
        
        return None, 0.0
    
    def _extract_date_commitment(self, text, language='en'):
        """Extract date/time commitment from user response"""
        text_lower = text.lower().strip()
        
        # Extract number of days
        days_pattern = r'(\d+)\s*(day|days|din)'
        match = re.search(days_pattern, text_lower)
        if match:
            num_days = int(match.group(1))
            commitment_date = datetime.now() + timedelta(days=num_days)
            return commitment_date, num_days
        
        # Tomorrow
        if any(word in text_lower for word in ['tomorrow', 'kal', 'कल']):
            commitment_date = datetime.now() + timedelta(days=1)
            return commitment_date, 1
        
        # Next week
        if any(phrase in text_lower for phrase in ['next week', 'agle hafte', 'अगले हफ्ते']):
            commitment_date = datetime.now() + timedelta(days=7)
            return commitment_date, 7
        
        return None, None
    
    def generate_verification_script(self, customer_data, bank_name, language='en'):
        script = MultilingualScriptTemplates.get_verification_script(
            language=language,
            bank_name=bank_name,
            customer_name=customer_data['name'],
            variation=0
        )
        print(f"[TEMPLATE/{language.upper()}] Verification script: {script}")
        return script
    
    def analyze_verification(self, customer_response, customer_data, language='en'):
        print(f"[GEMINI/VERIFICATION/{language.upper()}] Analyzing: '{customer_response}'")
        
        response_lower = customer_response.lower().strip()
        
        if language == 'en':
            positive_words = ['yes', 'yeah', 'yep', 'correct', 'speaking', 'this is', 'i am', 'myself', 'haan', 'ha']
            negative_words = ['no', 'wrong', 'not me', 'incorrect', 'nahi', 'nai']
            not_interested = ['not interested', 'stop calling', "don't call", 'mat karo']
        else:
            positive_words = ['हां', 'हा', 'जी', 'बोल रहा', 'बोल रही', 'yes', 'ha', 'haan', 'main hoon', 'मैं हूं', 'रेडी']
            negative_words = ['नहीं', 'गलत', 'नहीं', 'no', 'nahi', 'galat', 'nai']
            not_interested = ['रुचि नहीं', 'call mat', 'बंद करो', 'not interested', 'mat karo']
        
        if any(word in response_lower for word in positive_words):
            intent = 'CONFIRMED_IDENTITY'
        elif any(word in response_lower for word in negative_words):
            intent = 'DENIED_IDENTITY'
        elif any(phrase in response_lower for phrase in not_interested):
            intent = 'NOT_INTERESTED'
        else:
            prompt_template = {
                'en': f"""Classify this response to "Am I speaking with {customer_data['name']}?":
Response: "{customer_response}"

Return JSON only:
{{"intent": "CONFIRMED_IDENTITY|DENIED_IDENTITY|NOT_INTERESTED|CONFUSION|UNCLEAR"}}

Examples:
- "yes", "yeah", "speaking", "haan", "ji", "myself" → CONFIRMED_IDENTITY
- "no", "wrong number", "nahi" → DENIED_IDENTITY
- "not interested", "stop calling" → NOT_INTERESTED
- "who is this" → CONFUSION
- unclear → UNCLEAR""",
                
                'hi': f"""इस जवाब को वर्गीकृत करें "क्या मैं {customer_data['name']} जी से बात कर रही हूं?":
जवाब: "{customer_response}"

केवल JSON लौटाएं:
{{"intent": "CONFIRMED_IDENTITY|DENIED_IDENTITY|NOT_INTERESTED|CONFUSION|UNCLEAR"}}

उदाहरण:
- "हां", "हा", "जी", "बोल रहा हूं", "मैं हूं" → CONFIRMED_IDENTITY
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
        script = MultilingualScriptTemplates.get_emi_script(
            language, customer_data
        )
        print(f"[TEMPLATE/{language.upper()}] EMI script: {script[:100]}...")
        return script
    
    def get_bot_response(self, call_state, customer_response, customer_data, 
                        conversation_history, language='en'):
        print(f"[GEMINI/NLU/{language.upper()}] State={call_state}, Input='{customer_response}'")
        
        # Extract date commitment if present
        commitment_date, num_days = self._extract_date_commitment(customer_response, language)
        
        heuristic_intent, confidence = self._match_intent_heuristic(customer_response, language)
        
        if confidence >= 0.8:
            print(f"[HEURISTIC/{language.upper()}] Matched: {heuristic_intent}")
            return self._build_response(
                heuristic_intent, call_state, customer_data,
                conversation_history, customer_response, language,
                commitment_date=commitment_date, num_days=num_days
            )
        
        history_str = self._build_conversation_context(conversation_history, language)
        unclear_count = sum(1 for t in conversation_history if t.get('intent') == 'UNCLEAR')
        
        if language == 'en':
            prompt = f"""You are an NLU engine for EMI recovery. Classify customer intent and extract commitment details.

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

If customer says "No", "Nothing else", "That's all", classify as POLITE_EXIT.

Return JSON:
{{
    "intent": "classified_intent",
    "confidence": 0.0-1.0
}}"""
        
        else:
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

इरादे: WILL_PAY_NOW (अभी पेमेंट करेंगे), WILL_PAY_LATER (बाद में पेमेंट करेंगे), 
ALREADY_PAID (पहले ही पेमेंट किया), FACING_FINANCIAL_ISSUES (वित्तीय समस्याएं), 
DISPUTE_AMOUNT (राशि विवाद), REQUEST_EXTENSION (समय बढ़ाने की मांग), 
REQUEST_PAYMENT_PLAN (पेमेंट प्लान), DEMANDS_SUPERVISOR (सुपरवाइजर से बात), 
POLITE_EXIT (विनम्र बाहर निकलना / नहीं, बस इतना ही), ANGRY_ABUSIVE (गुस्सा/अपमानजनक), 
CONFUSION_WRONG_PERSON (गलत व्यक्ति), SMALL_TALK (छोटी बातचीत), UNCLEAR (अस्पष्ट)

अगर ग्राहक कहता है "नहीं", "कुछ नहीं", "बस", तो इसे POLITE_EXIT मानें।

JSON लौटाएं:
{{
    "intent": "classified_intent",
    "confidence": 0.0-1.0
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
            
            if ai_confidence < 0.6 and heuristic_intent:
                print(f"[FALLBACK/{language.upper()}] Using heuristic: {heuristic_intent}")
                intent = heuristic_intent
            
            return self._build_response(
                intent, call_state, customer_data, conversation_history,
                customer_response, language, 
                next_state=None,
                should_transfer=False, 
                context=result.get('context', {}), 
                commitment_date=commitment_date, 
                num_days=num_days
            )
            
        except Exception as e:
            print(f"[ERROR/{language.upper()}] AI failed: {e}")
            
            if heuristic_intent:
                return self._build_response(
                    heuristic_intent, call_state, customer_data,
                    conversation_history, customer_response, language,
                    commitment_date=commitment_date, num_days=num_days
                )
            
            return self._build_fallback_response(unclear_count, customer_data, language)
    
    def _extract_json(self, text):
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return text
    
    def _build_conversation_context(self, history, language='en'):
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
                       next_state=None, should_transfer=False, context=None,
                       commitment_date=None, num_days=None):
        
        if not context:
            context = {}
        
        # Handle commitment date
        if commitment_date and num_days:
            formatted_date = MultilingualScriptTemplates.format_date_for_speech(
                commitment_date.strftime("%Y-%m-%d"), language
            )
            context['commitment_date'] = formatted_date
            context['num_days'] = num_days
            print(f"[CONTEXT/{language.upper()}] Commitment: {num_days} days → {formatted_date}")
        
        if not next_state:
            unclear_count = sum(1 for t in conversation_history if t.get('intent') == 'UNCLEAR')
            
            if intent == 'POLITE_EXIT':
                next_state = 'HANGUP'
            # --- CHANGE: Do not hang up immediately. Keep conversation open. ---
            elif intent in ['WILL_PAY_NOW', 'WILL_PAY_LATER', 'ALREADY_PAID']:
                next_state = 'CONVERSATION' 
            # ------------------------------------------------------------------
            elif intent in ['DEMANDS_SUPERVISOR', 'ANGRY_ABUSIVE']:
                next_state = 'PENDING_TRANSFER'
                should_transfer = True
            elif unclear_count >= 2:
                next_state = 'OFFERING_OPTIONS'
            else:
                next_state = 'CONVERSATION'
        
        if next_state == 'OFFERING_OPTIONS':
            polite_response = MultilingualScriptTemplates.get_script(
                'offer_options', language
            )
        else:
            polite_response = MultilingualScriptTemplates.get_conversation_response(
                language=language,
                intent=intent,
                customer_data=customer_data,
                context=context,
                variation=0
            )
        
        print(f"[RESPONSE/{language.upper()}] Intent={intent}, NextState={next_state}")
        
        return {
            "intent": intent,
            "next_state": next_state,
            "polite_bot_response": polite_response,
            "should_transfer": should_transfer,
            "transfer_reason": f"Customer requested: {intent}" if should_transfer else None,
            "context": context
        }
    
    def _build_fallback_response(self, unclear_count, customer_data, language='en'):
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
                "सॉरी, क्या आप दोहरा सकते हैं?"
            )
            return {
                "intent": "UNCLEAR",
                "next_state": "CONVERSATION",
                "polite_bot_response": fallback_text,
                "should_transfer": False,
                "transfer_reason": None
            }