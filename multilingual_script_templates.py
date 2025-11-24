"""
Multi-lingual Script Templates with Dynamic Context Handling
Production-Ready Version 3.0 - Polite, Verbose & Comprehensive
"""
from config import Config
from datetime import datetime

class MultilingualScriptTemplates:
    
    MONTH_NAMES = {
        'en': {
            '01': 'January', '02': 'February', '03': 'March', '04': 'April',
            '05': 'May', '06': 'June', '07': 'July', '08': 'August',
            '09': 'September', '10': 'October', '11': 'November', '12': 'December'
        },
        'hi': {
            '01': 'जनवरी', '02': 'फरवरी', '03': 'मार्च', '04': 'अप्रैल',
            '05': 'मई', '06': 'जून', '07': 'जुलाई', '08': 'अगस्त',
            '09': 'सितंबर', '10': 'अक्टूबर', '11': 'नवंबर', '12': 'दिसंबर'
        }
    }

    TRANSITION_MESSAGES = {
        'en': {
            'connecting': "Connecting you now... please hold.",
            'to_emi': "One moment while I pull up your account details...",
            'processing': "Please hold while I process that..."
        },
        'hi': {
            'connecting': "कनेक्ट कर रही हूँ... कृपया लाइन पर बने रहें।",
            'to_emi': "एक मोमेंट रुकें... मैं आपके अकाउंट की डिटेल्स निकालती हूँ...",
            'processing': "कृपया रुकें... जब तक मैं इसे प्रोसेस करती हूँ..."
        }
    }

    OFFER_OPTIONS_PROMPT = {
        'en': (
            "I want to help you resolve this. You can simply say 'I will pay now', 'I need more time', or 'Connect me to an agent'. What would you like to do?"
        ),
        'hi': (
            "मैं आपकी मदद करना चाहती हूँ। आप कह सकते हैं 'मैं अभी पेमेंट करूँगा', 'मुझे समय चाहिए', या 'एजेंट से बात करवाओ'। आप क्या करना चाहेंगे?"
        )
    }
    
    # Critical for handling silence gracefully
    NO_INPUT_PROMPTS = {
        'en': [
            "Hello? Are you there?",
            "I couldn't hear you. Could you please repeat that?",
            "Sorry, I didn't get a response. Are you able to hear me?"
        ],
        'hi': [
            "हेलो? क्या आप मुझे सुन पा रहे हैं?",
            "माफ़ कीजिये, आपकी आवाज़ नहीं आयी। क्या आप दोहरा सकते हैं?",
            "हेलो? क्या आप लाइन पर हैं?"
        ]
    }

    VERIFICATION_SCRIPTS = {
        'en': [
            "Hello. This is a call from {bank_name}... Am I speaking with {customer_name}?",
            "Hi. I'm calling from {bank_name}... May I please speak with {customer_name}?",
            "Good {time_of_day}. This is {bank_name} calling... Is this {customer_name}?"
        ],
        'hi': [
            "नमस्ते। मैं {bank_name} से बोल रही हूं... क्या मैं {customer_name} जी से बात कर रही हूं?",
            "नमस्ते। मैं {bank_name} से कॉल कर रही हूं... क्या मैं {customer_name} जी से बात कर सकती हूं?",
            "नमस्ते। यह {bank_name} की ओर से कॉल है... क्या यह {customer_name} जी हैं?"
        ]
    }
    
    VERIFICATION_RESPONSES = {
        'en': {
            'CONFIRMED_IDENTITY': [
                "Great. Thank you.",
                "Perfect. Thank you for confirming.",
                "Thank you, {customer_name}."
            ],
            'DENIED_IDENTITY': [
                "I apologize for the disturbance. We will update our records... Have a good day.",
                "Sorry for the inconvenience. We'll correct this in our system... Thank you."
            ],
            'NOT_INTERESTED': [
                "I understand. I'll note that you do not wish to be contacted... However, please check your app for pending dues. Have a good day.",
                "No problem. I'll update your preferences right away... Goodbye."
            ],
            'CONFUSION': [
                "This is a call from {bank_name} regarding {customer_name}'s account... Is he or she available?",
                "I'm calling from {bank_name} for {customer_name}... May I speak with them, please?"
            ],
            'UNCLEAR': [
                "I'm sorry, I didn't quite catch that... Is this {customer_name} speaking?",
                "Pardon me... could you please confirm if this is {customer_name}?"
            ],
            # Added Inquiries during verification
            'ASK_WHO_ARE_YOU': [
                "I am calling from the collections department of {bank_name}. Can I confirm I am speaking with {customer_name}?",
                "This is a routine call from {bank_name} regarding your loan account. Are you {customer_name}?"
            ],
            'ASK_SOURCE_OF_INFO': [
                "We are calling the registered number for your loan account. Can you confirm if you are {customer_name}?",
                "This number is listed in {bank_name}'s records. Is this {customer_name}?"
            ]
        },
        'hi': {
            'CONFIRMED_IDENTITY': [
                "बहुत अच्छा। धन्यवाद।",
                "बिल्कुल ठीक। पुष्टि करने के लिए धन्यवाद।",
                "धन्यवाद {customer_name} जी।"
            ],
            'DENIED_IDENTITY': [
                "असुविधा के लिए खेद है। हम अपने रिकॉर्ड अपडेट कर देंगे... आपका दिन शुभ हो।",
                "क्षमा करें। हम इसे अपने सिस्टम में सही कर देंगे... धन्यवाद।"
            ],
            'NOT_INTERESTED': [
                "मैं समझती हूं। मैं नोट कर लूंगी कि आप संपर्क नहीं चाहते... आपका दिन शुभ हो।",
                "कोई बात नहीं। मैं आपकी प्राथमिकता अभी अपडेट कर देती हूं... नमस्ते।"
            ],
            'CONFUSION': [
                "यह {bank_name} की ओर से {customer_name} जी के अकाउंट के बारे में कॉल है... क्या वे उपलब्ध हैं?",
                "मैं {bank_name} से {customer_name} जी के लिए बोल रही हूं... क्या मैं उनसे बात कर सकती हूं?"
            ],
            'UNCLEAR': [
                "क्षमा करें, मुझे ठीक से समझ नहीं आया... क्या यह {customer_name} जी बोल रहे हैं?",
                "क्षमा करें... क्या आप पुष्टि कर सकते हैं कि यह {customer_name} जी हैं?"
            ],
            'ASK_WHO_ARE_YOU': [
                "मैं {bank_name} के कलेक्शन डिपार्टमेंट से बोल रही हूँ। क्या मैं {customer_name} जी से बात कर रही हूँ?",
                "यह {bank_name} की तरफ से एक ज़रूरी कॉल है। क्या आप {customer_name} जी हैं?"
            ],
            'ASK_SOURCE_OF_INFO': [
                "यह नंबर बैंक के रिकॉर्ड में आपके लोन अकाउंट के साथ रजिस्टर्ड है। क्या आप {customer_name} जी हैं?",
                "हमें यह जानकारी बैंक के डेटाबेस से मिली है। क्या मैं {customer_name} जी से बात कर रही हूँ?"
            ]
        }
    }
    
    EMI_SCRIPTS = {
        'en': {
            'current': (
                "I'm reaching out regarding your {loan_type}. "
                "Our records show a pending installment of rupees {amount}... which was due on {due_date_spoken}. "
                "I'd like to help resolve this... Could you tell me how you'd like to proceed?"
            ),
            'overdue': (
                "I'm reaching out about your {loan_type}. "
                "The payment of rupees {amount}... has been overdue since {due_date_spoken}. "
                "I understand things can get busy, so I'm here to help... How would you like to handle this payment?"
            )
        },
        'hi': {
            'current': (
                "मैं आपके {loan_type} के बारे में बात करने के लिए कॉल कर रही हूं। "
                "हमारे रिकॉर्ड के अनुसार {amount} रुपये की किस्त... {due_date_spoken} को देय थी... जो अभी बाकी है। "
                "मैं इसे हल करने में आपकी मदद करना चाहती हूं... आप इसे कैसे आगे बढ़ाना चाहेंगे?"
            ),
            'overdue': (
                "मैं आपके {loan_type} के बारे में बात करने के लिए कॉल कर रही हूं। "
                "{amount} रुपये का भुगतान... {due_date_spoken} से बाकी है। "
                "मैं समझती हूं कि कभी-कभी व्यस्तता हो जाती है... इसलिए मैं मदद के लिए यहां हूं... आप इस भुगतान को कैसे करना चाहेंगे?"
            )
        }
    }
    
    CONVERSATION_RESPONSES = {
        'en': {
            'WILL_PAY_NOW': [
                "Excellent. Thank you {customer_name}. I'll send a payment link to your registered number right away... Is there anything else I can assist you with?",
                "Great choice. I am triggering a payment link to your mobile now. Once paid, you will receive a confirmation SMS."
            ],
            'WILL_PAY_LATER': [
                "Understood {customer_name}. {num_days} days from now means {commitment_date}. I have updated the system with this new date.",
                "Okay. I have noted that you will pay on {commitment_date}. Please ensure the payment is made by then to avoid charges."
            ],
            'ALREADY_PAID': [
                "Thank you for letting me know {customer_name}. I will ask our team to verify this transaction... Is there any other query I can resolve for you?"
            ],
            'FACING_FINANCIAL_ISSUES': [
                "I'm really sorry to hear about your situation {customer_name}. I completely understand this is difficult... We can arrange a payment plan with smaller installments or provide an extension... Which option would work better for you?"
            ],
            'DISPUTE_AMOUNT': [
                "I understand your concern about the amount {customer_name}. Let me clarify the details... Your {loan_type} has an EMI of rupees {amount}... due on {due_date_spoken}... If this seems incorrect, I can connect you with our accounts team to review it... Would that help?"
            ],
            'REQUEST_EXTENSION': [
                "Absolutely {customer_name}. I can help with that... Based on your request, I'm noting an extension till {commitment_date}... That's {num_days} days from today... You'll receive a confirmation message shortly... Is there anything else I can assist you with?"
            ],
            'REQUEST_PAYMENT_PLAN': [
                "Of course {customer_name}. We can definitely set up a payment plan for you... Would you prefer to split this into two installments or three smaller payments? I'll arrange whichever works best for your situation... Let me know your preference."
            ],
            'DEMANDS_SUPERVISOR': [
                "I completely understand {customer_name}. Let me transfer you to a specialist right away... Please hold for just a moment."
            ],
            'POLITE_EXIT': [
                "Thank you so much for your time {customer_name}. We'll send you all the payment details on your registered number shortly... Have a wonderful day. Goodbye!",
                "Thank you for speaking with {bank_name}. Have a great day."
            ],
            'UNCLEAR': [
                "I'm sorry, I didn't quite catch that... Could you please repeat? You can say things like 'I'll pay now', 'need more time', or 'speak to manager'... What would you like to do?"
            ],
            # --- EXTENDED INTENTS FOR BETTER COVERAGE ---
            'ASK_AMOUNT': [
                "The current outstanding balance is rupees {amount}. Would you like to clear this today?",
                "You have a pending amount of rupees {amount} for your {loan_type}. Shall I send the payment link?"
            ],
            'ASK_DETAILS': [
                "I am calling from {bank_name} regarding your {loan_type}. The pending amount is rupees {amount}, which was due on {due_date_spoken}. Would you like to make the payment now?",
                "Sure. This is regarding your {loan_type} with {bank_name}. You have an overdue EMI of rupees {amount}. How would you like to proceed?"
            ],
            'ASK_SOURCE_OF_INFO': [
                "I am calling on behalf of {bank_name}. Your contact details are listed in the bank's records for this {loan_type} account. We are just following up on the pending payment.",
                "These details are from {bank_name}'s official records regarding your {loan_type}. I am just here to help you update the payment status."
            ],
            'ASK_WHO_ARE_YOU': [
                "My name is Aditi, and I am calling from the authorized collections department of {bank_name}. This call is being recorded for quality purposes.",
                "I am a virtual assistant calling on behalf of {bank_name} regarding your loan account maintenance."
            ],
            'REPEAT_DETAILS': [
                "Certainly. Let me repeat that. The total pending amount is {amount} rupees, which was due on {due_date_spoken}.",
                "I can say that again. You have an outstanding EMI of {amount} rupees for your {loan_type}."
            ],
            'ASK_PAYMENT_DATE': [
                "When do you think you can make the payment?",
                "Could you please confirm a date for the payment?"
            ]
        },
        'hi': {
            'WILL_PAY_NOW': [
                "बहुत अच्छा। धन्यवाद {customer_name} जी। मैं आपके रजिस्टर्ड नंबर पर अभी पेमेंट लिंक भेज देती हूं... क्या मैं आपकी किसी और बात में मदद कर सकती हूं?",
                "धन्यवाद। मैंने एसएमएस के जरिए लिंक भेज दिया है। कृपया अपना इनबॉक्स चेक करें।"
            ],
            'WILL_PAY_LATER': [
                "ठीक है {customer_name} जी। {num_days} दिन बाद... यानी {commitment_date}। मैंने आपकी पेंडिंग ईएमआई के लिए यह नई तारीख नोट कर ली है।",
                "समझ गई। {num_days} दिन बाद {commitment_date} तारीख होगी। मैंने सिस्टम में अपडेट कर दिया है कि आप तब भुगतान करेंगे।"
            ],
            'ALREADY_PAID': [
                "मुझे बताने के लिए धन्यवाद {customer_name} जी। मैं हमारी टीम से इस ट्रांजेक्शन को वेरिफाई करने के लिए कहूंगी... क्या आपके पास कोई और सवाल है?"
            ],
            'FACING_FINANCIAL_ISSUES': [
                "मुझे आपकी स्थिति के बारे में सुनकर बहुत दुख हुआ {customer_name} जी। मैं पूरी तरह समझती हूं कि यह मुश्किल है... हम छोटी किस्तों के साथ एक पेमेंट प्लान बना सकते हैं या एक्सटेंशन दे सकते हैं... कौन सा विकल्प आपके लिए बेहतर होगा?"
            ],
            'DISPUTE_AMOUNT': [
                "मैं राशि के बारे में आपकी चिंता समझती हूं {customer_name} जी। मुझे विवरण स्पष्ट करने दें... आपके {loan_type} की ईएमआई {amount} रुपये... {due_date_spoken} को देय है। अगर यह गलत लगता है, तो मैं आपको हमारी अकाउंट्स टीम से जोड़ सकती हूं... क्या इससे मदद मिलेगी?"
            ],
            'REQUEST_EXTENSION': [
                "बिल्कुल {customer_name} जी। मैं इसमें मदद कर सकती हूं... आपके अनुरोध के आधार पर, मैं {commitment_date} तक का एक्सटेंशन नोट कर रही हूं... यह आज से {num_days} दिन बाद है। आपको जल्द ही कन्फर्मेशन मैसेज मिल जाएगा... क्या कुछ और है जिसमें मैं आपकी मदद कर सकती हूं?"
            ],
            'REQUEST_PAYMENT_PLAN': [
                "बिल्कुल {customer_name} जी। हम निश्चित रूप से आपके लिए एक पेमेंट प्लान बना सकते हैं... क्या आप इसे दो किस्तों में या तीन छोटे भुगतानों में बांटना पसंद करेंगे? मैं जो भी आपकी स्थिति के लिए सबसे अच्छा हो वह व्यवस्था कर दूंगी... मुझे अपनी पसंद बताएं।"
            ],
            'DEMANDS_SUPERVISOR': [
                "मैं पूरी तरह समझती हूं {customer_name} जी। मैं आपको अभी एक स्पेशलिस्ट से जोड़ देती हूं... कृपया एक पल रुकें... वे आपकी बेहतर मदद कर पाएंगे।"
            ],
            'POLITE_EXIT': [
                "आपके समय के लिए बहुत-बहुत धन्यवाद {customer_name} जी। हम आपको आपके रजिस्टर्ड नंबर पर जल्द ही सभी पेमेंट डिटेल भेज देंगे... आपका दिन शुभ हो। नमस्ते!",
                "{bank_name} से बात करने के लिए धन्यवाद। आपका दिन शुभ हो।"
            ],
            'UNCLEAR': [
                "क्षमा करें, मुझे ठीक से समझ नहीं आया... क्या आप कृपया दोहरा सकते हैं? आप कह सकते हैं 'अभी भरूंगा', 'और समय चाहिए', या 'मैनेजर से बात'... आप क्या करना चाहेंगे?"
            ],
            # --- EXTENDED INTENTS (HINDI) ---
            'ASK_AMOUNT': [
                "बकाया राशि {amount} रुपये है। क्या आप इसे आज जमा कर सकते हैं?",
                "आपका पेंडिंग अमाउंट {amount} रुपये है। क्या मैं पेमेंट लिंक भेज दूं?"
            ],
            'ASK_DETAILS': [
                "मैं {bank_name} से आपके {loan_type} के बारे में बात कर रही हूं। {amount} रुपये की राशि {due_date_spoken} को देय थी। क्या आप अभी भुगतान करना चाहेंगे?",
                "यह आपके {loan_type} के बारे में है। {due_date_spoken} को {amount} रुपये भरने थे। आप यह पेमेंट कब तक करेंगे?"
            ],
            'ASK_SOURCE_OF_INFO': [
                "मैं {bank_name} की ओर से कॉल कर रही हूं। आपका नंबर बैंक के रिकॉर्ड में इस {loan_type} अकाउंट के लिए दर्ज है। हम बस पेंडिंग भुगतान के लिए फॉलो-अप कर रहे हैं।",
                "यह जानकारी {bank_name} के आधिकारिक रिकॉर्ड से है। मैं बस आपकी मदद करने के लिए कॉल कर रही हूं।"
            ],
            'ASK_WHO_ARE_YOU': [
                "मैं {bank_name} कलेक्शन डिपार्टमेंट से अदिति बोल रही हूँ। यह कॉल क्वालिटी के लिए रिकॉर्ड की जा रही है।",
                "मैं {bank_name} की तरफ से लोन रिमाइंडर के लिए कॉल कर रही हूँ।"
            ],
            'REPEAT_DETAILS': [
                "जी। मैं फिर से बता देती हूँ। आपके {loan_type} का कुल {amount} रुपये बकाया है, जो {due_date_spoken} को ड्यू था।",
                "बिल्कुल। आपको {amount} रुपये भरने हैं।"
            ],
            'ASK_PAYMENT_DATE': [
                "ठीक है, आप यह पेमेंट कब तक कर सकते हैं?",
                "समझ गई। क्या आप मुझे भुगतान की तारीख बता सकते हैं?"
            ]
        }
    }
    
    @staticmethod
    def format_date_for_speech(date_str, language='en'):
        try:
            parts = date_str.split('-')
            year = parts[0]
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
                return f"{day} {month_name} {year}"
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
        amount_str = str(int(amount))
        if language == 'hi': return amount_str
        if len(amount_str) <= 3: return amount_str
        formatted = ""
        for i, digit in enumerate(reversed(amount_str)):
            if i == 3 or (i > 3 and (i - 3) % 2 == 0):
                formatted = "," + formatted
            formatted = digit + formatted
        return formatted.lstrip(",")
    
    @staticmethod
    def get_script(script_type, language, **kwargs):
        if script_type == 'verification':
            return MultilingualScriptTemplates.get_verification_script(
                language, kwargs.get('bank_name'), kwargs.get('customer_name'), 
                kwargs.get('variation', 0)
            )
        elif script_type == 'verification_response':
            return MultilingualScriptTemplates.get_verification_response(
                language, kwargs.get('intent'), kwargs.get('bank_name'),
                kwargs.get('customer_name'), kwargs.get('variation', 0)
            )
        elif script_type == 'emi':
            return MultilingualScriptTemplates.get_emi_script(
                language, kwargs.get('customer_data')
            )
        elif script_type == 'conversation':
            return MultilingualScriptTemplates.get_conversation_response(
                language, kwargs.get('intent'), kwargs.get('customer_data'),
                kwargs.get('context'), kwargs.get('variation', 0)
            )
        elif script_type == 'offer_options':
            return MultilingualScriptTemplates.OFFER_OPTIONS_PROMPT.get(language, 
                MultilingualScriptTemplates.OFFER_OPTIONS_PROMPT['en'])
        elif script_type == 'no_input':
            prompts = MultilingualScriptTemplates.NO_INPUT_PROMPTS.get(language, 
                MultilingualScriptTemplates.NO_INPUT_PROMPTS['en'])
            return prompts[kwargs.get('variation', 0) % len(prompts)]
        elif script_type == 'transition':
            msg_type = kwargs.get('message_type', 'connecting')
            return MultilingualScriptTemplates.TRANSITION_MESSAGES[language].get(
                msg_type, MultilingualScriptTemplates.TRANSITION_MESSAGES['en'][msg_type]
            )
        return "Thank you."
    
    @staticmethod
    def get_verification_script(language, bank_name, customer_name, variation=0):
        scripts = MultilingualScriptTemplates.VERIFICATION_SCRIPTS[language]
        template = scripts[variation % len(scripts)]
        time_of_day = MultilingualScriptTemplates.get_time_of_day()
        return template.format(
            bank_name=bank_name,
            customer_name=customer_name,
            time_of_day=time_of_day
        )
    
    @staticmethod
    def get_verification_response(language, intent, bank_name, customer_name, variation=0):
        responses = MultilingualScriptTemplates.VERIFICATION_RESPONSES[language].get(
            intent, ['Thank you.']
        )
        template = responses[variation % len(responses)]
        return template.format(bank_name=bank_name, customer_name=customer_name)
    
    @staticmethod
    def get_emi_script(language, customer_data):
        amount = MultilingualScriptTemplates.format_amount(
            customer_data['bank_details']['pending_emi_amount'], language
        )
        due_date = customer_data['bank_details']['due_date']
        due_date_spoken = MultilingualScriptTemplates.format_date_for_speech(due_date, language)
        loan_type = customer_data['bank_details']['loan_type']
        
        from datetime import datetime
        due = datetime.strptime(due_date, "%Y-%m-%d")
        is_overdue = due < datetime.now()
        
        scripts = MultilingualScriptTemplates.EMI_SCRIPTS[language]
        template = scripts['overdue'] if is_overdue else scripts['current']
        
        return template.format(
            loan_type=loan_type, 
            amount=amount, 
            due_date_spoken=due_date_spoken
        )
    
    @staticmethod
    def get_conversation_response(language, intent, customer_data, context=None, variation=0):
        # Default intent fallback
        if not intent: intent = 'UNCLEAR'
        
        # Safe fallback if intent is missing in dictionary
        if intent not in MultilingualScriptTemplates.CONVERSATION_RESPONSES[language]:
            intent = 'UNCLEAR'
            
        responses = MultilingualScriptTemplates.CONVERSATION_RESPONSES[language].get(
            intent, ['Thank you for your response.']
        )
        template = responses[variation % len(responses)]
        
        due_date_spoken = MultilingualScriptTemplates.format_date_for_speech(
            customer_data['bank_details']['due_date'], language
        )
        
        # Prepare variables safely
        variables = {
            'bank_name': Config.BANK_NAME,
            'customer_name': customer_data.get('name'),
            'loan_type': customer_data['bank_details']['loan_type'],
            'amount': MultilingualScriptTemplates.format_amount(
                customer_data['bank_details']['pending_emi_amount'], language
            ),
            'due_date_spoken': due_date_spoken,
            'extension_days': '15',
            'commitment_date': '',
            'num_days': ''
        }
        
        # Inject dynamic context if available
        if context:
            if 'commitment_date' in context:
                variables['commitment_date'] = context['commitment_date']
            if 'num_days' in context:
                variables['num_days'] = context['num_days']
        
        # Fallback logic for WILL_PAY_LATER if date is not parsed
        if intent == 'WILL_PAY_LATER' and not variables.get('num_days'):
             if language == 'en':
                 return "Perfect {customer_name}. I've noted that you'll make the payment soon. Is there anything else I can help you with?".format(**variables)
             else:
                 return "बिल्कुल ठीक {customer_name} जी। मैंने नोट कर लिया है कि आप जल्द ही भुगतान कर देंगे। क्या कुछ और है जिसमें मैं आपकी मदद कर सकती हूं?".format(**variables)

        try:
            return template.format(**variables)
        except KeyError:
            return template