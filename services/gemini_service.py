import logging

import google.generativeai as genai

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GeminiService")


class GeminiService:
    def __init__(self):
        self.model = None
        try:
            if not Config.GEMINI_API_KEY:
                logger.warning("Gemini API key missing. LLM responses will be unavailable.")
                return
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        except Exception as exc:
            logger.error("Gemini initialization failed: %s", exc)
            self.model = None

    def get_streaming_response(self, system_prompt, conversation_history, user_input):
        """
        Streams text chunks immediately and keeps responses concise for voice calls.
        """
        if not self.model:
            yield "I am having trouble connecting right now. Please try again."
            return

        history_text = ""
        for turn in conversation_history[-4:]:
            role = "User" if turn["role"] == "user" else "AI"
            history_text += f"{role}: {turn['content']}\n"

        streaming_prompt = f"""
        {system_prompt}
        
        INSTRUCTIONS: 
        - Reply naturally in plain text.
        - Keep it under 2 sentences.
        - Think step-by-step internally, but never reveal internal reasoning.
        
        --- HISTORY ---
        {history_text}
        User: "{user_input}"
        """

        try:
            response_stream = self.model.generate_content(
                streaming_prompt,
                stream=True,
                generation_config={
                    "response_mime_type": "text/plain",
                    "max_output_tokens": 120,
                    "temperature": 0.2,
                },
            )

            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

        except Exception as exc:
            logger.error("Gemini streaming error: %s", exc)
            yield "I did not catch that."


gemini_service = GeminiService()
