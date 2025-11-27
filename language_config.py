class LanguageConfig:
    SUPPORTED_LANGUAGES = {
        'en': {
            'name': 'English',
            'code': 'en',
            'locale': 'en-IN',
            'google_voice': 'en-IN-Chirp3-HD-Enceladus',
            'google_language': 'en-IN',
            'stt_language': 'en-IN',
            'speaking_rate': 0.95,  # <-- This was added
            'speech_hints': (
                'yes, no, speaking, payment, pay, tomorrow, today, later, '
                'manager, supervisor, help, extension, dispute, haan, ha, nahi, '
                'paying now, will pay, already paid, financial problem, job lost'
            )
        },
        'hi': {
            'name': 'Hindi',
            'code': 'hi',
            'locale': 'hi-IN',
            'google_voice': 'hi-IN-Chirp3-HD-Aoede',
            'google_language': 'hi-IN',
            'stt_language': 'hi-IN',
            'speaking_rate': 0.95,  # <-- This was added
            'speech_hints': (
                'हां, नहीं, बोल रहा हूं, भुगतान, पे करूंगा, कल, आज, '
                'मैनेजर, सुपरवाइजर, मदद, समय, विवाद, '
                'अभी भर रही, कर रहा, पहले ही किया, नौकरी चली गई, '
                'yes, no, payment, pay, abhi, kal, already, help'
            )
        }
    }
    
    DEFAULT_LANGUAGE = 'en'
    
    IVR_MENU = {
        'timeout': 5,
        'num_digits': 1,
        'finish_on_key': '',
        'language_map': {
            '1': 'hi',
            '2': 'en'
        }
    }
    
    IVR_WELCOME_MESSAGE = (
        "नमस्ते। हिंदी में जारी रखने के लिए एक दबाएं। "
        "Hello. Press one for Hindi. Press two for English. "
        "अंग्रेज़ी के लिए दो दबाएं।"
    )
    
    IVR_REPEAT_MESSAGE = (
        "हिंदी के लिए एक, अंग्रेज़ी के लिए दो। "
        "Press one for Hindi, two for English."
    )
    
    IVR_INVALID_MESSAGE = (
        "गलत चयन। कृपया फिर से प्रयास करें। "
        "Invalid selection. Please try again."
    )
    
    @staticmethod
    def get_language_config(language_code):
        return LanguageConfig.SUPPORTED_LANGUAGES.get(
            language_code, 
            LanguageConfig.SUPPORTED_LANGUAGES[LanguageConfig.DEFAULT_LANGUAGE]
        )
    
    @staticmethod
    def get_voice(language_code):
        """Get Google Cloud TTS voice name"""
        config = LanguageConfig.get_language_config(language_code)
        return config['google_voice']

    # --- THIS IS THE MISSING METHOD ---
    @staticmethod
    def get_tts_config(language_code):
        """Get full configuration for Text-to-Speech"""
        config = LanguageConfig.get_language_config(language_code)
        return {
            'language_code': config['google_language'],
            'voice_name': config['google_voice'],
            'speaking_rate': config['speaking_rate']
        }
    # --- END OF MISSING METHOD ---
    
    @staticmethod
    def get_stt_config(language_code):
        """Get speech-to-text configuration"""
        config = LanguageConfig.get_language_config(language_code)
        return {
            'language': config['stt_language'],
            'hints': config['speech_hints']
        }
    
    @staticmethod
    def is_valid_language(language_code):
        return language_code in LanguageConfig.SUPPORTED_LANGUAGES
    
    @staticmethod
    def get_language_from_digit(digit):
        return LanguageConfig.IVR_MENU['language_map'].get(digit)