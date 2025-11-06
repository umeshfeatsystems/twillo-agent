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
        "name": "Rajesh Kumar",
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
    },
    {
        "customer_id": "CUST002",
        "name": "Priya Sharma",
        "phone": "+918097031280",  # ← REPLACE with another verified number
        "email": "priya.sharma@example.com",
        "bank_details": {
            "account_number": "2345678901",
            "loan_id": "LOAN23456",
            "pending_emi_amount": 8500,
            "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "emi_count": 12,
            "total_emis": 24,
            "loan_type": "Car Loan"
        },
        "call_history": [
            {
                "call_id": "CA001",
                "timestamp": (datetime.now() - timedelta(days=30)).isoformat(),
                "status": "completed",
                "duration": 65,
                "outcome": "WILL_PAY_LATER",
                "transcription": "I will pay by next week",
                "intent": "WILL_PAY_LATER",
                "next_action": "follow_up_scheduled"
            }
        ],
        "preferences": {
            "preferred_language": "en-IN",
            "preferred_call_time": "14:00-20:00"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "customer_id": "CUST003",
        "name": "Amit Patel",
        "phone": "+918097031280",  # ← REPLACE with another verified number
        "email": "amit.patel@example.com",
        "bank_details": {
            "account_number": "3456789012",
            "loan_id": "LOAN34567",
            "pending_emi_amount": 25000,
            "due_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),  # OVERDUE!
            "emi_count": 8,
            "total_emis": 60,
            "loan_type": "Personal Loan"
        },
        "call_history": [
            {
                "call_id": "CA002",
                "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
                "status": "completed",
                "duration": 120,
                "outcome": "FACING_ISSUES",
                "transcription": "I lost my job, need more time",
                "intent": "FACING_ISSUES",
                "next_action": "escalate_to_support"
            }
        ],
        "preferences": {
            "preferred_language": "en-IN",
            "preferred_call_time": "09:00-12:00"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "customer_id": "CUST004",
        "name": "Sneha Reddy",
        "phone": "+918097031280",  # ← REPLACE with another verified number
        "email": "sneha.reddy@example.com",
        "bank_details": {
            "account_number": "4567890123",
            "loan_id": "LOAN45678",
            "pending_emi_amount": 12000,
            "due_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "emi_count": 18,
            "total_emis": 36,
            "loan_type": "Education Loan"
        },
        "call_history": [],
        "preferences": {
            "preferred_language": "en-IN",
            "preferred_call_time": "16:00-21:00"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "customer_id": "CUST005",
        "name": "Vikram Singh",
        "phone": "+918097031280",  # ← REPLACE with another verified number
        "email": "vikram.singh@example.com",
        "bank_details": {
            "account_number": "5678901234",
            "loan_id": "LOAN56789",
            "pending_emi_amount": 18500,
            "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),  # URGENT!
            "emi_count": 5,
            "total_emis": 48,
            "loan_type": "Business Loan"
        },
        "call_history": [
            {
                "call_id": "CA003",
                "timestamp": (datetime.now() - timedelta(days=15)).isoformat(),
                "status": "completed",
                "duration": 45,
                "outcome": "ALREADY_PAID",
                "transcription": "I already paid yesterday",
                "intent": "ALREADY_PAID",
                "next_action": "verify_payment"
            },
            {
                "call_id": "CA004",
                "timestamp": (datetime.now() - timedelta(days=45)).isoformat(),
                "status": "completed",
                "duration": 80,
                "outcome": "WILL_PAY_NOW",
                "transcription": "Will pay immediately",
                "intent": "WILL_PAY_NOW",
                "next_action": "payment_link_sent"
            }
        ],
        "preferences": {
            "preferred_language": "en-IN",
            "preferred_call_time": "10:00-17:00"
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