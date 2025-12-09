from utils.db import db_instance
from models.customer import Customer
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SEED")

def seed_data():
    # 1. Connect to DB
    logger.info("Connecting to Database...")
    db_instance.connect()
    
    # 2. Define Dummy Customer
    customer_data = {
        "customer_id": "test_user_1",
        "name": "Rohan Sharma",
        "phone": "+918097031280",  # <--- REPLACE WITH YOUR REAL PHONE NUMBER TO TEST
        "bank_details": {
            "bank_name": "HDFC Bank",
            "account_no": "XXXX-1234",
            "pending_emi_amount": 15000
        },
        "call_history": []
    }

    # 3. Check if exists, otherwise insert
    collection = Customer.get_collection()
    existing = collection.find_one({"customer_id": customer_data["customer_id"]})
    
    if existing:
        logger.info(f"Customer {customer_data['customer_id']} already exists. Updating...")
        collection.update_one(
            {"customer_id": customer_data["customer_id"]}, 
            {"$set": customer_data}
        )
    else:
        logger.info(f"Creating new customer: {customer_data['customer_id']}")
        collection.insert_one(customer_data)
    
    logger.info("✅ Database seeded successfully!")

if __name__ == "__main__":
    seed_data()