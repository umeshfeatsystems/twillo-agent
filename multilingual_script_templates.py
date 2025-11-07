"""
Multi-lingual Script Templates
Professional scripts in Hindi and English with proper gender forms
"""

class MultilingualScriptTemplates:
    """
    Bilingual script templates with professional translations.
    All Hindi scripts use FEMININE forms to match Polly.Aditi voice.
    """
    
    VERIFICATION_SCRIPTS = {
        'en': [
            "Hello, this is a call from {bank_name}. Am I speaking with {customer_name}?",
            "Hi, I'm calling from {bank_name}. May I please speak with {customer_name}?",
            "Good {time_of_day}, this is {bank_name} calling. Is this {customer_name}?"
        ],
        'hi': [
            "नमस्ते, यह {bank_name} की तरफ से कॉल है। क्या मैं {customer_name} जी से बात कर रही हूं?",
            "नमस्कार, मैं {bank_name} से बोल रही हूं। क्या मैं {customer_name} जी से बात कर सकती हूं?",
            "सुप्रभात, यह {bank_name} की तरफ से कॉल है। क्या यह {customer_name} जी हैं?"
        ]
    }
    
    VERIFICATION_RESPONSES = {
        'en': {
            'CONFIRMED_IDENTITY': [
                "Great, thank you.",
                "Perfect, thank you for confirming.",
                "Thank you, {customer_name}."
            ],
            'DENIED_IDENTITY': [
                "I apologize for the disturbance. We will update our records. Have a good day.",
                "Sorry for the inconvenience. We'll correct this in our system. Thank you."
            ],
            'NOT_INTERESTED': [
                "I understand. I'll note that you do not wish to be contacted. Have a good day.",
                "No problem. I'll update your preferences right away. Goodbye."
            ],
            'CONFUSION': [
                "This is a call from {bank_name} regarding {customer_name}'s account. Is he or she available?",
                "I'm calling from {bank_name} for {customer_name}. May I speak with them, please?"
            ],
            'UNCLEAR': [
                "I'm sorry, I didn't quite catch that. Is this {customer_name} speaking?",
                "Pardon me, could you please confirm if this is {customer_name}?"
            ]
        },
        'hi': {
            'CONFIRMED_IDENTITY': [
                "बहुत अच्छा, धन्यवाद।",
                "परफेक्ट, पुष्टि करने के लिए धन्यवाद।",
                "धन्यवाद, {customer_name} जी।"
            ],
            'DENIED_IDENTITY': [
                "मुझे खेद है। हम अपने रिकॉर्ड अपडेट कर देंगे। आपका दिन शुभ हो।",
                "असुविधा के लिए क्षमा करें। हम इसे अपने सिस्टम में ठीक कर देंगे। धन्यवाद।"
            ],
            'NOT_INTERESTED': [
                "मैं समझती हूं। मैं नोट कर लूंगी कि आप संपर्क नहीं चाहते। आपका दिन शुभ हो।",
                "कोई बात नहीं। मैं आपकी प्राथमिकताएं अभी अपडेट कर दूंगी। अलविदा।"
            ],
            'CONFUSION': [
                "यह {bank_name} की तरफ से {customer_name} जी के अकाउंट के बारे में कॉल है। क्या वो उपलब्ध हैं?",
                "मैं {bank_name} से {customer_name} जी के लिए बोल रही हूं। क्या मैं उनसे बात कर सकती हूं?"
            ],
            'UNCLEAR': [
                "मुझे खेद है, मैं ठीक से समझ नहीं पाई। क्या यह {customer_name} जी बोल रहे हैं?",
                "क्षमा करें, क्या आप पुष्टि कर सकते हैं कि यह {customer_name} जी हैं?"
            ]
        }
    }
    
    EMI_SCRIPTS = {
        'en': {
            'current': (
                "I'm reaching out regarding your {loan_type}. "
                "Our records show a pending installment of rupees {amount} which was due on {due_date_spoken}. "
                "I'd like to help resolve this. Could you tell me how you'd like to proceed?"
            ),
            'overdue': (
                "I'm reaching out about your {loan_type}. "
                "The payment of rupees {amount} has been overdue since {due_date_spoken}. "
                "I understand things can get busy, so I'm here to help. How would you like to handle this payment?"
            )
        },
        'hi': {
            'current': (
                "मैं आपके {loan_type} के बारे में बात करने के लिए कॉल कर रही हूं। "
                "हमारे रिकॉर्ड के अनुसार {amount} रुपये की किस्त {due_date_spoken} को देय थी जो अभी लंबित है। "
                "मैं इसे हल करने में मदद करना चाहती हूं। आप इसे कैसे आगे बढ़ाना चाहेंगे?"
            ),
            'overdue': (
                "मैं आपके {loan_type} के बारे में बात करने के लिए कॉल कर रही हूं। "
                "{amount} रुपये का भुगतान {due_date_spoken} से ओवरड्यू है। "
                "मैं समझती हूं कि चीजें व्यस्त हो सकती हैं, इसलिए मैं मदद के लिए यहां हूं। आप इस भुगतान को कैसे हैंडल करना चाहेंगे?"
            )
        }
    }
    
    CONVERSATION_RESPONSES = {
        'en': {
            'WILL_PAY_NOW': [
                "Excellent, thank you {customer_name}. I'll send a payment link to your registered number right away. Please check your messages in the next minute. Is there anything else I can help you with?"
            ],
            'WILL_PAY_LATER': [
                "Thank you for confirming, {customer_name}. I've noted that you'll make the payment by {commitment_date}. We'll send a payment link shortly. Is there anything else you need help with?"
            ],
            'ALREADY_PAID': [
                "Thank you for letting me know. Let me verify this in our system. Could you please share the transaction reference number if you have it? Otherwise, may I know when and how you made the payment?"
            ],
            'FACING_FINANCIAL_ISSUES': [
                "I'm really sorry to hear about your situation, {customer_name}. I understand this is difficult. We have options like a payment plan or extension. Would either of these work for you? I'm here to help."
            ],
            'DISPUTE_AMOUNT': [
                "I see there's a concern about the amount. Let me clarify. Your {loan_type} had an EMI of rupees {amount} due on {due_date_spoken}. Does this seem incorrect? I can help you understand the breakdown."
            ],
            'REQUEST_EXTENSION': [
                "I can definitely help with an extension. We can offer up to {extension_days} days for this payment. Would that work for you? Let me know if you need more time."
            ],
            'REQUEST_PAYMENT_PLAN': [
                "Absolutely, we can set up a payment plan. Would you prefer to pay this in two installments or three smaller ones? I can arrange whichever works better for you."
            ],
            'DEMANDS_SUPERVISOR': [
                "I completely understand, {customer_name}. I'll transfer you to a specialist right away. Please hold for just a moment."
            ],
            'POLITE_EXIT': [
                "Thank you so much for your time, {customer_name}. We'll send you all the details on your registered number shortly. Have a wonderful day. Goodbye."
            ],
            'UNCLEAR': [
                "I'm sorry, I'm having trouble understanding. You can say 'make payment', 'request help', or 'speak to agent'. What would you like to do?"
            ]
        },
        'hi': {
            'WILL_PAY_NOW': [
                "बहुत अच्छा, धन्यवाद {customer_name} जी। मैं आपके रजिस्टर्ड नंबर पर तुरंत पेमेंट लिंक भेज दूंगी। कृपया अगले एक मिनट में अपने मैसेज चेक करें। क्या मैं कुछ और मदद कर सकती हूं?"
            ],
            'WILL_PAY_LATER': [
                "पुष्टि करने के लिए धन्यवाद, {customer_name} जी। मैंने नोट कर लिया है कि आप {commitment_date} तक भुगतान कर देंगे। हम जल्द ही पेमेंट लिंक भेज देंगे। क्या कोई और मदद चाहिए?"
            ],
            'ALREADY_PAID': [
                "मुझे बताने के लिए धन्यवाद। मुझे इसे अपने सिस्टम में वेरीफाई करने दें। अगर आपके पास है तो क्या आप ट्रांजेक्शन रेफरेंस नंबर शेयर कर सकते हैं? नहीं तो क्या आप बता सकते हैं कि आपने कब और कैसे भुगतान किया था?"
            ],
            'FACING_FINANCIAL_ISSUES': [
                "मुझे आपकी स्थिति के बारे में सुनकर बहुत दुख हुआ, {customer_name} जी। मैं समझती हूं कि यह मुश्किल है। हमारे पास पेमेंट प्लान या एक्सटेंशन जैसे विकल्प हैं। क्या इनमें से कोई आपके लिए काम करेगा? मैं मदद के लिए यहां हूं।"
            ],
            'DISPUTE_AMOUNT': [
                "मैं देख रही हूं कि राशि के बारे में चिंता है। मुझे स्पष्ट करने दें। आपके {loan_type} की ईएमआई {amount} रुपये {due_date_spoken} को देय थी। क्या यह गलत लग रहा है? मैं आपको ब्रेकडाउन समझा सकती हूं।"
            ],
            'REQUEST_EXTENSION': [
                "मैं निश्चित रूप से एक्सटेंशन में मदद कर सकती हूं। हम इस भुगतान के लिए {extension_days} दिनों तक का समय दे सकते हैं। क्या यह आपके लिए काम करेगा? बताइए अगर आपको और समय चाहिए।"
            ],
            'REQUEST_PAYMENT_PLAN': [
                "बिल्कुल, हम पेमेंट प्लान सेट अप कर सकते हैं। क्या आप इसे दो किस्तों में या तीन छोटी किस्तों में चुकाना पसंद करेंगे? मैं जो भी आपके लिए बेहतर हो वो व्यवस्था कर सकती हूं।"
            ],
            'DEMANDS_SUPERVISOR': [
                "मैं पूरी तरह से समझती हूं, {customer_name} जी। मैं आपको तुरंत एक स्पेशलिस्ट से कनेक्ट कर दूंगी। बस एक क्षण रुकें।"
            ],
            'POLITE_EXIT': [
                "आपके समय के लिए बहुत-बहुत धन्यवाद, {customer_name} जी। हम आपको आपके रजिस्टर्ड नंबर पर जल्द ही सभी विवरण भेज देंगे। आपका दिन शुभ हो। अलविदा।"
            ],
            'UNCLEAR': [
                "मुझे खेद है, मुझे समझने में परेशानी हो रही है। आप 'पेमेंट करें', 'मदद चाहिए', या 'एजेंट से बात' कह सकते हैं। आप क्या करना चाहेंगे?"
            ]
        }
    }
    
    TRANSITION_MESSAGES = {
        'en': {
            'connecting': "Hello, thank you for connecting. Please hold one moment.",
            'to_emi': "One moment while I pull up your account details.",
            'processing': "Please hold while I process that."
        },
        'hi': {
            'connecting': "नमस्ते, कनेक्ट करने के लिए धन्यवाद। कृपया एक क्षण रुकें।",
            'to_emi': "एक क्षण रुकें जब तक मैं आपके अकाउंट की जानकारी निकालती हूं।",
            'processing': "कृपया रुकें जब तक मैं इसे प्रोसेस करती हूं।"
        }
    }
    
    OFFER_OPTIONS_PROMPT = {
        'en': (
            "I'm sorry, I'm not sure I understand. "
            "To make this easier, you can simply say 'make a payment', 'request help', or 'speak to an agent'. "
            "What would you like to do?"
        ),
        'hi': (
            "मुझे खेद है, मुझे यकीन नहीं है कि मैं समझी। "
            "इसे आसान बनाने के लिए, आप बस 'पेमेंट करें', 'मदद चाहिए', या 'एजेंट से बात' कह सकते हैं। "
            "आप क्या करना चाहेंगे?"
        )
    }
    
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
    
    @staticmethod
    def format_date_for_speech(date_str, language='en'):
        """
        Convert YYYY-MM-DD to natural speech format.
        English: "March 15th, 2024"
        Hindi: "पंद्रह मार्च दो हज़ार चौबीस"
        
        Args:
            date_str: Date in YYYY-MM-DD format
            language: 'en' or 'hi'
        """
        try:
            parts = date_str.split('-')
            year = parts[0]
            month = parts[1]
            day = int(parts[2])
            
            month_name = MultilingualScriptTemplates.MONTH_NAMES[language].get(month, month)
            
            if language == 'en':
                if day in [1, 21, 31]:
                    day_suffix = 'st'
                elif day in [2, 22]:
                    day_suffix = 'nd'
                elif day in [3, 23]:
                    day_suffix = 'rd'
                else:
                    day_suffix = 'th'
                
                return f"{day}{day_suffix} {month_name} {year}"
            
            else:
                hindi_numbers = {
                    1: 'पहली', 2: 'दो', 3: 'तीन', 4: 'चार', 5: 'पांच',
                    6: 'छह', 7: 'सात', 8: 'आठ', 9: 'नौ', 10: 'दस',
                    11: 'ग्यारह', 12: 'बारह', 13: 'तेरह', 14: 'चौदह', 15: 'पंद्रह',
                    16: 'सोलह', 17: 'सत्रह', 18: 'अठारह', 19: 'उन्नीस', 20: 'बीस',
                    21: 'इक्कीस', 22: 'बाईस', 23: 'तेईस', 24: 'चौबीस', 25: 'पच्चीस',
                    26: 'छब्बीस', 27: 'सत्ताईस', 28: 'अट्ठाईस', 29: 'उनतीस', 30: 'तीस', 31: 'इकतीस'
                }
                
                day_spoken = hindi_numbers.get(day, str(day))
                year_spoken = year
                
                return f"{day_spoken} {month_name} {year_spoken}"
        
        except:
            return date_str
    
    @staticmethod
    def get_time_of_day():
        """Returns appropriate greeting based on time"""
        from datetime import datetime
        hour = datetime.now().hour
        if hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        else:
            return "evening"
    
    @staticmethod
    def format_amount(amount, language='en'):
        """Format amount for TTS in the given language"""
        amount_str = str(int(amount))
        if len(amount_str) <= 3:
            return amount_str
        
        formatted = ""
        for i, digit in enumerate(reversed(amount_str)):
            if i == 3 or (i > 3 and (i - 3) % 2 == 0):
                formatted = "," + formatted
            formatted = digit + formatted
        
        return formatted.lstrip(",")
    
    @staticmethod
    def get_script(script_type, language, **kwargs):
        """
        Generic method to get any script in any language.
        
        Args:
            script_type: 'verification', 'emi', 'conversation', etc.
            language: 'en' or 'hi'
            **kwargs: Variables for template formatting
        """
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
        
        return "Thank you." if language == 'en' else "धन्यवाद।"
    
    @staticmethod
    def get_verification_script(language, bank_name, customer_name, variation=0):
        """Get verification script in specified language"""
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
        """Get verification response in specified language"""
        responses = MultilingualScriptTemplates.VERIFICATION_RESPONSES[language].get(
            intent, ['Thank you.' if language == 'en' else 'धन्यवाद।']
        )
        template = responses[variation % len(responses)]
        return template.format(bank_name=bank_name, customer_name=customer_name)
    
    @staticmethod
    def get_emi_script(language, customer_data):
        """Get EMI presentation script in specified language"""
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
        
        if is_overdue:
            template = scripts['overdue']
        else:
            template = scripts['current']
        
        return template.format(
            loan_type=loan_type, 
            amount=amount, 
            due_date_spoken=due_date_spoken
        )
    
    @staticmethod
    def get_conversation_response(language, intent, customer_data, context=None, variation=0):
        """Get conversation response in specified language"""
        responses = MultilingualScriptTemplates.CONVERSATION_RESPONSES[language].get(
            intent, ['Thank you for your response.' if language == 'en' else 'आपकी प्रतिक्रिया के लिए धन्यवाद।']
        )
        template = responses[variation % len(responses)]
        
        due_date_spoken = MultilingualScriptTemplates.format_date_for_speech(
            customer_data['bank_details']['due_date'], language
        )
        
        variables = {
            'customer_name': customer_data.get('name'),
            'loan_type': customer_data['bank_details']['loan_type'],
            'amount': MultilingualScriptTemplates.format_amount(
                customer_data['bank_details']['pending_emi_amount'], language
            ),
            'due_date_spoken': due_date_spoken,
            'extension_days': '15',
            'commitment_date': context.get('commitment_date', 
                'the agreed date' if language == 'en' else 'सहमत तारीख') if context else (
                'the agreed date' if language == 'en' else 'सहमत तारीख')
        }
        
        try:
            return template.format(**variables)
        except KeyError:
            return template