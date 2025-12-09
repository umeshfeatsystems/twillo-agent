import google.generativeai as genai
from config import Config
from multilingual_script_templates import MultilingualScriptTemplates
import json
import re
from datetime import datetime

class GeminiService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def _log(self, message, icon="🤖"):
        time = datetime.now().strftime("%H:%M:%S")
        print(f"[{time}] [{icon} GEMINI] {message}")

    def _get_system_prompt(self, customer_data, language):
        bank_name = Config.BANK_NAME
        name = customer_data.get('name', 'Customer')
        amount = MultilingualScriptTemplates.format_amount(customer_data['bank_details']['pending_emi_amount'], language)
        due_date = customer_data['bank_details']['due_date']
        
        # --- DYNAMIC LANGUAGE INSTRUCTION ---
        if language == 'en':
            lang_instruction = """
            LANGUAGE: ENGLISH ONLY.
            - Speak professionally but naturally.
            - Use contractions (e.g., "I'm calling" instead of "I am calling").
            - TONE: Polite, firm, but empathetic.
            """
            closing_example = '"Thank you for your time. Have a good day."'
            
        elif language == 'hi':
            lang_instruction = """
            LANGUAGE: HINDI (Conversational).
            - Use Devanagari script for Hindi text (नमस्ते, धन्यवाद).
            - TONE: Natural, not robotic.
            - PRONUNCIATION FIXES (CRITICAL):
              - Write 'मै' (Mai) instead of 'मैं' (Main).
              - Write 'हूँ' (Hu) instead of 'हूँ' (Hoon).
            """
            closing_example = '"Samay dene ke liye shukriya. Aapka din shubh ho."'
            
        else: # en-hi-hybrid
            lang_instruction = """
            LANGUAGE: HINGLISH (Conversational).
            - Mix Hindi and English naturally.
            - KEY RULE: Use English for technical terms (Payment, Date, Due, Loan) and Hindi for grammar.
            - PRONUNCIATION FIXES (CRITICAL):
              - Write "Mai" or "मै" instead of "Main".
              - Write "Hu" or "हूँ" instead of "Hoon".
              - Use "Ji" with names (e.g., "Umesh ji").
            """
            closing_example = '"Time dene ke liye shukriya. Have a good day."'

        return f"""
        ROLE: You are 'Amit', a SENIOR Recovery Agent for {bank_name}.
        
        IDENTITY:
        - Name: Amit.
        - Gender: MALE.
        - Tone: Firm but Polite, Professional.
        
        CRITICAL INSTRUCTIONS:
        1. {lang_instruction}
        2. **NUMBERS:** Write amounts in WORDS (e.g. {amount}) inside the sentence.
        3. **PACING:** Use commas (,) and periods (.) frequently to create natural breathing pauses.
        
        DATA:
        - Customer: {name}
        - Due: {amount} (Pronounced exactly as written)
        - Date: {due_date}
        
        FLOW:
        1. **Negotiate**: Get a date.
        2. **Solution**: Secure a commitment.
        3. **Closing**: Example: {closing_example}

        OUTPUT JSON:
        {{
            "intent": "INTENT",
            "response_text": "Spoken text...",
            "next_state": "CONVERSATION" or "HANGUP" or "PENDING_TRANSFER",
            "commitment_date": "YYYY-MM-DD",
            "switch_language_to": "en" | "hi" | null 
        }}

        VALID INTENTS:
        WILL_PAY_NOW, WILL_PAY_LATER, CANT_PAY_REFUSAL, DISPUTE_AMOUNT, 
        ALREADY_PAID, DEMANDS_SUPERVISOR, BUSY_CALLBACK_LATER, WRONG_NUMBER, 
        UNCLEAR, POLITE_EXIT, DRIVING_SAFETY, SEND_WHATSAPP, SILENCE, ASK_IF_AVAILABLE,
        SWITCH_LANGUAGE
        
        NOTE ON SWITCH_LANGUAGE:
        - If user says "Speak in Hindi" -> intent: SWITCH_LANGUAGE, switch_language_to: "hi"
        - If user speaks PURE English -> intent: SWITCH_LANGUAGE, switch_language_to: "en"
        """

    def get_bot_response(self, call_state, customer_response, customer_data, conversation_history, language='en'):
        print(f"\n{'-'*60}")
        print(f"🗣️  USER SAID: \"{customer_response}\"") 
        print(f"{'-'*60}")
        
        if not customer_response or not customer_response.strip():
            self._log("Silence detected. Playing fallback.")
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
            self._log("Thinking...", icon="🧠")
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            result = json.loads(response.text)
            
            clean_text = result.get('response_text', '').replace('*', '').strip()
            
            self._log(f"Intent Identified: [{result.get('intent')}]")
            if result.get('switch_language_to'):
                 self._log(f"Language Switch Triggered: {result.get('switch_language_to')}", icon="🔀")
            
            print(f"{'-'*60}")
            print(f"💬  BOT SCRIPT: \"{clean_text}\"")
            print(f"{'-'*60}\n")

            return {
                "intent": result.get('intent', 'UNCLEAR'),
                "next_state": result.get('next_state', 'CONVERSATION'),
                "polite_bot_response": clean_text,
                "should_transfer": result.get('next_state') == 'PENDING_TRANSFER',
                "switch_language_to": result.get('switch_language_to'),
                "context": {"commitment_date": result.get('commitment_date')}
            }
        except Exception as e:
            self._log(f"ERROR: {e}", icon="❌")
            return {"intent": "ERROR", "next_state": "CONVERSATION", "polite_bot_response": "Can you hear me?", "should_transfer": False}

    def analyze_verification(self, customer_response, customer_data, language='en'):
        print(f"\n{'-'*60}")
        print(f"🗣️  USER SAID (Verification): \"{customer_response}\"")
        print(f"{'-'*60}")
        
        if not customer_response.strip():
             return {"intent": "UNCLEAR", "polite_bot_response": "Hello?", "detected_language": language}
        
        instruction = """
        1. Analyze if the user confirms identity (YES) or denies (NO).
        2. **DETECT LANGUAGE:** - If user speaks Hindi/Hinglish -> "detected_language": "hi"
           - If user speaks English -> "detected_language": "en"
        3. **RESPONSE RULES (Use Exact Scripts for Emotion):**
           - If YES + Hindi/Hybrid: Response = "धन्यवाद।" (Use Devanagari for correct pronunciation).
           - If YES + English: Response = "Thank you."
           - If NO + Hindi/Hybrid: Response = "क्षमा करें, गलत नंबर लग गया।"
           - If NO + English: Response = "Oh, sorry. Wrong number."
           - DO NOT repeat the user's name or words. Keep it short.
        """

        prompt = f"""
        Context: Agent Amit asked "Is this {customer_data['name']}?"
        User: "{customer_response}"
        
        Instructions:
        {instruction}
        
        Output JSON: 
        {{ 
            "intent": "CONFIRMED_IDENTITY" | "DENIED_IDENTITY" | "UNCLEAR" | "SWITCH_LANGUAGE", 
            "response_text": "Exact script from rules", 
            "detected_language": "en" | "hi" | "en-hi-hybrid"
        }}
        """
        try:
            self._log("Analyzing Verification...", icon="🔍")
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            res = json.loads(response.text)
            
            self._log(f"Verification: {res['intent']} | Lang Detected: {res.get('detected_language')}")
            print(f"💬  BOT RESPONSE: \"{res['response_text']}\"")
            print(f"{'-'*60}\n")
            
            return {
                "intent": res['intent'], 
                "polite_bot_response": res.get('response_text', ''), 
                "detected_language": res.get('detected_language', language),
                "switch_language_to": None
            }
        except:
            return {"intent": "UNCLEAR", "polite_bot_response": "Could you confirm your name?", "detected_language": language}

    def generate_verification_script(self, customer_data, bank_name, language='en'):
        return MultilingualScriptTemplates.get_verification_script(language, bank_name, customer_data['name'])

    def generate_emi_details_script(self, customer_data, language='en'):
        return MultilingualScriptTemplates.get_emi_script(language, customer_data)