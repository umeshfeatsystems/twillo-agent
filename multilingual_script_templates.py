"""
Script Helper - Focuses on Data Formatting and Compliance Scripts
"""
from config import Config
from datetime import datetime
try:
    from num2words import num2words
except ImportError:
    num2words = None

class MultilingualScriptTemplates:
    
    MONTH_NAMES = {
        'en': { '01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May', '06': 'June', '07': 'July', '08': 'August', '09': 'September', '10': 'October', '11': 'November', '12': 'December' },
        'hi': { '01': 'जनवरी', '02': 'फरवरी', '03': 'मार्च', '04': 'अप्रैल', '05': 'मई', '06': 'जून', '07': 'जुलाई', '08': 'अगस्त', '09': 'सितंबर', '10': 'अक्टूबर', '11': 'नवंबर', '12': 'दिसंबर' }
    }

    # Strict compliance scripts (Greeting & EMI Details) - Better to keep these hardcoded for legal safety
    VERIFICATION_SCRIPTS = {
        'en': ["Hello. This is a call from {bank_name}. Am I speaking with {customer_name}?", "Hi. Calling from {bank_name}. Is this {customer_name}?"],
        'hi': ["नमस्ते। मैं {bank_name} से बोल रही हूं। क्या मैं {customer_name} जी से बात कर रही हूं?", "नमस्ते। {bank_name} से कॉल है। क्या आप {customer_name} जी हैं?"]
    }

    EMI_SCRIPTS = {
        'en': { 'current': "Regarding your {loan_type}. There is a pending installment of rupees {amount}, due on {due_date_spoken}. How would you like to make this payment?", 'overdue': "Regarding your {loan_type}. A payment of rupees {amount} is overdue since {due_date_spoken}. We need to clear this. When can you pay?" },
        'hi': { 'current': "आपके {loan_type} के बारे में। {amount} रुपये की किश्त {due_date_spoken} को देनी है। आप यह पेमेंट कैसे करेंगे?", 'overdue': "आपके {loan_type} के लिए। {amount} रुपये {due_date_spoken} से बाकी हैं। इसे क्लियर करना ज़रूरी है। आप कब तक जमा करेंगे?" }
    }
    
    @staticmethod
    def _convert_number_to_hindi(n):
        """Robust native conversion using num2words library."""
        if num2words:
            try:
                # Force Hindi output
                return num2words(n, lang='hi') 
            except Exception:
                try:
                    # Fallback to Indian English
                    return num2words(n, lang='en_IN')
                except:
                    return str(n)
        return str(n)

    @staticmethod
    def format_date_for_speech(date_str, language='en'):
        try:
            parts = date_str.split('-')
            year = int(parts[0])
            month = parts[1]
            day = int(parts[2])
            month_name = MultilingualScriptTemplates.MONTH_NAMES.get(language, MultilingualScriptTemplates.MONTH_NAMES['en']).get(month, month)
            
            if language == 'hi':
                day_text = MultilingualScriptTemplates._convert_number_to_hindi(day)
                year_text = MultilingualScriptTemplates._convert_number_to_hindi(year)
                return f"{day_text} {month_name} {year_text}"
            
            # Default English
            if day in [1, 21, 31]: day_suffix = 'st'
            elif day in [2, 22]: day_suffix = 'nd'
            elif day in [3, 23]: day_suffix = 'rd'
            else: day_suffix = 'th'
            return f"{day}{day_suffix} {month_name} {year}"
        except:
            return date_str

    @staticmethod
    def format_amount(amount, language='en'):
        """
        Returns the spoken string of the amount.
        Example: 15000 -> "fifteen thousand" or "पंद्रह हज़ार"
        """
        try:
            amount_val = int(float(str(amount).replace(',', '')))
            
            if language == 'hi' or language == 'en-hi-hybrid':
                return MultilingualScriptTemplates._convert_number_to_hindi(amount_val)
            
            # For pure English, use num2words in English
            if num2words:
                return num2words(amount_val, lang='en_IN')
            
            return str(amount_val)
        except Exception:
            return str(amount)
            
    @staticmethod
    def get_verification_script(language, bank_name, customer_name, variation=0):
        # Hybrid defaults to English for greeting usually, or simple Hindi
        lang_key = 'hi' if language == 'hi' else 'en'
        scripts = MultilingualScriptTemplates.VERIFICATION_SCRIPTS[lang_key]
        return scripts[variation % len(scripts)].format(bank_name=bank_name, customer_name=customer_name)

    @staticmethod
    def get_emi_script(language, customer_data):
        # We prepare the variables here so the initial script is perfectly accurate
        lang_key = 'hi' if language == 'hi' else 'en'
        
        amount = MultilingualScriptTemplates.format_amount(customer_data['bank_details']['pending_emi_amount'], language)
        due_date_spoken = MultilingualScriptTemplates.format_date_for_speech(customer_data['bank_details']['due_date'], language)
        loan_type = customer_data['bank_details']['loan_type']
        
        from datetime import datetime
        due = datetime.strptime(customer_data['bank_details']['due_date'], "%Y-%m-%d")
        is_overdue = due < datetime.now()
        
        scripts = MultilingualScriptTemplates.EMI_SCRIPTS[lang_key]
        template = scripts['overdue'] if is_overdue else scripts['current']
        
        return template.format(loan_type=loan_type, amount=amount, due_date_spoken=due_date_spoken)