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
        
        # --- EXPANDED INTENT PATTERNS (Phase 2 & 3 Scenarios) ---
        self.INTENT_PATTERNS_EN = {
            'CONFIRMED_IDENTITY': [
                r'\b(speaking|this is|myself)\b',
                r'\b(i am)\b(?!\s*not)', 
                r'\b(yes|yeah|correct|right)\b'
            ],
            # Driving/Safety is a specific high-priority subset of BUSY
            'DRIVING_SAFETY': [
                r'\b(driving|drive|riding|bike|car|traffic)\b',
                r'\b(on the road|steering)\b'
            ],
            'BUSY_CALLBACK_LATER': [
                r'\b(busy|meeting|eating|lunch|dinner|sleeping|work|office)\b',
                r'\b(call|talk)\s+(later|after|tomorrow|evening|morning)',
                r'\b(not)\s+(free|now)',
                r'\b(call)\s+(me)\s+(at|in|on)',
            ],
            'WRONG_NUMBER': [
                r'\b(wrong|incorrect)\s+(number|person)',
                r'\b(don\'t know|dont know)\s+(him|her|them)',
                r'\b(no one|nobody)\s+(by that name)',
                r'\b(bought|new)\s+(sim|number)',
            ],
            'IS_BOT': [
                r'\b(are you)\s+(a)?\s*(bot|robot|computer|machine|ai)',
                r'\b(real|human)\s+(person|agent)',
                r'\b(recording|automated)',
            ],
            'SEND_WHATSAPP': [
                r'\b(whatsapp|whats app)\b',
                r'\b(send|share)\s+(on|via)\s+(whatsapp)',
            ],
            'CANT_PAY_REFUSAL': [
                r'\b(no|not)\s+(money|funds|cash)',
                r'\b(broke|empty)\b',
                r'\b(do|take)\s+(whatever|action)',
                r'\b(sue|court|legal)',
                r'\b(wont|will not|cannot)\s+(pay)',
            ],
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
            ]
        }
        
        # Hindi Regex Patterns
        self.INTENT_PATTERNS_HI = {
            'CONFIRMED_IDENTITY': [
                r'\b(main|mai|hum).*?(bol|baat).*?(raha|rahi)',
                r'\b(speaking|hi|hoon|hun)\b',
                r'\b(ha|haan|yes|ji|sahi)\b',
                r'\b(bilkul|zarur|hanji)\b'
            ],
            'DRIVING_SAFETY': [
                r'\b(drive|driving|gaadi|gadi|bike|car)\b',
                r'\b(chala)\s+(raha|rahi)',
                r'\b(raste|rasta|road)\s+(mein|pe)',
                r'\b(traffic)\b',
            ],
            'BUSY_CALLBACK_LATER': [
                r'\b(busy|vyast|kaam)\b',
                r'\b(meeting|lunch|khana|baad mein)\b',
                r'\b(call|baat)\s+(karo|karna|badme)',
                r'\b(abhi)\s+(nahi)',
                r'\b(baje|ghante|min|minutes)', # Time indicators
            ],
            'WRONG_NUMBER': [
                r'\b(wrong|galat)\s+(number|insaan|aadmi)',
                r'\b(nahi)\s+(janta|pehchanta|pata)',
                r'\b(koi|kisi)\s+(aur|dusra)',
            ],
            'IS_BOT': [
                r'\b(bot|robot|computer|machine|record|recording)\b',
                r'\b(insaan|human|aadmi).*?(baat|bol)',
            ],
            'SEND_WHATSAPP': [
                r'\b(whatsapp|watsapp)\b',
            ],
            'CANT_PAY_REFUSAL': [
                r'\b(nahi|no)\s+(paisa|paise|money|funds)',
                r'\b(jo|kuch).*?(karna|karlo|ukhaad)',
                r'\b(nahi)\s+(pay|dunga|dungi)',
                r'\b(mar|khatam|loss)\b',
            ],
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
            ]
        }
    
    def _match_intent_heuristic(self, text, language='en'):
        text_lower = text.lower().strip()
        
        if language == 'en-hi-hybrid':
            # Check English Patterns First
            for intent, pattern_list in self.INTENT_PATTERNS_EN.items():
                for pattern in pattern_list:
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        return intent, 0.95, 'en'
            
            # Then Check Hindi Patterns
            for intent, pattern_list in self.INTENT_PATTERNS_HI.items():
                for pattern in pattern_list:
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        return intent, 0.95, 'hi'
            return None, 0.0, 'en-hi-hybrid' 
            
        else:
            patterns = self.INTENT_PATTERNS_EN if language == 'en' else self.INTENT_PATTERNS_HI
            for intent, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        return intent, 0.95, language
            return None, 0.0, language
    
    def _extract_callback_time(self, text, language='en'):
        """Extract relative or absolute time for callback"""
        text_lower = text.lower().strip()
        now = datetime.now()
        
        # 1. Relative Minutes (10 min, aadhe ghante)
        min_match = re.search(r'(\d+)\s*(min|minute)', text_lower)
        if min_match:
            return now + timedelta(minutes=int(min_match.group(1))), f"{min_match.group(1)} minutes"
            
        if 'half' in text_lower or 'aadhe' in text_lower or 'adhe' in text_lower:
            return now + timedelta(minutes=30), "30 minutes"
            
        if 'hour' in text_lower or 'ghante' in text_lower or 'ghanta' in text_lower:
            # Check number before 'hour'
            hour_match = re.search(r'(\d+)\s*(hour|ghante|ghanta)', text_lower)
            hours = int(hour_match.group(1)) if hour_match else 1
            return now + timedelta(hours=hours), f"{hours} hour"

        # 2. Absolute Time (5 pm, 5 baje)
        time_match = re.search(r'(\d+)\s*(pm|am|baje)', text_lower)
        if time_match:
            hour = int(time_match.group(1))
            period = time_match.group(2)
            # Simple conversion logic
            if 'pm' in period and hour < 12: hour += 12
            # For 'baje', usually implies PM if small number in debt collection context, but let's assume raw
            return now.replace(hour=hour, minute=0), f"{time_match.group(1)} {period}"

        # 3. Vague (Tomorrow, Kal)
        if 'tomorrow' in text_lower or 'kal' in text_lower:
            return now + timedelta(days=1), "tomorrow"
            
        if 'evening' in text_lower or 'shaam' in text_lower:
            return now.replace(hour=18, minute=0), "this evening"
            
        return None, None

    def _extract_date_commitment(self, text, language='en'):
        text_lower = text.lower().strip()
        num_days = -1 
        
        # Improved: Capture "200 days", "10 din", "5 roj" - Recognizes large digits automatically
        digit_pattern = r'(\d+)\s*(day|days|din|dino|दिन|रोज)'
        digit_match = re.search(digit_pattern, text_lower)
        if digit_match: num_days = int(digit_match.group(1))
        
        if num_days == -1:
            # Fallback for common word-numbers if regex didn't catch digit
            # NOTE: STT usually outputs "200" as digits, so strict word-matching for large numbers is rarely needed
            hindi_nums = {'ek': 1, 'do': 2, 'teen': 3, 'chaar': 4, 'char': 4, 'paanch': 5, 'das': 10, 'एक': 1, 'दो': 2, 'तीन': 3, 'चार': 4, 'पांच': 5, 'दस': 10}
            for word, val in hindi_nums.items():
                # Checking boundary to ensure we don't match substrings like 'do' in 'doing'
                if re.search(rf'\b{word}\b\s*(din|days|दिन)', text_lower):
                    num_days = val; break

        if num_days == -1:
            if any(w in text_lower for w in ['today', 'aaj', 'abhi', 'now', 'today', 'आज', 'अभी']): num_days = 0
            elif any(w in text_lower for w in ['tomorrow', 'kal', 'कल']): num_days = 1
            elif any(p in text_lower for p in ['next week', 'agle hafte']): num_days = 7
        
        if num_days >= 0:
            return datetime.now() + timedelta(days=num_days), num_days
        return None, None
    
    def generate_verification_script(self, customer_data, bank_name, language='en'):
        if language == 'en-hi-hybrid':
            lang_for_script = 'en'
        else:
            lang_for_script = language
            
        return MultilingualScriptTemplates.get_verification_script(lang_for_script, bank_name, customer_data['name'])
    
    def analyze_verification(self, customer_response, customer_data, language='en'):
        print(f"[GEMINI/VERIFICATION/{language.upper()}] Analyzing: '{customer_response}'")
        
        detected_lang = 'en' if language == 'en-hi-hybrid' else language
        
        heuristic_intent, conf, detected_lang_from_heuristic = self._match_intent_heuristic(customer_response, language)
        
        if language == 'en-hi-hybrid' and detected_lang_from_heuristic in ['en', 'hi']:
            detected_lang = detected_lang_from_heuristic
            print(f"[HYBRID] Detected language via heuristic: {detected_lang}")

        response_lower = customer_response.lower().strip()
        
        negative_words_en = ['no', 'not', 'wrong', 'incorrect', "isn't", "don't know", "none"]
        negative_words_hi = ['नहीं', 'गलत', 'wrong', 'no', 'nahi', 'mat', 'na', 'kaun', 'nahin', 'nhi', 'wrong number']
        
        positive_words_en = ['yes', 'yeah', 'correct', 'speaking', 'this is', 'i am', 'myself', 'yep']
        positive_words_hi = [
            'हां', 'हा', 'जी', 'बोल रहा', 'में हूं', 'main hun', 'yes', 'मैं', 'sahi', 'yahi',
            'haan', 'han', 'bilkul', 'bol raha', 'bol rahi', 'hoon', 'hun', 'jee', 'ji', 'hanji'
        ]

        intent = 'UNCLEAR'

        if any(word in response_lower for word in negative_words_en + negative_words_hi):
             intent = 'DENIED_IDENTITY'
        elif any(word in response_lower for word in positive_words_en + positive_words_hi): 
             intent = 'CONFIRMED_IDENTITY'
        elif heuristic_intent:
             intent = heuristic_intent
        
        polite_response = MultilingualScriptTemplates.get_verification_response(detected_lang, intent, Config.BANK_NAME, customer_data['name'])
        
        return {
            "intent": intent, 
            "polite_bot_response": polite_response,
            "detected_language": detected_lang 
        }

    def generate_emi_details_script(self, customer_data, language='en'):
        lang_to_use = 'en' if language == 'en-hi-hybrid' else language
        return MultilingualScriptTemplates.get_emi_script(lang_to_use, customer_data)
    
    def get_bot_response(self, call_state, customer_response, customer_data, conversation_history, language='en'):
        print(f"[GEMINI/NLU/{language.upper()}] State={call_state}, Input='{customer_response}'")
        
        # 1. Check Heuristics
        heuristic_intent, confidence, detected_lang = self._match_intent_heuristic(customer_response, language)
        
        if language == 'en-hi-hybrid':
            current_response_lang = detected_lang if detected_lang in ['en', 'hi'] else 'en'
        else:
            current_response_lang = language

        # 2. Check Date/Commitment
        commitment_date, num_days = self._extract_date_commitment(customer_response, language)
        
        # 3. Check Callback Time (Smart Time Extraction)
        callback_dt, callback_str = self._extract_callback_time(customer_response, language)

        intent = None

        # --- PRIORITY LOGIC ---
        priority_intents = [
            'DRIVING_SAFETY', 'BUSY_CALLBACK_LATER', 'WRONG_NUMBER', 'IS_BOT', 'SEND_WHATSAPP', 'CANT_PAY_REFUSAL',
            'ASK_WHO_ARE_YOU', 'ASK_SOURCE_OF_INFO', 'ASK_DETAILS', 
            'ASK_AMOUNT', 'REPEAT_DETAILS', 'DISPUTE_AMOUNT', 
            'REQUEST_PAYMENT_PLAN', 'DEMANDS_SUPERVISOR', 'FACING_FINANCIAL_ISSUES'
        ]

        if heuristic_intent in priority_intents and confidence >= 0.8:
            intent = heuristic_intent
        elif commitment_date:
            if num_days == 0: intent = 'WILL_PAY_NOW'
            elif num_days > 7: intent = 'REQUEST_EXTENSION'
            else: intent = 'WILL_PAY_LATER'
        elif heuristic_intent:
            intent = heuristic_intent

        # Context-Aware Exit Logic
        last_intent = conversation_history[-1].get('intent') if conversation_history else None
        if last_intent in ['WILL_PAY_NOW', 'WILL_PAY_LATER', 'REQUEST_EXTENSION'] and (not intent or intent in ['CONFIRMED_IDENTITY', 'UNCLEAR']):
            text_lower = customer_response.lower().strip()
            agreement_words = ['ok', 'okay', 'theek', 'thik', 'ha', 'haan', 'han', 'ji', 'acha', 'done', 'yes', 'sahi', 'ठीक', 'हाँ', 'जी']
            if len(text_lower.split()) <= 3 and any(w in text_lower for w in agreement_words):
                 intent = 'POLITE_EXIT'

        if not intent:
            if len(customer_response.split()) < 3 and current_response_lang == 'hi' and 'ha' in customer_response.lower(): intent = 'POLITE_EXIT' 
            else: intent = 'UNCLEAR' 

        return self._build_response(intent, call_state, customer_data, conversation_history, customer_response, current_response_lang, commitment_date=commitment_date, num_days=num_days, callback_str=callback_str)

    def _build_response(self, intent, call_state, customer_data, conversation_history, customer_response, language='en', next_state=None, should_transfer=False, context=None, commitment_date=None, num_days=None, callback_str=None):
        if not context: context = {}
        if commitment_date:
            context['commitment_date'] = MultilingualScriptTemplates.format_date_for_speech(commitment_date.strftime("%Y-%m-%d"), language)
            context['num_days'] = num_days
        
        # Inject callback time into context for the template
        if callback_str:
            context['callback_time'] = callback_str
        
        if not next_state:
            # Handle End-to-End Scenarios
            if intent == 'DRIVING_SAFETY': next_state = 'HANGUP' # Safe disconnect
            elif intent == 'BUSY_CALLBACK_LATER': next_state = 'HANGUP' # Polite disconnect
            elif intent == 'WRONG_NUMBER': next_state = 'HANGUP'
            elif intent == 'POLITE_EXIT': next_state = 'HANGUP'
            elif intent == 'SEND_WHATSAPP': next_state = 'CONVERSATION' # Confirm and ask if anything else
            elif intent == 'IS_BOT': next_state = 'CONVERSATION'
            elif intent == 'CANT_PAY_REFUSAL': next_state = 'OFFERING_SOLUTIONS'
            
            # Standard Flows
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
        
        return {
            "intent": intent, 
            "next_state": next_state, 
            "polite_bot_response": polite_response, 
            "should_transfer": should_transfer, 
            "context": context,
            "detected_language": language 
        }