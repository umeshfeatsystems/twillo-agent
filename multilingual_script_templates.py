"""
Multi-lingual Script Templates
Professional scripts in Hindi and English
"""

class MultilingualScriptTemplates:
    """
    Bilingual script templates with professional translations.
    All Hindi scripts are professionally translated and TTS-optimized.
    """
    
    # ============================================
    # VERIFICATION SCRIPTS
    # ============================================
    VERIFICATION_SCRIPTS = {
        'en': [
            "Hello, this is a call from {bank_name}. Am I speaking with {customer_name}?",
            "Hi, I'm calling from {bank_name}. May I please speak with {customer_name}?",
            "Good {time_of_day}, this is {bank_name} calling. Is this {customer_name}?"
        ],
        'hi': [
            "नमस्ते, यह {bank_name} की तरफ से कॉल है। क्या मैं {customer_name} जी से बात कर रहा हूँ?",
            "नमस्कार, मैं {bank_name} से बोल रहा हूँ। क्या मैं {customer_name} जी से बात कर सकता हूँ?",
            "सुप्रभात, यह {bank_name} की तरफ से कॉल है। क्या यह {customer_name} जी हैं?"
        ]
    }
    
    # ============================================
    # VERIFICATION RESPONSES
    # ============================================
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
                "मैं समझता हूँ। मैं नोट कर लूंगा कि आप संपर्क नहीं चाहते। आपका दिन शुभ हो।",
                "कोई बात नहीं। मैं आपकी प्राथमिकताएं अभी अपडेट कर दूंगा। अलविदा।"
            ],
            'CONFUSION': [
                "यह {bank_name} की तरफ से {customer_name} जी के अकाउंट के बारे में कॉल है। क्या वो उपलब्ध हैं?",
                "मैं {bank_name} से {customer_name} जी के लिए बोल रहा हूँ। क्या मैं उनसे बात कर सकता हूँ?"
            ],
            'UNCLEAR': [
                "मुझे खेद है, मैं ठीक से समझ नहीं पाया। क्या यह {customer_name} जी बोल रहे हैं?",
                "क्षमा करें, क्या आप पुष्टि कर सकते हैं कि यह {customer_name} जी हैं?"
            ]
        }
    }
    
    # ============================================
    # EMI PRESENTATION SCRIPTS
    # ============================================
    EMI_SCRIPTS = {
        'en': {
            'first_time': (
                "I'm reaching out regarding your {loan_type}. "
                "Our records show a pending installment of rupees {amount} which was due on {due_date}. "
                "I'd like to help resolve this. Could you tell me how you'd like to proceed?"
            ),
            'with_history': (
                "I'm calling about your {loan_type}. "
                "I see we last spoke on {last_call_date}, and our records still show the pending amount of rupees {amount} from {due_date}. "
                "I was hoping we could find a solution today. What's the current situation?"
            ),
            'overdue': (
                "I'm reaching out about your {loan_type}. "
                "The payment of rupees {amount} has been overdue since {due_date}. "
                "I understand things can get busy, so I'm here to help. How would you like to handle this payment?"
            )
        },
        'hi': {
            'first_time': (
                "मैं आपके {loan_type} के बारे में बात करने के लिए कॉल कर रहा हूँ। "
                "हमारे रिकॉर्ड के अनुसार {amount} रुपये की किस्त {due_date} को देय थी जो अभी लंबित है। "
                "मैं इसे हल करने में मदद करना चाहता हूँ। आप इसे कैसे आगे बढ़ाना चाहेंगे?"
            ),
            'with_history': (
                "मैं आपके {loan_type} के बारे में बात कर रहा हूँ। "
                "हमने आखिरी बार {last_call_date} को बात की थी, और हमारे रिकॉर्ड में अभी भी {due_date} से {amount} रुपये की राशि लंबित दिख रही है। "
                "मुझे उम्मीद थी कि हम आज कोई समाधान निकाल सकते हैं। स्थिति क्या है?"
            ),
            'overdue': (
                "मैं आपके {loan_type} के बारे में बात करने के लिए कॉल कर रहा हूँ। "
                "{amount} रुपये का भुगतान {due_date} से ओवरड्यू है। "
                "मैं समझता हूँ कि चीजें व्यस्त हो सकती हैं, इसलिए मैं मदद के लिए यहाँ हूँ। आप इस भुगतान को कैसे हैंडल करना चाहेंगे?"
            )
        }
    }
    
    # ============================================
    # CONVERSATION RESPONSES
    # ============================================
    CONVERSATION_RESPONSES = {
        'en': {
            'WILL_PAY_NOW': [
                "Excellent, thank you {customer_name}. I'll send a payment link to your registered number right away. Is there anything else I can help with?",
                "Perfect. I'm sending the payment link to your mobile number now. You should receive it within a minute. Thank you!"
            ],
            'WILL_PAY_LATER': [
                "Thank you for confirming, {customer_name}. I've noted that you'll make the payment by {commitment_date}. We'll send a payment link shortly. Have a great day!",
                "I appreciate that. I've scheduled a reminder for {commitment_date}. The payment link will be sent to you. Thank you!"
            ],
            'ALREADY_PAID': [
                "Thank you for letting me know. Let me verify this in our system. Could you please share the transaction reference number if you have it?",
                "I see. Our records may not have updated yet. Could you tell me when you made the payment and through which method?"
            ],
            'FACING_FINANCIAL_ISSUES': [
                "I'm really sorry to hear about your situation, {customer_name}. I understand this is difficult. We have options like a payment plan or extension. Would either of these work for you?",
                "I understand this is a tough time. We can arrange smaller installments or defer this payment. Which option would be more manageable for you?"
            ],
            'DISPUTE_AMOUNT': [
                "I see there's a concern about the amount. Let me clarify. Your {loan_type} had an EMI of rupees {amount} due on {due_date}. Does this seem incorrect?",
                "Thank you for bringing this up. Could you help me understand what amount you were expecting? I'll verify this against our records."
            ],
            'REQUEST_EXTENSION': [
                "I can definitely help with an extension. We can offer up to {extension_days} days for this payment. Would that work for you?",
                "Of course. I can process an extension request. How many additional days would you need to make this payment comfortably?"
            ],
            'REQUEST_PAYMENT_PLAN': [
                "Absolutely, we can set up a payment plan. Would you prefer to pay this in two installments or three smaller ones?",
                "I can arrange that for you. We could split this into manageable amounts. What works better, weekly or monthly installments?"
            ],
            'DEMANDS_SUPERVISOR': [
                "I completely understand, {customer_name}. I'll transfer you to a specialist right away. Please hold for just a moment.",
                "Of course. Let me connect you with my supervisor immediately. One moment please."
            ],
            'POLITE_EXIT': [
                "Thank you so much for your time, {customer_name}. We'll send you a payment link shortly. Have a wonderful day!",
                "Perfect, thank you {customer_name}. You'll receive all the details on your registered number. Have a great day!"
            ],
            'UNCLEAR': [
                "I'm sorry, I'm having trouble understanding. You can say 'make payment', 'request help', or 'speak to agent'. What would you like to do?",
                "Pardon me, I didn't quite catch that. Could you please tell me if you'd like to make a payment, need assistance, or speak with an agent?"
            ]
        },
        'hi': {
            'WILL_PAY_NOW': [
                "बहुत अच्छा, धन्यवाद {customer_name} जी। मैं आपके रजिस्टर्ड नंबर पर तुरंत पेमेंट लिंक भेज दूंगा। क्या मैं कुछ और मदद कर सकता हूँ?",
                "परफेक्ट। मैं अभी आपके मोबाइल नंबर पर पेमेंट लिंक भेज रहा हूँ। आपको एक मिनट में मिल जाएगा। धन्यवाद!"
            ],
            'WILL_PAY_LATER': [
                "पुष्टि करने के लिए धन्यवाद, {customer_name} जी। मैंने नोट कर लिया है कि आप {commitment_date} तक भुगतान कर देंगे। हम जल्द ही पेमेंट लिंक भेज देंगे। आपका दिन शुभ हो!",
                "मैं इसकी सराहना करता हूँ। मैंने {commitment_date} के लिए रिमाइंडर शेड्यूल कर दिया है। पेमेंट लिंक आपको भेज दिया जाएगा। धन्यवाद!"
            ],
            'ALREADY_PAID': [
                "मुझे बताने के लिए धन्यवाद। मुझे इसे अपने सिस्टम में वेरीफाई करने दें। अगर आपके पास है तो क्या आप ट्रांजेक्शन रेफरेंस नंबर शेयर कर सकते हैं?",
                "मैं समझा। हो सकता है कि हमारे रिकॉर्ड अभी अपडेट नहीं हुए हों। क्या आप बता सकते हैं कि आपने कब और किस तरीके से भुगतान किया था?"
            ],
            'FACING_FINANCIAL_ISSUES': [
                "मुझे आपकी स्थिति के बारे में सुनकर बहुत दुख हुआ, {customer_name} जी। मैं समझता हूँ कि यह मुश्किल है। हमारे पास पेमेंट प्लान या एक्सटेंशन जैसे विकल्प हैं। क्या इनमें से कोई आपके लिए काम करेगा?",
                "मैं समझता हूँ कि यह मुश्किल समय है। हम छोटी किस्तों की व्यवस्था कर सकते हैं या इस भुगतान को टाल सकते हैं। आपके लिए कौन सा विकल्प ज्यादा मैनेजेबल होगा?"
            ],
            'DISPUTE_AMOUNT': [
                "मैं देख रहा हूँ कि राशि के बारे में चिंता है। मुझे स्पष्ट करने दें। आपके {loan_type} की ईएमआई {amount} रुपये {due_date} को देय थी। क्या यह गलत लग रहा है?",
                "इसे उठाने के लिए धन्यवाद। क्या आप मुझे समझा सकते हैं कि आप कितनी राशि की उम्मीद कर रहे थे? मैं इसे अपने रिकॉर्ड से वेरीफाई करूंगा।"
            ],
            'REQUEST_EXTENSION': [
                "मैं निश्चित रूप से एक्सटेंशन में मदद कर सकता हूँ। हम इस भुगतान के लिए {extension_days} दिनों तक का समय दे सकते हैं। क्या यह आपके लिए काम करेगा?",
                "बिल्कुल। मैं एक्सटेंशन रिक्वेस्ट प्रोसेस कर सकता हूँ। आपको यह भुगतान आराम से करने के लिए कितने अतिरिक्त दिन चाहिए?"
            ],
            'REQUEST_PAYMENT_PLAN': [
                "बिल्कुल, हम पेमेंट प्लान सेट अप कर सकते हैं। क्या आप इसे दो किस्तों में या तीन छोटी किस्तों में चुकाना पसंद करेंगे?",
                "मैं आपके लिए यह व्यवस्था कर सकता हूँ। हम इसे मैनेजेबल राशियों में बांट सकते हैं। साप्ताहिक या मासिक किस्त, कौन सा बेहतर काम करेगा?"
            ],
            'DEMANDS_SUPERVISOR': [
                "मैं पूरी तरह से समझता हूँ, {customer_name} जी। मैं आपको तुरंत एक स्पेशलिस्ट से कनेक्ट कर दूंगा। बस एक क्षण रुकें।",
                "बिल्कुल। मैं आपको तुरंत अपने सुपरवाइजर से कनेक्ट करता हूँ। एक क्षण रुकें।"
            ],
            'POLITE_EXIT': [
                "आपके समय के लिए बहुत-बहुत धन्यवाद, {customer_name} जी। हम जल्द ही आपको पेमेंट लिंक भेज देंगे। आपका दिन मंगलमय हो!",
                "परफेक्ट, धन्यवाद {customer_name} जी। आपको अपने रजिस्टर्ड नंबर पर सभी विवरण मिल जाएंगे। आपका दिन शुभ हो!"
            ],
            'UNCLEAR': [
                "मुझे खेद है, मुझे समझने में परेशानी हो रही है। आप 'पेमेंट करें', 'मदद चाहिए', या 'एजेंट से बात' कह सकते हैं। आप क्या करना चाहेंगे?",
                "क्षमा करें, मैं ठीक से समझ नहीं पाया। क्या आप बता सकते हैं कि आप पेमेंट करना चाहते हैं, मदद चाहिए, या एजेंट से बात करना चाहते हैं?"
            ]
        }
    }
    
    # ============================================
    # SPECIAL MESSAGES
    # ============================================
    TRANSITION_MESSAGES = {
        'en': {
            'connecting': "Hello, thank you for connecting. Please hold one moment.",
            'to_emi': "One moment while I pull up your account details.",
            'processing': "Please hold while I process that."
        },
        'hi': {
            'connecting': "नमस्ते, कनेक्ट करने के लिए धन्यवाद। कृपया एक क्षण रुकें।",
            'to_emi': "एक क्षण रुकें जब तक मैं आपके अकाउंट की जानकारी निकालता हूँ।",
            'processing': "कृपया रुकें जब तक मैं इसे प्रोसेस करता हूँ।"
        }
    }
    
    OFFER_OPTIONS_PROMPT = {
        'en': (
            "I'm sorry, I'm not sure I understand. "
            "To make this easier, you can simply say 'make a payment', 'request help', or 'speak to an agent'. "
            "What would you like to do?"
        ),
        'hi': (
            "मुझे खेद है, मुझे यकीन नहीं है कि मैं समझा। "
            "इसे आसान बनाने के लिए, आप बस 'पेमेंट करें', 'मदद चाहिए', या 'एजेंट से बात' कह सकते हैं। "
            "आप क्या करना चाहेंगे?"
        )
    }
    
    # ============================================
    # UTILITY METHODS
    # ============================================
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
        
        # Indian numbering: 15,000
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
                language, kwargs.get('customer_data'), kwargs.get('has_history', False)
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
    def get_emi_script(language, customer_data, has_history=False):
        """Get EMI presentation script in specified language"""
        amount = MultilingualScriptTemplates.format_amount(
            customer_data['bank_details']['pending_emi_amount'], language
        )
        due_date = customer_data['bank_details']['due_date']
        loan_type = customer_data['bank_details']['loan_type']
        
        # Check if overdue
        from datetime import datetime
        due = datetime.strptime(due_date, "%Y-%m-%d")
        is_overdue = due < datetime.now()
        
        scripts = MultilingualScriptTemplates.EMI_SCRIPTS[language]
        
        if is_overdue:
            template = scripts['overdue']
        elif has_history:
            template = scripts['with_history']
            call_history = customer_data.get('call_history', [])
            if len(call_history) > 1:
                last_call = call_history[-2]
                last_call_date = last_call.get('timestamp', '')[:10]
                return template.format(
                    loan_type=loan_type, amount=amount,
                    due_date=due_date, last_call_date=last_call_date
                )
        else:
            template = scripts['first_time']
        
        return template.format(loan_type=loan_type, amount=amount, due_date=due_date)
    
    @staticmethod
    def get_conversation_response(language, intent, customer_data, context=None, variation=0):
        """Get conversation response in specified language"""
        responses = MultilingualScriptTemplates.CONVERSATION_RESPONSES[language].get(
            intent, ['Thank you for your response.' if language == 'en' else 'आपकी प्रतिक्रिया के लिए धन्यवाद।']
        )
        template = responses[variation % len(responses)]
        
        variables = {
            'customer_name': customer_data.get('name'),
            'loan_type': customer_data['bank_details']['loan_type'],
            'amount': MultilingualScriptTemplates.format_amount(
                customer_data['bank_details']['pending_emi_amount'], language
            ),
            'due_date': customer_data['bank_details']['due_date'],
            'extension_days': '15',
            'commitment_date': context.get('commitment_date', 
                'the agreed date' if language == 'en' else 'सहमत तारीख') if context else (
                'the agreed date' if language == 'en' else 'सहमत तारीख')
        }
        
        try:
            return template.format(**variables)
        except KeyError:
            return template