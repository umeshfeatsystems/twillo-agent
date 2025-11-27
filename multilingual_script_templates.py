"""
Multi-lingual Script Templates with Dynamic Context Handling
Production-Ready Version 4.2 - End-to-End Scenarios
"""
from config import Config
from datetime import datetime
import re

class MultilingualScriptTemplates:
    
    HINDI_NUMS_0_100 = {
        0: 'शून्य', 1: 'एक', 2: 'दो', 3: 'तीन', 4: 'चार', 5: 'पाँच', 6: 'छह', 7: 'सात', 8: 'आठ', 9: 'नौ',
        10: 'दस', 11: 'ग्यारह', 12: 'बारह', 13: 'तेरह', 14: 'चौदह', 15: 'पंद्रह', 16: 'सोलह', 17: 'सत्रह', 18: 'अठारह', 19: 'उन्नीस',
        20: 'बीस', 21: 'इक्कीस', 22: 'बाईस', 23: 'तेइस', 24: 'चौबीस', 25: 'पच्चीस', 26: 'छब्बीस', 27: 'सत्ताइस', 28: 'अठ्ठाइस', 29: 'उनतीस',
        30: 'तीस', 31: 'इकतीस', 32: 'बत्तीस', 33: 'तैंतीस', 34: 'चौंतीस', 35: 'पैंतीस', 36: 'छत्तीस', 37: 'सैंतीस', 38: 'अड़तीस', 39: 'उनतालीस',
        40: 'चालीस', 41: 'इकतालीस', 42: 'बयालीस', 43: 'तैंतालिस', 44: 'चौवालिस', 45: 'पैंतालीस', 46: 'चियालीस', 47: 'सैंतालिस', 48: 'अड़तालीस', 49: 'उनचास',
        50: 'पचास', 51: 'इक्यावन', 52: 'बावन', 53: 'तिरेपन', 54: 'चौबन', 55: 'पचपन', 56: 'छप्पन', 57: 'सत्तावन', 58: 'अट्ठावन', 59: 'उनसठ',
        60: 'साठ', 61: 'इकसठ', 62: 'बासठ', 63: 'तिरसठ', 64: 'चौंसठ', 65: 'पैंसठ', 66: 'छियासठ', 67: 'सड़सठ', 68: 'अड़सठ', 69: 'उनहत्तर',
        70: 'सत्तर', 71: 'इकहत्तर', 72: 'बहत्तर', 73: 'तिहत्तर', 74: 'चौहत्तर', 75: 'पचहत्तर', 76: 'छिहत्तर', 77: 'सत्तहत्तर', 78: 'अठहत्तर', 79: 'उनासी',
        80: 'अस्सी', 81: 'इक्यासी', 82: 'बयासी', 83: 'तिरासी', 84: 'चौरासी', 85: 'पचासी', 86: 'छियासी', 87: 'सत्तासी', 88: 'अट्ठासी', 89: 'नवासी',
        90: 'नब्बे', 91: 'इक्यानवे', 92: 'बानवे', 93: 'तिरानवे', 94: 'चौरानवे', 95: 'पचानवे', 96: 'छियानवे', 97: 'सत्तानवे', 98: 'अट्ठानवे', 99: 'निन्यानवे', 100: 'सौ'
    }

    MONTH_NAMES = {
        'en': { '01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May', '06': 'June', '07': 'July', '08': 'August', '09': 'September', '10': 'October', '11': 'November', '12': 'December' },
        'hi': { '01': 'जनवरी', '02': 'फरवरी', '03': 'मार्च', '04': 'अप्रैल', '05': 'मई', '06': 'जून', '07': 'जुलाई', '08': 'अगस्त', '09': 'सितंबर', '10': 'अक्टूबर', '11': 'नवंबर', '12': 'दिसंबर' }
    }

    TRANSITION_MESSAGES = {
        'en': { 'connecting': "One moment.", 'to_emi': "Just a second.", 'processing': "Okay." },
        'hi': { 'connecting': "एक पल।", 'to_emi': "एक सेकंड।", 'processing': "ठीक है।" }
    }

    OFFER_OPTIONS_PROMPT = {
        'en': "I am here to help you with your payment or answer any questions. Please tell me, how would you like to proceed?",
        'hi': "मैं आपकी पेमेंट या किसी भी सवाल में मदद करने के लिए यहाँ हूँ। बताइये, आप क्या करना चाहेंगे?"
    }
    
    NO_INPUT_PROMPTS = {
        'en': ["Hello? Are you still there?", "I couldn't hear you clearly. Could you please repeat?", "Sorry, I didn't get that."],
        'hi': ["हेलो? क्या आप लाइन पर हैं?", "माफ़ कीजिये, आवाज़ नहीं आयी। क्या आप फिर से बोल सकते हैं?", "सॉरी, मुझे सुनाई नहीं दिया।"]
    }

    VERIFICATION_SCRIPTS = {
        'en': ["Hello. This is a call from {bank_name}. Am I speaking with {customer_name}?", "Hi. Calling from {bank_name}. Is this {customer_name}?", "Good {time_of_day}. This is {bank_name}. Are you {customer_name}?"],
        'hi': ["नमस्ते। मैं {bank_name} से बोल रही हूं। क्या मैं {customer_name} जी से बात कर रही हूं?", "नमस्ते। {bank_name} से कॉल है। क्या आप {customer_name} जी हैं?", "नमस्ते। यह {bank_name} की ओर से कॉल है। क्या यह {customer_name} जी हैं?"]
    }
    
    VERIFICATION_RESPONSES = {
        'en': { 'CONFIRMED_IDENTITY': ["Great. Thank you.", "Perfect. Thanks.", "Thank you, {customer_name}."], 'DENIED_IDENTITY': ["Apologies. We will update our records, Goodbye.", "Sorry for the inconvenience. Thank you."], 'NOT_INTERESTED': ["I understand. I'll note that. Have a good day.", "No problem. Updating preferences. Goodbye."], 'CONFUSION': ["Calling from {bank_name} for {customer_name}. Are they available?", "This is for {customer_name} regarding their account."], 'UNCLEAR': ["Sorry, is this {customer_name}?", "Could you confirm if this is {customer_name}?"], 'ASK_WHO_ARE_YOU': ["Calling from {bank_name} collections. Are you {customer_name}?", "Routine call from {bank_name}. Are you {customer_name}?"], 'ASK_SOURCE_OF_INFO': ["Calling the registered number for your loan. Are you {customer_name}?", "Number listed in {bank_name} records. Is this {customer_name}?"] },
        'hi': { 'CONFIRMED_IDENTITY': ["धन्यवाद।", "जी शुक्रिया।", "धन्यवाद {customer_name} जी।"], 'DENIED_IDENTITY': ["माफ़ी चाहती हूँ। रिकॉर्ड अपडेट कर देंगे। नमस्ते।", "क्षमा करें। धन्यवाद।"], 'NOT_INTERESTED': ["समझ गई। नोट कर लिया है। नमस्ते।", "कोई बात नहीं। ठीक है। नमस्ते।"], 'CONFUSION': ["{bank_name} से {customer_name} जी के लिए कॉल है। क्या वो हैं?", "यह {customer_name} जी के लिए कॉल है।"], 'UNCLEAR': ["माफ़ कीजिये, क्या यह {customer_name} जी हैं?", "क्या आप {customer_name} जी बोल रहे हैं?"], 'ASK_WHO_ARE_YOU': ["{bank_name} से बोल रही हूँ। क्या आप {customer_name} जी हैं?", "{bank_name} की ज़रूरी कॉल है। क्या आप {customer_name} जी हैं?"], 'ASK_SOURCE_OF_INFO': ["बैंक में यह नंबर रजिस्टर्ड है। क्या आप {customer_name} जी हैं?", "यह जानकारी बैंक से मिली है। क्या मैं {customer_name} जी से बात कर रही हूँ?"] }
    }
    
    EMI_SCRIPTS = {
        'en': { 'current': "Regarding your {loan_type}. There is a pending installment of rupees {amount}, due on {due_date_spoken}. How would you like to make this payment?", 'overdue': "Regarding your {loan_type}. A payment of rupees {amount} is overdue since {due_date_spoken}. We need to clear this. When can you pay?" },
        'hi': { 'current': "आपके {loan_type} के बारे में। {amount} रुपये की किश्त {due_date_spoken} को देनी है। आप यह पेमेंट कैसे करेंगे?", 'overdue': "आपके {loan_type} के लिए। {amount} रुपये {due_date_spoken} से बाकी हैं। इसे क्लियर करना ज़रूरी है। आप कब तक जमा करेंगे?" }
    }
    
    CONVERSATION_RESPONSES = {
        'en': { 
            # --- PHASE 2 SCENARIOS (BUSY/SAFETY/TIME) ---
            'DRIVING_SAFETY': ["I understand you are driving. Safety is first. I will call you back later. Please drive safe.", "Oh, please focus on the road. I'll call another time. Drive safe."],
            'BUSY_CALLBACK_LATER': ["No problem. I've noted to call you back at {callback_time}. Have a good day.", "Understood. I will call you at {callback_time}. Thank you."],
            
            # --- PHASE 5 SCENARIOS (CHANNEL/BOT) ---
            'IS_BOT': ["I am a virtual assistant from {bank_name}, here to help you with your account.", "I'm an automated assistant calling on behalf of {bank_name}."],
            'SEND_WHATSAPP': ["Sure. I will send the details on WhatsApp immediately.", "Okay, sending the payment link via WhatsApp now."],
            'WRONG_NUMBER': ["I apologize. I will update our records. Sorry for the disturbance.", "My mistake. We will remove this number. Goodbye."],
            
            # --- EXISTING SCENARIOS ---
            'WILL_PAY_NOW': ["Excellent. Thank you {customer_name}. I'll send a payment link to your registered number right away... Is there anything else I can assist you with?", "Great choice. I am triggering a payment link to your mobile now. Once paid, you will receive a confirmation SMS."], 
            'WILL_PAY_LATER': ["Understood {customer_name}. I have updated the system with this new date.", "Okay. I have noted that you will pay on {commitment_date}. Please ensure the payment is made by then to avoid charges."], 
            'ALREADY_PAID': ["Thank you for letting me know {customer_name}. I will ask our team to verify this transaction... Is there any other query I can resolve for you?"], 
            'FACING_FINANCIAL_ISSUES': ["I'm really sorry to hear about your situation {customer_name}. I completely understand this is difficult... We can arrange a payment plan with smaller installments or provide an extension... Which option would work better for you?"], 
            'DISPUTE_AMOUNT': ["I understand your concern about the amount {customer_name}. Let me clarify the details... Your {loan_type} has an EMI of rupees {amount}... due on {due_date_spoken}. If this seems incorrect, I can connect you with our accounts team to review it... Would that help?"], 
            'REQUEST_EXTENSION': ["Absolutely {customer_name}. I can help with that... Based on your request, I'm noting an extension till {commitment_date}... You'll receive a confirmation message shortly... Is there anything else I can assist you with?"], 
            'REQUEST_PAYMENT_PLAN': ["Of course {customer_name}. We can definitely set up a payment plan for you... Would you prefer to split this into two installments or three smaller payments? I'll arrange whichever works best for your situation... Let me know your preference."], 
            'DEMANDS_SUPERVISOR': ["I completely understand {customer_name}. Let me transfer you to a specialist right away... Please hold for just a moment."], 
            'POLITE_EXIT': ["Thank you so much for your time {customer_name}. We'll send you all the payment details on your registered number shortly... Have a wonderful day. Goodbye!", "Thank you for speaking with {bank_name}. Have a great day."], 
            'UNCLEAR': ["I'm sorry, I didn't quite catch that... Could you please repeat? You can say things like 'I'll pay now', 'need more time', or 'speak to manager'... What would you like to do?"], 
            'CANT_PAY_REFUSAL': ["I understand this is difficult, but non-payment can seriously affect your credit score. I strongly suggest making even a small partial payment to keep your account active.", "I urge you to reconsider. Pending dues can lead to penalties. Can we arrange a small token payment today?"], 
            'ASK_AMOUNT': ["The current outstanding balance is rupees {amount}. Would you like to clear this today?", "You have a pending amount of rupees {amount}. Shall I send the payment link?"], 
            'ASK_DETAILS': ["I am calling regarding your {loan_type}. The pending amount is rupees {amount}, which was due on {due_date_spoken}. Would you like to make the payment now?", "Sure. This is regarding your {loan_type}. You have an overdue EMI of rupees {amount}. How would you like to proceed?"], 
            'ASK_SOURCE_OF_INFO': ["I am calling on behalf of {bank_name}. Your contact details are listed in the bank's records for this {loan_type} account.", "These details are from {bank_name}'s official records."], 
            'ASK_WHO_ARE_YOU': ["My name is Aditi, and I am calling from the authorized collections department of {bank_name}. This call is being recorded for quality purposes.", "I am a virtual assistant calling on behalf of {bank_name} regarding your loan account maintenance."], 
            'REPEAT_DETAILS': ["Certainly. Let me repeat that. The total pending amount is {amount} rupees, which was due on {due_date_spoken}.", "I can say that again. You have an outstanding EMI of {amount} rupees for your {loan_type}."], 
            'ASK_PAYMENT_DATE': ["When do you think you can make the payment?", "Could you please confirm a date for the payment?"] 
        },
        'hi': { 
            # --- PHASE 2 SCENARIOS (BUSY/SAFETY/TIME) ---
            'DRIVING_SAFETY': ["मैं समझती हूँ। आप ड्राइव कर रहे हैं। सेफ्टी ज़रूरी है। मैं बाद में कॉल करूँगी। ध्यान रखें।", "प्लीज़ रोड पर ध्यान दें। मैं बाद में कॉल करती हूँ।"],
            'BUSY_CALLBACK_LATER': ["कोई बात नहीं। मैंने {callback_time} पर कॉल करने का नोट कर लिया है। नमस्ते।", "ठीक है। मैं {callback_time} पर कॉल करूँगी। धन्यवाद।"],
            
            # --- PHASE 5 SCENARIOS (CHANNEL/BOT) ---
            'IS_BOT': ["मैं {bank_name} से एक वर्चुअल असिस्टेंट हूँ।", "मैं बैंक की तरफ से एक ऑटोमेटेड कॉल हूँ।"],
            'SEND_WHATSAPP': ["ज़रूर। मैं आपको अभी व्हाट्सएप पर डिटेल भेज रही हूँ।", "ठीक है, व्हाट्सएप चेक करें।"],
            'WRONG_NUMBER': ["माफ़ी चाहती हूँ। मैं यह नंबर हमारे रिकॉर्ड से हटा दूंगी। असुविधा के लिए खेद है।", "गलती के लिए माफ़ी। हम रिकॉर्ड अपडेट कर देंगे।"],

            # --- EXISTING SCENARIOS ---
            'WILL_PAY_NOW': ["बहुत अच्छा। धन्यवाद {customer_name} जी। मैं आपके रजिस्टर्ड नंबर पर अभी पेमेंट लिंक भेज देती हूं... क्या मैं आपकी किसी और बात में मदद कर सकती हूं?", "धन्यवाद। मैंने एसएमएस के जरिए लिंक भेज दिया है। कृपया अपना इनबॉक्स चेक करें।"], 
            'WILL_PAY_LATER': ["ठीक है {customer_name} जी। {commitment_date} नोट कर लिया है। कृपया तब तक भुगतान सुनिश्चित करें।", "समझ गई। मैंने सिस्टम में अपडेट कर दिया है कि आप {commitment_date} को भुगतान करेंगे।"], 
            'ALREADY_PAID': ["मुझे बताने के लिए धन्यवाद {customer_name} जी। मैं हमारी टीम से इस ट्रांजेक्शन को वेरिफाई करने के लिए कहूंगी... क्या आपके पास कोई और सवाल है?"], 
            'FACING_FINANCIAL_ISSUES': ["मुझे आपकी स्थिति के बारे में सुनकर बहुत दुख हुआ {customer_name} जी। मैं पूरी तरह समझती हूं कि यह मुश्किल है... हम छोटी किस्तों के साथ एक पेमेंट प्लान बना सकते हैं या एक्सटेंशन दे सकते हैं... कौन सा विकल्प आपके लिए बेहतर होगा?"], 
            'DISPUTE_AMOUNT': ["मैं राशि के बारे में आपकी चिंता समझती हूं {customer_name} जी। मुझे विवरण स्पष्ट करने दें... आपके {loan_type} की ईएमआई {amount} रुपये... {due_date_spoken} को देय है। अगर यह गलत लगता है, तो मैं आपको हमारी अकाउंट्स टीम से जोड़ सकती हूं... क्या इससे मदद मिलेगी?"], 
            'REQUEST_EXTENSION': ["बिल्कुल {customer_name} जी। मैं इसमें मदद कर सकती हूं... आपके अनुरोध के आधार पर, मैं {commitment_date} तक का एक्सटेंशन नोट कर रही हूं... आपको जल्द ही कन्फर्मेशन मैसेज मिल जाएगा... क्या कुछ और है जिसमें मैं आपकी मदद कर सकती हूं?"], 
            'REQUEST_PAYMENT_PLAN': ["बिल्कुल {customer_name} जी। हम निश्चित रूप से आपके लिए एक पेमेंट प्लान बना सकते हैं... क्या आप इसे दो किस्तों में या तीन छोटे भुगतानों में बांटना पसंद करेंगे? मैं जो भी आपकी स्थिति के लिए सबसे अच्छा हो वह व्यवस्था कर दूंगी... मुझे अपनी पसंद बताएं।"], 
            'DEMANDS_SUPERVISOR': ["मैं पूरी तरह समझती हूं {customer_name} जी। मैं आपको अभी एक स्पेशलिस्ट से जोड़ देती हूं... कृपया एक पल रुकें... वे आपकी बेहतर मदद कर पाएंगे।"], 
            'POLITE_EXIT': ["आपके समय के लिए बहुत-बहुत धन्यवाद {customer_name} जी। हम आपको आपके रजिस्टर्ड नंबर पर जल्द ही सभी पेमेंट डिटेल भेज देंगे... आपका दिन शुभ हो। नमस्ते!", "{bank_name} से बात करने के लिए धन्यवाद। आपका दिन शुभ हो।"], 
            'UNCLEAR': ["क्षमा करें, मुझे ठीक से समझ नहीं आया... क्या आप कृपया दोहरा सकते हैं? आप कह सकते हैं 'अभी भरूंगा', 'और समय चाहिए', या 'मैनेजर से बात'... आप क्या करना चाहेंगे?"], 
            'CANT_PAY_REFUSAL': ["मैं समझती हूँ, लेकिन भुगतान न करने से आपका क्रेडिट स्कोर खराब हो सकता है। मेरी सलाह है कि आप कम से कम कुछ राशि जमा कर दें ताकि अकाउंट एक्टिव रहे।", "पेमेंट पेंडिंग रखने से पेनल्टी लग सकती है। क्या हम आज एक छोटा पेमेंट कर सकते हैं?"], 
            'ASK_AMOUNT': ["बकाया राशि {amount} रुपये है। क्या आप इसे आज जमा कर सकते हैं?", "आपका पेंडिंग अमाउंट {amount} रुपये है। क्या मैं पेमेंट लिंक भेज दूं?"], 
            'ASK_DETAILS': ["मैं {bank_name} से आपके {loan_type} के बारे में बात कर रही हूं। {amount} रुपये की राशि {due_date_spoken} को देय थी। क्या आप अभी भुगतान करना चाहेंगे?", "यह आपके {loan_type} के बारे में है। {due_date_spoken} को {amount} रुपये भरने थे। आप यह पेमेंट कब तक करेंगे?"], 
            'ASK_SOURCE_OF_INFO': ["मैं {bank_name} की ओर से कॉल कर रही हूं। आपका नंबर बैंक के रिकॉर्ड में इस {loan_type} अकाउंट के लिए दर्ज है।", "यह जानकारी {bank_name} के आधिकारिक रिकॉर्ड से है।"], 
            'ASK_WHO_ARE_YOU': ["मैं {bank_name} कलेक्शन डिपार्टमेंट से अदिति बोल रही हूँ। यह कॉल क्वालिटी के लिए रिकॉर्ड की जा रही है।", "मैं {bank_name} की तरफ से लोन रिमाइंडर के लिए कॉल कर रही हूँ।"], 
            'REPEAT_DETAILS': ["जी। मैं फिर से बता देती हूँ। आपके {loan_type} का कुल {amount} रुपये बकाया है, जो {due_date_spoken} को ड्यू था।", "बिल्कुल। आपको {amount} रुपये भरने हैं।"], 
            'ASK_PAYMENT_DATE': ["ठीक है, आप यह पेमेंट कब तक कर सकते हैं?", "समझ गई। क्या आप मुझे भुगतान की तारीख बता सकते हैं?"] 
        }
    }
    
    @staticmethod
    def _convert_number_to_hindi(n):
        """Robust native conversion of numbers to Hindi text"""
        try:
            n = int(n)
            if n in MultilingualScriptTemplates.HINDI_NUMS_0_100:
                return MultilingualScriptTemplates.HINDI_NUMS_0_100[n]
            
            if n < 1000:
                hundreds = n // 100
                remainder = n % 100
                text = f"{MultilingualScriptTemplates.HINDI_NUMS_0_100[hundreds]} सौ"
                if remainder > 0:
                    text += f" {MultilingualScriptTemplates.HINDI_NUMS_0_100[remainder]}"
                return text
            
            if n < 100000:
                thousands = n // 1000
                remainder = n % 1000
                text = f"{MultilingualScriptTemplates._convert_number_to_hindi(thousands)} हज़ार"
                if remainder > 0:
                    text += f" {MultilingualScriptTemplates._convert_number_to_hindi(remainder)}"
                return text
                
            if n < 10000000:
                lakhs = n // 100000
                remainder = n % 100000
                text = f"{MultilingualScriptTemplates._convert_number_to_hindi(lakhs)} लाख"
                if remainder > 0:
                    text += f" {MultilingualScriptTemplates._convert_number_to_hindi(remainder)}"
                return text
                
            return str(n)
        except:
            return str(n)

    @staticmethod
    def format_date_for_speech(date_str, language='en'):
        try:
            parts = date_str.split('-')
            year = int(parts[0])
            month = parts[1]
            day = int(parts[2])
            
            month_name = MultilingualScriptTemplates.MONTH_NAMES[language].get(month, month)
            
            if language == 'en':
                if day in [1, 21, 31]: day_suffix = 'st'
                elif day in [2, 22]: day_suffix = 'nd'
                elif day in [3, 23]: day_suffix = 'rd'
                else: day_suffix = 'th'
                return f"{day}{day_suffix} {month_name} {year}"
            else:
                day_text = MultilingualScriptTemplates._convert_number_to_hindi(day)
                year_text = MultilingualScriptTemplates._convert_number_to_hindi(year)
                return f"{day_text} {month_name} {year_text}"
        except:
            return date_str
    
    @staticmethod
    def get_time_of_day():
        hour = datetime.now().hour
        if hour < 12: return "morning"
        elif hour < 17: return "afternoon"
        else: return "evening"
    
    @staticmethod
    def format_amount(amount, language='en'):
        try:
            if isinstance(amount, str):
                amount = amount.replace(',', '').replace(' ', '')
            amount_val = int(float(amount))
            
            if language == 'hi':
                return MultilingualScriptTemplates._convert_number_to_hindi(amount_val)
            
            amount_str = str(amount_val)
            if len(amount_str) <= 3: return amount_str
            formatted = ""
            for i, digit in enumerate(reversed(amount_str)):
                if i == 3 or (i > 3 and (i - 3) % 2 == 0):
                    formatted = "," + formatted
                formatted = digit + formatted
            return formatted.lstrip(",")
            
        except Exception as e:
            print(f"[ERROR] format_amount failed: {e}")
            return str(amount)
    
    @staticmethod
    def get_script(script_type, language, **kwargs):
        if script_type == 'verification':
            return MultilingualScriptTemplates.get_verification_script(language, kwargs.get('bank_name'), kwargs.get('customer_name'), kwargs.get('variation', 0))
        elif script_type == 'verification_response':
            return MultilingualScriptTemplates.get_verification_response(language, kwargs.get('intent'), kwargs.get('bank_name'), kwargs.get('customer_name'), kwargs.get('variation', 0))
        elif script_type == 'emi':
            return MultilingualScriptTemplates.get_emi_script(language, kwargs.get('customer_data'))
        elif script_type == 'conversation':
            return MultilingualScriptTemplates.get_conversation_response(language, kwargs.get('intent'), kwargs.get('customer_data'), kwargs.get('context'), kwargs.get('variation', 0))
        elif script_type == 'offer_options':
            return MultilingualScriptTemplates.OFFER_OPTIONS_PROMPT.get(language, MultilingualScriptTemplates.OFFER_OPTIONS_PROMPT['en'])
        elif script_type == 'no_input':
            prompts = MultilingualScriptTemplates.NO_INPUT_PROMPTS.get(language, MultilingualScriptTemplates.NO_INPUT_PROMPTS['en'])
            return prompts[kwargs.get('variation', 0) % len(prompts)]
        elif script_type == 'transition':
            msg_type = kwargs.get('message_type', 'connecting')
            return MultilingualScriptTemplates.TRANSITION_MESSAGES[language].get(msg_type, MultilingualScriptTemplates.TRANSITION_MESSAGES['en'][msg_type])
        return "Thank you."
    
    @staticmethod
    def get_verification_script(language, bank_name, customer_name, variation=0):
        scripts = MultilingualScriptTemplates.VERIFICATION_SCRIPTS[language]
        template = scripts[variation % len(scripts)]
        time_of_day = MultilingualScriptTemplates.get_time_of_day()
        return template.format(bank_name=bank_name, customer_name=customer_name, time_of_day=time_of_day)
    
    @staticmethod
    def get_verification_response(language, intent, bank_name, customer_name, variation=0):
        responses = MultilingualScriptTemplates.VERIFICATION_RESPONSES[language].get(intent, ['Thank you.'])
        template = responses[variation % len(responses)]
        return template.format(bank_name=bank_name, customer_name=customer_name)
    
    @staticmethod
    def get_emi_script(language, customer_data):
        amount = MultilingualScriptTemplates.format_amount(customer_data['bank_details']['pending_emi_amount'], language)
        due_date = customer_data['bank_details']['due_date']
        due_date_spoken = MultilingualScriptTemplates.format_date_for_speech(due_date, language)
        loan_type = customer_data['bank_details']['loan_type']
        
        from datetime import datetime
        due = datetime.strptime(due_date, "%Y-%m-%d")
        is_overdue = due < datetime.now()
        
        scripts = MultilingualScriptTemplates.EMI_SCRIPTS[language]
        template = scripts['overdue'] if is_overdue else scripts['current']
        
        return template.format(loan_type=loan_type, amount=amount, due_date_spoken=due_date_spoken)
    
    @staticmethod
    def get_conversation_response(language, intent, customer_data, context=None, variation=0):
        if not intent: intent = 'UNCLEAR'
        if intent not in MultilingualScriptTemplates.CONVERSATION_RESPONSES[language]: intent = 'UNCLEAR'
        responses = MultilingualScriptTemplates.CONVERSATION_RESPONSES[language].get(intent, ['Thank you for your response.'])
        template = responses[variation % len(responses)]
        
        due_date_spoken = MultilingualScriptTemplates.format_date_for_speech(customer_data['bank_details']['due_date'], language)
        
        variables = {
            'bank_name': Config.BANK_NAME,
            'customer_name': customer_data.get('name'),
            'loan_type': customer_data['bank_details']['loan_type'],
            'amount': MultilingualScriptTemplates.format_amount(customer_data['bank_details']['pending_emi_amount'], language),
            'due_date_spoken': due_date_spoken,
            'extension_days': '15',
            'commitment_date': '',
            'num_days': '',
            'callback_time': 'later' # Default
        }
        
        if context:
            if 'commitment_date' in context: variables['commitment_date'] = context['commitment_date']
            if 'num_days' in context: variables['num_days'] = context['num_days']
            if 'callback_time' in context: variables['callback_time'] = context['callback_time']
        
        if intent == 'WILL_PAY_LATER' and not variables.get('num_days'):
             if language == 'en': return "Perfect {customer_name}. I've noted that you'll make the payment soon. Is there anything else I can help you with?".format(**variables)
             else: return "बिल्कुल ठीक {customer_name} जी। मैंने नोट कर लिया है कि आप जल्द ही भुगतान कर देंगे। क्या कुछ और है जिसमें मैं आपकी मदद कर सकती हूं?".format(**variables)

        try: return template.format(**variables)
        except KeyError: return template