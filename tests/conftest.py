import pytest
import mongomock
from unittest.mock import patch

# --- FIX: Add project root to Python's path ---
import sys
import os
# This line tells pytest to look one directory up (..) from the 'tests' folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# --- END FIX ---

# 1. Create a fake MongoDB instance
mock_db_client = mongomock.MongoClient()
mock_db = mock_db_client['test_db'] 

# 2. Define the patch, but DO NOT start it yet.
db_patch = patch('utils.db.db_instance.get_db', return_value=mock_db)

# 3. Import our app (this is safe to do now *because* of the path fix)
from app import create_app
from models.customer import Customer
from utils.db import db_instance # Import db_instance to use in fixtures

@pytest.fixture(scope='module')
def app():
    """Create a new app instance for each test module."""
    
    # Start the patch *inside* the fixture
    db_patch.start()
    
    # Set up a test config
    app = create_app()
    app.config.update({
        "TESTING": True,
        "MONGODB_URI": "mongodb://localhost:27017/test_db",  # Use a test URI
        "GEMINI_API_KEY": "fake-key",
        "TWILIO_ACCOUNT_SID": "fake-sid",
        "TWILIO_AUTH_TOKEN": "fake-token",
        "TWILIO_PHONE_NUMBER": "+1234567890",
        "AGENT_PHONE_NUMBER": "+0987654321",
        "BANK_NAME": "Test Bank"
    })
    
    # We must stop the patch at the end
    yield app
    
    # Stop the patch after the tests are done
    db_patch.stop()


@pytest.fixture(scope='module')
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    """A fixture to get the mock DB and clear it after each test."""
    # This db_instance.get_db() call will be *patched*
    db = db_instance.get_db() 
    
    # Setup: Add a fake customer
    Customer.get_collection().insert_one({
        "customer_id": "CUST_TEST_001",
        "name": "Test Customer",
        "phone": "+15551234567",
        "bank_details": {
            "pending_emi_amount": 5000,
            "due_date": "2025-11-01",
            "loan_type": "Test Loan"
        },
        "call_history": []
    })
    
    yield db
    
    # Teardown: Clear all collections after each test
    for collection in db.list_collection_names():
        db[collection].delete_many({})