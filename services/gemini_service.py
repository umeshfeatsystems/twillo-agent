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
                r'\b(i will|ill)\s+(pay|do it)\s+(today)',
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
            'POLITE_EXIT': [
                r'\b(no|nothing|that\'s it|that\'s all|bye|thank you|thanks)',
                r'\b(ok|okay|sure|fine)\b'
            ],
            'ASK_WHO_ARE_YOU': [
                r'\b(who|kaun)\s+(are you|is this|speaking|bol)',
                r'\b(your name|naam kya)',
                r'\b(calling from|kaha se)',
            ],
            # --- UPDATED REGEX FOR "How did you got" & PRIVACY ---
            'ASK_SOURCE_OF_INFO': [
                r'\b(how|where).*?(get|got|found|obtain|source).*?(number|details|info|data)',
                r'\b(who gave).*?(number|details)',
                r'\b(how do you know)',
                r'\b(privacy|personal)\s+(details|data)',
            ],
            'ASK_AMOUNT': [
                r'\b(how much|what is)\s+(the amount|pending|due|balance)',
                r'\b(total)\s+(amount|due)',
                r'\b(kitna|amount)\s+(hai|baki|dena)',
            ],
            'ASK_DETAILS': [
                r'\b(which|what)\s+(payment|loan|emi|bank)',
                r'\b(details|batao)\s+(bhejo|send|tell)',
                r'\b(konsa|kaunsa)\s+(payment|loan|emi)',
                r'\b(explain|details)\s+(please)',
            ],
            'REPEAT_DETAILS': [
                r'\b(repeat|say|tell).*?(again|details)',
                r'\b(didn\'t hear|pardon|what was that)',
            ],
            'DISPUTE_AMOUNT': [
                r'\b(wrong|incorrect|false|too high)\s+(amount|balance|due)',
                r'\b(calculated|calculation)\s+(error|mistake)',
                r'\b(not)\s+(my)\s+(loan|amount)',
                r'\b(fraud|scam)',
            ],
            'REQUEST_PAYMENT_PLAN': [
                r'\b(parts|installments|split|partial)\s+(payment|pay)',
                r'\b(half|some)\s+(now|today)',
                r'\b(cannot pay|can\'t pay)\s+(full|all)',
            ],
            'DEMANDS_SUPERVISOR': [
                r'\b(manager|supervisor|senior|boss)',
                r'\b(speak to|talk to)\s+(someone else|human|agent)',
            ],
            'FACING_FINANCIAL_ISSUES': [
                r'\b(lost.*?job|no job|unemployed)',
                r'\b(financial.*?(problem|issue|crisis))',
                r'\b(no money|broke)',
            ],
            'CONFIRMED_IDENTITY': [
                # Negative lookahead to ensure "I am" isn't followed by "not"
                r'\b(speaking|this is|myself)\b',
                r'\b(i am)\b(?!\s*not)', 
                r'\b(yes|yeah|correct|right)\b'
            ]
        }
        
        # Hindi Regex Patterns
        self.INTENT_PATTERNS_HI = {
            'WILL_PAY_NOW': [
                r'\b(अभी|आज|तुरंत|अब).*?(भर|दे|कर|भुगतान|पे).*?(दूंगा|दूंगी|देंगे|दूँगी|दूँगा|रहा|रही|हूं|हूँ)',
                r'\b(भर|दे|कर|pay).*?(दूंगा|दूंगी|दूँगी|दूँगा).*?(आज|अभी)',
                r'\b(main|mai).*?(aaj|abhi).*?(bhar|pay|kar).*?(dunga|dungi)',
                r'\b(aaj|abhi)\s+(hi)?\s*(bhar|pay|kar)\s*(dunga|dungi)',
                r'\b(payment|pay).*?(abhi|aaj|turant|kar|dunga|dungi|rahi|raha)',
                r'\b(link|लिंक|qr|upi).*?(bhejo|bejo|bhej|send|do|dedo)',
            ],
            'WILL_PAY_LATER': [
                r'\b(कल|बाद में|जल्द|अगले).*?(भुगतान|पे|देंगे|करूंगा|भर दूंगा)',
                r'\b(kal|baad|later|agle).*?(pay|payment|kar dunga)',
                r'\b(nahi|abhi nahi|baad mein).*?(pay|dunga)',
            ],
            'ALREADY_PAID': [
                r'\b(पहले ही|already).*?(भुगतान|paid|कर दिया)',
                r'\b(payment.*?(ho gaya|done|kar diya))',
            ],
            'POLITE_EXIT': [
                r'\b(nahi|bas|kuch nahi|shukriya|thank you|dhanyavad|bye|tata)',
                r'\b(नहीं|बस|शुक्रिया|धन्यवाद|नमस्ते)',
                r'\b(ha|haan|theek hai|ok|chale ga|acha|sahi hai|thik hai)\b',
                r'\b(ठीक|अच्छा|हाँ|जी|ओके|सही)\s*(है)?\b'
            ],
            'ASK_WHO_ARE_YOU': [
                r'\b(कौन|कहा).*?(बोल|कर|ho|rahe|se)',
                r'\b(kaun|kahan|who).*?(bol|speaking|calling)',
                r'\b(naam|name).*?(kya|batao)',
                r'\b(kisne|kisko).*?(call)',
                r'\b(aap kaun|tum kaun)',
            ],
            'ASK_SOURCE_OF_INFO': [
                r'\b(kahan se|kidhar se).*?(number|detail|mila|liya)',
                r'\b(kaise|kisne).*?(number|diya)',
                r'\b(mere baare mein).*?(kaise pata)',
            ],
            'ASK_AMOUNT': [
                r'\b(kitna|kya).*?(baki|amount|due|hai|paisa|bharna)',
                r'\b(amount|total).*?(batao|bolo|hai)',
            ],
            'ASK_DETAILS': [
                r'\b(konsa|kaunsa|kis|kiska|koun sa).*?(payment|loan|emi|din|day|chiz)',
                r'\b(detail|jankari).*?(do|batao|chahiye)',
                r'\b(kis|what).*?(baare mein|regarding)',
            ],
            'REPEAT_DETAILS': [
                r'\b(wapas|phir se|fir se|dobara).*?(batao|bolo|amount)',
                r'\b(sunayi nahi|samajh nahi).*?(diya|aaya)',
                r'\b(repeat).*?(karo|amount)',
            ],
            'DISPUTE_AMOUNT': [
                r'\b(galat|zyada|jyada).*?(hai|amount|lag raha)',
                r'\b(wrong|check).*?(karo|amount)',
                r'\b(hisab|calculation).*?(galat|check)',
                r'\b(fraud|scam)',
            ],
            'REQUEST_PAYMENT_PLAN': [
                r'\b(kisto|installment|tukdo|part).*?(mein|pay|karunga)',
                r'\b(aadha|half|thoda).*?(abhi|lelo|pay)',
                r'\b(pura|full).*?(nahi|baad mein)',
            ],
            'DEMANDS_SUPERVISOR': [
                r'\b(manager|senior|supervisor|sahab).*?(baat|connect)',
                r'\b(kisi aur).*?(baat|bol)',
            ],
            'FACING_FINANCIAL_ISSUES': [
                r'\b(paise|naukri|job).*?(nahi|gayi|problem|dikkat)',
                r'\b(financial|arthik).*?(problem|issue)',
                r'\b(garib|poor|pareshani)',
            ],
            'CONFIRMED_IDENTITY': [
                r'\b(main|mai|hum).*?(bol|baat).*?(raha|rahi)',
                r'\b(speaking|hi|hoon|hun)\b',
                r'\b(ha|haan|yes|ji|sahi)\b'
            ]
        }
    
    def _match_intent_heuristic(self, text, language='en'):
        text_lower = text.lower().strip()
        patterns = self.INTENT_PATTERNS_EN if language == 'en' else self.INTENT_PATTERNS_HI
        for intent, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return intent, 0.95
        return None, 0.0
    
    def _extract_date_commitment(self, text, language='en'):
        text_lower = text.lower().strip()
        num_days = -1 
        
        digit_pattern = r'(\d+)\s*(day|days|din|दिन|रोज)'
        digit_match = re.search(digit_pattern, text_lower)
        if digit_match: num_days = int(digit_match.group(1))
        
        if num_days == -1:
            hindi_nums = {'ek': 1, 'do': 2, 'teen': 3, 'chaar': 4, 'char': 4, 'paanch': 5, 'das': 10, 'एक': 1, 'दो': 2, 'तीन': 3, 'चार': 4, 'पांच': 5, 'दस': 10}
            for word, val in hindi_nums.items():
                if (f"{word} din" in text_lower or f"{word} days" in text_lower or f"{word} दिन" in text_lower):
                    num_days = val; break

        if num_days == -1:
            if any(w in text_lower for w in ['today', 'aaj', 'abhi', 'now', 'today', 'आज', 'अभी']): num_days = 0
            elif any(w in text_lower for w in ['tomorrow', 'kal', 'कल']): num_days = 1
            elif any(p in text_lower for p in ['next week', 'agle hafte']): num_days = 7
        
        if num_days >= 0:
            return datetime.now() + timedelta(days=num_days), num_days
        return None, None
    
    def generate_verification_script(self, customer_data, bank_name, language='en'):
        return MultilingualScriptTemplates.get_verification_script(language, bank_name, customer_data['name'])
    
    def analyze_verification(self, customer_response, customer_data, language='en'):
        print(f"[GEMINI/VERIFICATION/{language.upper()}] Analyzing: '{customer_response}'")
        response_lower = customer_response.lower().strip()
        
        # FIXED LOGIC: Prioritize Negatives first to avoid "I am not" matching "I am"
        if language == 'en':
            negative_words = ['no', 'not', 'wrong', 'incorrect', "isn't", "don't know", "none"]
            positive_words = ['yes', 'yeah', 'correct', 'speaking', 'this is', 'i am', 'myself', 'yep']
        else:
            negative_words = ['नहीं', 'गलत', 'wrong', 'no', 'nahi', 'mat', 'na', 'kaun'] 
            positive_words = ['हां', 'हा', 'जी', 'बोल रहा', 'में हूं', 'main hun', 'yes', 'मैं', 'sahi', 'yahi']
            
        # 1. Check Negative Words First
        if any(word in response_lower for word in negative_words):
             intent = 'DENIED_IDENTITY'
             
        # 2. Then Check Positive Words
        elif any(word in response_lower for word in positive_words): 
             intent = 'CONFIRMED_IDENTITY'
             
        else:
            # 3. Fallback to Heuristics for questions
            heuristic_intent, _ = self._match_intent_heuristic(customer_response, language)
            if heuristic_intent in ['ASK_WHO_ARE_YOU', 'ASK_SOURCE_OF_INFO', 'ASK_DETAILS', 'REPEAT_DETAILS', 'ASK_AMOUNT']:
                intent = heuristic_intent
            else:
                intent = 'UNCLEAR'
            
        polite_response = MultilingualScriptTemplates.get_verification_response(language, intent, Config.BANK_NAME, customer_data['name'])
        return {"intent": intent, "polite_bot_response": polite_response}

    def generate_emi_details_script(self, customer_data, language='en'):
        return MultilingualScriptTemplates.get_emi_script(language, customer_data)
    
    def get_bot_response(self, call_state, customer_response, customer_data, conversation_history, language='en'):
        print(f"[GEMINI/NLU/{language.upper()}] State={call_state}, Input='{customer_response}'")
        
        # 1. Check Heuristics (Regex) FIRST for Inquiries/Questions
        heuristic_intent, confidence = self._match_intent_heuristic(customer_response, language)
        
        # 2. Check Date/Commitment
        commitment_date, num_days = self._extract_date_commitment(customer_response, language)
        
        intent = None

        # --- PRIORITY LOGIC ---
        # Prioritize answering questions over accepting payments blindly
        priority_intents = [
            'ASK_WHO_ARE_YOU', 'ASK_SOURCE_OF_INFO', 'ASK_DETAILS', 
            'ASK_AMOUNT', 'REPEAT_DETAILS', 'DISPUTE_AMOUNT', 
            'REQUEST_PAYMENT_PLAN', 'DEMANDS_SUPERVISOR', 'FACING_FINANCIAL_ISSUES'
        ]

        if heuristic_intent in priority_intents and confidence >= 0.8:
            intent = heuristic_intent
            print(f"[LOGIC] Priority Inquiry Detected: {intent} (Ignoring date logic for now)")
        
        elif commitment_date:
            print(f"[LOGIC] Date detected ({num_days} days).")
            if num_days == 0: intent = 'WILL_PAY_NOW'
            elif num_days > 7: intent = 'REQUEST_EXTENSION'
            else: intent = 'WILL_PAY_LATER'
        
        elif heuristic_intent:
            intent = heuristic_intent
            print(f"[HEURISTIC] Matched: {intent} ({confidence})")

        # Context-Aware Exit Logic
        last_intent = conversation_history[-1].get('intent') if conversation_history else None
        if last_intent in ['WILL_PAY_NOW', 'WILL_PAY_LATER', 'REQUEST_EXTENSION'] and (not intent or intent in ['CONFIRMED_IDENTITY', 'UNCLEAR']):
            text_lower = customer_response.lower().strip()
            agreement_words = ['ok', 'okay', 'theek', 'thik', 'ha', 'haan', 'han', 'ji', 'acha', 'done', 'yes', 'sahi', 'ठीक', 'हाँ', 'जी']
            if len(text_lower.split()) <= 3 and any(w in text_lower for w in agreement_words):
                 intent = 'POLITE_EXIT'

        if not intent:
            if len(customer_response.split()) < 3 and language == 'hi' and 'ha' in customer_response.lower(): intent = 'POLITE_EXIT' 
            else: intent = 'UNCLEAR' 

        return self._build_response(intent, call_state, customer_data, conversation_history, customer_response, language, commitment_date=commitment_date, num_days=num_days)

    def _build_response(self, intent, call_state, customer_data, conversation_history, customer_response, language='en', next_state=None, should_transfer=False, context=None, commitment_date=None, num_days=None):
        if not context: context = {}
        if commitment_date:
            context['commitment_date'] = MultilingualScriptTemplates.format_date_for_speech(commitment_date.strftime("%Y-%m-%d"), language)
            context['num_days'] = num_days
        
        if not next_state:
            if intent == 'POLITE_EXIT': next_state = 'HANGUP'
            # INQUIRIES & DISPUTES: Stay in conversation
            elif intent in ['ASK_WHO_ARE_YOU', 'ASK_SOURCE_OF_INFO', 'ASK_DETAILS', 'REPEAT_DETAILS', 'ASK_AMOUNT', 'DISPUTE_AMOUNT', 'REQUEST_PAYMENT_PLAN', 'FACING_FINANCIAL_ISSUES']: next_state = 'CONVERSATION' 
            elif intent == 'WILL_PAY_NOW': next_state = 'CONVERSATION' 
            elif intent in ['WILL_PAY_LATER', 'REQUEST_EXTENSION', 'ALREADY_PAID', 'CONFIRMED_IDENTITY']: next_state = 'CONVERSATION'
            elif intent in ['DEMANDS_SUPERVISOR', 'ANGRY_ABUSIVE']: next_state = 'PENDING_TRANSFER'; should_transfer = True
            elif intent == 'UNCLEAR':
                unclear_count = sum(1 for t in conversation_history if t.get('intent') == 'UNCLEAR')
                next_state = 'OFFERING_OPTIONS' if unclear_count >= 2 else 'CONVERSATION'
            else: next_state = 'CONVERSATION'

        if next_state == 'OFFERING_OPTIONS':
             polite_response = MultilingualScriptTemplates.get_script('offer_options', language)
        else:
            polite_response = MultilingualScriptTemplates.get_conversation_response(language=language, intent=intent, customer_data=customer_data, context=context, variation=0)
        
        return {"intent": intent, "next_state": next_state, "polite_bot_response": polite_response, "should_transfer": should_transfer, "context": context}
