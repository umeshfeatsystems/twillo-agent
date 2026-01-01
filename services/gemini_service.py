import google.generativeai as genai
from config import Config
import json

class GeminiService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def get_generic_response(self, system_prompt, conversation_history, user_input):
        # 1. Format History
        history_text = ""
        for turn in conversation_history[-6:]:
            role = "User" if turn['role'] == 'user' else "AI"
            history_text += f"{role}: {turn['content']}\n"

        # 2. Build Prompt
        full_prompt = f"""
        {system_prompt}

        --- HISTORY ---
        {history_text}
        User: "{user_input}"
        """

        try:
            response = self.model.generate_content(
                full_prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Gemini Error: {e}")
            return {"response_text": "I didn't catch that.", "should_hangup": False}

gemini_service = GeminiService()