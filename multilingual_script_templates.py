"""
Script Helper - Focuses on Data Formatting and Compliance Scripts
"""
from config import Config
from datetime import datetime

# Import num2words (Backup)
try:
    from num2words import num2words
except ImportError:
    num2words = None

# Import indic-num2words (Primary for Hindi)
try:
    from num_to_words import num_to_word
except ImportError:
    num_to_word = None

class MultilingualScriptTemplates:
    
    MONTH_NAMES = {
        'en': { '01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May', '06': 'June', '07': 'July', '08': 'August', '09': 'September', '10': 'October', '11': 'November', '12': 'December' },
        'hi': { '01': 'जनवरी', '02': 'फरवरी', '03': 'मार्च', '04': 'अप्रैल', '05': 'मई', '06': 'जून', '07': 'जुलाई', '08': 'अगस्त', '09': 'सितंबर', '10': 'अक्टूबर', '11': 'नवंबर', '12': 'दिसंबर' }
    }

    # Strict compliance scripts
    VERIFICATION_SCRIPTS = {
        'en': [
            "Hello. This is a call from {bank_name}. Am I speaking with {customer_name}?", 
            "Hi. Calling from {bank_name}. Is this {customer_name}?"
        ],
        'hi': [
            "नमस्ते। मैं {bank_name} से बोल रहा हूं। क्या मैं {customer_name} जी से बात कर रहा हूं?", 
            "नमस्ते। {bank_name} से कॉल है। क्या आप {customer_name} जी हैं?"
        ],
        # NEW: Bilingual Greeting (English + Hindi)
        'en-hi-hybrid': [
            "Hello, this is a call from {bank_name}. Am I speaking with {customer_name}? Namaste, kya meri baat {customer_name} ji se ho rahi hai?",
            "Hi, calling from {bank_name}. Is this {customer_name}? Namaste, kya main {customer_name} ji se baat kar raha hoon?"
        ]
    }

    EMI_SCRIPTS = {
        'en': { 
            'current': "Regarding your {loan_type}. There is a pending installment of rupees {amount}, due on {due_date_spoken}. How would you like to make this payment?", 
            'overdue': "Regarding your {loan_type}. A payment of rupees {amount} is overdue since {due_date_spoken}. We need to clear this. When can you pay?" 
        },
        'hi': { 
            # STRICT HINDI: Replaced 'payment' with 'bhugtan' and 'clear' with 'jama/chukana'
            'current': "आपके {loan_type} के बारे में। {amount} रुपये की किश्त {due_date_spoken} को देनी है। आप यह भुगतान (Payment) कैसे करेंगे?", 
            'overdue': "आपके {loan_type} के लिए। {amount} रुपये {due_date_spoken} से बाकी हैं। इसे जमा करना ज़रूरी है। आप कब तक चुकायेंगे?" 
        }
    }
    
    @staticmethod
    def _convert_number_to_hindi(n):
        """Robust native conversion using indic-num2words (Primary) or num2words (Backup)."""
        if num_to_word:
            try:
                return num_to_word(n, lang='hi')
            except Exception as e:
                print(f"indic-num2words failed for {n}: {e}")
        
        if num2words:
            try:
                return num2words(n, lang='hi') 
            except Exception:
                pass
                
        if num2words:
            try:
                return num2words(n, lang='en_IN')
            except:
                pass
        return str(n)

    @staticmethod
    def format_date_for_speech(date_str, language='en'):
        try:
            parts = date_str.split('-')
            year = int(parts[0])
            month = parts[1]
            day = int(parts[2])
            
            lang_key = 'hi' if language in ['hi', 'en-hi-hybrid'] else 'en'
            
            month_name = MultilingualScriptTemplates.MONTH_NAMES.get(lang_key, MultilingualScriptTemplates.MONTH_NAMES['en']).get(month, month)
            
            if lang_key == 'hi':
                day_text = MultilingualScriptTemplates._convert_number_to_hindi(day)
                year_text = MultilingualScriptTemplates._convert_number_to_hindi(year)
                return f"{day_text} {month_name} {year_text}"
            
            if day in [1, 21, 31]: day_suffix = 'st'
            elif day in [2, 22]: day_suffix = 'nd'
            elif day in [3, 23]: day_suffix = 'rd'
            else: day_suffix = 'th'
            return f"{day}{day_suffix} {month_name} {year}"
        except:
            return date_str

    @staticmethod
    def format_amount(amount, language='en'):
        try:
            amount_str = str(amount).replace(',', '').strip()
            amount_val = int(float(amount_str))
            
            if language in ['hi', 'en-hi-hybrid']:
                return MultilingualScriptTemplates._convert_number_to_hindi(amount_val)
            
            if num2words:
                try:
                    return num2words(amount_val, lang='en_IN')
                except:
                    return str(amount_val)
            return str(amount_val)
        except Exception as e:
            print(f"Error formatting amount {amount}: {e}")
            return str(amount)
            
    @staticmethod
    def get_verification_script(language, bank_name, customer_name, variation=0):
        # Allow specific 'en-hi-hybrid' selection
        if language in MultilingualScriptTemplates.VERIFICATION_SCRIPTS:
            scripts = MultilingualScriptTemplates.VERIFICATION_SCRIPTS[language]
        else:
            lang_key = 'hi' if language == 'hi' else 'en'
            scripts = MultilingualScriptTemplates.VERIFICATION_SCRIPTS[lang_key]
            
        return scripts[variation % len(scripts)].format(bank_name=bank_name, customer_name=customer_name)

    @staticmethod
    def get_emi_script(language, customer_data):
        lang_key = 'hi' if language in ['hi', 'en-hi-hybrid'] else 'en'
        amount = MultilingualScriptTemplates.format_amount(customer_data['bank_details']['pending_emi_amount'], language)
        due_date_spoken = MultilingualScriptTemplates.format_date_for_speech(customer_data['bank_details']['due_date'], language)
        loan_type = customer_data['bank_details']['loan_type']
        
        from datetime import datetime
        due = datetime.strptime(customer_data['bank_details']['due_date'], "%Y-%m-%d")
        is_overdue = due < datetime.now()
        
        scripts = MultilingualScriptTemplates.EMI_SCRIPTS[lang_key]
        template = scripts['overdue'] if is_overdue else scripts['current']
        
        return template.format(loan_type=loan_type, amount=amount, due_date_spoken=due_date_spoken)