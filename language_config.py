class LanguageConfig:
    SUPPORTED_LANGUAGES = {
        'en': {
            'name': 'English',
            'code': 'en',
            'locale': 'en-IN',
            'google_voice': 'en-IN-Chirp3-HD-Vindemiatrix',
            'google_language': 'en-IN',
            'stt_language': 'en-IN',
            'speaking_rate': 0.9,
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
            'speaking_rate': 0.95,
            'speech_hints': (
                'हां, नहीं, बोल रहा हूं, भुगतान, पे करूंगा, कल, आज, '
                'मैनेजर, सुपरवाइजर, मदद, समय, विवाद, '
                'अभी भर रही, कर रहा, पहले ही किया, नौकरी चली गई, '
                'yes, no, payment, pay, abhi, kal, already, help'
            )
        },
        # --- NEW HYBRID PROFILE ---
        'en-hi-hybrid': {
            'name': 'Hybrid (Hinglish)',
            'code': 'en-hi-hybrid',
            'locale': 'en-IN',
            # Default to English voice for initial greeting
            'google_voice': 'en-IN-Chirp3-HD-Vindemiatrix', 
            'google_language': 'en-IN',
            # Use English STT model as base, but heavily bias with Hindi words
            'stt_language': 'en-IN', 
            'speaking_rate': 0.9,
            'speech_hints': (
                'yes, no, speaking, payment, pay, tomorrow, today, later, '
                'manager, supervisor, help, extension, dispute, '
                'haan, ha, nahi, abhi, kal, aaj, bhar dunga, dungi, '
                'paying now, will pay, already paid, financial problem, job lost, '
                'main bol raha hun, kya hai, kaisa hai, thik hai'
            )
        }
    }
    
    DEFAULT_LANGUAGE = 'en-hi-hybrid'
    
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

    @staticmethod
    def get_tts_config(language_code):
        """Get full configuration for Text-to-Speech"""
        # If hybrid is passed here (which shouldn't happen for TTS generation, 
        # but just in case), default to English config
        if language_code == 'en-hi-hybrid':
             language_code = 'en'
             
        config = LanguageConfig.get_language_config(language_code)
        return {
            'language_code': config['google_language'],
            'voice_name': config['google_voice'],
            'speaking_rate': config['speaking_rate']
        }
    
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