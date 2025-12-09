from datetime import datetime
from utils.db import db_instance

class Customer:
    collection_name = 'customers'
    
    @staticmethod
    def get_collection():
        if db_instance._db is None: db_instance.connect()
        return db_instance._db[Customer.collection_name]
    
    @staticmethod
    def find_by_id(customer_id):
        return Customer.get_collection().find_one({'customer_id': customer_id})
    
    @staticmethod
    def update_call_history(customer_id, call_record):
        Customer.get_collection().update_one(
            {'customer_id': customer_id},
            {'$push': {'call_history': call_record}}
        )