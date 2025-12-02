import google.generativeai as genai
from config import Config
from multilingual_script_templates import MultilingualScriptTemplates
import json

class GeminiService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def _get_system_prompt(self, customer_data, language):
        bank_name = Config.BANK_NAME
        name = customer_data.get('name', 'Customer')
        amount = MultilingualScriptTemplates.format_amount(customer_data['bank_details']['pending_emi_amount'], language)
        due_date = customer_data['bank_details']['due_date']
        
        # --- DYNAMIC LANGUAGE INSTRUCTION ---
        if language == 'en':
            lang_instruction = """
            LANGUAGE: ENGLISH ONLY.
            - Speak pure, professional English.
            - DO NOT use Hindi words.
            """
            negotiate_example = '"Sir, when can we expect the payment?"'
            closing_example = '"Thank you for your time. Have a good day."'
            
        elif language == 'hi':
            lang_instruction = """
            LANGUAGE: HINDI ONLY (Male Grammar).
            - Use clear Hindi.
            - CRITICAL: Use MASCULINE grammar (Male).
            - CORRECT: "Main karunga", "Main aaunga", "Samajh sakta hoon".
            - WRONG: "Main karungi", "Aungi", "Sakti hoon".
            """
            negotiate_example = '"Sir, payment kab tak ho payega?"'
            closing_example = '"Samay dene ke liye shukriya. Aapka din shubh ho."'
            
        else: # en-hi-hybrid
            lang_instruction = """
            LANGUAGE: HINGLISH (Male Grammar).
            - Mix Hindi and English naturally.
            - CRITICAL: Use MASCULINE grammar (Male).
            - CORRECT: "Main check karta hoon", "Call karunga".
            - WRONG: "Karti hoon", "Karungi".
            """
            negotiate_example = '"Sir, payment kab tak ho payega?"'
            closing_example = '"Time dene ke liye shukriya. Have a good day."'

        return f"""
        ROLE: You are 'Amit', a SENIOR Recovery Agent for {bank_name}.
        
        IDENTITY:
        - Name: Amit.
        - Gender: MALE.
        - Tone: Firm, Professional, Authoritative.
        
        CRITICAL INSTRUCTIONS:
        1. {lang_instruction}
        2. **NUMBERS:** Write amounts in WORDS (e.g. {amount}) inside the sentence.
        
        DATA:
        - Customer: {name}
        - Due: {amount} (Pronounced exactly as written)
        - Date: {due_date}
        
        FLOW:
        1. **Negotiate**: Get a date. Example: {negotiate_example}
        2. **Solution**: Secure a commitment.
        3. **Closing**: Example: {closing_example}

        OUTPUT JSON:
        {{
            "intent": "INTENT",
            "response_text": "Spoken text...",
            "next_state": "CONVERSATION" or "HANGUP" or "PENDING_TRANSFER",
            "commitment_date": "YYYY-MM-DD"
        }}

        VALID INTENTS:
        WILL_PAY_NOW, WILL_PAY_LATER, CANT_PAY_REFUSAL, DISPUTE_AMOUNT, 
        ALREADY_PAID, DEMANDS_SUPERVISOR, BUSY_CALLBACK_LATER, WRONG_NUMBER, 
        UNCLEAR, POLITE_EXIT, DRIVING_SAFETY, SEND_WHATSAPP, SILENCE, ASK_IF_AVAILABLE
        """

    def get_bot_response(self, call_state, customer_response, customer_data, conversation_history, language='en'):
        # --- IMPROVED LOGGING ---
        print(f"\n[GEMINI] 🗣️  User Said: '{customer_response}'") 
        
        # GUARDRAIL: Handle Silence/Empty Input
        if not customer_response or not customer_response.strip():
            print("[GEMINI] 🔇 Silence detected. Playing fallback.")
            return {
                "intent": "SILENCE",
                "next_state": "CONVERSATION",
                "polite_bot_response": "Hello? Are you there?",
                "should_transfer": False
            }

        history_text = ""
        for turn in conversation_history[-3:]:
            history_text += f"User: {turn.get('customer_response','')}\nBot: {turn.get('bot_response','')}\n"

        prompt = f"""
        {self._get_system_prompt(customer_data, language)}
        
        HISTORY:
        {history_text}
        
        USER SAID: "{customer_response}"
        
        Generate JSON response:
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            result = json.loads(response.text)
            
            print(f"[GEMINI] 🤖 Intent: {result.get('intent')} | Response: {result.get('response_text')}\n")

            # Post-processing overrides
            intent = result.get('intent', 'UNCLEAR')
            next_state = result.get('next_state', 'CONVERSATION')
            
            if intent in ['WRONG_NUMBER', 'POLITE_EXIT']:
                next_state = 'HANGUP'
            
            return {
                "intent": intent,
                "next_state": next_state,
                "polite_bot_response": result.get('response_text', "Sorry, I missed that."),
                "should_transfer": next_state == 'PENDING_TRANSFER',
                "context": {"commitment_date": result.get('commitment_date')}
            }
        except Exception as e:
            print(f"[GEMINI ERROR] {e}")
            return {"intent": "ERROR", "next_state": "CONVERSATION", "polite_bot_response": "Hello? Can you hear me?", "should_transfer": False}

    def analyze_verification(self, customer_response, customer_data, language='en'):
        print(f"\n[VERIFY] 🗣️  User Said: '{customer_response}'")
        
        if not customer_response.strip():
             return {"intent": "UNCLEAR", "polite_bot_response": "Hello?", "detected_language": language}
        
        # --- DYNAMIC INSTRUCTION FOR VERIFICATION ---
        if language == 'en':
            verify_instruction = "Generate response in ENGLISH ONLY. Example: 'Thank you.'"
        elif language == 'hi':
            verify_instruction = "Generate response in HINDI (Male grammar). Example: 'Dhanyavad.'"
        else:
            verify_instruction = "Generate response in HINGLISH (Male grammar). Example: 'Shukriya.'"

        prompt = f"""
        Context: Agent Amit asked "Is this {customer_data['name']}?"
        User: "{customer_response}"
        
        Instructions:
        - Classify intent.
        - {verify_instruction}
        
        Output JSON: {{ "intent": "CONFIRMED_IDENTITY" | "DENIED_IDENTITY" | "UNCLEAR" | "ASK_WHO_ARE_YOU", "response_text": "Short response" }}
        """
        try:
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            res = json.loads(response.text)
            print(f"[VERIFY] 🤖 Intent: {res['intent']} | Response: {res['response_text']}\n")
            return {"intent": res['intent'], "polite_bot_response": res['response_text'], "detected_language": language}
        except:
            return {"intent": "UNCLEAR", "polite_bot_response": "Could you confirm your name?", "detected_language": language}

    def generate_verification_script(self, customer_data, bank_name, language='en'):
        return MultilingualScriptTemplates.get_verification_script(language, bank_name, customer_data['name'])

    def generate_emi_details_script(self, customer_data, language='en'):
        return MultilingualScriptTemplates.get_emi_script(language, customer_data)