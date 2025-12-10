import google.generativeai as genai
from config import Config
from multilingual_script_templates import MultilingualScriptTemplates
import json
import re
from datetime import datetime

class GeminiService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
    def _log(self, message, icon="🤖"):
        time = datetime.now().strftime("%H:%M:%S")
        print(f"[{time}] [{icon} GEMINI] {message}")

    def _get_system_prompt(self, customer_data, language):
        bank_name = Config.BANK_NAME
        name = customer_data.get('name', 'Customer')
        amount = MultilingualScriptTemplates.format_amount(customer_data['bank_details']['pending_emi_amount'], language)
        due_date = customer_data['bank_details']['due_date']
        
        if language == 'en':
            lang_instruction = """
            LANGUAGE: ENGLISH ONLY.
            - Speak professionally but naturally.
            - Use contractions (e.g., "I'm calling" instead of "I am calling").
            - TONE: Polite, firm, but empathetic.
            - Keep responses under 3 sentences for faster delivery.
            """
            closing_example = '"Thank you for your time. Have a good day."'
            
        elif language == 'hi':
            lang_instruction = """
            LANGUAGE: HINDI (Conversational).
            - Use Devanagari script for Hindi text (नमस्ते, धन्यवाद).
            - TONE: Natural, not robotic.
            - Keep responses under 3 sentences.
            - PRONUNCIATION FIXES (CRITICAL):
              - Write 'मै' (Mai) instead of 'मैं' (Main).
              - Write 'हूं' (Hu) instead of 'हूँ' (Hoon).
            """
            closing_example = '"Samay dene ke liye shukriya. Aapka din shubh ho."'
            
        else:
            lang_instruction = """
            LANGUAGE: HINGLISH (Conversational).
            - Mix Hindi and English naturally.
            - Keep responses under 3 sentences for faster delivery.
            - KEY RULE: Use English for technical terms (Payment, Date, Due, Loan) and Hindi for grammar.
            - PRONUNCIATION FIXES (CRITICAL):
              - Write "Mai" or "मै" instead of "Main".
              - Write "Hu" or "हूं" instead of "Hoon".
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
        4. **BREVITY:** Keep responses SHORT (2-3 sentences max) for real-time streaming.
        
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
        """

    async def get_bot_response_streaming(self, call_state, customer_response, customer_data, conversation_history, language='en'):
        """Streaming version of get_bot_response"""
        print(f"\n{'-'*60}")
        print(f"🗣️  USER SAID: \"{customer_response}\"") 
        print(f"{'-'*60}")
        
        if not customer_response or not customer_response.strip():
            self._log("Silence detected. Playing fallback.")
            return "Hello? Are you there?"

        history_text = ""
        for turn in conversation_history[-2:]:  # Only last 2 for speed
            history_text += f"User: {turn.get('customer_response','')}\nBot: {turn.get('bot_response','')}\n"

        prompt = f"""
        {self._get_system_prompt(customer_data, language)}
        
        HISTORY:
        {history_text}
        
        USER SAID: "{customer_response}"
        
        Generate CONCISE JSON response (max 3 sentences):
        """
        
        try:
            self._log("Streaming response...", icon="🧠")
            
            # Use streaming API
            response = self.model.generate_content(
                prompt, 
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.7,
                    "max_output_tokens": 150  # Limit for faster responses
                },
                stream=True
            )
            
            accumulated_text = ""
            for chunk in response:
                if chunk.text:
                    accumulated_text += chunk.text
            
            result = json.loads(accumulated_text)
            clean_text = result.get('response_text', '').replace('*', '').strip()
            
            self._log(f"Intent: [{result.get('intent')}]")
            print(f"{'-'*60}")
            print(f"💬  BOT: \"{clean_text}\"")
            print(f"{'-'*60}\n")

            return clean_text
            
        except Exception as e:
            self._log(f"ERROR: {e}", icon="❌")
            return "Could you repeat that?"

    def get_bot_response(self, call_state, customer_response, customer_data, conversation_history, language='en'):
        """Non-streaming version (fallback)"""
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
        """
        CRITICAL FIX: Robust language detection that doesn't auto-switch on verification
        """
        print(f"\n{'-'*60}")
        print(f"🗣️  USER SAID (Verification): \"{customer_response}\"")
        print(f"{'-'*60}")
        
        if not customer_response.strip():
             return {"intent": "UNCLEAR", "polite_bot_response": "Hello?", "detected_language": language}
        
        # CRITICAL: Calculate language confidence before making decisions
        def calculate_language_confidence(text):
            """Determine language based on script and common words"""
            text_lower = text.lower()
            
            # Count Devanagari characters
            devanagari_count = len(re.findall(r'[\u0900-\u097F]', text))
            total_chars = len(text.replace(' ', ''))
            
            # Hindi indicators
            hindi_words = ['हां', 'जी', 'हाँ', 'नहीं', 'मैं', 'हूं', 'है', 'था', 'बोल', 'रहा']
            hindi_word_count = sum(1 for word in hindi_words if word in text)
            
            # English indicators (common verification responses)
            english_words = ['yes', 'yeah', 'yep', 'correct', 'right', 'speaking', 'this is', 'myself']
            english_word_count = sum(1 for word in english_words if word in text_lower)
            
            # Hinglish indicators (mixing both)
            has_english = any(c.isascii() and c.isalpha() for c in text)
            has_hindi = devanagari_count > 0
            
            # Decision logic
            if devanagari_count > total_chars * 0.3:  # 30%+ Devanagari = Hindi
                return 'hi', 0.8
            elif hindi_word_count >= 2:  # Multiple Hindi words = Hindi
                return 'hi', 0.7
            elif english_word_count >= 1:  # English verification words = English
                return 'en', 0.8
            elif has_english and has_hindi:  # Mixed = Hinglish
                return 'en-hi-hybrid', 0.6
            elif has_english:  # Only English characters
                return 'en', 0.7
            else:
                return language, 0.3  # Low confidence, keep current
        
        detected_lang, confidence = calculate_language_confidence(customer_response)
        
        self._log(f"Language Detection: {detected_lang} (confidence: {confidence:.2f})", icon="🌐")
        
        # ONLY switch if confidence is HIGH (>0.7) and language is DIFFERENT
        # This prevents false switches on names or unclear audio
        should_switch = (confidence > 0.7 and 
                        detected_lang != language and 
                        detected_lang != 'en-hi-hybrid')
        
        instruction = f"""
        Context: Agent Amit asked "Is this {customer_data['name']}?" in {language.upper()}.
        User responded: "{customer_response}"
        
        TASK:
        1. Determine if user CONFIRMED (yes/correct/हां/जी) or DENIED (no/wrong/नहीं/गलत) their identity.
        2. **CRITICAL**: Keep response SHORT (1-2 words max). DO NOT repeat customer name or long phrases.
        
        RESPONSE RULES (EXACT TEMPLATES):
        - Confirmed + English: "Thank you."
        - Confirmed + Hindi: "धन्यवाद।"
        - Confirmed + Hinglish: "Thank you."
        - Denied + English: "Sorry, wrong number."
        - Denied + Hindi: "क्षमा करें, गलत नंबर।"
        - Unclear: "Could you confirm your name?"
        
        **DO NOT auto-detect language for switching.** Use the current session language: {language}
        
        Output JSON:
        {{
            "intent": "CONFIRMED_IDENTITY" | "DENIED_IDENTITY" | "UNCLEAR",
            "response_text": "Exact template from above (1-2 words)",
            "notes": "Brief explanation"
        }}
        """

        prompt = instruction
        
        try:
            self._log("Analyzing Verification...", icon="🔍")
            response = self.model.generate_content(
                prompt, 
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.3  # Lower temperature for more consistent verification
                }
            )
            res = json.loads(response.text)
            
            intent = res.get('intent', 'UNCLEAR')
            response_text = res.get('response_text', '').strip()
            
            self._log(f"Verification: {intent} | Confidence: {confidence:.2f}")
            
            # ONLY return detected_language if we should actually switch
            final_detected_lang = detected_lang if should_switch else language
            
            if should_switch:
                self._log(f"⚠️  Language switch recommended: {language} → {detected_lang}", icon="🔀")
            else:
                self._log(f"✓ Language maintained: {language}", icon="🔒")
            
            print(f"💬  BOT RESPONSE: \"{response_text}\"")
            print(f"{'-'*60}\n")
            
            return {
                "intent": intent,
                "polite_bot_response": response_text,
                "detected_language": final_detected_lang,
                "switch_language_to": None,
                "confidence": confidence
            }
        except Exception as e:
            self._log(f"Verification Error: {e}", icon="❌")
            return {
                "intent": "UNCLEAR", 
                "polite_bot_response": "Could you confirm your name?", 
                "detected_language": language,
                "confidence": 0.0
            }

    def generate_verification_script(self, customer_data, bank_name, language='en'):
        return MultilingualScriptTemplates.get_verification_script(language, bank_name, customer_data['name'])

    def generate_emi_details_script(self, customer_data, language='en'):
        return MultilingualScriptTemplates.get_emi_script(language, customer_data)