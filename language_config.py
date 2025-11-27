class LanguageConfig:
    # Voice to use when in Hybrid mode (Fixed Female Voice)
    HYBRID_VOICE_NAME = 'en-IN-Chirp3-HD-Laomedeia'
    
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
                'paying now, will pay, already paid, financial problem, job lost, '
                'whatsapp, message, driving, busy, wrong number, robot, human'
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
                'yes, no, payment, pay, abhi, kal, already, help, '
                'whatsapp, message, driving, busy, galat number, robot, insaan'
            )
        },
        'en-hi-hybrid': {
            'name': 'Hybrid (Hinglish)',
            'code': 'en-hi-hybrid',
            'locale': 'en-IN',
            'google_voice': 'en-IN-Chirp3-HD-Laomedeia', 
            'google_language': 'en-IN',
            'stt_language': 'en-IN', 
            'speaking_rate': 0.9,
            'speech_hints': (
                'yes, no, speaking, payment, pay, tomorrow, today, later, '
                'manager, supervisor, help, extension, dispute, '
                'haan, ha, nahi, abhi, kal, aaj, bhar dunga, dungi, '
                'paying now, will pay, already paid, financial problem, job lost, '
                'main bol raha hun, kya hai, kaisa hai, thik hai, '
                'whatsapp, bhejo, driving, busy, wrong number, galat number'
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
        config = LanguageConfig.get_language_config(language_code)
        return config['google_voice']

    @staticmethod
    def get_tts_config(language_code):
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
        config = LanguageConfig.get_language_config(language_code)
        return {
            'language': config['stt_language'],
            'hints': config['speech_hints']
        }
    
    @staticmethod
    def is_valid_language(language_code):
        return language_code in LanguageConfig.SUPPORTED_LANGUAGES