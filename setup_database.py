from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/emi_call_agent')
client = MongoClient(MONGODB_URI)
db = client.get_default_database()

# Drop existing customers collection (for fresh start)
db.customers.drop()
print("✓ Cleared existing customers")

# 5 Sample Customers with diverse scenarios
customers = [
    {
        "customer_id": "CUST001",
        "name": "Umesh Tiwari",
        "phone": "+918097031280",  # ← REPLACE with your verified Twilio number
        "email": "rajesh.kumar@example.com",
        "bank_details": {
            "account_number": "1234567890",
            "loan_id": "LOAN12345",
            "pending_emi_amount": 15000,
            "due_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "emi_count": 3,
            "total_emis": 36,
            "loan_type": "Home Loan"
        },
        "call_history": [],
        "preferences": {
            "preferred_language": "en-IN",
            "preferred_call_time": "10:00-18:00"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

# Insert all customers
result = db.customers.insert_many(customers)
print(f"✓ Inserted {len(result.inserted_ids)} customers")

# Display inserted customers
print("\n" + "="*60)
print("📊 CUSTOMER DATABASE SUMMARY")
print("="*60)

for customer in db.customers.find():
    print(f"\n👤 {customer['name']} ({customer['customer_id']})")
    print(f"   📞 Phone: {customer['phone']}")
    print(f"   💰 Pending: ₹{customer['bank_details']['pending_emi_amount']}")
    print(f"   📅 Due: {customer['bank_details']['due_date']}")
    print(f"   🎯 Loan: {customer['bank_details']['loan_type']}")
    print(f"   📝 Call History: {len(customer['call_history'])} calls")

print("\n" + "="*60)
print("✅ Database setup complete!")
print("="*60)
print("\n💡 Note: Verification has been removed - bot will start conversation directly")

# Close connection
client.close()