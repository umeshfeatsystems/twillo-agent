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
        
        # English Regex Patterns
        self.INTENT_PATTERNS_EN = {
            'WILL_PAY_NOW': [
                r'\b(will|gonna|going to|can|would like to)\s+(pay|make payment|settle|clear)',
                r'\b(pay|paying|payment)\s+(now|immediately|right now|today|right away)',
                r'\b(send|share)\s+(link|payment details|qr code)',
            ],
            'WILL_PAY_LATER': [
                r'\b(will pay|gonna pay)\s+(tomorrow|next week|later|soon|by)',
                r'\b(pay|payment)\s+(tomorrow|next|later|soon)',
                r'\b(not)\s+(now|today)',
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
            'POLITE_EXIT': [
                r'\b(no|nothing|that\'s it|that\'s all|bye|thank you|thanks)',
            ],
            'ASK_WHO_ARE_YOU': [
                r'\b(who|kaun)\s+(are you|is this|speaking|bol)',
                r'\b(your name|naam kya)',
                r'\b(calling from|kaha se)',
            ],
            'ASK_SOURCE_OF_INFO': [
                r'\b(how|kaha se)\s+(get|mila)\s+(number|details|info)',
                r'\b(who gave|kisne diya)\s+(number)',
                r'\b(why|kyu)\s+(calling|call)',
            ],
            'ASK_DETAILS': [
                r'\b(which|konsa|what)\s+(payment|loan|emi|amount)',
                r'\b(details|batao)\s+(bhejo|send|tell)',
                r'\b(kitna|how much)\s+(pending|due|baki)',
                r'\b(due date|kab|date)\s+(hai|is)',
                r'\b(konsa|kaunsa)\s+(din|day)',
            ],
            'CONFIRMED_IDENTITY': [
                r'\b(speaking|this is|i am|myself)\b',
                r'\b(yes|yeah|correct|right)\b'
            ]
        }
        
        # Hindi Regex Patterns
        self.INTENT_PATTERNS_HI = {
            'WILL_PAY_NOW': [
                r'\b(अभी|आज|तुरंत|अब).*?(भुगतान|पे|देंगे|करेंगे|कर रही|कर रहा|भर रही|भर रहा)',
                r'\b(payment|pay).*?(abhi|aaj|turant|kar|dunga|dungi|rahi|raha)',
                r'\b(link|लिंक).*?(bhejo|bejo|bhej|send)',
            ],
            'WILL_PAY_LATER': [
                r'\b(कल|बाद में|जल्द|अगले).*?(भुगतान|पे|देंगे|करूंगा|भर दूंगा)',
                r'\b(kal|baad|later|agle).*?(pay|payment|kar dunga)',
                r'\b(nahi|abhi nahi|baad mein).*?(pay|dunga)',
            ],
            'ALREADY_PAID': [
                r'\b(पहले ही|already).*?(भुगतान|paid|कर दिया)',
                r'\b(payment.*?(ho gaya|done|kar diya))',
                r'\b(किया|दिया|हो गया).*?(पहले|already)',
            ],
            'POLITE_EXIT': [
                r'\b(nahi|bas|kuch nahi|shukriya|thank you|dhanyavad|bye)',
                r'\b(नहीं|बस|शुक्रिया|धन्यवाद|नमस्ते)',
                r'\b(ha|haan|theek hai|ok|chale ga|acha)\b' 
            ],
            'ASK_WHO_ARE_YOU': [
                r'\b(कौन|कहा).*?(बोल|कर|ho|rahe|se)',
                r'\b(kaun|kahan|who).*?(bol|speaking|calling)',
                r'\b(naam|name).*?(kya|batao)',
                r'\b(kisne|kisko).*?(call)',
                r'\b(aap kaun|tum kaun)',
            ],
            'ASK_SOURCE_OF_INFO': [
                r'\b(kahan se|kidhar se).*?(number|detail|mila)',
                r'\b(kaise|kisne).*?(number|diya)',
                r'\b(kyun|kyu).*?(call|phone)',
                r'\b(mere baare mein).*?(kaise pata)',
            ],
            'ASK_DETAILS': [
                r'\b(konsa|kaunsa|kis|kiska).*?(payment|loan|emi|amount|din|day)',
                r'\b(kitna|kya).*?(baki|amount|due|hai)',
                r'\b(kab|date).*?(hai|thi|tha)',
                r'\b(detail|jankari).*?(do|batao)',
            ],
            'CONFIRMED_IDENTITY': [
                r'\b(main|mai|hum).*?(bol|baat).*?(raha|rahi)',
                r'\b(speaking|hi|hoon|hun)\b',
                r'\b(ha|haan|yes|ji|sahi)\b'
            ]
        }
    
    def _match_intent_heuristic(self, text, language='en'):
        """Simple Regex matching for intent detection"""
        text_lower = text.lower().strip()
        patterns = self.INTENT_PATTERNS_EN if language == 'en' else self.INTENT_PATTERNS_HI
        
        for intent, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return intent, 0.85
        return None, 0.0
    
    def _extract_date_commitment(self, text, language='en'):
        """Extract date/time commitment from user response."""
        text_lower = text.lower().strip()
        num_days = 0
        
        # 1. Numeric extraction
        digit_pattern = r'(\d+)\s*(day|days|din|दिन|रोज)'
        digit_match = re.search(digit_pattern, text_lower)
        
        if digit_match:
            num_days = int(digit_match.group(1))
        
        # 2. Hindi text numbers
        if num_days == 0:
            hindi_nums = {
                'ek': 1, 'do': 2, 'teen': 3, 'chaar': 4, 'char': 4, 'paanch': 5, 
                'che': 6, 'saat': 7, 'aath': 8, 'nau': 9, 'das': 10,
                'pandrah': 15, 'bees': 20, 'tees': 30,
                'एक': 1, 'दो': 2, 'तीन': 3, 'चार': 4, 'पांच': 5, 'दस': 10, 'बीस': 20
            }
            for word, val in hindi_nums.items():
                if (f"{word} din" in text_lower or f"{word} days" in text_lower or f"{word} दिन" in text_lower):
                    num_days = val
                    break

        # 3. Weeks extraction
        if num_days == 0:
            week_pattern = r'(\d+)\s*(hafte|week|weeks|हफ्ते|सप्ताह)'
            week_match = re.search(week_pattern, text_lower)
            if week_match:
                num_days = int(week_match.group(1)) * 7

        # 4. Relative terms
        if num_days == 0:
            if any(word in text_lower for word in ['tomorrow', 'kal', 'कल']):
                num_days = 1
            elif any(phrase in text_lower for phrase in ['next week', 'agle hafte', 'अगले हफ्ते']):
                num_days = 7
            elif any(word in text_lower for word in ['month', 'mahine', 'mahina', 'महीने']):
                num_days = 30
        
        if num_days > 0:
            commitment_date = datetime.now() + timedelta(days=num_days)
            return commitment_date, num_days
        
        return None, None
    
    def generate_verification_script(self, customer_data, bank_name, language='en'):
        return MultilingualScriptTemplates.get_verification_script(
            language, bank_name, customer_data['name']
        )
    
    def analyze_verification(self, customer_response, customer_data, language='en'):
        print(f"[GEMINI/VERIFICATION/{language.upper()}] Analyzing: '{customer_response}'")
        response_lower = customer_response.lower().strip()
        
        if language == 'en':
            positive_words = ['yes', 'yeah', 'correct', 'speaking', 'this is', 'i am']
            negative_words = ['no', 'wrong', 'not me', 'incorrect']
        else:
            positive_words = ['हां', 'हा', 'जी', 'बोल रहा', 'में हूं', 'main hun', 'yes', 'मैं']
            negative_words = ['नहीं', 'गलत', 'नहीं', 'no', 'nahi']
            
        if any(word in response_lower for word in positive_words):
            intent = 'CONFIRMED_IDENTITY'
        elif any(word in response_lower for word in negative_words):
            intent = 'DENIED_IDENTITY'
        else:
            # Check heuristics for questions/details even during verification
            heuristic_intent, _ = self._match_intent_heuristic(customer_response, language)
            if heuristic_intent in ['ASK_WHO_ARE_YOU', 'ASK_SOURCE_OF_INFO', 'ASK_DETAILS']:
                intent = heuristic_intent
            else:
                intent = 'UNCLEAR'
            
        polite_response = MultilingualScriptTemplates.get_verification_response(
            language, intent, Config.BANK_NAME, customer_data['name']
        )
        
        return {"intent": intent, "polite_bot_response": polite_response}

    def generate_emi_details_script(self, customer_data, language='en'):
        return MultilingualScriptTemplates.get_emi_script(language, customer_data)
    
    def get_bot_response(self, call_state, customer_response, customer_data, 
                        conversation_history, language='en'):
        print(f"[GEMINI/NLU/{language.upper()}] State={call_state}, Input='{customer_response}'")
        
        # 1. EXTRACT DATE FIRST
        commitment_date, num_days = self._extract_date_commitment(customer_response, language)
        
        intent = None
        heuristic_intent = None
        
        # 2. LOGIC OVERRIDE: Date detected
        if commitment_date:
            print(f"[LOGIC] Date detected ({num_days} days).")
            intent = 'REQUEST_EXTENSION' if num_days > 7 else 'WILL_PAY_LATER'
        
        # 3. Heuristics
        if not intent:
            heuristic_intent, confidence = self._match_intent_heuristic(customer_response, language)
            if confidence >= 0.8:
                intent = heuristic_intent
                print(f"[HEURISTIC] Matched: {intent} ({confidence})")

        # 4. LLM Fallback
        if not intent:
            if len(customer_response.split()) < 3 and language == 'hi' and 'ha' in customer_response.lower():
                 intent = 'POLITE_EXIT' 
            else:
                 intent = 'UNCLEAR' 

        return self._build_response(
            intent, call_state, customer_data, conversation_history,
            customer_response, language,
            commitment_date=commitment_date, num_days=num_days
        )

    def _build_response(self, intent, call_state, customer_data, 
                       conversation_history, customer_response, language='en',
                       next_state=None, should_transfer=False, context=None,
                       commitment_date=None, num_days=None):
        
        if not context: context = {}
        
        if commitment_date:
            formatted_date = MultilingualScriptTemplates.format_date_for_speech(
                commitment_date.strftime("%Y-%m-%d"), language
            )
            context['commitment_date'] = formatted_date
            context['num_days'] = num_days
        
        if not next_state:
            if intent == 'POLITE_EXIT':
                next_state = 'HANGUP'
            # IMPORTANT: For questions, stay in CONVERSATION state to answer them
            elif intent in ['ASK_WHO_ARE_YOU', 'ASK_SOURCE_OF_INFO', 'ASK_DETAILS']:
                next_state = 'CONVERSATION' 
            elif intent in ['WILL_PAY_NOW', 'WILL_PAY_LATER', 'REQUEST_EXTENSION', 'ALREADY_PAID', 'CONFIRMED_IDENTITY']:
                next_state = 'CONVERSATION'
            elif intent in ['DEMANDS_SUPERVISOR', 'ANGRY_ABUSIVE']:
                next_state = 'PENDING_TRANSFER'
                should_transfer = True
            elif intent == 'UNCLEAR':
                unclear_count = sum(1 for t in conversation_history if t.get('intent') == 'UNCLEAR')
                next_state = 'OFFERING_OPTIONS' if unclear_count >= 2 else 'CONVERSATION'
            else:
                next_state = 'CONVERSATION'

        if next_state == 'OFFERING_OPTIONS':
             polite_response = MultilingualScriptTemplates.get_script('offer_options', language)
        else:
            # Map intents to template keys
            template_intent = intent
            
            polite_response = MultilingualScriptTemplates.get_conversation_response(
                language=language,
                intent=template_intent,
                customer_data=customer_data,
                context=context,
                variation=0
            )
        
        return {
            "intent": intent,
            "next_state": next_state,
            "polite_bot_response": polite_response,
            "should_transfer": should_transfer,
            "context": context
        }