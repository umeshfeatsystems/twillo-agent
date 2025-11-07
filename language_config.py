"""
Multi-Lingual Configuration
Centralized language settings for the AI agent
"""

class LanguageConfig:
    """
    Centralized configuration for multi-lingual support.
    Easily extensible for additional languages.
    """
    
    # ============================================
    # SUPPORTED LANGUAGES
    # ============================================
    SUPPORTED_LANGUAGES = {
        'en': {
            'name': 'English',
            'code': 'en',
            'locale': 'en-IN',
            'voice': 'Polly.Aditi',
            'alt_voice': 'Polly.Raveena',
            'stt_language': 'en-IN',
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
            'voice': 'Polly.Aditi',
            'alt_voice': 'Polly.Kajal',
            'stt_language': 'hi-IN',
            'speech_hints': (
                'हां, नहीं, बोल रहा हूं, भुगतान, पे करूंगा, कल, आज, '
                'मैनेजर, सुपरवाइजर, मदद, समय, विवाद, '
                'अभी भर रही, कर रहा, पहले ही किया, नौकरी चली गई, '
                'yes, no, payment, pay, abhi, kal, already, help'
            )
        }
    }
    
    # Default language if none selected
    DEFAULT_LANGUAGE = 'en'
    
    # ============================================
    # IVR MENU CONFIGURATION
    # ============================================
    IVR_MENU = {
        'timeout': 5,
        'num_digits': 1,
        'finish_on_key': '',
        'language_map': {
            '1': 'hi',
            '2': 'en'
        }
    }
    
    # ============================================
    # IVR WELCOME MESSAGE (Bilingual)
    # ============================================
    IVR_WELCOME_MESSAGE = (
        # Hindi first
        "नमस्ते। हिंदी में जारी रखने के लिए एक दबाएं। "
        # English
        "Hello. Press one for Hindi. Press two for English. "
        # Repeat in Hindi
        "अंग्रेज़ी के लिए दो दबाएं।"
    )
    
    # Shorter version for repeat prompts
    IVR_REPEAT_MESSAGE = (
        "हिंदी के लिए एक, अंग्रेज़ी के लिए दो। "
        "Press one for Hindi, two for English."
    )
    
    # Invalid selection message
    IVR_INVALID_MESSAGE = (
        "गलत चयन। कृपया फिर से प्रयास करें। "
        "Invalid selection. Please try again."
    )
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    @staticmethod
    def get_language_config(language_code):
        """Get configuration for a specific language"""
        return LanguageConfig.SUPPORTED_LANGUAGES.get(
            language_code, 
            LanguageConfig.SUPPORTED_LANGUAGES[LanguageConfig.DEFAULT_LANGUAGE]
        )
    
    @staticmethod
    def get_voice(language_code):
        """Get TTS voice for a language"""
        config = LanguageConfig.get_language_config(language_code)
        return config['voice']
    
    @staticmethod
    def get_stt_config(language_code):
        """Get STT configuration for a language"""
        config = LanguageConfig.get_language_config(language_code)
        return {
            'language': config['stt_language'],
            'hints': config['speech_hints']
        }
    
    @staticmethod
    def is_valid_language(language_code):
        """Check if language code is supported"""
        return language_code in LanguageConfig.SUPPORTED_LANGUAGES
    
    @staticmethod
    def get_language_from_digit(digit):
        """Convert IVR digit input to language code"""
        return LanguageConfig.IVR_MENU['language_map'].get(digit)