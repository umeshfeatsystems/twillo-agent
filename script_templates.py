"""
Professional TTS-Optimized Script Templates
All scripts are designed for consistent voice delivery with:
- Controlled sentence length (10-20 words)
- Natural pauses (commas, periods)
- Consistent punctuation patterns
"""

class ScriptTemplates:
    """
    Pre-written, TTS-optimized scripts that ensure consistent voice quality.
    Uses template variables instead of AI generation.
    """
    
    # ============================================
    # VERIFICATION SCRIPTS (Step 1)
    # ============================================
    VERIFICATION_SCRIPTS = [
        "Hello, this is a call from {bank_name}. Am I speaking with {customer_name}?",
        "Hi, I'm calling from {bank_name}. May I please speak with {customer_name}?",
        "Good {time_of_day}, this is {bank_name} calling. Is this {customer_name}?"
    ]
    
    # ============================================
    # VERIFICATION RESPONSES (Step 2)
    # ============================================
    VERIFICATION_RESPONSES = {
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
    }
    
    # ============================================
    # EMI PRESENTATION SCRIPTS (Step 3)
    # ============================================
    EMI_FIRST_TIME = (
        "I'm reaching out regarding your {loan_type}. "
        "Our records show a pending installment of rupees {amount} which was due on {due_date}. "
        "I'd like to help resolve this. Could you tell me how you'd like to proceed?"
    )
    
    EMI_WITH_HISTORY = (
        "I'm calling about your {loan_type}. "
        "I see we last spoke on {last_call_date}, and our records still show the pending amount of rupees {amount} from {due_date}. "
        "I was hoping we could find a solution today. What's the current situation?"
    )
    
    EMI_OVERDUE = (
        "I'm reaching out about your {loan_type}. "
        "The payment of rupees {amount} has been overdue since {due_date}. "
        "I understand things can get busy, so I'm here to help. How would you like to handle this payment?"
    )
    
    # ============================================
    # CONVERSATION RESPONSES (Step 4)
    # ============================================
    CONVERSATION_RESPONSES = {
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
            "I'm really sorry to hear about your situation, {customer_name}. I understand this is difficult. We have a few options that might help, like a payment plan or a temporary extension. Would either of these work for you?",
            "I understand this is a tough time. We can arrange smaller installments or defer this payment. Which option would be more manageable for you?"
        ],
        
        'DISPUTE_AMOUNT': [
            "I see there's a concern about the amount. Let me clarify the details. Your {loan_type} had an EMI of rupees {amount} due on {due_date}. Does this seem incorrect to you?",
            "Thank you for bringing this up. Could you help me understand what amount you were expecting? I'll verify this against our records."
        ],
        
        'REQUEST_EXTENSION': [
            "I can definitely help with an extension. We can offer up to {extension_days} days for this payment. Would that work for you, {customer_name}?",
            "Of course. I can process an extension request. How many additional days would you need to make this payment comfortably?"
        ],
        
        'REQUEST_PAYMENT_PLAN': [
            "Absolutely, we can set up a payment plan. Would you prefer to pay this in two installments or three smaller ones over the next few weeks?",
            "I can arrange that for you. We could split this into manageable amounts. What works better, weekly or monthly installments?"
        ],
        
        'DEMANDS_SUPERVISOR': [
            "I completely understand, {customer_name}. I'll transfer you to a specialist right away. Please hold for just a moment.",
            "Of course. Let me connect you with my supervisor immediately. One moment please."
        ],
        
        'ANGRY_ABUSIVE': [
            "I apologize if we've caused any frustration. Let me connect you with a supervisor who can better assist you. Please hold.",
            "I'm sorry you're upset. I think it's best if I transfer you to someone senior. One moment please."
        ],
        
        'CONFUSION_WRONG_PERSON': [
            "I apologize for the confusion. Could you please let me know who I'm speaking with? I want to make sure I have the right person.",
            "I'm sorry for any mix-up. Is {customer_name} available, or should I call back at a different time?"
        ],
        
        'UNCLEAR': [
            "I'm sorry, I'm having a little trouble understanding. To make this simple, you can say 'make a payment', 'request help', or 'speak to an agent'. What would you like to do?",
            "Pardon me, I didn't quite catch that. Could you please tell me if you'd like to make a payment, need assistance, or prefer to speak with an agent?"
        ],
        
        'SMALL_TALK': [
            "I appreciate that, {customer_name}. However, I do need to discuss your {loan_type} payment. Could we focus on that for just a moment?",
            "That's nice to hear. Now, regarding your pending payment of rupees {amount}, how would you like to proceed?"
        ],
        
        # ============================================
        # NEW: Polite Exit Responses
        # ============================================
        'POLITE_EXIT': [
            "Thank you so much for your time, {customer_name}. We'll send you a payment link shortly. Have a wonderful day!",
            "Perfect, thank you {customer_name}. You'll receive all the details on your registered number. Have a great day!",
            "Excellent. Thank you for speaking with me, {customer_name}. We'll follow up with the payment link. Take care!"
        ]
    }
    
    # ============================================
    # TRANSITION PHRASES (for smooth flow)
    # ============================================
    TRANSITION_CONNECTING = "Hello, thank you for connecting. Please hold one moment."
    
    TRANSITION_TO_EMI = "One moment while I pull up your account details."
    
    # ============================================
    # CONFUSION HANDLING (NEW)
    # ============================================
    OFFER_OPTIONS_PROMPT = (
        "I'm sorry, I'm not sure I understand. "
        "To make this easier, you can simply say 'make a payment', 'request help', or 'speak to an agent'. "
        "What would you like to do?"
    )
    
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
    def format_amount(amount):
        """Format amount in Indian rupee style"""
        # Convert 15000 to "fifteen thousand"
        amount_str = str(int(amount))
        if len(amount_str) <= 3:
            return amount_str
        
        # Indian numbering: 15,000 not 15000
        formatted = ""
        for i, digit in enumerate(reversed(amount_str)):
            if i == 3 or (i > 3 and (i - 3) % 2 == 0):
                formatted = "," + formatted
            formatted = digit + formatted
        
        return formatted.lstrip(",")
    
    @staticmethod
    def get_verification_script(bank_name, customer_name, variation=0):
        """Get verification script with consistent voice formatting"""
        template = ScriptTemplates.VERIFICATION_SCRIPTS[variation % len(ScriptTemplates.VERIFICATION_SCRIPTS)]
        time_of_day = ScriptTemplates.get_time_of_day()
        return template.format(
            bank_name=bank_name,
            customer_name=customer_name,
            time_of_day=time_of_day
        )
    
    @staticmethod
    def get_verification_response(intent, bank_name, customer_name, variation=0):
        """Get verification response based on intent"""
        responses = ScriptTemplates.VERIFICATION_RESPONSES.get(intent, ['Thank you.'])
        template = responses[variation % len(responses)]
        return template.format(
            bank_name=bank_name,
            customer_name=customer_name
        )
    
    @staticmethod
    def get_emi_script(customer_data, has_history=False):
        """Get EMI presentation script with consistent formatting"""
        amount = ScriptTemplates.format_amount(customer_data['bank_details']['pending_emi_amount'])
        due_date = customer_data['bank_details']['due_date']
        loan_type = customer_data['bank_details']['loan_type']
        
        # Check if overdue (simple date comparison)
        from datetime import datetime
        due = datetime.strptime(due_date, "%Y-%m-%d")
        is_overdue = due < datetime.now()
        
        if is_overdue:
            template = ScriptTemplates.EMI_OVERDUE
        elif has_history:
            template = ScriptTemplates.EMI_WITH_HISTORY
            # Get last call date
            call_history = customer_data.get('call_history', [])
            if len(call_history) > 1:
                last_call = call_history[-2]
                last_call_date = last_call.get('timestamp', '')[:10]  # YYYY-MM-DD
                return template.format(
                    loan_type=loan_type,
                    amount=amount,
                    due_date=due_date,
                    last_call_date=last_call_date
                )
        else:
            template = ScriptTemplates.EMI_FIRST_TIME
        
        return template.format(
            loan_type=loan_type,
            amount=amount,
            due_date=due_date
        )
    
    @staticmethod
    def get_conversation_response(intent, customer_data, context=None, variation=0):
        """Get conversation response based on intent"""
        responses = ScriptTemplates.CONVERSATION_RESPONSES.get(intent, ['Thank you for your response.'])
        template = responses[variation % len(responses)]
        
        # Prepare variables
        variables = {
            'customer_name': customer_data.get('name'),
            'loan_type': customer_data['bank_details']['loan_type'],
            'amount': ScriptTemplates.format_amount(customer_data['bank_details']['pending_emi_amount']),
            'due_date': customer_data['bank_details']['due_date'],
            'extension_days': '15',  # Default extension
            'commitment_date': context.get('commitment_date', 'the agreed date') if context else 'the agreed date'
        }
        
        # Format with available variables
        try:
            return template.format(**variables)
        except KeyError:
            # Fallback if template has variables we didn't provide
            return template
    
    @staticmethod
    def get_offer_options():
        """Get the 'offer options' script when confused"""
        return ScriptTemplates.OFFER_OPTIONS_PROMPT