import json
from unittest.mock import MagicMock

def test_initiate_call_success(client, db, mocker):
    """
    Tests the /api/call/initiate endpoint.
    We use the 'client' (fake Flask) and 'db' (fake MongoDB) fixtures.
    We 'mocker' (patch) the TwilioService.
    """
    
    # 1. Arrange
    # The 'db' fixture in conftest.py already added 'CUST_TEST_001'
    customer_id = "CUST_TEST_001"
    
    # Mock the TwilioService's 'initiate_call' method
    mock_twilio_service = MagicMock()
    mock_twilio_service.initiate_call.return_value = {
        'success': True,
        'call_sid': 'CA_FAKE_SID_123',
        'call_ref': 'CALL_FAKE_REF'
    }
    # Patch the service *instance* that call_routes imports
    mocker.patch('routes.call_routes.twilio_service', mock_twilio_service)
    
    # 2. Act
    # Use the 'client' to simulate a POST request
    response = client.post(
        '/api/call/initiate',
        data=json.dumps({'customer_id': customer_id}),
        content_type='application/json'
    )
    
    # 3. Assert
    assert response.status_code == 200
    
    response_data = response.get_json()
    assert response_data['success'] is True
    assert response_data['call_sid'] == 'CA_FAKE_SID_123'
    
    # Check that our mock service was called correctly
    mock_twilio_service.initiate_call.assert_called_once_with(
        '+15551234567',  # The phone number from our mock DB
        customer_id
    )

def test_initiate_call_no_customer(client, db):
    """
    Tests that the endpoint fails gracefully if the customer_id is wrong.
    """
    # 1. Arrange
    customer_id = "CUST_DOES_NOT_EXIST"
    
    # 2. Act
    response = client.post(
        '/api/call/initiate',
        data=json.dumps({'customer_id': customer_id}),
        content_type='application/json'
    )
    
    # 3. Assert
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Customer not found'