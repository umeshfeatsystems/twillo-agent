"""
Test script to initiate a call to a customer.
Run this after starting your Flask app to test the call flow.
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5000"  # Change if using ngrok
CUSTOMER_ID = "CUST001"  # Change to test different customers

def test_initiate_call():
    """Test the call initiation endpoint"""
    
    print("=" * 80)
    print("🧪 TESTING EMI RECOVERY AGENT CALL (v2.2 - Async Flow)")
    print("=" * 80)
    
    # First, check if customer exists
    print(f"\n1. Checking customer {CUSTOMER_ID}...")
    response = requests.get(f"{BASE_URL}/api/call/customers/{CUSTOMER_ID}")
    
    if response.status_code != 200:
        print(f"❌ Customer not found: {response.status_code}")
        print("Run setup_database.py first!")
        return
    
    customer = response.json()
    print(f"✓ Found customer: {customer['name']}")
    print(f"  Phone: {customer['phone']}")
    print(f"  Pending: ₹{customer['bank_details']['pending_emi_amount']}")
    print(f"  Due Date: {customer['bank_details']['due_date']}")
    print(f"  Loan Type: {customer['bank_details']['loan_type']}")
    
    # Initiate call
    print(f"\n2. Initiating recovery call to {customer['name']}...")
    response = requests.post(
        f"{BASE_URL}/api/call/initiate",
        json={"customer_id": CUSTOMER_ID},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"❌ Call initiation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    result = response.json()
    
    if result.get('success'):
        print(f"✓ Call initiated successfully!")
        print(f"  Call SID: {result['call_sid']}")
        print(f"  Call Ref: {result['call_ref']}")
        print(f"\n📞 Your phone should ring in a few seconds...")
        print(f"\n{'=' * 80}")
        print("💡 TESTING SCENARIOS (v2.2) - What to expect:")
        print("=" * 80)

        print("\n🤖 STEP 1: CONNECTING (Bot says 'Please hold...')")
        print("  • You don't need to say anything here.")
        
        print("\n🔐 STEP 2: VERIFICATION (Bot asks 'Am I speaking with...?')")
        print("  • 'Yes, this is him' (Confirms identity and continues to Step 3)")
        print("  • 'Speaking' (Confirms identity)")
        print("  • 'No, this is not Rajesh' (Denies identity, bot will hang up)")
        print("  • 'Wrong number' (Denies identity)")
        print("  • 'What is this about?' (Bot will re-state who it is)")
        
        print("\n🤖 STEP 3: FETCHING DETAILS (Bot says 'One moment...')")
        print("  • This happens *after* you say 'yes'. You don't need to say anything.")
        
        print("\n✅ STEP 4: MAIN CONVERSATION (Bot presents EMI details)")
        print("  • 'I will pay today'")
        print("  • 'I'll make the payment tomorrow'")
        print("  • 'I lost my job last month'")
        print("  • 'Let me speak to your manager' (say twice to trigger transfer)")
        
        print("\n❓ CONFUSION & 'OFFER OPTIONS' FLOW")
        print("  • In Step 4, say something random twice (e.g., 'What about the weather?')")
        print("  • Bot will say: '...you can simply say 'make a payment', 'request help', or 'speak to an agent''")
        print("  • Then say: 'I need to speak to an agent' (Bot will transfer)")
        
        print("\n" + "=" * 80)
        print("📊 RECOVERY AGENT BEHAVIOR (v2.2):")
        print("=" * 80)
        print("  ✓ NEW: Fully Asynchronous (No more timeouts!)")
        print("  ✓ Verifies identity before discussing EMI details")
        print("  ✓ Handles 'not interested' or 'wrong number' professionally")
        print("  ✓ Offers 3 clear options if it gets confused twice")
        print("  ✓ Offers payment plans, extensions, and solutions")
        print("  ✓ Only transfers if customer demands repeatedly")
        print("=" * 80)
        
    else:
        print(f"❌ Call failed: {result.get('error')}")
    
    print("\n" + "=" * 80)

def view_call_history():
    """View call history for a customer"""
    print("\n" + "=" * 80)
    print("📞 VIEWING CALL HISTORY")
    print("=" * 80)
    
    response = requests.get(f"{BASE_URL}/api/call/customers/{CUSTOMER_ID}/call-history")
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch call history")
        return
    
    data = response.json()
    
    print(f"\nCustomer: {data['customer_name']} ({data['customer_id']})")
    print(f"Total Calls: {data['total_calls']}")
    
    for i, call in enumerate(data['call_history'], 1):
        print(f"\n--- Call #{i} ---")
        print(f"Call ID: {call['call_id']}")
        print(f"Timestamp: {call['timestamp']}")
        print(f"Duration: {call['duration']}s")
        print(f"Status: {call['status']}")
        print(f"Outcome: {call['outcome']}")
        print(f"Transfer Attempted: {call['transfer_attempted']}")
        print(f"Unclear Count: {call['unclear_count']}")
        print(f"Conversation Turns: {call['conversation_turns']}")
        
        if call['conversation_history']:
            print(f"\nConversation:")
            for turn in call['conversation_history']:
                print(f"  [{turn.get('intent', 'N/A')}] (State: {turn.get('state_transition', 'N/A')})")
                print(f"  Agent: {turn['bot_response'][:100]}...")
                if turn['customer_response'] != 'N/A (Agent initiated call)':
                    print(f"  Customer: {turn['customer_response']}")
                print()
    
    print("=" * 80)

def check_health():
    """Check if the Flask app is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    # Check if app is running
    if not check_health():
        print("❌ Flask app is not running!")
        print("Start it with: python app.py")
        sys.exit(1)
    
    print("✓ Flask app is running")
    
    # Allow custom customer ID
    if len(sys.argv) > 1:
        if sys.argv[1] == 'history':
            view_call_history()
            sys.exit(0)
        else:
            CUSTOMER_ID = sys.argv[1]
    
    test_initiate_call()
    
    print("\n💡 TIP: Run 'python test_call.py history' to view call history after the call")