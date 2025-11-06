from datetime import datetime
from bson import ObjectId
from utils.db import db_instance

class Customer:
    collection_name = 'customers'
    
    @staticmethod
    def get_collection():
        """Get the customers collection"""
        db = db_instance.get_db()
        return db[Customer.collection_name]
    
    @staticmethod
    def find_by_id(customer_id):
        """Find customer by customer_id"""
        collection = Customer.get_collection()
        return collection.find_one({'customer_id': customer_id})
    
    @staticmethod
    def find_by_object_id(object_id):
        """Find customer by MongoDB _id"""
        collection = Customer.get_collection()
        return collection.find_one({'_id': ObjectId(object_id)})
    
    @staticmethod
    def find_by_phone(phone):
        """Find customer by phone number"""
        collection = Customer.get_collection()
        return collection.find_one({'phone': phone})
    
    @staticmethod
    def create(customer_data):
        """Create a new customer"""
        collection = Customer.get_collection()
        customer_data['created_at'] = datetime.utcnow()
        customer_data['updated_at'] = datetime.utcnow()
        result = collection.insert_one(customer_data)
        return str(result.inserted_id)
    
    @staticmethod
    def update_call_history(customer_id, call_record):
        """Add a call record to customer's call history"""
        collection = Customer.get_collection()
        result = collection.update_one(
            {'customer_id': customer_id},
            {
                '$push': {'call_history': call_record},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
        return result.modified_count > 0
    
    @staticmethod
    def update_bank_details(customer_id, bank_details):
        """Update customer's bank details"""
        collection = Customer.get_collection()
        result = collection.update_one(
            {'customer_id': customer_id},
            {
                '$set': {
                    'bank_details': bank_details,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    @staticmethod
    def get_pending_customers():
        """Get all customers with pending EMI"""
        collection = Customer.get_collection()
        return list(collection.find({'bank_details.pending_emi_amount': {'$gt': 0}}))
    
    @staticmethod
    def get_call_statistics(customer_id):
        """Get call statistics for a customer"""
        customer = Customer.find_by_id(customer_id)
        if not customer:
            return None
        
        call_history = customer.get('call_history', [])
        
        stats = {
            'total_calls': len(call_history),
            'completed_calls': sum(1 for c in call_history if c.get('status') == 'completed'),
            'transfers_attempted': sum(1 for c in call_history if c.get('transfer_attempted', False)),
            'payment_commitments': sum(1 for c in call_history if c.get('outcome') in ['WILL_PAY_NOW', 'WILL_PAY_LATER']),
            'avg_duration': sum(c.get('duration', 0) for c in call_history) / len(call_history) if call_history else 0,
            'outcomes': {}
        }
        
        # Count outcomes
        for call in call_history:
            outcome = call.get('outcome', 'unknown')
            stats['outcomes'][outcome] = stats['outcomes'].get(outcome, 0) + 1
        
        return stats