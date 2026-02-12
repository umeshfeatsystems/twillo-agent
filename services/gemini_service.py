import google.generativeai as genai
from config import Config
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GeminiService")

class GeminiService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def get_streaming_response(self, system_prompt, conversation_history, user_input):
        """
        Streams text chunks immediately. 
        Forces Plain Text mode for lowest latency.
        """
        # 1. Format History
        history_text = ""
        for turn in conversation_history[-6:]:
            role = "User" if turn['role'] == 'user' else "AI"
            history_text += f"{role}: {turn['content']}\n"

        # 2. Prompt - Explicitly ask for TEXT, not JSON
        streaming_prompt = f"""
        {system_prompt}
        
        INSTRUCTIONS: 
        - IGNORE all previous instructions about JSON format.
        - Reply naturally in plain text.
        - Keep it under 2 sentences.
        
        --- HISTORY ---
        {history_text}
        User: "{user_input}"
        """

        try:
            # 3. Stream = True
            response_stream = self.model.generate_content(
                streaming_prompt, 
                stream=True, 
                generation_config={
                    "response_mime_type": "text/plain", 
                    "max_output_tokens": 250,
                    "temperature": 0.3
                }
            )
            
            # 4. Yield text as it arrives
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Gemini Streaming Error: {e}")
            yield "I didn't catch that."

gemini_service = GeminiService()