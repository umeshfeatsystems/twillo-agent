class LanguageConfig:
    # Voice to use when in Hybrid mode (Male Voice - Amit)
    # Using Sadaltager (Male) as the SINGLE unified voice for consistency
    HYBRID_VOICE_NAME = 'en-IN-Chirp3-HD-Sadaltager'
    
    SUPPORTED_LANGUAGES = {
        'en': {
            'name': 'English',
            'code': 'en',
            'locale': 'en-IN',
            # Male English Voice
            'google_voice': 'en-IN-Chirp3-HD-Sadaltager',
            'google_language': 'en-IN',
            'stt_language': 'en-IN',
            'speaking_rate': 1.05,
            'speech_hints': 'yes, no, payment, pay, manager, busy, later, wrong number'
        },
        'hi': {
            'name': 'Hindi',
            'code': 'hi',
            'locale': 'hi-IN',
            # CRITICAL FIX: Use the SAME Male voice as English to prevent gender flipping.
            # Google's "en-IN" Chirp models can speak Hindi perfectly.
            'google_voice': 'en-IN-Chirp3-HD-Sadaltager', 
            'google_language': 'en-IN', # Must match the voice's language code
            'stt_language': 'hi-IN',    # STT can still use Hindi model for better recognition
            'speaking_rate': 1.05,
            'speech_hints': 'haan, nahi, paisa, payment, busy, baad mein, galat number'
        },
        'en-hi-hybrid': {
            'name': 'Hybrid',
            'code': 'en-hi-hybrid',
            'locale': 'en-IN',
            # Male Voice
            'google_voice': 'en-IN-Chirp3-HD-Sadaltager', 
            'google_language': 'en-IN',
            'stt_language': 'en-IN', 
            'speaking_rate': 1.0,
            'speech_hints': 'haan, yes, payment, pay, busy, later, call back, wrong number'
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
    def get_tts_config(language_code):
        # Always use the specific config to ensure the correct voice map is used
        if language_code not in LanguageConfig.SUPPORTED_LANGUAGES:
             config = LanguageConfig.SUPPORTED_LANGUAGES['en-hi-hybrid']
        else:
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