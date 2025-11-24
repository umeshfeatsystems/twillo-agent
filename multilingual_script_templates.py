"""
Multi-lingual Script Templates with Dynamic Context Handling
Production-Ready Version 2.7
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
            'connecting': "Hello. Thank you for connecting... Please hold one moment.",
            'to_emi': "One moment while I pull up your account details...",
            'processing': "Please hold while I process that..."
        },
        'hi': {
            'connecting': "नमस्ते। कनेक्ट करने के लिए धन्यवाद... कृपया एक पल रुकें।",
            'to_emi': "एक मोमेंट रुकें... जब तक मैं आपके अकाउंट का डिटेल निकालती हूं...",
            'processing': "कृपया रुकें... जब तक मैं इसे प्रोसेस करती हूं..."
        }
    }

    OFFER_OPTIONS_PROMPT = {
        'en': (
            "I'm sorry, I'm not sure I understand... "
            "To make this easier, you can simply say 'make a payment', 'request help', or 'speak to an agent'... "
            "What would you like to do?"
        ),
        'hi': (
            "क्षमा करें, मुझे पूरी तरह समझ नहीं आया... "
            "इसे आसान बनाने के लिए, आप बस 'पेमेंट करें', 'मदद चाहिए', या 'एजेंट से बात' कह सकते हैं... "
            "आप क्या करना चाहेंगे?"
        )
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
                "I understand. However, this is an important call regarding your loan. I will note your preference, but please check your banking app.",
                "No problem. I will update the system. Please ensure your dues are cleared to avoid penalties. Goodbye."
            ],
            'CONFUSION': [
                "This is a call from {bank_name} regarding {customer_name}'s loan account... Is he or she available to speak?",
                "I'm calling from {bank_name} for {customer_name}... May I speak with them, please?"
            ],
            'UNCLEAR': [
                "I'm sorry, I didn't quite catch that... Is this {customer_name} speaking?",
                "Pardon me... could you please confirm if this is {customer_name}?"
            ],
            'ASK_WHO_ARE_YOU': [
                "I am calling from {bank_name} regarding your loan account. Am I speaking with {customer_name}?",
                "This is an automated call from {bank_name} collections. Can you confirm if this is {customer_name}?"
            ],
            'ASK_SOURCE_OF_INFO': [
                "We have this number listed in our bank records for your loan account. Is this {customer_name}?",
                "This number is registered with {bank_name}. Could you please confirm if you are {customer_name}?"
            ],
            'ASK_DETAILS': [
                "I can provide all details once you confirm your identity. Are you {customer_name}?",
                "This is regarding your loan account. Please confirm if I am speaking with {customer_name}?"
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
                "मैं समझती हूं। लेकिन यह आपके लोन के बारे में एक जरूरी कॉल है। कृपया अपना बैंकिंग ऐप चेक करें।",
                "कोई बात नहीं। मैं सिस्टम अपडेट कर देती हूं। कृपया पेनल्टी से बचने के लिए अपनी ड्यूज़ क्लियर रखें। नमस्ते।"
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
                "मैं {bank_name} से आपके लोन अकाउंट के बारे में कॉल कर रही हूं। क्या मैं {customer_name} जी से बात कर रही हूं?",
                "यह {bank_name} से एक जरूरी कॉल है। क्या आप {customer_name} जी बोल रहे हैं?"
            ],
            'ASK_SOURCE_OF_INFO': [
                "यह नंबर हमारे बैंक रिकॉर्ड में आपके लोन अकाउंट के साथ रजिस्टर्ड है। क्या आप {customer_name} जी हैं?",
                "हमें यह जानकारी {bank_name} के डेटाबेस से मिली है। क्या मैं {customer_name} जी से बात कर सकती हूं?"
            ],
            'ASK_DETAILS': [
                "मैं आपको सारी जानकारी दे सकती हूं, बस आप अपनी पहचान कन्फर्म कर दें। क्या आप {customer_name} जी हैं?",
                "यह आपके लोन के बारे में है। कृपया पुष्टि करें कि क्या आप {customer_name} जी हैं?"
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
                "हमारे रिकॉर्ड के अनुसार {amount} रुपये की राशि... {due_date_spoken} को देय थी... जो अभी पेंडिंग है। "
                "मैं इसे हल करने में आपकी मदद करना चाहती हूं... आप इसे कैसे आगे बढ़ाना चाहेंगे?"
            ),
            'overdue': (
                "मैं आपके {loan_type} के बारे में बात करने के लिए कॉल कर रही हूं। "
                "{amount} रुपये का भुगतान... {due_date_spoken} से ओवरड्यू है। "
                "मैं समझती हूं कि कभी-कभी व्यस्तता हो जाती है... इसलिए मैं मदद के लिए यहां हूं... आप इस भुगतान को कैसे करना चाहेंगे?"
            )
        }
    }

    CONVERSATION_RESPONSES = {
        'en': {
            'WILL_PAY_NOW': [
                "Excellent. Thank you {customer_name}. I'll send a secure payment link to your registered number right away. Please complete it within 30 minutes to avoid late charges.",
                "Great choice. I am triggering a payment link to your mobile now. Once paid, you will receive a confirmation SMS."
            ],
            'WILL_PAY_LATER': [
                "Understood. {num_days} days from now is {commitment_date}. I have updated the system. Is there anything else I can help you with?",
                "Okay. I have noted your promise to pay on {commitment_date}. Please ensure it is cleared by then. Do you have any other questions?"
            ],
            'ALREADY_PAID': [
                "Thank you for letting me know. Sometimes it takes 24 hours to update. Do you happen to have the transaction ID or reference number handy?",
                "I see. I will flag this for verification with our accounts team immediately. If the payment reflects, you can ignore any further reminders."
            ],
            'FACING_FINANCIAL_ISSUES': [
                "I'm really sorry to hear about your situation, {customer_name}. We value you as a customer. I can check if you are eligible for a short extension or a restructuring plan. Would you like me to check that?",
                "I understand this is a difficult time. Instead of the full amount, would you be able to pay a partial amount today to keep the account active?"
            ],
            'DISPUTE_AMOUNT': [
                "I understand your concern regarding the amount. The system shows {amount} pending for the {loan_type}. Let me raise a dispute ticket for you so our backend team can re-calculate and call you back.",
                "Okay, if you believe the amount is incorrect, I can arrange a callback from the accounts manager to explain the calculation. Would that help?"
            ],
            'REQUEST_EXTENSION': [
                "I can help with that. Extending by {num_days} days sets your new date to {commitment_date}. I've noted this. Is there anything else I can assist you with?",
                "Based on your request, I've marked {commitment_date} as the payment date. Thank you. Do you need help with anything else?"
            ],
            'REQUEST_PAYMENT_PLAN': [
                "We can definitely look into a payment plan. Would you prefer to split the outstanding {amount} into two installments over the next 15 days?",
                "I can arrange for a split payment. How much would you be comfortable paying today to start the process?"
            ],
            'DEMANDS_SUPERVISOR': [
                "I understand you want to escalate this. My supervisor will have access to the same information, but I can certainly arrange a transfer. Please hold the line.",
                "I apologize if I haven't been able to resolve this. Let me connect you to a senior officer who can assist you further."
            ],
            'POLITE_EXIT': [
                "Thank you for your time, {customer_name}. We will await your payment. Have a wonderful day.",
                "Thanks for speaking with us. A summary of this call will be sent to your number. Goodbye!"
            ],
            'UNCLEAR': [
                "I'm sorry, I missed that. Could you please repeat? Are you planning to pay today or do you need more time?",
                "My apologies, the line is a bit unclear. Did you say you are ready to make the payment?"
            ],
            'CALL_LATER': [
                "I understand you are busy. I will schedule a callback. Would 5 PM today work for you, or do you prefer tomorrow morning?",
                "No problem. I will call you back later. Please keep your banking details handy next time."
            ],
            'PARTIAL_PAYMENT': [
                "While full payment is recommended to avoid charges, we can accept a partial payment of {amount} today. Shall I send the link for that?",
                "Okay, paying something is better than nothing. How much can you transfer right now?"
            ],
            'ASK_DETAILS': [
                 "This is regarding your {loan_type} ending in {account_last_4}. The due date was {due_date_spoken}. The total outstanding is rupees {amount}. When can we expect the payment?",
                 "I am calling to remind you about the {loan_type} EMI of rupees {amount}. It was due on {due_date_spoken}. Would you like to clear it now?"
            ],
            'ASK_WHO_ARE_YOU': [
                "I am calling from {bank_name} collections department regarding your pending EMI. Can we discuss the payment?",
                "This is a verified call from {bank_name}. I am reaching out to help you clear your outstanding dues."
            ],
            'ASK_SOURCE_OF_INFO': [
                "Your contact details are registered with {bank_name} as the primary contact for this loan account. We are simply following up on the pending amount.",
                "We are calling the number on file for your {loan_type} with {bank_name}. This is a standard follow-up for pending dues."
            ],
            'CONFIRMED_IDENTITY': [
                "Thank you for confirming. I am calling regarding your {loan_type}. You have a pending amount of {amount}. When can you make this payment?"
            ]
        },
        'hi': {
            'WILL_PAY_NOW': [
                "बहुत अच्छा। धन्यवाद {customer_name} जी। मैं आपके रजिस्टर्ड नंबर पर अभी पेमेंट लिंक भेज देती हूं। कृपया 30 मिनट के भीतर भुगतान पूरा करें ताकि कोई चार्ज न लगे।",
                "जी शुक्रिया। मैंने आपके मोबाइल पर लिंक भेज दिया है। पेमेंट होते ही आपको कन्फर्मेशन एसएमएस मिल जाएगा।"
            ],
            'WILL_PAY_LATER': [
                "ठीक है {customer_name} जी। {num_days} दिन बाद... यानी {commitment_date} तारीख होगी। मैंने सिस्टम में नोट कर लिया है। क्या कुछ और है जिसमें मैं आपकी मदद कर सकती हूं?",
                "समझ गई। {commitment_date} तक पेमेंट जरूर कर दें ताकि कोई चार्ज न लगे। क्या आपके पास कोई और सवाल है?"
            ],
            'ALREADY_PAID': [
                "जानकारी देने के लिए धन्यवाद। कभी-कभी अपडेट होने में 24 घंटे लगते हैं। क्या आपके पास ट्रांजेक्शन आईडी या रसीद नंबर है?",
                "जी, मैं इसे वेरिफिकेशन के लिए अकाउंट्स टीम को भेज देती हूं। अगर पेमेंट हो गया है, तो आपको और कॉल नहीं आएगा।"
            ],
            'FACING_FINANCIAL_ISSUES': [
                "मुझे आपकी स्थिति सुनकर दुख हुआ {customer_name} जी। मैं देख सकती हूं कि क्या हम आपको कुछ दिनों का एक्सटेंशन दे सकते हैं। क्या मैं चेक करूं?",
                "मैं समझती हूं कि अभी मुश्किल समय है। क्या पूरा अमाउंट भरने के बजाय, आप आज कुछ छोटा हिस्सा जमा कर सकते हैं ताकि अकाउंट एक्टिव रहे?"
            ],
            'DISPUTE_AMOUNT': [
                "मैं राशि को लेकर आपकी चिंता समझती हूं। सिस्टम में {loan_type} के लिए {amount} रुपये पेंडिंग दिख रहा है। मैं आपके लिए एक टिकट रेज़ (raise) कर देती हूं ताकि हमारी टीम इसे चेक कर सके।",
                "अगर आपको लगता है कि यह गलत है, तो मैं अकाउंट मैनेजर से आपको कॉल बैक करवा सकती हूं जो आपको कैलकुलेशन समझा देंगे।"
            ],
            'REQUEST_EXTENSION': [
                "मैं समझ सकती हूं। {num_days} दिन का एक्सटेंशन मिलने पर... आपकी नई तारीख {commitment_date} होगी। मैंने यह नोट कर लिया है। क्या आप कुछ और पूछना चाहेंगे?",
                "आपके कहने पर, मैंने पेमेंट की तारीख {commitment_date} तक बढ़ा दी है। कृपया तब तक इंतजाम कर लें। क्या मैं आपकी कोई और सहायता कर सकती हूं?"
            ],
            'REQUEST_PAYMENT_PLAN': [
                "हम पेमेंट प्लान बना सकते हैं। क्या आप इस {amount} को अगले 15 दिनों में दो किस्तों में बांटना चाहेंगे?",
                "मैं किस्तों की व्यवस्था कर सकती हूं। प्रोसेस शुरू करने के लिए आप आज कितना जमा कर सकते हैं?"
            ],
            'DEMANDS_SUPERVISOR': [
                "मैं समझती हूं कि आप सीनियर से बात करना चाहते हैं। मैं आपको अभी ट्रांसफर कर देती हूं, कृपया लाइन पर बने रहें।",
                "क्षमा करें अगर मैं आपकी पूरी मदद नहीं कर पाई। मैं आपको एक सीनियर ऑफिसर से कनेक्ट करती हूं।"
            ],
            'POLITE_EXIT': [
                "समय देने के लिए धन्यवाद {customer_name} जी। हम आपके भुगतान का इंतजार करेंगे। आपका दिन शुभ हो।",
                "हमसे बात करने के लिए शुक्रिया। कॉल की जानकारी आपको मैसेज में मिल जाएगी। नमस्ते।"
            ],
            'UNCLEAR': [
                "माफ़ कीजिये, आवाज कट रही है। क्या आप पेमेंट आज करेंगे या आपको और समय चाहिए?",
                "क्षमा करें, मुझे समझ नहीं आया। क्या आपने कहा कि आप पेमेंट करने के लिए तैयार हैं?"
            ],
            'CALL_LATER': [
                "मैं समझती हूं आप व्यस्त हैं। मैं बाद में कॉल कर लूंगी। क्या आज शाम 5 बजे कॉल करना ठीक रहेगा?",
                "कोई बात नहीं। मैं बाद में कॉल करती हूं। कृपया अगली बार अपनी बैंकिंग डिटेल्स तैयार रखें।"
            ],
            'PARTIAL_PAYMENT': [
                "हालांकि पूरा पेमेंट करना बेहतर होता है, लेकिन हम आज आंशिक भुगतान (partial payment) स्वीकार कर सकते हैं। क्या मैं लिंक भेज दूं?",
                "ठीक है, कुछ पेमेंट करना न करने से बेहतर है। आप अभी कितना जमा कर सकते हैं?"
            ],
            'ASK_DETAILS': [
                 "यह आपके {loan_type} के बारे में है। {due_date_spoken} को {amount} रुपये भरने थे। आप यह पेमेंट कब तक करेंगे?",
                 "मैं आपको {amount} रुपये की ईएमआई के बारे में याद दिलाने के लिए कॉल कर रही हूं। क्या आप इसे अभी क्लियर करना चाहेंगे?"
            ],
            'ASK_WHO_ARE_YOU': [
                "मैं {bank_name} कलेक्शन डिपार्टमेंट की ओर से कॉल कर रही हूं। हम आपकी पेंडिंग ईएमआई के बारे में बात कर रहे हैं।",
                "यह {bank_name} से एक ऑटोमेटेड कॉल है। हम बस आपके बकाया भुगतान के लिए फॉलो-अप कर रहे हैं।"
            ],
            'ASK_SOURCE_OF_INFO': [
                "आपका नंबर बैंक के पास आपके लोन अकाउंट के लिए प्राइमरी कॉन्टैक्ट के रूप में दर्ज है।",
                "यह जानकारी {bank_name} के सुरक्षित रिकॉर्ड से है। हम केवल रजिस्टर्ड ग्राहकों को कॉल करते हैं।"
            ],
            'ASK_AMOUNT': [
                "बकाया राशि {amount} रुपये है। क्या आप इसे आज जमा कर सकते हैं?",
                "आपका पेंडिंग अमाउंट {amount} रुपये है। क्या मैं पेमेंट लिंक भेज दूं?"
            ],
            'ASK_PAYMENT_DATE': [
                "ठीक है, आप यह पेमेंट कब तक कर सकते हैं?",
                "समझ गई। क्या आप मुझे भुगतान की तारीख बता सकते हैं?"
            ],
            'CONFIRMED_IDENTITY': [
                "पुष्टि करने के लिए धन्यवाद। मैं आपके {loan_type} के बारे में कॉल कर रही हूं। {amount} रुपये की राशि बकाया है। आप इसका भुगतान कब कर सकते हैं?"
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

        # Handle intents that might not be in the dictionary (safety check)
        if intent not in MultilingualScriptTemplates.CONVERSATION_RESPONSES[language]:
             # If we have a response for ASK_WHO_ARE_YOU but intent is just 'ASK_IDENTITY' map it
             intent = 'UNCLEAR'

        responses = MultilingualScriptTemplates.CONVERSATION_RESPONSES[language].get(
            intent, MultilingualScriptTemplates.CONVERSATION_RESPONSES[language]['UNCLEAR']
        )
        
        # Select variation
        template = responses[variation % len(responses)]
        
        # Helper variables
        due_date_spoken = MultilingualScriptTemplates.format_date_for_speech(
            customer_data['bank_details']['due_date'], language
        )
        
        # Safely get account last 4 digits
        acc_num = customer_data.get('bank_details', {}).get('account_number', '0000')
        account_last_4 = acc_num[-4:] if len(acc_num) >= 4 else acc_num

        variables = {
            'bank_name': Config.BANK_NAME,
            'customer_name': customer_data.get('name'),
            'loan_type': customer_data['bank_details']['loan_type'],
            'account_last_4': account_last_4,
            'amount': MultilingualScriptTemplates.format_amount(
                customer_data['bank_details']['pending_emi_amount'], language
            ),
            'due_date_spoken': due_date_spoken,
            'extension_days': '7',
            'commitment_date': 'soon',
            'num_days': 'few'
        }
        
        # Inject dynamic context if available
        if context:
            if 'commitment_date' in context and context['commitment_date']:
                variables['commitment_date'] = context['commitment_date']
            if 'num_days' in context and context['num_days']:
                variables['num_days'] = str(context['num_days'])
            if 'extension_days' in context:
                 variables['extension_days'] = str(context['extension_days'])

        # Fallback logic for missing slots in specific scenarios
        if intent in ['WILL_PAY_LATER', 'REQUEST_EXTENSION'] and variables['commitment_date'] == 'soon':
             if language == 'en':
                 return "Perfect {customer_name}. I've noted that you'll make the payment soon. Is there anything else I can help you with?".format(**variables)
             else:
                 return "बिल्कुल ठीक {customer_name} जी। मैंने नोट कर लिया है कि आप जल्द ही भुगतान कर देंगे। क्या कुछ और है जिसमें मैं आपकी मदद कर सकती हूं?".format(**variables)

        # Fallback for empty specific slots to avoid format errors
        try:
            return template.format(**variables)
        except KeyError:
            # If a variable is missing in specific template, return safe default or raw template
            return template