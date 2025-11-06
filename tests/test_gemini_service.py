import json
from unittest.mock import MagicMock
from services.gemini_service import GeminiService

def test_analyze_verification_confirms(mocker):
    """
    Tests that the verification analyzer correctly parses a 'CONFIRMED' intent.
    We 'mocker' (patch) the Gemini API call itself.
    """
    # 1. Arrange
    # This is the fake JSON string Gemini will "return"
    fake_gemini_response_text = """
    {
        "intent": "CONFIRMED_IDENTITY",
        "polite_bot_response": "Test: Great, thank you."
    }
    """
    
    # Mock the Gemini model's response chain
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = fake_gemini_response_text
    mock_model.generate_content.return_value = mock_response
    
    # Patch the 'fast_model' inside the service
    mocker.patch.object(GeminiService, 'fast_model', mock_model)
    
    service = GeminiService()
    customer_data = {"name": "Test Customer"}
    
    # 2. Act
    result = service.analyze_verification("Yes, this is him", customer_data)
    
    # 3. Assert
    assert result['intent'] == "CONFIRMED_IDENTITY"
    assert result['polite_bot_response'] == "Test: Great, thank you."
    
    # Bonus: Check that the API was called
    mock_model.generate_content.assert_called_once()